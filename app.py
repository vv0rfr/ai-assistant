from flask import Flask, render_template, request, jsonify
import requests
import json
import os

# 创建Flask应用
app = Flask(__name__)

# Mimo API配置（从环境变量读取，更安全）
MIMO_API_URL = os.getenv("MIMO_API_URL", "https://token-plan-cn.xiaomimimo.com/v1/chat/completions")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "tp-cfzyme5pp45hu98e69h6u93n00efjdn1rjydk13ao8xl5x48")

# 调用Mimo AI API
def call_mimo_api(question):
    """调用Mimo API获取AI回复"""
    try:
        # 设置请求头（OpenAI兼容格式）
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MIMO_API_KEY}"
        }

        # 设置请求体（OpenAI兼容格式）
        data = {
            "model": "mimo-v2.5-pro",
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        }

        # 发送请求
        response = requests.post(
            MIMO_API_URL,
            headers=headers,
            json=data,
            timeout=30
        )

        # 检查响应状态
        if response.status_code == 200:
            result = response.json()
            # 提取AI回复（OpenAI格式）
            ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "抱歉，无法获取回复。")
            return ai_response
        else:
            return f"API调用失败，状态码：{response.status_code}"

    except requests.exceptions.Timeout:
        return "请求超时，请稍后重试。"
    except requests.exceptions.RequestException as e:
        return f"网络错误：{str(e)}"
    except Exception as e:
        return f"发生错误：{str(e)}"

# 首页路由
@app.route('/')
def index():
    return render_template('index.html')

# 聊天API路由
@app.route('/api/chat', methods=['POST'])
def chat():
    # 获取用户发送的消息
    data = request.get_json()
    user_message = data.get('message', '')

    # 调用Mimo AI获取回复
    ai_response = call_mimo_api(user_message)

    # 返回JSON格式的回复
    return jsonify({
        'user_message': user_message,
        'ai_response': ai_response
    })

# 启动应用
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("AI智能助手启动中...")
    print(f"访问地址: http://localhost:{port}")
    app.run(debug=True, host="0.0.0.0", port=port)
