@echo off
chcp 65001 >nul
echo ========================================
echo AI智能助手 - 启动脚本
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)
echo [OK] Python环境正常

echo.
echo [2/3] 检查依赖包...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)
echo [OK] 依赖包已就绪

echo.
echo [3/3] 启动应用...
echo.
echo ========================================
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python app.py
