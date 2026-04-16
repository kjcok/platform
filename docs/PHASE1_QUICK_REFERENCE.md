# DataQ 第一阶段 - 快速参考

## 🗄️ 数据库表速查

### assets (资产表)
```python
AssetManager.create_asset(session, name, data_source, asset_type='csv', owner=None, quality_score_weight=1.0)
AssetManager.get_asset(session, asset_id)
AssetManager.get_all_assets(session, is_active=True/False/None)
AssetManager.update_asset(session, asset_id, **kwargs)
AssetManager.delete_asset(session, asset_id)  # 级联删除
```

### rules (规则表)
```python
RuleManager.create_rule(session, asset_id, name, rule_type, rule_template, ge_expectation, 
                       strength='weak', column_name=None, parameters=None)
RuleManager.get_rule(session, rule_id)
RuleManager.get_rules_by_asset(session, asset_id, is_active=True/False/None)
RuleManager.update_rule(session, rule_id, **kwargs)
RuleManager.delete_rule(session, rule_id)
```

### validation_history (校验历史表)
```python
ValidationHistoryManager.create_history(session, asset_id, rule_id, start_time)
ValidationHistoryManager.update_history(session, history_id, status='success/failed', 
                                       pass_rate, total_records, failed_records)
ValidationHistoryManager.get_history(session, history_id)
ValidationHistoryManager.get_history_by_asset(session, asset_id, limit=10)
```

### issues (问题清单表)
```python
IssueManager.create_issue(session, asset_id, title, issue_type='system_detected',
                         rule_id=None, validation_history_id=None, priority='medium',
                         assignee=None, reporter=None, status='pending')
IssueManager.get_issue(session, issue_id)
IssueManager.get_issues_by_status(session, status='pending', limit=50)
IssueManager.get_issues_by_assignee(session, assignee, status=None)
IssueManager.update_issue_status(session, issue_id, new_status)
# 状态: pending → processing → resolved
#       pending → ignored / whitelisted
```

### exception_data (异常数据归档表)
```python
ExceptionDataManager.add_exception(session, validation_history_id, asset_id, rule_id,
                                  row_number=None, column_name=None, 
                                  actual_value=None, expected_value=None, full_record=None)
ExceptionDataManager.get_exceptions_by_history(session, validation_history_id, limit=100)
ExceptionDataManager.count_exceptions_by_history(session, validation_history_id)
```

---

## 🔑 关键字段说明

### 规则类型 (rule_type)
- `completeness` - 完整性
- `uniqueness` - 唯一性
- `timeliness` - 及时性
- `validity` - 有效性
- `consistency` - 一致性
- `stability` - 稳定性
- `custom_sql` - 自定义SQL

### 规则强度 (strength)
- `strong` - 强规则（失败阻塞下游）
- `weak` - 弱规则（失败仅告警）

### 问题状态 (status)
- `pending` - 待处理
- `processing` - 整改中
- `resolved` - 已处理
- `ignored` - 已忽略
- `whitelisted` - 白名单

### 问题类型 (issue_type)
- `system_detected` - 系统识别
- `manual_feedback` - 人工反馈

### 优先级 (priority)
- `high` - 高
- `medium` - 中
- `low` - 低

---

## 💻 常用代码片段

### 初始化数据库
```python
from models import init_db, get_session

init_db()  # 创建所有表
session = get_session()
```

### 完整工作流示例
```python
# 1. 创建资产
asset = AssetManager.create_asset(session, 'user_table', 'data/users.csv', owner='张三')

# 2. 创建规则
rule = RuleManager.create_rule(
    session, asset.id, '用户ID非空', 'completeness', 
    '字段空值校验', 'expect_column_values_to_not_be_null',
    strength='strong', column_name='user_id'
)

# 3. 执行校验（第二阶段实现）
# history = run_validation(asset, rule)

# 4. 如果失败，自动创建问题
if history.status == 'failed':
    issue = IssueManager.create_issue(
        session, asset.id, '用户ID存在空值',
        rule_id=rule.id, validation_history_id=history.id,
        priority='high', assignee='张三'
    )

# 5. 治理流程
IssueManager.update_issue_status(session, issue.id, 'processing')
# ... 修复数据 ...
IssueManager.update_issue_status(session, issue.id, 'resolved')
```

### 查询统计
```python
# 获取所有待处理问题
pending_issues = IssueManager.get_issues_by_status(session, 'pending')

# 获取某人的问题
my_issues = IssueManager.get_issues_by_assignee(session, '张三', status='pending')

# 获取资产的校验历史
histories = ValidationHistoryManager.get_history_by_asset(session, asset_id=1, limit=10)

# 统计异常数量
count = ExceptionDataManager.count_exceptions_by_history(session, history_id=1)
```

---

## 🧪 测试命令

```bash
# 激活虚拟环境
D:\Python\venv310\Scripts\activate.bat

# 运行数据库模型测试
python tests\scripts\test_models.py

# 运行使用示例
python tests\scripts\db_usage_example.py

# 运行原有应用测试
python tests\scripts\test_app.py

# 重置数据库
python tests\scripts\init_database.py
```

---

## 📂 文件位置

| 文件 | 路径 |
|------|------|
| 数据库模型 | `src/backend/models.py` |
| 管理器类 | `src/backend/db_utils.py` |
| 测试用例 | `tests/scripts/test_models.py` |
| 使用示例 | `tests/scripts/db_usage_example.py` |
| 详细文档 | `docs/PHASE1_DATABASE_MODEL.md` |
| 完成总结 | `docs/PHASE1_COMPLETION_SUMMARY.md` |
| SQLite数据库 | `config/dataq.db` |

---

## ⚠️ 注意事项

1. **会话管理**：使用后务必关闭 session
   ```python
   try:
       # 操作数据库
       pass
   finally:
       session.close()
   ```

2. **级联删除**：删除资产会同时删除相关规则、历史、问题
   ```python
   AssetManager.delete_asset(session, asset_id)  # 谨慎操作
   ```

3. **事务提交**：管理器类会自动 commit，无需手动调用

4. **编码问题**：避免在 print 中使用 emoji，Windows GBK 不支持

---

## 🚀 下一步

第二阶段将实现：
- 从数据库动态读取规则配置
- 执行 GE 校验并保存结果
- 强/弱规则控制逻辑
- 自动归档异常数据
- 自动生成问题工单

详见：`docs/PHASE1_COMPLETION_SUMMARY.md`
