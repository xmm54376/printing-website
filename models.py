# -*- coding: utf-8 -*-
"""
印刷公司官网 - 数据库模型
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Inquiry(db.Model):
    """在线询价表"""
    __tablename__ = 'inquiries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    phone = db.Column(db.String(20), nullable=False, comment='电话')
    company = db.Column(db.String(100), comment='公司名称')
    product_type = db.Column(db.String(50), nullable=False, comment='产品类型')
    length = db.Column(db.Float, comment='长度(mm)')
    width = db.Column(db.Float, comment='宽度(mm)')
    height = db.Column(db.Float, comment='高度(mm)')
    quantity = db.Column(db.Integer, nullable=False, comment='数量')
    material = db.Column(db.String(100), comment='材质要求')
    craft = db.Column(db.String(200), comment='工艺要求')
    remark = db.Column(db.Text, comment='备注')
    file_name = db.Column(db.String(200), comment='上传文件名')
    status = db.Column(db.String(20), default='待处理', comment='状态: 待处理/已报价/已成交/已关闭')
    quote_price = db.Column(db.Float, comment='报价金额')
    quote_remark = db.Column(db.Text, comment='报价备注')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'company': self.company or '',
            'product_type': self.product_type,
            'length': self.length or 0,
            'width': self.width or 0,
            'height': self.height or 0,
            'quantity': self.quantity,
            'material': self.material or '',
            'craft': self.craft or '',
            'remark': self.remark or '',
            'file_name': self.file_name or '',
            'status': self.status,
            'quote_price': self.quote_price,
            'quote_remark': self.quote_remark or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else '',
        }


class Product(db.Model):
    """产品管理表"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='产品名称')
    category = db.Column(db.String(50), nullable=False, comment='产品分类')
    description = db.Column(db.Text, comment='产品描述')
    image = db.Column(db.String(200), comment='产品图片')
    min_price = db.Column(db.Float, comment='起步价')
    unit = db.Column(db.String(20), default='个', comment='计价单位')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description or '',
            'image': self.image or '',
            'min_price': self.min_price or 0,
            'unit': self.unit,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
        }


class SiteConfig(db.Model):
    """网站配置表"""
    __tablename__ = 'site_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False, comment='配置键')
    value = db.Column(db.Text, comment='配置值')
    description = db.Column(db.String(200), comment='配置说明')


class ContactMessage(db.Model):
    """留言/联系表"""
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email or '',
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
        }
