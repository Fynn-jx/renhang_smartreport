/**
 * 前端异步图片转译示例代码
 * 展示如何使用新的异步 API 进行图片转译和状态轮询
 */

class ImageTranslationClient {
  constructor(baseUrl = '/api/v1') {
    this.baseUrl = baseUrl;
  }

  /**
   * 上传图片并创建转译任务
   * @param {File} file - 图片文件
   * @returns {Promise<{translation_id: string, status: string}>}
   */
  async uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/image-translation/`, {
      method: 'POST',
      body: formData,
      // 不需要设置 Content-Type，浏览器会自动设置 multipart/form-data
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '上传失败');
    }

    const result = await response.json();
    return result.data; // { translation_id, filename, status, message }
  }

  /**
   * 查询转译状态
   * @param {string} translationId - 转译任务 ID
   * @returns {Promise<{status: string, message: string, preview_url?: string}>}
   */
  async getStatus(translationId) {
    const response = await fetch(
      `${this.baseUrl}/image-translation/${translationId}/status`
    );

    if (!response.ok) {
      throw new Error('查询状态失败');
    }

    const result = await response.json();
    return result.data;
  }

  /**
   * 轮询转译状态直到完成
   * @param {string} translationId - 转译任务 ID
   * @param {Function} onProgress - 进度回调函数 (status, data) => void
   * @param {number} interval - 轮询间隔（毫秒），默认 2000ms
   * @returns {Promise<string>} - 完成时的预览 URL
   */
  async pollUntilComplete(translationId, onProgress, interval = 2000) {
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
            resolve(status.preview_url);
          } else if (status.status === 'failed') {
            reject(new Error(status.error || '转译失败'));
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
   * 一站式：上传并等待转译完成
   * @param {File} file - 图片文件
   * @param {Function} onProgress - 进度回调函数
   * @returns {Promise<string>} - 完成时的预览 URL
   */
  async uploadAndWait(file, onProgress) {
    // 1. 上传图片
    const { translation_id } = await this.uploadImage(file);

    if (onProgress) {
      onProgress('pending', { message: '任务已创建' });
    }

    // 2. 轮询状态直到完成
    return this.pollUntilComplete(translation_id, onProgress);
  }

  /**
   * 获取转译后的图片 URL（用于预览）
   * @param {string} translationId - 转译任务 ID
   * @returns {string} - 图片 URL
   */
  getPreviewUrl(translationId) {
    return `${this.baseUrl}/image-translation/${translationId}/preview`;
  }

  /**
   * 获取下载 URL
   * @param {string} translationId - 转译任务 ID
   * @returns {string} - 下载 URL
   */
  getDownloadUrl(translationId) {
    return `${this.baseUrl}/image-translation/${translationId}/download`;
  }

  /**
   * 下载转译后的图片
   * @param {string} translationId - 转译任务 ID
   * @param {string} filename - 保存的文件名
   */
  async downloadImage(translationId, filename) {
    const url = this.getDownloadUrl(translationId);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `translated_${translationId}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
}

// ==================== 使用示例 ====================

// 示例 1：基本使用
async function basicExample(fileInput) {
  const client = new ImageTranslationClient();
  const file = fileInput.files[0];

  try {
    // 上传并等待完成
    const previewUrl = await client.uploadAndWait(file, (status, data) => {
      console.log(`状态: ${data.message}`);
      // 更新 UI 显示进度
      updateProgressUI(data);
    });

    console.log('转译完成！', previewUrl);
    // 显示图片
    showPreviewImage(previewUrl);
  } catch (error) {
    console.error('转译失败:', error);
    showError(error.message);
  }
}

// 示例 2：React 组件示例
function ImageTranslationComponent() {
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState('');
  const [previewUrl, setPreviewUrl] = useState('');
  const [progress, setProgress] = useState(0);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);

    try {
      const client = new ImageTranslationClient();

      // 上传并轮询状态
      const url = await client.uploadAndWait(file, (status, data) => {
        setStatus(data.message);
        // 根据状态更新进度条
        if (status === 'pending') setProgress(20);
        else if (status === 'processing') setProgress(60);
        else if (status === 'completed') setProgress(100);
      });

      setPreviewUrl(url);
    } catch (error) {
      setStatus(`错误: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        onChange={handleFileUpload}
        accept="image/*"
        disabled={uploading}
      />

      {uploading && (
        <div>
          <p>{status}</p>
          <progress value={progress} max={100} />
        </div>
      )}

      {previewUrl && (
        <div>
          <h3>转译结果</h3>
          <img src={previewUrl} alt="转译后的图片" />
          <a href={previewUrl} download="translated.png">
            下载图片
          </a>
        </div>
      )}
    </div>
  );
}

// 示例 3：Vue 3 组件示例
/*
<template>
  <div>
    <input type="file" @change="handleUpload" accept="image/*" :disabled="uploading" />

    <div v-if="uploading">
      <p>{{ statusMessage }}</p>
      <progress :value="progress" max="100"></progress>
    </div>

    <div v-if="previewUrl">
      <h3>转译结果</h3>
      <img :src="previewUrl" alt="转译后的图片" />
      <a :href="previewUrl" download="translated.png">下载图片</a>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const client = new ImageTranslationClient();
const uploading = ref(false);
const statusMessage = ref('');
const progress = ref(0);
const previewUrl = ref('');

const handleUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  uploading.value = true;
  progress.value = 0;

  try {
    const url = await client.uploadAndWait(file, (status, data) => {
      statusMessage.value = data.message;
      if (status === 'pending') progress.value = 20;
      else if (status === 'processing') progress.value = 60;
      else if (status === 'completed') progress.value = 100;
    });

    previewUrl.value = url;
  } catch (error) {
    statusMessage.value = `错误: ${error.message}`;
  } finally {
    uploading.value = false;
  }
};
</script>
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

function showPreviewImage(url) {
  const img = document.getElementById('preview-image');
  if (img) {
    img.src = url;
    img.style.display = 'block';
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
  <title>图片转译示例</title>
  <style>
    .container { max-width: 800px; margin: 0 auto; padding: 20px; }
    .progress { width: 100%; height: 30px; }
    #preview-image { max-width: 100%; margin-top: 20px; }
    #error-message { color: red; display: none; }
  </style>
</head>
<body>
  <div class="container">
    <h1>图片转译</h1>

    <input type="file" id="file-input" accept="image/*" />
    <button onclick="handleUpload()">上传并转译</button>

    <div>
      <p>状态: <span id="status-text">-</span></p>
      <progress id="progress-bar" class="progress" value="0" max="100"></progress>
    </div>

    <div id="error-message"></div>

    <img id="preview-image" style="display: none;" />

    <div id="result" style="display: none;">
      <a id="download-link" download="translated.png">下载图片</a>
    </div>
  </div>

  <script src="image-translation-client.js"></script>
  <script>
    const client = new ImageTranslationClient();

    async function handleUpload() {
      const fileInput = document.getElementById('file-input');
      const file = fileInput.files[0];

      if (!file) {
        alert('请选择文件');
        return;
      }

      try {
        const url = await client.uploadAndWait(file, (status, data) => {
          document.getElementById('status-text').textContent = data.message;
        });

        document.getElementById('preview-image').src = url;
        document.getElementById('preview-image').style.display = 'block';
        document.getElementById('download-link').href = url;
        document.getElementById('result').style.display = 'block';
      } catch (error) {
        document.getElementById('error-message').textContent = error.message;
        document.getElementById('error-message').style.display = 'block';
      }
    }
  </script>
</body>
</html>
*/

// 导出到全局（用于浏览器环境）
if (typeof window !== 'undefined') {
  window.ImageTranslationClient = ImageTranslationClient;
}
