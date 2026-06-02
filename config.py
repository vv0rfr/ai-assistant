import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///ai_assistant.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mimo AI API
    MIMO_API_KEY = os.getenv('MIMO_API_KEY', 'tp-cfzyme5pp45hu98e69h6u93n00efjdn1rjydk13ao8xl5x48')
    MIMO_API_URL = 'https://token-plan-cn.xiaomimimo.com/v1/chat/completions'

    # 和风天气API
    QWEATHER_API_KEY = os.getenv('QWEATHER_API_KEY', '')
    QWEATHER_API_URL = 'https://devapi.qweather.com/v7/weather/now'

    # 短信服务（阿里云SMS）
    SMS_ACCESS_KEY_ID = os.getenv('SMS_ACCESS_KEY_ID', '')
    SMS_ACCESS_KEY_SECRET = os.getenv('SMS_ACCESS_KEY_SECRET', '')
    SMS_SIGN_NAME = os.getenv('SMS_SIGN_NAME', 'AI助手')
    SMS_TEMPLATE_CODE = os.getenv('SMS_TEMPLATE_CODE', '')

    # 历史记录清理（天数）
    HISTORY_RETENTION_DAYS = int(os.getenv('HISTORY_RETENTION_DAYS', '30'))


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
