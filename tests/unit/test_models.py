"""
数据库模型测试用例
测试所有核心表的CRUD操作和关系
"""
import sys
import os
import unittest
from datetime import datetime, timedelta

# 添加后端代码路径到系统路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'backend'))

from models.base import init_db, get_session, Asset, Rule, ValidationHistory, Issue, ExceptionData
from models.managers import (
    AssetManager, RuleManager, ValidationHistoryManager, 
    IssueManager, ExceptionDataManager
)


class TestAssetModel(unittest.TestCase):
    """测试资产管理"""
    
    def setUp(self):
        """每个测试前初始化数据库"""
        init_db()
        self.session = get_session()
    
    def tearDown(self):
        """每个测试后清理数据"""
        # 删除所有测试数据
        self.session.query(ExceptionData).delete()
        self.session.query(Issue).delete()
        self.session.query(ValidationHistory).delete()
        self.session.query(Rule).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()
    
    def test_create_asset(self):
        """测试创建资产"""
        asset = AssetManager.create_asset(
            session=self.session,
            name='test_table',
            data_source='output/data/test.csv',
            asset_type='csv',
            owner='张三',
            description='测试表',
            quality_score_weight=5.0
        )
        
        self.assertIsNotNone(asset.id)
        self.assertEqual(asset.name, 'test_table')
        self.assertEqual(asset.asset_type, 'csv')
        self.assertEqual(asset.owner, '张三')
        self.assertEqual(asset.quality_score_weight, 5.0)
        self.assertTrue(asset.is_active)
        self.assertIsNotNone(asset.created_at)
    
    def test_get_asset(self):
        """测试获取单个资产"""
        # 先创建
        asset = AssetManager.create_asset(
            session=self.session,
            name='test_table_2',
            data_source='output/data/test2.csv'
        )
        
        # 再获取
        retrieved = AssetManager.get_asset(self.session, asset.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, 'test_table_2')
    
    def test_get_all_assets(self):
        """测试获取所有资产"""
        # 创建多个资产
        AssetManager.create_asset(self.session, 'table1', 'path1')
        AssetManager.create_asset(self.session, 'table2', 'path2')
        AssetManager.create_asset(self.session, 'table3', 'path3')
        
        assets = AssetManager.get_all_assets(self.session)
        self.assertEqual(len(assets), 3)
    
    def test_update_asset(self):
        """测试更新资产"""
        asset = AssetManager.create_asset(
            session=self.session,
            name='original_name',
            data_source='path'
        )
        
        # 更新
        updated = AssetManager.update_asset(
            session=self.session,
            asset_id=asset.id,
            name='new_name',
            owner='李四',
            quality_score_weight=8.0
        )
        
        self.assertEqual(updated.name, 'new_name')
        self.assertEqual(updated.owner, '李四')
        self.assertEqual(updated.quality_score_weight, 8.0)
    
    def test_delete_asset(self):
        """测试删除资产（级联删除）"""
        asset = AssetManager.create_asset(
            session=self.session,
            name='to_delete',
            data_source='path'
        )
        
        # 添加一个规则
        rule = RuleManager.create_rule(
            session=self.session,
            asset_id=asset.id,
            name='test_rule',
            rule_type='completeness',
            rule_template='空值校验',
            ge_expectation='expect_column_values_to_not_be_null'
        )
        
        # 删除资产
        result = AssetManager.delete_asset(self.session, asset.id)
        self.assertTrue(result)
        
        # 验证规则和资产都被删除
        deleted_asset = AssetManager.get_asset(self.session, asset.id)
        deleted_rule = RuleManager.get_rule(self.session, rule.id)
        self.assertIsNone(deleted_asset)
        self.assertIsNone(deleted_rule)
    
    def test_filter_active_assets(self):
        """测试按激活状态筛选资产"""
        asset1 = AssetManager.create_asset(self.session, 'active_table', 'path1')
        asset2 = AssetManager.create_asset(self.session, 'inactive_table', 'path2')
        AssetManager.update_asset(self.session, asset2.id, is_active=False)
        
        active_assets = AssetManager.get_all_assets(self.session, is_active=True)
        inactive_assets = AssetManager.get_all_assets(self.session, is_active=False)
        
        self.assertEqual(len(active_assets), 1)
        self.assertEqual(len(inactive_assets), 1)
        self.assertEqual(active_assets[0].name, 'active_table')


class TestRuleModel(unittest.TestCase):
    """测试规则管理"""
    
    def setUp(self):
        init_db()
        self.session = get_session()
        # 创建一个测试资产
        self.asset = AssetManager.create_asset(
            session=self.session,
            name='test_asset',
            data_source='path'
        )
    
    def tearDown(self):
        self.session.query(ExceptionData).delete()
        self.session.query(Issue).delete()
        self.session.query(ValidationHistory).delete()
        self.session.query(Rule).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()
    
    def test_create_rule(self):
        """测试创建规则"""
        rule = RuleManager.create_rule(
            session=self.session,
            asset_id=self.asset.id,
            name='非空校验',
            rule_type='completeness',
            rule_template='字段空值校验',
            ge_expectation='expect_column_values_to_not_be_null',
            strength='strong',
            column_name='user_id',
            description='用户ID不能为空'
        )
        
        self.assertIsNotNone(rule.id)
        self.assertEqual(rule.name, '非空校验')
        self.assertEqual(rule.rule_type, 'completeness')
        self.assertEqual(rule.strength, 'strong')
        self.assertEqual(rule.column_name, 'user_id')
        self.assertTrue(rule.is_active)
    
    def test_get_rules_by_asset(self):
        """测试获取资产的所有规则"""
        RuleManager.create_rule(self.session, self.asset.id, 'rule1', 'completeness', '模板1', 'exp1')
        RuleManager.create_rule(self.session, self.asset.id, 'rule2', 'uniqueness', '模板2', 'exp2')
        RuleManager.create_rule(self.session, self.asset.id, 'rule3', 'validity', '模板3', 'exp3')
        
        rules = RuleManager.get_rules_by_asset(self.session, self.asset.id)
        self.assertEqual(len(rules), 3)
    
    def test_update_rule(self):
        """测试更新规则"""
        rule = RuleManager.create_rule(
            session=self.session,
            asset_id=self.asset.id,
            name='old_name',
            rule_type='completeness',
            rule_template='模板',
            ge_expectation='exp'
        )
        
        updated = RuleManager.update_rule(
            session=self.session,
            rule_id=rule.id,
            name='new_name',
            strength='weak',
            is_active=False
        )
        
        self.assertEqual(updated.name, 'new_name')
        self.assertEqual(updated.strength, 'weak')
        self.assertFalse(updated.is_active)
    
    def test_delete_rule(self):
        """测试删除规则"""
        rule = RuleManager.create_rule(
            session=self.session,
            asset_id=self.asset.id,
            name='to_delete',
            rule_type='completeness',
            rule_template='模板',
            ge_expectation='exp'
        )
        
        result = RuleManager.delete_rule(self.session, rule.id)
        self.assertTrue(result)
        
        deleted = RuleManager.get_rule(self.session, rule.id)
        self.assertIsNone(deleted)
    
    def test_filter_active_rules(self):
        """测试按激活状态筛选规则"""
        rule1 = RuleManager.create_rule(self.session, self.asset.id, 'active_rule', 'type1', 't1', 'e1')
        rule2 = RuleManager.create_rule(self.session, self.asset.id, 'inactive_rule', 'type2', 't2', 'e2')
        RuleManager.update_rule(self.session, rule2.id, is_active=False)
        
        active_rules = RuleManager.get_rules_by_asset(self.session, self.asset.id, is_active=True)
        inactive_rules = RuleManager.get_rules_by_asset(self.session, self.asset.id, is_active=False)
        
        self.assertEqual(len(active_rules), 1)
        self.assertEqual(len(inactive_rules), 1)


class TestValidationHistoryModel(unittest.TestCase):
    """测试校验历史管理"""
    
    def setUp(self):
        init_db()
        self.session = get_session()
        self.asset = AssetManager.create_asset(self.session, 'test_asset', 'path')
        self.rule = RuleManager.create_rule(
            self.session, self.asset.id, 'test_rule', 'completeness', '模板', 'exp'
        )
    
    def tearDown(self):
        self.session.query(ExceptionData).delete()
        self.session.query(Issue).delete()
        self.session.query(ValidationHistory).delete()
        self.session.query(Rule).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()
    
    def test_create_history(self):
        """测试创建校验历史"""
        start_time = datetime.now()
        history = ValidationHistoryManager.create_history(
            session=self.session,
            asset_id=self.asset.id,
            rule_id=self.rule.id,
            start_time=start_time
        )
        
        self.assertIsNotNone(history.id)
        self.assertEqual(history.status, 'running')
        self.assertEqual(history.start_time, start_time)
    
    def test_update_history_success(self):
        """测试更新校验历史为成功"""
        history = ValidationHistoryManager.create_history(
            self.session, self.asset.id, self.rule.id, datetime.now()
        )
        
        updated = ValidationHistoryManager.update_history(
            session=self.session,
            history_id=history.id,
            status='success',
            end_time=datetime.now(),
            pass_rate=95.5,
            total_records=1000,
            failed_records=45
        )
        
        self.assertEqual(updated.status, 'success')
        self.assertEqual(updated.pass_rate, 95.5)
        self.assertEqual(updated.total_records, 1000)
        self.assertEqual(updated.failed_records, 45)
    
    def test_update_history_failed(self):
        """测试更新校验历史为失败"""
        history = ValidationHistoryManager.create_history(
            self.session, self.asset.id, self.rule.id, datetime.now()
        )
        
        updated = ValidationHistoryManager.update_history(
            session=self.session,
            history_id=history.id,
            status='failed',
            end_time=datetime.now(),
            error_message='列不存在',
            exception_data_path='output/reports/exception_123.csv'
        )
        
        self.assertEqual(updated.status, 'failed')
        self.assertEqual(updated.error_message, '列不存在')
        self.assertIsNotNone(updated.exception_data_path)
    
    def test_get_history_by_asset(self):
        """测试获取资产的校验历史"""
        # 创建多条历史记录
        for i in range(5):
            ValidationHistoryManager.create_history(
                self.session, self.asset.id, self.rule.id, 
                datetime.now() - timedelta(hours=i)
            )
        
        histories = ValidationHistoryManager.get_history_by_asset(self.session, self.asset.id, limit=3)
        self.assertEqual(len(histories), 3)
        # 应该按时间倒序
        self.assertTrue(histories[0].created_at >= histories[1].created_at)


class TestIssueModel(unittest.TestCase):
    """测试问题管理"""
    
    def setUp(self):
        init_db()
        self.session = get_session()
        self.asset = AssetManager.create_asset(self.session, 'test_asset', 'path')
        self.rule = RuleManager.create_rule(
            self.session, self.asset.id, 'test_rule', 'completeness', '模板', 'exp'
        )
        self.history = ValidationHistoryManager.create_history(
            self.session, self.asset.id, self.rule.id, datetime.now()
        )
    
    def tearDown(self):
        self.session.query(ExceptionData).delete()
        self.session.query(Issue).delete()
        self.session.query(ValidationHistory).delete()
        self.session.query(Rule).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()
    
    def test_create_system_issue(self):
        """测试创建系统识别的问题"""
        issue = IssueManager.create_issue(
            session=self.session,
            asset_id=self.asset.id,
            rule_id=self.rule.id,
            validation_history_id=self.history.id,
            title='用户ID存在空值',
            issue_type='system_detected',
            description='发现45条记录的用户ID为空',
            priority='high',
            assignee='张三'
        )
        
        self.assertIsNotNone(issue.id)
        self.assertEqual(issue.issue_type, 'system_detected')
        self.assertEqual(issue.status, 'pending')
        self.assertEqual(issue.priority, 'high')
        self.assertEqual(issue.assignee, '张三')
    
    def test_create_manual_issue(self):
        """测试创建人工反馈的问题"""
        issue = IssueManager.create_issue(
            session=self.session,
            asset_id=self.asset.id,
            title='数据格式异常',
            issue_type='manual_feedback',
            description='用户手动反馈数据格式有问题',
            reporter='李四',
            contact_info='lisi@example.com'
        )
        
        self.assertEqual(issue.issue_type, 'manual_feedback')
        self.assertIsNone(issue.rule_id)  # 人工反馈没有关联规则
        self.assertEqual(issue.reporter, '李四')
    
    def test_update_issue_status(self):
        """测试更新问题状态"""
        issue = IssueManager.create_issue(
            self.session, self.asset.id, 'test_issue', 'system_detected'
        )
        
        # 更新为整改中
        updated = IssueManager.update_issue_status(self.session, issue.id, 'processing')
        self.assertEqual(updated.status, 'processing')
        
        # 更新为已处理
        updated = IssueManager.update_issue_status(self.session, issue.id, 'resolved')
        self.assertEqual(updated.status, 'resolved')
        self.assertIsNotNone(updated.resolved_at)
    
    def test_get_issues_by_status(self):
        """测试按状态获取问题"""
        IssueManager.create_issue(self.session, self.asset.id, 'issue1', status='pending')
        IssueManager.create_issue(self.session, self.asset.id, 'issue2', status='pending')
        IssueManager.create_issue(self.session, self.asset.id, 'issue3', status='resolved')
        
        pending_issues = IssueManager.get_issues_by_status(self.session, 'pending')
        resolved_issues = IssueManager.get_issues_by_status(self.session, 'resolved')
        
        self.assertEqual(len(pending_issues), 2)
        self.assertEqual(len(resolved_issues), 1)
    
    def test_get_issues_by_assignee(self):
        """测试获取负责人的问题"""
        IssueManager.create_issue(self.session, self.asset.id, 'issue1', assignee='张三', status='pending')
        IssueManager.create_issue(self.session, self.asset.id, 'issue2', assignee='张三', status='resolved')
        IssueManager.create_issue(self.session, self.asset.id, 'issue3', assignee='李四', status='pending')
        
        zhangsan_issues = IssueManager.get_issues_by_assignee(self.session, '张三')
        zhangsan_pending = IssueManager.get_issues_by_assignee(self.session, '张三', status='pending')
        
        self.assertEqual(len(zhangsan_issues), 2)
        self.assertEqual(len(zhangsan_pending), 1)


class TestExceptionDataModel(unittest.TestCase):
    """测试异常数据管理"""
    
    def setUp(self):
        init_db()
        self.session = get_session()
        self.asset = AssetManager.create_asset(self.session, 'test_asset', 'path')
        self.rule = RuleManager.create_rule(
            self.session, self.asset.id, 'test_rule', 'completeness', '模板', 'exp'
        )
        self.history = ValidationHistoryManager.create_history(
            self.session, self.asset.id, self.rule.id, datetime.now()
        )
    
    def tearDown(self):
        self.session.query(ExceptionData).delete()
        self.session.query(Issue).delete()
        self.session.query(ValidationHistory).delete()
        self.session.query(Rule).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()
    
    def test_add_exception_single_field(self):
        """测试添加单字段异常数据"""
        exception = ExceptionDataManager.add_exception(
            session=self.session,
            validation_history_id=self.history.id,
            asset_id=self.asset.id,
            rule_id=self.rule.id,
            row_number=5,
            column_name='user_id',
            actual_value='NULL',
            expected_value='NOT NULL',
            error_detail='字段值为空'
        )
        
        self.assertIsNotNone(exception.id)
        self.assertEqual(exception.row_number, 5)
        self.assertEqual(exception.column_name, 'user_id')
        self.assertEqual(exception.actual_value, 'NULL')
    
    def test_add_exception_full_record(self):
        """测试添加完整记录异常"""
        import json
        full_record = json.dumps({
            'user_id': None,
            'name': '张三',
            'age': 25
        })
        
        exception = ExceptionDataManager.add_exception(
            session=self.session,
            validation_history_id=self.history.id,
            asset_id=self.asset.id,
            rule_id=self.rule.id,
            row_number=10,
            full_record=full_record,
            error_detail='完整记录归档'
        )
        
        self.assertIsNotNone(exception.full_record)
        record_data = json.loads(exception.full_record)
        self.assertEqual(record_data['name'], '张三')
    
    def test_get_exceptions_by_history(self):
        """测试获取校验历史的异常数据"""
        # 添加多条异常
        for i in range(10):
            ExceptionDataManager.add_exception(
                self.session, self.history.id, self.asset.id, self.rule.id,
                row_number=i, column_name='test_col', actual_value=f'value_{i}'
            )
        
        exceptions = ExceptionDataManager.get_exceptions_by_history(self.session, self.history.id, limit=5)
        self.assertEqual(len(exceptions), 5)
    
    def test_count_exceptions(self):
        """测试统计异常数量"""
        for i in range(15):
            ExceptionDataManager.add_exception(
                self.session, self.history.id, self.asset.id, self.rule.id
            )
        
        count = ExceptionDataManager.count_exceptions_by_history(self.session, self.history.id)
        self.assertEqual(count, 15)


class TestDatabaseRelationships(unittest.TestCase):
    """测试数据库关系"""
    
    def setUp(self):
        init_db()
        self.session = get_session()
    
    def tearDown(self):
        self.session.query(ExceptionData).delete()
        self.session.query(Issue).delete()
        self.session.query(ValidationHistory).delete()
        self.session.query(Rule).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()
    
    def test_asset_rules_relationship(self):
        """测试资产与规则的关系"""
        asset = AssetManager.create_asset(self.session, 'test_asset', 'path')
        rule1 = RuleManager.create_rule(self.session, asset.id, 'rule1', 'type1', 't1', 'e1')
        rule2 = RuleManager.create_rule(self.session, asset.id, 'rule2', 'type2', 't2', 'e2')
        
        # 通过关系访问
        self.assertEqual(len(asset.rules), 2)
        self.assertIn(rule1, asset.rules)
        self.assertIn(rule2, asset.rules)
    
    def test_asset_validation_history_relationship(self):
        """测试资产与校验历史的关系"""
        asset = AssetManager.create_asset(self.session, 'test_asset', 'path')
        rule = RuleManager.create_rule(self.session, asset.id, 'rule', 'type', 't', 'e')
        
        history1 = ValidationHistoryManager.create_history(self.session, asset.id, rule.id, datetime.now())
        history2 = ValidationHistoryManager.create_history(self.session, asset.id, rule.id, datetime.now())
        
        self.assertEqual(len(asset.validation_history), 2)
    
    def test_rule_issues_relationship(self):
        """测试规则与问题的关系"""
        asset = AssetManager.create_asset(self.session, 'test_asset', 'path')
        rule = RuleManager.create_rule(self.session, asset.id, 'rule', 'type', 't', 'e')
        history = ValidationHistoryManager.create_history(self.session, asset.id, rule.id, datetime.now())
        
        issue1 = IssueManager.create_issue(self.session, asset.id, 'issue1', rule_id=rule.id, validation_history_id=history.id)
        issue2 = IssueManager.create_issue(self.session, asset.id, 'issue2', rule_id=rule.id, validation_history_id=history.id)
        
        self.assertEqual(len(rule.issues), 2)
    
    def test_cascade_delete(self):
        """测试级联删除"""
        asset = AssetManager.create_asset(self.session, 'test_asset', 'path')
        rule = RuleManager.create_rule(self.session, asset.id, 'rule', 'type', 't', 'e')
        history = ValidationHistoryManager.create_history(self.session, asset.id, rule.id, datetime.now())
        issue = IssueManager.create_issue(self.session, asset.id, 'issue', rule_id=rule.id, validation_history_id=history.id)
        
        # 删除资产
        AssetManager.delete_asset(self.session, asset.id)
        
        # 验证相关数据都被删除
        self.assertIsNone(RuleManager.get_rule(self.session, rule.id))
        self.assertIsNone(ValidationHistoryManager.get_history(self.session, history.id))
        self.assertIsNone(IssueManager.get_issue(self.session, issue.id))


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
