/**
 * 前端公文翻译示例代码
 * 展示如何使用公文翻译 API 进行文档翻译
 */

class DocumentTranslationClient {
  constructor(baseUrl = '/api/v1') {
    this.baseUrl = baseUrl;
  }

  /**
   * 上传文档并创建翻译任务
   * @param {File} file - 文档文件（支持 PDF, TXT, MD）
   * @param {Object} options - 翻译选项
   * @returns {Promise<{translation_id: string, status: string}>}
   */
  async uploadDocument(file, options = {}) {
    const { sourceLanguage = 'auto', targetLanguage = 'zh' } = options;

    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams({
      source_language: sourceLanguage,
      target_language: targetLanguage,
    });

    const response = await fetch(
      `${this.baseUrl}/document-translation/?${params.toString()}`,
      {
        method: 'POST',
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '上传失败');
    }

    const result = await response.json();
    return result.data; // { translation_id, filename, status, message }
  }

  /**
   * 查询翻译状态
   * @param {string} translationId - 翻译任务 ID
   * @returns {Promise<{status: string, message: string}>}
   */
  async getStatus(translationId) {
    const response = await fetch(
      `${this.baseUrl}/document-translation/${translationId}/status`
    );

    if (!response.ok) {
      throw new Error('查询状态失败');
    }

    const result = await response.json();
    return result.data;
  }

  /**
   * 轮询翻译状态直到完成
   * @param {string} translationId - 翻译任务 ID
   * @param {Function} onProgress - 进度回调函数 (status, data) => void
   * @param {number} interval - 轮询间隔（毫秒），默认 3000ms
   * @returns {Promise<Object>} - 完成时的翻译数据
   */
  async pollUntilComplete(translationId, onProgress, interval = 3000) {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await this.getStatus(translationId);

          // 调用进度回调
          if (onProgress) {
            onProgress(status.status, status);
          }

          // 检查状态
          if (status.status === 'completed') {
            // 获取翻译文本
            const textResult = await this.getTranslationText(translationId);
            resolve(textResult);
          } else if (status.status === 'failed') {
            reject(new Error(status.error || '翻译失败'));
          } else {
            // 继续轮询
            setTimeout(poll, interval);
          }
        } catch (error) {
          reject(error);
        }
      };

      // 开始轮询
      poll();
    });
  }

  /**
   * 一站式：上传并等待翻译完成
   * @param {File} file - 文档文件
   * @param {Object} options - 翻译选项
   * @param {Function} onProgress - 进度回调函数
   * @returns {Promise<Object>} - 完成时的翻译数据
   */
  async uploadAndWait(file, options = {}, onProgress) {
    // 1. 上传文档
    const { translation_id } = await this.uploadDocument(file, options);

    if (onProgress) {
      onProgress('pending', { message: '任务已创建' });
    }

    // 2. 轮询状态直到完成
    return this.pollUntilComplete(translation_id, onProgress);
  }

  /**
   * 获取翻译后的文本内容
   * @param {string} translationId - 翻译任务 ID
   * @returns {Promise<{translated_text: string, original_text?: string}>}
   */
  async getTranslationText(translationId) {
    const response = await fetch(
      `${this.baseUrl}/document-translation/${translationId}/text`
    );

    if (!response.ok) {
      throw new Error('获取翻译内容失败');
    }

    const result = await response.json();
    return result.data;
  }

  /**
   * 下载翻译后的文本文件
   * @param {string} translationId - 翻译任务 ID
   */
  async downloadTranslation(translationId) {
    const url = `${this.baseUrl}/document-translation/${translationId}/download`;
    const a = document.createElement('a');
    a.href = url;
    a.download = `translated_${translationId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  /**
   * 获取翻译列表
   * @param {Object} filters - 筛选条件
   * @returns {Promise<Array>} - 翻译任务列表
   */
  async listTranslations(filters = {}) {
    const { page = 1, pageSize = 20, statusFilter } = filters;

    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    if (statusFilter) {
      params.append('status_filter', statusFilter);
    }

    const response = await fetch(
      `${this.baseUrl}/document-translation/?${params.toString()}`
    );

    if (!response.ok) {
      throw new Error('获取翻译列表失败');
    }

    const result = await response.json();
    return result.data;
  }

  /**
   * 删除翻译任务
   * @param {string} translationId - 翻译任务 ID
   */
  async deleteTranslation(translationId) {
    const response = await fetch(
      `${this.baseUrl}/document-translation/${translationId}`,
      {
        method: 'DELETE',
      }
    );

    if (!response.ok) {
      throw new Error('删除翻译任务失败');
    }

    const result = await response.json();
    return result.data;
  }
}

// ==================== 使用示例 ====================

// 示例 1：基本使用
async function basicExample(fileInput) {
  const client = new DocumentTranslationClient();
  const file = fileInput.files[0];

  try {
    // 上传并等待完成
    const translation = await client.uploadAndWait(
      file,
      { sourceLanguage: 'auto', targetLanguage: 'zh' },
      (status, data) => {
        console.log(`状态: ${data.message}`);
        // 更新 UI 显示进度
        updateProgressUI(data);
      }
    );

    console.log('翻译完成！', translation);
    // 显示翻译结果
    showTranslationResult(translation.translated_text);
  } catch (error) {
    console.error('翻译失败:', error);
    showError(error.message);
  }
}

// 示例 2：React 组件示例
function DocumentTranslationComponent() {
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [progress, setProgress] = useState(0);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);
    setTranslatedText('');

    try {
      const client = new DocumentTranslationClient();

      // 上传并轮询状态
      const translation = await client.uploadAndWait(
        file,
        { sourceLanguage: 'auto', targetLanguage: 'zh' },
        (status, data) => {
          setStatus(data.message);
          // 根据状态更新进度条
          if (status === 'pending') setProgress(20);
          else if (status === 'processing') setProgress(60);
          else if (status === 'completed') setProgress(100);
        }
      );

      setTranslatedText(translation.translated_text);
    } catch (error) {
      setStatus(`错误: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (translationId) => {
    const client = new DocumentTranslationClient();
    await client.downloadTranslation(translationId);
  };

  return (
    <div className="document-translation">
      <h2>公文翻译</h2>

      <input
        type="file"
        onChange={handleFileUpload}
        accept=".pdf,.txt,.md"
        disabled={uploading}
      />

      {uploading && (
        <div className="progress-container">
          <p>{status}</p>
          <progress value={progress} max={100} />
        </div>
      )}

      {translatedText && (
        <div className="result-container">
          <h3>翻译结果</h3>
          <div className="translated-text">
            {translatedText.split('\n').map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
          <button onClick={() => navigator.clipboard.writeText(translatedText)}>
            复制文本
          </button>
        </div>
      )}
    </div>
  );
}

// 示例 3：Vue 3 组件示例
/*
<template>
  <div class="document-translation">
    <h2>公文翻译</h2>

    <input
      type="file"
      @change="handleUpload"
      accept=".pdf,.txt,.md"
      :disabled="uploading"
    />

    <div v-if="uploading" class="progress-container">
      <p>{{ statusMessage }}</p>
      <progress :value="progress" max="100"></progress>
    </div>

    <div v-if="translatedText" class="result-container">
      <h3>翻译结果</h3>
      <div class="translated-text">
        <p v-for="(line, i) in translatedText.split('\n')" :key="i">
          {{ line }}
        </p>
      </div>
      <button @click="copyText">复制文本</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const client = new DocumentTranslationClient();
const uploading = ref(false);
const statusMessage = ref('');
const progress = ref(0);
const translatedText = ref('');

const handleUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  uploading.value = true;
  progress.value = 0;
  translatedText.value = '';

  try {
    const translation = await client.uploadAndWait(
      file,
      { sourceLanguage: 'auto', targetLanguage: 'zh' },
      (status, data) => {
        statusMessage.value = data.message;
        if (status === 'pending') progress.value = 20;
        else if (status === 'processing') progress.value = 60;
        else if (status === 'completed') progress.value = 100;
      }
    );

    translatedText.value = translation.translated_text;
  } catch (error) {
    statusMessage.value = `错误: ${error.message}`;
  } finally {
    uploading.value = false;
  }
};

const copyText = () => {
  navigator.clipboard.writeText(translatedText.value);
};
</script>

<style scoped>
.document-translation {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.progress-container {
  margin: 20px 0;
}

.result-container {
  margin-top: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 4px;
}

.translated-text {
  white-space: pre-wrap;
  line-height: 1.8;
  margin-bottom: 15px;
}
</style>
*/

// ==================== 辅助函数 ====================

function updateProgressUI(data) {
  // 更新进度条
  const progressBar = document.getElementById('progress-bar');
  if (progressBar) {
    const progressMap = {
      pending: 20,
      processing: 60,
      completed: 100,
    };
    progressBar.value = progressMap[data.status] || 0;
  }

  // 更新状态文本
  const statusText = document.getElementById('status-text');
  if (statusText) {
    statusText.textContent = data.message;
  }
}

function showTranslationResult(text) {
  const resultDiv = document.getElementById('translation-result');
  if (resultDiv) {
    resultDiv.textContent = text;
    resultDiv.style.display = 'block';
  }
}

function showError(message) {
  const errorDiv = document.getElementById('error-message');
  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
  }
}

// ==================== HTML 示例 ====================

/*
<!DOCTYPE html>
<html>
<head>
  <title>公文翻译示例</title>
  <style>
    .container { max-width: 900px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; }
    .progress { width: 100%; height: 30px; }
    #translation-result {
      margin-top: 20px;
      padding: 15px;
      background: #f5f5f5;
      border-radius: 4px;
      white-space: pre-wrap;
      line-height: 1.8;
      display: none;
    }
    #error-message { color: red; display: none; }
    .button {
      padding: 10px 20px;
      background: #4CAF50;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      margin-top: 10px;
    }
    .button:hover { background: #45a049; }
    .button:disabled { background: #ccc; cursor: not-allowed; }
  </style>
</head>
<body>
  <div class="container">
    <h1>公文翻译</h1>

    <input type="file" id="file-input" accept=".pdf,.txt,.md" />
    <button id="upload-button" class="button">上传并翻译</button>

    <div>
      <p>状态: <span id="status-text">-</span></p>
      <progress id="progress-bar" class="progress" value="0" max="100"></progress>
    </div>

    <div id="error-message"></div>

    <div id="translation-result"></div>

    <button id="copy-button" class="button" style="display: none;">复制翻译结果</button>
  </div>

  <script src="document-translation-client.js"></script>
  <script>
    const client = new DocumentTranslationClient();
    let currentTranslationText = '';

    document.getElementById('upload-button').addEventListener('click', async () => {
      const fileInput = document.getElementById('file-input');
      const file = fileInput.files[0];

      if (!file) {
        alert('请选择文件');
        return;
      }

      const uploadButton = document.getElementById('upload-button');
      uploadButton.disabled = true;
      uploadButton.textContent = '翻译中...';

      try {
        const translation = await client.uploadAndWait(
          file,
          { sourceLanguage: 'auto', targetLanguage: 'zh' },
          (status, data) => {
            document.getElementById('status-text').textContent = data.message;
          }
        );

        currentTranslationText = translation.translated_text;
        document.getElementById('translation-result').textContent = translation.translated_text;
        document.getElementById('translation-result').style.display = 'block';
        document.getElementById('copy-button').style.display = 'inline-block';
      } catch (error) {
        document.getElementById('error-message').textContent = error.message;
        document.getElementById('error-message').style.display = 'block';
      } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = '上传并翻译';
      }
    });

    document.getElementById('copy-button').addEventListener('click', () => {
      navigator.clipboard.writeText(currentTranslationText);
      alert('已复制到剪贴板');
    });
  </script>
</body>
</html>
*/

// 导出到全局（用于浏览器环境）
if (typeof window !== 'undefined') {
  window.DocumentTranslationClient = DocumentTranslationClient;
}
