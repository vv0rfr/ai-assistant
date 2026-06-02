@echo off
chcp 65001 >nul
cd /d "C:\Users\Lenovo\Desktop\ai-assistant"

echo 正在启动AI智能助手...
echo.

REM 启动应用（后台运行）
start /B python app.py

REM 等待应用启动
timeout /t 2 /nobreak >nul

REM 打开浏览器
start http://localhost:5000

echo.
echo AI智能助手已启动！
echo 浏览器将自动打开，如果没有请手动访问: http://localhost:5000
echo.
echo 按任意键关闭此窗口（应用将继续运行）...
pause >nul
