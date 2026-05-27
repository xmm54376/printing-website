# 精彩印刷官网 - 全栈版部署上线指南

> Flask + SQLite 全栈版本，包含在线询价数据库存储、管理后台、产品管理等功能。

---

## 技术架构

| 组件 | 技术 |
|------|------|
| 后端 | Python Flask 3.x |
| 数据库 | SQLite（轻量，无需单独安装） |
| ORM | Flask-SQLAlchemy |
| 前端 | 原生 HTML/CSS/JS（零框架依赖） |
| 管理后台 | Jinja2 模板 |

---

## 项目结构

```
printing-website/
├── app.py              # Flask 主应用（路由 + API + 后台）
├── config.py           # 配置文件（账号密码、网站信息）
├── models.py           # 数据库模型（询价、产品、留言）
├── requirements.txt    # Python 依赖
├── .gitignore          # Git 忽略规则
├── printing.db         # SQLite 数据库（自动生成）
├── templates/          # HTML 模板
│   ├── index.html      # 前台官网（对接后端 API）
│   └── admin/          # 管理后台
│       ├── login.html          # 登录页
│       ├── dashboard.html      # 工作台仪表盘
│       ├── inquiries.html      # 询价管理列表
│       ├── inquiry_detail.html # 询价详情/报价
│       ├── products.html       # 产品管理
│       ├── product_form.html   # 产品添加/编辑
│       └── messages.html       # 留言管理
└── static/             # 静态资源
    ├── css/styles.css  # 全站样式
    ├── js/main.js      # 交互逻辑（含 API 调用）
    ├── images/         # 图片目录
    └── uploads/        # 用户上传文件（自动生成）
```

---

## 本地运行（开发环境）

```bash
# 1. 确保 Python 3.10+ 已安装
python --version

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 启动服务器
python app.py

# 6. 访问
# 前台官网: http://127.0.0.1:5000/
# 管理后台: http://127.0.0.1:5000/admin/login
```

### 默认管理账号
- 用户名: `admin`
- 密码: `admin888`

> ⚠️ 上线前请修改 `config.py` 中的 `SECRET_KEY` 和管理员密码！

---

## 服务器部署（生产环境）

### 方案一：Gunicorn + Nginx（推荐，Linux）

```bash
# 1. 上传代码到服务器
git clone https://github.com/xmm54376/printing-website.git
cd printing-website

# 2. 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 3. 测试运行
gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"

# 4. 配置 Nginx（/etc/nginx/sites-available/printing）
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/printing-website/static/;
        expires 30d;
    }
}

# 5. 启动
sudo ln -s /etc/nginx/sites-available/printing /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 6. 使用 systemd 守护进程（/etc/systemd/system/printing.service）
[Unit]
Description=Printing Website
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/printing-website
ExecStart=/path/to/printing-website/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target

sudo systemctl enable printing
sudo systemctl start printing
```

### 方案二：宝塔面板部署（最简单）

1. 宝塔面板 → Python项目管理器 → 添加项目
2. 项目路径选择代码目录
3. Python版本选 3.10+
4. 启动文件填 `app.py`
5. 框架选 Flask，启动命令自动生成
6. 点击启动，配置域名即可

### 方案三：Vercel/Railway（云平台免费部署）

```bash
# 1. 安装 Vercel CLI
npm i -g vercel

# 2. 创建 vercel.json
cat > vercel.json << 'EOF'
{
  "version": 2,
  "builds": [
    { "src": "app.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/static/(.*)", "dest": "/static/$1" },
    { "src": "/(.*)", "dest": "app.py" }
  ]
}
EOF

# 3. 部署
vercel
```

> ⚠️ Vercel 方案数据库需替换为云数据库（如 Supabase），SQLite 不支持 serverless。

---

## 个性化修改指南

### 修改公司信息
编辑 `config.py`：
```python
SITE_NAME = '你的公司名'
SITE_PHONE = '你的电话'
SITE_WECHAT = '你的微信'
SITE_EMAIL = '你的邮箱'
SITE_ADDRESS = '你的地址'
```

### 修改管理员密码
编辑 `config.py`：
```python
ADMIN_USERNAME = '你的用户名'
ADMIN_PASSWORD = '你的密码'
```

### 修改品牌色
编辑 `static/css/styles.css`：
```css
:root {
    --primary: #E84B36;  /* 改成你的品牌色 */
}
```

### 修改报价规则
编辑 `app.py` 中的 `price_rules` 字典：
```python
price_rules = {
    '名片': {'base': 50, 'unit': 0.05, 'min_order': 100},
    # 添加或修改你的产品报价规则
}
```

---

## 功能清单

### 前台
- [x] 响应式官网（手机/平板/桌面）
- [x] 产品中心展示
- [x] 在线询价表单（存入数据库）
- [x] 尺寸/数量填报
- [x] 实时报价估算
- [x] 服务流程展示
- [x] 联系方式展示

### 管理后台
- [x] 管理员登录/登出
- [x] 工作台仪表盘（统计图表）
- [x] 询价管理（查看/报价/状态更新/删除）
- [x] 询价数据导出 CSV
- [x] 产品管理（添加/编辑/上下架/删除）
- [x] 留言管理（查看/已读/删除）
- [x] 近7天询价趋势图
- [x] 产品类型分布统计

### API 接口
- `POST /api/inquiry` - 提交询价
- `GET /api/products` - 获取产品列表
- `GET /api/product-categories` - 获取产品分类
- `POST /api/contact` - 提交留言
- `POST /api/estimate-price` - 估算价格
- `GET /admin/api/stats` - 获取统计数据

---

## 数据库备份

```bash
# 备份
cp printing.db printing_backup_$(date +%Y%m%d).db

# 如需迁移到 MySQL/PostgreSQL，修改 config.py:
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:pass@host/db'
```
