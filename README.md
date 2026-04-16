# 教育数据看板 - 静态部署包

## 特性
- 纯静态页面，无需后端
- 每个访问者需要自行上传 Excel 文件查看数据
- 数据仅存储在浏览器 IndexedDB 中，不会上传到任何服务器

## 本地运行

```bash
# 方式1：直接打开（推荐）
cd public
open index.html
# 或双击 index.html 文件

# 方式2：本地服务器
cd /path/to/dashboard-deploy
node server.js
# 然后访问 http://localhost:8080
```

## 部署到静态托管（任选其一）

### 方案A：Vercel（免费，推荐）
```bash
npm i -g vercel
cd /path/to/dashboard-deploy
vercel
# 按提示操作，获得类似 https://your-project.vercel.app 的链接
```

### 方案B：Netlify（免费）
1. 访问 https://app.netlify.com/drop
2. 将 `public` 文件夹拖入页面
3. 获得类似 `https://random-name.netlify.app` 的链接

### 方案C：GitHub Pages（免费）
1. 将 `public` 文件夹内容推送到 GitHub 仓库
2. 进入仓库 Settings → Pages
3. Source 选择 `main` branch 和 `/ (root)` 文件夹
4. 获得 `https://yourusername.github.io/repo-name/` 链接

### 方案D：阿里云 OSS / 腾讯云 COS
1. 创建 OSS/Bucket（公有读私有写）
2. 上传 `public` 文件夹内所有文件到 Bucket
3. 开启静态网站托管
4. 获得类似 `https://your-bucket.oss-cn-beijing.aliyuncs.com` 的链接

## 部署后使用
1. 分享链接给同事
2. 同事打开链接后，点击上传按钮上传 Excel 文件
3. 每个人只能看到自己本地的数据

## 文件说明
```
dashboard-deploy/
├── public/          # 静态文件（部署时上传这些）
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── server.js        # 本地开发用的小服务器（部署时不需要）
└── README.md        # 说明文档
```
