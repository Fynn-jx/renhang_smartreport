/**
 * content.js - 网页PDF嗅探器
 *
 * 功能：
 * 1. 扫描页面中所有 <a> 标签，提取 .pdf 链接
 * 2. 扫描 <embed> 和 <iframe> 标签的 PDF
 * 3. 去重机制，确保同一 PDF 只记录一次
 * 4. 将结果通过 chrome.runtime.sendMessage 发送给 popup 或 background
 */

const discoveredPdfs = new Map(); // url -> pdf object

function resolveUrl(url, baseUrl) {
  try {
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('//')) {
      return url.startsWith('//') ? window.location.protocol + url : url;
    }
    if (url.startsWith('/')) {
      return new URL(url, baseUrl).href;
    }
    return new URL(url, baseUrl).href;
  } catch (e) {
    return url;
  }
}

function isPdfUrl(url) {
  if (!url) return false;
  const lowerUrl = url.toLowerCase();
  return lowerUrl.endsWith('.pdf') || lowerUrl.includes('.pdf?') || lowerUrl.includes('.pdf#') || lowerUrl.includes('application/pdf');
}

function extractFromAnchorTags() {
  const anchors = document.querySelectorAll('a[href]');
  const results = [];

  anchors.forEach((anchor, index) => {
    const href = anchor.getAttribute('href');
    if (isPdfUrl(href)) {
      const absoluteUrl = resolveUrl(href, window.location.href);
      const title = anchor.textContent.trim() || anchor.innerText.trim() || `PDF文档_${index + 1}`;

      results.push({
        url: absoluteUrl,
        title: title.substring(0, 200),
        source: 'anchor',
        pageUrl: window.location.href,
        foundAt: new Date().toISOString()
      });
    }
  });

  return results;
}

function extractFromEmbedIframe() {
  const results = [];
  const selectors = ['embed[type="application/pdf"]', 'embed[src$=".pdf"]',
                     'iframe[type="application/pdf"]', 'iframe[src$=".pdf"]',
                     'object[type="application/pdf"]', 'object[data$=".pdf"]'];

  selectors.forEach(selector => {
    document.querySelectorAll(selector).forEach((el, index) => {
      let url = el.getAttribute('src') || el.getAttribute('data');
      if (url && isPdfUrl(url)) {
        const absoluteUrl = resolveUrl(url, window.location.href);
        const title = el.getAttribute('title') || el.getAttribute('name') || `嵌入PDF_${index + 1}`;

        results.push({
          url: absoluteUrl,
          title: title.substring(0, 200),
          source: 'embed_iframe',
          pageUrl: window.location.href,
          foundAt: new Date().toISOString()
        });
      }
    });
  });

  return results;
}

// 从storage恢复已发现的PDF
async function restoreFromStorage() {
  return new Promise((resolve) => {
    chrome.storage.local.get('discoveredPdfs', (result) => {
      if (result.discoveredPdfs && result.discoveredPdfs.length > 0) {
        // 只恢复当前页面的PDF
        const currentPagePdfs = result.discoveredPdfs.filter(
          pdf => !pdf.pageUrl || pdf.pageUrl === window.location.href
        );
        currentPagePdfs.forEach(pdf => discoveredPdfs.set(pdf.url, pdf));
        resolve(currentPagePdfs);
      } else {
        resolve([]);
      }
    });
  });
}

function scanForPdfs() {
  const allPdfs = [];

  const fromAnchors = extractFromAnchorTags();
  fromAnchors.forEach(pdf => {
    if (!discoveredPdfs.has(pdf.url)) {
      discoveredPdfs.set(pdf.url, pdf);
      allPdfs.push(pdf);
    }
  });

  const fromEmbeds = extractFromEmbedIframe();
  fromEmbeds.forEach(pdf => {
    if (!discoveredPdfs.has(pdf.url)) {
      discoveredPdfs.set(pdf.url, pdf);
      allPdfs.push(pdf);
    }
  });

  return allPdfs;
}

(async function autoScan() {
  // 先从storage恢复
  await restoreFromStorage();

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scanAndReport);
  } else {
    setTimeout(scanAndReport, 1000);
  }
})();

function scanAndReport() {
  const pdfs = scanForPdfs();
  console.log(`[PDF嗅探器] 在页面中发现 ${pdfs.length} 个 PDF 文件，当前页面: ${window.location.href}`);

  // 保存所有已发现的PDF到storage（合并新旧PDF）
  const allPdfs = Array.from(discoveredPdfs.values());
  chrome.storage.local.set({ 'discoveredPdfs': allPdfs }, () => {});
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_PDFS') {
    // 返回当前页面所有已发现的PDF
    const pdfs = Array.from(discoveredPdfs.values());
    sendResponse({ success: true, data: pdfs });
  } else if (message.type === 'REMOVE_PDF') {
    // 从列表中移除指定的PDF
    const urlToRemove = message.url;
    if (discoveredPdfs.has(urlToRemove)) {
      discoveredPdfs.delete(urlToRemove);
      // 更新storage
      const allPdfs = Array.from(discoveredPdfs.values());
      chrome.storage.local.set({ 'discoveredPdfs': allPdfs }, () => {
        sendResponse({ success: true });
      });
    } else {
      sendResponse({ success: true });
    }
    return true;
  }
  return true;
});

window.pdfScanner = {
  scan: scanForPdfs,
  getDiscovered: () => Array.from(discoveredPdfs.values())
};
