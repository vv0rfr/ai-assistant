from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nickname = db.Column(db.String(50), default='用户')
    password_hash = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic',
                                    cascade='all, delete-orphan')

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.phone}>'


class Conversation(db.Model):
    """对话模型"""
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), default='新对话')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    messages = db.relationship('Message', backref='conversation', lazy='dynamic',
                               cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M'),
            'message_count': self.messages.count()
        }

    def __repr__(self):
        return f'<Conversation {self.id}: {self.title}>'


class Message(db.Model):
    """消息模型"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # 'user' 或 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        return f'<Message {self.id}: {self.role}>'


class VerificationCode(db.Model):
    """验证码模型"""
    __tablename__ = 'verification_codes'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

    @staticmethod
    def generate_code():
        """生成6位随机验证码"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    @staticmethod
    def create_code(phone):
        """为指定手机号创建验证码"""
        # 清除该手机号的旧验证码
        VerificationCode.query.filter_by(phone=phone, is_used=False).delete()

        code = VerificationCode.generate_code()
        verification = VerificationCode(
            phone=phone,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=5)  # 5分钟有效
        )
        db.session.add(verification)
        db.session.commit()
        return code

    @staticmethod
    def verify_code(phone, code):
        """验证验证码"""
        verification = VerificationCode.query.filter_by(
            phone=phone,
            code=code,
            is_used=False
        ).first()

        if not verification:
            return False, '验证码不存在'

        if verification.expires_at < datetime.utcnow():
            return False, '验证码已过期'

        verification.is_used = True
        db.session.commit()
        return True, '验证成功'

    def __repr__(self):
        return f'<VerificationCode {self.phone}: {self.code}>'


def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("数据库表已创建")
