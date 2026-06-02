# AI 智能助手 — CLAUDE.md

## 项目概述
Flask + SQLAlchemy 聊天应用，支持 Mimo AI 对话、天气查询、用户认证、历史记录。

## 快速命令
```bash
python app.py                # 启动（端口 5000，支持流式输出）
python diagnose.py           # 网络诊断
python test_app.py           # 运行测试
```

## 关键文件
| 文件 | 用途 |
|------|------|
| `app.py` | 主应用（路由、Mimo API、对话管理） |
| `config.py` | 配置（Mimo/和风天气/阿里云SMS） |
| `models.py` | 数据库模型（User/Conversation/Message） |
| `auth.py` | 认证蓝图（注册/登录/验证码） |
| `weather.py` | 天气服务 + 穿搭/护肤建议 |
| `sms_service.py` | 短信服务（开发模式 + 阿里云SMS） |
| `scheduler.py` | APScheduler 定时任务（30天清理） |

## 配置（.env）
```
SECRET_KEY=                 # Flask密钥
MIMO_API_KEY=               # Mimo AI API Key（有默认值）
QWEATHER_API_KEY=           # 和风天气 API Key（可选）
SMS_ACCESS_KEY_ID=          # 阿里云 SMS（可选）
SMS_ACCESS_KEY_SECRET=      # 阿里云 SMS（可选）
```

## 已知限制
- 手机需和电脑同一网络才能访问
- 开发模式验证码在终端显示，非手机短信
- 无 HTTPS
- Mimo API key 有硬编码默认值（测试用）
