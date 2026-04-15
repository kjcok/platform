# 数据质量评估平台 (DataQ)

基于 GB/T 36344-2018 标准的结构化数据质量评估平台，使用 Great Expectations 引擎实现。

## 📁 项目结构

```
platform/
├── src/                    # 程序代码目录
│   ├── backend/           # 后端代码
│   │   ├── app.py        # Flask 主应用
│   │   ├── file_manager.py    # 文件管理模块
│   │   ├── ge_engine.py       # GE 评估引擎
│   │   └── report_renderer.py # 报告渲染器
│   └── frontend/          # 前端代码
│       └── templates/     # HTML 模板
├── docs/                   # 文档目录
│   ├── ARCHITECTURE.md    # 技术架构
│   ├── QUICKSTART.md      # 快速开始
│   ├── VENV_USAGE.md      # 虚拟环境说明
│   └── ...                # 其他文档
├── output/                 # 生成文件目录
│   ├── data/             # 上传的数据文件
│   └── reports/          # 生成的报告文件
├── tests/                  # 测试数据和代码
│   ├── data/             # 测试数据
│   └── scripts/          # 测试脚本
├── config/                 # 配置文件目录
│   ├── requirements.txt  # Python 依赖
│   └── settings.py       # 应用配置
├── temp/                   # 中间过程文件（可随时删除）
├── README.md              # 项目说明（本文件）
├── start.bat              # Windows 启动脚本
└── .gitignore             # Git 忽略配置
```

## 📋 功能特性

### 核心功能
- ✅ **多维质量规则库**
  - 完整性检查（非空验证）
  - 准确性检查（数值范围、枚举值、正则匹配、数据类型）
  - 唯一性检查（重复记录检测）
  - 一致性检查（跨字段逻辑校验）

- ✅ **自动化数据探查**
  - 自动识别数据类型和分布
  - 异常值检测
  - 生成推荐规则

- ✅ **可视化报告**
  - 美观的 HTML 报告
  - 详细的成功/失败统计
  - 异常值示例展示

### 技术特点
- 🚀 极简架构，零配置启动
- 📦 基于成熟的 Great Expectations 引擎
- 🎯 支持 CSV、XLSX、XLS 格式
- 💻 代码量精简（<500 行核心代码）

## 🛠️ 技术栈

- **评测引擎**: Great Expectations 1.16.0
- **数据处理**: Pandas 2.1.4
- **Web 框架**: Flask 3.0.0
- **数据库连接**: SQLAlchemy 2.0.23
- **Excel 支持**: OpenPyXL 3.1.2

### ⚠️ 重要：Python 虚拟环境

**本项目需要使用 Python 3.10 虚拟环境**

```bash
# 激活虚拟环境（Windows）
D:\Python\venv310\Scripts\activate.bat

# 验证环境
python --version  # 应显示 Python 3.10.x
python -c "import great_expectations; print(great_expectations.__version__)"  # 应显示 1.16.0
```

详细使用说明请参考：[VENV_USAGE.md](VENV_USAGE.md)

## 📦 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动。

### 3. 使用平台

1. 打开浏览器访问 `http://localhost:5000`
2. 上传 CSV/Excel 文件
3. 配置质量规则
4. 点击"开始测评"
5. 查看生成的质量报告

## 📁 项目结构

```
/dq_platform
│── app.py                  # Flask 主程序（启动入口）
│── file_manager.py         # 文件与元数据管理模块
│── ge_engine.py            # GE 评测引擎封装
│── report_renderer.py      # 报告渲染器
│── test_app.py             # 测试用例
│── requirements.txt        # Python 依赖
│── sample_data.csv         # 示例数据
│── data/                   # 上传文件存储目录（自动生成）
│── reports/                # 生成的报告目录（自动生成）
└── templates/              # HTML 模板
    ├── index.html          # 前端主页面
    └── report_template.html# 质量评估报告模板
```

## 🔧 API 接口

### 1. 上传文件
```
POST /api/upload
Content-Type: multipart/form-data

参数:
- file: 数据文件（CSV/XLSX/XLS）

返回:
{
  "status": "success",
  "file_id": "data_xxx.csv",
  "columns": ["id", "name", "age"]
}
```

### 2. 执行评估
```
POST /api/evaluate
Content-Type: application/json

请求体:
{
  "file_id": "data_xxx.csv",
  "rules": [
    {"column": "id", "rule_type": "unique"},
    {"column": "age", "rule_type": "between", "params": {"min_value": 0, "max_value": 100}},
    {"column": "email", "rule_type": "not_null"}
  ]
}

返回:
{
  "status": "success",
  "report_url": "/report/report_xxx.html",
  "summary": {
    "success_percent": 85.5,
    "total_rules": 3,
    "passed_rules": 2,
    "failed_rules": 1
  }
}
```

### 3. 查看报告
```
GET /report/<filename>
```

## 📊 支持的规则类型

| 规则类型 | 说明 | 参数示例 |
|---------|------|---------|
| not_null | 非空检查 | 无 |
| unique | 唯一性检查 | 无 |
| between | 数值范围 | min_value, max_value |
| in_set | 枚举值检查 | value_set |
| match_regex | 正则匹配 | regex |
| type_string | 字符串类型 | 无 |
| type_integer | 整数类型 | 无 |
| type_float | 浮点数类型 | 无 |

## 🧪 运行测试

```bash
python test_app.py
```

测试覆盖：
- TC-U1~U3: 文件上传测试
- TC-E1~E5: 评估引擎测试
- TC-R1~R2: 报告渲染测试
- API 接口测试

## 📖 使用示例

### 示例 1: 员工数据质量检查

使用提供的 `sample_data.csv` 文件，可以配置以下规则：

```json
[
  {"column": "id", "rule_type": "unique"},
  {"column": "id", "rule_type": "not_null"},
  {"column": "age", "rule_type": "between", "params": {"min_value": 18, "max_value": 65}},
  {"column": "age", "rule_type": "not_null"},
  {"column": "email", "rule_type": "not_null"},
  {"column": "gender", "rule_type": "in_set", "params": {"value_set": ["男", "女"]}},
  {"column": "salary", "rule_type": "between", "params": {"min_value": 0, "max_value": 100000}}
]
```

该数据集包含故意设置的问题：
- 第 11 条记录缺少 age 值
- ID 为 19 的记录缺失（不连续）

评估报告会清晰显示这些问题。

## 🎯 符合标准

本平台遵循 **GB/T 36344-2018 信息技术 数据质量评价指标** 国家标准，涵盖：

- **规范性** (01): 数据标准、数据模型、元数据、业务规则
- **完整性** (02): 数据元素完整性、数据记录完整性
- **准确性** (03): 数据内容正确性、数据格式合规性、数据唯一性
- **一致性** (04): 相同数据一致性、关联数据一致性
- **时效性** (05): 基于时间段的正确性、及时性
- **可访问性** (06): 数据可访问性、可用性

## 🔮 未来扩展

- [ ] 支持数据库直连（MySQL、PostgreSQL 等）
- [ ] 数据血缘追踪
- [ ] 定时任务调度
- [ ] 规则模板库
- [ ] 多用户权限管理
- [ ] 历史评估记录
- [ ] PDF 报告导出

## 📝 注意事项

1. **内存限制**: 当前版本将数据加载到内存，建议处理不超过 100MB 的文件
2. **并发支持**: 极简版本不支持高并发，生产环境建议使用 Gunicorn + Nginx
3. **文件清理**: 定期清理 `data/` 和 `reports/` 目录以释放空间

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**开发团队**: DataQ Team  
**版本**: v1.0.0  
**更新日期**: 2026-04-15
