# GE 1.16 升级说明

## 📌 升级概述

数据质量评估平台已从 Great Expectations 0.18.12 升级到 **1.16.0** 版本。

## 🔧 技术变更

### 核心变化

**旧方式 (GE 0.18.x):**
```python
ge_df = gx.from_pandas(df)
result = ge_df.expect_column_values_to_not_be_null(column="id")
success = result.success
```

**新方式 (GE 1.16.0):**
```python
# 1. 创建临时上下文
context = gx.get_context(mode="ephemeral")

# 2. 添加数据源和资产
datasource = context.data_sources.add_pandas(name="pandas_datasource")
asset = datasource.add_dataframe_asset(name="data_asset")
batch_def = asset.add_batch_definition_whole_dataframe("my_batch")

# 3. 创建期望套件
suite = context.suites.add(gx.ExpectationSuite(name="test_suite"))
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToNotBeNull(column="id")
)

# 4. 创建并运行验证定义
validation_definition = gx.ValidationDefinition(
    name="data_quality_validation",
    data=batch_def,
    suite=suite
)
result = validation_definition.run(batch_parameters={"dataframe": df})

# 5. 解析结果
result_dict = result.to_json_dict()
for exp_result in result_dict['results']:
    success = exp_result['success']
```

### API 对比

| 功能 | GE 0.18.x | GE 1.16.0 |
|------|-----------|-----------|
| 初始化 | `gx.from_pandas(df)` | `ValidationDefinition` |
| 执行期望 | 直接调用方法 | 添加到 Suite 后批量运行 |
| 结果格式 | ValidationResult 对象 | ExpectationSuiteValidationResult |
| 获取结果 | `result.success` | `result.to_json_dict()['success']` |

## ⚠️ 重要注意事项

### 1. RuntimeBatchRequest Bug

GE 1.16.0 的 `RuntimeBatchRequest` 存在已知 bug：
```
AttributeError: 'RuntimeBatchRequest' object has no attribute 'options'
```

**解决方案：** 使用 `ValidationDefinition` 替代。

### 2. Validator 初始化问题

直接使用 `Validator` 类会遇到 `active_batch cannot be None` 错误。

**解决方案：** 通过 `ValidationDefinition` 管理 batch。

### 3. 期望类命名规则

GE 1.x 使用类而不是方法：
- `expect_column_values_to_not_be_null` → `ExpectColumnValuesToNotBeNull`
- `expect_column_values_to_be_unique` → `ExpectColumnValuesToBeUnique`
- `expect_column_values_to_be_between` → `ExpectColumnValuesToBeBetween`

转换规则：去掉 `expect_` 前缀，每个单词首字母大写。

## ✅ 验证结果

所有测试已通过：
- ✅ 文件上传功能
- ✅ 数据质量评估（7条规则）
- ✅ 报告生成
- ✅ 成功率计算（85.71%）

运行演示：
```bash
D:\Python\venv310\Scripts\activate.bat
python demo.py
```

## 📚 相关文档

- [VENV_USAGE.md](VENV_USAGE.md) - 虚拟环境使用说明
- [README.md](README.md) - 项目主文档
- [QUICKSTART.md](QUICKSTART.md) - 快速开始指南

## 🔄 回退方案

如需回退到 GE 0.18.12：
```bash
D:\Python\venv310\Scripts\pip.exe install great-expectations==0.18.12
```

但需要同时恢复 `ge_engine.py` 中的旧代码逻辑。

---

**升级日期:** 2026-04-15  
**GE 版本:** 1.16.0  
**Python 版本:** 3.10
