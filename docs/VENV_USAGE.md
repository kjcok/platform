# Python 3.10 虚拟环境使用说明

## 📋 环境要求

- Python 3.10
- Great Expectations 1.16.0（最新版本）

## 🚀 快速开始

### 1. 激活虚拟环境

**Windows:**
```bash
D:\Python\venv310\Scripts\activate.bat
```

**或者使用 PowerShell:**
```powershell
D:\Python\venv310\Scripts\Activate.ps1
```

### 2. 验证环境

```bash
python --version
# 应该显示: Python 3.10.x

python -c "import great_expectations; print('GE Version:', great_expectations.__version__)"
# 应该显示: GE Version: 1.16.0
```

### 3. 启动应用

```bash
# 确保在正确的目录
cd d:\work\dataquality\dataq\platform

# 启动 Flask 应用
python app.py
```

应用将在 `http://localhost:5000` 启动。

### 4. 运行演示

打开新的终端窗口（同样需要激活虚拟环境）：

```bash
D:\Python\venv310\Scripts\activate.bat
cd d:\work\dataquality\dataq\platform
python demo.py
```

### 5. 运行测试

```bash
python test_app.py
```

预期结果：13/13 测试通过 ✅

## ⚠️ 重要提示

### Great Expectations 版本要求

当前平台**仅支持 GE 1.16.0+ 版本**。

**技术实现：**
- 使用 `ValidationDefinition` API（GE 1.x 推荐方式）
- 通过 `EphemeralDataContext` 创建临时上下文
- 动态映射规则到 GE Expectation 类

**如果遇到以下错误：**
```
检测到 Great Expectations 0.18.12 版本。
当前平台需要 GE 1.x 版本（推荐 1.16.0）。
请运行: pip install great-expectations==1.16.0
```

**解决方法：**
```bash
D:\Python\venv310\Scripts\pip.exe install great-expectations==1.16.0
```

### 常见问题

#### Q1: 为什么不能使用系统 Python？

A: 系统 Python (3.9) 和虚拟环境 Python (3.10) 是不同的环境。为确保一致性，请始终使用虚拟环境。

#### Q2: 如何确认使用的是虚拟环境的 Python？

A: 运行以下命令：
```bash
python -c "import sys; print(sys.executable)"
```
应该显示：`D:\Python\venv310\Scripts\python.exe`

#### Q3: 每次都需要激活虚拟环境吗？

A: 是的，每个新的终端窗口都需要激活。或者直接使用完整路径：
```bash
D:\Python\venv310\Scripts\python.exe app.py
```

#### Q4: 如果不小心安装了 GE 1.x 怎么办？

A: 重新安装正确的版本：
```bash
D:\Python\venv310\Scripts\pip.exe uninstall great-expectations
D:\Python\venv310\Scripts\pip.exe install great-expectations==0.18.12
```

## 📦 依赖管理

### 查看所有已安装的包

```bash
pip list
```

### 导出依赖列表

```bash
pip freeze > requirements_venv.txt
```

### 从 requirements.txt 安装

```bash
pip install -r requirements.txt
```

## 🔧 开发建议

### 1. 始终使用虚拟环境

```bash
# 激活环境
D:\Python\venv310\Scripts\activate.bat

# 工作...

# 完成后退出（可选）
deactivate
```

### 2. 定期检查版本

```bash
python -c "import great_expectations; print(great_expectations.__version__)"
```

### 3. 保持依赖一致

团队成员应使用相同的虚拟环境和依赖版本。

## 📝 总结

**关键命令速查：**

```bash
# 1. 激活虚拟环境
D:\Python\venv310\Scripts\activate.bat

# 2. 进入项目目录
cd d:\work\dataquality\dataq\platform

# 3. 启动应用
python app.py

# 4. 运行演示（新终端）
python demo.py

# 5. 运行测试
python test_app.py
```

**记住：始终先激活虚拟环境，再执行任何 Python 命令！**

---

**最后更新**: 2026-04-15  
**Python 版本**: 3.10  
**GE 版本**: 0.18.12
