# PWA (Progressive Web App) 功能说明

## 概述

AI Chat 应用已改造为 PWA (渐进式 Web 应用)，提供以下功能：

- **离线支持**: 应用资源缓存，离线时仍可访问基本界面
- **可安装**: 用户可将应用添加到主屏幕，获得原生应用般的体验
- **自动更新**: Service Worker 自动检测更新，提示用户刷新
- **快速加载**: 智能缓存策略，提升加载速度

## PWA 配置

### 配置文件

- [`vite.config.ts`](../frontend/vite.config.ts) - vite-plugin-pwa 配置
- [`index.html`](../frontend/index.html) - PWA meta 标签
- [`public/pwa-icon.svg`](../frontend/public/pwa-icon.svg) - 源图标文件

### 生成的图标

PWA 图标使用 `@vite-pwa/assets-generator` 从 `pwa-icon.svg` 自动生成：

| 文件名 | 尺寸 | 用途 |
|--------|------|------|
| `pwa-64x64.png` | 64x64 | 小图标 |
| `pwa-192x192.png` | 192x192 | Android Chrome 图标 |
| `pwa-512x512.png` | 512x512 | Android Chrome 启动画面 |
| `maskable-icon-512x512.png` | 512x512 | 可遮罩图标 (Android 自适应图标) |
| `apple-touch-icon-180x180.png` | 180x180 | iOS Safari 主屏幕图标 |
| `favicon.ico` | 多尺寸 | 浏览器标签图标 |

### 重新生成图标

如需更新图标，修改 `public/pwa-icon.svg` 后运行：

```bash
cd frontend
npm run generate-pwa-icons
```

## 缓存策略

### 静态资源 (CacheFirst)

- Fluent UI CDN 资源 (`res.cdn.office.net`)
- 缓存有效期: 1 年
- 最大条目数: 100

### API 请求 (NetworkFirst)

- `/api/*` 路径的请求
- 网络超时: 10 秒
- 缓存有效期: 5 分钟
- 最大条目数: 50

## 用户体验组件

### 更新提示 (PWAUpdatePrompt)

当检测到新版本时，显示更新提示通知用户刷新页面。

位置: [`src/components/PWAUpdatePrompt/`](../frontend/src/components/PWAUpdatePrompt/)

### 安装提示 (PWAInstallPrompt)

在支持的浏览器中，提示用户将应用安装到主屏幕。

位置: [`src/components/PWAInstallPrompt/`](../frontend/src/components/PWAInstallPrompt/)

特性:
- 延迟 3 秒显示，避免打扰用户
- 用户可选择"以后再说"，7 天后再次提示
- 已安装或独立模式下不显示

### 离线指示器 (OfflineIndicator)

当用户离线时显示提示。

位置: [`src/components/OfflineIndicator/`](../frontend/src/components/OfflineIndicator/)

## 测试 PWA

### 本地测试

1. 构建生产版本：
   ```bash
   cd frontend
   npm run build
   ```

2. 预览构建结果：
   ```bash
   npm run preview
   ```

3. 在 Chrome DevTools 中：
   - 打开 Application 面板
   - 查看 Manifest、Service Workers、Cache Storage

### Lighthouse 审计

1. 打开 Chrome DevTools
2. 切换到 Lighthouse 面板
3. 选择 "Progressive Web App" 类别
4. 运行审计

## 浏览器支持

| 浏览器 | 支持状态 |
|--------|----------|
| Chrome (Android/Desktop) | ✅ 完全支持 |
| Edge | ✅ 完全支持 |
| Safari (iOS) | ✅ 基本支持 (部分功能受限) |
| Firefox | ✅ 基本支持 (不支持安装提示) |

## 注意事项

1. **HTTPS 必需**: PWA 功能需要 HTTPS 环境 (localhost 除外)
2. **Service Worker 作用域**: 默认作用域为根路径 `/`
3. **更新延迟**: Service Worker 更新可能需要关闭所有标签页后生效
4. **清除缓存**: 如遇问题，可在 DevTools 中手动清除 Service Worker 和缓存