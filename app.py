# -*- coding: utf-8 -*-
"""
印刷公司官网 - Flask 主应用
"""

import os
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, flash, session
)
from werkzeug.utils import secure_filename

from config import Config
from models import db, Inquiry, Product, ContactMessage, SiteConfig, User


def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static',
                static_url_path='/static')
    app.config.from_object(Config)

    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 初始化数据库
    db.init_app(app)

    # 创建所有表 + 初始化默认数据
    with app.app_context():
        db.create_all()
        _init_default_data()

    # ========== 路由 ==========

    # --- 前台页面 ---
    @app.route('/')
    def index():
        products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).all()
        return render_template('index.html', products=products, config=_get_site_config())

    @app.route('/product/<int:pid>')
    def product_detail(pid):
        product = Product.query.get_or_404(pid)
        return render_template('product_detail.html', product=product)

    # --- API: 提交询价 ---
    @app.route('/api/inquiry', methods=['POST'])
    def submit_inquiry():
        try:
            data = request.get_json() or request.form

            inquiry = Inquiry(
                name=data.get('name', '').strip(),
                phone=data.get('phone', '').strip(),
                company=data.get('company', '').strip(),
                product_type=data.get('product_type', '').strip(),
                length=float(data['length']) if data.get('length') else None,
                width=float(data['width']) if data.get('width') else None,
                height=float(data['height']) if data.get('height') else None,
                quantity=int(data.get('quantity', 0)),
                material=data.get('material', '').strip(),
                craft=data.get('craft', '').strip(),
                remark=data.get('remark', '').strip(),
            )

            # 文件上传
            if 'file' in request.files:
                f = request.files['file']
                if f and f.filename:
                    fname = secure_filename(f.filename)
                    # 加时间戳防重名
                    import time
                    ext = os.path.splitext(fname)[1]
                    fname = f"{int(time.time())}{ext}"
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                    inquiry.file_name = fname

            if not inquiry.name or not inquiry.phone or not inquiry.product_type:
                return jsonify({'success': False, 'message': '请填写姓名、电话和产品类型'}), 400

            if inquiry.quantity <= 0:
                return jsonify({'success': False, 'message': '请填写有效的数量'}), 400

            db.session.add(inquiry)
            db.session.commit()

            return jsonify({'success': True, 'message': '询价提交成功！我们会尽快联系您。', 'id': inquiry.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'提交失败: {str(e)}'}), 500

    # --- API: 获取产品列表 ---
    @app.route('/api/products')
    def get_products():
        category = request.args.get('category', '')
        query = Product.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        products = query.order_by(Product.sort_order).all()
        return jsonify([p.to_dict() for p in products])

    # --- API: 获取产品分类 ---
    @app.route('/api/product-categories')
    def get_categories():
        categories = db.session.query(Product.category).filter_by(is_active=True).distinct().all()
        return jsonify([c[0] for c in categories])

    # --- API: 提交留言 ---
    @app.route('/api/contact', methods=['POST'])
    def submit_contact():
        try:
            data = request.get_json() or {}
            msg = ContactMessage(
                name=data.get('name', '').strip(),
                phone=data.get('phone', '').strip(),
                email=data.get('email', '').strip(),
                message=data.get('message', '').strip(),
            )
            if not msg.name or not msg.phone or not msg.message:
                return jsonify({'success': False, 'message': '请填写姓名、电话和留言内容'}), 400
            db.session.add(msg)
            db.session.commit()
            return jsonify({'success': True, 'message': '留言已提交！'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'提交失败: {str(e)}'}), 500

    # --- API: 简易报价估算 ---
    @app.route('/api/estimate-price', methods=['POST'])
    def estimate_price():
        """根据产品类型和数量返回估算价格区间"""
        data = request.get_json() or {}
        product_type = data.get('product_type', '')
        quantity = int(data.get('quantity', 0))

        # 基础报价规则 (可根据实际业务调整)
        price_rules = {
            '名片': {'base': 50, 'unit': 0.05, 'min_order': 100},
            '画册': {'base': 200, 'unit': 2.5, 'min_order': 50},
            '彩页': {'base': 80, 'unit': 0.15, 'min_order': 200},
            '海报': {'base': 100, 'unit': 0.3, 'min_order': 50},
            '手提袋': {'base': 300, 'unit': 1.5, 'min_order': 100},
            '纸盒': {'base': 500, 'unit': 3.0, 'min_order': 50},
            '不干胶': {'base': 60, 'unit': 0.08, 'min_order': 500},
            '吊牌': {'base': 80, 'unit': 0.1, 'min_order': 200},
        }

        rule = price_rules.get(product_type)
        if not rule:
            return jsonify({'success': False, 'message': '暂不支持该产品的在线估价'})

        if quantity < rule['min_order']:
            return jsonify({
                'success': True,
                'min_order': rule['min_order'],
                'message': f'{product_type}最小起订量为{rule["min_order"]}',
                'low': None, 'high': None,
            })

        estimated = rule['base'] + quantity * rule['unit']
        low = round(estimated * 0.85, 2)
        high = round(estimated * 1.15, 2)

        return jsonify({
            'success': True,
            'low': low,
            'high': high,
            'message': f'预估价格: ¥{low} ~ ¥{high}（最终价格以实际报价为准）',
        })

    # ========== 后台管理 ==========

    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('is_admin'):
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            user = User.query.filter_by(username=username, is_active=True).first()
            if user and user.check_password(password):
                session['is_admin'] = True
                session['admin_user'] = user.real_name or user.username
                session['admin_role'] = user.role
                session['admin_uid'] = user.id
                user.last_login = datetime.now()
                db.session.commit()
                return redirect(url_for('admin_dashboard'))
            flash('用户名或密码错误')
        return render_template('admin/login.html')

    @app.route('/admin/logout')
    def admin_logout():
        session.clear()
        return redirect(url_for('admin_login'))

    @app.route('/admin')
    @login_required
    def admin_dashboard():
        stats = {
            'total_inquiries': Inquiry.query.count(),
            'pending': Inquiry.query.filter_by(status='待处理').count(),
            'quoted': Inquiry.query.filter_by(status='已报价').count(),
            'completed': Inquiry.query.filter_by(status='已成交').count(),
            'total_messages': ContactMessage.query.count(),
            'unread_messages': ContactMessage.query.filter_by(is_read=False).count(),
            'total_products': Product.query.count(),
            'active_products': Product.query.filter_by(is_active=True).count(),
        }
        recent_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(5).all()
        return render_template('admin/dashboard.html', stats=stats, recent_inquiries=recent_inquiries)

    # --- 询价管理 ---
    @app.route('/admin/inquiries')
    @login_required
    def admin_inquiries():
        status_filter = request.args.get('status', '')
        page = request.args.get('page', 1, type=int)
        per_page = 15
        query = Inquiry.query
        if status_filter:
            query = query.filter_by(status=status_filter)
        pagination = query.order_by(Inquiry.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        return render_template('admin/inquiries.html',
                               inquiries=pagination.items,
                               pagination=pagination,
                               status_filter=status_filter)

    @app.route('/admin/inquiry/<int:iid>', methods=['GET'])
    @login_required
    def admin_inquiry_detail(iid):
        inquiry = Inquiry.query.get_or_404(iid)
        return render_template('admin/inquiry_detail.html', inquiry=inquiry)

    @app.route('/admin/inquiry/<int:iid>', methods=['POST'])
    @login_required
    def admin_update_inquiry(iid):
        inquiry = Inquiry.query.get_or_404(iid)
        inquiry.status = request.form.get('status', inquiry.status)
        inquiry.quote_price = float(request.form['quote_price']) if request.form.get('quote_price') else None
        inquiry.quote_remark = request.form.get('quote_remark', '')
        db.session.commit()
        flash('询价信息已更新')
        return redirect(url_for('admin_inquiry_detail', iid=iid))

    @app.route('/admin/inquiry/<int:iid>/delete', methods=['POST'])
    @login_required
    def admin_delete_inquiry(iid):
        inquiry = Inquiry.query.get_or_404(iid)
        db.session.delete(inquiry)
        db.session.commit()
        flash('询价记录已删除')
        return redirect(url_for('admin_inquiries'))

    @app.route('/admin/inquiry/export')
    @login_required
    def admin_export_inquiries():
        """导出询价数据为 CSV"""
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '姓名', '电话', '公司', '产品类型', '长(mm)', '宽(mm)', '高(mm)',
                         '数量', '材质', '工艺', '备注', '状态', '报价', '报价备注', '提交时间'])

        for i in Inquiry.query.order_by(Inquiry.created_at.desc()).all():
            writer.writerow([
                i.id, i.name, i.phone, i.company, i.product_type,
                i.length, i.width, i.height, i.quantity,
                i.material, i.craft, i.remark, i.status,
                i.quote_price or '', i.quote_remark or '',
                i.created_at.strftime('%Y-%m-%d %H:%M') if i.created_at else '',
            ])

        from flask import Response
        buf = io.BytesIO()
        buf.write(output.getvalue().encode('utf-8-sig'))
        buf.seek(0)
        return Response(buf.read(), mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=inquiries.csv'})

    # --- 产品管理 ---
    @app.route('/admin/products')
    @login_required
    def admin_products():
        products = Product.query.order_by(Product.sort_order).all()
        return render_template('admin/products.html', products=products)

    @app.route('/admin/product/add', methods=['GET', 'POST'])
    @login_required
    def admin_add_product():
        if request.method == 'POST':
            product = Product(
                name=request.form['name'],
                category=request.form['category'],
                description=request.form.get('description', ''),
                min_price=float(request.form['min_price']) if request.form.get('min_price') else None,
                unit=request.form.get('unit', '个'),
                sort_order=int(request.form.get('sort_order', 0)),
                is_active=True,
            )
            if 'image' in request.files:
                f = request.files['image']
                if f and f.filename:
                    import time
                    ext = os.path.splitext(secure_filename(f.filename))[1]
                    fname = f"product_{int(time.time())}{ext}"
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                    product.image = f'/static/uploads/{fname}'
            db.session.add(product)
            db.session.commit()
            flash('产品添加成功')
            return redirect(url_for('admin_products'))
        return render_template('admin/product_form.html', product=None)

    @app.route('/admin/product/<int:pid>/edit', methods=['GET', 'POST'])
    @login_required
    def admin_edit_product(pid):
        product = Product.query.get_or_404(pid)
        if request.method == 'POST':
            product.name = request.form['name']
            product.category = request.form['category']
            product.description = request.form.get('description', '')
            product.min_price = float(request.form['min_price']) if request.form.get('min_price') else None
            product.unit = request.form.get('unit', '个')
            product.sort_order = int(request.form.get('sort_order', 0))
            if 'image' in request.files:
                f = request.files['image']
                if f and f.filename:
                    import time
                    ext = os.path.splitext(secure_filename(f.filename))[1]
                    fname = f"product_{int(time.time())}{ext}"
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                    product.image = f'/static/uploads/{fname}'
            db.session.commit()
            flash('产品更新成功')
            return redirect(url_for('admin_products'))
        return render_template('admin/product_form.html', product=product)

    @app.route('/admin/product/<int:pid>/toggle', methods=['POST'])
    @login_required
    def admin_toggle_product(pid):
        product = Product.query.get_or_404(pid)
        product.is_active = not product.is_active
        db.session.commit()
        return jsonify({'success': True, 'is_active': product.is_active})

    @app.route('/admin/product/<int:pid>/delete', methods=['POST'])
    @login_required
    def admin_delete_product(pid):
        product = Product.query.get_or_404(pid)
        db.session.delete(product)
        db.session.commit()
        flash('产品已删除')
        return redirect(url_for('admin_products'))

    # --- 留言管理 ---
    @app.route('/admin/messages')
    @login_required
    def admin_messages():
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        return render_template('admin/messages.html', messages=messages)

    @app.route('/admin/message/<int:mid>/read', methods=['POST'])
    @login_required
    def admin_mark_read(mid):
        msg = ContactMessage.query.get_or_404(mid)
        msg.is_read = True
        db.session.commit()
        return jsonify({'success': True})

    @app.route('/admin/message/<int:mid>/delete', methods=['POST'])
    @login_required
    def admin_delete_message(mid):
        msg = ContactMessage.query.get_or_404(mid)
        db.session.delete(msg)
        db.session.commit()
        return jsonify({'success': True})

    # --- 用户管理 ---
    def super_admin_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('admin_role') != 'super_admin':
                flash('仅超级管理员可执行此操作')
                return redirect(url_for('admin_dashboard'))
            return f(*args, **kwargs)
        return decorated

    @app.route('/admin/users')
    @login_required
    def admin_users():
        users = User.query.order_by(User.created_at).all()
        return render_template('admin/users.html', users=users)

    @app.route('/admin/user/add', methods=['POST'])
    @login_required
    @super_admin_required
    def admin_add_user():
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        real_name = request.form.get('real_name', '').strip()
        role = request.form.get('role', 'staff')

        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        if len(password) < 4:
            return jsonify({'success': False, 'message': '密码至少4位'}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400

        user = User(username=username, real_name=real_name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'message': f'用户 {username} 创建成功'})

    @app.route('/admin/user/<int:uid>/toggle', methods=['POST'])
    @login_required
    @super_admin_required
    def admin_toggle_user(uid):
        if uid == session.get('admin_uid'):
            return jsonify({'success': False, 'message': '不能禁用自己的账号'}), 400
        user = User.query.get_or_404(uid)
        if user.role == 'super_admin':
            return jsonify({'success': False, 'message': '不能禁用超级管理员'}), 400
        user.is_active = not user.is_active
        db.session.commit()
        return jsonify({'success': True, 'is_active': user.is_active})

    @app.route('/admin/user/<int:uid>/reset-password', methods=['POST'])
    @login_required
    @super_admin_required
    def admin_reset_password(uid):
        new_pwd = request.form.get('new_password', '').strip()
        if len(new_pwd) < 4:
            return jsonify({'success': False, 'message': '新密码至少4位'}), 400
        user = User.query.get_or_404(uid)
        user.set_password(new_pwd)
        db.session.commit()
        return jsonify({'success': True, 'message': f'用户 {user.username} 密码已重置'})

    @app.route('/admin/user/<int:uid>/delete', methods=['POST'])
    @login_required
    @super_admin_required
    def admin_delete_user(uid):
        if uid == session.get('admin_uid'):
            return jsonify({'success': False, 'message': '不能删除自己的账号'}), 400
        user = User.query.get_or_404(uid)
        if user.role == 'super_admin':
            return jsonify({'success': False, 'message': '不能删除超级管理员'}), 400
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': f'用户 {user.username} 已删除'})

    # --- 统计图表数据 ---
    @app.route('/admin/api/stats')
    @login_required
    def admin_stats_api():
        """返回仪表盘需要的统计数据"""
        from sqlalchemy import func
        # 近7天询价趋势
        from datetime import timedelta
        trend = []
        for i in range(6, -1, -1):
            day = (datetime.now() - timedelta(days=i)).strftime('%m-%d')
            count = Inquiry.query.filter(
                func.date(Inquiry.created_at) == (datetime.now().date() - timedelta(days=i))
            ).count()
            trend.append({'date': day, 'count': count})

        # 产品类型分布
        type_dist = db.session.query(
            Inquiry.product_type, func.count(Inquiry.id)
        ).group_by(Inquiry.product_type).all()

        return jsonify({
            'trend': trend,
            'type_dist': [{'name': t, 'count': c} for t, c in type_dist],
        })

    return app


def _init_default_data():
    """初始化默认产品数据和默认管理员"""
    # 初始化默认超级管理员
    if User.query.filter_by(role='super_admin').count() == 0:
        admin = User(username='admin', real_name='超级管理员', role='super_admin')
        admin.set_password('admin888')
        db.session.add(admin)
        db.session.commit()
        print('✅ 默认管理员已创建 (admin / admin888)')

    # 初始化默认产品数据
    if Product.query.count() == 0:
        defaults = [
            ('名片印刷', '名片', '高品质名片，多种材质工艺可选，支持UV、烫金、击凸等特殊工艺', 50, '盒', 1),
            ('画册印刷', '画册', '企业画册、产品手册、宣传册，从设计到印刷一站式服务', 200, '本', 2),
            ('彩页传单', '彩页', 'A4/A5彩页、折页、传单，色彩鲜艳，印刷精美', 80, '张', 3),
            ('海报印刷', '海报', '大型海报、展会海报、宣传海报，支持各种尺寸', 100, '张', 4),
            ('手提袋定制', '手提袋', '纸质手提袋、无纺布袋，提升品牌形象', 300, '个', 5),
            ('纸盒包装', '纸盒', '产品包装盒、礼品盒、月饼盒等定制包装', 500, '个', 6),
            ('不干胶标签', '不干胶', '各种材质不干胶标签，食品标签、物流标签等', 60, '张', 7),
            ('吊牌卡片', '吊牌', '服装吊牌、贺卡、邀请函等精品印刷', 80, '张', 8),
        ]
        for name, cat, desc, price, unit, sort in defaults:
            db.session.add(Product(
                name=name, category=cat, description=desc,
                min_price=price, unit=unit, sort_order=sort
            ))
        db.session.commit()
        print('✅ 默认产品数据已初始化')


def _get_site_config():
    """获取网站配置"""
    configs = SiteConfig.query.all()
    cfg = {}
    for c in configs:
        cfg[c.key] = c.value
    return cfg


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
