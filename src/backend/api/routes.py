"""
DataQ 质量治理工作台 - RESTful API
提供资产、规则、校验执行、问题管理的完整接口
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os
import traceback

# 让 pymysql 充当 MySQLdb，供 SQLAlchemy 使用
import pymysql
pymysql.install_as_MySQLdb()

# 导入数据库工具和执行引擎
from models.managers import (
    get_session, AssetManager, RuleManager, 
    ValidationHistoryManager, IssueManager, ExceptionDataManager
)
from engine.quality_runner import QualityRunner

# 导入数据模型（用于统计查询）
from models.base import Asset, Rule, Issue, ValidationHistory

# 导入第四阶段模块（可选）
try:
    from services.scheduler_service import scheduler, init_scheduler
    SCHEDULER_ENABLED = True
except ImportError:
    SCHEDULER_ENABLED = False

try:
    from services.notification_service import alert_manager, init_default_alerts
    ALERT_ENABLED = True
except ImportError:
    ALERT_ENABLED = False

try:
    from middleware.auth import jwt_auth, token_required, admin_required
    AUTH_ENABLED = True
except ImportError:
    AUTH_ENABLED = False

# 导入文件服务
from services.file_service import save_uploaded_file


# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


def get_db_session():
    """获取数据库会话"""
    return get_session()


def handle_error(e, status_code=500):
    """统一错误处理"""
    error_response = {
        'status': 'error',
        'message': str(e),
        'timestamp': datetime.now().isoformat()
    }
    
    # 开发模式下返回详细错误信息
    if hasattr(api_bp, 'app') and api_bp.app.debug:
        error_response['traceback'] = traceback.format_exc()
    
    return jsonify(error_response), status_code


# ==================== 文件上传 API ====================

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    上传数据文件并获取表头
    
    Returns:
        JSON: 包含 file_id 和 columns 的响应
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '没有上传文件'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '文件名为空'
            }), 400
        
        # 配置上传目录
        import os
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
        UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'output', 'data')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # 保存文件并获取信息
        result = save_uploaded_file(file, UPLOAD_FOLDER)
        
        if result is None:
            return jsonify({
                'status': 'error',
                'message': '文件格式不支持或文件为空，仅支持 CSV、XLSX、XLS 格式'
            }), 400
        
        return jsonify({
            'status': 'success',
            'file_id': result['file_id'],
            'columns': result['columns'],
            'message': '文件上传成功'
        })
        
    except Exception as e:
        return handle_error(e)


# ==================== 数据预览 API ====================

@api_bp.route('/upload/preview', methods=['POST'])
def preview_uploaded_file():
    """预览上传的CSV/Excel文件内容"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': '文件名为空'}), 400
        
        import pandas as pd
        import io
        file_content = io.BytesIO(file.read())
        filename = file.filename.lower()
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file_content, nrows=20)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_content, nrows=20)
            else:
                return jsonify({'status': 'error', 'message': '不支持的文件格式'}), 400
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'读取文件失败: {str(e)}'}), 400
        columns = df.columns.tolist()
        rows = df.values.tolist()
        import numpy as np
        rows = [[None if (isinstance(x, float) and np.isnan(x)) else x for x in row] for row in rows]
        return jsonify({
            'status': 'success',
            'data': {
                'columns': columns,
                'rows': rows,
                'preview_rows': len(rows),
                'total_columns': len(columns)
            }
        })
    except Exception as e:
        return handle_error(e)


@api_bp.route('/assets/<int:asset_id>/preview', methods=['GET'])
def preview_asset_data(asset_id):
    """预览资产对应的数据文件内容"""
    try:
        session = get_db_session()
        try:
            from models.base import Asset
            asset = session.query(Asset).filter_by(id=asset_id).first()
            
            if not asset:
                return jsonify({'status': 'error', 'message': f'资产 {asset_id} 不存在'}), 404
            
            import os
            import pandas as pd
            import math
            CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
            PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
            UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'output', 'data')
            
            # 先读取总行数，计算预览行数
            total_rows = 0
            table_name = None
            df = None
            
            try:
                # 判断资产类型并读取数据
                if asset.asset_type == 'database':
                    # 数据库类型：需要区分 SQLite 文件型 和 MySQL/PostgreSQL 网络型
                    data_source = asset.data_source
                    
                    if data_source.startswith('sqlite:///'):
                        # SQLite 旧格式
                        file_path = data_source.replace('sqlite:///', '')
                        db_type = 'sqlite'
                    elif data_source.startswith('sqlite_') or data_source.lower().endswith('.db'):
                        # SQLite 新格式（已复制到 output/data）
                        file_path = os.path.join(UPLOAD_FOLDER, data_source)
                        db_type = 'sqlite'
                    elif data_source.startswith(('mysql://', 'mysql+pymysql://')):
                        db_type = 'mysql'
                    elif data_source.startswith(('postgresql://', 'postgres://', 'postgresql+psycopg2://')):
                        db_type = 'postgresql'
                    elif data_source.startswith(('mssql://', 'mssql+pyodbc://')):
                        db_type = 'sqlserver'
                    elif data_source.startswith('oracle://'):
                        db_type = 'oracle'
                    else:
                        db_type = 'sqlite'  # 默认按 SQLite 处理
                    
                    # 获取表名
                    if asset.db_config:
                        db_config = json.loads(asset.db_config) if isinstance(asset.db_config, str) else asset.db_config
                        table_name = db_config.get('table')
                    
                    if db_type == 'sqlite':
                        # SQLite：文件型数据库
                        if not os.path.exists(file_path):
                            return jsonify({'status': 'error', 'message': f'数据文件不存在: {data_source}'}), 404
                        
                        from integrations.db_connector import create_connector
                        conn = create_connector('sqlite', db_path=file_path)
                        with conn:
                            if not table_name:
                                tables_df = conn.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
                                if len(tables_df) > 0:
                                    table_name = tables_df.iloc[0]['name']
                                else:
                                    return jsonify({'status': 'error', 'message': 'SQLite 数据库中没有表'}), 400
                            
                            count_df = conn.execute_query(f"SELECT COUNT(*) as cnt FROM '{table_name}'")
                            total_rows = int(count_df.iloc[0]['cnt']) if len(count_df) > 0 else 0
                            preview_rows = min(total_rows, 10)
                            df = conn.execute_query(f"SELECT * FROM '{table_name}' LIMIT {preview_rows}")
                    else:
                        # MySQL/PostgreSQL/SQL Server/Oracle：网络型数据库
                        from integrations.db_connector import create_connector
                        
                        # 解析连接参数
                        if asset.db_config:
                            db_config = json.loads(asset.db_config) if isinstance(asset.db_config, str) else asset.db_config
                            table_name = db_config.get('table')
                        
                        if not table_name:
                            return jsonify({'status': 'error', 'message': '未配置数据库表名'}), 400
                        
                        # 使用 _load_data 风格的连接方式
                        import urllib.parse
                        from sqlalchemy import create_engine
                        
                        parsed = urllib.parse.urlparse(data_source)
                        path = parsed.path.strip('/')
                        
                        if '.' in path and '/' not in path:
                            last_dot_index = path.rfind('.')
                            if last_dot_index > 0:
                                database_name = path[:last_dot_index]
                                table_name = path[last_dot_index+1:]
                                new_path = '/' + database_name
                                parsed = parsed._replace(path=new_path)
                                connection_url = urllib.parse.urlunparse(parsed)
                            else:
                                connection_url = data_source
                        else:
                            connection_url = data_source
                        
                        if connection_url.startswith('mysql://') and not connection_url.startswith('mysql+pymysql://'):
                            connection_url = connection_url.replace('mysql://', 'mysql+pymysql://', 1)
                        
                        engine = create_engine(connection_url)
                        
                        # 获取总行数
                        count_result = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {table_name}", engine)
                        total_rows = int(count_result.iloc[0]['cnt'])
                        
                        # 读取预览数据
                        preview_rows = min(total_rows, 10)
                        df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT {preview_rows}", engine)
                        engine.dispose()
                        
                elif asset.asset_type in ['csv', 'excel']:
                    # 文件类型
                    file_path = os.path.join(UPLOAD_FOLDER, asset.data_source)
                    
                    if not os.path.exists(file_path):
                        return jsonify({'status': 'error', 'message': f'数据文件不存在: {asset.data_source}'}), 404
                    
                    if asset.asset_type == 'csv' or file_path.lower().endswith('.csv'):
                        total_rows = sum(1 for _ in open(file_path, 'r', encoding='utf-8')) - 1
                        preview_rows = min(total_rows, 10)
                        df = pd.read_csv(file_path, nrows=preview_rows)
                        
                    elif asset.asset_type == 'excel' or file_path.lower().endswith(('.xlsx', '.xls')):
                        total_rows = len(pd.read_excel(file_path))
                        preview_rows = min(total_rows, 10)
                        df = pd.read_excel(file_path, nrows=preview_rows)
                        
                else:
                    return jsonify({'status': 'error', 'message': '不支持的资产类型'}), 400
                    
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'读取数据失败: {str(e)}'}), 400
            columns = df.columns.tolist()
            rows = df.values.tolist()
            import numpy as np
            rows = [[None if (isinstance(x, float) and np.isnan(x)) else x for x in row] for row in rows]
            return jsonify({
                'status': 'success',
                'data': {
                    'columns': columns,
                    'rows': rows,
                    'total_rows': total_rows,
                    'total_columns': len(columns),
                    'preview_rows': len(rows)
                }
            })
        finally:
            session.close()
    except Exception as e:
        return handle_error(e)


@api_bp.route('/validations/history/<int:history_id>/export/json', methods=['GET'])
def export_validation_json(history_id):
    """导出校验历史结果为JSON格式"""
    try:
        session = get_db_session()
        try:
            from models.base import Asset, Rule, ValidationHistory
            representative = session.query(ValidationHistory).filter_by(id=history_id).first()
            if not representative:
                return jsonify({'status': 'error', 'message': f'校验历史 {history_id} 不存在'}), 404
            from datetime import timedelta
            if representative.start_time:
                start_min = representative.start_time.replace(second=0, microsecond=0)
                end_min = start_min + timedelta(minutes=1)
                histories = session.query(ValidationHistory)\
                    .filter(ValidationHistory.asset_id == representative.asset_id)\
                    .filter(ValidationHistory.start_time >= start_min)\
                    .filter(ValidationHistory.start_time <= end_min)\
                    .order_by(ValidationHistory.id.asc())\
                    .all()
            else:
                histories = [representative]
            asset = session.query(Asset).filter_by(id=representative.asset_id).first()
            total_rules = len(histories)
            passed_rules = sum(1 for h in histories if h.status == 'success')
            failed_rules = sum(1 for h in histories if h.status in ['failed', 'error'])
            success_rate = round((passed_rules / total_rules * 100), 2) if total_rules > 0 else 0
            rule_results = []
            exceptions = []
            for h in histories:
                rule = session.query(Rule).filter_by(id=h.rule_id).first() if h.rule_id else None
                rule_result = {
                    'history_id': h.id,
                    'rule_id': h.rule_id,
                    'rule_name': rule.name if rule else '未知规则',
                    'rule_type': rule.rule_type if rule else 'unknown',
                    'column_name': rule.column_name if rule else None,
                    'strength': rule.strength if rule else 'weak',
                    'status': h.status,
                    'success': h.status == 'success',
                    'pass_rate': h.pass_rate,
                    'total_records': h.total_records,
                    'failed_records': h.failed_records,
                    'error_message': h.error_message,
                    'start_time': h.start_time.isoformat() if h.start_time else None,
                    'end_time': h.end_time.isoformat() if h.end_time else None
                }
                rule_results.append(rule_result)
                if h.status in ['failed', 'error']:
                    exceptions.append({
                        'history_id': h.id,
                        'rule_id': h.rule_id,
                        'rule_name': rule.name if rule else '未知规则',
                        'column_name': rule.column_name if rule else None,
                        'error_type': h.status,
                        'error_message': h.error_message or '校验失败'
                    })
            from datetime import datetime
            export_result = {
                'export_time': datetime.now().isoformat(),
                'version': '1.0',
                'validation_summary': {
                    'batch_id': history_id,
                    'asset_id': representative.asset_id,
                    'asset_name': asset.name if asset else '未知资产',
                    'data_source': asset.data_source if asset else None,
                    'start_time': min(h.start_time for h in histories if h.start_time).isoformat() if any(h.start_time for h in histories) else None,
                    'end_time': max(h.end_time for h in histories if h.end_time).isoformat() if any(h.end_time for h in histories) else None,
                    'trigger_type': representative.trigger_type if hasattr(representative, 'trigger_type') else 'manual',
                    'total_rules': total_rules,
                    'passed_rules': passed_rules,
                    'failed_rules': failed_rules,
                    'success_rate': success_rate,
                    'has_strong_rule_failure': any(h.rule and h.rule.strength == 'strong' and h.status != 'success' for h in histories)
                },
                'rule_results': rule_results,
                'exceptions': exceptions
            }
            if request.args.get('download', 'false').lower() == 'true':
                from flask import make_response
                import json
                response = make_response(json.dumps(export_result, ensure_ascii=False, indent=2))
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                response.headers['Content-Disposition'] = f'attachment; filename="validation_result_{history_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
                return response
            return jsonify({'status': 'success', 'data': export_result})
        finally:
            session.close()
    except Exception as e:
        return handle_error(e)

# ==================== 资产管理 API ====================

@api_bp.route('/assets', methods=['GET'])
def list_assets():
    """
    获取资产列表
    
    Query Parameters:
        page: 页码（默认1）
        per_page: 每页数量（默认20）
        is_active: 是否只查询激活的资产（true/false）
        
    Returns:
        JSON: 资产列表和分页信息
    """
    try:
        session = get_db_session()
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            is_active = request.args.get('is_active', 'true').lower() == 'true'
            
            assets = AssetManager.list_assets(session, page=page, per_page=per_page, is_active=is_active)
            total = len(assets)
            
            result = []
            for asset in assets:
                # 获取该资产的规则数量
                rules = RuleManager.get_rules_by_asset(session, asset.id)
                
                result.append({
                    'id': asset.id,
                    'name': asset.name,
                    'data_source': asset.data_source,
                    'asset_type': asset.asset_type,
                    'owner': asset.owner,
                    'quality_score_weight': asset.quality_score_weight,
                    'is_active': asset.is_active,
                    'rule_count': len(rules),  # 添加规则数量
                    'created_at': asset.created_at.isoformat(),
                    'updated_at': asset.updated_at.isoformat()
                })
            
            return jsonify({
                'status': 'success',
                'data': result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/assets/<int:asset_id>', methods=['GET'])
def get_asset(asset_id):
    """
    获取单个资产详情
    
    Args:
        asset_id: 资产ID
        
    Returns:
        JSON: 资产详细信息
    """
    try:
        session = get_db_session()
        try:
            asset = AssetManager.get_asset(session, asset_id)
            
            if not asset:
                return jsonify({
                    'status': 'error',
                    'message': f'资产 {asset_id} 不存在'
                }), 404
            
            # 获取关联的规则
            rules = RuleManager.get_rules_by_asset(session, asset_id)
            rules_data = [{
                'id': rule.id,
                'name': rule.name,
                'rule_type': rule.rule_type,
                'rule_template': rule.rule_template,
                'column_name': rule.column_name,
                'strength': rule.strength,
                'enabled': rule.is_active,  # 使用enabled而不是is_active以匹配前端
                'description': rule.description,
                'ge_expectation': rule.ge_expectation,
                'parameters': rule.parameters,
                'created_at': rule.created_at.isoformat() if rule.created_at else None
            } for rule in rules]
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': asset.id,
                    'name': asset.name,
                    'data_source': asset.data_source,
                    'asset_type': asset.asset_type,
                    'owner': asset.owner,
                    'quality_score_weight': asset.quality_score_weight,
                    'is_active': asset.is_active,
                    'created_at': asset.created_at.isoformat(),
                    'updated_at': asset.updated_at.isoformat(),
                    'rules': rules_data,
                    'rule_count': len(rules_data)
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/assets/<int:asset_id>/columns', methods=['GET'])
def get_asset_columns(asset_id):
    """
    获取资产的字段列表
    
    Args:
        asset_id: 资产ID
        
    Returns:
        JSON: 字段列表
    """
    try:
        session = get_db_session()
        try:
            # 获取资产信息
            asset = AssetManager.get_asset(session, asset_id)
            if not asset:
                return jsonify({
                    'status': 'error',
                    'message': '资产不存在'
                }), 404
            
            columns = []
            
            # 根据资产类型获取字段
            try:
                if asset.asset_type == 'database':
                    # 数据库类型：需要区分 SQLite 文件型 和 MySQL/PostgreSQL 网络型
                    data_source = asset.data_source
                    
                    # 判断数据库类型
                    if data_source.startswith('sqlite:///') or data_source.startswith('sqlite_') or data_source.lower().endswith('.db'):
                        db_type = 'sqlite'
                    elif data_source.startswith(('mysql://', 'mysql+pymysql://')):
                        db_type = 'mysql'
                    elif data_source.startswith(('postgresql://', 'postgres://', 'postgresql+psycopg2://')):
                        db_type = 'postgresql'
                    elif data_source.startswith(('mssql://', 'mssql+pyodbc://')):
                        db_type = 'sqlserver'
                    elif data_source.startswith('oracle://'):
                        db_type = 'oracle'
                    else:
                        db_type = 'sqlite'
                    
                    # 获取表名
                    table_name = None
                    if asset.db_config:
                        db_config = json.loads(asset.db_config) if isinstance(asset.db_config, str) else asset.db_config
                        table_name = db_config.get('table')
                    
                    if db_type == 'sqlite':
                        # SQLite: 读取文件
                        if data_source.startswith('sqlite:///'):
                            file_path = data_source.replace('sqlite:///', '')
                        else:
                            CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
                            PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
                            UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'output', 'data')
                            file_path = os.path.join(UPLOAD_FOLDER, data_source)
                        
                        if os.path.exists(file_path):
                            from integrations.db_connector import create_connector
                            conn = create_connector('sqlite', db_path=file_path)
                            with conn:
                                if not table_name:
                                    tables_df = conn.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
                                    if len(tables_df) > 0:
                                        table_name = tables_df.iloc[0]['name']
                                
                                if table_name:
                                    info_df = conn.execute_query(f"PRAGMA table_info('{table_name}')")
                                    for _, row in info_df.iterrows():
                                        col_type = 'string'
                                        if 'INT' in str(row['type']).upper():
                                            col_type = 'integer'
                                        elif 'REAL' in str(row['type']).upper() or 'FLOAT' in str(row['type']).upper() or 'DOUBLE' in str(row['type']).upper():
                                            col_type = 'float'
                                        elif 'DATE' in str(row['type']).upper() or 'TIME' in str(row['type']).upper():
                                            col_type = 'datetime'
                                        columns.append({'name': row['name'], 'type': col_type})
                        else:
                            return jsonify({'status': 'error', 'message': f'SQLite 文件不存在: {file_path}'}), 404
                    else:
                        # MySQL/PostgreSQL/SQL Server/Oracle
                        if not table_name:
                            return jsonify({'status': 'error', 'message': '未配置数据库表名'}), 400
                        
                        import urllib.parse
                        from sqlalchemy import create_engine, inspect
                        
                        parsed = urllib.parse.urlparse(data_source)
                        path = parsed.path.strip('/')
                        
                        if '.' in path and '/' not in path:
                            last_dot_index = path.rfind('.')
                            if last_dot_index > 0:
                                database_name = path[:last_dot_index]
                                new_path = '/' + database_name
                                parsed = parsed._replace(path=new_path)
                                connection_url = urllib.parse.urlunparse(parsed)
                            else:
                                connection_url = data_source
                        else:
                            connection_url = data_source
                        
                        if connection_url.startswith('mysql://') and not connection_url.startswith('mysql+pymysql://'):
                            connection_url = connection_url.replace('mysql://', 'mysql+pymysql://', 1)
                        
                        engine = create_engine(connection_url)
                        inspector = inspect(engine)
                        
                        # 获取表列信息
                        column_info = inspector.get_columns(table_name)
                        for col in column_info:
                            col_type = 'string'
                            db_type_name = str(col['type']).upper()
                            if 'INT' in db_type_name:
                                col_type = 'integer'
                            elif 'FLOAT' in db_type_name or 'DOUBLE' in db_type_name or 'REAL' in db_type_name or 'DECIMAL' in db_type_name or 'NUMERIC' in db_type_name:
                                col_type = 'float'
                            elif 'DATE' in db_type_name or 'TIME' in db_type_name:
                                col_type = 'datetime'
                            elif 'BOOL' in db_type_name:
                                col_type = 'boolean'
                            columns.append({'name': col['name'], 'type': col_type})
                        engine.dispose()
                        
                elif asset.asset_type in ['csv', 'excel']:
                    # 文件类型
                    import pandas as pd
                    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
                    PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
                    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'output', 'data')
                    file_path = os.path.join(UPLOAD_FOLDER, asset.data_source)
                    
                    if os.path.exists(file_path):
                        if asset.asset_type == 'csv' or file_path.lower().endswith('.csv'):
                            df = pd.read_csv(file_path, nrows=0)
                        else:
                            df = pd.read_excel(file_path, nrows=0)
                        columns = [{'name': col, 'type': 'string'} for col in df.columns.tolist()]
                    else:
                        return jsonify({'status': 'error', 'message': f'文件不存在: {file_path}'}), 404
                        
                elif asset.asset_type == 'api':
                    # API类型暂时返回示例字段
                    columns = [
                        {'name': 'id', 'type': 'integer'},
                        {'name': 'data', 'type': 'string'}
                    ]
                    
            except Exception as e:
                print(f"读取字段失败: {e}")
                import traceback
                traceback.print_exc()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'asset_id': asset_id,
                    'asset_name': asset.name,
                    'columns': columns,
                    'total': len(columns)
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/assets', methods=['POST'])
def create_asset():
    """
    创建新资产
    
    Request Body:
        name: 资产名称（必填）
        data_source: 数据源路径/表名（必填）
        asset_type: 资产类型（csv/excel/database）
        owner: 负责人
        quality_score_weight: 质量权重（1-10）
        description: 描述
        
    Returns:
        JSON: 创建的资产信息
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({
                'status': 'error',
                'message': '资产名称不能为空'
            }), 400
        
        if not data.get('data_source'):
            return jsonify({
                'status': 'error',
                'message': '数据源不能为空'
            }), 400
        
        # 处理 SQLite 文件：复制到 output/data 目录
        data_source = data['data_source']
        asset_type = data.get('asset_type', 'csv')
        
        if asset_type == 'database' and data_source.startswith('sqlite:///'):
            # 提取原始文件路径
            sqlite_path = data_source.replace('sqlite:///', '')
            
            # 构建目标路径
            import shutil
            CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
            PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
            UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'output', 'data')
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # 生成唯一文件名
            import uuid
            original_filename = os.path.basename(sqlite_path)
            file_id = f"sqlite_{uuid.uuid4().hex}_{original_filename}"
            dest_path = os.path.join(UPLOAD_FOLDER, file_id)
            
            # 复制文件
            if os.path.exists(sqlite_path):
                shutil.copy2(sqlite_path, dest_path)
                # 更新 data_source 为相对路径
                data_source = file_id
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'SQLite 文件不存在: {sqlite_path}'
                }), 400
        
        session = get_db_session()
        try:
            asset = AssetManager.create_asset(
                session=session,
                name=data['name'],
                data_source=data_source,
                asset_type=asset_type,
                db_config=json.dumps(data.get('db_config')) if data.get('db_config') else None,
                owner=data.get('owner'),
                quality_score_weight=data.get('quality_score_weight', 5.0),
                description=data.get('description')
            )
            session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': asset.id,
                    'name': asset.name,
                    'data_source': asset.data_source,
                    'asset_type': asset.asset_type,
                    'created_at': asset.created_at.isoformat()
                },
                'message': '资产创建成功'
            }), 201
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/assets/<int:asset_id>', methods=['PUT'])
def update_asset(asset_id):
    """
    更新资产信息
    
    Args:
        asset_id: 资产ID
        
    Request Body:
        name: 资产名称
        owner: 负责人
        quality_score_weight: 质量权重
        is_active: 是否激活
        description: 描述
        
    Returns:
        JSON: 更新后的资产信息
    """
    try:
        data = request.get_json()
        
        # 处理 db_config 序列化
        if 'db_config' in data and data['db_config'] is not None:
            if isinstance(data['db_config'], dict):
                data['db_config'] = json.dumps(data['db_config'])
        
        session = get_db_session()
        try:
            asset = AssetManager.update_asset(session, asset_id, **data)
            session.commit()
            
            if not asset:
                return jsonify({
                    'status': 'error',
                    'message': f'资产 {asset_id} 不存在'
                }), 404
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': asset.id,
                    'name': asset.name,
                    'updated_at': asset.updated_at.isoformat()
                },
                'message': '资产更新成功'
            })
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/assets/<int:asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """
    删除资产（级联删除相关规则和异常数据）
    
    Args:
        asset_id: 资产ID
        
    Returns:
        JSON: 删除结果
    """
    try:
        session = get_db_session()
        try:
            success = AssetManager.delete_asset(session, asset_id)
            session.commit()
            
            if not success:
                return jsonify({
                    'status': 'error',
                    'message': f'资产 {asset_id} 不存在'
                }), 404
            
            return jsonify({
                'status': 'success',
                'message': '资产删除成功'
            })
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


# ==================== 规则管理 API ====================

@api_bp.route('/assets/<int:asset_id>/rules', methods=['GET'])
def list_rules(asset_id):
    """
    获取资产的规则列表
    
    Args:
        asset_id: 资产ID
        
    Query Parameters:
        is_active: 是否只查询激活的规则（true/false）
        
    Returns:
        JSON: 规则列表
    """
    try:
        session = get_db_session()
        try:
            is_active = request.args.get('is_active', None)
            if is_active is not None:
                is_active = is_active.lower() == 'true'
            
            rules = RuleManager.get_rules_by_asset(session, asset_id, is_active=is_active)
            
            result = []
            for rule in rules:
                result.append({
                    'id': rule.id,
                    'name': rule.name,
                    'column_name': rule.column_name,
                    'rule_type': rule.rule_type,
                    'rule_template': rule.rule_template,
                    'ge_expectation': rule.ge_expectation,
                    'parameters': rule.parameters,
                    'strength': rule.strength,
                    'enabled': rule.is_active,  # 前端使用enabled字段
                    'description': rule.description,
                    'created_at': rule.created_at.isoformat()
                })
            
            return jsonify({
                'status': 'success',
                'data': {
                    'rules': result,  # 前端期望data.rules
                    'count': len(result)
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/assets/<int:asset_id>/rules', methods=['POST'])
def create_rule(asset_id):
    """
    为资产创建规则
    
    Args:
        asset_id: 资产ID
        
    Request Body:
        name: 规则名称（必填）
        rule_type: 规则类型（必填）
        rule_template: 规则模板（必填）
        ge_expectation: GE期望类名（必填）
        column_name: 字段名
        parameters: 参数（JSON字符串）
        strength: 强度（strong/weak）
        description: 描述
        
    Returns:
        JSON: 创建的规则信息
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({
                'status': 'error',
                'message': '规则名称不能为空'
            }), 400
        
        required_fields = ['rule_type', 'rule_template', 'ge_expectation']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'{field} 不能为空'
                }), 400
        
        session = get_db_session()
        try:
            rule = RuleManager.create_rule(
                session=session,
                asset_id=asset_id,
                name=data['name'],
                rule_type=data['rule_type'],
                rule_template=data['rule_template'],
                ge_expectation=data['ge_expectation'],
                column_name=data.get('column_name'),
                parameters=data.get('parameters'),
                strength=data.get('strength', 'weak'),
                description=data.get('description')
            )
            session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': rule.id,
                    'name': rule.name,
                    'rule_type': rule.rule_type,
                    'strength': rule.strength,
                    'created_at': rule.created_at.isoformat()
                },
                'message': '规则创建成功'
            }), 201
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/rules/<int:rule_id>', methods=['GET'])
def get_rule(rule_id):
    """
    获取规则详情
    
    Args:
        rule_id: 规则ID
        
    Returns:
        JSON: 规则详细信息
    """
    try:
        session = get_db_session()
        try:
            rule = RuleManager.get_rule(session, rule_id)
            
            if not rule:
                return jsonify({
                    'status': 'error',
                    'message': f'规则 {rule_id} 不存在'
                }), 404
            
            return jsonify({
                'status': 'success',
                'data': rule.to_dict()
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/rules/<int:rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """
    更新规则
    
    Args:
        rule_id: 规则ID
        
    Request Body:
        name: 规则名称
        parameters: 参数
        strength: 强度
        is_active: 是否激活
        description: 描述
        
    Returns:
        JSON: 更新后的规则信息
    """
    try:
        data = request.get_json()
        
        session = get_db_session()
        try:
            rule = RuleManager.update_rule(session, rule_id, **data)
            session.commit()
            
            if not rule:
                return jsonify({
                    'status': 'error',
                    'message': f'规则 {rule_id} 不存在'
                }), 404
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': rule.id,
                    'name': rule.name,
                    'updated_at': rule.updated_at.isoformat()
                },
                'message': '规则更新成功'
            })
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """
    删除规则
    
    Args:
        rule_id: 规则ID
        
    Returns:
        JSON: 删除结果
    """
    try:
        session = get_db_session()
        try:
            success = RuleManager.delete_rule(session, rule_id)
            session.commit()
            
            if not success:
                return jsonify({
                    'status': 'error',
                    'message': f'规则 {rule_id} 不存在'
                }), 404
            
            return jsonify({
                'status': 'success',
                'message': '规则删除成功'
            })
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


# ==================== 校验执行 API ====================

@api_bp.route('/validations', methods=['POST'])
def execute_validation():
    """
    执行质量校验
    
    Request Body:
        asset_id: 资产ID（必填）
        rule_ids: 规则ID列表（可选，不传则执行所有激活规则）
        auto_archive: 是否自动归档异常数据（默认true）
        auto_create_issue: 是否自动创建问题工单（默认true）
        trigger_type: 触发方式 manual/scheduled/api（默认manual）
        
    Returns:
        JSON: 校验结果
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('asset_id'):
            return jsonify({
                'status': 'error',
                'message': 'asset_id 不能为空'
            }), 400
        
        asset_id = data['asset_id']
        rule_ids = data.get('rule_ids')
        auto_archive = data.get('auto_archive', True)
        auto_create_issue = data.get('auto_create_issue', True)
        trigger_type = data.get('trigger_type', 'manual')
        
        runner = QualityRunner()
        try:
            result = runner.run_asset_validation(
                asset_id=asset_id,
                rule_ids=rule_ids,
                auto_archive=auto_archive,
                auto_create_issue=auto_create_issue,
                trigger_type=trigger_type
            )

            return jsonify({
                'status': 'success',
                'data': result,
                'message': '校验执行完成'
            })
        finally:
            if runner.should_close_session:
                runner.session.close()
            
    except FileNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except Exception as e:
        return handle_error(e)


@api_bp.route('/validations/history', methods=['GET'])
def list_validation_history():
    """
    获取校验历史记录
    
    Query Parameters:
        asset_id: 资产ID（可选）
        page: 页码（默认1）
        per_page: 每页数量（默认20）
        
    Returns:
        JSON: 校验历史列表（按执行批次聚合）
    """
    try:
        session = get_db_session()
        try:
            asset_id = request.args.get('asset_id', type=int)
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            # 获取所有历史记录
            all_histories = ValidationHistoryManager.list_histories(
                session, asset_id=asset_id, page=1, per_page=1000  # 获取更多记录用于聚合
            )
            
            # 按 asset_id + start_time（精确到分钟）分组，识别执行批次
            from collections import defaultdict
            from datetime import datetime, timedelta
            
            batch_groups = defaultdict(list)
            for history in all_histories:
                # 使用 asset_id + start_time的分钟级时间戳作为批次标识
                time_key = history.start_time.strftime('%Y-%m-%d %H:%M') if history.start_time else 'unknown'
                batch_key = (history.asset_id, time_key)
                batch_groups[batch_key].append(history)
            
            # 转换为聚合结果
            result = []
            for (asset_id, time_key), histories in batch_groups.items():
                if not histories:
                    continue
                
                # 取第一条记录作为代表
                representative = histories[0]
                
                # 聚合统计
                total_rules = len(histories)
                passed_rules = sum(1 for h in histories if h.status == 'success')
                failed_rules = sum(1 for h in histories if h.status in ['failed', 'error'])
                success_rate = (passed_rules / total_rules * 100) if total_rules > 0 else 0
                
                result.append({
                    'id': representative.id,
                    'asset_id': representative.asset_id,
                    'asset_name': representative.asset.name if representative.asset else None,
                    'trigger_type': representative.trigger_type if hasattr(representative, 'trigger_type') else 'manual',
                    'start_time': representative.start_time.isoformat() if representative.start_time else None,
                    'end_time': max((h.end_time for h in histories if h.end_time), default=None).isoformat() if any(h.end_time for h in histories) else None,
                    'status': (
                        'success' if passed_rules == total_rules else
                        ('failed' if passed_rules == 0 else 'partial')
                    ),
                    'total_rules': total_rules,
                    'passed_rules': passed_rules,
                    'failed_rules': failed_rules,
                    'success_rate': success_rate,
                    'created_at': representative.created_at.isoformat() if representative.created_at else None
                })
            
            # 按开始时间降序排序
            result.sort(key=lambda x: x['start_time'] or '', reverse=True)
            
            # 分页
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_result = result[start_idx:end_idx]
            
            return jsonify({
                'status': 'success',
                'data': paginated_result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': len(result)
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/validations/history/<int:history_id>', methods=['GET'])
def get_validation_history(history_id):
    """
    获取校验历史详情
    
    Args:
        history_id: 校验历史ID
        
    Returns:
        JSON: 校验历史详细信息（包含聚合统计）
    """
    try:
        session = get_db_session()
        try:
            history = ValidationHistoryManager.get_history(session, history_id)
            
            if not history:
                return jsonify({
                    'status': 'error',
                    'message': f'校验历史 {history_id} 不存在'
                }), 404
            
            # 查询同一执行批次的所有规则记录（相同资产 + 相近时间）
            from datetime import timedelta
            
            # 定义时间窗口：前后5分钟内的记录视为同一批次
            time_window = timedelta(minutes=5)
            start_time = history.start_time
            
            if start_time:
                # 查询相同资产、时间相近的所有记录
                same_batch = session.query(ValidationHistory).filter(
                    ValidationHistory.asset_id == history.asset_id,
                    ValidationHistory.start_time >= start_time - time_window,
                    ValidationHistory.start_time <= start_time + time_window
                ).all()
            else:
                same_batch = [history]
            
            # 聚合统计
            total_rules = len(same_batch)
            passed_rules = sum(1 for h in same_batch if h.status == 'success')
            failed_rules = sum(1 for h in same_batch if h.status in ['failed', 'error'])
            success_rate = (passed_rules / total_rules * 100) if total_rules > 0 else 0
            
            # 确定整体状态
            # 1条规则：只有success或failed，没有partial
            # 多条规则：全部通过=success，至少1条通过但不是全部=partial，全部失败=failed
            if total_rules == 1:
                overall_status = 'success' if passed_rules == 1 else 'failed'
            else:
                if passed_rules == total_rules:
                    overall_status = 'success'
                elif passed_rules > 0:
                    overall_status = 'partial'
                else:
                    overall_status = 'failed'
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': history.id,
                    'asset_id': history.asset_id,
                    'asset_name': history.asset.name if history.asset else None,
                    'trigger_type': history.trigger_type if hasattr(history, 'trigger_type') else 'manual',
                    'start_time': history.start_time.isoformat() if history.start_time else None,
                    'end_time': history.end_time.isoformat() if history.end_time else None,
                    'status': overall_status,
                    'total_rules': total_rules,
                    'passed_rules': passed_rules,
                    'failed_rules': failed_rules,
                    'success_rate': success_rate,
                    'error_message': history.error_message,
                    'created_at': history.created_at.isoformat() if history.created_at else None
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/validations/history/<int:history_id>/rules', methods=['GET'])
def get_validation_rules(history_id):
    """
    获取校验历史中的规则校验结果列表
    
    Args:
        history_id: 校验历史聚合ID（一次执行的聚合ID）
        
    Returns:
        JSON: 规则校验结果列表
    """
    try:
        session = get_db_session()
        try:
            # 查询这一次执行的所有规则校验记录
            # 由于每一条规则对应一条validation_history记录，我们需要通过batch_key找到同一次执行的所有记录
            # batch_key = (asset_id, time_key) - 但我们不知道这个。换个思路：通过asset_id和相近时间查找
            
            # 先获取这条聚合记录对应的资产ID
            # 实际上，history_id这里是聚合后的代表ID，我们需要找到这个资产在这个时间段的所有记录
            representative = session.query(ValidationHistory).filter(ValidationHistory.id == history_id).first()
            
            if not representative:
                return jsonify({
                    'status': 'error',
                    'message': f'校验历史 {history_id} 不存在'
                }), 404
            
            # 查询同一个资产在同一分钟内的所有校验记录（同一次批量执行）
            from datetime import timedelta
            if representative.start_time:
                start_min = representative.start_time.replace(second=0)
                end_min = start_min + timedelta(minutes=1)
                histories = session.query(ValidationHistory)\
                    .filter(ValidationHistory.asset_id == representative.asset_id)\
                    .filter(ValidationHistory.start_time >= start_min)\
                    .filter(ValidationHistory.start_time <= end_min)\
                    .order_by(ValidationHistory.id.asc())\
                    .all()
            else:
                histories = [representative]
            
            # 构建结果
            rules = []
            for h in histories:
                rules.append({
                    'id': h.id,
                    'rule_id': h.rule_id,
                    'rule_name': h.rule.name if h.rule else '未知规则',
                    'rule_type': h.rule.rule_type if h.rule else 'unknown',
                    'column_name': h.rule.column_name if h.rule else None,
                    'strength': h.rule.strength if h.rule else 'weak',
                    'status': h.status,
                    'pass_rate': h.pass_rate,
                    'total_records': h.total_records,
                    'failed_records': h.failed_records,
                    'error_message': h.error_message
                })
            
            return jsonify({
                'status': 'success',
                'data': {
                    'history_id': history_id,
                    'rules': rules,
                    'total': len(rules)
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/validations/history/<int:history_id>/exceptions', methods=['GET'])
def get_validation_exceptions(history_id):
    """
    获取校验历史的异常数据
    
    Args:
        history_id: 校验历史ID
        rule_id: 规则ID（可选）
        page: 页码
        per_page: 每页数量
        
    Returns:
        JSON: 异常数据列表
    """
    try:
        rule_id = request.args.get('rule_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        session = get_db_session()
        try:
            # TODO: 实现获取异常数据的逻辑
            # 目前返回模拟数据
            exceptions = [
                {
                    'id': 1,
                    'row_number': 5,
                    'column_name': 'email',
                    'actual_value': 'invalid-email',
                    'expected_value': '有效邮箱格式'
                },
                {
                    'id': 2,
                    'row_number': 12,
                    'column_name': 'email',
                    'actual_value': '',
                    'expected_value': '非空'
                }
            ]
            
            return jsonify({
                'status': 'success',
                'data': {
                    'history_id': history_id,
                    'rule_id': rule_id,
                    'exceptions': exceptions,
                    'total': len(exceptions),
                    'page': page,
                    'per_page': per_page
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/validations/history/<int:history_id>/exceptions/download', methods=['GET'])
def download_validation_exceptions(history_id):
    """
    下载校验历史的异常数据
    
    Args:
        history_id: 校验历史ID
        rule_id: 规则ID（可选）
        
    Returns:
        CSV文件
    """
    try:
        rule_id = request.args.get('rule_id', type=int)
        
        # TODO: 实现下载异常数据的逻辑
        # 生成CSV文件并返回
        
        return jsonify({
            'status': 'success',
            'message': '下载功能开发中'
        })
        
    except Exception as e:
        return handle_error(e)


# ==================== 问题管理 API ====================

@api_bp.route('/issues', methods=['GET'])
def list_issues():
    """
    获取问题列表
    
    Query Parameters:
        asset_id: 资产ID（可选）
        status: 状态过滤（pending/processing/resolved/closed）
        priority: 优先级过滤（high/medium/low）
        page: 页码（默认1）
        per_page: 每页数量（默认20）
        
    Returns:
        JSON: 问题列表
    """
    try:
        session = get_db_session()
        try:
            asset_id = request.args.get('asset_id', type=int)
            status = request.args.get('status')
            priority = request.args.get('priority')
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            issues = IssueManager.list_issues(
                session,
                asset_id=asset_id,
                status=status,
                priority=priority,
                page=page,
                per_page=per_page
            )
            
            result = []
            for issue in issues:
                result.append({
                    'id': issue.id,
                    'asset_id': issue.asset_id,
                    'asset_name': issue.asset.name if issue.asset else None,
                    'rule_id': issue.rule_id,
                    'rule_name': issue.rule.name if issue.rule else None,
                    'title': issue.title,
                    'description': issue.description,
                    'status': issue.status,
                    'priority': issue.priority,
                    'assignee': issue.assignee,
                    'validation_history_id': issue.validation_history_id,
                    'created_at': issue.created_at.isoformat(),
                    'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None
                })
            
            return jsonify({
                'status': 'success',
                'data': result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': len(result)
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/issues', methods=['POST'])
def create_issue():
    """
    创建新的问题工单
    
    Request Body:
        asset_id: 关联资产ID（必填）
        rule_id: 关联规则ID（可选）
        title: 问题标题（必填）
        description: 问题描述（可选）
        priority: 优先级 high/medium/low（默认 medium）
        assignee: 负责人（可选）
        contact_info: 联系人信息（可选）
        validation_history_id: 关联校验记录ID（可选，自动创建时会填写）
        
    Returns:
        JSON: 创建成功后的问题信息
    """
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data or 'asset_id' not in data or not data.get('title'):
            return jsonify({
                'status': 'error',
                'message': '缺少必填字段: asset_id 和 title'
            }), 400
        
        session = get_db_session()
        try:
            issue = IssueManager.create_issue(
                session,
                asset_id=data['asset_id'],
                rule_id=data.get('rule_id'),
                title=data['title'],
                description=data.get('description'),
                priority=data.get('priority', 'medium'),
                assignee=data.get('assignee'),
                contact_info=data.get('contact_info'),
                validation_history_id=data.get('validation_history_id')
            )
            session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': issue.id,
                    'title': issue.title,
                    'asset_id': issue.asset_id,
                    'rule_id': issue.rule_id,
                    'message': '问题创建成功'
                }
            }), 201
        except ValueError as e:
            session.rollback()
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)

@api_bp.route('/assets/<int:asset_id>/validations', methods=['GET'])
def get_asset_validations(asset_id):
    """
    获取指定资产的校验历史
    """
    try:
        session = get_db_session()
        try:
            limit = request.args.get('limit', 20, type=int)
            from models.base import ValidationHistory
            histories = session.query(ValidationHistory)\
                .filter_by(asset_id=asset_id)\
                .order_by(ValidationHistory.created_at.desc())\
                .limit(limit)\
                .all()

            result = []
            for h in histories:
                result.append({
                    'id': h.id,
                    'asset_id': h.asset_id,
                    'status': h.status,
                    'pass_rate': h.pass_rate,
                    'total_records': h.total_records,
                    'failed_records': h.failed_records,
                    'trigger_type': getattr(h, 'trigger_type', 'manual'),
                    'executed_at': h.created_at.isoformat() if h.created_at else None,
                    'created_at': h.created_at.isoformat() if h.created_at else None
                })
            
            return jsonify({
                'status': 'success',
                'data': {
                    'validations': result
                }
            })
        finally:
            session.close()
    except Exception as e:
        return handle_error(e)

@api_bp.route('/assets/<int:asset_id>/issues', methods=['GET'])
def get_asset_issues_by_asset(asset_id):
    """
    获取指定资产的问题记录
    """
    try:
        session = get_db_session()
        try:
            limit = request.args.get('limit', 20, type=int)
            from models.base import Issue
            issues = session.query(Issue)\
                .filter_by(asset_id=asset_id)\
                .order_by(Issue.created_at.desc())\
                .limit(limit)\
                .all()
            result = []
            for issue in issues:
                result.append({
                    'id': issue.id,
                    'asset_id': issue.asset_id,
                    'rule_id': issue.rule_id,
                    'title': issue.title,
                    'description': issue.description,
                    'status': issue.status,
                    'priority': issue.priority,
                    'assignee': issue.assignee,
                    'created_at': issue.created_at.isoformat() if issue.created_at else None
                })
            return jsonify({
                'status': 'success',
                'data': {
                    'issues': result
                }
            })
        finally:
            session.close()
    except Exception as e:
        return handle_error(e)


@api_bp.route('/issues/<int:issue_id>', methods=['GET'])
def get_issue(issue_id):
    """
    获取问题详情
    
    Args:
        issue_id: 问题ID
        
    Returns:
        JSON: 问题详细信息
    """
    try:
        session = get_db_session()
        try:
            issue = IssueManager.get_issue(session, issue_id)
            
            if not issue:
                return jsonify({
                    'status': 'error',
                    'message': f'问题 {issue_id} 不存在'
                }), 404
            
            # 获取相关的异常数据
            exceptions = ExceptionDataManager.get_exceptions_by_issue(session, issue_id)
            exception_data = [{
                'id': exc.id,
                'record_index': exc.record_index,
                'exception_value': exc.exception_value,
                'created_at': exc.created_at.isoformat()
            } for exc in exceptions]
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': issue.id,
                    'asset_id': issue.asset_id,
                    'asset_name': issue.asset.name if issue.asset else None,
                    'rule_id': issue.rule_id,
                    'rule_name': issue.rule.name if issue.rule else None,
                    'title': issue.title,
                    'description': issue.description,
                    'status': issue.status,
                    'priority': issue.priority,
                    'assignee': issue.assignee,
                    'resolution_note': issue.resolution_note,
                    'validation_history_id': issue.validation_history_id,
                    'created_at': issue.created_at.isoformat(),
                    'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None,
                    'exceptions': exception_data,
                    'exception_count': len(exception_data)
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/issues/<int:issue_id>/status', methods=['PUT'])
def update_issue_status(issue_id):
    """
    更新问题状态（状态流转）
    
    Args:
        issue_id: 问题ID
        
    Request Body:
        status: 新状态（pending/processing/resolved/closed）（必填）
        assignee: 处理人
        resolution_note: 解决说明
        
    Returns:
        JSON: 更新后的问题信息
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('status'):
            return jsonify({
                'status': 'error',
                'message': 'status 不能为空'
            }), 400
        
        session = get_db_session()
        try:
            issue = IssueManager.update_issue_status(
                session,
                issue_id,
                status=data['status'],
                assignee=data.get('assignee'),
                resolution_note=data.get('resolution_note')
            )
            session.commit()
            
            if not issue:
                return jsonify({
                    'status': 'error',
                    'message': f'问题 {issue_id} 不存在'
                }), 404
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': issue.id,
                    'status': issue.status,
                    'assignee': issue.assignee,
                    'resolution_note': issue.resolution_note,
                    'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None,
                    'updated_at': issue.updated_at.isoformat()
                },
                'message': '问题状态更新成功'
            })
        except ValueError as e:
            session.rollback()
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/issues/<int:issue_id>/recheck', methods=['POST'])
def recheck_issue(issue_id):
    """
    重新校验问题（验证问题是否已解决）
    
    Args:
        issue_id: 问题ID
        
    Returns:
        JSON: 重新校验结果
    """
    try:
        session = get_db_session()
        try:
            issue = IssueManager.get_issue(session, issue_id)
            
            if not issue:
                return jsonify({
                    'status': 'error',
                    'message': f'问题 {issue_id} 不存在'
                }), 404
            
            if not issue.rule:
                return jsonify({
                    'status': 'error',
                    'message': '问题关联的规则不存在'
                }), 400
            
            # 执行单个规则的校验
            runner = QualityRunner(session=session)
            try:
                result = runner.run_asset_validation(
                    asset_id=issue.asset_id,
                    rule_ids=[issue.rule_id],
                    auto_archive=False,
                    auto_create_issue=False
                )
                
                rule_result = result['results'][0] if result['results'] else None
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'issue_id': issue_id,
                        'rule_passed': rule_result['success'] if rule_result else False,
                        'success_rate': rule_result.get('success_rate', 0),
                        'message': '校验通过，问题可能已解决' if rule_result and rule_result['success'] else '校验仍失败，问题依然存在'
                    }
                })
            finally:
                if runner.should_close_session:
                    runner.session.close()
                    
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


# ==================== 统计分析 API ====================

@api_bp.route('/statistics/overview', methods=['GET'])
def get_statistics_overview():
    """
    获取统计概览
    
    Returns:
        JSON: 统计数据
    """
    try:
        session = get_db_session()
        try:
            # 资产统计
            total_assets = session.query(Asset).filter_by(is_active=True).count()
            
            # 规则统计
            total_rules = session.query(Rule).filter_by(is_active=True).count()
            strong_rules = session.query(Rule).filter_by(is_active=True, strength='strong').count()
            weak_rules = session.query(Rule).filter_by(is_active=True, strength='weak').count()
            
            # 问题统计
            total_issues = session.query(Issue).count()
            pending_issues = session.query(Issue).filter_by(status='pending').count()
            processing_issues = session.query(Issue).filter_by(status='processing').count()
            resolved_issues = session.query(Issue).filter_by(status='resolved').count()
            
            # 校验历史统计
            total_validations = session.query(ValidationHistory).count()
            successful_validations = session.query(ValidationHistory).filter_by(status='success').count()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'assets': {
                        'total': total_assets
                    },
                    'rules': {
                        'total': total_rules,
                        'strong': strong_rules,
                        'weak': weak_rules
                    },
                    'issues': {
                        'total': total_issues,
                        'pending': pending_issues,
                        'processing': processing_issues,
                        'resolved': resolved_issues
                    },
                    'validations': {
                        'total': total_validations,
                        'successful': successful_validations
                    }
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


@api_bp.route('/statistics/trend', methods=['GET'])
def get_validation_trend():
    """
    获取最近7天的校验趋势数据
    
    Returns:
        JSON: 趋势数据
    """
    try:
        session = get_db_session()
        try:
            from datetime import datetime, timedelta
            
            # 获取最近7天的数据
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=6)
            
            # 按日期统计成功和失败的校验次数
            trend_data = []
            current_date = start_date
            
            while current_date <= end_date:
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                # 统计当天成功校验
                success_count = session.query(ValidationHistory).filter(
                    ValidationHistory.start_time >= day_start,
                    ValidationHistory.start_time <= day_end,
                    ValidationHistory.status == 'success'
                ).count()
                
                # 统计当天失败校验
                failed_count = session.query(ValidationHistory).filter(
                    ValidationHistory.start_time >= day_start,
                    ValidationHistory.start_time <= day_end,
                    ValidationHistory.status == 'failed'
                ).count()
                
                trend_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'day_label': current_date.strftime('%a'),
                    'success': success_count,
                    'failed': failed_count
                })
                
                current_date += timedelta(days=1)
            
            return jsonify({
                'status': 'success',
                'data': {
                    'trend': trend_data,
                    'days': 7
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        return handle_error(e)


# ==================== 第四阶段：自动化与集成 API ====================

# --- 定时任务管理 API ---

@api_bp.route('/scheduler/jobs', methods=['GET'])
def list_scheduled_jobs():
    """获取所有定时任务列表"""
    if not SCHEDULER_ENABLED:
        return jsonify({
            'status': 'error',
            'message': '调度器未启用'
        }), 503
    
    try:
        jobs = scheduler.list_all_jobs()
        return jsonify({
            'status': 'success',
            'data': {
                'jobs': jobs,
                'total': len(jobs)
            }
        })
    except Exception as e:
        return handle_error(e)


@api_bp.route('/assets/<int:asset_id>/schedule', methods=['POST'])
def schedule_asset_validation(asset_id):
    """为资产创建定时校验任务"""
    if not SCHEDULER_ENABLED:
        return jsonify({
            'status': 'error',
            'message': '调度器未启用'
        }), 503
    
    try:
        data = request.get_json()
        
        schedule_type = data.get('schedule_type', 'interval')
        interval_hours = data.get('interval_hours', 24)
        cron_expression = data.get('cron_expression')
        rule_ids = data.get('rule_ids')
        auto_archive = data.get('auto_archive', True)
        auto_create_issue = data.get('auto_create_issue', True)
        
        job_id = scheduler.add_asset_validation_job(
            asset_id=asset_id,
            schedule_type=schedule_type,
            interval_hours=interval_hours,
            cron_expression=cron_expression,
            rule_ids=rule_ids,
            auto_archive=auto_archive,
            auto_create_issue=auto_create_issue
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'job_id': job_id,
                'asset_id': asset_id,
                'schedule_type': schedule_type
            }
        })
    except Exception as e:
        return handle_error(e)


@api_bp.route('/assets/<int:asset_id>/schedule', methods=['DELETE'])
def remove_asset_schedule(asset_id):
    """移除资产的定时校验任务"""
    if not SCHEDULER_ENABLED:
        return jsonify({
            'status': 'error',
            'message': '调度器未启用'
        }), 503
    
    try:
        scheduler.remove_job(asset_id)
        return jsonify({
            'status': 'success',
            'message': f'已移除资产 {asset_id} 的定时任务'
        })
    except Exception as e:
        return handle_error(e)


@api_bp.route('/assets/<int:asset_id>/schedule/status', methods=['GET'])
def get_schedule_status(asset_id):
    """获取资产的调度状态"""
    if not SCHEDULER_ENABLED:
        return jsonify({
            'status': 'error',
            'message': '调度器未启用'
        }), 503
    
    try:
        status = scheduler.get_job_status(asset_id)
        return jsonify({
            'status': 'success',
            'data': status
        })
    except Exception as e:
        return handle_error(e)


# --- 告警配置 API ---

@api_bp.route('/alerts/configure', methods=['POST'])
def configure_alerts():
    """配置告警渠道"""
    if not ALERT_ENABLED:
        return jsonify({
            'status': 'error',
            'message': '告警模块未启用'
        }), 503
    
    try:
        config = request.get_json()
        init_default_alerts(config)
        
        return jsonify({
            'status': 'success',
            'data': {
                'channels': list(alert_manager.channels.keys())
            }
        })
    except Exception as e:
        return handle_error(e)


@api_bp.route('/alerts/test', methods=['POST'])
def test_alert():
    """测试告警发送"""
    if not ALERT_ENABLED:
        return jsonify({
            'status': 'error',
            'message': '告警模块未启用'
        }), 503
    
    try:
        data = request.get_json()
        title = data.get('title', '测试告警')
        message = data.get('message', '这是一条测试告警消息')
        channels = data.get('channels')  # None 表示发送到所有渠道
        
        if channels:
            results = alert_manager.send_alert(channels, title, message)
        else:
            results = alert_manager.send_all(title, message)
        
        return jsonify({
            'status': 'success',
            'data': {
                'results': results
            }
        })
    except Exception as e:
        return handle_error(e)


@api_bp.route('/alerts/channels', methods=['GET'])
def list_alert_channels():
    """获取已配置的告警渠道"""
    if not ALERT_ENABLED:
        return jsonify({
            'status': 'error',
            'message': '告警模块未启用'
        }), 503
    
    try:
        channels = list(alert_manager.channels.keys())
        return jsonify({
            'status': 'success',
            'data': {
                'channels': channels,
                'total': len(channels)
            }
        })
    except Exception as e:
        return handle_error(e)


# --- 认证 API ---

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录（生成 Token）"""
    if not AUTH_ENABLED:
        return jsonify({
            'status': 'error',
            'message': '认证模块未启用'
        }), 503
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # TODO: 这里应该验证用户名密码（从数据库或 LDAP）
        # 目前简化处理，只要提供用户名就生成 Token
        if not username:
            return jsonify({
                'status': 'error',
                'message': '缺少用户名'
            }), 400
        
        # 生成 Token
        token = jwt_auth.generate_token(
            user_id='1',  # 简化：固定用户ID
            username=username,
            role=data.get('role', 'user')
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'token': token,
                'username': username,
                'expires_in': f'{jwt_auth.token_expiry_hours}小时'
            }
        })
    except Exception as e:
        return handle_error(e)


@api_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """刷新 Token"""
    if not AUTH_ENABLED:
        return jsonify({
            'status': 'error',
            'message': '认证模块未启用'
        }), 503
    
    try:
        data = request.get_json()
        old_token = data.get('token')
        
        if not old_token:
            return jsonify({
                'status': 'error',
                'message': '缺少 Token'
            }), 400
        
        new_token = jwt_auth.refresh_token(old_token)
        
        return jsonify({
            'status': 'success',
            'data': {
                'token': new_token
            }
        })
    except Exception as e:
        return handle_error(e)


@api_bp.route('/auth/verify', methods=['POST'])
def verify_token():
    """验证 Token"""
    if not AUTH_ENABLED:
        return jsonify({
            'status': 'error',
            'message': '认证模块未启用'
        }), 503
    
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({
                'status': 'error',
                'message': '缺少 Token'
            }), 400
        
        payload = jwt_auth.verify_token(token)
        
        return jsonify({
            'status': 'success',
            'data': {
                'valid': True,
                'user': {
                    'user_id': payload['user_id'],
                    'username': payload['username'],
                    'role': payload.get('role', 'user')
                },
                'expires_at': datetime.fromtimestamp(payload['exp']).isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Token 无效: {str(e)}'
        }), 401


# 注册蓝图
def register_api(app):
    """注册 API 蓝图到 Flask 应用"""
    app.register_blueprint(api_bp)
