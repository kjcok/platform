"""
数据质量评估平台 - 数据库模型
定义核心元数据表结构
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# 获取项目根目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # src/backend
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))  # platform

# 数据库配置
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'config', 'dataq.db')
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# 创建引擎和会话
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Asset(Base):
    """
    对象表 (Asset)
    记录要监控的数据资产（表、文件等）
    """
    __tablename__ = 'assets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False, comment='资产名称（表名/文件名）')
    asset_type = Column(String(50), nullable=False, default='table', 
                       comment='资产类型: table/csv/excel/database')
    data_source = Column(String(512), nullable=False, comment='数据源路径或连接信息')
    owner = Column(String(256), nullable=True, comment='质量负责人')
    description = Column(Text, nullable=True, comment='资产描述')
    quality_score_weight = Column(Float, default=1.0, comment='质量分权重 (1-10)')
    is_active = Column(Boolean, default=True, comment='是否启用监控')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    rules = relationship('Rule', back_populates='asset', cascade='all, delete-orphan')
    validation_history = relationship('ValidationHistory', back_populates='asset', cascade='all, delete-orphan')
    issues = relationship('Issue', back_populates='asset', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'asset_type': self.asset_type,
            'data_source': self.data_source,
            'owner': self.owner,
            'description': self.description,
            'quality_score_weight': self.quality_score_weight,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Rule(Base):
    """
    规则表 (Rule)
    记录质量校验规则的配置
    """
    __tablename__ = 'rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False, comment='关联的资产ID')
    name = Column(String(256), nullable=False, comment='规则名称')
    column_name = Column(String(256), nullable=True, comment='校验字段名，NULL表示全表级别')
    rule_type = Column(String(50), nullable=False, comment='规则类型: completeness/uniqueness/timeliness/validity/consistency/stability/custom_sql')
    rule_template = Column(String(100), nullable=False, comment='规则模板名称')
    ge_expectation = Column(String(200), nullable=False, comment='对应的GE Expectation类名')
    parameters = Column(Text, nullable=True, comment='规则参数(JSON格式)')
    strength = Column(String(20), nullable=False, default='weak', 
                     comment='规则强度: strong(强规则)/weak(弱规则)')
    is_active = Column(Boolean, default=True, comment='是否生效')
    description = Column(Text, nullable=True, comment='规则描述')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    asset = relationship('Asset', back_populates='rules')
    validation_history = relationship('ValidationHistory', back_populates='rule', cascade='all, delete-orphan')
    issues = relationship('Issue', back_populates='rule', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'name': self.name,
            'column_name': self.column_name,
            'rule_type': self.rule_type,
            'rule_template': self.rule_template,
            'ge_expectation': self.ge_expectation,
            'parameters': self.parameters,
            'strength': self.strength,
            'is_active': self.is_active,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ValidationHistory(Base):
    """
    运行记录表 (Validation_History)
    记录每次质量校验的执行结果
    """
    __tablename__ = 'validation_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False, comment='关联的资产ID')
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=False, comment='关联的规则ID')
    start_time = Column(DateTime, nullable=False, comment='校验开始时间')
    end_time = Column(DateTime, nullable=True, comment='校验结束时间')
    status = Column(String(20), nullable=False, default='pending', 
                   comment='执行状态: pending/running/success/failed/cancelled')
    pass_rate = Column(Float, nullable=True, comment='通过率 (0-100)')
    total_records = Column(Integer, nullable=True, comment='总记录数')
    failed_records = Column(Integer, nullable=True, comment='失败记录数')
    exception_data_path = Column(String(512), nullable=True, comment='异常数据存储路径')
    error_message = Column(Text, nullable=True, comment='错误信息')
    execution_log = Column(Text, nullable=True, comment='执行日志')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    asset = relationship('Asset', back_populates='validation_history')
    rule = relationship('Rule', back_populates='validation_history')
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'rule_id': self.rule_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'pass_rate': self.pass_rate,
            'total_records': self.total_records,
            'failed_records': self.failed_records,
            'exception_data_path': self.exception_data_path,
            'error_message': self.error_message,
            'execution_log': self.execution_log,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Issue(Base):
    """
    问题清单表 (Issue)
    记录校验发现的质量问题和人工反馈的问题
    """
    __tablename__ = 'issues'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False, comment='关联的资产ID')
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=True, comment='关联的规则ID，NULL表示人工反馈')
    validation_history_id = Column(Integer, ForeignKey('validation_history.id'), nullable=True, 
                                  comment='关联的校验记录ID')
    issue_type = Column(String(50), nullable=False, default='system_detected', 
                       comment='问题类型: system_detected(系统识别)/manual_feedback(人工反馈)')
    title = Column(String(512), nullable=False, comment='问题标题')
    description = Column(Text, nullable=True, comment='问题描述')
    status = Column(String(20), nullable=False, default='pending', 
                   comment='状态: pending(待处理)/processing(整改中)/resolved(已处理)/ignored(已忽略)/whitelisted(白名单)')
    priority = Column(String(10), nullable=True, default='medium', 
                     comment='优先级: high/medium/low')
    assignee = Column(String(256), nullable=True, comment='问题负责人')
    reporter = Column(String(256), nullable=True, comment='报告人')
    attachments = Column(Text, nullable=True, comment='附件路径列表(JSON格式)')
    contact_info = Column(String(512), nullable=True, comment='联系方式')
    resolved_at = Column(DateTime, nullable=True, comment='解决时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    asset = relationship('Asset', back_populates='issues')
    rule = relationship('Rule', back_populates='issues')
    validation_history = relationship('ValidationHistory')
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'rule_id': self.rule_id,
            'validation_history_id': self.validation_history_id,
            'issue_type': self.issue_type,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assignee': self.assignee,
            'reporter': self.reporter,
            'attachments': self.attachments,
            'contact_info': self.contact_info,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ExceptionData(Base):
    """
    异常数据归档表 (Exception_Data)
    存储未通过校验的具体脏数据
    """
    __tablename__ = 'exception_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    validation_history_id = Column(Integer, ForeignKey('validation_history.id'), nullable=False, 
                                  comment='关联的校验记录ID')
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False, comment='关联的资产ID')
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=False, comment='关联的规则ID')
    issue_id = Column(Integer, ForeignKey('issues.id'), nullable=True, comment='关联的问题ID')
    row_number = Column(Integer, nullable=True, comment='原始数据行号')
    column_name = Column(String(256), nullable=True, comment='异常字段名')
    actual_value = Column(Text, nullable=True, comment='实际值')
    expected_value = Column(Text, nullable=True, comment='期望值')
    error_detail = Column(Text, nullable=True, comment='错误详情')
    full_record = Column(Text, nullable=True, comment='完整记录(JSON格式)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    validation_history = relationship('ValidationHistory')
    asset = relationship('Asset')
    rule = relationship('Rule')
    issue = relationship('Issue')
    
    def to_dict(self):
        return {
            'id': self.id,
            'validation_history_id': self.validation_history_id,
            'asset_id': self.asset_id,
            'rule_id': self.rule_id,
            'row_number': self.row_number,
            'column_name': self.column_name,
            'actual_value': self.actual_value,
            'expected_value': self.expected_value,
            'error_detail': self.error_detail,
            'full_record': self.full_record,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def init_db():
    """
    初始化数据库，创建所有表
    """
    Base.metadata.create_all(bind=engine)
    print(f"[OK] 数据库初始化完成: {DATABASE_PATH}")


def get_session():
    """
    获取数据库会话
    """
    return SessionLocal()


if __name__ == '__main__':
    # 测试：初始化数据库
    init_db()
    print("✅ 所有表创建成功")
