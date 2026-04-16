"""
数据库模型使用示例
演示如何使用资产管理器、规则管理器等
"""
import sys
import os
from datetime import datetime

# 添加后端代码路径到系统路径
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'backend')
sys.path.insert(0, backend_path)

from models import init_db, get_session
from db_utils import AssetManager, RuleManager, ValidationHistoryManager, IssueManager


def demo_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("DataQ 数据库模型使用示例")
    print("=" * 60)
    
    # 初始化数据库
    init_db()
    session = get_session()
    
    try:
        # 1. 创建资产
        print("\n[步骤 1] 创建监控资产...")
        asset = AssetManager.create_asset(
            session=session,
            name='user_info_table',
            data_source='output/data/user_info.csv',
            asset_type='csv',
            owner='张三',
            description='用户信息表',
            quality_score_weight=5.0
        )
        print(f"✅ 创建资产: {asset.name} (ID: {asset.id})")
        
        # 2. 创建质量规则
        print("\n[步骤 2] 创建质量规则...")
        
        # 规则1: 完整性检查 - 强规则
        rule1 = RuleManager.create_rule(
            session=session,
            asset_id=asset.id,
            name='用户ID非空校验',
            rule_type='completeness',
            rule_template='字段空值校验',
            ge_expectation='expect_column_values_to_not_be_null',
            strength='strong',  # 强规则
            column_name='user_id',
            description='用户ID不能为空，失败会阻塞下游任务'
        )
        print(f"✅ 创建强规则: {rule1.name} (ID: {rule1.id})")
        
        # 规则2: 唯一性检查 - 弱规则
        rule2 = RuleManager.create_rule(
            session=session,
            asset_id=asset.id,
            name='邮箱唯一性校验',
            rule_type='uniqueness',
            rule_template='字段唯一性校验',
            ge_expectation='expect_column_values_to_be_unique',
            strength='weak',  # 弱规则
            column_name='email',
            description='邮箱应该唯一，失败仅告警'
        )
        print(f"✅ 创建弱规则: {rule2.name} (ID: {rule2.id})")
        
        # 3. 模拟执行校验
        print("\n[步骤 3] 模拟执行校验...")
        start_time = datetime.now()
        history = ValidationHistoryManager.create_history(
            session=session,
            asset_id=asset.id,
            rule_id=rule1.id,
            start_time=start_time
        )
        print(f"🔄 开始校验: {history.id}")
        
        # 模拟校验完成
        from datetime import timedelta
        end_time = start_time + timedelta(seconds=5)
        ValidationHistoryManager.update_history(
            session=session,
            history_id=history.id,
            status='success',
            end_time=end_time,
            pass_rate=98.5,
            total_records=10000,
            failed_records=150
        )
        print(f"✅ 校验完成: 通过率 {98.5}%")
        
        # 4. 创建问题工单（因为发现了异常）
        print("\n[步骤 4] 创建问题工单...")
        issue = IssueManager.create_issue(
            session=session,
            asset_id=asset.id,
            rule_id=rule1.id,
            validation_history_id=history.id,
            title='用户ID存在空值',
            issue_type='system_detected',
            description=f'发现150条记录的用户ID为空，需要修复',
            priority='high',
            assignee='张三'
        )
        print(f"⚠️  创建问题: {issue.title} (状态: {issue.status})")
        
        # 5. 查询统计信息
        print("\n[步骤 5] 查询统计信息...")
        all_assets = AssetManager.get_all_assets(session)
        print(f"📊 总资产数: {len(all_assets)}")
        
        asset_rules = RuleManager.get_rules_by_asset(session, asset.id)
        print(f"📊 资产的规则数: {len(asset_rules)}")
        
        pending_issues = IssueManager.get_issues_by_status(session, 'pending')
        print(f"📊 待处理问题数: {len(pending_issues)}")
        
        asset_histories = ValidationHistoryManager.get_history_by_asset(session, asset.id)
        print(f"📊 校验历史数: {len(asset_histories)}")
        
        # 6. 更新问题状态（模拟治理流程）
        print("\n[步骤 6] 模拟问题治理...")
        IssueManager.update_issue_status(session, issue.id, 'processing')
        print(f"🔄 问题状态更新为: processing")
        
        IssueManager.update_issue_status(session, issue.id, 'resolved')
        print(f"✅ 问题状态更新为: resolved")
        
        # 7. 查看资产详情
        print("\n[步骤 7] 查看资产完整信息...")
        retrieved_asset = AssetManager.get_asset(session, asset.id)
        print(f"\n资产详情:")
        print(f"  名称: {retrieved_asset.name}")
        print(f"  类型: {retrieved_asset.asset_type}")
        print(f"  负责人: {retrieved_asset.owner}")
        print(f"  质量分权重: {retrieved_asset.quality_score_weight}")
        print(f"  关联规则数: {len(retrieved_asset.rules)}")
        print(f"  校验历史数: {len(retrieved_asset.validation_history)}")
        print(f"  问题数: {len(retrieved_asset.issues)}")
        
        print("\n" + "=" * 60)
        print("✅ 示例执行完成！")
        print("=" * 60)
        
    finally:
        session.close()


if __name__ == '__main__':
    demo_basic_usage()
