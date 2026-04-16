"""
DataQ API 快速启动和测试脚本
演示如何使用第三阶段的 RESTful API
"""
import sys
import os
import json

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_path = os.path.join(project_root, 'src', 'backend')
sys.path.insert(0, backend_path)

from db_utils import get_session, AssetManager, RuleManager
from quality_runner import QualityRunner


def demo_api_workflow():
    """演示完整的 API 工作流程"""
    
    print("=" * 80)
    print("DataQ API 工作流程演示")
    print("=" * 80)
    print()
    
    session = get_session()
    
    try:
        # 1. 创建资产
        print("[步骤 1] 创建监控资产...")
        asset = AssetManager.create_asset(
            session=session,
            name='用户信息表',
            data_source='users_demo.csv',
            asset_type='csv',
            owner='数据管理员',
            quality_score_weight=8.5,
            description='核心用户数据，需要严格的质量监控'
        )
        print(f"  ✅ 资产创建成功: ID={asset.id}, 名称={asset.name}")
        print()
        
        # 2. 创建质量规则
        print("[步骤 2] 创建质量规则...")
        
        rule1 = RuleManager.create_rule(
            session=session,
            asset_id=asset.id,
            name='用户ID唯一性校验',
            rule_type='uniqueness',
            rule_template='字段唯一性校验',
            ge_expectation='ExpectColumnValuesToBeUnique',
            column_name='user_id',
            strength='strong',
            description='用户ID必须唯一，这是强规则'
        )
        print(f"  ✅ 规则1创建成功: {rule1.name} (强度: {rule1.strength})")
        
        rule2 = RuleManager.create_rule(
            session=session,
            asset_id=asset.id,
            name='邮箱非空校验',
            rule_type='completeness',
            rule_template='字段非空校验',
            ge_expectation='ExpectColumnValuesToNotBeNull',
            column_name='email',
            strength='weak',
            description='邮箱不能为空，这是弱规则'
        )
        print(f"  ✅ 规则2创建成功: {rule2.name} (强度: {rule2.strength})")
        print()
        
        # 3. 查询资产和规则
        print("[步骤 3] 查询资产详情...")
        retrieved_asset = AssetManager.get_asset(session, asset.id)
        rules = RuleManager.get_rules_by_asset(session, asset.id)
        
        print(f"  资产: {retrieved_asset.name}")
        print(f"  规则数量: {len(rules)}")
        for rule in rules:
            print(f"    - {rule.name} ({rule.strength})")
        print()
        
        # 4. 更新资产信息
        print("[步骤 4] 更新资产信息...")
        updated_asset = AssetManager.update_asset(
            session=session,
            asset_id=asset.id,
            owner='张三',
            quality_score_weight=9.0
        )
        print(f"  ✅ 资产负责人更新为: {updated_asset.owner}")
        print(f"  ✅ 质量权重更新为: {updated_asset.quality_score_weight}")
        print()
        
        # 5. 更新规则状态
        print("[步骤 5] 禁用规则...")
        disabled_rule = RuleManager.update_rule(
            session=session,
            rule_id=rule2.id,
            is_active=False
        )
        print(f"  ✅ 规则 '{disabled_rule.name}' 已禁用")
        
        # 重新激活
        reactivated_rule = RuleManager.update_rule(
            session=session,
            rule_id=rule2.id,
            is_active=True
        )
        print(f"  ✅ 规则 '{reactivated_rule.name}' 已重新激活")
        print()
        
        # 6. 统计信息
        print("[步骤 6] 查看统计信息...")
        all_assets = AssetManager.get_all_assets(session, is_active=True)
        all_rules = RuleManager.get_rules_by_asset(session, asset.id, is_active=True)
        
        print(f"  激活的资产总数: {len(all_assets)}")
        print(f"  当前资产的激活规则数: {len(all_rules)}")
        print()
        
        # 7. 清理（可选）
        print("[步骤 7] 清理测试数据...")
        AssetManager.delete_asset(session, asset.id)
        session.commit()
        print(f"  ✅ 资产及其关联数据已删除")
        print()
        
        print("=" * 80)
        print("演示完成！所有操作都成功了 ✅")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def show_api_endpoints():
    """显示可用的 API 端点"""
    
    print("\n" + "=" * 80)
    print("可用的 API 端点")
    print("=" * 80)
    print()
    
    endpoints = [
        ("资产管理", [
            ("GET", "/api/v1/assets", "获取资产列表"),
            ("GET", "/api/v1/assets/<id>", "获取单个资产"),
            ("POST", "/api/v1/assets", "创建资产"),
            ("PUT", "/api/v1/assets/<id>", "更新资产"),
            ("DELETE", "/api/v1/assets/<id>", "删除资产"),
        ]),
        ("规则管理", [
            ("GET", "/api/v1/assets/<asset_id>/rules", "获取规则列表"),
            ("POST", "/api/v1/assets/<asset_id>/rules", "创建规则"),
            ("PUT", "/api/v1/rules/<rule_id>", "更新规则"),
            ("DELETE", "/api/v1/rules/<rule_id>", "删除规则"),
        ]),
        ("校验执行", [
            ("POST", "/api/v1/validations", "执行质量校验"),
            ("GET", "/api/v1/validations/history", "获取校验历史"),
            ("GET", "/api/v1/validations/history/<id>", "获取校验详情"),
        ]),
        ("问题管理", [
            ("GET", "/api/v1/issues", "获取问题列表"),
            ("GET", "/api/v1/issues/<id>", "获取问题详情"),
            ("PUT", "/api/v1/issues/<id>/status", "更新问题状态"),
            ("POST", "/api/v1/issues/<id>/recheck", "重新校验问题"),
        ]),
        ("统计分析", [
            ("GET", "/api/v1/statistics/overview", "获取统计概览"),
        ]),
    ]
    
    for category, eps in endpoints:
        print(f"📁 {category}")
        for method, path, desc in eps:
            print(f"  {method:6} {path:45} {desc}")
        print()


if __name__ == '__main__':
    print()
    demo_api_workflow()
    show_api_endpoints()
    print()
    print("提示: 要启动 Flask 服务器，请运行:")
    print("  python src/backend/app.py")
    print()
