# 人行智汇 - 浏览器PDF智能助手

> 自动识别网页中的PDF文件，一键下载到本地或保存到报告库

![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-green)
![Manifest V3](https://img.shields.io/badge/Manifest-V3-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 功能特性

- **智能PDF识别** - 自动扫描网页中的PDF链接，支持 `<a>`、`<embed>`、`<iframe>` 等标签
- **批量操作** - 支持多选PDF，一键批量下载或上传
- **报告库同步** - 直接保存PDF到云端报告库
- **标题编辑** - 点击即可修改PDF标题
- **多浏览器支持** - 兼容 Chrome、Edge、Firefox（部分功能）

## 安装说明

### Chrome / Edge

1. 打开 `chrome://extensions/` 或 `edge://extensions/`
2. 开启右上角「开发者模式」
3. 点击「加载解包的扩展程序」
4. 选择本仓库的 `browser-extension` 文件夹

### Firefox

详见 [FIREFOX_EDGE.md](./FIREFOX_EDGE.md)

## 使用指南

1. 安装扩展后，访问包含PDF的网页
2. 点击扩展图标打开popup面板
3. 查看识别的PDF列表
4. 选择操作：
   - **预览** - 在新标签页打开PDF
   - **本地** - 下载到本地
   - **报告库** - 上传到云端报告库
5. 支持批量选择和全选操作

## 项目结构

```
browser-extension/
├── manifest.json          # 扩展配置文件
├── popup/                 # Popup弹窗页面
│   ├── popup.html        # HTML结构
│   ├── popup.js         # 弹窗逻辑
│   └── popup.css        # 样式文件
├── content/              # Content Script（注入网页）
│   └── content.js       # PDF嗅探器
├── background/           # Background Service Worker
│   └── background.js    # 后台脚本
└── icons/               # 扩展图标
```

## 技术实现

- **Manifest V3** - 最新扩展规范
- **Content Script** - 网页PDF自动扫描
- **chrome.storage.local** - 数据持久化
- **chrome.downloads** - 文件下载
- **FormData API** - 文件上传到后端

## 后端对接

插件需要配合后端服务使用，API端点配置在 `popup.js` 中：

```javascript
const CLOUD_CONFIG = {
  apiEndpoint: 'http://localhost:8000/api/v1/documents/',
  apiToken: 'dev-token-for-localhost'
};
```

### API要求

- `POST /api/v1/documents/` - 上传文档
  - Content-Type: `multipart/form-data`
  - 参数: `file`, `title`, `source_url`

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Shift+P` | 打开PDF助手 |
| `Ctrl+Shift+S` | 扫描页面PDF |
| `Ctrl+Shift+D` | 下载页面所有PDF |

## 开发相关

### 调试

1. 加载扩展后，在扩展页面找到「服务工作者」或「背景页」
2. 点击可查看控制台日志
3. Popup页面可右键 → 检查弹出内容

### 修改代码后

在 `chrome://extensions/` 页面点击扩展的刷新按钮即可。

## 浏览器兼容性

| 浏览器 | 支持程度 | 备注 |
|--------|----------|------|
| Chrome | ✅ 完全支持 | 推荐使用 |
| Edge | ✅ 完全支持 | 基于Chromium |
| Firefox | ⚠️ 部分支持 | 见FIREFOX_EDGE.md |

## License

MIT License
