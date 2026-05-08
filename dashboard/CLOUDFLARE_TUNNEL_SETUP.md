# Cloudflare Tunnel 接入说明

目标：让 [platform.html](file:///Users/x/Downloads/Project/dashboard/platform.html) 通过 Cloudflare 暴露出来的远程 `server.js` 访问统一后端，解决 GitHub Pages 静态页与本地/子账号数据源不一致的问题。

## 一、当前代码已支持的能力

当前前端已支持“远程 API 优先”模式：

1. 在页面里设置：
```html
<script>
  window.SALES_PLATFORM_API_BASE = 'https://你的-tunnel.trycloudflare.com';
</script>
```
2. 或者在浏览器控制台设置：
```js
localStorage.setItem('sales-platform-api-base', 'https://你的-tunnel.trycloudflare.com')
location.reload()
```
3. 配置后，`platform.js` 会优先请求远程 API，而不是 GitHub Pages 本地模式。

相关文件：
- [platform.html](file:///Users/x/Downloads/Project/dashboard/platform.html)
- [platform.js](file:///Users/x/Downloads/Project/dashboard/platform.js)
- [server.js](file:///Users/x/Downloads/Project/dashboard/server.js)

## 二、是否需要购买域名

不需要。先用 Cloudflare Tunnel 的临时地址即可。

适合当前阶段：
1. 快速验证登录
2. 验证子账号 `wfshu / ets@wfshu`
3. 验证静态前端 + 远程后端统一数据源

后续如果要长期正式给团队使用，再考虑购买域名并绑定到 Cloudflare。

## 三、最快接入步骤（不买域名）

### 1. 本地启动 Node 服务

在项目目录执行：
```bash
cd /Users/x/Downloads/Project/dashboard
node server.js
```

默认会监听：
- `http://127.0.0.1:8090`

### 2. 安装 cloudflared

macOS 推荐：
```bash
brew install cloudflared
```

### 3. 启动临时 Tunnel

```bash
cloudflared tunnel --url http://127.0.0.1:8090
```

启动后终端会给出一个类似地址：
```text
https://abcde-12345.trycloudflare.com
```

这个地址就是你的后端公网入口。

### 4. 配置前端指向远程 API

打开 [platform.html](file:///Users/x/Downloads/Project/dashboard/platform.html)，把：
```html
<script>
    window.SALES_PLATFORM_API_BASE = '';
</script>
```
改成：
```html
<script>
    window.SALES_PLATFORM_API_BASE = 'https://abcde-12345.trycloudflare.com';
</script>
```

然后重新发布静态页即可。

### 5. 无需改代码的临时验证方式

如果你只是先临时验证，不想立刻改文件，可以在打开线上页后，浏览器控制台执行：
```js
localStorage.setItem('sales-platform-api-base', 'https://abcde-12345.trycloudflare.com')
location.reload()
```

清除方法：
```js
localStorage.removeItem('sales-platform-api-base')
location.reload()
```

## 四、验证顺序

按这个顺序测：

1. 打开 Tunnel 后端地址，确认能访问
2. 打开 GitHub Pages 上的 `platform.html`
3. 确认顶部用户信息处会显示“远程服务：你的 tunnel 地址”
4. 用管理员登录
5. 进入子账号管理
6. 用 `wfshu / ets@wfshu` 登录
7. 看是否能正常进入并看到山东范围学校

## 五、正式化建议

如果临时 Tunnel 验证通过，下一步可以做：

1. 购买域名（可选）
2. Cloudflare DNS 托管
3. 固定子域名：
   - `dashboard.xxx.com` 指向静态前端
   - `api.xxx.com` 指向后端
4. 前端把 `window.SALES_PLATFORM_API_BASE` 固定成：
```html
<script>
  window.SALES_PLATFORM_API_BASE = 'https://api.xxx.com';
</script>
```

## 六、你当前最该做的事

不是先买域名，而是先跑通：

1. `node server.js`
2. `cloudflared tunnel --url http://127.0.0.1:8090`
3. 把 tunnel 地址填进 `window.SALES_PLATFORM_API_BASE`
4. 验证子账号和登录是否恢复正常

如果这一步通过，说明问题已经从“静态页本地模式”切回到“统一远程后端”了。
