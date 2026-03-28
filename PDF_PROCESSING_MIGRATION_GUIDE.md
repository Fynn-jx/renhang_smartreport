# PDF 处理方案迁移指南

## 🎯 目标

将 MinerU 替换为 PyMuPDF (fitz)，提供更快速、更稳定的 PDF 处理能力。

---

## 📊 方案对比

### MinerU（已弃用）

| 特性 | 说明 |
|------|------|
| **优点** | 输出格式好，支持复杂文档结构 |
| **缺点** | ❌ 需要 Docker 或复杂的安装 |
| | ❌ 启动慢，资源占用大 |
| | ❌ 配置复杂 |
| **状态** | ❌ 已弃用，正在清理 |

### PyMuPDF (fitz) ⭐ 推荐

| 特性 | 说明 |
|------|------|
| **优点** | ✅ 安装简单：`pip install PyMuPDF` |
| | ✅ 性能极快（比 PyPDF2 快 4-5 倍） |
| | ✅ 功能完整：文本、图片、表格、元数据 |
| | ✅ 纯 Python 调用，C 扩展优化 |
| | ✅ 跨平台，不需要 Docker |
| | ✅ 保留文档结构，生成 Markdown |
| **缺点** | 依赖 C 扩展（但已包含在 wheel 中） |
| **状态** | ✅ 当前推荐方案 |

---

## 🚀 迁移步骤

### 步骤 1：安装 PyMuPDF

```bash
pip install PyMuPDF
```

### 步骤 2：测试 PyMuPDF

```bash
python test_fitz.py
```

**预期输出**：
```
✅ PyMuPDF 安装: 通过
✅ fitz_extractor 导入: 通过
✅ PDF 提取: 通过
✅ Markdown 输出: 通过
```

### 步骤 3：替换代码

运行自动替换脚本：

```bash
replace_mineru_with_fitz.bat
```

**手动替换**（如果脚本失败）：

在以下 3 个文件中：
- `backend/services/translation_workflow_service.py`
- `backend/services/academic_to_official_service.py`
- `backend/services/document_translation_service.py`

**替换**：
```python
# 从这个
from services.mineru_extractor import mineru_extractor

# 改为
from services.fitz_extractor import fitz_extractor
```

**替换所有使用处**：
```python
# 从这个
if mineru_extractor is None:
    raise EnvironmentError("MinerU 不可用...")
result = mineru_extractor.extract_from_bytes(...)

# 改为
if fitz_extractor is None:
    raise EnvironmentError("PyMuPDF 不可用，请运行: pip install PyMuPDF")
result = fitz_extractor.extract_from_bytes(...)
```

### 步骤 4：清理 MinerU

```bash
cleanup_mineru.bat
```

**手动清理**（如果脚本失败）：

删除以下文件：
- `MinerU_安装指南.md`
- `MinerU_快速指南.md`
- `backend/services/mineru_extractor.py`
- `test_mineru.bat`
- `test_mineru.sh`
- `test_mineru_integration.py`
- `install_mineru.bat`
- `check_docker.bat`
- `debug_translation.py`

卸载 Python 包：
```bash
pip uninstall -y mineru magic-pdf
```

### 步骤 5：重启后端

```bash
cd backend
python main.py
```

---

## 🔍 验证迁移结果

### 1. 检查后端日志

应该看到：
```
[OK] 确保目录存在: storage
[OK] 数据库连接成功
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**不应该**看到：
```
[WARNING] PyMuPDF 未安装
```

### 2. 测试 API

访问 Swagger UI：
```
http://localhost:8000/docs
```

测试翻译功能：
1. 找到 `/workflows/translation` 接口
2. 上传一个 PDF 文件
3. 检查是否成功处理

### 3. 浏览器测试

1. 打开前端：`http://localhost:5174`
2. 进入"公文翻译"模块
3. 上传 PDF 文件
4. 检查是否正常翻译

---

## 📦 PyMuPDF 功能说明

### 基础功能

```python
from services.fitz_extractor import fitz_extractor

# 提取 PDF 内容
result = fitz_extractor.extract_from_bytes(pdf_bytes)

# 返回结果
{
    "content": "Markdown 格式的文档内容",
    "page_count": 10,
    "metadata": {...},
    "author": "作者",
    "title": "标题",
    "subject": "主题",
    "paragraphs": 50
}
```

### 高级功能

**提取图片**：
```python
images = fitz_extractor.extract_images(pdf_bytes, output_dir="./images")
# 返回: [{"page": 1, "index": 1, "width": 800, "height": 600, "format": "png"}]
```

**提取表格**（需要额外配置）：
```python
result = fitz_extractor.extract_from_bytes(
    pdf_bytes,
    extract_tables=True  # 启用表格检测
)
# 返回: {"tables": 5, ...}
```

---

## 🆚 对比其他方案

### pdfplumber

```bash
pip install pdfplumber
```

**优点**：表格提取好
**缺点**：速度慢，占用内存大

### PyPDF2（已有，但不推荐）

**优点**：纯 Python，无需安装
**缺点**：功能有限，不支持表格和图片

### pdfminer.six

**优点**：精确提取
**缺点**：非常慢，API 复杂

---

## ⚠️ 注意事项

### 1. 字符编码问题

PyMuPDF 默认使用 UTF-8 编码，如果遇到编码问题：

```python
# 指定编码
result = fitz_extractor.extract_from_bytes(pdf_bytes)
content = result["content"].encode("utf-8", errors="ignore").decode("utf-8")
```

### 2. 大文件处理

对于大 PDF 文件（>100MB），建议：

```python
# 分页处理
doc = fitz.open(stream=pdf_bytes, filetype="pdf")
for page in doc:
    # 处理单页
    text = page.get_text()
```

### 3. 图片提取

图片提取会增加处理时间，按需启用：

```python
result = fitz_extractor.extract_from_bytes(
    pdf_bytes,
    extract_images=True  # 只在需要时启用
)
```

---

## 🐛 故障排除

### 问题1：PyMuPDF 导入失败

```bash
ModuleNotFoundError: No module named 'fitz'
```

**解决方案**：
```bash
pip install PyMuPDF
```

### 问题2：提取的内容为空

**原因**：PDF 可能是扫描版（图片格式）

**解决方案**：
```bash
# 需要先 OCR 处理
pip install pytesseract
```

### 问题3：性能较慢

**优化**：
- 只提取需要的页数
- 禁用图片和表格提取
- 使用缓存

---

## 📚 参考资料

- PyMuPDF 官方文档：https://pymupdf.readthedocs.io/
- 安装指南：https://pymupdf.readthedocs.io/en/latest/installation/
- API 文档：https://pymupdf.readthedocs.io/en/latest/functions/

---

## ✅ 检查清单

迁移完成后，确认：

- [ ] PyMuPDF 已安装 (`pip list | grep PyMuPDF`)
- [ ] `test_fitz.py` 所有测试通过
- [ ] 3 个服务文件已替换导入
- [ ] MinerU 文件已清理
- [ ] 后端服务正常启动
- [ ] API 翻译功能正常
- [ ] 前端上传 PDF 成功
- [ ] 翻译结果正确显示

---

## 🎉 完成

现在你的系统使用更快速、更稳定的 PyMuPDF 进行 PDF 处理了！
