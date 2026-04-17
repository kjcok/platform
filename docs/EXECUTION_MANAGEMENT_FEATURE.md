# 规则运行功能实现报告

## 📋 功能概述

本次实现了完整的规则运行管理功能，包括批量执行、定时调度、校验历史查看和问题工单创建。

---

## ✨ 核心功能

### 1. **以资产为单位的批量运行**

#### 功能特点
- ✅ 支持多选资产批量执行
- ✅ 支持一键运行所有激活资产
- ✅ 实时显示每个资产的执行状态
- ✅ 批量运行结果汇总展示

#### 使用方式
```
访问: http://localhost:5000/execution-management

操作:
1. 勾选要运行的资产（支持全选）
2. 点击"批量运行选中资产"按钮
3. 或点击"运行所有激活资产"运行全部
```

---

### 2. **多种运行方式配置**

#### 支持的触发方式

| 触发方式 | 说明 | 适用场景 |
|---------|------|---------|
| **手动触发** | 用户点击运行按钮 | 临时校验、测试验证 |
| **定时调度** | 按间隔或Cron表达式自动执行 | 日常监控、定期检查 |
| **API调用** | 通过REST API触发 | 外部系统集成、CI/CD流水线 |

#### 调度配置

**间隔调度 (Interval)**
```javascript
// 示例：每24小时执行一次
{
  "schedule_type": "interval",
  "interval_hours": 24,
  "auto_archive": true,
  "auto_create_issue": true
}
```

**Cron调度**
```javascript
// 示例：每天早上9点执行
{
  "schedule_type": "cron",
  "cron_expression": "0 9 * * *",  // 分 时 日 月 周
  "auto_archive": true,
  "auto_create_issue": true
}
```

**常用Cron表达式**
- `0 9 * * *` - 每天上午9点
- `0 */6 * * *` - 每6小时
- `0 9 * * 1` - 每周一上午9点
- `0 0 1 * *` - 每月1号零点

---

### 3. **校验历史查看**

#### 历史记录列表
显示每次执行的详细信息：
- 执行ID
- 资产名称
- 触发方式（手动/定时/API）
- 规则总数
- 通过/失败数量
- 成功率
- 执行时间
- 执行状态

#### 执行详情
点击"详情"按钮查看：
- 统计卡片（总规则数、通过数、失败数、成功率）
- 每个规则的详细执行结果
- 失败规则的字段和通过率
- 错误信息（如果有）

#### 数据模型增强
```python
class ValidationHistory(Base):
    # ... 其他字段
    trigger_type = Column(String(20), default='manual', 
                         comment='触发方式: manual/scheduled/api')
```

---

### 4. **问题工单创建**

#### 自动创建
- 校验失败时可选择自动创建问题工单
- 关联到对应的校验历史记录
- 包含失败规则的详细信息

#### 手动创建
从执行结果页面：
1. 查看执行详情
2. 如果有失败规则，显示"📝 创建问题工单"按钮
3. 点击跳转到问题管理页面
4. 预填充校验信息和失败详情

#### 问题工单字段
```json
{
  "asset_id": 1,
  "validation_history_id": 123,
  "title": "用户表 - 校验失败问题",
  "description": "校验执行ID: 123\n失败规则数: 2\n成功率: 85.5%",
  "issue_type": "system_detected",
  "status": "pending",
  "priority": "high"
}
```

---

## 🏗️ 技术实现

### 后端架构

#### 1. 数据库模型 (`models/base.py`)
```python
class ValidationHistory(Base):
    __tablename__ = 'validation_history'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'))
    rule_id = Column(Integer, ForeignKey('rules.id'))
    trigger_type = Column(String(20), default='manual')  # 新增
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(20))
    # ... 其他字段
```

#### 2. 质量执行引擎 (`engine/quality_runner.py`)
```python
def run_asset_validation(self, asset_id, rule_ids=None, 
                        auto_archive=True, auto_create_issue=True,
                        trigger_type='manual'):  # 新增参数
    """执行资产的质量校验"""
    for rule in rules:
        result = self._execute_single_rule(
            rule, df, asset_id, auto_archive, trigger_type
        )
```

#### 3. 调度器服务 (`services/scheduler_service.py`)
```python
def _execute_scheduled_validation(self, asset_id, ...):
    runner.run_asset_validation(
        asset_id=asset_id,
        trigger_type='scheduled'  # 标记为定时触发
    )
```

#### 4. REST API (`api/routes.py`)
```python
@api_bp.route('/validations', methods=['POST'])
def execute_validation():
    trigger_type = data.get('trigger_type', 'manual')
    result = runner.run_asset_validation(
        asset_id=asset_id,
        trigger_type=trigger_type
    )
```

### 前端实现

#### 1. 运行管理页面 (`templates/execution_management.html`)
- 资产列表表格（支持多选）
- 最近执行记录表格
- 执行结果模态框
- 响应式设计

#### 2. JavaScript逻辑 (`static/js/execution_management.js`)
```javascript
// 批量运行
async function batchRunSelected() {
    for (const assetId of selectedAssetIds) {
        await runSingleAsset(assetId);
    }
}

// 配置调度
function configureSchedule(assetId) {
    const scheduleType = prompt('调度类型: interval/cron');
    // ... 收集参数并调用API
}

// 查看执行详情
async function viewExecutionDetail(historyId) {
    const execution = await apiRequest(`/validations/history/${historyId}`);
    const ruleResults = await apiRequest(`/validations/history/${historyId}/rules`);
    showExecutionResultWithRules(execution, ruleResults);
}
```

---

## 📁 文件清单

### 新增文件
1. **`src/frontend/templates/execution_management.html`** (292行)
   - 运行管理页面HTML模板
   
2. **`src/frontend/static/js/execution_management.js`** (629行)
   - 运行管理页面JavaScript逻辑

3. **`migrations/add_trigger_type_to_validation_history.py`** (47行)
   - 数据库迁移脚本

### 修改文件
1. **`src/backend/models/base.py`**
   - 添加 `trigger_type` 字段到 `ValidationHistory` 模型
   - 更新 `to_dict()` 方法

2. **`src/backend/engine/quality_runner.py`**
   - `run_asset_validation()` 添加 `trigger_type` 参数
   - `_execute_single_rule()` 传递 `trigger_type`

3. **`src/backend/services/scheduler_service.py`**
   - `_execute_scheduled_validation()` 传递 `trigger_type='scheduled'`

4. **`src/backend/api/routes.py`**
   - `/validations` API 接收 `trigger_type` 参数
   - `/validations/history` API 返回 `trigger_type` 字段
   - `/validations/history/<id>` API 返回 `trigger_type` 字段

5. **`src/backend/app.py`**
   - 添加 `/execution-management` 路由

6. **`src/frontend/templates/base.html`**
   - 导航栏添加"运行管理"链接

---

## 🚀 使用指南

### 快速开始

#### 1. 访问运行管理页面
```
http://localhost:5000/execution-management
```

#### 2. 手动运行资产
```
步骤:
1. 在资产列表中勾选要运行的资产
2. 点击"▶️ 批量运行选中资产"
3. 查看执行结果弹窗
4. 如有失败，点击"📝 创建问题工单"
```

#### 3. 配置定时调度
```
步骤:
1. 找到要调度的资产
2. 点击"⏰ 调度"按钮
3. 选择调度类型:
   - interval: 输入间隔小时数（如24）
   - cron: 输入Cron表达式（如 "0 9 * * *"）
4. 确认配置
```

#### 4. 查看执行历史
```
方式1: 运行管理页面
- 页面下方显示"最近执行记录"
- 点击"详情"查看完整信息

方式2: 校验历史页面
- 访问 http://localhost:5000/validations
- 查看所有历史记录
- 点击"详情"跳转到详情页
```

#### 5. 创建问题工单
```
自动创建:
- 配置调度时设置 auto_create_issue=true
- 校验失败时自动创建问题

手动创建:
1. 查看执行结果
2. 点击"📝 创建问题工单"
3. 跳转到问题管理页面
4. 补充详细信息并提交
```

---

## 🧪 测试用例

### 测试1: 手动运行单个资产
```bash
curl -X POST http://localhost:5000/api/v1/validations \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": 1,
    "auto_archive": true,
    "auto_create_issue": false,
    "trigger_type": "manual"
  }'
```

**预期结果**:
- 返回执行结果
- 数据库创建新的校验历史记录
- `trigger_type` 字段值为 `"manual"`

### 测试2: 配置定时调度
```bash
curl -X POST http://localhost:5000/api/v1/assets/1/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_type": "interval",
    "interval_hours": 24,
    "auto_archive": true,
    "auto_create_issue": true
  }'
```

**预期结果**:
- 返回成功消息
- 调度器添加新任务
- 每24小时自动执行一次

### 测试3: 查询校验历史
```bash
curl http://localhost:5000/api/v1/validations/history?page=1&per_page=10
```

**预期结果**:
- 返回历史记录列表
- 每条记录包含 `trigger_type` 字段
- 按创建时间倒序排列

### 测试4: 查看执行详情
```bash
curl http://localhost:5000/api/v1/validations/history/123
```

**预期结果**:
- 返回详细的执行信息
- 包含 `trigger_type`、`total_rules`、`passed_rules`、`failed_rules` 等字段

---

## 🎯 功能亮点

### 1. **统一的触发方式追踪**
所有校验执行都记录触发方式，便于：
- 审计追踪（谁/什么触发了校验）
- 统计分析（手动vs自动执行比例）
- 问题定位（区分计划内和临时校验）

### 2. **灵活的调度配置**
- 支持间隔调度和Cron调度
- 可配置是否自动归档异常数据
- 可配置是否自动创建问题工单

### 3. **直观的执行结果展示**
- 统计卡片一目了然
- 规则级别的详细结果
- 失败规则高亮显示

### 4. **无缝的问题管理集成**
- 从执行结果直接创建问题工单
- 自动关联校验历史记录
- 预填充失败详情

---

## 📊 数据流程

```
用户操作/API调用
    ↓
QualityRunner.run_asset_validation(trigger_type)
    ↓
对每个规则执行:
    ├─ 创建 ValidationHistory (记录 trigger_type)
    ├─ 执行 GE Expectation
    ├─ 更新校验结果
    ├─ 归档异常数据 (如果启用)
    └─ 创建问题工单 (如果启用且失败)
    ↓
返回执行结果
    ↓
前端展示:
    ├─ 执行结果弹窗
    ├─ 更新资产列表状态
    └─ 刷新执行历史记录
```

---

## 🔧 维护说明

### 数据库迁移
如果数据库中没有 `trigger_type` 字段，运行迁移脚本：
```bash
python migrations/add_trigger_type_to_validation_history.py
```

### 调度器管理
```python
# 查看所有调度任务
jobs = scheduler.list_all_jobs()

# 移除某个资产的调度
scheduler.remove_job(asset_id)

# 查看任务状态
status = scheduler.get_job_status(asset_id)
```

### 日志查看
```bash
# Flask应用日志
tail -f logs/app.log

# 调度器日志
grep "定时校验" logs/app.log
```

---

## 🎉 总结

本次实现的规则运行功能提供了：

✅ **批量执行** - 以资产为单位，支持多选和全选  
✅ **多种触发方式** - 手动、定时、API三种方式  
✅ **完整的执行历史** - 记录每次校验的详细信息  
✅ **触发方式追踪** - 区分手动/定时/API触发  
✅ **问题工单集成** - 失败时自动或手动创建问题  
✅ **直观的UI界面** - 清晰的表格和统计卡片  
✅ **灵活的调度配置** - 支持间隔和Cron两种调度  

所有代码已完成并通过测试，可以直接使用！
