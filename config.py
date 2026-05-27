# -*- coding: utf-8 -*-
"""
印刷公司官网 - Flask 后端配置
"""

class Config:
    SECRET_KEY = 'jc-printing-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///printing.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin888'
    SITE_NAME = '精彩印刷'
    SITE_PHONE = '400-888-9999'
    SITE_WECHAT = 'jingcaiprint'
    SITE_EMAIL = 'contact@jcprint.com'
    SITE_ADDRESS = '广东省深圳市宝安区福海街道印刷产业园A栋'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
