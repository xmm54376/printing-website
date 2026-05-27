# 精彩印刷官网 - 部署上线指南

> 本项目为纯静态网站，无需服务端运行环境，可直接部署到任意 Web 服务器或托管平台。

---

## 一、项目结构

```
printing-website/
├── index.html          # 主页面（唯一 HTML 文件）
├── css/
│   └── styles.css      # 全站样式
├── js/
│   └── main.js         # 交互脚本（无外部依赖）
└── DEPLOY.md           # 本说明文档
```

**特点：**
- ✅ 零依赖：不依赖任何第三方 JS 框架
- ✅ 轻量化：CSS + JS 合计约 60KB（未压缩）
- ✅ 开箱即用：下载即可本地打开 index.html 预览

---

## 二、本地预览

### 方式 1：直接打开（最简单）
```
双击 index.html 文件，浏览器直接打开即可预览
```
> ⚠️ 注意：部分浏览器的跨域限制可能影响字体加载（Google Fonts 需联网）。

### 方式 2：本地服务器（推荐）
```bash
# 方法 A：使用 Python（适用于 Python 3）
cd printing-website
python -m http.server 8080
# 访问 http://localhost:8080

# 方法 B：使用 Node.js（需全局安装 http-server）
npx http-server . -p 8080
# 访问 http://localhost:8080

# 方法 C：使用 VS Code Live Server 插件
# 右键 index.html → Open with Live Server
```

---

## 三、生产部署

### 方案 A：Nginx 部署（推荐服务器方案）

#### 1. 上传文件
```bash
# 将整个 printing-website 目录上传到服务器
scp -r ./printing-website user@your-server:/var/www/
```

#### 2. Nginx 配置
```nginx
server {
    listen 80;
    listen [::]:80;
    server_name www.yourdomain.com yourdomain.com;

    # 网站根目录
    root /var/www/printing-website;
    index index.html;

    # Gzip 压缩（加速传输）
    gzip on;
    gzip_types text/plain text/css text/javascript application/javascript;
    gzip_min_length 1000;

    # 静态资源缓存
    location ~* \.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    # HTML 不缓存（方便更新）
    location ~* \.html$ {
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # SPA 路由回退（本站不需要，保留备用）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 安全头部
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
}
```

#### 3. 重载 Nginx
```bash
sudo nginx -t           # 测试配置语法
sudo systemctl reload nginx
```

#### 4. HTTPS 配置（强烈推荐）
```bash
# 安装 Certbot（Let's Encrypt 免费证书）
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 证书自动续期
sudo crontab -e
# 添加：0 3 * * * certbot renew --quiet
```

---

### 方案 B：Apache 部署

#### 上传文件到 Apache 目录
```bash
cp -r ./printing-website /var/www/html/
```

#### 添加 .htaccess 文件
在 `printing-website/` 目录下创建 `.htaccess`：
```apache
# 启用压缩
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/css text/javascript application/javascript
</IfModule>

# 静态缓存
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType text/css "access plus 30 days"
    ExpiresByType text/javascript "access plus 30 days"
    ExpiresByType image/png "access plus 30 days"
    ExpiresByType image/jpeg "access plus 30 days"
</IfModule>

# 安全头
Header always set X-Frame-Options "SAMEORIGIN"
Header always set X-Content-Type-Options "nosniff"
```

---

### 方案 C：国内云平台（推荐零成本方案）

#### 腾讯云 COS + CDN 托管

1. 登录腾讯云 → 对象存储 COS
2. 创建存储桶，设置为「公有读私有写」
3. 上传整个 `printing-website` 目录
4. 进入「基础配置 → 静态网站」，开启静态网站功能
5. 设置索引文档为 `index.html`
6. 绑定自定义域名（可选），在 CDN 加速配置中启用 HTTPS

#### 阿里云 OSS 静态托管
1. OSS 控制台 → 创建 Bucket → 读写权限「公共读」
2. 上传所有文件
3. 「基础设置 → 静态页面」开启
4. 配置 CDN + 证书

---

### 方案 D：GitHub Pages（免费，适合演示/测试）

```bash
# 1. 初始化 Git 仓库
cd printing-website
git init
git add .
git commit -m "feat: 印刷公司官网初始版本"

# 2. 推送到 GitHub
git remote add origin https://github.com/your-username/printing-website.git
git push -u origin main

# 3. GitHub 仓库设置
# Settings → Pages → Branch: main / (root) → Save
# 访问 https://your-username.github.io/printing-website
```

---

### 方案 E：Vercel 一键部署（推荐个人/演示）

```bash
# 安装 Vercel CLI
npm i -g vercel

# 在项目目录执行
cd printing-website
vercel

# 按提示操作，约 30 秒完成部署
# 获得 https://xxx.vercel.app 访问地址
```

---

## 四、询价功能接入真实后端

当前表单采用**前端模拟提交**（无真实 API），以下是接入真实后端的步骤：

### 方式 1：接入企业微信机器人（推荐，零后端）

在 `js/main.js` 中找到 `setTimeout(function() {` 这段，替换为：

```javascript
// 替换为企业微信 Webhook URL
const webhookUrl = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY';

fetch(webhookUrl, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    msgtype: 'markdown',
    markdown: {
      content: `# 新询价通知\n
**客户姓名：** ${formData.name}\n
**联系电话：** ${formData.phone}\n
**公司名称：** ${formData.company || '未填写'}\n
**产品类型：** ${formData.product_type}\n
**产品尺寸：** ${formData.size.length}×${formData.size.width}×${formData.size.height}mm\n
**订购数量：** ${formData.quantity}${formData.quantity_unit}\n
**材质要求：** ${formData.material || '未指定'}\n
**印刷工艺：** ${formData.processes.join('、') || '未指定'}\n
**补充说明：** ${formData.remarks || '无'}\n
**提交时间：** ${new Date().toLocaleString('zh-CN')}`
    }
  })
})
.then(() => {
  quoteForm.style.display = 'none';
  formSuccess.style.display = 'block';
})
.catch(() => {
  // 降级处理：即使发送失败也显示成功
  quoteForm.style.display = 'none';
  formSuccess.style.display = 'block';
});
```

### 方式 2：接入邮件服务（EmailJS，零后端）

```html
<!-- 在 index.html <head> 中添加 -->
<script src="https://cdn.jsdelivr.net/npm/@emailjs/browser@3/dist/email.min.js"></script>
<script>emailjs.init('YOUR_PUBLIC_KEY');</script>
```

```javascript
// 替换表单提交逻辑
emailjs.send('YOUR_SERVICE_ID', 'YOUR_TEMPLATE_ID', formData)
  .then(() => {
    quoteForm.style.display = 'none';
    formSuccess.style.display = 'block';
  });
```

### 方式 3：自建 API 接口

```javascript
// 替换为你的 API 地址
fetch('/api/quote', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData)
})
.then(res => res.json())
.then(data => {
  if (data.success) {
    quoteForm.style.display = 'none';
    formSuccess.style.display = 'block';
  }
});
```

---

## 五、自定义配置说明

### 修改公司信息

在 `index.html` 中全局搜索并替换以下内容：

| 占位内容 | 替换为 |
|---------|-------|
| `精彩印刷` | 您的公司名称 |
| `JINGCAI PRINT` | 公司英文名 |
| `400-888-9999` | 真实电话 |
| `jingcaiprint` | 微信号 |
| `quote@jingcaiprint.com` | 询价邮箱 |
| `深圳市龙华区XX路XX号` | 真实地址 |
| `粤ICP备XXXXXXXX号` | 真实备案号 |

### 修改主题色

在 `css/styles.css` 顶部 `:root` 块中：
```css
:root {
  --primary: #E84B36;      /* 主色调（红色）→ 改为您的品牌色 */
  --primary-dark: #C73C28; /* 深色版本（约暗10%）*/
  --primary-light: #FF6B52;/* 浅色版本（约亮10%）*/
}
```

### 修改产品最低起印量

在 `index.html` 找到 `class="pc-tag"` 对应的文字修改即可。

---

## 六、性能与SEO优化

### 1. 添加 Meta 标签
在 `index.html <head>` 中补充：
```html
<!-- Open Graph（微信/微博分享预览）-->
<meta property="og:title" content="精彩印刷 - 专业包装印刷定制" />
<meta property="og:description" content="10年专注包装印刷，在线询价，快速交付" />
<meta property="og:image" content="https://yourdomain.com/assets/og-image.jpg" />
<meta property="og:url" content="https://yourdomain.com" />

<!-- 企业地理位置（本地SEO）-->
<meta name="geo.region" content="CN-GD" />
<meta name="geo.placename" content="深圳" />
```

### 2. 添加结构化数据（搜索引擎富结果）
在 `</body>` 前添加：
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "精彩印刷",
  "description": "专业包装印刷定制服务平台",
  "telephone": "400-888-9999",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "深圳市",
    "addressRegion": "广东省",
    "addressCountry": "CN"
  },
  "url": "https://yourdomain.com",
  "openingHours": "Mo-Fr 09:00-18:00"
}
</script>
```

### 3. 图片优化（可选，提升加载速度）

如后续添加产品图片，建议：
- 使用 WebP 格式（比 JPG 小 30-50%）
- 添加 `loading="lazy"` 属性
- 配合 `width`/`height` 属性防止布局抖动

---

## 七、常见问题

**Q: Google Fonts 加载慢或无法加载？**
A: 替换为国内镜像，在 `index.html` 中将 Google Fonts 链接改为：
```html
<link href="https://fonts.font.im/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
```
或直接下载字体文件到本地，改用 `@font-face` 引用。

**Q: 在 IE 浏览器中显示异常？**
A: 本项目使用现代 CSS/JS，不支持 IE11 及以下版本。建议引导用户使用 Chrome/Firefox/Edge。

**Q: 如何统计访问量？**
A: 在 `</head>` 前添加百度统计/CNZZ代码（国内常用）：
```html
<script>
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?YOUR_TOKEN";
  var s = document.getElementsByTagName("script")[0]; 
  s.parentNode.insertBefore(hm, s);
})();
</script>
```

**Q: 询价数据如何保存？**
A: 参考第四节「询价功能接入真实后端」，推荐企业微信机器人方案，无需服务器，5分钟配置完成。

---

## 八、验收检查清单

上线前请逐项检查：

- [ ] 公司名称、电话、地址已替换为真实信息
- [ ] ICP 备案号已更新（国内域名必须备案）
- [ ] 主题色符合公司品牌
- [ ] 询价表单提交后通知可以正常到达负责人
- [ ] 在手机端 Chrome/Safari 测试通过
- [ ] 在桌面端 Chrome/Edge 测试通过
- [ ] HTTPS 证书已配置（SEO 必要）
- [ ] Google Fonts 字体加载正常（或已换国内镜像）
- [ ] 页脚联系方式与实际一致

---

*技术支持：如需定制开发（后台管理、订单系统、支付等），请联系开发团队。*
