# MinerU精准解析API集成文档

> 本文档说明MinerU PDF转Markdown功能如何集成到项目中

## 概述

MinerU是精准的PDF解析服务，可以将PDF转换为高质量Markdown，自动去除页眉、页脚、脚注等元素。

## 架构设计

### 流程图

```
本地PDF文件
    ↓
上传到腾讯云COS（公开访问URL）
    ↓
MinerU从COS URL拉取并解析
    ↓
返回高质量Markdown
```

### 为什么用COS中转？

1. **稳定性**：MinerU内置的文件上传API不稳定，经常失败
2. **公开访问**：COS设置为公开读取，MinerU可以直接拉取
3. **成本低**：COS存储和流量费用低

## 修改的文件

### 1. `backend/core/config.py`

**新增配置项：**

```python
# ==================== MinerU 配置 ====================
MINERU_API_KEY: str = ""           # MinerU API密钥
MINERU_BASE_URL: str = "https://mineru.net"
MINERU_ENABLED: bool = True        # 是否启用MinerU

# ==================== 腾讯云 COS 配置 ====================
TENCENT_COS_SECRET_ID: str = ""    # 腾讯云SecretId
TENCENT_COS_SECRET_KEY: str = ""    # 腾讯云SecretKey
TENCENT_COS_REGION: str = "ap-guangzhou"
TENCENT_COS_BUCKET: str = "gongwen-1410891391"
```

**环境变量配置（`.env`）：**

```env
# MinerU
MINERU_API_KEY=your_mineru_api_key_here
MINERU_BASE_URL=https://mineru.net

# 腾讯云COS（可选，没配置则使用内置上传）
TENCENT_COS_SECRET_ID=your_secret_id
TENCENT_COS_SECRET_KEY=your_secret_key
TENCENT_COS_REGION=ap-guangzhou
TENCENT_COS_BUCKET=your_bucket_name
```

### 2. `backend/services/mineru_service.py`

**核心修改：**

1. **新增COS上传方法 `_upload_to_cos()`**
   - 使用 `cos-python-sdk-v5` 上传到腾讯云COS
   - 返回公开访问URL

2. **修改 `_upload_file()` 方法**
   - 优先使用COS上传（稳定）
   - 失败时回退到MinerU内置上传

3. **保留的端点：**
   - `parse_pdf_to_markdown(file_path)` - 本地文件路径
   - `parse_pdf_by_url(pdf_url)` - 直接URL

**新增API端点：**
```
POST /api/v1/workflows/mineru-parse/url      # SSE流式
POST /api/v1/workflows/mineru-parse/url/sync # 同步返回JSON
```

**请求示例：**
```bash
curl -X POST http://localhost:8000/api/v1/workflows/mineru-parse/url/sync \
  -H "Content-Type: application/json" \
  -d '{"pdf_url": "https://your-cos-url.com/file.pdf"}'
```

### 3. `backend/services/translation_workflow_service.py`

**修改位置：** `_extract_text_from_document()` 方法

**修改逻辑：**
```python
if file_ext == '.pdf':
    # 优先使用MinerU
    if settings.MINERU_ENABLED and settings.MINERU_API_KEY:
        try:
            # 1. 保存到临时文件
            # 2. 上传到COS
            # 3. MinerU解析
            # 4. 返回Markdown
        except:
            # 回退到PyMuPDF
```

**效果：** 对照翻译功能的PDF提取自动使用MinerU

### 4. `backend/services/academic_to_official_service.py`

**修改位置：** `_extract_document()` 方法

**效果：** 公文写作功能的PDF提取自动使用MinerU

### 5. `backend/services/document_translation_service.py`

**修改位置：** `_extract_text_from_document()` 方法

**效果：** 文档翻译功能的PDF提取自动使用MinerU

## 使用方式

### 方式一：直接调用MinerU API

```python
from services.mineru_service import mineru_service

# 从文件路径
content = await mineru_service.parse_pdf_to_markdown("/path/to/file.pdf")

# 从URL
content = await mineru_service.parse_pdf_by_url("https://example.com/file.pdf")
```

### 方式二：使用已集成的工作流

```bash
# 公文写作（会自动用MinerU提取）
curl -X POST http://localhost:8000/api/v1/workflows/academic-to-official \
  -F "file=@document.pdf"

# 对照翻译（会自动用MinerU提取）
curl -X POST http://localhost:8000/api/v1/workflows/translation/extract \
  -F "file=@document.pdf"
```

## 依赖安装

```bash
pip install cos-python-sdk-v5
```

## 注意事项

1. **COS桶需要设置公开读取权限**，或者确保桶策略允许跨账号访问

2. **回退机制**：如果COS上传失败，会自动回退到MinerU内置上传

3. **临时文件清理**：上传后会清理COS临时文件

4. **SSL证书**：httpx客户端使用 `verify=False` 忽略SSL验证（因为证书问题）

## 故障排查

### 问题：COS上传失败403

**检查：**
- SecretId/SecretKey是否正确
- 桶名称和区域是否匹配
- 密钥是否有写权限

### 问题：MinerU任务失败 "failed to read file"

**原因：** 文件URL无法访问或文件损坏

**解决：**
- 确保COS桶设置为公开读取
- 检查PDF文件是否完整

### 问题：MinerU回退到PyMuPDF

**原因：** MinerU API Key无效或网络问题

**解决：**
- 检查 `MINERU_API_KEY` 环境变量
- 确认API Key有权限

## API响应示例

```json
{
  "success": true,
  "content": "# South Africa's Fiscal Framework...\n\n正文内容...",
  "stats": {
    "chars": 59351
  }
}
```

## 后续优化建议

1. **COS预签名URL**：不用公开桶，用预签名URL更安全
2. **文件缓存**：已解析的PDF缓存到COS，避免重复解析
3. **异步处理**：大文件使用异步任务队列
4. **PDF直接上传**：前端直接上传到COS，后端只返回COS URL
