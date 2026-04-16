"""
测试第三阶段：质量治理工作台 API
"""
import unittest
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'backend'))

from db_utils import (
    get_session, AssetManager, RuleManager,
    ValidationHistoryManager, IssueManager, ExceptionDataManager
)


class TestAssetAPI(unittest.TestCase):
    """测试资产管理 API"""
    
    def setUp(self):
        """设置测试环境"""
        self.session = get_session()
        
        # 创建测试资产
        self.asset = AssetManager.create_asset(
            session=self.session,
            name='测试资产API',
            data_source='test_api_data.csv',
            asset_type='csv',
            owner='测试用户'
        )
        self.session.commit()
    
    def tearDown(self):
        """清理测试环境"""
        if self.asset:
            AssetManager.delete_asset(self.session, self.asset.id)
            self.session.commit()
        self.session.close()
    
    def test_create_asset(self):
        """测试创建资产"""
        asset = AssetManager.create_asset(
            session=self.session,
            name='新测试资产',
            data_source='new_test.csv',
            asset_type='csv'
        )
        self.session.commit()
        
        self.assertIsNotNone(asset)
        self.assertEqual(asset.name, '新测试资产')
        self.assertTrue(asset.is_active)
        
        # 清理
        AssetManager.delete_asset(self.session, asset.id)
        self.session.commit()
    
    def test_get_asset(self):
        """测试获取单个资产"""
        asset = AssetManager.get_asset(self.session, self.asset.id)
        
        self.assertIsNotNone(asset)
        self.assertEqual(asset.name, '测试资产API')
    
    def test_list_assets(self):
        """测试获取资产列表"""
        assets = AssetManager.list_assets(self.session, page=1, per_page=10)
        
        self.assertIsInstance(assets, list)
        self.assertGreater(len(assets), 0)
    
    def test_update_asset(self):
        """测试更新资产"""
        updated_asset = AssetManager.update_asset(
            self.session,
            self.asset.id,
            owner='新负责人',
            quality_score_weight=9.0
        )
        self.session.commit()
        
        self.assertEqual(updated_asset.owner, '新负责人')
        self.assertEqual(float(updated_asset.quality_score_weight), 9.0)
    
    def test_delete_asset(self):
        """测试删除资产"""
        # 创建一个临时资产用于删除测试
        temp_asset = AssetManager.create_asset(
            session=self.session,
            name='临时资产',
            data_source='temp.csv'
        )
        self.session.commit()
        
        # 删除
        success = AssetManager.delete_asset(self.session, temp_asset.id)
        self.session.commit()
        
        self.assertTrue(success)
        
        # 验证已删除
        deleted_asset = AssetManager.get_asset(self.session, temp_asset.id)
        self.assertIsNone(deleted_asset)


class TestRuleAPI(unittest.TestCase):
    """测试规则管理 API"""
    
    def setUp(self):
        """设置测试环境"""
        self.session = get_session()
        
        # 创建测试资产
        self.asset = AssetManager.create_asset(
            session=self.session,
            name='测试规则API资产',
            data_source='test_rule_api.csv',
            asset_type='csv'
        )
        
        # 创建测试规则
        self.rule = RuleManager.create_rule(
            session=self.session,
            asset_id=self.asset.id,
            name='测试规则API',
            rule_type='completeness',
            rule_template='字段非空校验',
            ge_expectation='ExpectColumnValuesToNotBeNull',
            column_name='test_column',
            strength='weak'
        )
        self.session.commit()
    
    def tearDown(self):
        """清理测试环境"""
        if self.asset:
            AssetManager.delete_asset(self.session, self.asset.id)
            self.session.commit()
        self.session.close()
    
    def test_create_rule(self):
        """测试创建规则"""
        rule = RuleManager.create_rule(
            session=self.session,
            asset_id=self.asset.id,
            name='新测试规则',
            rule_type='uniqueness',
            rule_template='字段唯一性校验',
            ge_expectation='ExpectColumnValuesToBeUnique',
            column_name='email',
            strength='strong'
        )
        self.session.commit()
        
        self.assertIsNotNone(rule)
        self.assertEqual(rule.name, '新测试规则')
        self.assertEqual(rule.strength, 'strong')
        
        # 清理
        RuleManager.delete_rule(self.session, rule.id)
        self.session.commit()
    
    def test_get_rules_by_asset(self):
        """测试获取资产的规则列表"""
        rules = RuleManager.get_rules_by_asset(self.session, self.asset.id)
        
        self.assertIsInstance(rules, list)
        self.assertGreater(len(rules), 0)
        
        # 检查规则信息
        rule = rules[0]
        self.assertEqual(rule.name, '测试规则API')
        self.assertEqual(rule.column_name, 'test_column')
    
    def test_update_rule(self):
        """测试更新规则"""
        updated_rule = RuleManager.update_rule(
            self.session,
            self.rule.id,
            strength='strong',
            description='更新后的描述'
        )
        self.session.commit()
        
        self.assertEqual(updated_rule.strength, 'strong')
        self.assertEqual(updated_rule.description, '更新后的描述')
    
    def test_delete_rule(self):
        """测试删除规则"""
        # 创建一个临时规则用于删除测试
        temp_rule = RuleManager.create_rule(
            session=self.session,
            asset_id=self.asset.id,
            name='临时规则',
            rule_type='completeness',
            rule_template='字段非空校验',
            ge_expectation='ExpectColumnValuesToNotBeNull'
        )
        self.session.commit()
        
        # 删除
        success = RuleManager.delete_rule(self.session, temp_rule.id)
        self.session.commit()
        
        self.assertTrue(success)


class TestValidationHistoryAPI(unittest.TestCase):
    """测试校验历史 API"""
    
    def setUp(self):
        """设置测试环境"""
        self.session = get_session()
        
        # 创建测试资产
        self.asset = AssetManager.create_asset(
            session=self.session,
            name='测试校验历史资产',
            data_source='test_history.csv',
            asset_type='csv'
        )
        self.session.commit()
    
    def tearDown(self):
        """清理测试环境"""
        if self.asset:
            AssetManager.delete_asset(self.session, self.asset.id)
            self.session.commit()
        self.session.close()
    
    def test_create_validation_history(self):
        """测试创建校验历史"""
        history = ValidationHistoryManager.create_history(
            session=self.session,
            asset_id=self.asset.id,
            total_rules=5,
            passed_rules=4,
            failed_rules=1,
            status='completed'
        )
        self.session.commit()
        
        self.assertIsNotNone(history)
        self.assertEqual(history.total_rules, 5)
        self.assertEqual(history.status, 'completed')
    
    def test_get_history(self):
        """测试获取校验历史"""
        # 先创建一个历史记录
        history = ValidationHistoryManager.create_history(
            session=self.session,
            asset_id=self.asset.id,
            total_rules=3,
            passed_rules=3,
            failed_rules=0,
            status='completed'
        )
        self.session.commit()
        
        # 获取
        retrieved = ValidationHistoryManager.get_history(self.session, history.id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.total_rules, 3)
        
        # 清理
        ValidationHistoryManager.delete_history(self.session, history.id)
        self.session.commit()
    
    def test_list_histories(self):
        """测试获取校验历史列表"""
        histories = ValidationHistoryManager.list_histories(
            self.session,
            asset_id=self.asset.id
        )
        
        self.assertIsInstance(histories, list)


class TestIssueAPI(unittest.TestCase):
    """测试问题管理 API"""
    
    def setUp(self):
        """设置测试环境"""
        self.session = get_session()
        
        # 创建测试资产
        self.asset = AssetManager.create_asset(
            session=self.session,
            name='测试问题资产',
            data_source='test_issue.csv',
            asset_type='csv'
        )
        
        # 创建测试规则
        self.rule = RuleManager.create_rule(
            session=self.session,
            asset_id=self.asset.id,
            name='测试问题规则',
            rule_type='completeness',
            rule_template='字段非空校验',
            ge_expectation='ExpectColumnValuesToNotBeNull',
            column_name='email'
        )
        
        # 创建校验历史
        self.history = ValidationHistoryManager.create_history(
            session=self.session,
            asset_id=self.asset.id,
            total_rules=1,
            passed_rules=0,
            failed_rules=1,
            status='completed'
        )
        
        # 创建测试问题
        self.issue = IssueManager.create_issue(
            session=self.session,
            asset_id=self.asset.id,
            rule_id=self.rule.id,
            title='测试问题',
            description='这是一个测试问题',
            validation_history_id=self.history.id
        )
        self.session.commit()
    
    def tearDown(self):
        """清理测试环境"""
        if self.asset:
            AssetManager.delete_asset(self.session, self.asset.id)
            self.session.commit()
        self.session.close()
    
    def test_create_issue(self):
        """测试创建问题"""
        issue = IssueManager.create_issue(
            session=self.session,
            asset_id=self.asset.id,
            rule_id=self.rule.id,
            title='新问题',
            description='新问题的描述',
            priority='high',
            validation_history_id=self.history.id
        )
        self.session.commit()
        
        self.assertIsNotNone(issue)
        self.assertEqual(issue.title, '新问题')
        self.assertEqual(issue.priority, 'high')
        self.assertEqual(issue.status, 'pending')
        
        # 清理
        IssueManager.delete_issue(self.session, issue.id)
        self.session.commit()
    
    def test_get_issue(self):
        """测试获取问题详情"""
        issue = IssueManager.get_issue(self.session, self.issue.id)
        
        self.assertIsNotNone(issue)
        self.assertEqual(issue.title, '测试问题')
        self.assertEqual(issue.status, 'pending')
    
    def test_list_issues(self):
        """测试获取问题列表"""
        issues = IssueManager.list_issues(self.session, asset_id=self.asset.id)
        
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)
    
    def test_update_issue_status_pending_to_processing(self):
        """测试问题状态流转：pending -> processing"""
        updated_issue = IssueManager.update_issue_status(
            self.session,
            self.issue.id,
            status='processing',
            assignee='张三'
        )
        self.session.commit()
        
        self.assertEqual(updated_issue.status, 'processing')
        self.assertEqual(updated_issue.assignee, '张三')
    
    def test_update_issue_status_processing_to_resolved(self):
        """测试问题状态流转：processing -> resolved"""
        # 先设置为 processing
        IssueManager.update_issue_status(
            self.session,
            self.issue.id,
            status='processing',
            assignee='李四'
        )
        self.session.commit()
        
        # 再设置为 resolved
        updated_issue = IssueManager.update_issue_status(
            self.session,
            self.issue.id,
            status='resolved',
            resolution_note='问题已修复'
        )
        self.session.commit()
        
        self.assertEqual(updated_issue.status, 'resolved')
        self.assertIsNotNone(updated_issue.resolved_at)
        self.assertEqual(updated_issue.resolution_note, '问题已修复')
    
    def test_invalid_status_transition(self):
        """测试无效的状态流转"""
        # 尝试从 pending 直接到 closed（跳过中间状态）
        with self.assertRaises(ValueError):
            IssueManager.update_issue_status(
                self.session,
                self.issue.id,
                status='closed'
            )


class TestExceptionDataAPI(unittest.TestCase):
    """测试异常数据 API"""
    
    def setUp(self):
        """设置测试环境"""
        self.session = get_session()
        
        # 创建测试资产和规则
        self.asset = AssetManager.create_asset(
            session=self.session,
            name='测试异常数据资产',
            data_source='test_exception.csv',
            asset_type='csv'
        )
        
        self.rule = RuleManager.create_rule(
            session=self.session,
            asset_id=self.asset.id,
            name='测试异常数据规则',
            rule_type='completeness',
            rule_template='字段非空校验',
            ge_expectation='ExpectColumnValuesToNotBeNull',
            column_name='email'
        )
        
        # 创建校验历史
        self.history = ValidationHistoryManager.create_history(
            session=self.session,
            asset_id=self.asset.id,
            total_rules=1,
            passed_rules=0,
            failed_rules=1,
            status='completed'
        )
        
        # 创建问题
        self.issue = IssueManager.create_issue(
            session=self.session,
            asset_id=self.asset.id,
            rule_id=self.rule.id,
            title='测试异常数据问题',
            validation_history_id=self.history.id
        )
        self.session.commit()
    
    def tearDown(self):
        """清理测试环境"""
        if self.asset:
            AssetManager.delete_asset(self.session, self.asset.id)
            self.session.commit()
        self.session.close()
    
    def test_archive_exception(self):
        """测试归档异常数据"""
        exception = ExceptionDataManager.archive_exception(
            session=self.session,
            asset_id=self.asset.id,
            rule_id=self.rule.id,
            validation_history_id=self.history.id,
            issue_id=self.issue.id,
            record_index=1,
            field_name='email',
            exception_value='null'
        )
        self.session.commit()
        
        self.assertIsNotNone(exception)
        self.assertEqual(exception.record_index, 1)
        self.assertEqual(exception.field_name, 'email')
        self.assertEqual(exception.exception_value, 'null')
    
    def test_get_exceptions_by_issue(self):
        """测试根据问题ID获取异常数据"""
        # 先创建一些异常数据
        for i in range(3):
            ExceptionDataManager.archive_exception(
                session=self.session,
                asset_id=self.asset.id,
                rule_id=self.rule.id,
                validation_history_id=self.history.id,
                issue_id=self.issue.id,
                record_index=i,
                field_name='email',
                exception_value=f'value_{i}'
            )
        self.session.commit()
        
        # 获取
        exceptions = ExceptionDataManager.get_exceptions_by_issue(
            self.session,
            self.issue.id
        )
        
        self.assertIsInstance(exceptions, list)
        self.assertEqual(len(exceptions), 3)
    
    def test_delete_exceptions_by_rule(self):
        """测试删除规则相关的异常数据"""
        # 先创建一些异常数据
        for i in range(2):
            ExceptionDataManager.archive_exception(
                session=self.session,
                asset_id=self.asset.id,
                rule_id=self.rule.id,
                validation_history_id=self.history.id,
                issue_id=self.issue.id,
                record_index=i,
                field_name='email',
                exception_value=f'value_{i}'
            )
        self.session.commit()
        
        # 删除
        count = ExceptionDataManager.delete_exceptions_by_rule(
            self.session,
            self.rule.id
        )
        self.session.commit()
        
        self.assertEqual(count, 2)


class TestStatisticsAPI(unittest.TestCase):
    """测试统计分析 API"""
    
    def setUp(self):
        """设置测试环境"""
        self.session = get_session()
        
        # 创建测试数据
        self.asset = AssetManager.create_asset(
            session=self.session,
            name='测试统计资产',
            data_source='test_stats.csv',
            asset_type='csv'
        )
        
        self.rule = RuleManager.create_rule(
            session=self.session,
            asset_id=self.asset.id,
            name='测试统计规则',
            rule_type='completeness',
            rule_template='字段非空校验',
            ge_expectation='ExpectColumnValuesToNotBeNull',
            strength='strong'
        )
        self.session.commit()
    
    def tearDown(self):
        """清理测试环境"""
        if self.asset:
            AssetManager.delete_asset(self.session, self.asset.id)
            self.session.commit()
        self.session.close()
    
    def test_count_active_assets(self):
        """测试统计激活的资产数量"""
        from sqlalchemy import func
        
        count = self.session.query(func.count()).filter(
            AssetManager.model.is_active == True
        ).scalar()
        
        self.assertGreater(count, 0)
    
    def test_count_rules_by_strength(self):
        """测试按强度统计规则数量"""
        from sqlalchemy import func
        
        strong_count = self.session.query(func.count()).filter(
            RuleManager.model.strength == 'strong'
        ).scalar()
        
        weak_count = self.session.query(func.count()).filter(
            RuleManager.model.strength == 'weak'
        ).scalar()
        
        self.assertGreaterEqual(strong_count, 0)
        self.assertGreaterEqual(weak_count, 0)
    
    def test_count_issues_by_status(self):
        """测试按状态统计问题数量"""
        from sqlalchemy import func
        
        pending_count = self.session.query(func.count()).filter(
            IssueManager.model.status == 'pending'
        ).scalar()
        
        self.assertGreaterEqual(pending_count, 0)


if __name__ == '__main__':
    print("=" * 80)
    print("测试第三阶段：质量治理工作台 API")
    print("=" * 80)
    unittest.main(verbosity=2)
