# Safari 适配指南

## Safari Web Extensions

Safari使用WebExtensions API，但与Chrome有较大差异。

## 主要问题

### 1. Manifest V3 支持
- Safari 14+ 部分支持 Manifest V3
- 但 Service Worker 支持不完整

### 2. 不支持的API
- `chrome.downloads.*` - 不支持
- `chrome.notifications` - 不支持
- `chrome.contextMenus` - 不支持
- `chrome.commands` (快捷键) - 支持有限

### 3. 需要使用 Safari App Extensions

对于完整的Safari支持，需要：
1. 使用 Safari App Extension
2. 或使用 Safari Web Extension + Native App

## 解决方案

### 方案一：使用 Web Extension (推荐)

创建 `manifest.safari.json`：

```json
{
  "manifest_version": 2,
  "name": "公文PDF助手",
  "version": "1.0.0",
  "description": "自动识别网页中的PDF文件",
  "permissions": [
    "activeTab",
    "storage"
  ],
  "browser_action": {
    "default_popup": "popup/popup.html"
  }
}
```

### 方案二：简化为基础版本

如只需核心功能，创建一个仅包含PDF嗅探的简化版本。

## 建议

如需完整Safari支持，建议：
1. 使用 Safari App Extension 技术栈
2. 参考 Apple 官方文档：
   https://developer.apple.com/documentation/safariservices
3. 考虑使用跨平台工具如：
   - [ExtensionFactory](https://extensionworkshop.com)
   - [Nativefier](https://github.com/nativefier/nativefier)

## 当前状态

当前插件主要面向 Chrome/Edge，Safari 需要额外适配工作。
