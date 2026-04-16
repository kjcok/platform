"""
数据库操作工具类
提供常用的CRUD操作
"""
from datetime import datetime
from sqlalchemy.orm import Session
from models.base import Asset, Rule, ValidationHistory, Issue, ExceptionData, get_session


class AssetManager:
    """资产管理器"""
    
    @staticmethod
    def create_asset(session: Session, name: str, data_source: str, 
                    asset_type: str = 'table', owner: str = None, 
                    description: str = None, quality_score_weight: float = 1.0):
        """创建资产"""
        asset = Asset(
            name=name,
            data_source=data_source,
            asset_type=asset_type,
            owner=owner,
            description=description,
            quality_score_weight=quality_score_weight,
            is_active=True
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)
        return asset
    
    @staticmethod
    def get_asset(session: Session, asset_id: int):
        """获取单个资产"""
        return session.query(Asset).filter(Asset.id == asset_id).first()
    
    @staticmethod
    def get_all_assets(session: Session, is_active: bool = None):
        """获取所有资产"""
        query = session.query(Asset)
        if is_active is not None:
            query = query.filter(Asset.is_active == is_active)
        return query.all()
    
    @staticmethod
    def list_assets(session: Session, page: int = 1, per_page: int = 20, is_active: bool = True):
        """获取资产列表（支持分页）"""
        query = session.query(Asset)
        if is_active:
            query = query.filter(Asset.is_active == True)
        
        offset = (page - 1) * per_page
        return query.order_by(Asset.created_at.desc()).offset(offset).limit(per_page).all()
    
    @staticmethod
    def update_asset(session: Session, asset_id: int, **kwargs):
        """更新资产"""
        asset = session.query(Asset).filter(Asset.id == asset_id).first()
        if asset:
            for key, value in kwargs.items():
                if hasattr(asset, key):
                    setattr(asset, key, value)
            asset.updated_at = datetime.now()
            session.commit()
            session.refresh(asset)
        return asset
    
    @staticmethod
    def delete_asset(session: Session, asset_id: int):
        """删除资产（级联删除相关规则、记录等）"""
        asset = session.query(Asset).filter(Asset.id == asset_id).first()
        if asset:
            session.delete(asset)
            session.commit()
            return True
        return False


class RuleManager:
    """规则管理器"""
    
    @staticmethod
    def create_rule(session: Session, asset_id: int, name: str, rule_type: str,
                   rule_template: str, ge_expectation: str, strength: str = 'weak',
                   column_name: str = None, parameters: str = None,
                   description: str = None, is_active: bool = True):
        """创建规则"""
        rule = Rule(
            asset_id=asset_id,
            name=name,
            column_name=column_name,
            rule_type=rule_type,
            rule_template=rule_template,
            ge_expectation=ge_expectation,
            parameters=parameters,
            strength=strength,
            description=description,
            is_active=is_active
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule
    
    @staticmethod
    def get_rule(session: Session, rule_id: int):
        """获取单个规则"""
        return session.query(Rule).filter(Rule.id == rule_id).first()
    
    @staticmethod
    def get_rules_by_asset(session: Session, asset_id: int, is_active: bool = None):
        """获取资产的所有规则"""
        query = session.query(Rule).filter(Rule.asset_id == asset_id)
        if is_active is not None:
            query = query.filter(Rule.is_active == is_active)
        return query.all()
    
    @staticmethod
    def update_rule(session: Session, rule_id: int, **kwargs):
        """更新规则"""
        rule = session.query(Rule).filter(Rule.id == rule_id).first()
        if rule:
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            rule.updated_at = datetime.now()
            session.commit()
            session.refresh(rule)
        return rule
    
    @staticmethod
    def delete_rule(session: Session, rule_id: int):
        """删除规则"""
        rule = session.query(Rule).filter(Rule.id == rule_id).first()
        if rule:
            session.delete(rule)
            session.commit()
            return True
        return False


class ValidationHistoryManager:
    """校验历史管理器"""
    
    @staticmethod
    def create_history(session: Session, asset_id: int, rule_id: int = None, 
                      start_time: datetime = None, **kwargs):
        """创建校验历史记录"""
        history = ValidationHistory(
            asset_id=asset_id,
            rule_id=rule_id,
            start_time=start_time or datetime.now(),
            status='running'
        )
        # 支持额外参数
        for key, value in kwargs.items():
            if hasattr(history, key):
                setattr(history, key, value)
        session.add(history)
        session.commit()
        session.refresh(history)
        return history
    
    @staticmethod
    def update_history(session: Session, history_id: int, **kwargs):
        """更新校验历史"""
        history = session.query(ValidationHistory).filter(ValidationHistory.id == history_id).first()
        if history:
            for key, value in kwargs.items():
                if hasattr(history, key):
                    setattr(history, key, value)
            session.commit()
            session.refresh(history)
        return history
    
    @staticmethod
    def get_history(session: Session, history_id: int):
        """获取单个校验历史"""
        return session.query(ValidationHistory).filter(ValidationHistory.id == history_id).first()
    
    @staticmethod
    def get_history_by_asset(session: Session, asset_id: int, limit: int = 10):
        """获取资产的校验历史"""
        return session.query(ValidationHistory).filter(
            ValidationHistory.asset_id == asset_id
        ).order_by(ValidationHistory.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def list_histories(session: Session, asset_id: int = None, page: int = 1, per_page: int = 20):
        """获取校验历史列表（支持分页和过滤）"""
        query = session.query(ValidationHistory)
        if asset_id:
            query = query.filter(ValidationHistory.asset_id == asset_id)
        
        offset = (page - 1) * per_page
        return query.order_by(ValidationHistory.created_at.desc()).offset(offset).limit(per_page).all()
    
    @staticmethod
    def delete_history(session: Session, history_id: int):
        """删除校验历史"""
        history = session.query(ValidationHistory).filter(ValidationHistory.id == history_id).first()
        if history:
            session.delete(history)
            session.commit()
            return True
        return False


class IssueManager:
    """问题管理器"""
    
    @staticmethod
    def create_issue(session: Session, asset_id: int, title: str, issue_type: str = 'system_detected',
                    rule_id: int = None, validation_history_id: int = None,
                    description: str = None, priority: str = 'medium',
                    assignee: str = None, reporter: str = None,
                    contact_info: str = None, attachments: str = None,
                    status: str = 'pending'):
        """创建问题"""
        issue = Issue(
            asset_id=asset_id,
            rule_id=rule_id,
            validation_history_id=validation_history_id,
            issue_type=issue_type,
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee=assignee,
            reporter=reporter,
            contact_info=contact_info,
            attachments=attachments
        )
        session.add(issue)
        session.commit()
        session.refresh(issue)
        return issue
    
    @staticmethod
    def get_issue(session: Session, issue_id: int):
        """获取单个问题"""
        return session.query(Issue).filter(Issue.id == issue_id).first()
    
    @staticmethod
    def get_issues_by_status(session: Session, status: str, limit: int = 50):
        """按状态获取问题"""
        return session.query(Issue).filter(
            Issue.status == status
        ).order_by(Issue.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def list_issues(session: Session, asset_id: int = None, status: str = None,
                   priority: str = None, page: int = 1, per_page: int = 20):
        """获取问题列表（支持分页和过滤）"""
        query = session.query(Issue)
        if asset_id:
            query = query.filter(Issue.asset_id == asset_id)
        if status:
            query = query.filter(Issue.status == status)
        if priority:
            query = query.filter(Issue.priority == priority)
        
        offset = (page - 1) * per_page
        return query.order_by(Issue.created_at.desc()).offset(offset).limit(per_page).all()
    
    @staticmethod
    def update_issue_status(session: Session, issue_id: int, new_status: str = None,
                           status: str = None, assignee: str = None,
                           resolution_note: str = None):
        """更新问题状态"""
        # 兼容新旧参数名
        final_status = status or new_status
        
        issue = session.query(Issue).filter(Issue.id == issue_id).first()
        if issue:
            # 状态流转验证
            if final_status and final_status != issue.status:
                valid_transitions = {
                    'pending': ['processing'],
                    'processing': ['resolved', 'pending'],
                    'resolved': ['closed', 'processing'],
                    'closed': []
                }
                if final_status not in valid_transitions.get(issue.status, []):
                    raise ValueError(
                        f"Invalid status transition from '{issue.status}' to '{final_status}'. "
                        f"Valid transitions: {valid_transitions.get(issue.status, [])}"
                    )
            
            if final_status:
                issue.status = final_status
                if final_status == 'resolved':
                    issue.resolved_at = datetime.now()
            if assignee:
                issue.assignee = assignee
            if resolution_note:
                issue.resolution_note = resolution_note
            issue.updated_at = datetime.now()
            session.commit()
            session.refresh(issue)
        return issue
    
    @staticmethod
    def get_issues_by_assignee(session: Session, assignee: str, status: str = None):
        """获取负责人的问题"""
        query = session.query(Issue).filter(Issue.assignee == assignee)
        if status:
            query = query.filter(Issue.status == status)
        return query.order_by(Issue.created_at.desc()).all()
    
    @staticmethod
    def delete_issue(session: Session, issue_id: int):
        """删除问题"""
        issue = session.query(Issue).filter(Issue.id == issue_id).first()
        if issue:
            session.delete(issue)
            session.commit()
            return True
        return False


class ExceptionDataManager:
    """异常数据管理器"""
    
    @staticmethod
    def add_exception(session: Session, validation_history_id: int, asset_id: int,
                     rule_id: int, row_number: int = None, column_name: str = None,
                     actual_value: str = None, expected_value: str = None,
                     error_detail: str = None, full_record: str = None):
        """添加异常数据（兼容旧接口）"""
        exception = ExceptionData(
            validation_history_id=validation_history_id,
            asset_id=asset_id,
            rule_id=rule_id,
            row_number=row_number,
            column_name=column_name,
            actual_value=actual_value,
            expected_value=expected_value,
            error_detail=error_detail,
            full_record=full_record
        )
        session.add(exception)
        session.commit()
        session.refresh(exception)
        return exception
    
    @staticmethod
    def archive_exception(session: Session, asset_id: int, rule_id: int,
                         validation_history_id: int, issue_id: int = None,
                         record_index: int = None, field_name: str = None,
                         exception_value: str = None):
        """归档异常数据（新接口，支持 issue_id）"""
        exception = ExceptionData(
            validation_history_id=validation_history_id,
            asset_id=asset_id,
            rule_id=rule_id,
            issue_id=issue_id,
            row_number=record_index,
            column_name=field_name,
            actual_value=exception_value
        )
        session.add(exception)
        session.commit()
        session.refresh(exception)
        return exception
    
    @staticmethod
    def get_exceptions_by_history(session: Session, validation_history_id: int, limit: int = 100):
        """获取校验历史的异常数据"""
        return session.query(ExceptionData).filter(
            ExceptionData.validation_history_id == validation_history_id
        ).limit(limit).all()
    
    @staticmethod
    def get_exceptions_by_issue(session: Session, issue_id: int, limit: int = 100):
        """根据问题ID获取异常数据"""
        return session.query(ExceptionData).filter(
            ExceptionData.issue_id == issue_id
        ).limit(limit).all()
    
    @staticmethod
    def count_exceptions_by_history(session: Session, validation_history_id: int):
        """统计校验历史的异常数量"""
        return session.query(ExceptionData).filter(
            ExceptionData.validation_history_id == validation_history_id
        ).count()
    
    @staticmethod
    def delete_exceptions_by_rule(session: Session, rule_id: int):
        """删除规则相关的异常数据"""
        count = session.query(ExceptionData).filter(
            ExceptionData.rule_id == rule_id
        ).delete()
        session.commit()
        return count
