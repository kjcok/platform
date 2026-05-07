# DataQ 平台功能增强工作计划

## 需求背景
用户提出以下功能增强需求：
1. **缺乏验证数据集** - 需要创建标准测试数据集
2. **数据集内容预览** - 上传数据后预览内容
3. **缺乏测试规则全功能验证** - 完善所有规则类型的单元测试
4. **界面显示问题（超长）** - 解决表格超长文本显示
5. **测试结果导出（json）** - 支持校验结果导出为JSON格式

## 项目架构
- **后端框架**: Flask + SQLAlchemy + Great Expectations
- **前端技术**: 原生 JavaScript + HTML/CSS
- **规则引擎**: GE 1.x 版本，支持8种核心规则类型

---

## 任务清单与实施计划

### 任务 1: 创建标准验证数据集
**优先级**: 高
**预计工作量**: 小

**目标**: 创建覆盖所有规则类型的标准测试数据集

**具体内容**:
1. 创建 `tests/data/validation_test_data.csv 文件
2. 数据字段设计：
   - `id`: 整数（测试 unique、type_integer）
   - `name`: 字符串（测试 not_null、type_string）
   - `age`: 整数（测试 between、边界值）
   - `email`: 字符串（测试 match_regex、非空）
   - `gender`: 枚举（测试 in_set）
   - `salary`: 数值（测试 between、type_float）
   - `score`: 浮点数（测试 type_float）
   - `grade`: 字符串（测试 in_set）
   - `create_time`: 时间戳
   - `update_time`: 时间戳（测试 column_pair_greater_than）

3. 包含的测试场景：
   - ✅ 正常数据（前10行）
   - ❌ 空值/缺失值（行11-15）
   - ❌ 重复ID（行16）
   - ❌ 非法邮箱格式
   - ❌ 超出范围的年龄（负数、过大值）
   - ❌ 负数薪资
   - ❌ 不在枚举范围内的 gender/grade
   - ❌ 超长字符串（测试界面截断）

**验收标准**:
- CSV文件格式正确，可被pandas正常读取
- 包含所有8种规则类型的测试用例数据
- 既有正常数据也有异常数据

---

### 任务 2: 实现数据集内容预览功能
**优先级**: 高
**预计工作量**: 中

**目标**: 上传文件后支持预览数据前N行

**后端实现** (`src/backend/api/routes.py`):
1. 新增API端点：`GET /api/v1/assets/<int:asset_id>/preview`
2. 新增API端点：`POST /api/v1/upload/preview`（上传后立即预览）
3. 实现逻辑：
   - 读取CSV/Excel文件前N行（默认20行）
   - 返回JSON格式：列名、数据行、总行数、总列数
   - 支持参数 `rows` 自定义预览行数

**API响应格式**:
```json
{
  "status": "success",
  "data": {
    "columns": ["id", "name", "age", ...],
    "rows": [[1, "张三", 25, ...], ...],
    "total_rows": 100,
    "total_columns": 10,
    "preview_rows": 20
  }
}
```

**前端实现**:
1. `asset_detail.html`: 添加"数据预览"标签页
2. `asset_detail.js`: 调用预览API，渲染表格
3. `assets.js`: 资产列表添加预览快捷按钮
4. 表格样式：支持横向滚动，超长单元格截断 + tooltip

**验收标准**:
- 上传文件后可立即预览前20行数据
- 资产详情页有专门的数据预览标签
- 大文件预览不超时（<3秒）
- 超长文本正确显示（截断+悬浮提示）

---

### 任务 3: 全功能规则验证单元测试
**优先级**: 高
**预计工作量**: 中

**目标**: 为所有8种规则类型编写完整单元测试

**测试文件**: `tests/scripts/test_all_rules.py`

**测试覆盖的规则类型**:
1. **not_null** - 非空检查
   - ✅ 所有值非空 → 通过
   - ❌ 存在空值 → 失败
   - ❌ 存在空字符串 → 失败

2. **unique** - 唯一性检查
   - ✅ 所有值唯一 → 通过
   - ❌ 存在重复值 → 失败

3. **between** - 数值范围
   - ✅ 值在范围内 → 通过
   - ❌ 值小于最小值 → 失败
   - ❌ 值大于最大值 → 失败
   - ✅ 等于边界值 → 通过

4. **in_set** - 枚举值检查
   - ✅ 所有值在集合内 → 通过
   - ❌ 存在不在集合内的值 → 失败

5. **match_regex** - 正则匹配
   - ✅ 邮箱格式正确 → 通过
   - ❌ 邮箱格式错误 → 失败
   - ✅ 空值（结合not_null）→ 正确处理

6. **type_string** - 字符串类型
   - ✅ 字符串类型 → 通过
   - ❌ 数值/其他类型 → 失败

7. **type_integer** - 整数类型
   - ✅ 整数 → 通过
   - ❌ 浮点数/字符串 → 失败
   - ✅ 边界值（0、负数、大数）→ 通过

8. **type_float** - 浮点数类型
   - ✅ 浮点数 → 通过
   - ✅ 整数（兼容）→ 通过
   - ❌ 字符串 → 失败

9. **column_pair_greater_than** - 两列比较
   - ✅ A列值 > B列值 → 通过
   - ❌ A列值 <= B列值 → 失败
   - ❌ 空值比较 → 正确处理

**额外测试场景**:
- 强规则 vs 弱规则
- 多规则同时执行
- 异常数据归档
- 问题工单自动创建

**验收标准**:
- 测试文件可独立运行 `python -m pytest tests/scripts/test_all_rules.py -v`
- 所有测试用例通过（≥30个测试用例）
- 测试覆盖率 ≥ 80%

---

### 任务 4: 修复界面超长文本显示
**优先级**: 中
**预计工作量**: 小

**目标**: 解决表格中超长文本的显示问题

**修改文件**:
1. `src/frontend/static/css/style.css`:
```css
/* 表格单元格截断样式 */
.table-cell-truncate {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* 悬浮时显示完整内容 */
.table-cell-truncate:hover {
    overflow: visible;
    white-space: normal;
    word-break: break-all;
    background-color: #fffbeb;
    z-index: 100;
    position: relative;
}
```

2. 所有表格页面应用样式：
   - `assets.html` - 资产列表
   - `issues.html` - 问题列表
   - `validations.html` - 校验历史
   - `rule_management.html` - 规则列表
   - `asset_detail.html` - 资产详情规则列表

**实现方式**:
- 表格 `<td>` 添加 `class="table-cell-truncate" title="完整内容"`
- JavaScript 动态添加 title 属性

**验收标准**:
- 所有表格超长文本正确截断（最大200px）
- 鼠标悬浮时显示完整内容tooltip
- 不影响表格布局和响应式

---

### 任务 5: 测试结果JSON导出功能
**优先级**: 高
**预计工作量**: 中

**目标**: 支持将校验结果导出为JSON文件

**后端实现** (`src/backend/api/routes.py`):
1. 新增API端点：`GET /api/v1/validations/history/<int:history_id>/export/json`
2. 导出内容包含：
   - 基本信息：资产名称、执行时间、触发方式
   - 统计汇总：总规则数、通过数、失败数、成功率
   - 详细结果：每个规则的校验结果
   - 异常数据：失败规则的异常值列表

**JSON导出格式**:
```json
{
  "export_time": "2024-01-15T10:30:00",
  "version": "1.0",
  "validation_summary": {
    "asset_id": 1,
    "asset_name": "测试数据",
    "start_time": "2024-01-15T10:00:00",
    "end_time": "2024-01-15T10:00:05",
    "trigger_type": "manual",
    "total_rules": 8,
    "passed_rules": 5,
    "failed_rules": 3,
    "success_rate": 62.5
  },
  "rule_results": [
    {
      "rule_id": 1,
      "rule_name": "ID非空检查",
      "rule_type": "not_null",
      "column_name": "id",
      "success": true,
      "pass_rate": 100.0,
      "total_records": 100,
      "failed_records": 0,
      "exception_values": []
    }
  ]
}
```

**前端实现**:
1. `validation_detail.html`: 添加"导出JSON"按钮
2. `validations.html`: 历史列表每行添加导出按钮
3. JavaScript: 调用API，触发浏览器下载
   - 文件名格式：`validation_result_{history_id}_{timestamp}.json`

**验收标准**:
- 点击导出按钮正确下载JSON文件
- JSON格式正确，包含所有必要信息
- 文件命名规范，内容完整

---

### 任务 6: 集成验收测试
**优先级**: 中
**预计工作量**: 小

**目标**: 端到端验证所有功能

**测试场景**:
1. 上传标准测试数据集
2. 预览数据内容
3. 配置所有类型规则
4. 执行校验，查看结果
5. 导出JSON结果
6. 验证界面超长文本显示

**验收标准**:
- 所有功能正常工作
- 无明显bug
- 性能可接受

---

## 执行顺序与依赖关系

```
任务1 (数据集)
   ↓
任务2 (数据预览) → 依赖: 任务1
   ↓
任务3 (单元测试) → 依赖: 任务1
   ↓
任务4 (界面修复)
   ↓
任务5 (JSON导出)
   ↓
任务6 (集成测试) → 依赖: 任务2,3,4,5
```

**可并行任务**: 任务4（界面修复）可与任务2、3并行执行

---

## 技术风险与注意事项

### 风险点
1. **GE版本兼容性**: 确保测试用例与GE 1.x API兼容
2. **大文件性能**: 预览大文件时注意内存使用
3. **后端-前端数据格式**: 确保JSON导出格式前后端一致

### 质量保障
- 每个功能完成后编写单元测试
- 代码review确保质量
- 最终集成测试验证整体功能

---

## 预期成果

1. ✅ 标准测试数据集，支持所有规则类型测试
2. ✅ 数据预览功能（上传后 + 资产详情页）
3. ✅ 完整的规则单元测试套件（≥30个测试用例）
4. ✅ 界面超长文本优雅显示
5. ✅ 校验结果JSON导出功能
6. ✅ 所有功能集成测试通过

---

## 下一步操作

计划已完成，请选择：
- **[开始执行]** - 立即按计划开始实施
- **[需要修改]** - 提出调整需求
- **[仅确认]** - 审核后执行