"""
调试脚本：测试 GE 执行
"""
import sys
import os
sys.path.insert(0, 'src/backend')

from models import init_db, get_session
from db_utils import AssetManager, RuleManager
from quality_runner import QualityRunner
import pandas as pd

# 初始化数据库
init_db()
session = get_session()

# 创建测试数据文件
test_data = {
    'user_id': [1, 2, 3, 4, 5],
    'name': ['张三', '李四', '王五', '赵六', '钱七'],
    'age': [25, 30, 35, 40, 45]
}
df = pd.DataFrame(test_data)
test_file = 'temp/debug_test.csv'
os.makedirs('temp', exist_ok=True)
df.to_csv(test_file, index=False)

print(f"测试数据: {len(df)} 行")
print(df.head())

# 创建资产
asset = AssetManager.create_asset(
    session=session,
    name='debug_test',
    data_source=test_file,
    asset_type='csv',
    owner='测试'
)
print(f"\n创建资产: ID={asset.id}")

# 创建规则
rule = RuleManager.create_rule(
    session=session,
    asset_id=asset.id,
    name='用户ID非空',
    rule_type='completeness',
    rule_template='字段空值校验',
    ge_expectation='ExpectColumnValuesToNotBeNull',
    strength='weak',
    column_name='user_id'
)
print(f"创建规则: ID={rule.id}, GE期望={rule.ge_expectation}")

# 执行校验
print("\n执行校验...")
runner = QualityRunner(session=session)
try:
    result = runner.run_asset_validation(
        asset_id=asset.id,
        rule_ids=[rule.id],
        auto_archive=False,
        auto_create_issue=False
    )
    print(f"\n校验结果:")
    print(f"  总规则数: {result['total_rules']}")
    print(f"  通过数: {result['passed_rules']}")
    print(f"  失败数: {result['failed_rules']}")
    for r in result['results']:
        print(f"  - {r['rule_name']}: {'通过' if r['success'] else '失败'}")
        print(f"    状态: {r.get('status')}")
        if not r['success']:
            print(f"    错误: {r.get('error', 'N/A')}")
except Exception as e:
    print(f"\n异常: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# 清理
session.close()
if os.path.exists(test_file):
    os.remove(test_file)
print("\n[完成]")
