"""
质量规则执行引擎 (Quality Runner)
基于数据库配置动态执行 Great Expectations 校验
支持强/弱规则控制、异常数据归档、问题工单自动生成
"""
import os
import pandas as pd
import json
from datetime import datetime
from sqlalchemy.orm import Session

# 导入数据库模型和管理器
from models.base import get_session
from models.managers import (
    AssetManager, RuleManager, ValidationHistoryManager,
    IssueManager, ExceptionDataManager
)
from engine.ge_wrapper import run_evaluation as ge_run_evaluation

# 导入告警模块（可选）
try:
    from services.notification_service import alert_manager, format_validation_failure_alert
    ALERT_ENABLED = True
except ImportError:
    ALERT_ENABLED = False


class QualityRunner:
    """
    质量规则执行器
    
    工作流程：
    1. 从数据库读取资产和规则配置
    2. 加载数据并执行 GE 校验
    3. 保存校验历史到数据库
    4. 根据结果强度处理（强规则失败抛出异常）
    5. 归档异常数据
    6. 自动生成问题工单
    """
    
    def __init__(self, session: Session = None):
        """
        初始化执行器
        
        Args:
            session: 数据库会话，如果为None则自动创建
        """
        self.session = session or get_session()
        self.should_close_session = session is None
    
    def __del__(self):
        """清理资源"""
        if self.should_close_session and hasattr(self, 'session'):
            try:
                self.session.close()
            except:
                pass
    
    def run_asset_validation(self, asset_id: int, rule_ids: list = None, 
                            data_source: str = None, auto_archive: bool = True,
                            auto_create_issue: bool = True, trigger_type: str = 'manual'):
        """
        执行资产的质量校验
        
        Args:
            asset_id: 资产ID
            rule_ids: 指定要执行的规则ID列表，None表示执行所有激活的规则
            data_source: 可选的数据源路径，覆盖资产配置的data_source
            auto_archive: 是否自动归档异常数据
            auto_create_issue: 是否自动创建问题工单
            trigger_type: 触发方式 ('manual'/'scheduled'/'api')
            
        Returns:
            dict: 包含所有规则的校验结果
        """
        # 1. 获取资产信息
        asset = AssetManager.get_asset(self.session, asset_id)
        if not asset:
            raise ValueError(f"资产不存在: ID={asset_id}")
        
        if not asset.is_active:
            raise ValueError(f"资产未启用监控: {asset.name}")
        
        # 确定数据源路径
        source_path = data_source or asset.data_source
        
        # 2. 获取规则列表
        if rule_ids:
            rules = []
            for rule_id in rule_ids:
                rule = RuleManager.get_rule(self.session, rule_id)
                if rule and rule.is_active:
                    rules.append(rule)
        else:
            rules = RuleManager.get_rules_by_asset(self.session, asset_id, is_active=True)
        
        if not rules:
            raise ValueError(f"没有找到可执行的规则")
        
        # 3. 加载数据（从 db_config 中提取表名传入）
        db_config = json.loads(asset.db_config) if asset.db_config else None
        table_name = db_config.get('table') if isinstance(db_config, dict) else None
        df = self._load_data(source_path, asset.asset_type, table_name=table_name)
        
        # 4. 执行每个规则的校验（所有规则统一按弱规则处理，全部执行完后再给出结果）
        results = []

        for rule in rules:
            try:
                result = self._execute_single_rule(rule, df, asset_id, auto_archive, trigger_type)
                results.append(result)
            except Exception as e:
                # 记录执行错误，继续执行后续规则
                error_result = {
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'success': False,
                    'error': str(e),
                    'status': 'error'
                }
                results.append(error_result)

        # 5. 如果启用了自动创建问题工单，为失败的规则创建问题
        if auto_create_issue:
            for result in results:
                if not result.get('success', True) and result.get('status') != 'error':
                    self._auto_create_issue(asset_id, result)

        total = len(results)
        passed = sum(1 for r in results if r.get('success'))
        failed = total - passed

        if total == 1:
            overall_status = 'success' if passed == 1 else 'failed'
        else:
            if passed == total:
                overall_status = 'success'
            elif passed > 0:
                overall_status = 'partial'
            else:
                overall_status = 'failed'

        return {
            'asset_id': asset_id,
            'asset_name': asset.name,
            'status': overall_status,
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_rules': len(rules),
            'passed_rules': sum(1 for r in results if r.get('success')),
            'failed_rules': sum(1 for r in results if not r.get('success')),
            'success_rate': round(sum(1 for r in results if r.get('success')) / len(rules) * 100, 1) if len(rules) > 0 else 0,
            'results': results,
            'trigger_type': trigger_type,
            'error_message': None
        }
    
    def _load_data(self, source_path: str, asset_type: str, table_name: str = None) -> pd.DataFrame:
        """
        加载数据

        Args:
            source_path: 数据源路径（可能是相对路径或完整路径，或数据库连接URL）
            asset_type: 资产类型
            table_name: 数据库表名（可选，优先使用）

        Returns:
            DataFrame
        """
        try:
            # 处理数据库类型数据源
            if asset_type == 'database' or source_path.startswith(('postgresql://', 'postgres://', 'postgresql+psycopg2://', 'mysql://', 'mysql+pymysql://', 'sqlite://')):
                # 检查是否是已复制到 output/data 的 SQLite 文件
                if asset_type == 'database' and not source_path.startswith(('postgresql://', 'postgres://', 'postgresql+psycopg2://', 'mysql://', 'mysql+pymysql://', 'sqlite://')):
                    # 这是复制到 src/output/data 的 SQLite 文件
                    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
                    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
                    possible_paths = [
                        os.path.join(PROJECT_ROOT, 'src', 'output', 'data', source_path),
                        os.path.join(PROJECT_ROOT, 'output', 'data', source_path),
                    ]
                    db_path = None
                    for p in possible_paths:
                        if os.path.exists(p):
                            db_path = p
                            break

                    if db_path:
                        source_path = f"sqlite:///{db_path}"
                    else:
                        raise FileNotFoundError(f"SQLite 文件不存在: {possible_paths[0]}")
                
                # 解析连接URL，提取连接字符串和表名
                # 
                # 支持两种格式：
                # 格式1（推荐）: postgresql://user:pass@host:port/database/newtable
                #              -> database = database, table = newtable
                # 格式2: postgresql://user:pass@host:port/database.schema.newtable
                #              -> database = database, table = schema.newtable
                # 格式3: postgresql://user:pass@host:port/database.newtable
                #              -> database = database, table = newtable  (这里database是不带后缀的)
                #
                # 我们需要处理格式3，其中数据库名和表名用点号分隔在同一部分
                # 
                import urllib.parse
                from sqlalchemy import create_engine
                
                # 解析URL
                # 格式: scheme://netloc/path
                parsed = urllib.parse.urlparse(source_path)
                
                # path 部分可能包含 database/table 或 database.table
                path = parsed.path.strip('/')
                
                if '/' in path:
                    # 格式1: database/table
                    database_name, table_name = path.split('/', 1)
                    # 重建连接URL：只到数据库部分
                    new_path = '/' + database_name
                    parsed = parsed._replace(path=new_path)
                    connection_url = urllib.parse.urlunparse(parsed)
                elif '.' in path and not parsed.scheme == 'sqlite':
                    # 格式3: database.table (或 database.schema.table)
                    # 找到最后一个点号，点号前面是数据库名，点号后面是表名
                    # 如果有多个点号，最后一个点号分隔数据库和表
                    last_dot_index = path.rfind('.')
                    if last_dot_index > 0:
                        database_name = path[:last_dot_index]
                        table_name = path[last_dot_index+1:]
                        # 重建连接URL：只到数据库部分
                        new_path = '/' + database_name
                        parsed = parsed._replace(path=new_path)
                        connection_url = urllib.parse.urlunparse(parsed)
                    else:
                        # 点号在开头，不常见
                        raise ValueError(
                            f"数据库URL格式错误: 无法从URL提取表名，请使用格式: "
                            f"postgresql://user:password@host:port/database/table"
                        )
                else:
                    # SQLite 或只有数据库名
                    if parsed.scheme == 'sqlite':
                        # SQLite：优先使用传入的 table_name，否则读取第一张表
                        connection_url = source_path
                        if table_name:
                            pass  # 使用传入的表名
                        else:
                            engine = create_engine(connection_url)
                            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", engine)
                            if len(tables) > 0:
                                table_name = tables.iloc[0]['name']
                            else:
                                raise ValueError("SQLite 数据库中没有表")
                            engine.dispose()
                    else:
                        # 只有数据库名，没有表名
                        raise ValueError(
                            f"数据库URL格式错误: 无法从URL提取表名，请将表名放在URL最后，格式为: "
                            f"postgresql://user:password@host:port/database/table 或 "
                            f"postgresql://user:password@host:port/database.table"
                        )
                
                # 创建SQLAlchemy引擎并读取数据
                if connection_url.startswith('mysql://') and not connection_url.startswith('mysql+pymysql://'):
                    connection_url = connection_url.replace('mysql://', 'mysql+pymysql://', 1)
                
                engine = create_engine(connection_url)

                # 读取整张表（SQLite 使用 pd.read_sql 避免表名大小写敏感问题）
                if parsed.scheme == 'sqlite':
                    df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
                else:
                    df = pd.read_sql_table(table_name, engine)
                engine.dispose()
                
                print(f"[INFO] 成功从数据库加载数据: {table_name}")
                print(f"[INFO] 数据规模: {len(df)} 行, {len(df.columns)} 列")
                return df
            
            # 处理文件类型（CSV/Excel）
            else:
                # 构建完整的文件路径
                # 如果source_path不是绝对路径，则需要构建完整路径
                if not os.path.isabs(source_path):
                    # 获取项目根目录和上传目录
                    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # src/backend/engine
                    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))  # platform
                    
                    # 尝试多个可能的上传目录
                    possible_paths = [
                        os.path.join(PROJECT_ROOT, 'src', 'output', 'data'),  # platform/src/output/data
                        os.path.join(PROJECT_ROOT, 'output', 'data'),  # platform/output/data (兼容旧版本)
                    ]
                    
                    # 查找文件
                    file_path = None
                    for base_path in possible_paths:
                        candidate = os.path.join(base_path, source_path)
                        if os.path.exists(candidate):
                            file_path = candidate
                            break
                    
                    # 如果都没找到，使用第一个路径（会抛出FileNotFoundError）
                    if file_path is None:
                        file_path = os.path.join(possible_paths[0], source_path)
                else:
                    file_path = source_path
                
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"文件不存在: {file_path}")
                
                if asset_type == 'csv' or source_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                elif asset_type in ['excel', 'xlsx'] or source_path.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_path)
                elif asset_type == 'table':
                    # table类型默认按CSV处理（向后兼容）
                    df = pd.read_csv(file_path)
                else:
                    raise ValueError(f"不支持的资产类型: {asset_type}")
                
                print(f"[INFO] 成功加载数据: {file_path}")
                print(f"[INFO] 数据规模: {len(df)} 行, {len(df.columns)} 列")
                return df
            
        except FileNotFoundError:
            raise
        except Exception as e:
            raise ValueError(f"加载数据失败: {str(e)}")
    
    def _execute_single_rule(self, rule, df: pd.DataFrame, asset_id: int, 
                            auto_archive: bool = True, trigger_type: str = 'manual') -> dict:
        """
        执行单个规则的校验
        
        Args:
            rule: 规则对象
            df: 数据DataFrame
            asset_id: 资产ID
            auto_archive: 是否自动归档异常数据
            trigger_type: 触发方式
            
        Returns:
            dict: 校验结果
        """
        # 1. 创建校验历史记录
        history = ValidationHistoryManager.create_history(
            session=self.session,
            asset_id=asset_id,
            rule_id=rule.id,
            start_time=datetime.now(),
            trigger_type=trigger_type
        )
        
        try:
            # 2. 校验列是否存在
            if rule.column_name and rule.column_name not in df.columns:
                raise ValueError(f"列 '{rule.column_name}' 不存在于数据表中，可用列: {list(df.columns)}")

            # 3. 构建规则配置
            rule_config = self._build_rule_config(rule)

            # 4. 直接使用 GE 执行校验（不通过 ge_engine）
            import great_expectations as gx
            
            # 确保日期列被解析为datetime类型（避免字符串比较问题）
            if rule.column_name and rule.column_name in df.columns:
                # 尝试检测并转换日期列
                col_dtype = str(df[rule.column_name].dtype)
                if 'object' in col_dtype or 'string' in col_dtype:
                    # 尝试转换为datetime（无法解析的值设为NaT）
                    try:
                        original_count = len(df[rule.column_name])
                        converted = pd.to_datetime(df[rule.column_name], errors='coerce')
                        na_count = converted.isna().sum()
                        # 如果超过一半无法解析，说明不是日期列，回退到原始类型
                        if na_count / original_count > 0.5:
                            print(f"[INFO] 列 {rule.column_name} 非日期列（{na_count}/{original_count} 无法解析），保持原类型")
                        else:
                            df[rule.column_name] = converted
                            if na_count > 0:
                                print(f"[WARN] 列 {rule.column_name} 转换 datetime 时有 {na_count}/{original_count} 个值无法解析")
                            print(f"[INFO] 列 {rule.column_name} 已转换为 datetime 类型")
                    except Exception as conv_err:
                        print(f"[WARN] 列 {rule.column_name} 转换为 datetime 失败: {conv_err}")
            
            # 创建临时上下文
            context = gx.get_context(mode="ephemeral")
            
            # 添加 Pandas datasource
            datasource = context.data_sources.add_pandas(name="pandas_datasource")
            
            # 添加 dataframe asset
            asset_gx = datasource.add_dataframe_asset(name="data_asset")
            
            # 创建 batch definition
            batch_def = asset_gx.add_batch_definition_whole_dataframe("my_batch")
            
            # 创建 Expectation Suite
            suite = context.suites.add(gx.ExpectationSuite(name="test_suite"))
            
            # 构建 GE 期望
            ge_method_name = self._map_rule_type_to_ge(rule.rule_type, rule.ge_expectation)
            expectation_class_name = ''.join(word.capitalize() for word in ge_method_name.replace('expect_', '').split('_'))
            expectation_class = getattr(gx.expectations, f'Expect{expectation_class_name}', None)
            
            if not expectation_class:
                raise ValueError(f"无法找到GE期望类: Expect{expectation_class_name}")
            
            exp_params = {'column': rule.column_name}
            
            # 解析参数
            mostly_value = 1.0  # 默认100%通过才算成功
            if rule.parameters:
                try:
                    params = json.loads(rule.parameters)
                    # 通用参数
                    # 数值/日期范围参数（兼容 min_length/max_length 旧命名）
                    min_val = params.get('min_value')
                    if min_val is None:
                        min_val = params.get('min_length')
                    if min_val is not None:
                        # 如果列是datetime类型且边界值是字符串，将边界值也转换为datetime，避免GX类型不匹配
                        if (rule.column_name in df.columns and
                                pd.api.types.is_datetime64_any_dtype(df[rule.column_name]) and
                                isinstance(min_val, str)):
                            try:
                                min_val = pd.to_datetime(min_val)
                            except Exception as date_err:
                                print(f"[WARN] min_value '{min_val}' 转换为datetime失败: {date_err}")
                        exp_params['min_value'] = min_val

                    max_val = params.get('max_value')
                    if max_val is None:
                        max_val = params.get('max_length')
                    if max_val is not None:
                        if (rule.column_name in df.columns and
                                pd.api.types.is_datetime64_any_dtype(df[rule.column_name]) and
                                isinstance(max_val, str)):
                            try:
                                max_val = pd.to_datetime(max_val)
                            except Exception as date_err:
                                print(f"[WARN] max_value '{max_val}' 转换为datetime失败: {date_err}")
                        exp_params['max_value'] = max_val
                    if 'value_set' in params:
                        exp_params['value_set'] = params['value_set']
                    if 'mostly' in params:
                        exp_params['mostly'] = params['mostly']
                        mostly_value = float(params['mostly'])
                    # 日期格式校验参数
                    if 'strftime_format' in params:
                        exp_params['strftime_format'] = params['strftime_format']
                    # 递增/递减校验参数
                    if 'strictly' in params:
                        exp_params['strictly'] = params['strictly'] == 'true'
                except Exception as e:
                    print(f"[WARN] 解析规则参数时出错: {e}")
            
            suite.add_expectation(expectation_class(**exp_params))
            
            # 创建 Validation Definition
            validation_definition = gx.ValidationDefinition(
                name="data_quality_validation",
                data=batch_def,
                suite=suite
            )
            
            # 运行验证
            result = validation_definition.run(batch_parameters={"dataframe": df})
            
            # 解析结果
            result_dict = result.to_json_dict()
            if result_dict.get('results'):
                detail = result_dict['results'][0]
                ge_success = detail.get('success', False)
                result_data = detail.get('result', {})

                # 如果 GE 内部出错（如列不存在），result 为空且 success=False
                # 此时应抛出异常，而不是显示 pass_rate=100% 但 status=failed
                if not ge_success and not result_data:
                    exc_info = detail.get('exception_info', {})
                    exc_msg = 'GE 校验内部错误'
                    for v in exc_info.values():
                        if isinstance(v, dict) and v.get('raised_exception'):
                            exc_msg = v.get('exception_message', exc_msg)
                            break
                    raise ValueError(exc_msg)

                unexpected_count = result_data.get('unexpected_count', 0)
                unexpected_percent = result_data.get('unexpected_percent', 0.0)
                total_records = result_data.get('element_count', len(df))
                failed_records = unexpected_count
                pass_rate = round((1 - unexpected_percent / 100) * 100, 2) if unexpected_percent < 100 else 0.0

                # 根据mostly参数判断规则是否成功
                success = (unexpected_percent / 100) <= (1 - mostly_value)
                if not ge_success:
                    success = False

                sample_unexpected = result_data.get('partial_unexpected_list', [])[:10]
                
                # 5. 更新校验历史（根据实际结果设置状态）
                ValidationHistoryManager.update_history(
                    session=self.session,
                    history_id=history.id,
                    status='success' if success else 'failed',
                    end_time=datetime.now(),
                    pass_rate=pass_rate,
                    total_records=total_records,
                    failed_records=failed_records
                )
                
                # 6. 如果失败且有异常值，归档异常数据
                if not success and auto_archive and sample_unexpected:
                    self._archive_exceptions(history.id, asset_id, rule.id, 
                                           {'column': rule.column_name, 'sample_unexpected': sample_unexpected}, 
                                           df)
                
                return {
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'rule_type': rule.rule_type,
                    'strength': rule.strength,
                    'column': rule.column_name,
                    'success': success,
                    'pass_rate': pass_rate,
                    'total_records': total_records,
                    'failed_records': failed_records,
                    'validation_history_id': history.id,
                    'status': 'completed'
                }
            else:
                raise ValueError("GE返回结果为空")
                
        except Exception as e:
            # 更新历史记录为失败
            ValidationHistoryManager.update_history(
                session=self.session,
                history_id=history.id,
                status='failed',
                end_time=datetime.now(),
                error_message=str(e)
            )
            
            return {
                'rule_id': rule.id,
                'rule_name': rule.name,
                'success': False,
                'error': str(e),
                'validation_history_id': history.id,
                'status': 'error'
            }
    
    def _build_rule_config(self, rule) -> dict:
        """
        从规则对象构建GE规则配置
        
        Args:
            rule: 规则对象
            
        Returns:
            dict: GE规则配置
        """
        config = {
            'column': rule.column_name or '',
            'rule_type': self._map_rule_type_to_ge(rule.rule_type, rule.ge_expectation)
        }
        
        # 解析参数
        if rule.parameters:
            try:
                params = json.loads(rule.parameters)
                config['params'] = params
            except:
                config['params'] = {}
        else:
            config['params'] = {}
        
        return config
    
    # GE期望ID别名映射（兼容旧版错误命名）
    GE_EXPECTATION_ALIASES = {
        'expect_column_values_to_match_length_between': 'expect_column_value_lengths_to_be_between',
    }

    def _map_rule_type_to_ge(self, rule_type: str, ge_expectation: str) -> str:
        """
        将规则类型映射回GE方法名
        
        Args:
            rule_type: 规则类型
            ge_expectation: GE期望类名或方法名
            
        Returns:
            str: GE方法名
        """
        # 别名修正（兼容数据库中存储的旧版错误ID）
        ge_expectation = self.GE_EXPECTATION_ALIASES.get(ge_expectation, ge_expectation)

        # 如果ge_expectation以Expect开头，说明是类名，需要转换为方法名
        # 例如: ExpectColumnValuesToNotBeNull -> expect_column_values_to_not_be_null
        if ge_expectation.startswith('Expect'):
            method_name = ge_expectation[6:]  # 去掉'Expect'
            # 驼峰转下划线
            import re
            method_name = re.sub(r'(?<!^)(?=[A-Z])', '_', method_name).lower()
            return method_name
        # 如果不以Expect开头，说明已经是方法名（下划线格式），直接返回
        # 例如: expect_column_values_to_not_be_null -> expect_column_values_to_not_be_null
        return ge_expectation
    
    def _archive_exceptions(self, history_id: int, asset_id: int, rule_id: int,
                           detail: dict, df: pd.DataFrame):
        """
        归档异常数据
        
        Args:
            history_id: 校验历史ID
            asset_id: 资产ID
            rule_id: 规则ID
            detail: 校验详情
            df: 原始数据
        """
        sample_unexpected = detail.get('sample_unexpected', [])
        column = detail.get('column', '')
        
        # 找出异常值的行号
        if column and column in df.columns:
            for idx, value in enumerate(df[column]):
                if value in sample_unexpected:
                    ExceptionDataManager.add_exception(
                        session=self.session,
                        validation_history_id=history_id,
                        asset_id=asset_id,
                        rule_id=rule_id,
                        row_number=idx + 1,  # 行号从1开始
                        column_name=column,
                        actual_value=str(value),
                        expected_value='符合规则的值',
                        error_detail=f'字段 {column} 的值不符合规则要求'
                    )
    
    def _auto_create_issue(self, asset_id: int, result: dict):
        """
        自动创建问题工单
        
        Args:
            asset_id: 资产ID
            result: 校验结果
        """
        # 获取资产和规则信息
        asset = AssetManager.get_asset(self.session, asset_id)
        rule = RuleManager.get_rule(self.session, result['rule_id'])
        
        if not asset or not rule:
            return
        
        # 获取校验历史
        history_id = result.get('validation_history_id')
        
        # 创建问题
        issue = IssueManager.create_issue(
            session=self.session,
            asset_id=asset_id,
            rule_id=rule.id,
            validation_history_id=history_id,
            title=f"{rule.name} - 校验失败",
            issue_type='system_detected',
            description=f"规则 '{rule.name}' 校验失败\n"
                       f"通过率: {result.get('pass_rate', 0)}%\n"
                       f"失败记录数: {result.get('failed_records', 0)}",
            priority='high' if rule.strength == 'strong' else 'medium',
            assignee=asset.owner
        )
        
        print(f"[INFO] 自动创建问题工单: {issue.title} (ID: {issue.id})")
        
        # 发送告警通知（如果启用了告警）
        if ALERT_ENABLED and alert_manager.channels:
            try:
                title, message = format_validation_failure_alert(
                    asset_name=asset.name,
                    failed_rules=[{
                        'rule_name': rule.name,
                        'rule_type': rule.rule_type,
                        'column_name': rule.column_name,
                        'success_percent': result.get('pass_rate', 0)
                    }],
                    validation_result=result
                )
                
                # 发送到所有配置的渠道
                alert_manager.send_all(title, message)
                print(f"[INFO] 已发送告警通知")
            except Exception as e:
                print(f"[WARNING] 告警发送失败: {e}")


class StrongRuleFailedException(Exception):
    """
    强规则失败异常
    
    当强规则校验失败时抛出，用于中断下游任务
    """
    def __init__(self, message: str, failed_rules: list, validation_result: dict = None):
        super().__init__(message)
        self.failed_rules = failed_rules
        self.validation_result = validation_result


def run_quality_check(asset_id: int, rule_ids: list = None, 
                     data_source: str = None, auto_archive: bool = True,
                     auto_create_issue: bool = True):
    """
    便捷函数：执行质量校验
    
    Args:
        asset_id: 资产ID
        rule_ids: 规则ID列表
        data_source: 数据源路径
        auto_archive: 是否自动归档
        auto_create_issue: 是否自动创建问题
        
    Returns:
        dict: 校验结果
    """
    runner = QualityRunner()
    try:
        return runner.run_asset_validation(
            asset_id=asset_id,
            rule_ids=rule_ids,
            data_source=data_source,
            auto_archive=auto_archive,
            auto_create_issue=auto_create_issue
        )
    finally:
        if runner.should_close_session:
            runner.session.close()


if __name__ == '__main__':
    # 测试代码
    from models import init_db
    
    # 初始化数据库
    init_db()
    
    print("Quality Runner 模块加载成功")
    print("使用示例:")
    print("  from quality_runner import run_quality_check")
    print("  result = run_quality_check(asset_id=1)")
