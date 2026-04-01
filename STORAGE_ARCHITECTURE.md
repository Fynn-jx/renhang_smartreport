# 央行公文写作 AI 系统 - 存储架构文档

> 文档版本：v1.0
> 最后更新：2026-04-01
> 维护者：开发团队

---

## 📋 目录

- [1. 存储架构概述](#1-存储架构概述)
- [2. 本地文件存储](#2-本地文件存储)
- [3. 云存储集成](#3-云存储集成)
- [4. 各模块存储方案](#4-各模块存储方案)
- [5. 浏览器插件存储方案](#5-浏览器插件存储方案)
- [6. 存储路径规范](#6-存储路径规范)
- [7. 文件去重策略](#7-文件去重策略)
- [8. 存储安全与备份](#8-存储安全与备份)

---

## 1. 存储架构概述

### 1.1 存储层级

```
┌─────────────────────────────────────────────────────────────┐
│                     应用层                                  │
│  前沿报告库 | 公文库 | 图片转译 | 对照翻译 | 公文写作        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   FileService (统一文件服务)                │
│  - 保存文件    - 生成路径    - 哈希去重    - URL 生成        │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
┌─────────▼───��─────┐   ┌────────▼────────┐
│   本地存储        │   │   云存储        │
│   (主存储)        │   │   (临时中转)    │
└───────────────────┘   └─────────────────┘
```

### 1.2 存储原则

1. **本地优先**：所有文件永久存储在本地服务器
2. **云存储辅助**：仅用于 AI 处理时的临时中转（如 MinerU）
3. **相对路径**：数据库只存储相对路径，便于迁移
4. **哈希去重**：使用 SHA256 哈希避免重复存储
5. **分类存储**：按文档类型分目录存储

---

## 2. 本地文件存储

### 2.1 目录结构

```
backend/storage/
├── uploads/                    # 用户上传的文件
│   ├── document/              # 前沿报告库文档
│   │   └── {SHA256}.pdf
│   ├── pdf/                   # PDF 文件（专用类型）
│   │   └── {SHA256}.pdf
│   ├── image/                 # 图片转译的原图
│   │   └── {UUID}.{ext}
│   ├── official/              # 公文库文档
│   │   └── {UUID}.{ext}
│   └── temp/                  # 临时文件
├── official_documents/         # 公文库存储（独立目录）
│   └── {UUID}.{ext}
├── thumbnails/                # 缩略图（未来功能）
├── cache/                     # 缓存文件
├── documents.db               # SQLite 数据库
└── logs/                      # 日志文件
```

### 2.2 配置参数

**`backend/core/config.py`**

```python
# ==================== 文件存储配置 ====================
STORAGE_ROOT: str = "./storage"              # 存储根目录
UPLOAD_DIR: str = "./storage/uploads"       # 上传目录
THUMBNAIL_DIR: str = "./storage/thumbnails" # 缩略图目录
CACHE_DIR: str = "./storage/cache"          # 缓存目录

# 文件大小限制（MB）
MAX_FILE_SIZE_MB: int = 100                 # 最大文件大小
MAX_IMAGE_SIZE_MB: int = 10                 # 最大图片大小
```

### 2.3 FileService 核心方法

**`backend/services/file_service.py`**

| 方法 | 功能 | 返回值 |
|------|------|--------|
| `save_file()` | 保存文件到磁盘 | `(file_path, file_hash, file_size)` |
| `get_full_path()` | 获取完整路径 | `Path` 对象 |
| `get_url()` | 获取访问 URL | `/storage/{relative_path}` |
| `delete_file()` | 删除文件 | `bool` |
| `file_exists()` | 检查文件是否存在 | `bool` |
| `get_file_hash()` | 计算 SHA256 哈希 | `str` |

---

## 3. 云存储集成

### 3.1 腾讯云 COS（临时中转）

**用途**：MinerU PDF 解析时的文件中转

**配置**：

```env
# .env 文件
TENCENT_COS_SECRET_ID=AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TENCENT_COS_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TENCENT_COS_REGION=ap-guangzhou
TENCENT_COS_BUCKET=your-bucket-name
```

**工作流程**：

```
本地 PDF → 上传到 COS（公开 URL）→ MinerU 解析 → 删除 COS 文件
```

**特点**：
- ⚠️ **仅用于临时中转**，不永久存储
- ✅ 自动清理，解析完成后删除
- ✅ 公开读取权限，确保 MinerU 可访问

### 3.2 其他云存储（未来扩展）

| 云存储 | 状态 | 用途 |
|--------|------|------|
| 阿里云 OSS | ⏳ 计划中 | 备份存储 |
| AWS S3 | ⏳ 计划中 | 国际业务 |
| CDN 加速 | ⏳ 计划中 | 静态资源加速 |

---

## 4. 各模块存储方案

### 4.1 前沿报告库（Document）

**数据库模型**：`backend/models/document.py`

```python
class Document(Base):
    # 文件存储信息
    file_path: Mapped[str]          # 相对路径，如 "uploads/document/{hash}.pdf"
    file_size: Mapped[int]           # 文件大小（字节）
    file_hash: Mapped[str]           # SHA256 哈希
```

**存储路径格式**：

```
uploads/document/{SHA256}.pdf
```

**示例**：

```
uploads/document/70b138594766102a8e356173ada79a8e2a2f35f739ddabd01ec3b96c666716c5.pdf
```

**访问 URL**：

```
/storage/uploads/document/{SHA256}.pdf
```

**API 端点**：

- `POST /api/v1/documents/upload` - 上传文档
- `GET /storage/{file_path}` - 下载文档

---

### 4.2 公文库（OfficialDocument）

**数据库模型**：`backend/models/official_document.py`

```python
class OfficialDocument(Base):
    # 文件存储信息
    file_path: Mapped[str]          # 相对路径
    file_size: Mapped[int]           # 文件大小
    file_hash: Mapped[str]           # SHA256 哈希（去重）
```

**存储路径格式**：

```
storage/official_documents/{UUID}.{ext}
```

**示例**：

```
storage/official_documents/355b48a4-ab9d-4466-86d3-ee42f923177d.docx
```

**特点**：
- ✅ 独立目录 `storage/official_documents/`
- ✅ 使用 UUID 而非哈希（避免与其他模块冲突）
- ✅ 支持多种格式（PDF、DOCX、TXT、MD）

---

### 4.3 图片转译（ImageTranslation）

**数据库模型**：`backend/models/image_translation.py`

```python
class ImageTranslation(Base):
    # 文件存储信息
    original_image_path: Mapped[str]      # 原图路径
    translated_image_path: Mapped[str | None]  # 转译后图片路径
```

**存储路径格式**：

```
# 原图
uploads/image/{UUID}.{ext}

# 转译后图片
uploads/image/{UUID}.{ext}
```

**示例**：

```
uploads/image/3d44b4b41f19b9cbc2ecb142fccfe6e2be29849f4e2cc69bede931509f23f8fd.png
```

**API 端点**：

- `POST /api/v1/image-translation/` - 上传图片
- `GET /api/v1/image-translation/{id}/preview` - 预览转译后图片
- `GET /api/v1/image-translation/{id}/download` - 下载转译后图片

---

### 4.4 对照翻译 & 公文写作

**特点**：
- ✅ 不额外存储文件，复用 Document 模块的存储
- ✅ 使用 MinerU 或 PyMuPDF 实时提取内容
- ✅ 生成的 Markdown 内容临时存储在内存中

**工作流程**：

```
1. 读取 Document.file_path
2. 使用 MinerU/PyMuPDF 提取内容
3. AI 处理（翻译/写作）
4. 返回 Markdown 给前端
5. 前端导出为 Word（客户端下载）
```

---

## 5. 浏览器插件存储方案

### 5.1 插件下载流程

```
┌─────────────┐
│ 浏览器插件  │
└──────┬──────┘
       │ 1. 识别网页报告
       │ 2. 提取元数据（标题、来源、日期）
       ▼
┌─────────────────┐
│  插件后端 API   │
│  /api/v1/plugins│
│  /documents      │
└────────┬────────┘
         │ 3. 下载 PDF/网页
         │ 4. 生成 Markdown
         ▼
┌─────────────────┐
│  FileService    │
│  保存到本地     │
└────────┬────────┘
         │ 5. 返回 Document 记录
         ▼
┌─────────────────┐
│  前沿报告库     │
│  显示新文档     │
└─────────────────┘
```

### 5.2 插件 API 设计

#### 5.2.1 上传文档端点

**请求**：

```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: [PDF 文件]
title: "南非财政框架：挑战与改革选项"
source: "南非央行"
source_url: "https://www.resbank.co.za/..."
upload_date: "2026-04-01"
tags: "财政,政策"
```

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "南非财政框架：挑战与改革选项",
    "source": "南非央行",
    "file_path": "uploads/document/70b138594766102a8e356173ada79a8e2a2f35f739ddabd01ec3b96c666716c5.pdf",
    "file_size": 1234567,
    "upload_date": "2026-04-01",
    "download_url": "/storage/uploads/document/70b138594766102a8e356173ada79a8e2a2f35f739ddabd01ec3b96c666716c5.pdf"
  }
}
```

#### 5.2.2 直接 URL 上传端点

**请求**：

```http
POST /api/v1/documents/from-url
Content-Type: application/json

{
  "url": "https://www.imf.org/.../report.pdf",
  "title": "全球金融稳定报告",
  "source": "IMF",
  "tags": "金融,稳定"
}
```

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "...",
    "title": "全球金融稳定报告",
    "file_path": "uploads/document/{hash}.pdf",
    "download_url": "/storage/uploads/document/{hash}.pdf"
  }
}
```

### 5.3 插件存储规则

| 规则 | 说明 |
|------|------|
| **去重** | 使用 SHA256 哈希，重复文件不重复存储 |
| **路径** | `uploads/document/{SHA256}.pdf` |
| **元数据** | 标题、来源、URL、日期、标签 |
| **权限** | 需要用户认证（JWT Token） |
| **限流** | 单用户每分钟最多上传 10 个文件 |

---

## 6. 存储路径规范

### 6.1 路径生成规则

**FileService.generate_file_path()**

```python
def generate_file_path(
    original_filename: str,
    document_type: str,
    file_hash: Optional[str] = None,
) -> str:
    """
    生成文件存储路径

    Args:
        original_filename: 原始文件名
        document_type: 文档类型 (document/image/pdf/official)
        file_hash: 文件哈希（可选）

    Returns:
        相对路径: "uploads/{type}/{filename}"
    """
```

### 6.2 路径映射表

| 模块 | document_type | 目录 | 文件名规则 |
|------|---------------|------|-----------|
| 前沿报告库 | `document` | `uploads/document/` | `{SHA256}.pdf` |
| 公文库 | `official` | `storage/official_documents/` | `{UUID}.{ext}` |
| 图片转译 | `image` | `uploads/image/` | `{UUID}.{ext}` |
| PDF 专用 | `pdf` | `uploads/pdf/` | `{SHA256}.pdf` |

### 6.3 URL 访问规则

**本地访问**：

```
http://localhost:8000/storage/{relative_path}
```

**生产环境**：

```
https://api.example.com/storage/{relative_path}
```

**静态文件映射**（FastAPI）：

```python
# backend/main.py
app.mount("/storage", StaticFiles(directory="storage"), name="storage")
```

---

## 7. 文件去重策略

### 7.1 SHA256 哈希去重

**实现**：

```python
def get_file_hash(self, file_content: bytes) -> str:
    """计算文件的 SHA256 哈希值"""
    return hashlib.sha256(file_content).hexdigest()
```

**优势**：
- ✅ 相同文件只存储一份
- ✅ 节省存储空间
- ✅ 快速检测重复

**应用场景**：
- 前沿报告库：`Document.file_hash`
- 公文库：`OfficialDocument.file_hash`

### 7.2 去重流程

```
1. 接收文件上传
2. 计算 SHA256 哈希
3. 检查数据库中是否已存在该哈希
4. 如果存在 → 返回已有记录（不重复存储）
5. 如果不存在 → 保存文件 → 创建新记录
```

**API 示例**：

```python
# 检查文件是否已存在
existing_doc = await db.execute(
    select(Document).where(Document.file_hash == file_hash)
)
if existing_doc:
    return existing_doc  # 返回已有文档
```

---

## 8. 存储安全与备份

### 8.1 安全措施

| 措施 | 说明 | 状态 |
|------|------|------|
| **文件类型验证** | 只允许 PDF、图片、文档 | ✅ 已实现 |
| **文件大小限制** | 最大 100MB，图片 10MB | ✅ 已实现 |
| **路径遍历防护** | 使用 Path 对象，禁止 `..` | ✅ 已实现 |
| **用户认证** | JWT Token 验证 | ✅ 已实现 |
| **病毒扫描** | 未来集成 ClamAV | ⏳ 计划中 |

### 8.2 备份策略

**当前方案**：

```
本地存储 → 定期备份到 NAS/云存储
```

**备份脚本示例**：

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/storage_$DATE"

# 备份存储目录
rsync -av /path/to/backend/storage/ $BACKUP_DIR/

# 压缩
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR/

# 上传到云存储（可选）
# aws s3 cp $BACKUP_DIR.tar.gz s3://backup-bucket/
```

### 8.3 灾难恢复

**恢复流程**：

1. **数据丢失** → 从备份恢复文件
2. **数据库损坏** → 从 SQLite 备份恢复
3. **服务器故障** → 部署新服务器，恢复存储和数据库

**建议**：
- ✅ 每日自动备份
- ✅ 异地备份（不同机房/云）
- ✅ 定期测试恢复流程

---

## 9. 存储性能优化

### 9.1 当前优化

| 优化项 | 说明 | 效果 |
|--------|------|------|
| **哈希去重** | 避免重复存储 | 节省 30-50% 空间 |
| **分类存储** | 按类型分目录 | 提升检索速度 |
| **SHA256 索引** | 数据库索引 | 快速查找重复 |

### 9.2 未��优化

| 优化项 | 说明 | 优先级 |
|--------|------|--------|
| **CDN 加速** | 静态资源 CDN | 🔴 高 |
| **对象存储** | 迁移到云存储 | 🟡 中 |
| **缓存层** | Redis 缓存热点文件 | 🟢 低 |
| **压缩存储** | GZIP 压缩 PDF | 🟢 低 |

---

## 10. 常见问题 FAQ

### Q1: 文件存储在哪里？

**A**: 所有文件永久存储在本地服务器 `backend/storage/` 目录下。

### Q2: 为什么使用腾讯云 COS？

**A**: COS 仅用于 MinerU PDF 解析时的临时中转，解析完成后会自动删除。不永久存储在云端。

### Q3: 如何扩容存储？

**A**:
1. 本地扩容：添加硬盘，扩展 `storage/` 目录
2. 云存储迁移：配置云存储（OSS/S3），修改 FileService
3. 混合存储：热数据本地，冷数据云端

### Q4: 文件丢失怎么办？

**A**:
1. 检查备份：从每日备份恢复
2. 检查回收站：部分系统有软删除
3. 联系管理员：数据库可能仍有记录

### Q5: 如何迁移到新服务器？

**A**:
1. 导出数据库：`sqlite3 documents.db .dump > backup.sql`
2. 复制存储目录：`rsync -av storage/ new_server:/path/to/storage/`
3. 更新配置：修改 `STORAGE_ROOT`
4. 测试访问：验证文件 URL 可访问

---

## 11. 附录

### 11.1 相关文档

- [项目 README](README.md)
- [API 文档](http://localhost:8000/docs)
- [MinerU 集成文档](MINERU_INTEGRATION.md)
- [开发任务清单](DEVELOPMENT_TASKS.md)

### 11.2 代码位置

| 模块 | 文件路径 |
|------|---------|
| FileService | `backend/services/file_service.py` |
| 配置 | `backend/core/config.py` |
| 数据库模型 | `backend/models/` |
| API 端点 | `backend/api/endpoints/` |

### 11.3 联系方式

- **技术问题**：提交 GitHub Issue
- **紧急问题**：联系开发团队
- **文档更新**：提交 PR

---

**最后更新**：2026-04-01
**维护者**：开发团队
**文档版本**：v1.0
