' AI智能助手 - 静默启动脚本
' 双击运行即可启动应用并打开浏览器

Set WshShell = CreateObject("WScript.Shell")

' 设置工作目录
WshShell.CurrentDirectory = "C:\Users\Lenovo\Desktop\ai-assistant"

' 后台启动Python应用（隐藏窗口）
WshShell.Run "python app.py", 0, False

' 等待应用启动
WScript.Sleep 2000

' 打开浏览器
WshShell.Run "http://localhost:5000"
