/**
 * API 数据类型定义
 */

// 文档类型
export type DocumentType = "pdf" | "docx" | "txt" | "markdown" | "image";

// AI 处理状态
export type AiStatus = "completed" | "processing" | "pending";

// 文档来源
export type SourceType = "upload" | "url" | "plugin";

// 文档接口
export interface Document {
  id: string;
  title: string;
  original_filename: string;
  document_type: DocumentType;
  author?: string;
  subject?: string;
  keywords?: string[];
  tag_ids?: string[];
  source_url?: string;
  source_type: SourceType;
  content_preview?: string;
  page_count?: number;
  file_size: number;
  file_path?: string;
  is_shared: boolean;
  created_at: string;
  updated_at: string;
}

// 文档列表响应
export interface DocumentListResponse {
  items: Document[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// 文档上传响应
export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  file_size: number;
  document_type: DocumentType;
  message: string;
}

// 通用响应格式
export interface ApiResponse<T> {
  code?: number;
  message?: string;
  data: T;
}

// 分页参数
export interface PaginationParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

// 文档上传参数
export interface DocumentUploadParams {
  file: File;
  title: string;
  author?: string;
  subject?: string;
  keywords?: string;
  tag_ids?: string;
  source_url?: string;
  is_shared?: boolean;
}

// 任务状态
export type TaskStatus = "pending" | "running" | "completed" | "failed";

// 任务类型
export type TaskType = "translate" | "write" | "research" | "image_translate";

// 任务接口
export interface Task {
  id: string;
  task_type: TaskType;
  status: TaskStatus;
  document_id?: string;
  progress: number;
  result?: string;
  error?: string;
  created_at: string;
  updated_at: string;
}

// 知识库条目
export interface KnowledgeEntry {
  id: string;
  title: string;
  content: string;
  source?: string;
  tags?: string[];
  created_at: string;
}

// 国别研究参数
export interface ResearchParams {
  country: string;
  research_type: string;
  model: string;
  custom_urls?: string[];
}

// 图片翻译参数
export interface ImageTranslateParams {
  image_url: string;
  target_language: string;
  model?: string;
}

// ==================== 文档翻译相关类型 ====================

// 文档翻译状态
export type DocumentTranslationStatus = "pending" | "processing" | "completed" | "failed";

// 文档翻译上传响应
export interface DocumentTranslationUploadResponse {
  translation_id: string;
  filename: string;
  status: DocumentTranslationStatus;
  message: string;
}

// 文档翻译状态响应
export interface DocumentTranslationStatusResponse {
  translation_id: string;
  status: DocumentTranslationStatus;
  message: string;
  created_at: string;
  updated_at: string;
  text_url?: string;
  download_txt_url?: string;
  download_word_url?: string;
  download_markdown_url?: string;
  translated_text?: string;
  original_text?: string;
  error?: string;
}

// 文档翻译上传参数
export interface DocumentTranslationParams {
  file?: File;
  document_id?: string;
  source_language?: string;
  target_language?: string;
}

// ==================== 国别研究相关类型 ====================

// 国别研究阶段
export type CountryResearchStage =
  | "config_loading"
  | "data_fetching"
  | "economic_analysis"
  | "political_analysis"
  | "diplomacy_analysis"
  | "report_generation"
  | "quality_review"
  | "failed"
  | "completed";

// 国家信息
export interface Country {
  code: string;
  name: string;
  name_en: string;
  region: string;
  income_level: string;
  currency: string;
  data_source_count: number;
}

// 国家数据源详情
export interface CountryDataSource {
  name: string;
  type: string;
  url: string;
  label: string;
  description?: string;
  enabled: boolean;
  data_format?: string;
}

// 国家详情
export interface CountryDetail {
  country_code: string;
  country_name: string;
  country_name_en: string;
  region: string;
  income_level: string;
  currency: string;
  data_sources: CountryDataSource[];
}

// 国别研究参数
export interface CountryResearchParams {
  country_code: string;
  reference_file?: File;
  user_sources?: string;
}

// 国别研究进度更新（SSE）
export interface CountryResearchProgressUpdate {
  stage: CountryResearchStage;
  stage_name: string;
  progress: number;
  message: string;
  timestamp: string;
  thinking_node?: {
    stage: string;
    node_id: string;
    title: string;
    content: string;
    timestamp: string;
    metadata?: Record<string, unknown>;
  };
  data?: {
    stats?: Record<string, unknown>;
    [key: string]: unknown;
  };
}

// ==================== 季度报告相关类型 ====================

// 季度报告阶段
export type QuarterlyReportStage =
  | "config_loading"
  | "data_fetching"
  | "macro_analysis"
  | "financial_market_analysis"
  | "policy_analysis"
  | "risk_assessment"
  | "report_generation"
  | "quality_review"
  | "failed"
  | "completed";

// 季度报告参数
export interface QuarterlyReportParams {
  country_code: string;
  reference_file?: File;
  user_sources?: string;
}

// 季度报告进度更新（SSE）
export interface QuarterlyReportProgressUpdate {
  stage: QuarterlyReportStage;
  stage_name: string;
  progress: number;
  message: string;
  timestamp: string;
  thinking_node?: {
    stage: string;
    node_id: string;
    title: string;
    content: string;
    timestamp: string;
    metadata?: Record<string, unknown>;
  };
  data?: {
    stats?: Record<string, unknown>;
    [key: string]: unknown;
  };
}

// ==================== 图片转译相关类型 ====================

// 图片转译状态
export type ImageTranslationStatus = "pending" | "processing" | "completed" | "failed";

// 图片转译上传响应
export interface ImageTranslationUploadResponse {
  translation_id: string;
  filename: string;
  status: ImageTranslationStatus;
  message: string;
}

// 图片转译响应
export interface ImageTranslation {
  id: string;
  original_filename: string;
  status: ImageTranslationStatus;
  original_image_path?: string;
  translated_image_path?: string;
  mime_type?: string;
  error_message?: string;
  progress?: number;
  created_at: string;
  updated_at: string;
}

// 图片转译状态响应
export interface ImageTranslationStatusResponse {
  translation_id: string;
  status: ImageTranslationStatus;
  message: string;
  created_at: string;
  updated_at: string;
  preview_url?: string;
  download_url?: string;
  error?: string;
}

// 图片转译上传参数
export interface ImageTranslationParams {
  file: File;
}

// ==================== 工作流通用类型 ====================

// 工作流阶段信息
export interface WorkflowStage {
  value: string;
  name: string;
  description: string;
  icon: string;
}

// 工作流阶段列表响应
export interface WorkflowStagesResponse {
  stages: WorkflowStage[];
}
