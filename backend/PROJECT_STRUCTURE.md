# 后端项目结构说明

本项目采用分层架构设计，严格遵循单一职责原则。

## 📁 目录结构详解

### 🚀 `api/` - API 路由层
**职责**：处理 HTTP 请求，参数验证，调用服务层，返回响应

```
api/
├── __init__.py
├── dependencies.py          # API 依赖注入（认证、权限等）
├── v1/
│   ├── __init__.py
│   └── api.py              # API v1 主路由，聚合所有端点
└── endpoints/
    ├── __init__.py
    ├── auth.py             # 认证相关端点
    ├── documents.py        # 文档管理端点
    ├── tasks.py            # 任务执行端点
    ├── knowledge.py        # 知识库端点
    ├── workflows.py        # 工作流端点
    └── storage.py          # 文件存储端点
```

**规则**：
- ❌ 不包含业务逻辑
- ❌ 不直接操作数据库
- ✅ 仅处理请求/响应
- ✅ 参数验证（使用 Pydantic）

---

### ⚙️ `core/` - 核心配置层
**职责**：全局配置、安全、数据库连接、常量定义

```
core/
├── __init__.py
├── config.py              # 配置类（环境变量、常量）
├── security.py            # 安全相关（JWT、密码哈希）
├── database.py            # 数据库连接管理
├── redis.py               # Redis 连接管理
└── constants.py           # 业务常量（任务类型、状态等）
```

**规则**：
- ✅ 全局单例（如数据库连接池）
- ✅ 环境变量管理
- ✅ 密钥管理

---

### 🗄️ `models/` - 数据库模型层
**职责**：SQLAlchemy ORM 模型定义

```
models/
├── __init__.py
├── base.py                # Base 类和通用方法
├── document.py            # 文档模型
├── task.py                # 任务历史模型
├── knowledge.py           # 知识库模型
├── user.py                # 用户模型（如需）
└── tag.py                 # 标签模型
```

**规则**：
- ✅ 仅定义表结构
- ✅ 定义关系（relationship）
- ❌ 不包含业务逻辑

---

### 📋 `schemas/` - Pydantic 模型层
**职责**：请求/响应数据验证、序列化

```
schemas/
├── __init__.py
├── document.py            # 文档相关 Schema
├── task.py                # 任务相关 Schema
├── knowledge.py           # 知识库相关 Schema
├── user.py                # 用户相关 Schema
└── common.py              # 通用 Schema（分页、响应等）
```

**规则**：
- ✅ 请求验证（Request Model）
- ✅ 响应序列化（Response Model）
- ✅ 字段描述、示例

---

### 🔧 `services/` - 业务逻辑层
**职责**：核心业务逻辑实现

```
services/
├── __init__.py
├── document_service.py    # 文档管理业务逻辑
├── task_service.py        # 任务管理业务逻辑
├── knowledge_service.py   # 知识库业务逻辑
├── ai_service.py          # AI 调用服务（DeepSeek、OpenRouter）
├── file_service.py        # 文件处理服务
└── workflow_service.py    # 工作流编排服务
```

**规则**：
- ✅ 核心业务逻辑
- ✅ 跨模型操作
- ✅ 事务管理
- ❌ 不处理 HTTP 相关

---

### 🔄 `tasks/` - 异步任务层
**职责**：Celery 异步任务定义

```
tasks/
├── __init__.py
├── celery_app.py          # Celery 应用配置
├── document_tasks.py      # 文档相关任务（如：批量处理）
├── workflow_tasks.py      # 工作流任务
└── ai_tasks.py            # AI 调用任务
```

**规则**：
- ✅ 长时间运行的任务
- ✅ 定时任务
- ✅ 需要重试的任务

---

### 🛠️ `utils/` - 工具函数层
**职责**：通用工具函数

```
utils/
├── __init__.py
├── text_processing.py     # 文本处理（分块、清洗）
├── file_utils.py          # 文件操作工具
├── pdf_extractor.py       # PDF 提取
├── sse_manager.py         # SSE 连接管理器
├── retry.py               # 重试装饰器
└── logger.py              # 日志配置
```

**规则**：
- ✅ 纯函数（无副作用）
- ✅ 可复用
- ❌ 不依赖业务模型

---

### 🔍 `vector_store/` - 向量存储层
**职责**：向量数据库操作（知识库检索）

```
vector_store/
├── __init__.py
├── base.py                # 向量存储基类
├── pgvector_store.py      # pgvector 实现
├── qdrant_store.py        # Qdrant 实现（可选）
└── embeddings.py          # 向量生成（如使用 DeepSeek Embedding）
```

**规则**：
- ✅ 向量 CRUD 操作
- ✅ 相似度搜索
- ✅ 支持多种向量数据库

---

### 🧩 `workflows/` - 工作流定义层
**职责**：五大 AI 工作流的具体实现

```
workflows/
├── __init__.py
├── base.py                # 工作流基类
├── academic_to_official.py # 学术报告转公文
├── translation.py         # 公文翻译
├── country_research.py    # 国别研究
├── quarterly_report.py    # 季度报告
└── image_translation.py   # 图片转译
```

**规则**：
- ✅ 工作流步骤定义
- ✅ 状态管理
- ✅ 支持流式输出

---

### 📦 `storage/` - 文件存储层
**职责**：本地文件存储管理

```
storage/
├── uploads/               # 用户上传的原始文件
│   ├── pdfs/
│   ├── images/
│   └── docs/
├── thumbnails/            # PDF/图片缩略图
├── cache/                 # 临时缓存文件
└── .gitkeep               # 保持目录结构
```

**规则**：
- ✅ 按类型分类存储
- ✅ 文件命名规则（UUID + 原始扩展名）
- ✅ 定期清理缓存

---

### 🧪 `tests/` - 测试层
**职责**：单元测试、集成测试

```
tests/
├── __init__.py
├── conftest.py            # pytest 配置
├── test_api/              # API 测试
├── test_services/         # 服务层测试
├── test_workflows/        # 工作流测试
└── test_utils/            # 工具函数测试
```

---

### 📜 `scripts/` - 脚本层
**职责**：初始化、迁移、维护脚本

```
scripts/
├── init_db.py             # 数据库初始化
├── import_knowledge.py    # 导入知识库
├── migrate.py             # 数据迁移
└── cleanup.py             # 清理脚本
```

---

## 🎯 开发规则

### 1. 调用链路
```
API 层 → 服务层 → 模型层/工具层
   ↓        ↓
  响应    数据库/外部API
```

### 2. 禁止事项
- ❌ API 层直接操作数据库
- ❌ 服务层返回 HTTP 响应
- ❌ 跨层调用（如 API → 工具层）
- ❌ 循环依赖

### 3. 命名规范
- 文件名：小写 + 下划线（如 `document_service.py`）
- 类名：大驼峰（如 `DocumentService`）
- 函数名：小写 + 下划线（如 `get_document_by_id`）
- 常量：大写 + 下划线（如 `MAX_UPLOAD_SIZE`）

### 4. 依赖注入
```python
# ✅ 正确：通过依赖注入
@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    service: DocumentService = Depends()
):
    return await service.get_document(doc_id)

# ❌ 错误：直接实例化
@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    service = DocumentService()  # 不要这样做
    return await service.get_document(doc_id)
```

---

## 📌 文件变更规则

### 新增功能时
1. `models/` - 定义数据模型（如需要）
2. `schemas/` - 定义请求/响应模型
3. `services/` - 实现业务逻辑
4. `api/endpoints/` - 创建 API 端点
5. `api/v1/api.py` - 注册路由

### 新增工作流时
1. `workflows/` - 创建工作流类
2. `services/workflow_service.py` - 注册工作流
3. `api/endpoints/workflows.py` - 添加触发端点

---

## 🚀 下一步

1. 初始化数据库和配置
2. 实现文档库功能
3. 实现任务管理
4. 实现工作流引擎

**严格按照此结构进行开发！**
