# 项目目录结构说明

## 📁 目录概览

```
platform/
├── src/                    # 程序代码目录
│   ├── backend/           # 后端代码（Python）
│   │   ├── app.py        # Flask 主应用入口
│   │   ├── file_manager.py    # 文件管理模块
│   │   ├── ge_engine.py       # Great Expectations 评估引擎
│   │   └── report_renderer.py # HTML 报告渲染器
│   └── frontend/          # 前端代码
│       └── templates/     # Jinja2 HTML 模板
│           ├── index.html            # 主页模板
│           └── report_template.html  # 报告模板
├── docs/                   # 文档目录
│   ├── ARCHITECTURE.md    # 技术架构设计文档
│   ├── CHECKLIST.md       # 项目交付检查清单
│   ├── DELIVERY_SUMMARY.md # 交付总结
│   ├── GE_UPGRADE_NOTES.md # GE 版本升级说明
│   ├── PROJECT_OVERVIEW.md # 项目概览
│   ├── QUICKSTART.md      # 快速开始指南
│   └── VENV_USAGE.md      # Python 虚拟环境使用说明
├── output/                 # 生成文件目录（程序运行产物）
│   ├── data/             # 上传的数据文件（CSV、Excel等）
│   └── reports/          # 生成的质量评估报告（HTML）
├── tests/                  # 测试数据和代码
│   ├── data/             # 测试用数据文件
│   │   └── sample_data.csv   # 示例数据
│   └── scripts/          # 测试脚本
│       ├── demo.py       # 演示脚本
│       └── test_app.py   # 单元测试
├── config/                 # 配置文件目录
│   ├── requirements.txt  # Python 依赖包列表
│   └── settings.py       # 应用配置文件
├── temp/                   # 中间过程文件（可随时删除）
│   └── .gitkeep          # Git 占位文件
├── README.md              # 项目主文档
├── start.bat              # Windows 启动脚本
└── .gitignore             # Git 忽略配置
```

## 📂 各目录详细说明

### 1. src/ - 程序代码目录

存放所有源代码，按前后端分离：

- **backend/**: Python 后端代码
  - `app.py`: Flask Web 应用，提供 RESTful API
  - `file_manager.py`: 文件上传、保存、读取功能
  - `ge_engine.py`: 核心评估引擎，集成 Great Expectations
  - `report_renderer.py`: HTML 报告生成器

- **frontend/**: 前端代码
  - `templates/`: Jinja2 HTML 模板文件

### 2. docs/ - 文档目录

存放所有项目文档（除根目录的 README.md 外）：

- 技术文档
- 使用指南
- 架构设计
- 升级说明

### 3. output/ - 生成文件目录

存放程序运行时产生的文件：

- **data/**: 用户上传的数据文件
  - 自动创建
  - 文件名格式：`data_<uuid>.csv/xlsx/xls`
  
- **reports/**: 生成的质量评估报告
  - 自动创建
  - 文件名格式：`report_<uuid>.html`

⚠️ **注意**: 此目录下的文件通常不提交到 Git（见 .gitignore）

### 4. tests/ - 测试数据和代码

存放所有测试相关文件：

- **data/**: 测试用数据文件
  - `sample_data.csv`: 示例数据集
  
- **scripts/**: 测试脚本
  - `demo.py`: 完整流程演示
  - `test_app.py`: 单元测试套件（13个测试用例）

### 5. config/ - 配置文件目录

存放各种配置文件：

- `requirements.txt`: Python 依赖包及版本
- `settings.py`: 应用配置参数（端口、路径等）

### 6. temp/ - 中间过程文件

存放程序运行过程中产生的临时文件：

- 缓存文件
- 临时处理文件
- 日志文件（如有）

✅ **可以随时清空此目录**，不影响程序运行

## 🔧 路径配置说明

所有路径都使用绝对路径，基于 `PROJECT_ROOT` 计算：

```python
# 在 app.py 和 report_renderer.py 中
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # src/backend
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))  # platform
```

这样无论从哪里启动应用，路径都能正确解析。

## 🚀 启动方式

### 方式 1: 使用启动脚本（推荐）
```bash
start.bat
```

### 方式 2: 手动启动
```bash
# 激活虚拟环境
D:\Python\venv310\Scripts\activate.bat

# 启动应用
python src\backend\app.py
```

### 方式 3: 运行测试
```bash
# 运行演示
python tests\scripts\demo.py

# 运行单元测试
python tests\scripts\test_app.py
```

## 📝 注意事项

1. **不要手动修改 output/ 目录**：所有文件由程序自动管理
2. **temp/ 可定期清理**：不会影响程序功能
3. **测试数据放在 tests/data/**：不要放在 output/data/
4. **文档统一放在 docs/**：便于管理和查找
5. **配置文件放在 config/**：集中管理所有配置

## 🔄 目录重构历史

- **重构日期**: 2026-04-15
- **重构目的**: 提高项目可维护性，清晰分离关注点
- **主要变更**:
  - 前后端代码分离到 src/
  - 文档集中到 docs/
  - 生成文件统一到 output/
  - 测试代码和数据放到 tests/
  - 配置文件集中到 config/
  - 临时文件独立到 temp/
