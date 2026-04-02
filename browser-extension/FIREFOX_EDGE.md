# Firefox/Edge 适配指南

## Microsoft Edge

Edge基于Chromium内核，与Chrome基本兼容。

### 安装方法
1. 打开 `edge://extensions/`
2. 开启右上角「开发者模式」
3. 点击「加载解包的扩展程序」
4. 选择 `browser-extension` 文件夹

### 已知差异
- 快捷键可能与Chrome不同
- 通知使用系统通知

---

## Mozilla Firefox

Firefox 78+ 支持Manifest V3，但有部分API差异。

### 安装方法
1. 打开 `about:debugging#/runtime/this-firefox`
2. 点击「临时加载扩展程序...」
3. 选择 `browser-extension` 文件夹

### 需要修改的代码

Firefox不支持 `chrome.downloads.search` 的部分参数，需要调整：

**popup.js 中的 loadHistory 函数需要修改：**

```javascript
// Firefox版本 - 简化版历史记录
async function loadHistory() {
  // Firefox不支持chrome.downloads.search，使用storage存储历史
  const result = await chrome.storage.local.get('downloadHistory');
  const items = result.downloadHistory || [];
  // ...渲染列表
}
```

**background.js 中的右键菜单在Firefox中需要不同写法**

### Firefox不支持的功能
- `chrome.notifications` 在某些版本中有限制
- Service Worker部分API不同
- 网络请求拦截需要不同权限

### 建议

如需完整Firefox支持，建议：
1. 创建 `manifest.firefox.json`
2. 使用 polyfill 处理API差异
3. 参考 https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions

---

## 测试建议

测试浏览器插件前，先在Chrome中确认功能正常，然后：
1. 在Edge中加载并测试基础功能
2. 在Firefox中加载并记录不兼容的部分
3. 根据测试结果针对性修复
