from . import db
from datetime import datetime

# ================================
# 1. 用户表
# ================================
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(10), default='user')  # 'admin' or 'user'


# ================================
# 2. 传感器数据表
# ================================
class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    light = db.Column(db.Float)


# ================================
# 3. 控制指令表 (核心修改处)
# ================================
class ControlCommand(db.Model):
    __tablename__ = 'control_commands'
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50))
    command = db.Column(db.String(10))
    status = db.Column(db.String(20), default='pending')  # pending, done
    created_at = db.Column(db.DateTime, default=datetime.now)
    executed_at = db.Column(db.DateTime, nullable=True)

    # 👇👇👇 【核心修改】 👇👇👇
    # 增加 user_id 字段，并设置为外键，关联到 users 表的 id
    # 这样可以记录是哪个用户发送的指令
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


# ================================
# 4. AI 聊天记录表
# ================================
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    # 关联到用户ID，如果 user_id 为空，说明是游客消息
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    role = db.Column(db.String(20))  # 'user' or 'assistant' or 'system'
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now)