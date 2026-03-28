# 央行公文写作 AI 系统

## 📖 项目简介

这是一个基于 FastAPI + React 的企业级文档管理与 AI 处理平台，提供 Zotero 式的文档管理能力和五大 AI 工作流，专为央行公文写作场景设计。

### 核心功能

1. **文献与公文库** - Zotero 风格的文档管理系统，支持 PDF、Word、TXT、Markdown 等多种格式
2. **国别深度研究** - 自动化国别研究报告生成，支持多数据源插拔式配置
3. **季度报告生成** - 金融市场与宏观经济分析报告自动生成
4. **公文翻译** - 专业公文对照翻译，支持段落对照格式
5. **学术报告转公文** - 学术报告自动转换为公文格式
6. **图片转译** - 图片中的文字提取与翻译

---

## 🏗️ 技术架构

### 后端技术栈

- **Web 框架**: FastAPI 0.109+
- **数据库**: PostgreSQL 15+ (通过 SQLAlchemy 2.0 异步驱动)
- **缓存/队列**: Redis 7+
- **任务队列**: Celery 5+
- **AI 服务**:
  - DeepSeek V3 (通过硅基流动 API)
  - DeepSeek R1 (推理模型)
  - OpenRouter (图片转译)
- **向量检索**: pgvector / Qdrant
- **网页抓取**: Firecrawl
- **文档处理**: PyPDF2, python-docx, Pillow
- **API 文档**: Swagger UI / ReDoc

### 前端技术栈

- **框架**: React 18.3.1 + TypeScript
- **构建工具**: Vite 6.3.5
- **UI 组件**: Radix UI + shadcn/ui
- **样式**: Tailwind CSS 4.1.12
- **动画**: Framer Motion 12.23.24
- **图表**: Recharts 2.15.2
- **状态管理**: React Hooks
- **路由**: React Router 7.13.0

---

## 📁 项目结构

```
央行公文写作/
├── backend/                    # 后端服务
│   ├── api/                    # API 路由
│   │   ├── endpoints/          # 各功能模块端点
│   │   │   ├── documents.py    # 文档管理
│   │   │   ├── tasks.py        # 任务管理
│   │   │   ├── workflows.py    # 工作流
│   │   │   ├── document_translation.py  # 公文翻译
│   │   │   ├── image_translation.py    # 图片转译
│   │   │   ├── knowledge.py    # 知识库
│   │   │   └── storage.py      # 文件存储
│   │   ├── v1/                 # API v1 路由聚合
│   │   └── dependencies.py     # 依赖注入
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 应用配置（环境变量）
│   │   ├── database.py         # 数据库连接
│   │   ├── security.py         # 安全相关
│   │   └── constants.py        # 常量定义
│   ├── models/                 # SQLAlchemy 数据模型
│   │   ├── base.py             # 基类
│   │   ├── document.py         # 文档模型
│   │   ├── task.py             # 任务模型
│   │   ├── user.py             # 用户模型
│   │   ├── tag.py              # 标签模型
│   │   ├── document_translation.py    # 翻译记录
│   │   └── image_translation.py       # 图片转译
│   ├── schemas/                # Pydantic 数据验证模式
│   │   ├── document.py         # 文档相关
│   │   ├── task.py             # 任务相关
│   │   ├── user.py             # 用户相关
│   │   └── common.py           # 通用响应
│   ├── services/               # 业务逻辑服务
│   │   ├── document_service.py         # 文档管理
│   │   ├── file_service.py             # 文件处理
│   │   ├── academic_to_official_service.py  # 学术转公文
│   │   ├── country_research_service.py     # 国别研究
│   │   ├── quarterly_report_service.py    # 季度报告
│   │   ├── translation_workflow_service.py # 翻译工作流
│   │   ├── document_translation_service.py # 公文翻译
│   │   └── image_translation_service.py    # 图片转译
│   ├── utils/                  # 工具函数
│   │   ├── pdf_extractor.py    # PDF 内容提取
│   │   └── markdown_to_word.py # Markdown 转 Word
│   ├── configs/                # 工作流配置
│   │   └── country_data_sources.py  # 国别研究数据源
│   ├── storage/                # 文件存储目录
│   │   ├── uploads/            # 上传文件
│   │   ├── thumbnails/         # 缩略图
│   │   └── cache/              # 缓存
│   ├── tasks/                  # Celery 任务
│   ├── alembic/                # 数据库迁移
│   ├── main.py                 # 应用入口
│   └── requirements.txt        # Python 依赖
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── app/
│   │   │   ├── App.tsx         # 主应用组件
│   │   │   ├── components/
│   │   │   │   ├── layout/     # 布局组件
│   │   │   │   │   ├── Sidebar.tsx        # 侧边栏
│   │   │   │   │   └── DataSourcePanel.tsx  # 数据源面板
│   │   │   │   ├── features/   # 功能模块
│   │   │   │   │   ├── library/       # 文献库
│   │   │   │   │   ├── research/      # 国别研究
│   │   │   │   │   └── image/         # 图片转译
│   │   │   │   └── ui/          # UI 组件库 (shadcn/ui)
│   │   │   ├── config/         # 前端配置
│   │   │   └── types/          # TypeScript 类型定义
│   │   ├── api/
│   │   │   ├── client.ts       # API 客户端封装
│   │   │   ├── types.ts        # API 数据类型
│   │   │   └── index.ts        # API 导出
│   │   ├── main.tsx            # 前端入口
│   │   └── vite-env.d.ts       # Vite 类型声明
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
│
├── 公文翻译 .yml               # 公文翻译工作流配置
├── 国别研究 .yml               # 国别研究工作流配置
├── 季报生成 .yml               # 季度报告工作流配置
├── 学术报告转公文.yml          # 学术转公文工作流配置
└── README.md                   # 本文档
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 1. 后端设置

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制 .env.example 到 .env 并修改）
cp .env.example .env

# 初始化数据库
alembic upgrade head

# 启动后端服务
python main.py
```

后端服务将在 `http://localhost:8000` 启动

API 文档访问: `http://localhost:8000/docs`

### 2. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 配置环境变量（创建 .env.local）
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

# 启动开发服务器
npm run dev
```

前端应用将在 `http://localhost:5173` 启动

### 3. 启动 Celery Worker (可选)

```bash
cd backend
celery -A tasks.celery_app worker --loglevel=info
```

---

## 📚 API 接口文档

### 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (JWT)
- **响应格式**: JSON

### 通用响应格式

所有 API 响应遵循以下格式：

```typescript
{
  "code": number,        // 状态码（可选）
  "message": string,     // 消息（可选）
  "data": T             // 实际数据
}
```

### 主要 API 端点

#### 1. 健康检查

```
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "service": "公文写作AI系统",
  "version": "1.0.0"
}
```

#### 2. 文档管理

##### 2.1 获取文档列表

```
GET /documents/
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 20, 最大: 100)
- `document_type`: 文档类型筛选 (pdf, docx, txt, markdown, image)
- `keyword`: 关键词搜索
- `sort_by`: 排序字段 (默认: created_at)
- `sort_order`: 排序方向 (asc/desc)

**响应示例**:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "文档标题",
      "original_filename": "文件名.pdf",
      "document_type": "pdf",
      "author": "作者",
      "subject": "主题",
      "keywords": ["关键词1", "关键词2"],
      "content_preview": "内容预览...",
      "page_count": 10,
      "file_size": 1024000,
      "is_shared": false,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

##### 2.2 上传文档

```
POST /documents/
Content-Type: multipart/form-data
```

**表单参数**:
- `file`: 文件 (必填)
- `title`: 文档标题 (必填)
- `author`: 作者 (可选)
- `subject`: 主题 (可选)
- `keywords`: 关键词，逗号分隔 (可选)
- `tag_ids`: 标签ID，逗号分隔 (可选)
- `source_url`: 来源 URL (可选)
- `is_shared`: 是否共享 (可选，默认: false)

**响应示例**:
```json
{
  "document_id": "uuid",
  "filename": "文件名.pdf",
  "file_size": 1024000,
  "document_type": "pdf",
  "message": "文档上传成功"
}
```

##### 2.3 获取文档详情

```
GET /documents/{document_id}
```

##### 2.4 删除文档

```
DELETE /documents/{document_id}
```

##### 2.5 获取文档内容

```
GET /documents/{document_id}/content
```

#### 3. 工作流 API

所有工作流接口支持 **SSE (Server-Sent Events)** 流式输出，前端可实时接收处理进度。

##### 3.1 学术报告转公文

```
POST /workflows/academic-to-official
Content-Type: multipart/form-data
```

**表单参数**:
- `file`: 学术报告文件 (可选，与 document_id 二选一)
- `document_id`: 已上传文档的 ID (可选，与 file 二选一)

**响应格式**: SSE 流

```javascript
// 前端使用示例
const response = await fetch('/api/v1/workflows/academic-to-official', {
  method: 'POST',
  body: formData
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      console.log(data.stage, data.message, data.progress);
    }
  }
}
```

**SSE 事件格式**:
```json
{
  "stage": "outline_generation",
  "stage_name": "大纲生成",
  "progress": 30.0,
  "message": "正在生成公文大纲...",
  "timestamp": "2024-01-01T12:00:00",
  "data": {}
}
```

**处理流程**:
1. 文档提取 (doc_extraction)
2. 知识检索 (knowledge_retrieval)
3. 大纲生成 (outline_generation)
4. 参数提取 (parameter_extraction)
5. 章节写作 (chapter_writing)
6. 模板转换 (template_transform)
7. 内容整合 (content_integration)
8. 最终调整 (final_adjustment)

##### 3.2 公文翻译

```
POST /workflows/translation
Content-Type: multipart/form-data
```

**表单参数**:
- `file`: 文档文件 (可选)
- `document_id`: 已上传文档的 ID (可选)
- `source_language`: 源语言 (默认: auto)
- `target_language`: 目标语言 (默认: zh)
- `model`: 翻译模型 (默认: deepseek-ai/DeepSeek-V3)

##### 3.3 国别研究

```
POST /workflows/country-research
Content-Type: multipart/form-data
```

**表单参数**:
- `country_code`: 国家代码 (必填，如 EG, KE, NG)
- `reference_file`: 参考文件 (可选)
- `user_sources`: 用户补充数据源 JSON 数组 (可选)

**user_sources 格式**:
```json
[
  {"name": "数据源名称", "url": "https://example.com"},
  {"name": "央行报告", "url": "https://centralbank.example.com/report"}
]
```

**获取支持的国家列表**:
```
GET /workflows/country-research/countries
```

**获取国家详细配置**:
```
GET /workflows/country-research/countries/{country_code}
```

##### 3.4 季度报告生成

```
POST /workflows/quarterly-report
Content-Type: multipart/form-data
```

参数同国别研究。

##### 3.5 导出为 Word

```
POST /workflows/academic-to-official/export-word
Content-Type: multipart/form-data
```

**表单参数**:
- `content`: Markdown 格式的内容 (必填)
- `filename`: 输出文件名 (必填)

**响应**: Word 文档文件流

#### 4. 公文翻译 API

##### 4.1 创建翻译任务

```
POST /document-translation/
Content-Type: multipart/form-data
```

**表单参数**:
- `file`: 文档文件 (可选，与 document_id 二选一)
- `document_id`: 已上传文档的 ID (可选)
- `source_language`: 源语言 (默认: auto)
- `target_language`: 目标语言 (默认: zh)

**响应示例**:
```json
{
  "translation_id": "uuid",
  "filename": "文件名.pdf",
  "status": "pending",
  "message": "翻译任务已创建，正在后台处理中"
}
```

##### 4.2 查询翻译状态 (轮询)

```
GET /document-translation/{translation_id}/status
```

**响应示例**:
```json
{
  "translation_id": "uuid",
  "status": "completed",
  "message": "翻译完成",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "text_url": "/api/v1/document-translation/{id}/text",
  "download_txt_url": "/api/v1/document-translation/{id}/download",
  "download_word_url": "/api/v1/document-translation/{id}/download-word",
  "download_markdown_url": "/api/v1/document-translation/{id}/download-markdown",
  "translated_text": "翻译后的文本...",
  "original_text": "原始文本..."
}
```

**状态值**:
- `pending`: 等待处理
- `processing`: 正在翻译中
- `completed`: 翻译完成
- `failed`: 翻译失败

##### 4.3 下载翻译结果

```
GET /document-translation/{translation_id}/download        # TXT
GET /document-translation/{translation_id}/download-word   # Word
GET /document-translation/{translation_id}/download-markdown  # Markdown
```

#### 5. 图片转译 API

##### 5.1 创建转译任务

```
POST /image-translation/
Content-Type: multipart/form-data
```

**表单参数**:
- `file`: 图片文件 (必填)

支持的图片类型: JPG, PNG, GIF, WebP, BMP

##### 5.2 查询转译状态

```
GET /image-translation/{translation_id}/status
```

##### 5.3 预览/下载转译图片

```
GET /image-translation/{translation_id}/preview    # 预览
GET /image-translation/{translation_id}/download   # 下载
```

#### 6. 任务管理

```
GET /tasks/              # 获取任务列表
GET /tasks/{task_id}     # 获取任务详情
POST /tasks/             # 创建任务
DELETE /tasks/{task_id}  # 取消任务
```

---

## 🔧 核心功能实现详解

### 1. 文档管理 (Document Management)

#### 后端实现

**文件**: `backend/services/document_service.py`

**核心功能**:
- 文件上传与存储（支持 PDF、DOCX、TXT、Markdown、图片）
- PDF 内容自动提取（使用 PyPDF2）
- 文件去重（基于 SHA256 哈希）
- 缩略图自动生成
- 元数据管理（作者、主题、关键词）
- 标签系统
- 分页、搜索、排序

**数据模型**: `backend/models/document.py`

```python
class Document(Base, UUIDMixin, TimestampMixin):
    title: str                              # 文档标题
    original_filename: str                  # 原始文件名
    document_type: str                      # 文档类型
    file_path: str                          # 文件存储路径
    file_size: int                          # 文件大小
    file_hash: str                          # SHA256 哈希（去重）
    content: str | None                     # 提取的文本内容
    content_preview: str | None             # 内容预览
    page_count: int | None                  # 页数
    author: str | None                      # 作者
    subject: str | None                     # 主题
    keywords: str | None                    # 关键词
    source_url: str | None                  # 来源 URL
    is_shared: bool                         # 是否共享
    owner_id: str                           # 所有者 ID
```

#### 前端实现

**文件**: `frontend/src/app/components/LibraryModule.tsx`

**功能**:
- 文档列表展示（卡片视图）
- 拖拽上传
- 元数据编辑
- 文档搜索与筛选
- 文档预览

---

### 2. 学术报告转公文 (Academic to Official Document)

#### 后端实现

**文件**: `backend/services/academic_to_official_service.py`

**工作流阶段**:

1. **文档提取** (Document Extraction)
   - 从 PDF/TXT 文件中提取文本内容
   - 识别文档元数据

2. **知识检索** (Knowledge Retrieval)
   - 从向量数据库检索相关公文模板
   - 提取参考材料

3. **大纲生成** (Outline Generation)
   - 使用 DeepSeek V3 生成公文框架
   - 确定章节结构

4. **参数提取** (Parameter Extraction)
   - 提取各章节标题和要点

5. **章节写作** (Chapter Writing)
   - 并发写作各章节内容
   - 保持公文风格

6. **模板转换** (Template Transform)
   - 整合各章节内容

7. **内容整合** (Content Integration)
   - 逻辑检查
   - 语言润色

8. **最终调整** (Final Adjustment)
   - 格式规范化

**SSE 流式输出**:

```python
async def process_academic_to_official(file_path, progress_callback, db):
    """异步处理工作流，流式返回进度更新"""

    # 每个阶段完成后发送进度更新
    await progress_callback(ProgressUpdate(
        stage=WorkflowStage.DOCUMENT_EXTRACTION,
        stage_name="文档提取",
        progress=10.0,
        message="正在提取文档内容...",
        timestamp=datetime.now()
    ))

    # ... 执行实际处理

    yield update  # 返回给 SSE
```

#### 前端实现

**文件**: `frontend/src/app/components/ResearchModule.tsx`

**功能**:
- 文件上传
- 实时进度条（SSE 接收）
- 阶段展示
- 结果预览
- 导出 Word/Markdown

---

### 3. 国别深度研究 (Country Research)

#### 后端实现

**文件**: `backend/services/country_research_service.py`

**数据源配置**: `backend/configs/country_data_sources.py`

**支持的国家**:
- EG (埃及)
- KE (肯尼亚)
- NG (尼日利亚)
- ... (可扩展)

**数据源类型**:
- Trading Economics
- IMF
- World Bank
- 央行官网
- 新闻网站

**处理流程**:

1. **配置加载**
   - 加载目标国家的数据源配置
   - 验证数据源可用性

2. **数据采集** (并发)
   - 使用 Firecrawl 抓取各数据源
   - 异步并发处理

3. **经济分析**
   - GDP、通胀、货币政策分析
   - 使用 DeepSeek R1 进行深度推理

4. **政治分析**
   - 国家元首、政治体制分析

5. **外交分析**
   - 重点分析对华关系

6. **报告生成**
   - 整合分析结果

7. **质量审核**
   - 完整性检查
   - 规范性检查

**思维链输出**:

每个关键节点输出思维链信息，帮助用户理解 AI 的分析过程：

```python
thinking_node = {
    "stage": "data_fetching",
    "node_id": "fetch_0",
    "title": "采集数据源: GDP增速",
    "content": "URL: https://tradingeconomics.com/egypt/gdp-growth",
    "timestamp": datetime.now().isoformat(),
    "metadata": {
        "source": "Trading Economics",
        "indicator": "GDP Growth",
        "country": "Egypt"
    }
}
```

#### 前端实现

**功能**:
- 国家选择器
- 数据源配置面板
- 用户自定义数据源
- 实时进度展示
- 思维链可视化

---

### 4. 公文翻译 (Document Translation)

#### 后端实现

**文件**: `backend/services/document_translation_service.py`

**翻译策略**:

1. **文档分析**
   - 检测文档类型和大小
   - 分析文本结构

2. **分段处理**
   - 按段落分割文本
   - 保持段落完整性

3. **批量翻译**
   - 使用 DeepSeek V3 API
   - 并发处理多个段落

4. **对照格式**
   - 生成段落对照格式
   - 先中文后英文
   - 段落间空行分隔

5. **质量检查**
   - 术语一致性检查
   - 格式规范化

**后台异步处理**:

```python
async def create_translation_task(...):
    """创建翻译任务"""

    # 创建翻译记录
    translation = DocumentTranslation(
        original_filename=filename,
        status=DocumentTranslationStatus.PENDING,
        ...
    )
    db.add(translation)
    await db.commit()

    # 启动后台处理（不阻塞 HTTP 响应）
    asyncio.create_task(
        process_translation_background(translation.id)
    )

    return translation
```

**前端轮询**:

```javascript
// 前端轮询翻译状态
const pollStatus = async (translationId) => {
  const interval = setInterval(async () => {
    const status = await api.fetchDocumentTranslationStatus(translationId);

    if (status.status === 'completed') {
      clearInterval(interval);
      // 显示翻译结果
    } else if (status.status === 'failed') {
      clearInterval(interval);
      // 显示错误信息
    }
  }, 2000);  // 每 2 秒轮询一次
};
```

---

### 5. 图片转译 (Image Translation)

#### 后端实现

**文件**: `backend/services/image_translation_service.py`

**实现方案**:

1. **图片接收**
   - 验证图片格式
   - 检查文件大小

2. **OCR 提取**
   - 使用 PaddleOCR 或 Tesseract
   - 提取图片中的文字

3. **文本翻译**
   - 调用 DeepSeek API
   - 翻译提取的文字

4. **图片重建**
   - 将翻译文字覆盖到原图片
   - 保持原始布局

5. **结果输出**
   - 生成转译后的图片
   - 提供预览和下载

---

## 🔐 认证与授权

### 当前实现（开发阶段）

**简化认证**: `backend/api/dependencies.py`

```python
async def get_current_user_id():
    """开发阶段：返回默认用户 ID"""
    return settings.DEFAULT_USER_ID  # 固定的 UUID
```

### 生产环境建议

1. **JWT 认证**
   - 用户登录获取 JWT Token
   - 每个 API 请求携带 Token

2. **权限控制**
   - 基于角色的访问控制 (RBAC)
   - 文档级权限控制

3. **API 密钥**
   - 外部系统集成使用 API Key

---

## 🗄️ 数据库设计

### 核心表结构

#### documents (文档表)

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    document_type VARCHAR(20) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash VARCHAR(64) UNIQUE,
    content TEXT,
    content_preview TEXT,
    page_count BIGINT,
    author VARCHAR(255),
    subject VARCHAR(500),
    keywords TEXT,
    source_url TEXT,
    source_type VARCHAR(50),
    is_shared BOOLEAN DEFAULT FALSE,
    owner_id VARCHAR(36) NOT NULL,
    parent_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_documents_owner ON documents(owner_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_shared ON documents(is_shared);
```

#### document_translations (公文翻译记录表)

```sql
CREATE TABLE document_translations (
    id UUID PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    original_document_path TEXT NOT NULL,
    translated_document_path TEXT,
    original_text TEXT,
    translated_text TEXT,
    source_language VARCHAR(10),
    target_language VARCHAR(10),
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    owner_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### image_translations (图片转译记录表)

```sql
CREATE TABLE image_translations (
    id UUID PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    original_image_path TEXT NOT NULL,
    translated_image_path TEXT,
    mime_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    owner_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🎨 前端架构

### 组件层次结构

```
App
├── Sidebar (侧边栏)
│   ├── 文献与公文库
│   ├── 国别深度研究
│   ├── 季度报告生成
│   ├── 公文翻译
│   ├── 图片转译
│   └── 历史记录
├── DataSourcePanel (数据源面板)
├── HistoryPanel (历史记录面板)
└── 功能模块
    ├── LibraryModule (文献库)
    ├── ResearchModule (国别研究)
    └── ImageModule (图片转译)
```

### 状态管理

使用 React Hooks 进行状态管理：

```typescript
// 示例：文档列表状态
const [documents, setDocuments] = useState<Document[]>([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

// 加载文档列表
const loadDocuments = async (params?: PaginationParams) => {
  setLoading(true);
  try {
    const response = await api.fetchDocuments(params);
    setDocuments(response.items);
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};
```

### API 调用封装

**文件**: `frontend/src/api/client.ts`

```typescript
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

  // 添加认证 Token
  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || data.message);
  }

  return (data as ApiResponse<T>).data ?? data;
}
```

### SSE 连接处理

```typescript
// 处理 SSE 流式响应
const handleWorkflowStream = async (
  endpoint: string,
  formData: FormData,
  onProgress: (update: ProgressUpdate) => void,
  onComplete: () => void,
  onError: (error: string) => void
) => {
  const response = await fetch(endpoint, {
    method: 'POST',
    body: formData,
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader?.read() ?? { done: true };
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          onProgress(data);
        }
      }
    }
    onComplete();
  } catch (error) {
    onError(error.message);
  }
};
```

---

## 🔍 Debug 指南

### 后端 Debug

#### 1. 查看日志

后端使用 `loguru` 记录日志：

```python
from loguru import logger

logger.info("[INFO] 处理文档...")
logger.warning("[WARNING] PDF 内容提取失败")
logger.error("[ERROR] 文档创建失败")
```

日志文件位置: `backend/logs/app.log`

#### 2. 数据库查询

使用 SQLAlchemy 的日志功能查看 SQL 查询：

```python
# core/database.py
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### 3. API 测试

使用 Swagger UI: `http://localhost:8000/docs`

或使用 `curl`:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.pdf" \
  -F "title=测试文档"
```

### 前端 Debug

#### 1. 浏览器开发者工具

- **Network 标签**: 查看 API 请求和响应
- **Console 标签**: 查看错误和日志
- **React DevTools**: 查看组件状态和 props

#### 2. API 调用日志

```typescript
// 在 client.ts 中添加日志
async function request<T>(...) {
  console.log(`[API Request] ${endpoint}`, options);

  const response = await fetch(url, options);

  console.log(`[API Response] ${endpoint}`, response.status);
  return data;
}
```

#### 3. SSE 连接调试

```typescript
// 打印 SSE 事件
const lines = chunk.split('\n');
for (const line of lines) {
  console.log('[SSE]', line);  // 查看原始 SSE 数据

  if (line.startsWith('data: ')) {
    const data = JSON.parse(line.slice(6));
    console.log('[SSE Data]', data);  // 查看解析后的数据
  }
}
```

---

## 🐛 常见问题与解决方案

### 问题 1: CORS 错误

**现象**: 前端请求后端 API 时出现 CORS 错误

**原因**: 后端未配置允许的前端域名

**解决方案**:

```python
# core/config.py
ALLOWED_ORIGINS = "http://localhost:3000,http://localhost:5173"

# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 问题 2: 文件上传失败

**现象**: 上传大文件时失败

**原因**: 文件大小超过限制

**解决方案**:

```python
# core/config.py
MAX_FILE_SIZE_MB = 100  # 调整文件大小限制
MAX_IMAGE_SIZE_MB = 10
```

### 问题 3: SSE 连接中断

**现象**: 工作流处理中 SSE 连接意外断开

**原因**: Nginx/Gunicorn 超时设置

**解决方案**:

```nginx
# Nginx 配置
location /api/v1/workflows/ {
    proxy_pass http://backend;
    proxy_buffering off;          # 禁用缓冲
    proxy_read_timeout 3600s;     # 增加读取超时
    proxy_connect_timeout 3600s;
}
```

### 问题 4: 数据库连接池耗尽

**现象**: 大量并发请求时出现数据库连接错误

**原因**: 连接未正确释放

**解决方案**:

```python
# core/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # 增加连接池大小
    max_overflow=40,       # 增加最大溢出连接数
    pool_pre_ping=True,    # 连接前检查可用性
    echo=False,
)
```

### 问题 5: AI API 调用失败

**现象**: DeepSeek API 调用超时或失败

**原因**: API 限流或网络问题

**解决方案**:

```python
# 添加重试机制
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_deepseek_api(prompt):
    # API 调用逻辑
    pass
```

---

## 📈 性能优化建议

### 后端优化

1. **数据库查询优化**
   - 使用 `selectinload()` 预加载关联数据
   - 添加适当的数据库索引
   - 使用查询缓存

2. **异步处理**
   - 使用 Celery 处理耗时任务
   - 使用 `asyncio.gather()` 并发处理

3. **文件存储优化**
   - 使用 CDN 存储静态文件
   - 实现文件分片上传
   - 添加文件缓存

### 前端优化

1. **代码分割**
   ```typescript
   // 使用 React.lazy 进行路由级代码分割
   const LibraryModule = React.lazy(() => import('./components/LibraryModule'));
   ```

2. **虚拟列表**
   ```typescript
   // 使用 react-window 处理大列表
   import { FixedSizeList } from 'react-window';
   ```

3. **请求缓存**
   ```typescript
   // 使用 SWR 或 React Query 进行数据缓存
   import useSWR from 'swr';

   const { data, error } = useSWR('/api/v1/documents', fetcher);
   ```

---

## 🚢 部署指南

### Docker 部署

**后端 Dockerfile**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

**前端 Dockerfile**:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off;"]
```

**docker-compose.yml**:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: docwriting
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  backend:
    build: ./backend
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql+asyncpg://user:password@postgres/docwriting
      REDIS_URL: redis://redis:6379/0

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## 📝 开发规范

### Git 提交规范

使用 Conventional Commits:

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具链相关

### 代码风格

**后端 (Python)**:
- 使用 Black 格式化代码
- 使用 isort 排序导入
- 使用 flake8 检查代码规范
- 使用 mypy 进行类型检查

**前端 (TypeScript)**:
- 使用 ESLint + Prettier
- 遵循 React Hooks 规则
- 使用 TypeScript 严格模式

---

## 📄 License

MIT License

---

## 👥 联系方式

如有问题，请提 Issue 或联系开发团队。

---

## 🎯 路线图

- [ ] 完善单元测试覆盖
- [ ] 实现完整的用户认证系统
- [ ] 添加更多工作流模板
- [ ] 支持更多文档格式
- [ ] 实现文档版本控制
- [ ] 添加协作功能
- [ ] 性能优化和负载测试
- [ ] Docker/K8s 部署方案
