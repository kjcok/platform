"""
DataQ 质量治理工作台 - RESTful API
提供资产、规则、校验执行、问题管理的完整接口
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from datetime import datetime
import json
import traceback

# 导入数据库工具和执行引擎
from models.managers import (
    get_session, AssetManager, RuleManager, 
    ValidationHistoryManager, IssueManager, ExceptionDataManager
)
from engine.quality_runner import QualityRunner, StrongRuleFailedException

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
                result.append({
                    'id': asset.id,
                    'name': asset.name,
                    'data_source': asset.data_source,
                    'asset_type': asset.asset_type,
                    'owner': asset.owner,
                    'quality_score_weight': asset.quality_score_weight,
                    'is_active': asset.is_active,
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
                'column_name': rule.column_name,
                'strength': rule.strength,
                'is_active': rule.is_active
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
        
        session = get_db_session()
        try:
            asset = AssetManager.create_asset(
                session=session,
                name=data['name'],
                data_source=data['data_source'],
                asset_type=data.get('asset_type', 'csv'),
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
                    'is_active': rule.is_active,
                    'description': rule.description,
                    'created_at': rule.created_at.isoformat()
                })
            
            return jsonify({
                'status': 'success',
                'data': result,
                'count': len(result)
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
        
        runner = QualityRunner()
        try:
            result = runner.run_asset_validation(
                asset_id=asset_id,
                rule_ids=rule_ids,
                auto_archive=auto_archive,
                auto_create_issue=auto_create_issue
            )
            
            return jsonify({
                'status': 'success',
                'data': result,
                'message': '校验执行完成'
            })
        except StrongRuleFailedException as e:
            # 强规则失败，返回特殊状态
            return jsonify({
                'status': 'strong_rule_failed',
                'message': str(e),
                'failed_rules': e.failed_rules,
                'data': {
                    'validation_history_id': getattr(e, 'validation_history_id', None)
                }
            }), 409
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
        JSON: 校验历史列表
    """
    try:
        session = get_db_session()
        try:
            asset_id = request.args.get('asset_id', type=int)
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            histories = ValidationHistoryManager.list_histories(
                session, asset_id=asset_id, page=page, per_page=per_page
            )
            
            result = []
            for history in histories:
                result.append({
                    'id': history.id,
                    'asset_id': history.asset_id,
                    'asset_name': history.asset.name if history.asset else None,
                    'start_time': history.start_time.isoformat(),
                    'end_time': history.end_time.isoformat() if history.end_time else None,
                    'status': history.status,
                    'total_rules': history.total_rules,
                    'passed_rules': history.passed_rules,
                    'failed_rules': history.failed_rules,
                    'success_rate': float(history.success_rate) if history.success_rate else None,
                    'has_strong_failure': history.has_strong_failure,
                    'created_at': history.created_at.isoformat()
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


@api_bp.route('/validations/history/<int:history_id>', methods=['GET'])
def get_validation_history(history_id):
    """
    获取校验历史详情
    
    Args:
        history_id: 校验历史ID
        
    Returns:
        JSON: 校验历史详细信息
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
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': history.id,
                    'asset_id': history.asset_id,
                    'asset_name': history.asset.name if history.asset else None,
                    'start_time': history.start_time.isoformat(),
                    'end_time': history.end_time.isoformat() if history.end_time else None,
                    'status': history.status,
                    'total_rules': history.total_rules,
                    'passed_rules': history.passed_rules,
                    'failed_rules': history.failed_rules,
                    'success_rate': float(history.success_rate) if history.success_rate else None,
                    'has_strong_failure': history.has_strong_failure,
                    'error_message': history.error_message,
                    'created_at': history.created_at.isoformat()
                }
            })
        finally:
            session.close()
            
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
            successful_validations = session.query(ValidationHistory).filter_by(status='completed').count()
            
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
