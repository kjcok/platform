"""
GE 测评执行引擎
负责将规则映射为 Great Expectations 的 expect_* 函数并执行校验
兼容 GE 0.18.x 和 1.x 版本
"""
import pandas as pd
import great_expectations as gx
from services.file_service import get_file_path, check_file_exists


# 规则类型到 GE 方法的映射
RULE_MAPPING = {
    # 完整性检查
    'not_null': 'expect_column_values_to_not_be_null',
    
    # 准确性检查 - 数值范围
    'between': 'expect_column_values_to_be_between',
    
    # 准确性检查 - 枚举值
    'in_set': 'expect_column_values_to_be_in_set',
    
    # 准确性检查 - 正则表达式
    'match_regex': 'expect_column_values_to_match_regex',
    
    # 唯一性检查
    'unique': 'expect_column_values_to_be_unique',
    
    # 准确性检查 - 数据类型
    'type_string': 'expect_column_values_to_be_of_type',
    'type_integer': 'expect_column_values_to_be_of_type',
    'type_float': 'expect_column_values_to_be_of_type',
    
    # 一致性检查 - 比较两个列
    'column_pair_greater_than': 'expect_column_pair_values_A_to_be_greater_than_B',
}


def run_evaluation(file_id, rules_config, upload_folder='data'):
    """
    执行数据质量评估
    
    Args:
        file_id: 文件ID
        rules_config: 规则配置列表
        upload_folder: 文件目录
        
    Returns:
        dict: 评估结果字典，包含成功率和详细结果
    """
    # 检查文件是否存在
    if not check_file_exists(file_id, upload_folder):
        raise FileNotFoundError(f"文件不存在: {file_id}")
    
    # 获取文件路径
    file_path = get_file_path(file_id, upload_folder)
    
    # 读取数据
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式")
    except Exception as e:
        raise ValueError(f"读取文件失败: {str(e)}")
    
    # 将 DataFrame 转换为 GE Validator（仅支持 GE 1.x）
    ge_version = tuple(map(int, gx.__version__.split('.')[:2]))
    
    if ge_version < (1, 0):
        raise ImportError(
            f"检测到 Great Expectations {gx.__version__} 版本。\n"
            f"当前平台需要 GE 1.x 版本（推荐 1.16.0）。\n"
            f"请运行: pip install great-expectations==1.16.0"
        )
    
    # GE 1.x 版本：使用 ValidationDefinition（推荐方式）
    try:
        # 创建临时上下文
        context = gx.get_context(mode="ephemeral")
        
        # 添加 Pandas datasource
        datasource = context.data_sources.add_pandas(name="pandas_datasource")
        
        # 添加 dataframe asset
        asset = datasource.add_dataframe_asset(name="data_asset")
        
        # 创建 batch definition
        batch_def = asset.add_batch_definition_whole_dataframe("my_batch")
        
        # 创建 Expectation Suite
        suite = context.suites.add(gx.ExpectationSuite(name="test_suite"))
        
        # 将规则映射为 GE 期望并添加到 suite
        for rule in rules_config:
            column = rule['column']
            rule_type = rule['rule_type']
            params = rule.get('params', {})
            
            # 验证列是否存在
            if column not in df.columns:
                raise ValueError(f"列 '{column}' 不存在于数据集中")
            
            ge_method_name = RULE_MAPPING.get(rule_type)
            if not ge_method_name:
                raise ValueError(f"不支持的规则类型: {rule_type}")
            
            # 转换为 GE 期望类名
            expectation_class_name = ''.join(word.capitalize() for word in ge_method_name.replace('expect_', '').split('_'))
            expectation_class = getattr(gx.expectations, f'Expect{expectation_class_name}', None)
            
            if expectation_class:
                # 准备参数
                exp_params = {'column': column}
                
                # 特殊处理：根据规则类型设置 type_ 参数
                if rule_type.startswith('type_'):
                    type_map = {
                        'type_string': 'str',
                        'type_integer': 'int',
                        'type_float': 'float'
                    }
                    exp_params['type_'] = type_map.get(rule_type, 'str')
                elif rule_type == 'between':
                    exp_params['min_value'] = params.get('min_value')
                    exp_params['max_value'] = params.get('max_value')
                elif rule_type == 'in_set':
                    exp_params['value_set'] = params.get('value_set', [])
                elif rule_type == 'length_between':
                    exp_params['min_value'] = params.get('min_value')
                    exp_params['max_value'] = params.get('max_value')
                
                # 添加期望到 suite
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
        results = []
        passed_rules = 0
        
        for exp_result in result_dict.get('results', []):
            success = exp_result.get('success', False)
            if success:
                passed_rules += 1
            
            exp_config = exp_result.get('expectation_config', {})
            result_data = exp_result.get('result', {})
            
            # 提取列名和规则类型
            kwargs = exp_config.get('kwargs', {})
            column = kwargs.get('column', 'unknown')
            exp_type = exp_config.get('type', '')
            
            # 反向映射：从 GE 期望类型到规则类型
            reverse_mapping = {v: k for k, v in RULE_MAPPING.items()}
            rule_type = reverse_mapping.get(exp_type, exp_type)
            
            result_info = {
                'column': column,
                'rule_type': rule_type,
                'success': success,
                'unexpected_count': result_data.get('unexpected_count', 0),
                'unexpected_percent': result_data.get('unexpected_percent', 0.0),
                'element_count': result_data.get('element_count', 0),
            }
            
            # 如果有异常值，添加部分示例
            if not success and result_data.get('partial_unexpected_list'):
                result_info['sample_unexpected'] = result_data['partial_unexpected_list'][:10]
            
            results.append(result_info)
        
        # 计算成功率
        total_rules = len(results)
        success_percent = round((passed_rules / total_rules * 100), 2) if total_rules > 0 else 0
        
        return {
            'file_id': file_id,
            'total_rules': total_rules,
            'passed_rules': passed_rules,
            'failed_rules': total_rules - passed_rules,
            'success_percent': success_percent,
            'details': results,
            'total_rows': len(df),
            'columns': df.columns.tolist()
        }
        
    except (ValueError, FileNotFoundError):
        # 让这些异常正常传播
        raise
    except Exception as e:
        raise ImportError(f"GE 1.x 评估失败: {str(e)}")
