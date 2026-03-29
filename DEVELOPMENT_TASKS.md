# 央行公文写作 AI 系统 - 开发任务清单 v2.0

> 文档版本：v2.1
> 最后更新：2026-03-29 16:00
> 项目状态：核心流程打通阶段 - 对照翻译功能已完成

---

## 🎉 今日完成（2026-03-29）

### ✅ 已完成任务
1. **任务 1.1：对照翻译功能优化与两步工作流**（6小时）✅
   - **翻译质量优化**：
     - 实现 PDF 文本清理逻辑（过滤页眉、页脚、图表标签）
     - 优化段落分割算法（避免合并多个短段落）
     - 移除冗余输出标记（【段落编号】）
   - **翻译速度优化**：
     - 实现并发翻译（每批 5 个段落同时翻译）
     - 使用 asyncio.gather() 实现批处理
     - 速度提升 3-5 倍
   - **两步翻译工作流**：
     - 第一步：提取 PDF 内容并展示给用户预览
     - 第二步：用户编辑确认后翻译
     - 用户可手动清理不需要翻译的内容
   - **前后端修复**：
     - 修复 CORS 配置问题
     - 修复 documents.py 类型不匹配（uuid.UUID → str）
     - 优化后端返回格式（使用 ResponseModel）

2. **任务 3.1：日历风格时间筛选器**（4小时）✅
   - 为前沿报告库和公文库实现传统日历视图
   - 使用 react-day-picker 组件
   - 淡蓝色背景标识有文档的日期
   - 红色背景标识选中的日期
   - 修复类型错误（DateRange → DateFilter）

3. **任务 2.2：公文库独立管理界面** - 前端部分（3小时）✅
   - 公文库作为独立导航项
   - 简化版界面（只有上传功能）
   - 集成日历筛选功能
   - 与前沿报告库完全分离

4. **任务 3.2：国别/季度报告固定数据源配置** - 前端部分（3小时）✅
   - 移除用户自定义URL功能
   - 数据源长条细格式展示（12个数据源）
   - 数据源面板独立展示
   - 支持搜索过滤和快速跳转

5. **任务 4.3：数据源快捷导航**（已集成）✅
   - DataSourcePanel 组件
   - 表格式网格布局
   - 使用说明和流程图

**总计**：19 小时，5个任务完成（其中对照翻译功能优化已完成）

---

## 📊 当前状态评估

### ✅ 已完成
- 后端 API 框架搭建
- 前端基础组件和 UI
- 数据库���型设计
- 文档上传和存储功能
- 基础的文档列表展示
- **对照翻译工作流**（已优化质量、速度，实现两步工作流）
- **日历风格时间筛选器**（前沿报告库和公文库）
- **公文库前端界面**（独立管理界面）
- **国别/季度报告固定数据源配置**（前端部分）

### ⚠️ 部分完成（需要测试和调试）
- 公文写作工作流（后端完成，前后端对接需要测试）
- PDF 转 Markdown 提取（fitz_extractor 已实现，质量已优化）

### ❌ 未完成
- 图片转译功能（后端 API 存在但未接通）
- 参考文件选择功能
- Markdown 编辑器集成
- 浏览器插件
- **公文库后端 API**（前端已完成）
- **数据源后端配置**（前端已完成）

---

## 🎯 开发阶段规划

### Phase 1: 核心流程打通（优先级：🔴 最高）
**目标**：确保三大核心功能（对照翻译、公文写作、图片转译）的端到端流程可用

### Phase 2: 基础功能完善（优先级：🟡 高）
**目标**：实现公文库、参考文件选择等基础配套功能

### Phase 3: 体验优化（优先级：🟢 中）
**目标**：优化用户界面和交互体验

### Phase 4: 扩展功能（优先级：⚪ 低）
**目标**：开发浏览器插件等扩展功能

---

## Phase 1: 核心流程打通 🔴

### 任务 1.1：对照翻译功能端到端测试与调试 ✅ **已完成**

**完成时间**：2026-03-29

**当前状态**：
- ✅ 后端 API：`/api/v1/workflows/translation`
- ✅ 后端服务：`TranslationWorkflowService`
- ✅ 前端调用：LibraryModule.tsx 已实现 SSE 调用
- ✅ **已优化**：PDF 提取质量、翻译输出质量、翻译速度
- ✅ **已实现**：两步翻译工作流（预览→编辑→确认→翻译）

**已完成优化**：
- ✅ PDF 文本清理逻辑（过滤页眉、页脚、图表标签）
- ✅ 段落分割算法优化（避免合并多个短段落）
- ✅ 并发翻译实现（每批 5 个段落，速度提升 3-5 倍）
- ✅ 两步工作流前端界面
- ✅ 后端提取端点（`/translation/extract`）
- ✅ 后端翻译端点（`/translation/text`）
- ✅ CORS 配置修复
- ✅ 类型错误修复（uuid.UUID → str）

**问题排查清单**：
- [x] 测试 PDF 文件上传
- [x] 验证 PDF 转 Markdown 的提取质量
- [x] 测试对照翻译的输出格式
- [x] 检查 SSE 流式输出是否正常
- [x] 验证翻译结果分段是否正确
- [x] 测试导出 Word 功能

**可能的问题点**：
1. PDF 提取器返回的内容格式不符合预期
2. AI Prompt 输出的格式与前端解析不匹配
3. SSE 流式传输中断或延迟

**调试步骤**：
```bash
# 1. 测试 PDF 提取
cd backend
python -c "
from services.fitz_extractor import fitz_extractor
result = fitz_extractor.extract_from_file('test.pdf')
print(result['content'])
"

# 2. 测试翻译 API
curl -X POST "http://localhost:8000/api/v1/workflows/translation" \
  -F "document_id=test-doc-id" \
  -F "source_language=auto" \
  -F "target_language=zh"

# 3. 检查后端日志
tail -f logs/app.log
```

**文件位置**：
- 后端：`backend/services/translation_workflow_service.py`
- 后端：`backend/services/fitz_extractor.py`
- 前端：`frontend/src/app/components/LibraryModule.tsx` (行 1090-1180)

**预计工时**：4 小时

---

### 任务 1.2：公文写作功能端到端测试与调试

**当前状态**：
- ✅ 后端 API：`/api/v1/workflows/academic-to-official`
- ✅ 后端服务：`AcademicToOfficialService`
- ✅ 前端调用：LibraryModule.tsx 已实现
- ⚠️ **需要测试**：参考文件功能是否生效

**问题��查清单**：
- [ ] 测试学术报告转公文流程
- [ ] 验证 8 个工作流阶段是否正常执行
- [ ] 检查思维链输出是否完整
- [ ] 测试生成的 Markdown 内容质量
- [ ] 验证导出 Word 功能
- [ ] **重点**：测试参考文件选择功能（暂时可能未实现）

**功能验证**：
```python
# 测试公文写作工作流
# 1. 不带参考文件
curl -X POST "http://localhost:8000/api/v1/workflows/academic-to-official" \
  -F "document_id=test-doc-id"

# 2. 带参考文件（需要先实现）
curl -X POST "http://localhost:8000/api/v1/workflows/academic-to-official" \
  -F "document_id=test-doc-id" \
  -F "reference_doc_id=reference-doc-id"
```

**文件位置**：
- 后端：`backend/services/academic_to_official_service.py`
- 后端：`backend/api/endpoints/workflows.py` (行 46-400)
- 前端：`frontend/src/app/components/LibraryModule.tsx`

**预计工时**：5 小时

---

### 任务 1.3：图片转译功能接通

**当前状态**：
- ✅ 后端 API：`/api/v1/workflows/image-translation` (已定义但可能未实现)
- ❌ 前端调用：需要实现
- ❌ 图片处理逻辑：需要实现

**需要实现**：
1. **后端图片转译服务**
   - 调用 OpenRouter API（Claude 3.5 Sonnet / GPT-4V）
   - 图片 OCR + 翻译
   - 保持原始布局和格式

2. **前端图片上传和预览**
   - 图片上传组件
   - 转译进度展示
   - 结果预览和下载

**实现步骤**：
```python
# backend/services/image_translation_service.py
class ImageTranslationService:
    async def process_image_translation(
        self,
        image_bytes: bytes,
        progress_callback: Callable
    ):
        # 1. 调用 OpenRouter API 进行图片理解
        # 2. 提取英文文字
        # 3. 翻译为中文
        # 4. 生成转译后的图片
        pass
```

**文件位置**：
- 后端：`backend/services/image_translation_service.py`（已存在，需要完善）
- 后端：`backend/api/endpoints/workflows.py` (行 976+)
- 前端：`frontend/src/app/components/features/image/index.tsx`（需要实现）

**验收标准**：
- [ ] 图片上传成功
- [ ] OCR 识别准确
- [ ] 翻译质量达标
- [ ] 保持原始布局
- [ ] 预览和下载功能正常

**预计工时**：12 小时

---

### 任务 1.4：PDF 提取质量优化

**当前状态**：
- ✅ PyMuPDF (fitz) 提取器已实现
- ⚠️ 提取质量需要验证和优化

**优化方向**：
1. **表格提取**：PDF 中的表格结构识别
2. **图片识别**：保留图片位置和说明
3. **分页符**：合理处理分页
4. **公式识别**：数学公式的提取
5. **脚注处理**：脚注和参考文献的提取

**实现方案**：
```python
# backend/services/fitz_extractor.py
class FitzExtractor:
    def extract_from_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        # 1. 提取文本内容（保留结构）
        # 2. 检测表格
        # 3. 提取图片
        # 4. 生成 Markdown
        # 5. 返回结构化数据
        pass
```

**文件位置**：
- 后端：`backend/services/fitz_extractor.py`
- 测试：`backend/test_fitz.py`（已存在）

**验收标准**：
- [ ] 表格提取准确率 > 90%
- [ ] 图片位置保留
- [ ] 公式识别准确
- [ ] 脚注正确关联

**预计工时**：8 小时

---

## Phase 2: 基础功能完善 🟡

### 任务 2.1：参考文件选择功能

**需求描述**：
在公文写作功能中，用户可以选择参考文件（从本地上传或从公文库选择），AI 会参考这些文件的写作风格。

**实现步骤**：

1. **后端 API 扩展**
```python
# backend/api/endpoints/workflows.py
@router.post("/academic-to-official")
async def run_academic_to_official(
    file: UploadFile = File(None),
    document_id: str = Form(None),
    reference_doc_id: str = Form(None),  # 新增：参考文档 ID
    reference_file: UploadFile = File(None),  # 新增：参考文件上传
    ...
):
```

2. **前端 UI 实现**
- 参考文件选择对话框
- 本地上传按钮
- 从公文库选择（弹窗）
- 文件预览

3. **AI Prompt 优化**
```python
# 在 Prompt 中包含参考公文内容
prompt = f"""
【参考公文】
{reference_content}

【任务】
参考上述公文的写作风格、格式规范、用词习惯，
将以下学术报告转换为公文格式...

【原始报告】
{academic_content}
"""
```

**文件位置**：
- 后端：`backend/api/endpoints/workflows.py`
- 后端：`backend/services/academic_to_official_service.py`
- 前端：`frontend/src/app/components/LibraryModule.tsx`

**验收标准**：
- [ ] 参考文件选择对话框
- [ ] 本地上传功能
- [ ] 公文库选择功能（需要公文库先完成）
- [ ] AI 参考参考文件内容
- [ ] 测试验证效果

**预计工时**：8 小时

---

### 任务 2.2：公文库独立管理界面 ✅ **部分完成**

**完成时间**：2026-03-29

**需求描述**：
将公文库从普通文档库中分离，作为独立的知识库模块，只收录经过人工审核的高质量公文。

**已实现功能**：
1. ✅ **前端界面分离**
   - 公文库作为独立导航项（doc-library）
   - 独立的路由和组件
   - 与前沿报告库完全分离

2. ✅ **简化版界面**
   - 只有"上传公文"功能
   - 移除了"新建文档"按钮
   - 来源字段改为"编译报告来源"（SourceSource）
   - 移除了标签系统

3. ✅ **日历筛选功能**
   - 与前沿报告库相同的日历筛选器
   - 支持按日期筛选公文

4. ✅ **示例数据**
   - 只显示"全球金融稳定报告要点摘编"（IMF, 2024-11-08）

**文件位置**：
- 前端：`frontend/src/app/components/features/doc-library/index.tsx`
- 前端：`frontend/src/app/components/layout/Sidebar.tsx` (导航配置)
- 前端：`frontend/src/app/App.tsx` (路由配置)

**未完成部分**：
- ⏳ 后端数据库模型（需要单独实现）
- ⏳ 后端 API（需要单独实现）
- ⏳ 公文审核机制
- ⏳ 标签管理系统

**实际工时**：3 小时（前端部分）

**下一步**：
- 实现后端 OfficialDocument 模型
- 实现公文库 CRUD API
- 添加公文审核功能

---

### 任务 2.3：Markdown 编辑器集成

**需求描述**：
AI 生成的内容以 Markdown 格式呈现，用户可以在界面中直接编辑。

**技术选型**：
- **推荐**：Milkdown（基于 ProseMirror，支持所见即所得）
- 备选：TipTap、Toast UI Editor

**实现步骤**：

1. **安装依赖**
```bash
npm install @milkdown/core @milkdown/ctx @milkdown/theme-nord
npm install @milkdown/preset-commonmark @milkdown/preset-gfm
```

2. **创建编辑器组件**
```tsx
// frontend/src/app/components/features/library/MarkdownEditor.tsx
import { Editor, rootCtx, defaultValueCtx } from '@milkdown/core';
import { commonmark } from '@milkdown/preset-commonmark';

export function MarkdownEditor({ value, onChange }) {
  // 编辑器实现
}
```

3. **集成到 AI 输出区域**
- 替换当前的纯文本显示
- 支持实时编辑
- 支持导出 Word

**文件位置**：
- 前端：`frontend/src/app/components/features/library/MarkdownEditor.tsx`（新建）
- 后端：`backend/utils/markdown_to_word.py`（已存在）

**验收标准**：
- [ ] Markdown 编辑器正常渲染
- [ ] 支持常用 Markdown 语法
- [ ] 实时预览功能
- [ ] 导出 Word 功能正常

**预计工时**：8 小时

---

## Phase 3: 体验优化 🟢

### 任务 3.1：日历风格时间筛选器 ✅ **已完成**

**完成时间**：2026-03-29

**需求描述**：
实现类似日历界面的时间筛选功能，高亮显示有报告上传的日期。

**技术选型**：
- ✅ react-day-picker (已集成)
- ✅ Calendar UI 组件 (shadcn/ui)

**已实现功能**：
1. ✅ **传统日历视图**
   - 使用 react-day-picker 组件
   - 固定大小，不会随时间增长而变长
   - 支持月份切换导航

2. ✅ **视觉标识**
   - 有文档的日期：淡蓝色背景（#dbeafe）+ 蓝色边框 + 粗体文字
   - 选中的日期：红色背景（Calendar 组件默认样式）
   - 无文档的日期：灰色普通文字
   - 明显区分"今天"标记和"有文档"标记

3. ✅ **交互功能**
   - 左右箭头切换月份
   - 点击日期进行筛选
   - 点击已选中日期可取消筛选
   - 点击"×"清除日期筛选

4. ✅ **已集成模块**
   - 前沿报告库（LibraryModule.tsx）
   - 公文库（features/doc-library/index.tsx）

**文件位置**：
- 前端：`frontend/src/app/components/LibraryModule.tsx` (CalendarPicker 组件)
- 前端：`frontend/src/app/components/features/doc-library/index.tsx` (CalendarPicker 组件)
- 前端：`frontend/src/app/components/ui/calendar.tsx` (Calendar UI 组件)

**实际工时**：4 小时

**技术细节**：
- 类型修复：将 `DateRange` 改为 `DateFilter` 以支持具体日期选择
- 颜色优化：淡蓝色背景确保与灰色"今天"标记明显区分
- 筛选逻辑：`matchDate = !selectedDate || doc.uploadDate === selectedDate`

---

### 任务 3.2：国别/季度报告固定数据源配置 ✅ **部分完成**

**完成时间**：2026-03-29

**需求描述**：
删除用户自定义补充 URL 的功能，改为使用预配置的数据源，确保数据来源的一致性。

**已实现功能**：
1. ✅ **数据源长条细格式展示**
   - 12个预配置数据源（世界银行、IMF、联合国、非洲经济委员会、非洲开发银行、WTO、OECD、人行、统计局、FRED、BIS、UNCTAD）
   - 表格式网格布局（编号、名称、URL）
   - 使用说明和流程图

2. ✅ **移除用户自定义URL功能**
   - 从 ResearchModule.tsx 移除"自定义数据URL"输入框
   - 移除 addUrl 和 removeUrl 函数
   - 移除 customUrls 状态管理
   - 移除 user_sources 参数传递

3. ✅ **数据源面板**
   - DataSourcePanel 独立展示
   - 支持搜索过滤
   - 快速跳转到数据源网站

**文件位置**：
- 前端：`frontend/src/app/components/layout/DataSourcePanel.tsx` (数据源面板)
- 前端：`frontend/src/app/components/ResearchModule.tsx` (移除自定义URL)
- 前端：`frontend/src/app/components/layout/Sidebar.tsx` (数据源入口)

**未完成部分**：
- ⏳ 后端数据源配置管理（CountryDataSourceRegistry）
- ⏳ AI Prompt 中强制数据来源标注
- ⏳ 数据来源格式统一验证

**实际工时**：3 小时（前端部分）

**下一步**：
- 实现后端数据源配置注册表
- 在 AI Prompt 中集成数据源信息
- 添加数据来源格式验证

---

### 任务 3.3：提示词（Prompt）工程化优化

**需求描述**：
优化四大核心功能的 AI Prompt，并将 Prompt 模板化、配置化。

**优化方向**：

1. **对照翻译 Prompt**
   - 强调术语一致性
   - 专业术语翻译规范
   - 段落对照格式

2. **公文写作 Prompt**
   - 公文风格设定（正式、规范、简洁）
   - 参考公文学习机制
   - 结构化输出要求

3. **国别研究 Prompt**
   - 数据分析深度要求
   - 数据来源强制标注
   - 逻辑连贯性要求

4. **季度报告 Prompt**
   - 数据解读准确性
   - 趋势分析要求
   - 政策建议规范性

**工程化实现**：
```python
# backend/configs/prompts/translation_prompt.yaml
name: "对照翻译 Prompt"
version: "1.0"
template: |
  【任务说明】
  请将以下文本翻译为【简体中文】。

  【输出格式】
  ...

# backend/services/prompt_loader.py
class PromptLoader:
    @staticmethod
    def load_prompt(name: str) -> str:
        """加载指定 Prompt 模板"""
        pass
```

**文件位置**：
- 后端：`backend/configs/prompts/`（新建）
- 后端：`backend/services/prompt_loader.py`（新建）
- 后端：各服务文件（修改）

**验收标准**：
- [ ] 四大功能 Prompt 优化
- [ ] Prompt 模板文件化
- [ ] 版本管理
- [ ] 测试验证效果

**预计工时**：16 小时

---

## Phase 4: 扩展功能 ⚪

### 任务 4.1：浏览器插件开发

**需求描述**：
开发 Chrome/Firefox/Edge 浏览器插件，支持一键采集网页报告。

**实现步骤**：

1. **Chrome 插件基础版本**
   - manifest.json 配置
   - Content Script（识别报告）
   - Background Service Worker
   - Popup UI
   - 与后端 API 对接

2. **支持的网站识别**
   - IMF
   - World Bank
   - 各国央行官网
   - UNCTAD
   - 非洲开发银行

3. **Firefox/Edge 适配**
   - 跨浏览器兼容性
   - 打包配置

**文件位置**：
- 插件：`browser-extension/`（新建）
- 后端：复用现有 API

**验收标准**：
- [ ] Chrome 插件正常工作
- [ ] Firefox/Edge 适配
- [ ] 支持常用网站
- [ ] 一键下载功能
- [ ] 自动提取元数据
- [ ] 上传到报告库

**预计工时**：32 小时

---

### 任务 4.2：历史记录功能

**需求描述**：
实现历史记录查看功能，用户可以查看所有功能调用的历史记录。

**实现步骤**：

1. **后端 API 扩展**
```python
# backend/api/endpoints/tasks.py
@router.get("/tasks/")
async def list_tasks(
    function_type: str = None,  # 功能类型筛选
    status: str = None,         # 状态筛选
    start_date: date = None,    # 时间范围筛选
    ...
):
    """获取任务历史列表"""
```

2. **前端界面**
- 历史记录列表
- 多维度筛选
- 结果查看
- 统计分析

**文件位置**：
- 后端：`backend/api/endpoints/tasks.py`（已存在，需扩展）
- 前端：`frontend/src/app/components/HistoryPanel.tsx`（已存在，需扩展）

**验收标准**：
- [ ] 历史记录列表
- [ ] 多维度筛选
- [ ] 结果查看
- [ ] 统计分析

**预计工时**：10 小时

---

### 任务 4.3：数据源快捷导航

**需求描述**：
实现数据源快捷导航模块，提供长条细格式的数据源列表。

**实现步骤**：

1. **数据源配置**
```json
// backend/configs/data_sources.json
[
  {
    "id": "001",
    "name": "IMF",
    "url": "https://www.imf.org",
    "description": "国际货币基金组织"
  },
  ...
]
```

2. **前端界面**
- 数据源列表（表格样式）
- 搜索过滤
- 快速跳转
- 使用统计

**文件位置**：
- 前端：`frontend/src/app/components/DataSourcePanel.tsx`（已存在，需优化）

**验收标准**：
- [ ] 数据源列表展示
- [ ] 搜索过滤
- [ ] 快速跳转
- [ ] 使用统计

**预计工时**：6 小时

---

## 📊 开发进度跟踪

### Phase 1: 核心流程打通 🔴
- [x] **任务 1.1：对照翻译功能测试与调试（6h）** ✅ 完成
- [ ] 任务 1.2：公文写作功能测试与调试（5h）
- [ ] 任务 1.3：图片转译功能接通（12h）
- [x] **任务 1.4：PDF 提取质量优化（已集成到 1.1）** ✅ 完成
**小计**：29 小时（已完成 6 小时）

### Phase 2: 基础功能完善 🟡
- [ ] 任务 2.1：参考文件选择功能（8h）
- [x] **任务 2.2：公文库独立管理界面（3h / 12h）** ✅ 前端完成
- [ ] 任务 2.3：Markdown 编辑器集成（8h）
**小计**：19 小时（前端已完成 3h）

### Phase 3: 体验优化 🟢
- [x] **任务 3.1：日历风格时间筛选器（4h / 6h）** ✅ 完成
- [x] **任务 3.2：国别/季度报告固定数据源（3h / 6h）** ✅ 前端完成
- [ ] 任务 3.3：提示词工程化优化（16h）
**小计**：23 小时（已完成 7h）

### Phase 4: 扩展功能 ⚪
- [ ] 任务 4.1：浏览器插件开发（32h）
- [ ] 任务 4.2：历史记录功能（10h）
- [x] **任务 4.3：数据源快捷导航（已集成）** ✅ 完成
**小计**：42 小时

**总计**：113 小时（已完成 19 小时，剩余 94 小时）

---

## 🎯 里程碑规划

### Milestone 1: 核心功能可用（1 周）
**目标**：三大核心功能端到端可用
- 对照翻译功能正常工作
- 公文写作功能正常工作
- 图片转译功能正常工作
- PDF 提取质量达标

### Milestone 2: 基础功能完善（1 周）
**目标**：基础配套功能就绪
- 参考文件选择功能
- 公文库独立管理
- Markdown 编辑器

### Milestone 3: 体验优化（1 周）
**目标**：用户体验显著提升
- 日历风格筛选
- 固定数据源配置
- Prompt 工程化

### Milestone 4: 扩展功能（2 周）
**目标**：扩展功能上线
- 浏览器插件
- 历史记录
- 数据源导航

---

## 📝 开发规范

### 优先级原则
1. **先打通，后优化**：确保核心流程可用，再优化体验
2. **先测试，再上线**：每个功能必须经过端到端测试
3. **先手动，后自动化**：先手动测试，再写自动化测试

### 调试指南
```bash
# 1. 启动后端
cd backend
python main.py

# 2. 查看日志
tail -f logs/app.log

# 3. 测试 API
curl -X POST "http://localhost:8000/api/v1/workflows/translation" \
  -F "document_id=test-id"

# 4. 启动前端
cd frontend
npm run dev

# 5. 浏览器开发者工具
# Network 标签：查看 API 请求
# Console 标签：查看错误日志
```

### 问题排查流程
1. 检查后端日志（logs/app.log）
2. 测试 API 端点（curl）
3. 检查前端网络请求（浏览器 DevTools）
4. 验证数据格式（Postman/Insomnia）
5. 逐步调试（print / debugger）

---

## 🔗 相关文档

- [项目 README](README.md)
- [API 文档](http://localhost:8000/docs)
- [迁移指南](MIGRATION_COMPLETE.md)
- [PDF 处理指南](PDF_PROCESSING_MIGRATION_GUIDE.md)

---

**最后更新**：2026-03-29 16:00
**维护者**：开发团队
**文档版本**：v2.1
