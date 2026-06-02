"""
AI智能助手 - 主应用
支持日常聊天、天气查询、用户认证、历史记录等功能
"""
import os
import json
import logging
import requests as http_requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, stream_with_context, current_app
from flask_login import LoginManager, login_required, current_user

from config import config
from models import db, User, Conversation, Message, init_db
from auth import auth as auth_blueprint
from weather import get_weather, generate_weather_advice, format_weather_response, is_weather_query
from scheduler import setup_scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化数据库
    init_db(app)

    # 初始化Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_page'
    login_manager.login_message = '请先登录'

    # 未登录时API返回JSON而非HTML
    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': '请先登录', 'redirect': '/login'}), 401
        return redirect(url_for('auth.login_page'))

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 注册蓝图
    app.register_blueprint(auth_blueprint)

    # 注册路由
    register_routes(app)

    # 设置定时任务
    if not app.debug or os.getenv('ENABLE_SCHEDULER') == 'true':
        setup_scheduler(app)

    return app


def register_routes(app):
    """注册路由"""

    @app.route('/')
    def index():
        """主页 - 未登录也能使用"""
        return render_template('index.html')

    @app.route('/api/chat', methods=['POST'])
    def chat():
        """聊天API - 支持天气查询和AI对话"""
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')

        if not user_message:
            return jsonify({'success': False, 'message': '消息不能为空'}), 400

        # 检查是否是天气查询
        is_weather, city = is_weather_query(user_message)

        if is_weather and city:
            # 处理天气查询
            weather_info, error = get_weather(city)
            if weather_info:
                advice = generate_weather_advice(weather_info)
                ai_response = format_weather_response(weather_info, advice)
            else:
                ai_response = f"抱歉，无法获取{city}的天气信息：{error}"
        elif is_weather and not city:
            # 有天气关键词但没有城市
            ai_response = "请问你要查询哪个城市的天气呢？比如：北京天气、上海天气"
        else:
            # 调用AI API
            ai_response = call_mimo_api(user_message, conversation_id)

        # 如果有对话ID且用户已登录，保存消息
        if conversation_id and current_user.is_authenticated:
            save_message(conversation_id, 'user', user_message)
            save_message(conversation_id, 'assistant', ai_response)

        return jsonify({
            'success': True,
            'user_message': user_message,
            'ai_response': ai_response,
            'is_weather': is_weather and city is not None
        })

    @app.route('/api/chat/stream', methods=['POST'])
    def chat_stream():
        """流式聊天API - 带上下文理解的AI对话"""
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        # 游客模式下，前端可以传最近的对话片段作为上下文
        context_messages = data.get('context', [])

        if not user_message:
            return jsonify({'success': False, 'message': '消息不能为空'}), 400

        # 保存用户消息
        if conversation_id and current_user.is_authenticated:
            save_message(conversation_id, 'user', user_message)

        # 提前取出配置（generator 中拿不到 current_app）
        api_url = current_app.config['MIMO_API_URL']
        api_key = current_app.config['MIMO_API_KEY']

        # ===== 上下文感知的天气注入 =====
        # 如果用户只说了城市名，结合上下文判断是否在问天气
        weather_context = None
        city_name = user_message.strip()
        COMMON_CITIES = ['北京','上海','广州','深圳','杭州','成都','武汉','西安','南京',
                       '重庆','天津','苏州','长沙','郑州','东莞','青岛','沈阳','宁波',
                       '昆明','大连','厦门','合肥','佛山','福州','哈尔滨','济南','温州',
                       '长春','石家庄','常州','泉州','南宁','贵阳','南昌','太原','烟台',
                       '嘉兴','南通','金华','珠海','惠州','徐州','海口','乌鲁木齐','绍兴',
                       '中山','台州','兰州','焦作','洛阳','开封','南阳','新乡','安阳',
                       '邯郸','保定','芜湖','蚌埠','秦皇岛','唐山','淄博','潍坊','济宁',
                       '临沂','包头','呼和浩特','银川','西宁','拉萨','绵阳','德阳','宜宾',
                       '遵义','桂林','柳州','湛江','茂名','韶关','潮州','汕头','九江',
                       '赣州','宜昌','襄阳','岳阳','株洲','湘潭','丹东','锦州','鞍山']

        match_city = None
        for suffix in ['市', '城']:
            if city_name.endswith(suffix):
                match_city = city_name[:-1]
                break
        if not match_city:
            match_city = city_name

        is_bare_city = match_city in COMMON_CITIES

        if is_bare_city:
            # 查看上下文：上一条助手回复是否在问城市
            last_assistant_content = None
            if conversation_id and current_user.is_authenticated:
                try:
                    last = Message.query.filter_by(
                        conversation_id=conversation_id, role='assistant'
                    ).order_by(Message.created_at.desc()).first()
                    if last:
                        last_assistant_content = last.content
                except Exception:
                    pass
            elif context_messages:
                # 游客模式：从上下文中找最后一条助手消息
                for ctx in reversed(context_messages):
                    if ctx.get('role') == 'assistant':
                        last_assistant_content = ctx.get('content', '')
                        break

            if last_assistant_content and ('城市' in last_assistant_content or '哪个' in last_assistant_content or '地方' in last_assistant_content):
                try:
                    from weather import get_weather, generate_weather_advice
                    w_info, w_err = get_weather(match_city)
                    if w_info:
                        advice = generate_weather_advice(w_info)
                        desc = w_info.get('description', '未知')
                        weather_context = (
                            f"当前{match_city}天气：{w_info['temp']}°C，湿度{w_info['humidity']}%，"
                            f"天气状况：{desc}\n"
                            f"穿搭建议：{advice}"
                        )
                except Exception:
                    pass

        # 构建 system prompt
        system_prompt = "你是一个友好的AI助手，可以用中文回答各种问题。"
        if weather_context:
            system_prompt += (
                f"\n\n[系统已为你获取以下天气数据]\n{weather_context}\n"
                f"请基于这些真实天气数据回答用户，给出具体的穿搭/护肤建议。"
            )
        else:
            system_prompt += (
                "\n\n你有以下能力："
                "\n- 日常聊天"
                "\n- 天气查询：用户说'xx天气'时主动询问城市，获得城市后回答"
                "\n- 穿搭/护肤建议：基于天气给出，需要先知道用户所在城市"
                "\n- 上下文理解：注意结合聊天历史理解用户意图"
            )

        # 构建消息列表（发全部历史，让 AI 理解上下文）
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_id and current_user.is_authenticated:
            # 登录用户从 DB 加载历史
            try:
                history = Message.query.filter_by(
                    conversation_id=conversation_id
                ).order_by(Message.created_at.asc()).all()
                for msg in history:
                    if msg.role in ('user', 'assistant'):
                        if msg.role == 'user' and msg.content == user_message:
                            continue
                        messages.append({"role": msg.role, "content": msg.content})
            except Exception:
                pass
        elif context_messages:
            # 游客模式：使用前端传的上下文
            for ctx_msg in context_messages:
                role = ctx_msg.get('role', 'user')
                content = ctx_msg.get('content', '')
                if role in ('user', 'assistant') and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        def generate():
            """SSE 生成器"""
            full_response = ""
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }

                # 调用流式API
                response = http_requests.post(
                    api_url,
                    headers=headers,
                    json={"model": "mimo-v2.5-pro", "messages": messages, "stream": True},
                    stream=True,
                    timeout=60
                )

                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith('data: '):
                            data_str = decoded[6:].strip()
                            if data_str == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data_str)
                                choices = chunk.get('choices', [])
                                if choices and isinstance(choices, list) and len(choices) > 0:
                                    content = choices[0].get('delta', {}).get('content', '')
                                    if content:
                                        full_response += content
                                        yield f"data: {json.dumps({'content': content})}\n\n"
                            except json.JSONDecodeError:
                                continue

            except http_requests.exceptions.Timeout:
                yield f"data: {json.dumps({'error': '请求超时，请稍后重试'})}\n\n"
            except http_requests.exceptions.RequestException as e:
                logger.error(f"网络错误: {str(e)}")
                yield f"data: {json.dumps({'error': f'网络错误: {str(e)}'})}\n\n"
            except Exception as e:
                logger.error(f"流式API调用失败: {str(e)}")
                yield f"data: {json.dumps({'error': f'发生错误: {str(e)}'})}\n\n"
            finally:
                # 保存AI回复
                if conversation_id and current_user.is_authenticated and full_response:
                    try:
                        save_message(conversation_id, 'assistant', full_response)
                    except Exception:
                        pass
                yield "data: [DONE]\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
            }
        )

    # ========== 对话管理API（登录用户可用） ==========

    @app.route('/api/conversations', methods=['GET'])
    @login_required
    def get_conversations():
        """获取用户的对话列表"""
        conversations = Conversation.query.filter_by(
            user_id=current_user.id
        ).order_by(Conversation.updated_at.desc()).all()
        return jsonify({
            'success': True,
            'conversations': [conv.to_dict() for conv in conversations]
        })

    @app.route('/api/conversations', methods=['POST'])
    @login_required
    def create_conversation():
        """创建新对话"""
        data = request.get_json() or {}
        title = data.get('title', '新对话')
        conversation = Conversation(user_id=current_user.id, title=title)
        db.session.add(conversation)
        db.session.commit()
        return jsonify({'success': True, 'conversation': conversation.to_dict()})

    @app.route('/api/conversations/<int:conv_id>', methods=['GET'])
    @login_required
    def get_conversation(conv_id):
        """获取对话详情和消息"""
        conversation = Conversation.query.filter_by(
            id=conv_id, user_id=current_user.id
        ).first()
        if not conversation:
            return jsonify({'success': False, 'message': '对话不存在'}), 404

        messages = Message.query.filter_by(
            conversation_id=conv_id
        ).order_by(Message.created_at.asc()).all()

        return jsonify({
            'success': True,
            'conversation': conversation.to_dict(),
            'messages': [msg.to_dict() for msg in messages]
        })

    @app.route('/api/conversations/<int:conv_id>', methods=['PUT'])
    @login_required
    def update_conversation(conv_id):
        """更新对话标题"""
        conversation = Conversation.query.filter_by(
            id=conv_id, user_id=current_user.id
        ).first()
        if not conversation:
            return jsonify({'success': False, 'message': '对话不存在'}), 404

        data = request.get_json()
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'success': False, 'message': '标题不能为空'}), 400

        conversation.title = title
        db.session.commit()
        return jsonify({'success': True, 'conversation': conversation.to_dict()})

    @app.route('/api/conversations/<int:conv_id>', methods=['DELETE'])
    @login_required
    def delete_conversation(conv_id):
        """删除对话"""
        conversation = Conversation.query.filter_by(
            id=conv_id, user_id=current_user.id
        ).first()
        if not conversation:
            return jsonify({'success': False, 'message': '对话不存在'}), 404

        db.session.delete(conversation)
        db.session.commit()
        return jsonify({'success': True, 'message': '对话已删除'})

    @app.route('/api/health')
    def health_check():
        """健康检查"""
        return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})


def call_mimo_api(question, conversation_id=None):
    """调用Mimo API获取AI回复"""
    try:
        from flask import current_app

        api_url = current_app.config['MIMO_API_URL']
        api_key = current_app.config['MIMO_API_KEY']

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        messages = [
            {"role": "system", "content": "你是一个友好的AI助手，可以帮助用户解答日常问题。请用中文回复。"}
        ]

        # 如果有对话ID，添加历史消息作为上下文
        if conversation_id:
            try:
                history = Message.query.filter_by(
                    conversation_id=conversation_id
                ).order_by(Message.created_at.desc()).limit(10).all()

                for msg in reversed(history):
                    messages.append({"role": msg.role, "content": msg.content})
            except Exception:
                pass

        messages.append({"role": "user", "content": question})

        response = http_requests.post(
            api_url,
            headers=headers,
            json={"model": "mimo-v2.5-pro", "messages": messages},
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "抱歉，无法获取回复。")
            return ai_response
        else:
            logger.error(f"API调用失败，状态码：{response.status_code}")
            return f"API调用失败，状态码：{response.status_code}"

    except http_requests.exceptions.Timeout:
        return "请求超时，请稍后重试。"
    except http_requests.exceptions.RequestException as e:
        logger.error(f"网络错误：{str(e)}")
        return f"网络错误：{str(e)}"
    except Exception as e:
        logger.error(f"发生错误：{str(e)}")
        return f"发生错误：{str(e)}"


def save_message(conversation_id, role, content):
    """保存消息到数据库"""
    try:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.session.add(message)

        conversation = Conversation.query.get(conversation_id)
        if conversation:
            conversation.updated_at = datetime.utcnow()
            if role == 'user' and conversation.title == '新对话':
                conversation.title = content[:20] + ('...' if len(content) > 20 else '')

        db.session.commit()
    except Exception as e:
        logger.error(f"保存消息失败: {str(e)}")
        db.session.rollback()


# 创建应用实例
app = create_app()

# 启动应用
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("=" * 50)
    print("  AI 智能助手已启动（支持流式输出 ✨）")
    print(f"  本地访问: http://localhost:{port}")
    print(f"  手机访问: http://10.45.3.68:{port}（同一网络）")
    print("=" * 50)
    # 使用 run_simple 确保流式输出正常工作
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', port, app, use_reloader=False)
