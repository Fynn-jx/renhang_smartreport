const pdfList = document.getElementById('pdfList');
const emptyState = document.getElementById('emptyState');
const loadingState = document.getElementById('loadingState');
const pdfCount = document.getElementById('pdfCount');
const pageUrl = document.getElementById('pageUrl');
const downloadAllBtn = document.getElementById('downloadAllBtn');
const saveToCloudBtn = document.getElementById('saveToCloudBtn');
const refreshBtn = document.getElementById('refreshBtn');
const selectAllBtn = document.getElementById('selectAllBtn');
const selectedCount = document.getElementById('selectedCount');

// 云端配置（按照 STORAGE_ARCHITECTURE.md）
const CLOUD_CONFIG = {
  apiEndpoint: 'http://localhost:8000/api/v1/documents/',
  apiToken: 'dev-token-for-localhost'
};

let currentPdfs = [];
let currentTabId = null;
let selectedPdfs = new Set();

document.addEventListener('DOMContentLoaded', async () => {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tabs.length > 0) {
    currentTabId = tabs[0].id;
    pageUrl.textContent = truncateUrl(tabs[0].url);
  }
  await loadPdfs();
  bindEvents();
});

function bindEvents() {
  refreshBtn.addEventListener('click', loadPdfs);
  downloadAllBtn.addEventListener('click', downloadSelected);
  saveToCloudBtn.addEventListener('click', saveSelectedToCloud);
  selectAllBtn.addEventListener('click', toggleSelectAll);
}


async function loadPdfs() {
  showLoading(true);
  try {
    if (!currentTabId) throw new Error('无法获取标签页');

    let response;
    try {
      response = await chrome.tabs.sendMessage(currentTabId, { type: 'GET_PDFS' });
    } catch (e) {
      // Content script 可能还没加载，重试一次
      await new Promise(r => setTimeout(r, 500));
      response = await chrome.tabs.sendMessage(currentTabId, { type: 'GET_PDFS' });
    }

    if (response && response.success) {
      currentPdfs = response.data || [];
    } else {
      // Fallback: 从storage获取，但只获取当前页面的PDF
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      const currentUrl = tabs[0]?.url || '';
      const stored = await chrome.storage.local.get('discoveredPdfs');
      const allPdfs = stored.discoveredPdfs || [];
      // 过滤当前页面的PDF
      currentPdfs = allPdfs.filter(pdf => !pdf.pageUrl || pdf.pageUrl === currentUrl);
    }
    selectedPdfs.clear();
    renderPdfs();
  } catch (error) {
    console.error('获取PDF列表失败:', error);
    currentPdfs = [];
    renderPdfs();
  }
}

function toggleSelectAll() {
  if (selectedPdfs.size === currentPdfs.length) {
    selectedPdfs.clear();
    selectAllBtn.textContent = '全选';
  } else {
    selectedPdfs = new Set(currentPdfs.map((_, i) => i));
    selectAllBtn.textContent = '取消全选';
  }
  updateSelectionUI();
}

function updateSelectionUI() {
  const count = selectedPdfs.size;
  selectedCount.textContent = count > 0 ? `已选 ${count} 个` : '';
  downloadAllBtn.disabled = count === 0;
  saveToCloudBtn.disabled = count === 0;
  selectAllBtn.textContent = count === currentPdfs.length ? '取消全选' : '全选';

  // 更新复选框状态
  document.querySelectorAll('.pdf-checkbox').forEach((cb, i) => {
    cb.checked = selectedPdfs.has(i);
  });
}

function renderPdfs() {
  showLoading(false);
  pdfCount.textContent = currentPdfs.length === 0 ? '未发现PDF' : `发现 ${currentPdfs.length} 个PDF`;
  downloadAllBtn.disabled = selectedPdfs.size === 0;
  saveToCloudBtn.disabled = selectedPdfs.size === 0;

  // 显示/隐藏选择栏
  const selectionBar = document.getElementById('selectionBar');
  selectionBar.style.display = currentPdfs.length > 0 ? 'flex' : 'none';

  pdfList.innerHTML = '';

  if (currentPdfs.length === 0) {
    emptyState.classList.add('show');
    return;
  }
  emptyState.classList.remove('show');

  currentPdfs.forEach((pdf, index) => {
    const li = document.createElement('li');
    li.className = 'pdf-item';
    li.innerHTML = `
      <input type="checkbox" class="pdf-checkbox" data-index="${index}" ${selectedPdfs.has(index) ? 'checked' : ''}>
      <div class="pdf-icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM8.5 13c-.83 0-1.5.67-1.5 1.5S7.67 16 8.5 16s1.5-.67 1.5-1.5S9.33 13 8.5 13zm5 0c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5 1.5-.67 1.5-1.5-.67-1.5-1.5-1.5z"/></svg></div>
      <div class="pdf-info">
        <div class="pdf-title-wrapper">
          <span class="pdf-title" data-index="${index}" title="点击修改标题">${escapeHtml(pdf.title)}</span>
          <input type="text" class="pdf-title-input" data-index="${index}" value="${escapeHtml(pdf.title)}" style="display:none;">
        </div>
        <div class="pdf-url" title="${escapeHtml(pdf.url)}">${escapeHtml(truncateUrl(pdf.url))}</div>
      </div>
      <div class="pdf-actions">
        <button class="btn-sm btn-preview" data-index="${index}" title="预览">预览</button>
        <button class="btn-sm btn-download" data-index="${index}">本地</button>
        <button class="btn-sm btn-cloud" data-index="${index}">报告库</button>
        <button class="btn-sm btn-remove" data-index="${index}" title="移除">×</button>
      </div>
    `;

    // 复选框事件
    li.querySelector('.pdf-checkbox').addEventListener('change', (e) => {
      if (e.target.checked) {
        selectedPdfs.add(index);
      } else {
        selectedPdfs.delete(index);
      }
      updateSelectionUI();
    });

    // 标题点击编辑
    const titleSpan = li.querySelector('.pdf-title');
    const titleInput = li.querySelector('.pdf-title-input');

    titleSpan.addEventListener('click', () => {
      titleSpan.style.display = 'none';
      titleInput.style.display = 'inline';
      titleInput.focus();
      titleInput.select();
    });

    titleInput.addEventListener('blur', () => {
      const newTitle = titleInput.value.trim() || pdf.title;
      pdf.title = newTitle;
      titleSpan.textContent = newTitle;
      titleSpan.style.display = 'inline';
      titleInput.style.display = 'none';
    });

    titleInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        titleInput.blur();
      } else if (e.key === 'Escape') {
        titleInput.value = pdf.title;
        titleInput.blur();
      }
    });

    li.querySelector('.btn-preview').addEventListener('click', () => previewPdf(pdf));
    li.querySelector('.btn-download').addEventListener('click', () => downloadPdf(pdf));
    li.querySelector('.btn-cloud').addEventListener('click', () => saveToCloud(pdf));
    li.querySelector('.btn-remove').addEventListener('click', () => removePdf(index));
    pdfList.appendChild(li);
  });

  updateSelectionUI();
}

// 移除PDF
async function removePdf(index) {
  const pdf = currentPdfs[index];
  if (!pdf) return;

  try {
    // 通知content script移除
    await chrome.tabs.sendMessage(currentTabId, { type: 'REMOVE_PDF', url: pdf.url });
  } catch (e) {
    // Content script可能未加载，忽略错误
  }

  // 从列表移除
  currentPdfs.splice(index, 1);
  // 更新storage
  const allStored = await chrome.storage.local.get('discoveredPdfs');
  const filtered = (allStored.discoveredPdfs || []).filter(p => p.url !== pdf.url);
  await chrome.storage.local.set({ 'discoveredPdfs': filtered });

  // 更新选择状态
  selectedPdfs.clear();
  renderPdfs();
  showToast('已移除: ' + pdf.title, 'success');
}

// PDF预览 - 使用新标签页打开，避免CORS问题
function previewPdf(pdf) {
  // 强制在新标签页打开，避免浏览器复用tab
  chrome.tabs.create({ url: pdf.url, active: true });
}

async function downloadPdf(pdf) {
  if (!chrome.downloads) {
    // Safari 等不支持 chrome.downloads 的浏览器，使用新标签页方式触发下载
    chrome.tabs.create({ url: pdf.url });
    showToast('开始下载: ' + pdf.title, 'success');
    return;
  }
  try {
    await chrome.downloads.download({ url: pdf.url, filename: sanitizeFilename(pdf.title) + '.pdf', saveAs: true });
    showToast('开始下载: ' + pdf.title, 'success');
  } catch (error) {
    showToast('下载失败: ' + error.message, 'error');
  }
}

async function downloadSelected() {
  if (selectedPdfs.size === 0) return;
  const selected = Array.from(selectedPdfs).map(i => currentPdfs[i]);
  if (!chrome.downloads) {
    for (const pdf of selected) {
      chrome.tabs.create({ url: pdf.url });
    }
    showToast(`已打开 ${selected.length} 个PDF`, 'success');
    return;
  }
  for (const pdf of selected) {
    try {
      await chrome.downloads.download({ url: pdf.url, filename: sanitizeFilename(pdf.title) + '.pdf', saveAs: false });
    } catch (e) {}
  }
  showToast(`已添加 ${selected.length} 个文件到下载队列`, 'success');
}

async function saveToCloud(pdf) {
  try {
    console.log('正在获取PDF:', pdf.url);
    const response = await fetch(pdf.url);
    console.log('获取PDF响应:', response.status, response.statusText);
    if (!response.ok) throw new Error(`获取文件失败: ${response.status} ${response.statusText}`);
    const blob = await response.blob();
    console.log('PDF大小:', blob.size);
    const formData = new FormData();
    formData.append('file', blob, pdf.title + '.pdf');
    formData.append('title', pdf.title);
    formData.append('source_url', pdf.url);
    console.log('正在上传到:', CLOUD_CONFIG.apiEndpoint);
    const uploadResponse = await fetch(CLOUD_CONFIG.apiEndpoint, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${CLOUD_CONFIG.apiToken}` },
      body: formData
    });
    console.log('上传响应:', uploadResponse.status, uploadResponse.statusText);
    const result = await uploadResponse.text();
    console.log('上传结果:', result);
    if (!uploadResponse.ok) throw new Error(`上传失败: ${uploadResponse.status} - ${result}`);
    showToast('上传成功: ' + pdf.title, 'success');
  } catch (error) {
    console.error('上传失败:', error);
    showToast('上传失败: ' + error.message, 'error');
  }
}

async function saveSelectedToCloud() {
  if (selectedPdfs.size === 0) return;
  const selected = Array.from(selectedPdfs).map(i => currentPdfs[i]);
  let success = 0, fail = 0;
  for (const pdf of selected) {
    try {
      const response = await fetch(pdf.url);
      if (!response.ok) { fail++; continue; }
      const blob = await response.blob();
      const formData = new FormData();
      formData.append('file', blob, pdf.title + '.pdf');
      formData.append('title', pdf.title);
      formData.append('source_url', pdf.url);
      const uploadResponse = await fetch(CLOUD_CONFIG.apiEndpoint, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${CLOUD_CONFIG.apiToken}` },
        body: formData
      });
      if (uploadResponse.ok) success++; else fail++;
    } catch (e) { fail++; }
  }
  showToast(`完成: ${success} 成功, ${fail} 失败`, 'success');
}

function showLoading(show) {
  if (show) {
    loadingState.classList.add('show');
    emptyState.classList.remove('show');
    pdfList.innerHTML = '';
  } else {
    loadingState.classList.remove('show');
  }
}

function showToast(message, type = 'info') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.classList.add('show'), 10);
  setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, 3000);
}

function truncateUrl(url, maxLength = 40) {
  if (!url) return '';
  return url.length <= maxLength ? url : '...' + url.substring(url.length - maxLength);
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function sanitizeFilename(name) {
  if (!name) return 'document';
  return name.replace(/[\\/:*?"<>|]/g, '_').replace(/\s+/g, '_').substring(0, 100);
}
