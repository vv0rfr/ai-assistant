"""
测试脚本 - 验证应用是否可以正常启动
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    try:
        from config import Config
        print("[OK] config 模块导入成功")
    except Exception as e:
        print(f"[FAIL] config 模块导入失败: {e}")
        return False

    try:
        from models import db, User, Conversation, Message
        print("[OK] models 模块导入成功")
    except Exception as e:
        print(f"[FAIL] models 模块导入失败: {e}")
        return False

    try:
        from auth import auth
        print("[OK] auth 模块导入成功")
    except Exception as e:
        print(f"[FAIL] auth 模块导入失败: {e}")
        return False

    try:
        from chat import chat
        print("[OK] chat 模块导入成功")
    except Exception as e:
        print(f"[FAIL] chat 模块导入失败: {e}")
        return False

    try:
        from weather import get_weather, is_weather_query
        print("[OK] weather 模块导入成功")
    except Exception as e:
        print(f"[FAIL] weather 模块导入失败: {e}")
        return False

    try:
        from sms_service import get_sms_service
        print("[OK] sms_service 模块导入成功")
    except Exception as e:
        print(f"[FAIL] sms_service 模块导入失败: {e}")
        return False

    return True


def test_app_creation():
    """测试应用创建"""
    print("\n测试应用创建...")
    try:
        from app import create_app
        app = create_app()
        print("[OK] Flask应用创建成功")
        return True
    except Exception as e:
        print(f"[FAIL] Flask应用创建失败: {e}")
        return False


def test_database():
    """测试数据库初始化"""
    print("\n测试数据库初始化...")
    try:
        from app import create_app
        from models import db

        app = create_app()
        with app.app_context():
            # 检查表是否创建
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"[OK] 数据库表已创建: {', '.join(tables)}")
        return True
    except Exception as e:
        print(f"[FAIL] 数据库初始化失败: {e}")
        return False


def test_weather_query():
    """测试天气查询判断"""
    print("\n测试天气查询判断...")
    try:
        from weather import is_weather_query

        test_cases = [
            ("北京天气怎么样？", True, "北京"),
            ("上海今天会下雨吗", True, "上海"),
            ("今天天气真好", True, None),
            ("你好", False, None),
        ]

        for message, expected_is_weather, expected_city in test_cases:
            is_weather, city = is_weather_query(message)
            if is_weather == expected_is_weather and city == expected_city:
                print(f"[OK] '{message}' -> 天气: {is_weather}, 城市: {city}")
            else:
                print(f"[FAIL] '{message}' -> 预期: 天气={expected_is_weather}, 城市={expected_city}, 实际: 天气={is_weather}, 城市={city}")
                return False

        return True
    except Exception as e:
        print(f"[FAIL] 天气查询测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 50)
    print("AI智能助手 - 项目测试")
    print("=" * 50)

    all_passed = True

    # 测试模块导入
    if not test_imports():
        all_passed = False

    # 测试应用创建
    if not test_app_creation():
        all_passed = False

    # 测试数据库
    if not test_database():
        all_passed = False

    # 测试天气查询
    if not test_weather_query():
        all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("[OK] 所有测试通过！项目可以正常运行。")
        print("\n启动命令: python app.py")
        print("访问地址: http://localhost:5000")
    else:
        print("[FAIL] 部分测试失败，请检查错误信息。")
    print("=" * 50)

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
