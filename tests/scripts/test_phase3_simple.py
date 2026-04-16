"""
简化版第三阶段 API 测试
只测试核心的 CRUD 操作
"""
import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'backend'))

from db_utils import (
    get_session, AssetManager, RuleManager,
    ValidationHistoryManager, IssueManager, ExceptionDataManager
)


class TestPhase3Core(unittest.TestCase):
    """测试第三阶段核心功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.session = get_session()
        
        # 创建测试资产
        self.asset = AssetManager.create_asset(
            session=self.session,
            name='测试资产P3',
            data_source='test_p3.csv',
            asset_type='csv',
            owner='测试用户'
        )
        
        # 创建测试规则
        self.rule = RuleManager.create_rule(
            session=self.session,
            asset_id=self.asset.id,
            name='测试规则P3',
            rule_type='completeness',
            rule_template='字段非空校验',
            ge_expectation='ExpectColumnValuesToNotBeNull',
            column_name='email',
            strength='weak'
        )
        
        # 创建校验历史
        from datetime import datetime
        self.history = ValidationHistoryManager.create_history(
            session=self.session,
            asset_id=self.asset.id,
            rule_id=self.rule.id,
            start_time=datetime.now()
        )
        
        # 创建问题
        self.issue = IssueManager.create_issue(
            session=self.session,
            asset_id=self.asset.id,
            rule_id=self.rule.id,
            title='测试问题P3',
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
    
    def test_01_asset_crud(self):
        """测试资产 CRUD"""
        # Create - 已在 setUp 中完成
        self.assertIsNotNone(self.asset)
        self.assertEqual(self.asset.name, '测试资产P3')
        
        # Read
        asset = AssetManager.get_asset(self.session, self.asset.id)
        self.assertIsNotNone(asset)
        self.assertEqual(asset.owner, '测试用户')
        
        # Update
        updated = AssetManager.update_asset(
            self.session,
            self.asset.id,
            owner='新负责人',
            quality_score_weight=8.5
        )
        self.session.commit()
        self.assertEqual(updated.owner, '新负责人')
        self.assertEqual(float(updated.quality_score_weight), 8.5)
        
        print("[OK] 资产 CRUD 测试通过")
    
    def test_02_rule_crud(self):
        """测试规则 CRUD"""
        # Create - 已在 setUp 中完成
        self.assertIsNotNone(self.rule)
        self.assertEqual(self.rule.strength, 'weak')
        
        # Read
        rules = RuleManager.get_rules_by_asset(self.session, self.asset.id)
        self.assertGreater(len(rules), 0)
        
        # Update
        updated = RuleManager.update_rule(
            self.session,
            self.rule.id,
            strength='strong',
            description='更新为强规则'
        )
        self.session.commit()
        self.assertEqual(updated.strength, 'strong')
        
        print("[OK] 规则 CRUD 测试通过")
    
    def test_03_validation_history(self):
        """测试校验历史"""
        # Create - 已在 setUp 中完成
        self.assertIsNotNone(self.history)
        self.assertEqual(self.history.status, 'running')
        
        # Read
        history = ValidationHistoryManager.get_history(self.session, self.history.id)
        self.assertIsNotNone(history)
        
        # Update
        from datetime import datetime
        updated = ValidationHistoryManager.update_history(
            self.session,
            self.history.id,
            status='completed',
            end_time=datetime.now(),
            total_rules=1,
            passed_rules=1,
            failed_rules=0,
            success_rate=100.0
        )
        self.session.commit()
        self.assertEqual(updated.status, 'completed')
        
        print("[OK] 校验历史测试通过")
    
    def test_04_issue_crud(self):
        """测试问题 CRUD"""
        # Create - 已在 setUp 中完成
        self.assertIsNotNone(self.issue)
        self.assertEqual(self.issue.status, 'pending')
        
        # Read
        issue = IssueManager.get_issue(self.session, self.issue.id)
        self.assertIsNotNone(issue)
        self.assertEqual(issue.title, '测试问题P3')
        
        # Update status: pending -> processing
        updated = IssueManager.update_issue_status(
            self.session,
            self.issue.id,
            status='processing',
            assignee='张三'
        )
        self.session.commit()
        self.assertEqual(updated.status, 'processing')
        self.assertEqual(updated.assignee, '张三')
        
        # Update status: processing -> resolved
        updated2 = IssueManager.update_issue_status(
            self.session,
            self.issue.id,
            status='resolved',
            resolution_note='问题已修复'
        )
        self.session.commit()
        self.assertEqual(updated2.status, 'resolved')
        self.assertIsNotNone(updated2.resolved_at)
        
        print("[OK] 问题 CRUD 测试通过")
    
    def test_05_exception_data(self):
        """测试异常数据归档"""
        # Archive
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
        self.assertEqual(exception.row_number, 1)  # 使用 row_number 而不是 record_index
        self.assertEqual(exception.actual_value, 'null')  # 使用 actual_value 而不是 exception_value
        
        # Read by issue
        exceptions = ExceptionDataManager.get_exceptions_by_issue(
            self.session,
            self.issue.id
        )
        self.assertIsInstance(exceptions, list)
        self.assertGreater(len(exceptions), 0)
        
        print("[OK] 异常数据测试通过")
    
    def test_06_get_all_assets(self):
        """测试获取所有资产"""
        assets = AssetManager.get_all_assets(self.session, is_active=True)
        self.assertIsInstance(assets, list)
        self.assertGreater(len(assets), 0)
        
        print("[OK] 获取资产列表测试通过")
    
    def test_07_delete_cascade(self):
        """测试级联删除"""
        # 创建临时资产和规则
        temp_asset = AssetManager.create_asset(
            session=self.session,
            name='临时资产',
            data_source='temp.csv'
        )
        
        temp_rule = RuleManager.create_rule(
            session=self.session,
            asset_id=temp_asset.id,
            name='临时规则',
            rule_type='completeness',
            rule_template='字段非空校验',
            ge_expectation='ExpectColumnValuesToNotBeNull'
        )
        self.session.commit()
        
        # 删除资产（应该级联删除规则）
        success = AssetManager.delete_asset(self.session, temp_asset.id)
        self.session.commit()
        
        self.assertTrue(success)
        
        # 验证规则也被删除
        deleted_rule = RuleManager.get_rule(self.session, temp_rule.id)
        self.assertIsNone(deleted_rule)
        
        print("[OK] 级联删除测试通过")


if __name__ == '__main__':
    print("=" * 80)
    print("测试第三阶段：质量治理工作台核心功能")
    print("=" * 80)
    unittest.main(verbosity=2)
