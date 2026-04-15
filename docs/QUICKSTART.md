# 快速开始指南

## 🚀 5分钟快速体验

### 1. 安装依赖（首次使用）

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动。

### 3. 访问平台

打开浏览器访问：`http://localhost:5000`

### 4. 上传数据并评估

**方式一：使用 Web 界面**

1. 点击"选择数据文件"按钮
2. 选择 `sample_data.csv`（示例数据已提供）
3. 系统自动识别字段：id, name, age, email, gender, salary, department
4. 添加质量规则，例如：
   - id → 唯一性检查
   - age → 数值范围 (18-65)
   - email → 非空检查
   - gender → 枚举值检查 (男/女)
5. 点击"开始测评"
6. 查看生成的 HTML 报告

**方式二：使用演示脚本**

```bash
python demo.py
```

这将自动完成上传、配置规则、执行评估的全过程，并在 `reports/` 目录生成报告。

### 5. 运行测试

```bash
python test_app.py
```

所有 13 个测试用例应该全部通过 ✅

---

## 📋 支持的规则类型

| 规则 | 说明 | 示例 |
|------|------|------|
| not_null | 非空检查 | 确保字段不为空 |
| unique | 唯一性检查 | 确保字段值不重复 |
| between | 数值范围 | age 在 18-65 之间 |
| in_set | 枚举值检查 | gender 只能是"男"或"女" |
| match_regex | 正则匹配 | 邮箱格式验证 |
| type_string | 字符串类型 | 确保是文本类型 |
| type_integer | 整数类型 | 确保是整数 |
| type_float | 浮点数类型 | 确保是小数 |

---

## 🎯 示例数据说明

`sample_data.csv` 包含 20 条员工记录，故意设置了以下问题用于测试：

- **第 11 条记录**：缺少 age 值（测试非空检查）
- **ID 不连续**：缺少 ID=19 的记录（测试唯一性和完整性）

预期评估结果：
- 成功率约 85%
- age 字段的非空检查会失败
- 其他规则应该通过

---

## 🔧 API 使用示例

### Python 代码调用

```python
import requests

# 1. 上传文件
with open('data.csv', 'rb') as f:
    response = requests.post('http://localhost:5000/api/upload', 
                           files={'file': f})
file_id = response.json()['file_id']

# 2. 配置规则
rules = [
    {"column": "id", "rule_type": "unique"},
    {"column": "age", "rule_type": "between", 
     "params": {"min_value": 0, "max_value": 100}}
]

# 3. 执行评估
response = requests.post('http://localhost:5000/api/evaluate',
                       json={"file_id": file_id, "rules": rules})
report_url = response.json()['report_url']

print(f"报告地址: http://localhost:5000{report_url}")
```

### cURL 命令

```bash
# 上传文件
curl -X POST -F "file=@sample_data.csv" http://localhost:5000/api/upload

# 执行评估
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "file_id": "data_xxx.csv",
    "rules": [
      {"column": "id", "rule_type": "unique"}
    ]
  }' \
  http://localhost:5000/api/evaluate
```

---

## 📊 解读评估报告

报告包含以下部分：

1. **总体摘要**
   - 成功率百分比
   - 通过/失败规则数量
   - 总记录数和字段数

2. **详细结果表格**
   - 每个字段的规则执行情况
   - 异常数量和比例
   - 异常值示例（最多显示 10 个）

3. **视觉指示**
   - ✅ 绿色 = 通过
   - ❌ 红色 = 失败
   - 进度条显示整体成功率

---

## 💡 常见问题

### Q: 支持多大的文件？
A: 当前版本将数据加载到内存，建议处理不超过 100MB 的文件。

### Q: 如何清理旧文件？
A: 定期删除 `data/` 和 `reports/` 目录中的文件即可。

### Q: 可以连接数据库吗？
A: 第一版本仅支持文件上传。未来版本将支持 MySQL、PostgreSQL 等数据库直连。

### Q: 如何自定义规则？
A: 在 `ge_engine.py` 的 `RULE_MAPPING` 字典中添加新的规则映射即可。

### Q: 报告可以导出为 PDF 吗？
A: 当前仅支持 HTML 格式。可以使用浏览器的"打印为 PDF"功能。

---

## 🆘 获取帮助

- 查看完整文档：[README.md](README.md)
- 查看测试用例：[test_app.py](test_app.py)
- 查看示例脚本：[demo.py](demo.py)

---

**祝您使用愉快！** 🎉
