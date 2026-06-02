"""
聊天蓝图
处理对话管理、消息存储、历史记录等功能
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db, Conversation, Message
from config import Config

chat = Blueprint('chat', __name__)


@chat.route('/api/conversations', methods=['GET'])
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


@chat.route('/api/conversations', methods=['POST'])
@login_required
def create_conversation():
    """创建新对话"""
    data = request.get_json() or {}
    title = data.get('title', '新对话')

    conversation = Conversation(
        user_id=current_user.id,
        title=title
    )
    db.session.add(conversation)
    db.session.commit()

    return jsonify({
        'success': True,
        'conversation': conversation.to_dict()
    })


@chat.route('/api/conversations/<int:conv_id>', methods=['GET'])
@login_required
def get_conversation(conv_id):
    """获取对话详情和消息"""
    conversation = Conversation.query.filter_by(
        id=conv_id,
        user_id=current_user.id
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


@chat.route('/api/conversations/<int:conv_id>', methods=['PUT'])
@login_required
def update_conversation(conv_id):
    """更新对话标题"""
    conversation = Conversation.query.filter_by(
        id=conv_id,
        user_id=current_user.id
    ).first()

    if not conversation:
        return jsonify({'success': False, 'message': '对话不存在'}), 404

    data = request.get_json()
    title = data.get('title', '').strip()

    if not title:
        return jsonify({'success': False, 'message': '标题不能为空'}), 400

    conversation.title = title
    db.session.commit()

    return jsonify({
        'success': True,
        'conversation': conversation.to_dict()
    })


@chat.route('/api/conversations/<int:conv_id>', methods=['DELETE'])
@login_required
def delete_conversation(conv_id):
    """删除对话"""
    conversation = Conversation.query.filter_by(
        id=conv_id,
        user_id=current_user.id
    ).first()

    if not conversation:
        return jsonify({'success': False, 'message': '对话不存在'}), 404

    db.session.delete(conversation)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '对话已删除'
    })


@chat.route('/api/conversations/<int:conv_id>/messages', methods=['POST'])
@login_required
def add_message(conv_id):
    """添加消息到对话"""
    conversation = Conversation.query.filter_by(
        id=conv_id,
        user_id=current_user.id
    ).first()

    if not conversation:
        return jsonify({'success': False, 'message': '对话不存在'}), 404

    data = request.get_json()
    role = data.get('role', 'user')
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'success': False, 'message': '消息内容不能为空'}), 400

    if role not in ['user', 'assistant']:
        return jsonify({'success': False, 'message': '无效的消息角色'}), 400

    message = Message(
        conversation_id=conv_id,
        role=role,
        content=content
    )
    db.session.add(message)

    # 更新对话时间和标题
    conversation.updated_at = datetime.utcnow()
    if role == 'user' and conversation.title == '新对话':
        # 用用户的第一条消息作为标题（截取前20个字符）
        conversation.title = content[:20] + ('...' if len(content) > 20 else '')

    db.session.commit()

    return jsonify({
        'success': True,
        'message': message.to_dict()
    })


@chat.route('/api/conversations/<int:conv_id>/context', methods=['GET'])
@login_required
def get_conversation_context(conv_id):
    """获取对话上下文（用于发送给AI）"""
    conversation = Conversation.query.filter_by(
        id=conv_id,
        user_id=current_user.id
    ).first()

    if not conversation:
        return jsonify({'success': False, 'message': '对话不存在'}), 404

    # 获取最近的消息作为上下文
    messages = Message.query.filter_by(
        conversation_id=conv_id
    ).order_by(Message.created_at.desc()).limit(20).all()

    # 反转为正序
    messages.reverse()

    context = [
        {'role': msg.role, 'content': msg.content}
        for msg in messages
    ]

    return jsonify({
        'success': True,
        'context': context
    })


def cleanup_old_conversations():
    """
    清理超过保留期的对话
    应该通过定时任务调用
    """
    retention_days = Config.HISTORY_RETENTION_DAYS
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    old_conversations = Conversation.query.filter(
        Conversation.updated_at < cutoff_date
    ).all()

    count = len(old_conversations)
    for conv in old_conversations:
        db.session.delete(conv)

    db.session.commit()

    if count > 0:
        print(f"已清理 {count} 个超过 {retention_days} 天的对话")

    return count
