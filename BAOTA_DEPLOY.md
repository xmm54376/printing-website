# 宝塔面板部署指南 - 精彩印刷官网

> 本文档详细介绍如何将印刷公司官网部署到宝塔面板（BT Panel）服务器上。

## 目录

1. [服务器要求](#1-服务器要求)
2. [安装宝塔面板](#2-安装宝塔面板)
3. [宝塔面板初始设置](#3-宝塔面板初始设置)
4. [安装运行环境](#4-安装运行环境)
5. [上传项目代码](#5-上传项目代码)
6. [配置Python项目](#6-配置python项目)
7. [配置Nginx反向代理](#7-配置nginx反向代理)
8. [配置SSL证书（HTTPS）](#8-配置ssl证书https)
9. [配置静态文件与上传目录](#9-配置静态文件与上传目录)
10. [数据库管理](#10-数据库管理)
11. [常见问题排查](#11-常见问题排查)
12. [日常维护](#12-日常维护)

---

## 1. 服务器要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | CentOS 7+ / Ubuntu 18.04+ | Ubuntu 22.04 LTS |
| CPU | 1核 | 2核 |
| 内存 | 512MB | 2GB |
| 硬盘 | 10GB | 40GB SSD |
| 带宽 | 1Mbps | 5Mbps |
| Python | 3.9+ | 3.12 |

> **推荐使用**：阿里云/腾讯云轻量应用服务器，2核2G，Ubuntu 22.04，预装宝塔面板。

---

## 2. 安装宝塔面板

### 2.1 Ubuntu/Debian 安装命令

```bash
wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh ed8484bec
```

### 2.2 CentOS 安装命令

```bash
yum install -y wget && wget -O install.sh https://download.bt.cn/install/install_6.0.sh && sh install.sh ed8484bec
```

### 2.3 安装完成记录

安装完成后，宝塔面板会显示以下信息，**请务必保存**：

```
==================================================================
Congratulations! Installed successfully!
==================================================================
外网面板地址: https://xxx.xxx.xxx.xxx:8888/xxxxxxxx
内网面板地址: https://192.168.x.x:8888/xxxxxxxx
username: xxxxxxxx
password: xxxxxxxx
==================================================================
```

---

## 3. 宝塔面板初始设置

1. 使用外网面板地址登录宝塔面板
2. 首次登录会弹出"推荐安装"窗口，**先跳过**
3. 进入面板设置，修改默认端口和密码
4. **绑定宝塔账号**（必须，否则无法安装软件）

---

## 4. 安装运行环境

在宝塔面板的 **软件商店** 中安装以下组件：

### 4.1 必须安装

| 软件 | 版本 | 用途 |
|------|------|------|
| Nginx | 1.24+ | Web服务器/反向代理 |
| Python项目管理器 | 最新版 | 管理Python项目 |
| MySQL 5.7/8.0（可选） | 5.7+ | 后续可迁移到MySQL |

### 4.2 安装步骤

1. 进入 **软件商店** → 搜索"Nginx" → 点击 **安装**
2. 搜索"Python项目管理器" → 点击 **安装**
3. 安装完成后，在"已安装"中确认两个插件都显示为"运行中"

---

## 5. 上传项目代码

### 方式一：从GitHub拉取（推荐）

1. SSH登录服务器
2. 安装Git（宝塔面板 → 终端）：
   ```bash
   apt install git -y    # Ubuntu
   # 或
   yum install git -y    # CentOS
   ```
3. 创建项目目录并拉取代码：
   ```bash
   mkdir -p /www/wwwroot/printing-website
   cd /www/wwwroot/printing-website
   git clone https://github.com/xmm54376/printing-website.git .
   ```

### 方式二：宝塔面板上传

1. 将本地代码打包为 `printing-website.zip`
2. 宝塔面板 → **文件** → 进入 `/www/wwwroot/`
3. 创建目录 `printing-website`，进入后点击 **上传** → 选择zip文件
4. 上传完成后，右键 → **解压**

---

## 6. 配置Python项目

### 6.1 创建Python项目

1. 宝塔面板 → **软件商店** → **Python项目管理器** → **设置**
2. 点击 **添加项目**，填写：
   - **项目名称**: `printing-website`
   - **项目路径**: `/www/wwwroot/printing-website`
   - **项目启动文件**: `app.py`
   - **Python版本**: 选择 3.9 以上（推荐 3.12）
   - **框架**: 选择 **Flask**
   - **启动方式**: 选择 **gunicorn**
   - **端口**: `5000`
   - **备注**: 印刷公司官网

### 6.2 安装依赖

在Python项目管理器中，进入项目，点击 **模块** → 输入以下依赖并安装：

```
Flask>=3.0.0
Flask-SQLAlchemy>=3.0.0
Werkzeug>=3.0.0
gunicorn>=21.0.0
```

或者通过终端执行：
```bash
cd /www/wwwroot/printing-website
pip3 install -r requirements.txt
```

### 6.3 配置启动命令

Python项目管理器中，启动命令配置为：

```
gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()"
```

参数说明：
- `-w 4`: 4个工作进程（2核CPU推荐）
- `-b 127.0.0.1:5000`: 绑定到本地5000端口（通过Nginx反向代理对外服务）

### 6.4 修改生产配置

编辑 `/www/wwwroot/printing-website/config.py`，确保以下配置适合生产环境：

```python
# 生产环境SECRET_KEY（请修改为随机字符串）
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-random-secret-key-here-change-me')

# 数据库路径（SQLite）
SQLALCHEMY_DATABASE_URI = 'sqlite:////www/wwwroot/printing-website/instance/printing.db'
```

> **安全建议**：修改SECRET_KEY为一个随机字符串，可通过 `python3 -c "import secrets; print(secrets.token_hex(32))"` 生成。

### 6.5 创建必要目录并初始化

```bash
cd /www/wwwroot/printing-website
mkdir -p instance static/uploads
python3 -c "from app import create_app; from models import init_default_data; app = create_app(); init_default_data(app)"
```

### 6.6 启动项目

在Python项目管理器中点击 **启动**，确认状态变为"运行中"。

也可通过终端验证：
```bash
curl http://127.0.0.1:5000
# 应返回HTML内容
```

---

## 7. 配置Nginx反向代理

### 7.1 创建网站

1. 宝塔面板 → **网站** → **添加站点**
2. 选择 **Python项目**
3. 填写域名（如 `printing.example.com`）
4. 项目选择之前创建的 `printing-website`
5. 点击 **提交**

### 7.2 手动配置Nginx（如果需要）

如果手动创建网站，在网站设置 → **配置文件** 中修改：

```nginx
server {
    listen 80;
    server_name printing.example.com;  # 改为你的域名

    # 静态文件直接由Nginx提供
    location /static/ {
        alias /www/wwwroot/printing-website/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 上传文件
    location /static/uploads/ {
        alias /www/wwwroot/printing-website/static/uploads/;
        expires 7d;
    }

    # 反向代理到Flask应用
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;

        # 文件上传大小限制
        client_max_body_size 16m;
    }

    # 禁止访问隐藏文件和数据库
    location ~ /\. {
        deny all;
    }
    location ~ \.(db|sqlite|pyc)$ {
        deny all;
    }

    access_log /www/wwwlogs/printing_access.log;
    error_log /www/wwwlogs/printing_error.log;
}
```

---

## 8. 配置SSL证书（HTTPS）

### 8.1 申请免费SSL证书

1. 宝塔面板 → **网站** → 点击站点名 → **SSL**
2. 选择 **Let's Encrypt** → 勾选域名 → 点击 **申请**
3. 等待1-2分钟，申请成功后开启 **强制HTTPS**

### 8.2 或使用自有证书

1. 在SSL页面选择 **其他证书**
2. 粘贴证书内容（.pem）和密钥内容（.key）
3. 点击 **保存** → 开启 **强制HTTPS**

---

## 9. 配置静态文件与上传目录

### 9.1 目录权限

```bash
# 设置项目目录权限
chown -R www:www /www/wwwroot/printing-website
chmod -R 755 /www/wwwroot/printing-website

# 上传目录需要写权限
chmod -R 775 /www/wwwroot/printing-website/static/uploads

# 数据库目录需要写权限
chmod -R 775 /www/wwwroot/printing-website/instance
```

### 9.2 宝塔面板文件管理

在宝塔面板的 **文件** 管理中，可以方便地上传产品图片、管理上传文件等。

---

## 10. 数据库管理

### 10.1 当前使用SQLite

本项目默认使用SQLite数据库，数据文件位于：
```
/www/wwwroot/printing-website/instance/printing.db
```

### 10.2 备份数据库

```bash
# 手动备份
cp /www/wwwroot/printing-website/instance/printing.db /www/backup/printing_$(date +%Y%m%d).db

# 设置宝塔定时备份（推荐）
# 宝塔面板 → 计划任务 → 添加任务
# 类型: 备份目录
# 目录: /www/wwwroot/printing-website/instance
# 执行周期: 每天凌晨3点
```

### 10.3 如需迁移到MySQL（可选）

1. 修改 `config.py`：
   ```python
   SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@localhost/printing_db?charset=utf8mb4'
   ```
2. 安装MySQL驱动：
   ```bash
   pip3 install pymysql
   ```
3. 在MySQL中创建数据库：
   ```sql
   CREATE DATABASE printing_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
4. 重新初始化数据（会自动创建表和默认数据）

---

## 11. 常见问题排查

### Q: 访问502 Bad Gateway

```bash
# 检查Flask进程是否运行
ps aux | grep gunicorn

# 检查端口是否被占用
netstat -tlnp | grep 5000

# 重启项目
# Python项目管理器 → 重启
```

### Q: 页面样式/图片加载不出来

- 检查Nginx静态文件配置是否正确
- 确认 `static` 目录权限：`chmod -R 755 /www/wwwroot/printing-website/static`
- 检查Nginx配置中的 `alias` 路径是否正确

### Q: 上传图片失败

- 检查 `static/uploads` 目录写权限：`chmod -R 775 static/uploads`
- 检查Nginx `client_max_body_size` 配置（至少16m）

### Q: 后台管理无法访问

- 确认URL是 `/admin`（不是 `/admin/`）
- 默认账号：`admin` / `admin888`
- 检查是否被防火墙拦截

### Q: 数据库报错"no such table"

- 删除数据库文件重新初始化：
  ```bash
  rm -f /www/wwwroot/printing-website/instance/printing.db
  python3 -c "from app import create_app; from models import init_default_data; app = create_app(); init_default_data(app)"
  ```

### Q: 修改了代码但不生效

```bash
# 重启Python项目
# Python项目管理器 → 重启

# 或终端执行
pkill -f gunicorn
cd /www/wwwroot/printing-website
gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()" -D
```

---

## 12. 日常维护

### 定时任务建议

| 任务 | 周期 | 说明 |
|------|------|------|
| 数据库备份 | 每天 | 宝塔面板 → 计划任务 |
| 日志清理 | 每周 | 清理access/error日志 |
| 系统更新 | 每月 | 更新系统安全补丁 |

### 更新网站代码

```bash
cd /www/wwwroot/printing-website
git pull origin main
# 重启项目
pkill -f gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()" -D
```

### 管理后台入口

部署完成后，通过以下地址访问管理后台：

```
https://你的域名/admin
```

默认管理员账号：`admin` / `admin888`

> **首次登录后请立即修改密码！** 后台 → 后台用户 → 修改密码

---

## 附录：快速部署命令（一键执行）

将以下命令保存为 `deploy.sh` 并在服务器上执行：

```bash
#!/bin/bash
# 精彩印刷官网 - 快速部署脚本
# 使用方法：bash deploy.sh

set -e

echo "========================================="
echo "  精彩印刷官网 - 宝塔面板快速部署"
echo "========================================="

PROJECT_DIR="/www/wwwroot/printing-website"

# 1. 检查是否已存在
if [ -d "$PROJECT_DIR" ]; then
    echo "[!] 项目目录已存在: $PROJECT_DIR"
    read -p "是否更新代码？(y/n): " confirm
    if [ "$confirm" = "y" ]; then
        cd $PROJECT_DIR && git pull origin main
        echo "[✓] 代码已更新"
    fi
else
    echo "[1/5] 拉取代码..."
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR
    git clone https://github.com/xmm54376/printing-website.git .
    echo "[✓] 代码拉取完成"
fi

echo "[2/5] 创建必要目录..."
mkdir -p $PROJECT_DIR/instance $PROJECT_DIR/static/uploads
echo "[✓] 目录创建完成"

echo "[3/5] 安装Python依赖..."
pip3 install -r $PROJECT_DIR/requirements.txt 2>/dev/null || pip install -r $PROJECT_DIR/requirements.txt
echo "[✓] 依赖安装完成"

echo "[4/5] 初始化数据库..."
cd $PROJECT_DIR
python3 -c "from app import create_app; from models import init_default_data; app = create_app(); init_default_data(app)"
echo "[✓] 数据库初始化完成"

echo "[5/5] 设置权限..."
chown -R www:www $PROJECT_DIR
chmod -R 755 $PROJECT_DIR
chmod -R 775 $PROJECT_DIR/static/uploads $PROJECT_DIR/instance
echo "[✓] 权限设置完成"

echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo "后续步骤："
echo "1. 在宝塔Python项目管理器中启动项目"
echo "2. 配置Nginx反向代理（参见完整文档）"
echo "3. 申请SSL证书并开启HTTPS"
echo "4. 访问 /admin 修改默认管理员密码"
echo ""
echo "管理后台: http://你的域名/admin"
echo "默认账号: admin / admin888"
```

---

*文档版本：v1.0 | 最后更新：2026年5月*
