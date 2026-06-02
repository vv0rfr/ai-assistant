"""
诊断脚本 - 检查常见问题
"""
import sys
import os
import socket

def check_port(port=5000):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def main():
    print("=" * 50)
    print("AI智能助手 - 问题诊断")
    print("=" * 50)

    # 检查Python版本
    print(f"\n[1] Python版本: {sys.version}")

    # 检查依赖
    print("\n[2] 检查依赖包...")
    required_packages = ['flask', 'requests', 'flask_sqlalchemy', 'flask_login']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [MISSING] {package}")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n缺少依赖包，请运行: pip install -r requirements.txt")
        return 1

    # 检查端口
    print("\n[3] 检查端口5000...")
    if check_port(5000):
        print("  [INFO] 端口5000已被占用")
        print("  可能原因：")
        print("    - 应用已在运行")
        print("    - 其他程序占用了该端口")
        print("  解决方法：")
        print("    - 访问 http://localhost:5000 查看是否已运行")
        print("    - 或者关闭占用端口的程序")
    else:
        print("  [OK] 端口5000可用")
        print("  应用未运行，请启动: python app.py")

    # 检查配置文件
    print("\n[4] 检查配置文件...")
    if os.path.exists('.env'):
        print("  [OK] .env 文件存在")
    else:
        print("  [INFO] .env 文件不存在（使用默认配置）")

    # 检查数据库
    print("\n[5] 检查数据库...")
    db_path = os.path.join('instance', 'ai_assistant.db')
    if os.path.exists(db_path):
        print(f"  [OK] 数据库文件存在: {db_path}")
    else:
        print(f"  [INFO] 数据库文件不存在（首次运行时自动创建）")

    print("\n" + "=" * 50)
    print("诊断完成！")
    print("\n如果遇到'网络错误'，请确保：")
    print("1. 已运行 'python app.py' 启动应用")
    print("2. 看到 'Running on http://127.0.0.1:5000' 表示启动成功")
    print("3. 然后在浏览器访问 http://localhost:5000")
    print("=" * 50)

    return 0

if __name__ == '__main__':
    sys.exit(main())
