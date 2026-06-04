# AI智能助手 - 项目状态

## 项目概述

基于Flask的AI聊天助手，本地部署测试项目。

## 已完成功能

| 功能 | 状态 | 说明 |
|------|------|------|
| Mimo AI对话 | ✅ | OpenAI兼容格式，支持上下文 |
| 流式输出 | ✅ | 文字逐字显示，不再等全部生成完 |
| 天气查询 | ✅ | wttr.in免费API，无需Key |
| 穿搭/护肤建议 | ✅ | 基于天气数据自动生成 |
| 手机号登录 | ✅ | 开发模式验证码在终端显示 |
| 聊天历史 | ✅ | 登录后保存，支持搜索、删除、重命名 |
| 30天自动清理 | ✅ | APScheduler定时任务 |
| 响应式设计 | ✅ | 桌面端+移动端 |
| 移动端访问 | ✅ | 同一网络下可用（手机热点或同一WiFi） |
| 文档问答 | ✅ | 上传PDF/Word/TXT，AI总结+回答 |
| 毛玻璃UI改造 | ✅ | 深蓝紫渐变+磨砂玻璃效果（2026-06-04） |

## 技术栈

- **后端**: Flask + SQLAlchemy + Flask-Login
- **数据库**: SQLite（`instance/ai_assistant.db`）
- **天气API**: wttr.in（免费，无需API Key）
- **AI API**: Mimo AI（`token-plan-cn.xiaomimimo.com`）
- **前端**: HTML + CSS + JavaScript（无框架）
- **定时任务**: APScheduler

## 项目结构

```
ai-assistant/
├── app.py              # 主应用（路由、Mimo API、对话管理）
├── config.py           # 配置文件
├── models.py           # 数据库模型（User/Conversation/Message/VerificationCode）
├── auth.py             # 认证蓝图（注册/登录/验证码）
├── weather.py          # 天气服务（wttr.in，内置约60个城市）
├── sms_service.py      # 短信服务（DevSMSService + AliyunSMSService）
├── scheduler.py        # 定时任务（30天清理）
├── templates/          # HTML模板（base/index/login/register）
└── static/             # 静态资源（css/style.css + js/app.js）
```

## 启动方式

```bash
python app.py
```

默认端口 5000，监听 `0.0.0.0`（支持局域网访问）。

## 移动端访问

手机和电脑必须在同一网络下：
- 方案1：手机和电脑连同一个WiFi
- 方案2：手机开热点 → 电脑连热点 → 手机访问电脑IP:5000

注意：电脑关机后手机无法访问（本地部署限制）。

## 已知限制

- 移动端需要同一网络才能访问
- 验证码在开发模式下只在电脑终端显示
- 无HTTPS（本地部署）
- Mimo API key硬编码在config.py中（仅测试用）
