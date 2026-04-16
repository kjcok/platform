"""
第二阶段使用示例：质量执行引擎
演示如何使用 QualityRunner 执行基于数据库配置的质量校验
"""
import sys
import os
# 添加后端代码路径到系统路径
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'backend')
sys.path.insert(0, backend_path)

from models import init_db, get_session
from db_utils import AssetManager, RuleManager
from quality_runner import QualityRunner, run_quality_check


def demo_quality_runner():
    """演示 QualityRunner 的使用"""
    print("=" * 70)
    print("DataQ 第二阶段 - 质量执行引擎使用示例")
    print("=" * 70)
    
    # 初始化数据库
    init_db()
    session = get_session()
    
    try:
        # 1. 准备测试数据
        print("\n[步骤 1] 准备测试数据...")
        import pandas as pd
        
        test_data = {
            'user_id': [1, 2, 3, 4, 5],
            'name': ['张三', '李四', '王五', '赵六', '钱七'],
            'age': [25, 30, 35, 40, 45],
            'email': [
                'zhang@test.com',
                'li@test.com', 
                'wang@test.com',
                'zhao@test.com',
                'qian@test.com'
            ]
        }
        df = pd.DataFrame(test_data)
        
        test_file = 'temp/quality_demo.csv'
        os.makedirs('temp', exist_ok=True)
        df.to_csv(test_file, index=False)
        print(f"✅ 创建测试数据: {test_file} ({len(df)} 行)")
        
        # 2. 创建监控资产
        print("\n[步骤 2] 创建监控资产...")
        asset = AssetManager.create_asset(
            session=session,
            name='用户信息表',
            data_source=test_file,
            asset_type='csv',
            owner='数据管理员',
            quality_score_weight=8.0,
            description='系统用户基本信息表'
        )
        print(f"✅ 创建资产: {asset.name} (ID: {asset.id})")
        
        # 3. 创建质量规则
        print("\n[步骤 3] 创建质量规则...")
        
        # 规则1: 强规则 - 用户ID唯一性
        rule1 = RuleManager.create_rule(
            session=session,
            asset_id=asset.id,
            name='用户ID唯一性校验',
            rule_type='uniqueness',
            rule_template='字段唯一性校验',
            ge_expectation='ExpectColumnValuesToBeUnique',
            strength='strong',  # 强规则
            column_name='user_id',
            description='用户ID必须唯一，失败会阻塞下游任务'
        )
        print(f"✅ 创建强规则: {rule1.name}")
        
        # 规则2: 弱规则 - 邮箱非空
        rule2 = RuleManager.create_rule(
            session=session,
            asset_id=asset.id,
            name='邮箱非空校验',
            rule_type='completeness',
            rule_template='字段空值校验',
            ge_expectation='ExpectColumnValuesToNotBeNull',
            strength='weak',  # 弱规则
            column_name='email',
            description='邮箱不能为空，失败仅告警'
        )
        print(f"✅ 创建弱规则: {rule2.name}")
        
        # 规则3: 弱规则 - 年龄范围
        rule3 = RuleManager.create_rule(
            session=session,
            asset_id=asset.id,
            name='年龄范围校验',
            rule_type='validity',
            rule_template='数值范围校验',
            ge_expectation='ExpectColumnValuesToBeBetween',
            strength='weak',
            column_name='age',
            parameters='{"min_value": 0, "max_value": 150}',
            description='年龄应在0-150之间'
        )
        print(f"✅ 创建弱规则: {rule3.name}")
        
        # 4. 执行质量校验
        print("\n[步骤 4] 执行质量校验...")
        runner = QualityRunner(session=session)
        
        result = runner.run_asset_validation(
            asset_id=asset.id,
            auto_archive=True,      # 自动归档异常数据
            auto_create_issue=True  # 自动创建问题工单
        )
        
        print(f"\n📊 校验结果汇总:")
        print(f"  资产名称: {result['asset_name']}")
        print(f"  总规则数: {result['total_rules']}")
        print(f"  通过数: {result['passed_rules']}")
        print(f"  失败数: {result['failed_rules']}")
        print(f"  时间戳: {result['timestamp']}")
        
        print(f"\n📋 详细结果:")
        for i, r in enumerate(result['results'], 1):
            status_icon = "✅" if r['success'] else "❌"
            print(f"  {i}. {status_icon} {r['rule_name']}")
            print(f"     类型: {r['rule_type']} | 强度: {r['strength']}")
            print(f"     状态: {r['status']} | 通过率: {r.get('pass_rate', 'N/A')}%")
            if r.get('validation_history_id'):
                print(f"     历史记录ID: {r['validation_history_id']}")
        
        # 5. 查询校验历史
        print("\n[步骤 5] 查询校验历史...")
        from db_utils import ValidationHistoryManager
        histories = ValidationHistoryManager.get_history_by_asset(session, asset.id, limit=5)
        print(f"📊 找到 {len(histories)} 条校验历史:")
        for h in histories:
            print(f"  - 规则ID: {h.rule_id}, 状态: {h.status}, 通过率: {h.pass_rate}%")
        
        # 6. 查询问题工单
        print("\n[步骤 6] 查询问题工单...")
        from db_utils import IssueManager
        issues = IssueManager.get_issues_by_status(session, 'pending')
        print(f"📊 待处理问题数: {len(issues)}")
        for issue in issues:
            print(f"  - {issue.title}")
            print(f"    优先级: {issue.priority} | 负责人: {issue.assignee}")
        
        # 7. 模拟问题治理流程
        if issues:
            print("\n[步骤 7] 模拟问题治理...")
            issue = issues[0]
            print(f"  处理问题: {issue.title}")
            
            # 更新为整改中
            IssueManager.update_issue_status(session, issue.id, 'processing')
            print(f"  🔄 状态更新为: processing")
            
            # 模拟修复后重新校验
            print(f"  🔧 修复数据后重新校验...")
            result2 = runner.run_asset_validation(
                asset_id=asset.id,
                rule_ids=[issue.rule_id],
                auto_archive=True,
                auto_create_issue=False
            )
            
            # 如果通过了，标记为已处理
            if result2['results'][0]['success']:
                IssueManager.update_issue_status(session, issue.id, 'resolved')
                print(f"  ✅ 校验通过，状态更新为: resolved")
        
        print("\n" + "=" * 70)
        print("✅ 示例执行完成！")
        print("=" * 70)
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
        
    finally:
        session.close()


if __name__ == '__main__':
    demo_quality_runner()
