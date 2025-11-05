from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Device(db.Model):
    """设备模型"""
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 设备名称
    ip = db.Column(db.String(50))  # IP地址
    username = db.Column(db.String(100))  # 登录账号
    password = db.Column(db.String(100))  # 登录密码
    status = db.Column(db.String(20), default='available')  # 状态: available/occupied
    current_user = db.Column(db.String(100))  # 当前使用者中文名
    current_user_account = db.Column(db.String(100))  # 当前使用者账号
    occupy_duration = db.Column(db.Integer, default=2)  # 占用时长（小时）
    occupy_until = db.Column(db.DateTime)  # 占用截止时间
    ssh_connections = db.Column(db.Text)  # SSH连接配置 (JSON格式)
    serial_connections = db.Column(db.Text)  # 串口连接配置 (JSON格式)
    tags = db.Column(db.Text)  # 标签 (JSON格式)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系 - 使用 cascade 确保删除设备时同时删除相关记录
    usage_records = db.relationship('UsageRecord', backref='device', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Device {self.name}>'

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<User {self.username}>'

class UsageRecord(db.Model):
    """使用记录模型"""
    __tablename__ = 'usage_records'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)  # 使用人中文名
    user_account = db.Column(db.String(100))  # 使用人账号
    purpose = db.Column(db.Text)  # 使用目的
    start_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime)
    
    def get_duration(self):
        """计算使用时长（小时）"""
        if self.end_time:
            delta = self.end_time - self.start_time
            duration = round(delta.total_seconds() / 3600, 2)
            return max(0.00, duration)  # 确保最小值为0.00
        return 0.00  # 未结束的记录显示0.00而非None
    
    def __repr__(self):
        return f'<UsageRecord {self.id} - Device {self.device_id}>'

class AllowedUser(db.Model):
    """授权用户模型 - 只有在此列表中的用户才能占用设备"""
    __tablename__ = 'allowed_users'
    
    id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.String(100), unique=True, nullable=False)  # 账号（唯一标识）
    chinese_name = db.Column(db.String(100), nullable=False)  # 中文名
    department = db.Column(db.String(100))  # 部门（可选）
    password = db.Column(db.String(100), default='123456')  # 密码（默认123456）
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<AllowedUser {self.account} - {self.chinese_name}>'
