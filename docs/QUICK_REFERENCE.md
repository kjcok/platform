# 快速参考卡片

## 🚀 快速启动

```bash
# 方式1: 使用启动脚本（推荐）
start.bat

# 方式2: 手动启动
D:\Python\venv310\Scripts\activate.bat
python src\backend\app.py
```

## 🧪 运行测试

```bash
# 单元测试
python tests\scripts\test_app.py

# 完整演示
python tests\scripts\demo.py
```

## 📁 目录速查

| 目录 | 用途 | 示例 |
|------|------|------|
| `src/backend/` | 后端代码 | app.py, ge_engine.py |
| `src/frontend/templates/` | 前端模板 | index.html |
| `docs/` | 项目文档 | README, 架构设计 |
| `output/data/` | 上传的数据 | data_xxx.csv |
| `output/reports/` | 生成的报告 | report_xxx.html |
| `tests/data/` | 测试数据 | sample_data.csv |
| `tests/scripts/` | 测试脚本 | test_app.py |
| `config/` | 配置文件 | requirements.txt |
| `temp/` | 临时文件 | 可随时删除 |

## 🔧 常用命令

```bash
# 查看 Python 版本
python --version

# 查看 GE 版本
python -c "import great_expectations as gx; print(gx.__version__)"

# 安装依赖
pip install -r config\requirements.txt

# 清理临时文件
del /q temp\*
```

## 📖 文档索引

- **README.md** - 项目介绍和快速开始
- **docs/DIRECTORY_STRUCTURE.md** - 详细目录说明
- **docs/QUICKSTART.md** - 快速开始指南
- **docs/VENV_USAGE.md** - 虚拟环境使用
- **docs/GE_UPGRADE_NOTES.md** - GE 版本说明
- **docs/REFACTORING_SUMMARY.md** - 重构总结

## ⚡ 关键路径

所有路径基于项目根目录自动计算，无需手动配置：

```python
# 在代码中
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
```

## 🎯 测试状态

- ✅ 13/13 单元测试通过
- ✅ 完整流程演示成功
- ✅ GE 1.16.0 完全兼容
- ✅ 成功率 85.71% (示例数据)

---

**最后更新**: 2026-04-15  
**版本**: v1.0 (重构后)
