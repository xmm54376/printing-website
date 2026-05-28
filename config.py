# -*- coding: utf-8 -*-
"""
印刷公司官网 - Flask 配置（升级版）
"""

import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jc-printing-secret-2026-upgrade'

    # ── 数据库 ──
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///printing.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── 文件上传 ──
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # ── 站点基础信息（会被数据库的 SiteConfig 覆盖）──
    SITE_NAME = '精彩印刷'
    SITE_PHONE = '400-888-9999'
    SITE_PHONE_CHECK = '400-888-8888'
    SITE_PHONE_COMPLAINT = '400-888-7777'
    SITE_WECHAT = 'jingcaiprint'
    SITE_EMAIL = 'contact@jcprint.com'
    SITE_ADDRESS = '广东省深圳市宝安区印刷产业园A栋'
    SITE_ICP = ''

    # ── 管理员默认账户（仅用于初始化，实际密码存数据库）──
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin888'

    # ── 分页 ──
    ITEMS_PER_PAGE = 15
    STOCK_PER_PAGE = 12

    # ── 允许上传的文件类型 ──
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_FILE_EXTENSIONS = {'pdf', 'ai', 'psd', 'zip', 'rar', 'png', 'jpg', 'jpeg'}
