import os

class Config:
    # 替换你的数据库信息: mysql+pymysql://用户名:密码@地址/数据库名
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:www.cx123@localhost/smart_orchard'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key_123'  # 用于 Session 加密