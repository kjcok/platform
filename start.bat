@echo off
REM 数据质量评估平台启动脚本 (Windows)

echo ========================================
echo 数据质量评估平台 - 启动中...
echo ========================================

REM 检查虚拟环境
if exist "D:\Python\venv310\Scripts\activate.bat" (
    echo [1/3] 激活 Python 3.10 虚拟环境...
    call D:\Python\venv310\Scripts\activate.bat
) else (
    echo [警告] 未找到虚拟环境，使用系统 Python
)

REM 检查依赖
echo [2/3] 检查依赖包...
python -c "import great_expectations" 2>nul
if errorlevel 1 (
    echo [错误] 缺少依赖包，正在安装...
    pip install -r config\requirements.txt
)

REM 启动应用
echo [3/3] 启动 Flask 应用...
echo.
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务
echo.

cd /d "%~dp0"
python src\backend\app.py

pause
