/**
 * background.js - 后台 Service Worker (Manifest V3)
 */

const tabPdfsMap = new Map();

chrome.runtime.onInstalled.addListener(() => {
  console.log('[公文PDF助手] 插件已安装');

  // 创建右键菜单
  chrome.contextMenus.create({
    id: 'downloadPdf',
    title: '下载此PDF',
    contexts: ['link']
  });

  chrome.contextMenus.create({
    id: 'savePdfToCloud',
    title: '保存PDF到云端',
    contexts: ['link']
  });

  chrome.contextMenus.create({
    id: 'downloadAllFromPage',
    title: '下载页面所有PDF',
    contexts: ['page']
  });

  chrome.contextMenus.create({
    id: 'scanAndShow',
    title: '扫描页面PDF',
    contexts: ['page']
  });

  chrome.contextMenus.create({
    id: 'previewPdf',
    title: '预览PDF',
    contexts: ['link']
  });

  // 初始化存储
  chrome.storage.local.get('cloudSettings', (result) => {
    if (!result.cloudSettings) {
      chrome.storage.local.set({ cloudSettings: { apiEndpoint: '', apiToken: '', autoSave: false } });
    }
  });
});

// 右键菜单点击事件
chrome.contextMenus.onClicked.addListener((info, tab) => {
  const linkUrl = info.linkUrl;

  switch (info.menuItemId) {
    case 'downloadPdf':
      // 下载单个PDF
      if (linkUrl && isPdfUrl(linkUrl)) {
        chrome.downloads.download({
          url: linkUrl,
          saveAs: true
        });
      }
      break;

    case 'savePdfToCloud':
      // 保存到云端
      if (linkUrl && isPdfUrl(linkUrl)) {
        savePdfToCloud(linkUrl, tab);
      }
      break;

    case 'downloadAllFromPage':
      // 下载页面所有PDF
      if (tab?.id) {
        chrome.tabs.sendMessage(tab.id, { type: 'GET_PDFS' }, (response) => {
          if (response && response.success && response.data) {
            response.data.forEach((pdf, index) => {
              setTimeout(() => {
                chrome.downloads.download({
                  url: pdf.url,
                  saveAs: false
                });
              }, index * 500); // 间隔500ms避免被阻止
            });
          }
        });
      }
      break;

    case 'scanAndShow':
      // 扫描并显示popup
      if (tab?.id) {
        chrome.tabs.sendMessage(tab.id, { type: 'GET_PDFS' }, (response) => {
          if (response && response.success) {
            // 打开popup
            chrome.action.openPopup();
          }
        });
      }
      break;

    case 'previewPdf':
      // 在新标签页预览PDF
      if (linkUrl && isPdfUrl(linkUrl)) {
        chrome.tabs.create({ url: linkUrl });
      }
      break;
  }
});

// 检查URL是否为PDF
function isPdfUrl(url) {
  if (!url) return false;
  const lower = url.toLowerCase();
  return lower.endsWith('.pdf') || lower.includes('.pdf?') || lower.includes('application/pdf');
}

// 保存PDF到云端
async function savePdfToCloud(pdfUrl, tab) {
  const settings = await getSettings();

  if (!settings.apiEndpoint || !settings.apiToken) {
    // 打开popup让用户配置
    chrome.action.openPopup();
    return;
  }

  try {
    // 获取PDF内容
    const response = await fetch(pdfUrl);
    if (!response.ok) {
      throw new Error(`获取失败: ${response.status}`);
    }

    const blob = await response.blob();
    const filename = pdfUrl.split('/').pop().split('?')[0] || 'document.pdf';

    // 构建FormData
    const formData = new FormData();
    formData.append('file', blob, filename);
    formData.append('title', filename);
    formData.append('sourceUrl', pdfUrl);
    formData.append('pageUrl', tab?.url || '');

    // 上传到云端
    const uploadResponse = await fetch(settings.apiEndpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${settings.apiToken}`
      },
      body: formData
    });

    if (!uploadResponse.ok) {
      throw new Error(`上传失败: ${uploadResponse.status}`);
    }

    // 显示通知
    chrome.notifications.create({
      type: 'basic',
      iconUrl: '../icons/icon48.png',
      title: '上传成功',
      message: filename + ' 已保存到云端'
    });

  } catch (error) {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: '../icons/icon48.png',
      title: '上传失败',
      message: error.message
    });
  }
}

// 获取设置
function getSettings() {
  return new Promise((resolve) => {
    chrome.storage.local.get('cloudSettings', (result) => {
      resolve(result.cloudSettings || {});
    });
  });
}

// 监听标签页更新
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    tabPdfsMap.delete(tabId);
  }
});

chrome.tabs.onActivated.addListener((activeInfo) => {
  tabPdfsMap.delete(activeInfo.tabId);
});

// 消息监听
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const { type, data } = message;
  const tabId = sender.tab?.id;

  switch (type) {
    case 'PDF_FOUND_FROM_NETWORK':
      if (tabId && data) {
        const tabPdfs = tabPdfsMap.get(tabId) || [];
        data.forEach(pdf => {
          if (!tabPdfs.find(p => p.url === pdf.url)) tabPdfs.push(pdf);
        });
        tabPdfsMap.set(tabId, tabPdfs);
      }
      break;

    case 'GET_PDFS_FROM_BACKGROUND':
      if (tabId) sendResponse({ success: true, data: tabPdfsMap.get(tabId) || [] });
      else sendResponse({ success: false, data: [] });
      break;

    case 'DOWNLOAD_PDF':
      if (data?.url) {
        chrome.downloads.download({ url: data.url, filename: data.filename || 'document.pdf' }, (id) => {
          sendResponse({ success: !chrome.runtime.lastError, downloadId: id });
        });
        return true;
      }
      break;
  }
  return false;
});

// 快捷键命令处理
chrome.commands.onCommand.addListener((command) => {
  console.log('[公文PDF助手] 快捷键:', command);

  // 获取当前标签页
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs || tabs.length === 0) return;
    const tab = tabs[0];

    switch (command) {
      case 'scan-page':
        // 扫描页面PDF
        chrome.tabs.sendMessage(tab.id, { type: 'GET_PDFS' }, (response) => {
          if (response && response.success) {
            const count = response.data?.length || 0;
            showNotification('扫描完成', `页面发现 ${count} 个PDF文件`);
          }
        });
        break;

      case 'download-all':
        // 下载页面所有PDF
        chrome.tabs.sendMessage(tab.id, { type: 'GET_PDFS' }, (response) => {
          if (response && response.success && response.data) {
            response.data.forEach((pdf, index) => {
              setTimeout(() => {
                chrome.downloads.download({
                  url: pdf.url,
                  saveAs: false
                });
              }, index * 500);
            });
            showNotification('开始下载', `已添加 ${response.data.length} 个PDF到下载队列`);
          }
        });
        break;
    }
  });
});

// 显示通知
function showNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: '../icons/icon48.png',
    title: title,
    message: message
  });
}

console.log('[公文PDF助手] Background Service Worker 已启动');
