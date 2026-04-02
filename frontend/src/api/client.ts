/**
 * API 客户端 - 封装所有后端 API 请求
 */

import type {
  Document,
  DocumentListResponse,
  DocumentUploadResponse,
  DocumentUploadParams,
  ApiResponse,
  PaginationParams,
  Task,
  ResearchParams,
  DocumentTranslationParams,
  DocumentTranslationUploadResponse,
  DocumentTranslationStatusResponse,
  Country,
  CountryDetail,
  WorkflowStagesResponse,
  CountryResearchParams,
  QuarterlyReportParams,
  ImageTranslation,
  ImageTranslationUploadResponse,
  ImageTranslationStatusResponse,
  ImageTranslationParams,
} from "./types";

// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

// 获取完整 API URL
const getApiUrl = (path: string): string => `${API_BASE_URL}${API_PREFIX}${path}`;

// 获取认证 Token（从 localStorage 获取）
const getAuthToken = (): string => {
  return localStorage.getItem("auth_token") || "";
};

// 通用请求函数
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = getApiUrl(endpoint);

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // 添加认证 Token（如果有）
  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      // 禁用缓存，确保获取最新数据
      cache: "no-store",
    });

    // 处理 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    // 解析 JSON
    const data = await response.json();

    // 检查错误
    if (!response.ok) {
      throw new Error(data.detail || data.message || `请求失败: ${response.status}`);
    }

    // 返回 data 字段（如果存在）
    return (data as ApiResponse<T>).data ?? data;
  } catch (error) {
    console.error("API 请求错误:", error);
    throw error;
  }
}

// 上传文件的请求函数
async function uploadRequest<T>(
  endpoint: string,
  formData: FormData
): Promise<T> {
  const url = getApiUrl(endpoint);

  const headers: HeadersInit = {};

  // 添加认证 Token（如果有）
  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || data.message || `上传失败: ${response.status}`);
    }

    return (data as ApiResponse<T>).data ?? data;
  } catch (error) {
    console.error("文件上传错误:", error);
    throw error;
  }
}

// ==================== 文档 API ====================

/**
 * 获取文档列表
 */
export async function fetchDocuments(params?: PaginationParams): Promise<DocumentListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.append("page", params.page.toString());
  if (params?.page_size) queryParams.append("page_size", params.page_size.toString());
  if (params?.keyword) queryParams.append("keyword", params.keyword);
  if (params?.sort_by) queryParams.append("sort_by", params.sort_by);
  if (params?.sort_order) queryParams.append("sort_order", params.sort_order);

  const queryString = queryParams.toString();
  return request<DocumentListResponse>(`/documents/${queryString ? `?${queryString}` : ""}`);
}

/**
 * 获取单个文档详情
 */
export async function fetchDocument(id: string): Promise<Document> {
  return request<Document>(`/documents/${id}`);
}

/**
 * 上传文档
 */
export async function uploadDocument(params: DocumentUploadParams): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", params.file);
  formData.append("title", params.title);
  if (params.author) formData.append("author", params.author);
  if (params.subject) formData.append("subject", params.subject);
  if (params.keywords) formData.append("keywords", params.keywords);
  if (params.tag_ids) formData.append("tag_ids", params.tag_ids);
  if (params.source_url) formData.append("source_url", params.source_url);
  if (params.is_shared !== undefined) formData.append("is_shared", params.is_shared.toString());

  return uploadRequest<DocumentUploadResponse>("/documents/", formData);
}

/**
 * 删除文档
 */
export async function deleteDocument(id: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/documents/${id}`, {
    method: "DELETE",
  });
}

/**
 * 获取文档内容
 */
export async function fetchDocumentContent(id: string): Promise<{
  content: string;
  content_preview: string;
  page_count: number;
}> {
  return request(`/documents/${id}/content`);
}

// ==================== 任务 API ====================

/**
 * 创建翻译任务
 */
export async function createTranslateTask(documentId: string, model: string): Promise<Task> {
  return request<Task>("/tasks/", {
    method: "POST",
    body: JSON.stringify({
      task_type: "translate",
      document_id: documentId,
      config: { model },
    }),
  });
}

/**
 * 创建公文写作任务
 */
export async function createWriteTask(documentId: string, model: string): Promise<Task> {
  return request<Task>("/tasks/", {
    method: "POST",
    body: JSON.stringify({
      task_type: "write",
      document_id: documentId,
      config: { model },
    }),
  });
}

/**
 * 获取任务状态
 */
export async function fetchTaskStatus(taskId: string): Promise<Task> {
  return request<Task>(`/tasks/${taskId}`);
}

// ==================== 工作流 API ====================

/**
 * 启动国别研究工作流
 */
export async function startResearchWorkflow(params: ResearchParams): Promise<Task> {
  return request<Task>("/workflows/research", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

// ==================== 健康检查 ====================

/**
 * 健康检查
 */
export async function healthCheck(): Promise<{ status: string; service: string; version: string }> {
  return request("/health");
}

// ==================== 文档翻译 API ====================

/**
 * 创建文档翻译任务（上传文件或使用已有文档）
 */
export async function createDocumentTranslation(params: DocumentTranslationParams): Promise<DocumentTranslationUploadResponse> {
  const formData = new FormData();

  if (params.file) {
    formData.append("file", params.file);
  }
  if (params.document_id) {
    formData.append("document_id", params.document_id);
  }
  if (params.source_language) {
    formData.append("source_language", params.source_language);
  }
  if (params.target_language) {
    formData.append("target_language", params.target_language);
  }

  return uploadRequest<DocumentTranslationUploadResponse>("/document-translation/", formData);
}

/**
 * 获取文档翻译状态（用于轮询）
 */
export async function fetchDocumentTranslationStatus(translationId: string): Promise<DocumentTranslationStatusResponse> {
  return request<DocumentTranslationStatusResponse>(`/document-translation/${translationId}/status`);
}

/**
 * 下载翻译后的 Word 文档
 */
export async function downloadTranslationWord(translationId: string): Promise<void> {
  const url = getApiUrl(`/document-translation/${translationId}/download-word`);
  const token = getAuthToken();

  const response = await fetch(url, {
    headers: token ? { "Authorization": `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    throw new Error(`下载失败: ${response.status}`);
  }

  // 从响应头获取文件名
  const contentDisposition = response.headers.get("Content-Disposition");
  let filename = "translation.docx";
  if (contentDisposition) {
    const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    if (match && match[1]) {
      filename = match[1].replace(/['"]/g, "");
    }
  }

  // 下载文件
  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(blobUrl);
}

// ==================== 国别研究 API ====================

/**
 * 获取所有已注册的国家列表
 */
export async function fetchCountries(): Promise<{ countries: Country[] }> {
  return request<{ countries: Country[] }>("/workflows/country-research/countries");
}

/**
 * 获取指定国家的详细配置
 */
export async function fetchCountryDetail(countryCode: string): Promise<CountryDetail> {
  return request<CountryDetail>(`/workflows/country-research/countries/${countryCode}`);
}

/**
 * 获取国别研究工作流的所有阶段信息
 */
export async function fetchCountryResearchStages(): Promise<WorkflowStagesResponse> {
  return request<WorkflowStagesResponse>("/workflows/country-research/stages");
}

/**
 * 启动国别研究工作流（SSE 流式响应）
 * 返回 ReadableStream，需要调用方处理 SSE 事件
 */
export async function startCountryResearch(params: CountryResearchParams): Promise<ReadableStream> {
  const url = getApiUrl("/workflows/country-research");
  const token = getAuthToken();

  const formData = new FormData();
  formData.append("country_code", params.country_code);
  if (params.reference_file) {
    formData.append("reference_file", params.reference_file);
  }
  if (params.user_sources) {
    formData.append("user_sources", params.user_sources);
  }

  const response = await fetch(url, {
    method: "POST",
    headers: token ? { "Authorization": `Bearer ${token}` } : {},
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `请求失败: ${response.status}`);
  }

  if (!response.body) {
    throw new Error("无法读取响应流");
  }

  return response.body;
}

// ==================== 季度报告 API ====================

/**
 * 获取季度报告工作流的所有阶段信息
 */
export async function fetchQuarterlyReportStages(): Promise<WorkflowStagesResponse> {
  return request<WorkflowStagesResponse>("/workflows/quarterly-report/stages");
}

/**
 * 启动季度报告工作流（SSE 流式响应）
 * 返回 ReadableStream，需要调用方处理 SSE 事件
 */
export async function startQuarterlyReport(params: QuarterlyReportParams): Promise<ReadableStream> {
  const url = getApiUrl("/workflows/quarterly-report");
  const token = getAuthToken();

  const formData = new FormData();
  formData.append("country_code", params.country_code);
  if (params.reference_file) {
    formData.append("reference_file", params.reference_file);
  }
  if (params.user_sources) {
    formData.append("user_sources", params.user_sources);
  }

  const response = await fetch(url, {
    method: "POST",
    headers: token ? { "Authorization": `Bearer ${token}` } : {},
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `请求失败: ${response.status}`);
  }

  if (!response.body) {
    throw new Error("无法读取响应流");
  }

  return response.body;
}

// ==================== 图片转译 API ====================

/**
 * 上传图片并进行转译
 */
export async function uploadImageForTranslation(params: ImageTranslationParams): Promise<ImageTranslationUploadResponse> {
  const formData = new FormData();
  formData.append("file", params.file);

  return uploadRequest<ImageTranslationUploadResponse>("/image-translation/", formData);
}

/**
 * 获取图片转译列表
 */
export async function fetchImageTranslations(page?: number, pageSize?: number, statusFilter?: string): Promise<ImageTranslation[]> {
  const queryParams = new URLSearchParams();
  if (page) queryParams.append("page", page.toString());
  if (pageSize) queryParams.append("page_size", pageSize.toString());
  if (statusFilter) queryParams.append("status_filter", statusFilter);

  const queryString = queryParams.toString();
  return request<ImageTranslation[]>(`/image-translation/${queryString ? `?${queryString}` : ""}`);
}

/**
 * 获取单个图片转译详情
 */
export async function fetchImageTranslation(translationId: string): Promise<ImageTranslation> {
  return request<ImageTranslation>(`/image-translation/${translationId}`);
}

/**
 * 查询图片转译状态（用于轮询）
 */
export async function fetchImageTranslationStatus(translationId: string): Promise<ImageTranslationStatusResponse> {
  return request<ImageTranslationStatusResponse>(`/image-translation/${translationId}/status`);
}

/**
 * 预览转译后的图片
 * 返回图片URL
 */
export function getImagePreviewUrl(translationId: string): string {
  return getApiUrl(`/image-translation/${translationId}/preview`);
}

/**
 * 下载转译后的图片
 */
export async function downloadTranslatedImage(translationId: string, filename?: string): Promise<void> {
  const url = getApiUrl(`/image-translation/${translationId}/download`);
  const token = getAuthToken();

  const response = await fetch(url, {
    headers: token ? { "Authorization": `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    throw new Error(`下载失败: ${response.status}`);
  }

  // 从响应头获取文件名
  const contentDisposition = response.headers.get("Content-Disposition");
  let downloadFilename = filename || "translated_image.jpg";
  if (contentDisposition) {
    const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    if (match && match[1]) {
      downloadFilename = match[1].replace(/['"]/g, "");
    }
  }

  // 下载文件
  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = downloadFilename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(blobUrl);
}

/**
 * 下载原始图片
 */
export async function downloadOriginalImage(translationId: string): Promise<void> {
  const url = getApiUrl(`/image-translation/${translationId}/original`);
  const token = getAuthToken();

  const response = await fetch(url, {
    headers: token ? { "Authorization": `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    throw new Error(`下载失败: ${response.status}`);
  }

  // 从响应头获取文件名
  const contentDisposition = response.headers.get("Content-Disposition");
  let filename = "original_image.jpg";
  if (contentDisposition) {
    const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    if (match && match[1]) {
      filename = match[1].replace(/['"]/g, "");
    }
  }

  // 下载文件
  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(blobUrl);
}

/**
 * 删除图片转译记录
 */
export async function deleteImageTranslation(translationId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/image-translation/${translationId}`, {
    method: "DELETE",
  });
}

// ==================== 公文库 API ====================

/**
 * 获取公文列表
 */
export async function fetchOfficialDocuments(params?: {
  page?: number;
  page_size?: number;
  source?: string;
  keyword?: string;
  sort_by?: string;
  sort_order?: string;
}): Promise<{
  items: Array<{
    id: string;
    title: string;
    source: string;
    created_at: number;
    description: string | null;
    document_type: string;
    file_size: number;
    file_path: string;
    content: string | null;
    content_preview: string | null;
  }>;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}> {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.append("page", params.page.toString());
  if (params?.page_size) queryParams.append("page_size", params.page_size.toString());
  if (params?.source) queryParams.append("source", params.source);
  if (params?.keyword) queryParams.append("keyword", params.keyword);
  if (params?.sort_by) queryParams.append("sort_by", params.sort_by);
  if (params?.sort_order) queryParams.append("sort_order", params.sort_order);

  const queryString = queryParams.toString();
  return request<{ items: any[]; total: number; page: number; page_size: number; total_pages: number }>(
    `/official-documents/${queryString ? `?${queryString}` : ""}`
  );
}

/**
 * 删除公文
 */
export async function deleteOfficialDocument(documentId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/official-documents/${documentId}`, {
    method: "DELETE",
  });
}

/**
 * 下载公文
 */
export async function downloadOfficialDocument(documentId: string, filename: string): Promise<void> {
  const url = getApiUrl(`/official-documents/${documentId}/download`);
  const token = getAuthToken();

  const response = await fetch(url, {
    headers: token ? { "Authorization": `Bearer ${token}` } : {},
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`下载失败: ${response.status}`);
  }

  // 下载文件
  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(blobUrl);
}

/**
 * 上传公文
 */
export async function uploadOfficialDocument(params: {
  file: File;
  title: string;
  description?: string;
  source: string;
}): Promise<any> {
  const formData = new FormData();
  formData.append("file", params.file);
  formData.append("title", params.title);
  if (params.description) formData.append("description", params.description);
  formData.append("source", params.source);
  formData.append("is_verified", "false");

  return uploadRequest("/official-documents/", formData);
}

// 导出 API 客户端
export const api = {
  // 文档
  fetchDocuments,
  fetchDocument,
  uploadDocument,
  deleteDocument,
  fetchDocumentContent,

  // 任务
  createTranslateTask,
  createWriteTask,
  fetchTaskStatus,

  // 工作流
  startResearchWorkflow,

  // 文档翻译
  createDocumentTranslation,
  fetchDocumentTranslationStatus,
  downloadTranslationWord,

  // 国别研究
  fetchCountries,
  fetchCountryDetail,
  fetchCountryResearchStages,
  startCountryResearch,

  // 季度报告
  fetchQuarterlyReportStages,
  startQuarterlyReport,

  // 图片转译
  uploadImageForTranslation,
  fetchImageTranslations,
  fetchImageTranslation,
  fetchImageTranslationStatus,
  getImagePreviewUrl,
  downloadTranslatedImage,
  downloadOriginalImage,
  deleteImageTranslation,

  // 公文库
  fetchOfficialDocuments,
  deleteOfficialDocument,
  downloadOfficialDocument,
  uploadOfficialDocument,

  // 健康检查
  healthCheck,
};
