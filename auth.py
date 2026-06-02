"""
用户认证蓝图
处理用户注册、登录、验证码等功能
"""
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, VerificationCode
from sms_service import get_sms_service

auth = Blueprint('auth', __name__)


def validate_phone(phone):
    """验证手机号格式"""
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


@auth.route('/login')
def login_page():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')


@auth.route('/register')
def register_page():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('register.html')


@auth.route('/api/send-code', methods=['POST'])
def send_code():
    """发送验证码"""
    data = request.get_json()
    phone = data.get('phone', '').strip()

    if not phone:
        return jsonify({'success': False, 'message': '请输入手机号'}), 400

    if not validate_phone(phone):
        return jsonify({'success': False, 'message': '手机号格式不正确'}), 400

    # 创建验证码
    code = VerificationCode.create_code(phone)

    # 发送验证码
    sms_service = get_sms_service()
    success, message = sms_service.send_code(phone, code)

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 500


@auth.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    nickname = data.get('nickname', '').strip()

    # 验证参数
    if not phone or not code:
        return jsonify({'success': False, 'message': '手机号和验证码不能为空'}), 400

    if not validate_phone(phone):
        return jsonify({'success': False, 'message': '手机号格式不正确'}), 400

    if len(code) != 6:
        return jsonify({'success': False, 'message': '验证码必须是6位数字'}), 400

    # 验证验证码
    valid, message = VerificationCode.verify_code(phone, code)
    if not valid:
        return jsonify({'success': False, 'message': message}), 400

    # 检查用户是否已存在
    existing_user = User.query.filter_by(phone=phone).first()
    if existing_user:
        return jsonify({'success': False, 'message': '该手机号已注册'}), 400

    # 创建用户
    user = User(
        phone=phone,
        nickname=nickname or f'用户{phone[-4:]}'
    )
    db.session.add(user)
    db.session.commit()

    # 自动登录
    login_user(user)
    user.last_login = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '注册成功',
        'user': {
            'id': user.id,
            'phone': user.phone,
            'nickname': user.nickname
        }
    })


@auth.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()

    # 验证参数
    if not phone or not code:
        return jsonify({'success': False, 'message': '手机号和验证码不能为空'}), 400

    if not validate_phone(phone):
        return jsonify({'success': False, 'message': '手机号格式不正确'}), 400

    # 验证验证码
    valid, message = VerificationCode.verify_code(phone, code)
    if not valid:
        return jsonify({'success': False, 'message': message}), 400

    # 查找用户
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'success': False, 'message': '用户不存在，请先注册'}), 400

    # 登录
    login_user(user)
    user.last_login = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '登录成功',
        'user': {
            'id': user.id,
            'phone': user.phone,
            'nickname': user.nickname
        }
    })


@auth.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    logout_user()
    return jsonify({'success': True, 'message': '已退出登录'})


@auth.route('/api/user/info', methods=['GET'])
@login_required
def user_info():
    """获取用户信息"""
    return jsonify({
        'success': True,
        'user': {
            'id': current_user.id,
            'phone': current_user.phone,
            'nickname': current_user.nickname,
            'created_at': current_user.created_at.strftime('%Y-%m-%d %H:%M'),
            'last_login': current_user.last_login.strftime('%Y-%m-%d %H:%M')
        }
    })


@auth.route('/api/user/nickname', methods=['PUT'])
@login_required
def update_nickname():
    """更新用户昵称"""
    data = request.get_json()
    nickname = data.get('nickname', '').strip()

    if not nickname:
        return jsonify({'success': False, 'message': '昵称不能为空'}), 400

    if len(nickname) > 50:
        return jsonify({'success': False, 'message': '昵称不能超过50个字符'}), 400

    current_user.nickname = nickname
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '昵称已更新',
        'nickname': nickname
    })
