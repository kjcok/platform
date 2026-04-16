# 第一阶段：元数据模型设计与存储层

## 📋 概述

本阶段完成了 DataQ 数质宝的数据库模型设计与实现，使用轻量级的 **SQLite** + **SQLAlchemy ORM** 构建了5张核心表，为后续的质量规则管理、校验执行、问题治理等功能打下基础。

---

## 🗄️ 数据库表结构

### 1. assets (资产表)

记录要监控的数据资产（表、文件等）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| name | String(256) | 资产名称（表名/文件名） |
| asset_type | String(50) | 资产类型: table/csv/excel/database |
| data_source | String(512) | 数据源路径或连接信息 |
| owner | String(256) | 质量负责人 |
| description | Text | 资产描述 |
| quality_score_weight | Float | 质量分权重 (1-10)，默认1.0 |
| is_active | Boolean | 是否启用监控，默认True |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**关系**：
- 一对多：rules（规则）
- 一对多：validation_history（校验历史）
- 一对多：issues（问题）

---

### 2. rules (规则表)

记录质量校验规则的配置

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| asset_id | Integer | 外键 → assets.id |
| name | String(256) | 规则名称 |
| column_name | String(256) | 校验字段名，NULL表示全表级别 |
| rule_type | String(50) | 规则类型: completeness/uniqueness/timeliness/validity/consistency/stability/custom_sql |
| rule_template | String(100) | 规则模板名称 |
| ge_expectation | String(200) | 对应的GE Expectation类名 |
| parameters | Text | 规则参数(JSON格式) |
| strength | String(20) | 规则强度: strong(强规则)/weak(弱规则) |
| is_active | Boolean | 是否生效，默认True |
| description | Text | 规则描述 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**关系**：
- 多对一：asset（所属资产）
- 一对多：validation_history（校验历史）
- 一对多：issues（问题）

---

### 3. validation_history (校验历史表)

记录每次质量校验的执行结果

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| asset_id | Integer | 外键 → assets.id |
| rule_id | Integer | 外键 → rules.id |
| start_time | DateTime | 校验开始时间 |
| end_time | DateTime | 校验结束时间 |
| status | String(20) | 执行状态: pending/running/success/failed/cancelled |
| pass_rate | Float | 通过率 (0-100) |
| total_records | Integer | 总记录数 |
| failed_records | Integer | 失败记录数 |
| exception_data_path | String(512) | 异常数据存储路径 |
| error_message | Text | 错误信息 |
| execution_log | Text | 执行日志 |
| created_at | DateTime | 创建时间 |

**关系**：
- 多对一：asset（所属资产）
- 多对一：rule（所属规则）

---

### 4. issues (问题清单表)

记录校验发现的质量问题和人工反馈的问题

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| asset_id | Integer | 外键 → assets.id |
| rule_id | Integer | 外键 → rules.id，NULL表示人工反馈 |
| validation_history_id | Integer | 外键 → validation_history.id |
| issue_type | String(50) | 问题类型: system_detected/manual_feedback |
| title | String(512) | 问题标题 |
| description | Text | 问题描述 |
| status | String(20) | 状态: pending/processing/resolved/ignored/whitelisted |
| priority | String(10) | 优先级: high/medium/low |
| assignee | String(256) | 问题负责人 |
| reporter | String(256) | 报告人 |
| attachments | Text | 附件路径列表(JSON格式) |
| contact_info | String(512) | 联系方式 |
| resolved_at | DateTime | 解决时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**关系**：
- 多对一：asset（所属资产）
- 多对一：rule（关联规则）
- 多对一：validation_history（关联校验记录）

---

### 5. exception_data (异常数据归档表)

存储未通过校验的具体脏数据

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| validation_history_id | Integer | 外键 → validation_history.id |
| asset_id | Integer | 外键 → assets.id |
| rule_id | Integer | 外键 → rules.id |
| row_number | Integer | 原始数据行号 |
| column_name | String(256) | 异常字段名 |
| actual_value | Text | 实际值 |
| expected_value | Text | 期望值 |
| error_detail | Text | 错误详情 |
| full_record | Text | 完整记录(JSON格式) |
| created_at | DateTime | 创建时间 |

**关系**：
- 多对一：validation_history（所属校验记录）
- 多对一：asset（所属资产）
- 多对一：rule（关联规则）

---

## 🔧 核心功能模块

### 1. 数据库初始化

```python
from models import init_db, get_session

# 初始化数据库（创建所有表）
init_db()

# 获取数据库会话
session = get_session()
```

### 2. 资产管理器 (AssetManager)

```python
from db_utils import AssetManager

# 创建资产
asset = AssetManager.create_asset(
    session=session,
    name='user_table',
    data_source='path/to/data.csv',
    asset_type='csv',
    owner='张三',
    quality_score_weight=5.0
)

# 获取资产
asset = AssetManager.get_asset(session, asset_id=1)

# 获取所有资产
assets = AssetManager.get_all_assets(session, is_active=True)

# 更新资产
AssetManager.update_asset(session, asset_id=1, owner='李四')

# 删除资产（级联删除相关规则、记录等）
AssetManager.delete_asset(session, asset_id=1)
```

### 3. 规则管理器 (RuleManager)

```python
from db_utils import RuleManager

# 创建规则
rule = RuleManager.create_rule(
    session=session,
    asset_id=1,
    name='用户ID非空校验',
    rule_type='completeness',
    rule_template='字段空值校验',
    ge_expectation='expect_column_values_to_not_be_null',
    strength='strong',  # 强规则
    column_name='user_id'
)

# 获取资产的所有规则
rules = RuleManager.get_rules_by_asset(session, asset_id=1)

# 更新规则
RuleManager.update_rule(session, rule_id=1, strength='weak')

# 删除规则
RuleManager.delete_rule(session, rule_id=1)
```

### 4. 校验历史管理器 (ValidationHistoryManager)

```python
from db_utils import ValidationHistoryManager
from datetime import datetime

# 创建校验历史
history = ValidationHistoryManager.create_history(
    session=session,
    asset_id=1,
    rule_id=1,
    start_time=datetime.now()
)

# 更新校验结果
ValidationHistoryManager.update_history(
    session=session,
    history_id=1,
    status='success',
    end_time=datetime.now(),
    pass_rate=98.5,
    total_records=10000,
    failed_records=150
)

# 获取资产的校验历史
histories = ValidationHistoryManager.get_history_by_asset(session, asset_id=1, limit=10)
```

### 5. 问题管理器 (IssueManager)

```python
from db_utils import IssueManager

# 创建系统识别的问题
issue = IssueManager.create_issue(
    session=session,
    asset_id=1,
    rule_id=1,
    validation_history_id=1,
    title='用户ID存在空值',
    issue_type='system_detected',
    description='发现150条记录的用户ID为空',
    priority='high',
    assignee='张三'
)

# 创建人工反馈的问题
issue = IssueManager.create_issue(
    session=session,
    asset_id=1,
    title='数据格式异常',
    issue_type='manual_feedback',
    reporter='李四',
    contact_info='lisi@example.com'
)

# 更新问题状态
IssueManager.update_issue_status(session, issue_id=1, new_status='processing')
IssueManager.update_issue_status(session, issue_id=1, new_status='resolved')

# 按状态获取问题
pending_issues = IssueManager.get_issues_by_status(session, status='pending')

# 获取负责人的问题
my_issues = IssueManager.get_issues_by_assignee(session, assignee='张三')
```

### 6. 异常数据管理器 (ExceptionDataManager)

```python
from db_utils import ExceptionDataManager

# 添加单字段异常
ExceptionDataManager.add_exception(
    session=session,
    validation_history_id=1,
    asset_id=1,
    rule_id=1,
    row_number=5,
    column_name='user_id',
    actual_value='NULL',
    expected_value='NOT NULL',
    error_detail='字段值为空'
)

# 添加完整记录异常
import json
full_record = json.dumps({'user_id': None, 'name': '张三'})
ExceptionDataManager.add_exception(
    session=session,
    validation_history_id=1,
    asset_id=1,
    rule_id=1,
    row_number=10,
    full_record=full_record
)

# 获取异常数据
exceptions = ExceptionDataManager.get_exceptions_by_history(session, validation_history_id=1, limit=100)

# 统计异常数量
count = ExceptionDataManager.count_exceptions_by_history(session, validation_history_id=1)
```

---

## 🧪 测试用例

所有测试用例位于 `tests/scripts/test_models.py`，共 **28个测试用例**，覆盖：

### 测试覆盖范围

1. **资产管理测试** (6个)
   - 创建、获取、更新、删除资产
   - 筛选激活/未激活资产
   - 级联删除验证

2. **规则管理测试** (5个)
   - 创建、获取、更新、删除规则
   - 按激活状态筛选规则

3. **校验历史测试** (4个)
   - 创建历史记录
   - 更新成功/失败状态
   - 按资产查询历史

4. **问题管理测试** (5个)
   - 创建系统识别/人工反馈问题
   - 更新问题状态
   - 按状态/负责人查询问题

5. **异常数据测试** (4个)
   - 添加单字段/完整记录异常
   - 查询异常数据
   - 统计异常数量

6. **数据库关系测试** (4个)
   - 资产与规则关系
   - 资产与校验历史关系
   - 规则与问题关系
   - 级联删除验证

### 运行测试

```bash
# 激活虚拟环境
D:\Python\venv310\Scripts\activate.bat

# 运行所有测试
python tests\scripts\test_models.py

# 预期输出
Ran 28 tests in 0.843s
OK
```

---

## 📝 使用示例

完整的演示脚本位于 `tests/scripts/db_usage_example.py`：

```bash
python tests\scripts\db_usage_example.py
```

演示内容包括：
1. 创建监控资产
2. 创建强/弱规则
3. 模拟执行校验
4. 创建问题工单
5. 查询统计信息
6. 模拟问题治理流程
7. 查看资产完整信息

---

## 🎯 关键设计要点

### 1. 强规则 vs 弱规则

- **强规则** (`strength='strong'`): 校验失败时会阻塞下游任务
- **弱规则** (`strength='weak'`): 校验失败时仅告警，不影响下游

### 2. 问题状态流转

```
pending (待处理)
  ↓
processing (整改中)
  ↓
resolved (已处理)

或者：
pending → ignored (已忽略)
pending → whitelisted (白名单)
```

### 3. 异常数据归档模式

- **单字段归档**: 只记录异常字段的值
- **完整记录归档**: 记录整条数据的JSON格式

### 4. 级联删除

删除资产时会自动删除：
- 该资产下的所有规则
- 该资产下的所有校验历史
- 该资产下的所有问题
- 相关的异常数据

---

## 📂 文件清单

| 文件 | 说明 |
|------|------|
| `src/backend/models.py` | 数据库模型定义 (5张表) |
| `src/backend/db_utils.py` | 数据库操作工具类 (5个管理器) |
| `tests/scripts/test_models.py` | 单元测试用例 (28个测试) |
| `tests/scripts/init_database.py` | 数据库初始化脚本 |
| `tests/scripts/db_usage_example.py` | 使用示例脚本 |
| `config/dataq.db` | SQLite数据库文件 (自动生成) |

---

## ✅ 完成状态

- ✅ 5张核心表设计与实现
- ✅ SQLAlchemy ORM 映射
- ✅ 5个管理器类封装CRUD操作
- ✅ 28个单元测试全部通过
- ✅ 完整的使用示例
- ✅ 级联删除和关系维护
- ✅ 支持强/弱规则标记
- ✅ 支持问题状态流转
- ✅ 支持异常数据归档

---

## 🚀 下一步

第二阶段将基于此数据库模型改造 Great Expectations 执行引擎，实现：
1. 从数据库动态读取规则配置
2. 执行 GE 校验并保存结果
3. 实现强/弱规则控制逻辑
4. 自动归档异常数据
