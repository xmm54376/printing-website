# -*- coding: utf-8 -*-
"""
印刷公司官网 - 数据库模型（全面升级版）
对标：智盒包装 + 聚意印刷
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ============================================================
# 用户系统
# ============================================================

class AdminUser(db.Model):
    """后台管理员（原User模型，改名避免与前台用户冲突）"""
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    real_name = db.Column(db.String(50))
    role = db.Column(db.String(20), default='staff')  # super_admin / staff
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'role': self.role,
            'is_active': self.is_active,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M') if self.last_login else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
        }


class FrontUser(db.Model):
    """前台注册用户"""
    __tablename__ = 'front_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(100))
    password_hash = db.Column(db.String(200), nullable=False)
    real_name = db.Column(db.String(50))
    company = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联
    inquiries = db.relationship('Inquiry', backref='user', lazy='dynamic')
    orders = db.relationship('Order', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'phone': self.phone,
            'email': self.email,
            'real_name': self.real_name,
            'company': self.company,
        }


# ============================================================
# 网站内容管理
# ============================================================

class Banner(db.Model):
    """轮播图管理"""
    __tablename__ = 'banners'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    image = db.Column(db.String(300))           # 图片路径或URL
    link = db.Column(db.String(300))            # 点击跳转链接
    description = db.Column(db.String(300))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'image': self.image,
            'link': self.link,
            'description': self.description,
        }


class SiteConfig(db.Model):
    """网站配置键值对"""
    __tablename__ = 'site_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))

    @classmethod
    def get(cls, key, default=''):
        cfg = cls.query.filter_by(key=key).first()
        return cfg.value if cfg else default

    @classmethod
    def set(cls, key, value, description=''):
        cfg = cls.query.filter_by(key=key).first()
        if cfg:
            cfg.value = value
        else:
            cfg = cls(key=key, value=value, description=description)
            db.session.add(cfg)
        db.session.commit()


class Article(db.Model):
    """文章/印刷指南"""
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    summary = db.Column(db.String(500))
    cover_image = db.Column(db.String(300))
    category = db.Column(db.String(50))       # 印前规范 / 新手指南 / 常见问题 / 活动资讯
    view_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'cover_image': self.cover_image,
            'category': self.category,
            'view_count': self.view_count,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else None,
        }


class Coupon(db.Model):
    """优惠券"""
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100))
    discount_type = db.Column(db.String(20))   # percent（折扣）/ fixed（固定金额）
    discount_value = db.Column(db.Float)
    min_order = db.Column(db.Float, default=0) # 最低使用金额
    total_count = db.Column(db.Integer, default=0)  # 总发放数量，0=不限
    used_count = db.Column(db.Integer, default=0)
    valid_from = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def is_valid(self):
        now = datetime.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.total_count > 0 and self.used_count >= self.total_count:
            return False
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'min_order': self.min_order,
            'is_valid': self.is_valid,
            'valid_until': self.valid_until.strftime('%Y-%m-%d') if self.valid_until else None,
        }


# ============================================================
# 产品体系
# ============================================================

class ProductCategory(db.Model):
    """产品大分类"""
    __tablename__ = 'product_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)   # 卡盒 / 手提袋 / 彩箱 / 精品盒 / 其他
    icon = db.Column(db.String(100))                   # 图标类名或SVG
    image = db.Column(db.String(300))                  # 分类图片
    description = db.Column(db.String(300))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    # 关联盒型
    box_types = db.relationship('BoxType', backref='category', lazy='dynamic', order_by='BoxType.sort_order')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'image': self.image,
            'description': self.description,
            'box_count': self.box_types.filter_by(is_active=True).count(),
        }


class BoxType(db.Model):
    """盒型/产品类型"""
    __tablename__ = 'box_types'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)   # 双插盒 / 扣底盒 / 飞机盒 等
    alias = db.Column(db.String(100))                  # 别名（如：锁底盒/勾底盒）
    icon = db.Column(db.String(300))                   # 盒型图示/SVG图标
    thumbnail = db.Column(db.String(300))              # 缩略图
    description = db.Column(db.Text)
    # 参数配置（JSON字符串存储）
    # 格式：{"fields":["length","width","height"],"materials":["白卡纸","金卡纸"],"crafts":["覆膜","烫金"]}
    params_config = db.Column(db.Text, default='{}')
    min_quantity = db.Column(db.Integer, default=100)  # 起印量
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联报价规则
    quotation_rules = db.relationship('QuotationRule', backref='box_type', lazy='dynamic')

    def to_dict(self, with_rules=False):
        data = {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'name': self.name,
            'alias': self.alias,
            'icon': self.icon,
            'thumbnail': self.thumbnail,
            'description': self.description,
            'params_config': self.params_config,
            'min_quantity': self.min_quantity,
        }
        if with_rules:
            data['rules'] = [r.to_dict() for r in self.quotation_rules.all()]
        return data


class QuotationRule(db.Model):
    """报价规则"""
    __tablename__ = 'quotation_rules'

    id = db.Column(db.Integer, primary_key=True)
    box_type_id = db.Column(db.Integer, db.ForeignKey('box_types.id'), nullable=False)
    material = db.Column(db.String(50), default='通用')   # 材质条件（空=所有材质）
    base_price = db.Column(db.Float, default=0)            # 起步价（元）
    unit_price = db.Column(db.Float, default=0)            # 单价（元/个）
    min_quantity = db.Column(db.Integer, default=100)      # 最低数量
    # 阶梯价格（JSON字符串）
    # 格式：[{"min":100,"max":499,"unit":2.5},{"min":500,"max":999,"unit":2.0}]
    range_config = db.Column(db.Text, default='[]')
    remark = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'box_type_id': self.box_type_id,
            'material': self.material,
            'base_price': self.base_price,
            'unit_price': self.unit_price,
            'min_quantity': self.min_quantity,
            'range_config': self.range_config,
        }


class StockProduct(db.Model):
    """通用现货产品"""
    __tablename__ = 'stock_products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    specs = db.Column(db.Text)                     # 规格参数（JSON）
    image = db.Column(db.String(300))
    price = db.Column(db.Float, nullable=False)    # 售价
    original_price = db.Column(db.Float)           # 原价（划线价）
    unit = db.Column(db.String(20), default='个')
    min_order = db.Column(db.Integer, default=1)   # 起购量
    sales_count = db.Column(db.Integer, default=0) # 销量（可手动设置）
    stock = db.Column(db.Integer, default=999)     # 库存
    is_active = db.Column(db.Boolean, default=True)
    is_hot = db.Column(db.Boolean, default=False)  # 是否推荐/热销
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'image': self.image,
            'price': self.price,
            'original_price': self.original_price,
            'unit': self.unit,
            'min_order': self.min_order,
            'sales_count': self.sales_count,
            'is_hot': self.is_hot,
        }


# ============================================================
# 业务交易
# ============================================================

class Inquiry(db.Model):
    """在线询价单"""
    __tablename__ = 'inquiries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('front_users.id'), nullable=True)
    # 联系人信息
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    company = db.Column(db.String(100))
    email = db.Column(db.String(100))
    # 产品参数
    box_type_id = db.Column(db.Integer, db.ForeignKey('box_types.id'), nullable=True)
    product_type = db.Column(db.String(50), nullable=False)  # 冗余文字
    length = db.Column(db.Float)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    quantity = db.Column(db.Integer, nullable=False)
    material = db.Column(db.String(100))
    craft = db.Column(db.String(200))
    remark = db.Column(db.Text)
    file_name = db.Column(db.String(200))
    # 估算价格
    estimated_price_min = db.Column(db.Float)
    estimated_price_max = db.Column(db.Float)
    # 处理结果
    status = db.Column(db.String(20), default='待处理')  # 待处理/已报价/已成交/已关闭
    quote_price = db.Column(db.Float)
    quote_remark = db.Column(db.Text)
    # 时间
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'company': self.company,
            'product_type': self.product_type,
            'quantity': self.quantity,
            'material': self.material,
            'craft': self.craft,
            'status': self.status,
            'quote_price': self.quote_price,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
        }


class Order(db.Model):
    """订单（预留，支付接入后完善）"""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('front_users.id'), nullable=True)
    # 联系信息
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    # 产品信息（JSON存储）
    items = db.Column(db.Text)               # JSON格式的订单项目
    # 金额
    subtotal = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    coupon_code = db.Column(db.String(50))
    # 状态
    status = db.Column(db.String(20), default='待确认')  # 待确认/生产中/已发货/已完成/已取消
    payment_status = db.Column(db.String(20), default='未支付')
    payment_method = db.Column(db.String(20))
    # 发货信息
    shipping_address = db.Column(db.String(300))
    tracking_no = db.Column(db.String(100))
    remark = db.Column(db.Text)
    # 时间
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'name': self.name,
            'phone': self.phone,
            'total': self.total,
            'status': self.status,
            'payment_status': self.payment_status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
        }


class ContactMessage(db.Model):
    """留言/联系消息"""
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


# ============================================================
# 初始化默认数据
# ============================================================

def init_default_data(app):
    """初始化默认数据（首次运行时）"""
    with app.app_context():
        db.create_all()

        # ── 超级管理员 ──
        if not AdminUser.query.filter_by(username='admin').first():
            admin = AdminUser(username='admin', real_name='超级管理员', role='super_admin')
            admin.set_password('admin888')
            db.session.add(admin)
            print('已创建默认超级管理员: admin / admin888')

        # ── 网站配置 ──
        default_configs = [
            ('site_name', '精彩印刷', '网站名称'),
            ('site_phone', '400-888-9999', '服务热线'),
            ('site_phone_check', '400-888-8888', '查货热线'),
            ('site_phone_complaint', '400-888-7777', '投诉热线'),
            ('site_wechat', 'jingcaiprint', '微信号'),
            ('site_email', 'contact@jcprint.com', '联系邮箱'),
            ('site_address', '广东省深圳市宝安区印刷产业园A栋', '公司地址'),
            ('site_icp', '', 'ICP备案号'),
            ('site_qq1', '', 'QQ客服1'),
            ('site_qq2', '', 'QQ客服2'),
            ('stat_experience', '10', '行业经验（年）'),
            ('stat_clients', '5000', '服务客户数量'),
            ('stat_projects', '50000', '完成项目数量'),
            ('stat_satisfaction', '99', '客户满意度（%）'),
        ]
        for key, value, desc in default_configs:
            if not SiteConfig.query.filter_by(key=key).first():
                db.session.add(SiteConfig(key=key, value=value, description=desc))

        # ── 产品大分类 ──
        categories_data = [
            ('卡盒', '📦', '白卡/金银卡纸盒定制，多种盒型，小批量起印', 1),
            ('手提袋', '🛍️', '专属品牌手提袋，移动式广告载体', 2),
            ('彩箱/瓦楞盒', '📫', '结实耐用彩箱，适合物流运输', 3),
            ('精品礼盒', '🎁', '高端精品礼盒，提升品牌溢价', 4),
            ('其他印刷品', '📄', '不干胶标签、说明书、包装设计等', 5),
        ]
        cat_map = {}
        for name, icon, desc, sort in categories_data:
            if not ProductCategory.query.filter_by(name=name).first():
                cat = ProductCategory(name=name, icon=icon, description=desc, sort_order=sort)
                db.session.add(cat)
                db.session.flush()
                cat_map[name] = cat.id
            else:
                cat = ProductCategory.query.filter_by(name=name).first()
                cat_map[name] = cat.id

        db.session.flush()

        # ── 盒型数据 ──
        box_types_data = [
            # (分类名, 盒型名, 别名, 起印量, 排序)
            # 卡盒
            ('卡盒', '双插盒', None, 100, 1),
            ('卡盒', 'T型双插盒', None, 100, 2),
            ('卡盒', '扣底盒', None, 100, 3),
            ('卡盒', '带安全扣扣底盒', None, 100, 4),
            ('卡盒', '锁底盒', '勾底盒', 100, 5),
            ('卡盒', '带安全扣勾底盒', None, 100, 6),
            ('卡盒', '平粘盒', None, 100, 7),
            ('卡盒', '挂勾双插盒', None, 100, 8),
            ('卡盒', '挂勾扣底盒', None, 100, 9),
            ('卡盒', '飞机盒', None, 100, 10),
            ('卡盒', '腰封', None, 200, 11),
            ('卡盒', '抽屉盒', None, 100, 12),
            ('卡盒', '天地盖盒', None, 100, 13),
            ('卡盒', '手提盒', None, 100, 14),
            ('卡盒', '单插盒', None, 100, 15),
            # 手提袋
            ('手提袋', '手提袋', None, 100, 1),
            # 彩箱/瓦楞盒
            ('彩箱/瓦楞盒', '双插盒（瓦楞）', None, 50, 1),
            ('彩箱/瓦楞盒', '扣底盒（瓦楞）', None, 50, 2),
            ('彩箱/瓦楞盒', '飞机盒（瓦楞）', None, 50, 3),
            ('彩箱/瓦楞盒', '天地盖盒（瓦楞）', None, 50, 4),
            ('彩箱/瓦楞盒', '屋顶箱', None, 50, 5),
            ('彩箱/瓦楞盒', '手提箱', None, 50, 6),
            ('彩箱/瓦楞盒', '平口对插箱', None, 50, 7),
            ('彩箱/瓦楞盒', '对口箱', None, 50, 8),
            # 精品礼盒
            ('精品礼盒', '书型盒', None, 50, 1),
            ('精品礼盒', '全包天地盖', None, 50, 2),
            ('精品礼盒', '围框天地盒', None, 50, 3),
            ('精品礼盒', '抽拉盒', None, 50, 4),
            # 其他
            ('其他印刷品', '不干胶标签', None, 500, 1),
            ('其他印刷品', '说明书/单页', None, 200, 2),
            ('其他印刷品', '包装设计服务', None, 1, 3),
        ]

        import json
        default_params = json.dumps({
            "fields": ["length", "width", "height"],
            "materials": ["白卡纸", "金卡纸", "银卡纸", "牛皮纸", "哑粉纸", "铜版纸"],
            "crafts": ["覆亮膜", "覆哑膜", "烫金", "烫银", "UV", "压纹", "凹凸", "镂空"],
        }, ensure_ascii=False)

        for cat_name, box_name, alias, min_qty, sort in box_types_data:
            if cat_name in cat_map and not BoxType.query.filter_by(name=box_name).first():
                bt = BoxType(
                    category_id=cat_map[cat_name],
                    name=box_name,
                    alias=alias,
                    min_quantity=min_qty,
                    sort_order=sort,
                    params_config=default_params,
                )
                db.session.add(bt)

        db.session.flush()

        # ── 报价规则（每种盒型默认规则）──
        all_boxes = BoxType.query.all()
        price_map = {
            '卡盒': (0.8, 0.5, 0.3),          # (100+单价, 500+单价, 1000+单价)
            '手提袋': (1.5, 1.2, 1.0),
            '彩箱/瓦楞盒': (2.0, 1.5, 1.2),
            '精品礼盒': (5.0, 4.0, 3.5),
            '其他印刷品': (0.3, 0.2, 0.15),
        }
        for bt in all_boxes:
            if QuotationRule.query.filter_by(box_type_id=bt.id).first():
                continue
            cat_name = bt.category.name if bt.category else '卡盒'
            prices = price_map.get(cat_name, (1.0, 0.8, 0.6))
            range_config = json.dumps([
                {"min": bt.min_quantity, "max": 499, "unit_price": prices[0]},
                {"min": 500, "max": 999, "unit_price": prices[1]},
                {"min": 1000, "max": 9999, "unit_price": prices[2]},
            ], ensure_ascii=False)
            rule = QuotationRule(
                box_type_id=bt.id,
                material='通用',
                base_price=50,
                unit_price=prices[0],
                min_quantity=bt.min_quantity,
                range_config=range_config,
            )
            db.session.add(rule)

        # ── 轮播图 ──
        if Banner.query.count() == 0:
            banners_data = [
                ('精彩印刷 · 品质定制', '/offer', '专业包装定制，小批量起印，快速交货', 1),
                ('六大优势 · 品质保障', '/about', '工厂直销，没有中间商，价格直降70%', 2),
                ('免费打样 · 极速交货', '/offer', '下单即安排，72小时出样，满意再大货', 3),
            ]
            for title, link, desc, sort in banners_data:
                db.session.add(Banner(title=title, link=link, description=desc, sort_order=sort, image=''))

        # ── 示例文章 ──
        if Article.query.count() == 0:
            articles_data = [
                ('如何选择适合的纸张材质', '印前规范', '白卡纸、铜版纸、牛皮纸…不同材质有不同的适用场景。本文带你了解常见印刷纸张的特点和选择建议。'),
                ('印刷色彩模式：CMYK vs RGB', '印前规范', '为什么印出来的颜色和电脑上看到的不一样？深入解析CMYK与RGB的区别，以及如何正确设置印前文件。'),
                ('出血位是什么，为什么必须设置', '印前规范', '设计文件必须留出血位，否则裁切后会出现白边。本文详解出血位的设置方法。'),
                ('新手下单指南：从报价到收货全流程', '新手指南', '第一次定制包装？别担心，这篇指南一步步告诉你怎么做。'),
                ('如何计算包装盒的展开尺寸', '新手指南', '了解盒型结构，掌握展开尺寸计算方法，避免尺寸错误导致返工。'),
                ('为什么印刷起订量最低100个', '常见问题', '印刷开机有固定成本，批量越大单价越低。我们解释为什么有最低起印量以及如何降低成本。'),
            ]
            for title, cat, summary in articles_data:
                db.session.add(Article(
                    title=title,
                    category=cat,
                    summary=summary,
                    content=f'<p>{summary}</p><p>（详细内容待编辑…）</p>',
                    is_active=True,
                ))

        # ── 示例现货产品 ──
        if StockProduct.query.count() == 0:
            stock_data = [
                ('通用礼品纸箱（橙子款）', '彩箱', 35.90, 5000, '适合橙子、柚子、苹果等水果礼品，精美印刷，加厚材质'),
                ('熟食礼品盒（通用款）', '精品礼盒', 39.90, 300, '适用于卤味、烧鸡、土特产等熟食礼品，高档大气'),
                ('葡萄礼盒包装盒', '彩箱', 25.00, 200, '适合葡萄、草莓等水果礼品，内衬保护'),
                ('牛皮纸手提袋（中号）', '手提袋', 1.80, 1000, '通用牛皮纸手提袋，可按需印logo'),
                ('白卡纸折叠盒（通用）', '卡盒', 0.80, 5000, '常用白卡纸折叠盒，适合小商品包装'),
            ]
            for name, cat, price, sales, desc in stock_data:
                db.session.add(StockProduct(
                    name=name,
                    category=cat,
                    price=price,
                    sales_count=sales,
                    description=desc,
                    is_hot=True,
                    stock=999,
                ))

        # ── 示例优惠券 ──
        if Coupon.query.count() == 0:
            db.session.add(Coupon(
                code='NEW100',
                name='新用户立减100元',
                discount_type='fixed',
                discount_value=100,
                min_order=500,
                total_count=100,
                is_active=True,
            ))
            db.session.add(Coupon(
                code='SALE9',
                name='全场9折优惠',
                discount_type='percent',
                discount_value=90,
                min_order=200,
                total_count=0,
                is_active=True,
            ))

        db.session.commit()
        print('默认数据初始化完成')
