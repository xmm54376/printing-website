# -*- coding: utf-8 -*-
"""
印刷公司官网 - Flask 主应用（全面升级版）
对标：智盒包装(zhihebox.com) + 聚意印刷(juyiyinshua.com)
"""

import os
import json
import uuid
import csv
import io
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, flash, session, send_file,
    make_response
)
from werkzeug.utils import secure_filename

from config import Config
from models import (
    db, AdminUser, FrontUser, Banner, SiteConfig, Article, Coupon,
    ProductCategory, BoxType, QuotationRule, StockProduct,
    Inquiry, Order, ContactMessage, FAQ, init_default_data
)


def create_app():
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    app.config.from_object(Config)

    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    # 注册蓝图（路由）
    _register_frontend_routes(app)
    _register_api_routes(app)
    _register_admin_routes(app)

    # 自定义404错误处理
    @app.errorhandler(404)
    def page_not_found(e):
        cfg = get_site_config()
        return render_template('404.html', cfg=cfg), 404

    # robots.txt 和 sitemap.xml
    @app.route('/robots.txt')
    def robots_txt():
        return app.send_static_file('robots.txt')

    @app.route('/sitemap.xml')
    def sitemap_xml():
        return app.send_static_file('sitemap.xml')

    return app


# ============================================================
# 认证装饰器
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


def super_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        if session.get('admin_role') != 'super_admin':
            flash('此操作需要超级管理员权限', 'error')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated


def front_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('user_login'))
        return f(*args, **kwargs)
    return decorated


# ============================================================
# 辅助函数
# ============================================================

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


def get_site_config():
    """获取常用网站配置"""
    return {
        'site_name': SiteConfig.get('site_name', Config.SITE_NAME),
        'site_phone': SiteConfig.get('site_phone', Config.SITE_PHONE),
        'site_phone_check': SiteConfig.get('site_phone_check', Config.SITE_PHONE_CHECK),
        'site_phone_complaint': SiteConfig.get('site_phone_complaint', Config.SITE_PHONE_COMPLAINT),
        'site_wechat': SiteConfig.get('site_wechat', Config.SITE_WECHAT),
        'site_email': SiteConfig.get('site_email', Config.SITE_EMAIL),
        'site_address': SiteConfig.get('site_address', Config.SITE_ADDRESS),
        'site_icp': SiteConfig.get('site_icp', Config.SITE_ICP),
        'site_qq1': SiteConfig.get('site_qq1', ''),
        'site_qq2': SiteConfig.get('site_qq2', ''),
        'site_qq3': SiteConfig.get('site_qq3', ''),
        'site_logo': SiteConfig.get('site_logo', ''),
        'site_favicon': SiteConfig.get('site_favicon', ''),
        'site_qrcode_wechat': SiteConfig.get('site_qrcode_wechat', ''),
        'site_about_image1': SiteConfig.get('site_about_image1', ''),
        'site_about_image2': SiteConfig.get('site_about_image2', ''),
        'seo_title': SiteConfig.get('seo_title', ''),
        'seo_description': SiteConfig.get('seo_description', ''),
        'seo_keywords': SiteConfig.get('seo_keywords', ''),
        'business_hours': SiteConfig.get('business_hours', '周一至周六 8:30-18:00'),
        'site_description': SiteConfig.get('site_description', ''),
    }


def _register_frontend_routes(app):
    """注册前台路由"""

    @app.route('/')
    def index():
        categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.sort_order).all()
        banners = Banner.query.filter_by(is_active=True).order_by(Banner.sort_order).all()
        hot_stocks = StockProduct.query.filter_by(is_active=True, is_hot=True).order_by(
            StockProduct.sales_count.desc()).limit(6).all()
        stats = {
            'experience': SiteConfig.get('stat_experience', '10'),
            'clients': SiteConfig.get('stat_clients', '5000'),
            'projects': SiteConfig.get('stat_projects', '50000'),
            'satisfaction': SiteConfig.get('stat_satisfaction', '99'),
        }
        cfg = get_site_config()
        return render_template('index.html',
                               categories=categories,
                               banners=banners,
                               hot_stocks=hot_stocks,
                               stats=stats,
                               cfg=cfg)

    @app.route('/offer')
    @app.route('/offer/<int:box_type_id>')
    def offer(box_type_id=None):
        categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.sort_order).all()
        selected_box = None
        if box_type_id:
            selected_box = BoxType.query.get(box_type_id)
        cfg = get_site_config()
        return render_template('offer.html',
                               categories=categories,
                               selected_box=selected_box,
                               cfg=cfg)

    @app.route('/products')
    def products():
        category = request.args.get('category', '')
        keyword = request.args.get('keyword', '') or request.args.get('q', '')
        page = request.args.get('page', 1, type=int)

        query = StockProduct.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        if keyword:
            query = query.filter(StockProduct.name.contains(keyword))

        pagination = query.order_by(StockProduct.sales_count.desc()).paginate(
            page=page, per_page=Config.STOCK_PER_PAGE, error_out=False)

        # 所有分类
        cats = db.session.query(StockProduct.category).filter_by(is_active=True).distinct().all()
        categories = [c[0] for c in cats if c[0]]

        cfg = get_site_config()
        return render_template('products.html',
                               products=pagination.items,
                               pagination=pagination,
                               categories=categories,
                               current_category=category,
                               keyword=keyword,
                               cfg=cfg)

    @app.route('/product/<int:pid>')
    def product_detail(pid):
        product = StockProduct.query.get_or_404(pid)
        related = StockProduct.query.filter_by(
            category=product.category, is_active=True
        ).filter(StockProduct.id != pid).limit(4).all()
        cfg = get_site_config()
        return render_template('product_detail.html',
                               product=product,
                               related=related,
                               cfg=cfg)

    @app.route('/about')
    def about():
        cfg = get_site_config()
        return render_template('about.html', cfg=cfg)

    @app.route('/contact')
    def contact():
        cfg = get_site_config()
        return render_template('contact.html', cfg=cfg)

    @app.route('/guide')
    def guide():
        category = request.args.get('category', '')
        page = request.args.get('page', 1, type=int)
        query = Article.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        pagination = query.order_by(Article.sort_order, Article.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False)
        cats = db.session.query(Article.category).filter_by(is_active=True).distinct().all()
        categories = [c[0] for c in cats if c[0]]
        cfg = get_site_config()
        return render_template('guide.html',
                               articles=pagination.items,
                               pagination=pagination,
                               categories=categories,
                               current_category=category,
                               cfg=cfg)

    @app.route('/guide/<int:aid>')
    def guide_detail(aid):
        article = Article.query.get_or_404(aid)
        article.view_count = (article.view_count or 0) + 1
        db.session.commit()
        cfg = get_site_config()
        return render_template('guide_detail.html', article=article, cfg=cfg)

    @app.route('/activity')
    def activity():
        coupons = Coupon.query.filter_by(is_active=True).all()
        valid_coupons = [c for c in coupons if c.is_valid]
        articles = Article.query.filter_by(category='活动资讯', is_active=True).limit(6).all()
        cfg = get_site_config()
        return render_template('activity.html',
                               coupons=valid_coupons,
                               articles=articles,
                               cfg=cfg)

    @app.route('/faq')
    def faq():
        category = request.args.get('category', '')
        query = FAQ.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        faqs = query.order_by(FAQ.sort_order).all()
        # 所有分类
        cats = db.session.query(FAQ.category).filter_by(is_active=True).distinct().all()
        categories = [c[0] for c in cats if c[0]]
        cfg = get_site_config()
        return render_template('faq.html', faqs=faqs, categories=categories,
                               current_category=category, cfg=cfg)

    @app.route('/inquiry-query')
    def inquiry_query():
        """前台询价进度查询（无需登录）"""
        cfg = get_site_config()
        return render_template('inquiry_query.html', cfg=cfg)

    @app.route('/api/inquiry-query', methods=['POST'])
    def api_inquiry_query():
        """根据手机号+询价ID查询询价进度"""
        data = request.get_json() or {}
        inquiry_id = data.get('inquiry_id', '').strip()
        phone = data.get('phone', '').strip()

        if not inquiry_id or not phone:
            return jsonify({'ok': False, 'msg': '请填写询价单号和手机号'})

        try:
            iid = int(inquiry_id)
        except ValueError:
            return jsonify({'ok': False, 'msg': '询价单号格式不正确'})

        inquiry = Inquiry.query.filter_by(id=iid, phone=phone).first()
        if not inquiry:
            return jsonify({'ok': False, 'msg': '未找到匹配的询价记录，请检查单号和手机号'})

        return jsonify({
            'ok': True,
            'inquiry': {
                'id': inquiry.id,
                'status': inquiry.status,
                'product_type': inquiry.product_type,
                'quantity': inquiry.quantity,
                'created_at': inquiry.created_at.strftime('%Y-%m-%d %H:%M') if inquiry.created_at else '',
                'quote_price': inquiry.quote_price,
                'quote_remark': inquiry.quote_remark,
                'updated_at': inquiry.updated_at.strftime('%Y-%m-%d %H:%M') if inquiry.updated_at else '',
            }
        })

    @app.route('/login', methods=['GET', 'POST'])
    def user_login():
        if session.get('user_id'):
            return redirect(url_for('user_center'))
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            user = FrontUser.query.filter(
                (FrontUser.username == username) | (FrontUser.phone == username)
            ).first()
            if user and user.check_password(password) and user.is_active:
                session['user_id'] = user.id
                session['user_name'] = user.real_name or user.username
                user.last_login = datetime.now()
                db.session.commit()
                next_url = request.args.get('next') or url_for('user_center')
                return redirect(next_url)
            flash('用户名/手机号或密码错误', 'error')
        cfg = get_site_config()
        return render_template('login.html', cfg=cfg)

    @app.route('/register', methods=['GET', 'POST'])
    def user_register():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '').strip()
            real_name = request.form.get('real_name', '').strip()

            if not username or not phone or not password:
                flash('请填写必填字段', 'error')
            elif FrontUser.query.filter_by(username=username).first():
                flash('用户名已被使用', 'error')
            elif FrontUser.query.filter_by(phone=phone).first():
                flash('该手机号已注册', 'error')
            else:
                user = FrontUser(username=username, phone=phone, real_name=real_name)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                session['user_id'] = user.id
                session['user_name'] = user.real_name or user.username
                return redirect(url_for('user_center'))
        cfg = get_site_config()
        return render_template('register.html', cfg=cfg)

    @app.route('/logout')
    def user_logout():
        session.pop('user_id', None)
        session.pop('user_name', None)
        return redirect(url_for('index'))

    @app.route('/user')
    @front_login_required
    def user_center():
        user = FrontUser.query.get(session['user_id'])
        inquiries = Inquiry.query.filter_by(user_id=user.id).order_by(
            Inquiry.created_at.desc()).limit(5).all()
        orders = Order.query.filter_by(user_id=user.id).order_by(
            Order.created_at.desc()).limit(5).all()
        cfg = get_site_config()
        return render_template('user/center.html', user=user, inquiries=inquiries, orders=orders, cfg=cfg)

    @app.route('/user/inquiries')
    @front_login_required
    def user_inquiries():
        page = request.args.get('page', 1, type=int)
        pagination = Inquiry.query.filter_by(user_id=session['user_id']).order_by(
            Inquiry.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
        cfg = get_site_config()
        return render_template('user/inquiries.html', pagination=pagination, cfg=cfg)

    @app.route('/user/orders')
    @front_login_required
    def user_orders():
        page = request.args.get('page', 1, type=int)
        pagination = Order.query.filter_by(user_id=session['user_id']).order_by(
            Order.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
        cfg = get_site_config()
        return render_template('user/orders.html', pagination=pagination, cfg=cfg)

    @app.route('/user/profile', methods=['GET', 'POST'])
    @front_login_required
    def user_profile():
        user = FrontUser.query.get(session['user_id'])
        if request.method == 'POST':
            user.real_name = request.form.get('real_name', '').strip()
            user.company = request.form.get('company', '').strip()
            user.email = request.form.get('email', '').strip()
            db.session.commit()
            flash('个人信息已更新', 'success')
        cfg = get_site_config()
        return render_template('user/profile.html', user=user, cfg=cfg)

    @app.route('/user/change-password', methods=['POST'])
    @front_login_required
    def user_change_password():
        user = FrontUser.query.get(session['user_id'])
        old_pw = request.form.get('old_password', '')
        new_pw = request.form.get('new_password', '')
        confirm_pw = request.form.get('confirm_password', '')
        if not user.check_password(old_pw):
            flash('当前密码错误', 'error')
            return redirect(url_for('user_profile'))
        if len(new_pw) < 8:
            flash('新密码至少8位', 'error')
            return redirect(url_for('user_profile'))
        if new_pw != confirm_pw:
            flash('两次输入的新密码不一致', 'error')
            return redirect(url_for('user_profile'))
        user.set_password(new_pw)
        db.session.commit()
        flash('密码修改成功', 'success')
        return redirect(url_for('user_profile'))

    @app.route('/user/inquiry/<int:iid>')
    @front_login_required
    def user_inquiry_detail(iid):
        inquiry = Inquiry.query.get_or_404(iid)
        if inquiry.user_id != session['user_id']:
            flash('无权查看该询价', 'error')
            return redirect(url_for('user_inquiries'))
        cfg = get_site_config()
        return render_template('user/inquiry_detail.html', inquiry=inquiry, cfg=cfg)

    @app.route('/user/order/<int:oid>')
    @front_login_required
    def user_order_detail(oid):
        order = Order.query.get_or_404(oid)
        if order.user_id != session['user_id']:
            flash('无权查看该订单', 'error')
            return redirect(url_for('user_orders'))
        cfg = get_site_config()
        return render_template('user/order_detail.html', order=order, cfg=cfg)

    @app.route('/forgot-password')
    def forgot_password():
        cfg = get_site_config()
        return render_template('forgot_password.html', cfg=cfg)

    @app.route('/terms')
    def terms():
        cfg = get_site_config()
        return render_template('terms.html', cfg=cfg)

    @app.route('/privacy')
    def privacy():
        cfg = get_site_config()
        return render_template('privacy.html', cfg=cfg)


def _register_api_routes(app):
    """注册前台 API 路由"""

    @app.route('/api/categories')
    def api_categories():
        cats = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.sort_order).all()
        result = []
        for cat in cats:
            cat_dict = cat.to_dict()
            cat_dict['box_types'] = [bt.to_dict() for bt in
                                     cat.box_types.filter_by(is_active=True).order_by(BoxType.sort_order).all()]
            result.append(cat_dict)
        return jsonify(result)

    @app.route('/api/box-type/<int:btid>')
    def api_box_type(btid):
        bt = BoxType.query.get_or_404(btid)
        return jsonify(bt.to_dict(with_rules=True))

    @app.route('/api/offer/calculate', methods=['POST'])
    def api_calculate_price():
        data = request.get_json() or {}
        box_type_id = data.get('box_type_id')
        quantity = int(data.get('quantity', 0))
        material = data.get('material', '通用')

        if not box_type_id or quantity <= 0:
            return jsonify({'ok': False, 'msg': '请选择盒型并填写数量'})

        bt = BoxType.query.get(box_type_id)
        if not bt:
            return jsonify({'ok': False, 'msg': '盒型不存在'})

        if quantity < bt.min_quantity:
            return jsonify({
                'ok': False,
                'msg': f'该盒型最低起印量为 {bt.min_quantity} 个'
            })

        # 查找匹配规则（先找材质匹配，再找通用）
        rule = QuotationRule.query.filter_by(
            box_type_id=box_type_id, material=material, is_active=True).first()
        if not rule:
            rule = QuotationRule.query.filter_by(
                box_type_id=box_type_id, material='通用', is_active=True).first()
        if not rule:
            return jsonify({'ok': False, 'msg': '暂无报价规则，请联系客服'})

        # 从阶梯价格计算
        unit_price = rule.unit_price
        try:
            ranges = json.loads(rule.range_config)
            for r in ranges:
                if r['min'] <= quantity <= r.get('max', 999999):
                    unit_price = r['unit_price']
                    break
        except Exception:
            pass

        subtotal = rule.base_price + unit_price * quantity
        # 给出一个浮动区间（±10%）
        price_min = round(subtotal * 0.9, 2)
        price_max = round(subtotal * 1.1, 2)

        return jsonify({
            'ok': True,
            'unit_price': unit_price,
            'base_price': rule.base_price,
            'subtotal': round(subtotal, 2),
            'price_min': price_min,
            'price_max': price_max,
            'msg': f'参考报价：¥{price_min} ~ ¥{price_max}（含起步费，最终以客服确认为准）'
        })

    @app.route('/api/offer/submit', methods=['POST'])
    def api_submit_inquiry():
        # 支持 JSON 和 multipart/form-data
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()

        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        product_type = data.get('product_type', '').strip()
        quantity_str = data.get('quantity', '0')

        if not name:
            return jsonify({'ok': False, 'msg': '请填写姓名'})
        if not phone or len(phone) < 7:
            return jsonify({'ok': False, 'msg': '请填写正确的手机号'})
        if not product_type:
            return jsonify({'ok': False, 'msg': '请选择产品类型'})

        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            return jsonify({'ok': False, 'msg': '请填写正确的数量'})

        # 文件上传处理
        file_name = None
        if 'file' in request.files:
            f = request.files['file']
            if f and f.filename and allowed_file(f.filename, Config.ALLOWED_FILE_EXTENSIONS):
                ext = f.filename.rsplit('.', 1)[1].lower()
                file_name = f'{uuid.uuid4().hex}.{ext}'
                f.save(os.path.join(Config.UPLOAD_FOLDER, file_name))

        inquiry = Inquiry(
            user_id=session.get('user_id'),
            name=name,
            phone=phone,
            company=data.get('company', ''),
            email=data.get('email', ''),
            box_type_id=data.get('box_type_id') or None,
            product_type=product_type,
            length=float(data.get('length') or 0) or None,
            width=float(data.get('width') or 0) or None,
            height=float(data.get('height') or 0) or None,
            quantity=quantity,
            material=data.get('material', ''),
            craft=data.get('craft', ''),
            print_color=data.get('print_color', ''),
            paper_weight=data.get('paper_weight', ''),
            need_sample=data.get('need_sample') == '1',
            remark=data.get('remark', ''),
            file_name=file_name,
            estimated_price_min=float(data.get('price_min') or 0) or None,
            estimated_price_max=float(data.get('price_max') or 0) or None,
        )
        db.session.add(inquiry)
        db.session.commit()

        return jsonify({
            'ok': True,
            'msg': '询价提交成功！我们的客服会在2小时内与您联系，请保持手机畅通。',
            'inquiry_id': inquiry.id
        })

    @app.route('/api/stock-products')
    def api_stock_products():
        category = request.args.get('category', '')
        keyword = request.args.get('q', '')
        limit = request.args.get('limit', 12, type=int)

        query = StockProduct.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        if keyword:
            query = query.filter(StockProduct.name.contains(keyword))
        items = query.order_by(StockProduct.sales_count.desc()).limit(limit).all()
        return jsonify([p.to_dict() for p in items])

    @app.route('/api/banners')
    def api_banners():
        banners = Banner.query.filter_by(is_active=True).order_by(Banner.sort_order).all()
        return jsonify([b.to_dict() for b in banners])

    @app.route('/api/articles')
    def api_articles():
        category = request.args.get('category', '')
        limit = request.args.get('limit', 10, type=int)
        query = Article.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        items = query.order_by(Article.created_at.desc()).limit(limit).all()
        return jsonify([a.to_dict() for a in items])

    @app.route('/api/coupons')
    def api_coupons():
        coupons = Coupon.query.filter_by(is_active=True).all()
        return jsonify([c.to_dict() for c in coupons if c.is_valid])

    @app.route('/api/contact', methods=['POST'])
    def api_contact():
        data = request.get_json() or request.form.to_dict()
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        message = data.get('message', '').strip()

        if not name or not phone or not message:
            return jsonify({'ok': False, 'msg': '请填写姓名、电话和留言内容'})

        msg = ContactMessage(
            name=name, phone=phone,
            email=data.get('email', ''),
            message=message
        )
        db.session.add(msg)
        db.session.commit()
        return jsonify({'ok': True, 'msg': '留言提交成功，我们会尽快回复您！'})

    @app.route('/api/user/register', methods=['POST'])
    def api_user_register():
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()

        if not username or not phone or not password:
            return jsonify({'ok': False, 'msg': '请填写完整信息'})
        if FrontUser.query.filter_by(username=username).first():
            return jsonify({'ok': False, 'msg': '用户名已存在'})
        if FrontUser.query.filter_by(phone=phone).first():
            return jsonify({'ok': False, 'msg': '手机号已注册'})

        user = FrontUser(username=username, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['user_name'] = user.username
        return jsonify({'ok': True, 'msg': '注册成功'})

    @app.route('/api/user/login', methods=['POST'])
    def api_user_login():
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        user = FrontUser.query.filter(
            (FrontUser.username == username) | (FrontUser.phone == username)
        ).first()
        if not user or not user.check_password(password) or not user.is_active:
            return jsonify({'ok': False, 'msg': '账号或密码错误'})

        session['user_id'] = user.id
        session['user_name'] = user.real_name or user.username
        user.last_login = datetime.now()
        db.session.commit()
        return jsonify({'ok': True, 'msg': '登录成功', 'user': user.to_dict()})

    @app.route('/api/user/logout', methods=['POST'])
    def api_user_logout():
        session.pop('user_id', None)
        session.pop('user_name', None)
        return jsonify({'ok': True})


def _register_admin_routes(app):
    """注册后台管理路由"""

    # ── 认证 ──

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            user = AdminUser.query.filter_by(username=username, is_active=True).first()
            if user and user.check_password(password):
                session['is_admin'] = True
                session['admin_user'] = user.real_name or user.username
                session['admin_role'] = user.role
                session['admin_uid'] = user.id
                user.last_login = datetime.now()
                db.session.commit()
                return redirect(url_for('admin_dashboard'))
            flash('用户名或密码错误', 'error')
        return render_template('admin/login.html')

    @app.route('/admin/logout')
    def admin_logout():
        session.pop('is_admin', None)
        session.pop('admin_user', None)
        session.pop('admin_role', None)
        session.pop('admin_uid', None)
        return redirect(url_for('admin_login'))

    # ── 仪表盘 ──

    @app.route('/admin/')
    @app.route('/admin')
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        stats = {
            'total_inquiries': Inquiry.query.count(),
            'pending': Inquiry.query.filter_by(status='待处理').count(),
            'quoted': Inquiry.query.filter_by(status='已报价').count(),
            'completed': Inquiry.query.filter_by(status='已成交').count(),
            'total_messages': ContactMessage.query.count(),
            'unread_messages': ContactMessage.query.filter_by(is_read=False).count(),
            'total_products': StockProduct.query.count(),
            'active_products': StockProduct.query.filter_by(is_active=True).count(),
            'total_orders': Order.query.count(),
            'total_users': FrontUser.query.count(),
            'total_box_types': BoxType.query.count(),
        }
        recent_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(8).all()
        recent_messages = ContactMessage.query.filter_by(is_read=False).order_by(
            ContactMessage.created_at.desc()).limit(5).all()
        return render_template('admin/dashboard.html',
                               stats=stats,
                               recent_inquiries=recent_inquiries,
                               recent_messages=recent_messages)

    @app.route('/admin/api/stats')
    @login_required
    def admin_api_stats():
        from sqlalchemy import func
        # 近7天询价趋势
        trend_data = []
        for i in range(6, -1, -1):
            from datetime import timedelta
            day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            day_start = day - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            count = Inquiry.query.filter(
                Inquiry.created_at >= day_start,
                Inquiry.created_at < day_end
            ).count()
            trend_data.append({'date': day_start.strftime('%m/%d'), 'count': count})

        # 盒型分类分布
        cat_stats = db.session.query(
            Inquiry.product_type,
            func.count(Inquiry.id).label('cnt')
        ).group_by(Inquiry.product_type).order_by(func.count(Inquiry.id).desc()).limit(8).all()

        return jsonify({
            'trend': trend_data,
            'categories': [{'name': r[0], 'count': r[1]} for r in cat_stats],
        })

    # ── 询价管理 ──

    @app.route('/admin/inquiries')
    @login_required
    def admin_inquiries():
        status = request.args.get('status', '')
        page = request.args.get('page', 1, type=int)
        query = Inquiry.query
        if status:
            query = query.filter_by(status=status)
        pagination = query.order_by(Inquiry.created_at.desc()).paginate(
            page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
        return render_template('admin/inquiries.html',
                               pagination=pagination,
                               current_status=status)

    @app.route('/admin/inquiry/<int:iid>', methods=['GET', 'POST'])
    @login_required
    def admin_inquiry_detail(iid):
        inquiry = Inquiry.query.get_or_404(iid)
        if request.method == 'POST':
            inquiry.status = request.form.get('status', inquiry.status)
            price_str = request.form.get('quote_price', '')
            inquiry.quote_price = float(price_str) if price_str else None
            inquiry.quote_remark = request.form.get('quote_remark', '')
            db.session.commit()
            flash('询价单已更新', 'success')
            return redirect(url_for('admin_inquiry_detail', iid=iid))
        return render_template('admin/inquiry_detail.html', inquiry=inquiry)

    @app.route('/admin/inquiry/<int:iid>/delete', methods=['POST'])
    @login_required
    def admin_inquiry_delete(iid):
        inquiry = Inquiry.query.get_or_404(iid)
        db.session.delete(inquiry)
        db.session.commit()
        flash('询价单已删除', 'success')
        return redirect(url_for('admin_inquiries'))

    @app.route('/admin/inquiry/export')
    @login_required
    def admin_inquiry_export():
        inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '姓名', '电话', '公司', '产品类型', '数量', '材质', '工艺', '状态', '报价', '提交时间'])
        for inq in inquiries:
            writer.writerow([
                inq.id, inq.name, inq.phone, inq.company or '',
                inq.product_type, inq.quantity, inq.material or '',
                inq.craft or '', inq.status, inq.quote_price or '',
                inq.created_at.strftime('%Y-%m-%d %H:%M') if inq.created_at else '',
            ])
        output.seek(0)
        response = make_response(output.getvalue().encode('utf-8-sig'))
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename=inquiries_{datetime.now().strftime("%Y%m%d")}.csv'
        return response

    # ── 现货产品管理 ──

    @app.route('/admin/products')
    @login_required
    def admin_products():
        category = request.args.get('category', '')
        page = request.args.get('page', 1, type=int)
        query = StockProduct.query
        if category:
            query = query.filter_by(category=category)
        pagination = query.order_by(StockProduct.sort_order, StockProduct.id.desc()).paginate(
            page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
        cats = db.session.query(StockProduct.category).distinct().all()
        categories = [c[0] for c in cats if c[0]]
        return render_template('admin/products.html',
                               pagination=pagination,
                               categories=categories,
                               current_category=category)

    @app.route('/admin/product/add', methods=['GET', 'POST'])
    @login_required
    def admin_product_add():
        if request.method == 'POST':
            product = StockProduct(
                name=request.form.get('name', '').strip(),
                category=request.form.get('category', '').strip(),
                description=request.form.get('description', ''),
                price=float(request.form.get('price', 0)),
                original_price=float(request.form.get('original_price') or 0) or None,
                unit=request.form.get('unit', '个'),
                min_order=int(request.form.get('min_order', 1)),
                sales_count=int(request.form.get('sales_count', 0)),
                is_hot='is_hot' in request.form,
                sort_order=int(request.form.get('sort_order', 0)),
            )
            if 'image' in request.files:
                f = request.files['image']
                if f and f.filename and allowed_file(f.filename, Config.ALLOWED_IMAGE_EXTENSIONS):
                    ext = f.filename.rsplit('.', 1)[1].lower()
                    fname = f'{uuid.uuid4().hex}.{ext}'
                    f.save(os.path.join(Config.UPLOAD_FOLDER, fname))
                    product.image = f'/static/uploads/{fname}'
            db.session.add(product)
            db.session.commit()
            flash('产品已添加', 'success')
            return redirect(url_for('admin_products'))
        return render_template('admin/product_form.html', product=None)

    @app.route('/admin/product/<int:pid>/edit', methods=['GET', 'POST'])
    @login_required
    def admin_product_edit(pid):
        product = StockProduct.query.get_or_404(pid)
        if request.method == 'POST':
            product.name = request.form.get('name', '').strip()
            product.category = request.form.get('category', '').strip()
            product.description = request.form.get('description', '')
            product.price = float(request.form.get('price', 0))
            product.original_price = float(request.form.get('original_price') or 0) or None
            product.unit = request.form.get('unit', '个')
            product.min_order = int(request.form.get('min_order', 1))
            product.sales_count = int(request.form.get('sales_count', 0))
            product.is_hot = 'is_hot' in request.form
            product.sort_order = int(request.form.get('sort_order', 0))
            if 'image' in request.files:
                f = request.files['image']
                if f and f.filename and allowed_file(f.filename, Config.ALLOWED_IMAGE_EXTENSIONS):
                    ext = f.filename.rsplit('.', 1)[1].lower()
                    fname = f'{uuid.uuid4().hex}.{ext}'
                    f.save(os.path.join(Config.UPLOAD_FOLDER, fname))
                    product.image = f'/static/uploads/{fname}'
            db.session.commit()
            flash('产品已更新', 'success')
            return redirect(url_for('admin_products'))
        return render_template('admin/product_form.html', product=product)

    @app.route('/admin/product/<int:pid>/toggle', methods=['POST'])
    @login_required
    def admin_product_toggle(pid):
        product = StockProduct.query.get_or_404(pid)
        product.is_active = not product.is_active
        db.session.commit()
        return jsonify({'ok': True, 'is_active': product.is_active})

    @app.route('/admin/product/<int:pid>/delete', methods=['POST'])
    @login_required
    def admin_product_delete(pid):
        product = StockProduct.query.get_or_404(pid)
        db.session.delete(product)
        db.session.commit()
        flash('产品已删除', 'success')
        return redirect(url_for('admin_products'))

    # ── 盒型管理 ──

    @app.route('/admin/box-types')
    @login_required
    def admin_box_types():
        categories = ProductCategory.query.order_by(ProductCategory.sort_order).all()
        cat_id = request.args.get('category_id', 0, type=int)
        query = BoxType.query
        if cat_id:
            query = query.filter_by(category_id=cat_id)
        box_types = query.order_by(BoxType.sort_order).all()
        return render_template('admin/box_types.html',
                               categories=categories,
                               box_types=box_types,
                               current_cat_id=cat_id)

    @app.route('/admin/box-type/add', methods=['GET', 'POST'])
    @login_required
    def admin_box_type_add():
        if request.method == 'POST':
            bt = BoxType(
                category_id=int(request.form.get('category_id')),
                name=request.form.get('name', '').strip(),
                alias=request.form.get('alias', ''),
                description=request.form.get('description', ''),
                min_quantity=int(request.form.get('min_quantity', 100)),
                sort_order=int(request.form.get('sort_order', 0)),
            )
            db.session.add(bt)
            db.session.commit()
            flash('盒型已添加', 'success')
            return redirect(url_for('admin_box_types'))
        categories = ProductCategory.query.order_by(ProductCategory.sort_order).all()
        return render_template('admin/box_type_form.html', bt=None, categories=categories)

    @app.route('/admin/box-type/<int:btid>/edit', methods=['GET', 'POST'])
    @login_required
    def admin_box_type_edit(btid):
        bt = BoxType.query.get_or_404(btid)
        if request.method == 'POST':
            bt.category_id = int(request.form.get('category_id'))
            bt.name = request.form.get('name', '').strip()
            bt.alias = request.form.get('alias', '')
            bt.description = request.form.get('description', '')
            bt.min_quantity = int(request.form.get('min_quantity', 100))
            bt.sort_order = int(request.form.get('sort_order', 0))
            db.session.commit()
            flash('盒型已更新', 'success')
            return redirect(url_for('admin_box_types'))
        categories = ProductCategory.query.order_by(ProductCategory.sort_order).all()
        return render_template('admin/box_type_form.html', bt=bt, categories=categories)

    @app.route('/admin/box-type/<int:btid>/toggle', methods=['POST'])
    @login_required
    def admin_box_type_toggle(btid):
        bt = BoxType.query.get_or_404(btid)
        bt.is_active = not bt.is_active
        db.session.commit()
        return jsonify({'ok': True, 'is_active': bt.is_active})

    @app.route('/admin/box-type/<int:btid>/delete', methods=['POST'])
    @login_required
    def admin_box_type_delete(btid):
        bt = BoxType.query.get_or_404(btid)
        db.session.delete(bt)
        db.session.commit()
        flash('盒型已删除', 'success')
        return redirect(url_for('admin_box_types'))

    # ── 留言管理 ──

    @app.route('/admin/messages')
    @login_required
    def admin_messages():
        page = request.args.get('page', 1, type=int)
        is_read = request.args.get('read', '')
        query = ContactMessage.query
        if is_read == '0':
            query = query.filter_by(is_read=False)
        elif is_read == '1':
            query = query.filter_by(is_read=True)
        pagination = query.order_by(ContactMessage.created_at.desc()).paginate(
            page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
        return render_template('admin/messages.html', pagination=pagination, current_read=is_read)

    @app.route('/admin/message/<int:mid>/read', methods=['POST'])
    @login_required
    def admin_message_read(mid):
        msg = ContactMessage.query.get_or_404(mid)
        msg.is_read = True
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/admin/message/<int:mid>/delete', methods=['POST'])
    @login_required
    def admin_message_delete(mid):
        msg = ContactMessage.query.get_or_404(mid)
        db.session.delete(msg)
        db.session.commit()
        return jsonify({'ok': True})

    # ── 用户管理（前台用户）──

    @app.route('/admin/front-users')
    @login_required
    def admin_front_users():
        page = request.args.get('page', 1, type=int)
        pagination = FrontUser.query.order_by(FrontUser.created_at.desc()).paginate(
            page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
        return render_template('admin/front_users.html', pagination=pagination)

    # ── 后台用户管理 ──

    @app.route('/admin/users')
    @login_required
    def admin_users():
        users = AdminUser.query.order_by(AdminUser.created_at.desc()).all()
        return render_template('admin/users.html', users=users)

    @app.route('/admin/user/add', methods=['POST'])
    @super_admin_required
    def admin_user_add():
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        real_name = request.form.get('real_name', '').strip()
        role = request.form.get('role', 'staff')

        if not username or not password:
            return jsonify({'ok': False, 'msg': '用户名和密码不能为空'})
        if AdminUser.query.filter_by(username=username).first():
            return jsonify({'ok': False, 'msg': '用户名已存在'})

        user = AdminUser(username=username, real_name=real_name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'ok': True, 'msg': '用户已创建', 'user': user.to_dict()})

    @app.route('/admin/user/<int:uid>/toggle', methods=['POST'])
    @super_admin_required
    def admin_user_toggle(uid):
        user = AdminUser.query.get_or_404(uid)
        if user.id == session.get('admin_uid'):
            return jsonify({'ok': False, 'msg': '不能禁用自己'})
        user.is_active = not user.is_active
        db.session.commit()
        return jsonify({'ok': True, 'is_active': user.is_active})

    @app.route('/admin/user/<int:uid>/reset-password', methods=['POST'])
    @super_admin_required
    def admin_user_reset_password(uid):
        user = AdminUser.query.get_or_404(uid)
        new_password = request.form.get('new_password', '').strip()
        if not new_password or len(new_password) < 6:
            return jsonify({'ok': False, 'msg': '密码至少6位'})
        user.set_password(new_password)
        db.session.commit()
        return jsonify({'ok': True, 'msg': '密码已重置'})

    @app.route('/admin/user/<int:uid>/delete', methods=['POST'])
    @super_admin_required
    def admin_user_delete(uid):
        user = AdminUser.query.get_or_404(uid)
        if user.id == session.get('admin_uid'):
            return jsonify({'ok': False, 'msg': '不能删除自己'})
        db.session.delete(user)
        db.session.commit()
        return jsonify({'ok': True, 'msg': '用户已删除'})

    # ── 轮播图管理 ──

    @app.route('/admin/banners')
    @login_required
    def admin_banners():
        banners = Banner.query.order_by(Banner.sort_order).all()
        return render_template('admin/banners.html', banners=banners)

    @app.route('/admin/banner/add', methods=['POST'])
    @login_required
    def admin_banner_add():
        banner = Banner(
            title=request.form.get('title', ''),
            link=request.form.get('link', ''),
            description=request.form.get('description', ''),
            sort_order=int(request.form.get('sort_order', 0)),
        )
        if 'image' in request.files:
            f = request.files['image']
            if f and f.filename and allowed_file(f.filename, Config.ALLOWED_IMAGE_EXTENSIONS):
                ext = f.filename.rsplit('.', 1)[1].lower()
                fname = f'{uuid.uuid4().hex}.{ext}'
                f.save(os.path.join(Config.UPLOAD_FOLDER, fname))
                banner.image = f'/static/uploads/{fname}'
        db.session.add(banner)
        db.session.commit()
        flash('轮播图已添加', 'success')
        return redirect(url_for('admin_banners'))

    @app.route('/admin/banner/<int:bid>/edit', methods=['POST'])
    @login_required
    def admin_banner_edit(bid):
        banner = Banner.query.get_or_404(bid)
        banner.title = request.form.get('title', '')
        banner.link = request.form.get('link', '')
        banner.description = request.form.get('description', '')
        banner.sort_order = int(request.form.get('sort_order', 0))
        if 'image' in request.files:
            f = request.files['image']
            if f and f.filename and allowed_file(f.filename, Config.ALLOWED_IMAGE_EXTENSIONS):
                ext = f.filename.rsplit('.', 1)[1].lower()
                fname = f'{uuid.uuid4().hex}.{ext}'
                f.save(os.path.join(Config.UPLOAD_FOLDER, fname))
                banner.image = f'/static/uploads/{fname}'
        db.session.commit()
        flash('轮播图已更新', 'success')
        return redirect(url_for('admin_banners'))

    @app.route('/admin/banner/<int:bid>/toggle', methods=['POST'])
    @login_required
    def admin_banner_toggle(bid):
        banner = Banner.query.get_or_404(bid)
        banner.is_active = not banner.is_active
        db.session.commit()
        return jsonify({'ok': True, 'is_active': banner.is_active})

    @app.route('/admin/banner/<int:bid>/delete', methods=['POST'])
    @login_required
    def admin_banner_delete(bid):
        banner = Banner.query.get_or_404(bid)
        db.session.delete(banner)
        db.session.commit()
        flash('轮播图已删除', 'success')
        return redirect(url_for('admin_banners'))

    # ── 分类管理 ──

    @app.route('/admin/categories')
    @login_required
    def admin_categories():
        categories = ProductCategory.query.order_by(ProductCategory.sort_order).all()
        return render_template('admin/categories.html', categories=categories)

    @app.route('/admin/category/add', methods=['POST'])
    @login_required
    def admin_category_add():
        cat = ProductCategory(
            name=request.form.get('name', '').strip(),
            icon=request.form.get('icon', ''),
            description=request.form.get('description', ''),
            sort_order=int(request.form.get('sort_order', 0)),
        )
        db.session.add(cat)
        db.session.commit()
        flash('分类已添加', 'success')
        return redirect(url_for('admin_categories'))

    @app.route('/admin/category/<int:cid>/edit', methods=['POST'])
    @login_required
    def admin_category_edit(cid):
        cat = ProductCategory.query.get_or_404(cid)
        cat.name = request.form.get('name', '').strip()
        cat.icon = request.form.get('icon', '')
        cat.description = request.form.get('description', '')
        cat.sort_order = int(request.form.get('sort_order', 0))
        db.session.commit()
        flash('分类已更新', 'success')
        return redirect(url_for('admin_categories'))

    @app.route('/admin/category/<int:cid>/delete', methods=['POST'])
    @login_required
    def admin_category_delete(cid):
        cat = ProductCategory.query.get_or_404(cid)
        db.session.delete(cat)
        db.session.commit()
        flash('分类已删除', 'success')
        return redirect(url_for('admin_categories'))

    # ── 文章管理 ──

    @app.route('/admin/articles')
    @login_required
    def admin_articles():
        page = request.args.get('page', 1, type=int)
        category = request.args.get('category', '')
        query = Article.query
        if category:
            query = query.filter_by(category=category)
        pagination = query.order_by(Article.created_at.desc()).paginate(
            page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
        cats = db.session.query(Article.category).distinct().all()
        categories = [c[0] for c in cats if c[0]]
        return render_template('admin/articles.html',
                               pagination=pagination,
                               categories=categories,
                               current_category=category)

    @app.route('/admin/article/add', methods=['GET', 'POST'])
    @login_required
    def admin_article_add():
        if request.method == 'POST':
            article = Article(
                title=request.form.get('title', '').strip(),
                category=request.form.get('category', ''),
                summary=request.form.get('summary', ''),
                content=request.form.get('content', ''),
                is_active='is_active' in request.form,
                sort_order=int(request.form.get('sort_order', 0)),
            )
            db.session.add(article)
            db.session.commit()
            flash('文章已发布', 'success')
            return redirect(url_for('admin_articles'))
        return render_template('admin/article_form.html', article=None)

    @app.route('/admin/article/<int:aid>/edit', methods=['GET', 'POST'])
    @login_required
    def admin_article_edit(aid):
        article = Article.query.get_or_404(aid)
        if request.method == 'POST':
            article.title = request.form.get('title', '').strip()
            article.category = request.form.get('category', '')
            article.summary = request.form.get('summary', '')
            article.content = request.form.get('content', '')
            article.is_active = 'is_active' in request.form
            article.sort_order = int(request.form.get('sort_order', 0))
            db.session.commit()
            flash('文章已更新', 'success')
            return redirect(url_for('admin_articles'))
        return render_template('admin/article_form.html', article=article)

    @app.route('/admin/article/<int:aid>/delete', methods=['POST'])
    @login_required
    def admin_article_delete(aid):
        article = Article.query.get_or_404(aid)
        db.session.delete(article)
        db.session.commit()
        flash('文章已删除', 'success')
        return redirect(url_for('admin_articles'))

    # ── 网站配置管理 ──

    @app.route('/admin/site-config', methods=['GET', 'POST'])
    @super_admin_required
    def admin_site_config():
        if request.method == 'POST':
            # 文本配置项
            config_keys = [
                'site_name', 'site_phone', 'site_phone_check', 'site_phone_complaint',
                'site_wechat', 'site_email', 'site_address', 'site_icp',
                'site_qq1', 'site_qq2', 'site_qq3',
                'stat_experience', 'stat_clients', 'stat_projects', 'stat_satisfaction',
                'seo_title', 'seo_description', 'seo_keywords',
                'business_hours', 'site_description',
            ]
            for key in config_keys:
                value = request.form.get(key, '')
                cfg = SiteConfig.query.filter_by(key=key).first()
                if cfg:
                    cfg.value = value
                else:
                    db.session.add(SiteConfig(key=key, value=value))

            # 图片上传（Logo）
            for img_key in ['site_logo', 'site_favicon', 'site_qrcode_wechat', 'site_about_image1', 'site_about_image2']:
                if img_key in request.files:
                    f = request.files[img_key]
                    if f and f.filename and allowed_file(f.filename, Config.ALLOWED_IMAGE_EXTENSIONS):
                        ext = f.filename.rsplit('.', 1)[1].lower()
                        fname = f'{img_key}_{uuid.uuid4().hex}.{ext}'
                        f.save(os.path.join(Config.UPLOAD_FOLDER, fname))
                        img_path = f'/static/uploads/{fname}'
                        cfg = SiteConfig.query.filter_by(key=img_key).first()
                        if cfg:
                            cfg.value = img_path
                        else:
                            db.session.add(SiteConfig(key=img_key, value=img_path))

            db.session.commit()
            flash('网站配置已保存', 'success')
            return redirect(url_for('admin_site_config'))

        configs = {c.key: c.value for c in SiteConfig.query.all()}
        return render_template('admin/site_config.html', configs=configs)

    # ── 优惠券管理 ──

    @app.route('/admin/coupons')
    @login_required
    def admin_coupons():
        coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
        return render_template('admin/coupons.html', coupons=coupons)

    @app.route('/admin/coupon/add', methods=['POST'])
    @login_required
    def admin_coupon_add():
        from datetime import datetime as dt
        valid_until_str = request.form.get('valid_until', '')
        valid_until = dt.strptime(valid_until_str, '%Y-%m-%d') if valid_until_str else None

        coupon = Coupon(
            code=request.form.get('code', '').strip().upper(),
            name=request.form.get('name', ''),
            discount_type=request.form.get('discount_type', 'fixed'),
            discount_value=float(request.form.get('discount_value', 0)),
            min_order=float(request.form.get('min_order', 0)),
            total_count=int(request.form.get('total_count', 0)),
            valid_until=valid_until,
        )
        db.session.add(coupon)
        db.session.commit()
        flash('优惠券已添加', 'success')
        return redirect(url_for('admin_coupons'))

    @app.route('/admin/coupon/<int:cid>/toggle', methods=['POST'])
    @login_required
    def admin_coupon_toggle(cid):
        coupon = Coupon.query.get_or_404(cid)
        coupon.is_active = not coupon.is_active
        db.session.commit()
        return jsonify({'ok': True, 'is_active': coupon.is_active})

    @app.route('/admin/coupon/<int:cid>/delete', methods=['POST'])
    @login_required
    def admin_coupon_delete(cid):
        coupon = Coupon.query.get_or_404(cid)
        db.session.delete(coupon)
        db.session.commit()
        flash('优惠券已删除', 'success')
        return redirect(url_for('admin_coupons'))

    # ── 订单管理 ──

    @app.route('/admin/orders')
    @login_required
    def admin_orders():
        status = request.args.get('status', '')
        page = request.args.get('page', 1, type=int)
        query = Order.query
        if status:
            query = query.filter_by(status=status)
        pagination = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
        return render_template('admin/orders.html',
                               pagination=pagination, current_status=status)

    @app.route('/admin/order/<int:oid>', methods=['GET', 'POST'])
    @login_required
    def admin_order_detail(oid):
        order = Order.query.get_or_404(oid)
        if request.method == 'POST':
            order.status = request.form.get('status', order.status)
            order.tracking_no = request.form.get('tracking_no', '')
            order.remark = request.form.get('remark', '')
            db.session.commit()
            flash('订单已更新', 'success')
        return render_template('admin/order_detail.html', order=order)

    # ── 报价规则管理 ──

    @app.route('/admin/quotation-rules')
    @login_required
    def admin_quotation_rules():
        box_type_id = request.args.get('box_type_id', 0, type=int)
        query = QuotationRule.query
        if box_type_id:
            query = query.filter_by(box_type_id=box_type_id)
        rules = query.order_by(QuotationRule.id).all()
        box_types = BoxType.query.order_by(BoxType.sort_order).all()
        return render_template('admin/quotation_rules.html',
                               rules=rules,
                               box_types=box_types,
                               current_box_type_id=box_type_id)

    @app.route('/admin/quotation-rule/add', methods=['GET', 'POST'])
    @login_required
    def admin_quotation_rule_add():
        if request.method == 'POST':
            box_type_id = int(request.form.get('box_type_id'))
            material = request.form.get('material', '通用').strip()
            base_price = float(request.form.get('base_price', 0))
            unit_price = float(request.form.get('unit_price', 0))
            min_quantity = int(request.form.get('min_quantity', 100))
            remark = request.form.get('remark', '').strip()

            # 解析阶梯价格
            ranges = []
            range_count = int(request.form.get('range_count', 0))
            for i in range(range_count):
                r_min = int(request.form.get(f'range_{i}_min', 0))
                r_max = int(request.form.get(f'range_{i}_max', 0))
                r_price = float(request.form.get(f'range_{i}_price', 0))
                if r_min > 0 and r_price > 0:
                    ranges.append({'min': r_min, 'max': r_max, 'unit_price': r_price})

            rule = QuotationRule(
                box_type_id=box_type_id,
                material=material or '通用',
                base_price=base_price,
                unit_price=unit_price,
                min_quantity=min_quantity,
                range_config=json.dumps(ranges, ensure_ascii=False),
                remark=remark,
            )
            db.session.add(rule)
            db.session.commit()
            flash('报价规则已添加', 'success')
            return redirect(url_for('admin_quotation_rules'))

        box_types = BoxType.query.order_by(BoxType.sort_order).all()
        return render_template('admin/quotation_rule_form.html', rule=None, box_types=box_types)

    @app.route('/admin/quotation-rule/<int:rid>/edit', methods=['GET', 'POST'])
    @login_required
    def admin_quotation_rule_edit(rid):
        rule = QuotationRule.query.get_or_404(rid)
        if request.method == 'POST':
            rule.box_type_id = int(request.form.get('box_type_id'))
            rule.material = request.form.get('material', '通用').strip() or '通用'
            rule.base_price = float(request.form.get('base_price', 0))
            rule.unit_price = float(request.form.get('unit_price', 0))
            rule.min_quantity = int(request.form.get('min_quantity', 100))
            rule.remark = request.form.get('remark', '').strip()

            # 解析阶梯价格
            ranges = []
            range_count = int(request.form.get('range_count', 0))
            for i in range(range_count):
                r_min = int(request.form.get(f'range_{i}_min', 0))
                r_max = int(request.form.get(f'range_{i}_max', 0))
                r_price = float(request.form.get(f'range_{i}_price', 0))
                if r_min > 0 and r_price > 0:
                    ranges.append({'min': r_min, 'max': r_max, 'unit_price': r_price})

            rule.range_config = json.dumps(ranges, ensure_ascii=False)
            db.session.commit()
            flash('报价规则已更新', 'success')
            return redirect(url_for('admin_quotation_rules'))

        box_types = BoxType.query.order_by(BoxType.sort_order).all()
        return render_template('admin/quotation_rule_form.html', rule=rule, box_types=box_types)

    @app.route('/admin/quotation-rule/<int:rid>/toggle', methods=['POST'])
    @login_required
    def admin_quotation_rule_toggle(rid):
        rule = QuotationRule.query.get_or_404(rid)
        rule.is_active = not rule.is_active
        db.session.commit()
        return jsonify({'ok': True, 'is_active': rule.is_active})

    @app.route('/admin/quotation-rule/<int:rid>/delete', methods=['POST'])
    @login_required
    def admin_quotation_rule_delete(rid):
        rule = QuotationRule.query.get_or_404(rid)
        db.session.delete(rule)
        db.session.commit()
        flash('报价规则已删除', 'success')
        return redirect(url_for('admin_quotation_rules'))

    # ── FAQ管理 ──

    @app.route('/admin/faqs')
    @login_required
    def admin_faqs():
        faqs = FAQ.query.order_by(FAQ.sort_order).all()
        return render_template('admin/faqs.html', faqs=faqs)

    @app.route('/admin/faq/add', methods=['POST'])
    @login_required
    def admin_faq_add():
        faq = FAQ(
            question=request.form.get('question', '').strip(),
            answer=request.form.get('answer', '').strip(),
            category=request.form.get('category', '常见问题'),
            sort_order=int(request.form.get('sort_order', 0)),
            is_active=True,
        )
        db.session.add(faq)
        db.session.commit()
        flash('FAQ已添加', 'success')
        return redirect(url_for('admin_faqs'))

    @app.route('/admin/faq/<int:fid>/edit', methods=['POST'])
    @login_required
    def admin_faq_edit(fid):
        faq = FAQ.query.get_or_404(fid)
        faq.question = request.form.get('question', '').strip()
        faq.answer = request.form.get('answer', '').strip()
        faq.category = request.form.get('category', '常见问题')
        faq.sort_order = int(request.form.get('sort_order', 0))
        db.session.commit()
        flash('FAQ已更新', 'success')
        return redirect(url_for('admin_faqs'))

    @app.route('/admin/faq/<int:fid>/toggle', methods=['POST'])
    @login_required
    def admin_faq_toggle(fid):
        faq = FAQ.query.get_or_404(fid)
        faq.is_active = not faq.is_active
        db.session.commit()
        return jsonify({'ok': True, 'is_active': faq.is_active})

    @app.route('/admin/faq/<int:fid>/delete', methods=['POST'])
    @login_required
    def admin_faq_delete(fid):
        faq = FAQ.query.get_or_404(fid)
        db.session.delete(faq)
        db.session.commit()
        flash('FAQ已删除', 'success')
        return redirect(url_for('admin_faqs'))


# ============================================================
# 入口
# ============================================================

if __name__ == '__main__':
    app = create_app()
    init_default_data(app)
    app.run(debug=False, host='0.0.0.0', port=5000)
