# 央行公文写作 AI 系统

## 📖 项目简介

这是一个基于 FastAPI + React 的企业级文档管理与 AI 处理平台，提供 Zotero 式的文档管理能力和六大 AI 工作流，专为央行公文写作场景设计。系统集成了多模型协作架构（DeepSeek-V3 + Kimi-K2.5 + Gemini-3.1-Pro + GLM-5），支持 SSE 流式输出、MinerU 高精度 PDF 解析、插拔式数据源配置等企业级特性。

### 核心功能

1. **前沿报告库** - Zotero 风格的文档管理系统，支持 PDF、Word、TXT、Markdown 等多种格式，集成对照翻译与公文写作
2. **公文库** - 独立的知识库，用于管理经过人工审核的高质量公文模板，支持审核状态管理
3. **公文对照翻译** - 两步工作流（提取→编辑→翻译），支持段落对照格式与 Word 导出
4. **学术报告转公文** - 10 阶段多模型协作工作流，支持严谨完整型/简洁概括型两种风格
5. **国别深度研究** - 自动化国别研究报告生成，支持非洲 54 国插拔式数据源配置
6. **季度报告生成** - 金融市场与宏观经济分析报告自动生成，8 阶段工作流
7. **图片转译** - 图片中的英文文字提取与中文翻译，保持原始布局
8. **浏览器插件** - 人行智汇，一键采集网页 PDF 到报告库

---

## 🎯 功能详解

### 1. 前沿报告库（核心文档管理）

**功能概述**：
前沿报告库是系统的核心文档管理模块，用户可以从本地电脑上传或通过浏览器插件直接爬取前沿报告。

**核心特性**：
- 📁 **多种上传方式**：本地上传 / 浏览器插件一键爬取
- 📅 **日历风格筛选**：按时间维度可视化展示
- 🏷️ **来源分类管理**：按信息来源自动分类（世界银行/IMF/联合国等 14 种来源）
- 👁️ **PDF 实时预览**：点击报告后左侧显示 PDF 预览
- 🔄 **两大核心功能**：对照翻译 / 公文写作
- 🎨 **AI 写作舱**：分屏视图，左侧原始文献 + 右侧 AI 写作结果
- 🗑️ **文档管理**：完整的 CRUD 操作，支持删除、下载
- 🔍 **哈希去重**：SHA256 文件哈希避免重复上传

**技术实现**：
- 前端：React + TypeScript + Tailwind CSS + Framer Motion
- 后端：FastAPI + SQLAlchemy 2.0 异步
- AI：DeepSeek-V3 / Kimi-K2.5 / Gemini-3.1-Pro（通过硅基流动 + OpenRouter）
- PDF 提取：MinerU（高精度）/ PyMuPDF（回退）

---

### 2. 公文库（独立知识库）

**功能概述**：
独立的知识库模块，用于管理经过人工审核的高质量公文模板，作为 AI 写作的风格参考库。

**核心特性**：
- ✅ 独立管理界面（与前沿报告库分离）
- ✅ 审核状态管理（verified_by / verified_at / is_verified）
- ✅ 来源机构筛选（世界银行/IMF/联合国/非洲开发银行/WTO/OECD/中国人民银行/国家统计局等）
- ✅ DOCX / PDF / TXT / Markdown 格式支持
- ✅ 日历日期筛选
- ✅ 文件哈希去重

---

### 3. 公文对照翻译

**功能概述**：
专业公文对照翻译，支持两步工作流与段落对照格式。

**工作流**：
1. **提取阶段**：使用 MinerU/PyMuPDF 提取 PDF 文本内容
2. **编辑阶段**：用户预览提取内容，可编辑修改
3. **翻译阶段**：DeepSeek-V3 逐段翻译，每 5 段一批并发处理

**核心特性**：
- 📝 两步工作流（提取→编辑→翻译）
- ⚡ 并发翻译（速度提升 3-5 倍）
- 📄 段落对照格式
- 📥 多格式导出：TXT / Word（DOCX）/ Markdown
- 🔄 SSE 流式输出
- 🧹 智能文本清理（移除参考文献、页眉页脚、目录等）

**独立文档翻译服务**：
- 支持从已有文档 ID 或上传文件创建翻译任务
- 后台异步处理
- 双语对照 Word 导出

---

### 4. 学术报告转公文

**功能概述**：
将学术论文/研究报告自动转换为正式公文格式，采用 10 阶段多模型协作工作流。

**工作流阶段**：
1. 文档提取 → 2. 知识检索 → 3. 大纲生成 → 4. 标题提取 → 5. 内容整理 → 6. 章节并发写作 → 7. 模板转换 → 8. 内容整合润色 → 9. 内容检查 → 10. 最终调整

**多模型协作**：
| 阶段 | 模型 | 说明 |
|------|------|------|
| 大纲生成 | Kimi-K2.5 | 生成 JSON 格式大纲，大文档使用分层摘要策略 |
| 章节写作 | DeepSeek-V3 | 并发写作各章节（最大 3 并发） |
| 内容整合 | Gemini-3.1-Pro | 渐进式整合润色（支持超长文档分段整合） |
| 内容检查 | Kimi-K2.5 | 数据一致性、术语统一性检查 |
| 最终调整 | Kimi-K2.5 | 格式调整（去除英文缩写、"引言"改"按"等） |

**核心特性**：
- 🎨 两种风格模式：`complete`（严谨完整型）/ `concise`（简洁概括型）
- 📚 大文档分层处理（超过 150000 字符自动分层摘要）
- ⚡ 并发章节写作（信号量控制）
- 📥 导出 Word 文档
- 🔍 完整调试日志（每阶段记录输入/输出/模型/提示词）

---

### 5. 国别深度研究

**功能概述**：
基于插拔式数据源配置，系统自动爬取数据、分析数据、生成《[国家名称]经济与政治概况》。

**工作流阶段**（7 阶段）：
1. 配置加载 → 2. 数据采集（并发） → 3. 经济分析 → 4. 政治分析 → 5. 外交分析 → 6. 报告生成 → 7. 质量审核

**支持国家**：非洲全部 54 国（埃及、肯尼亚、尼日利亚、南非等）

**数据源类型**：Trading Economics / 央行 / 财政部 / 新闻社 / 政府门户 / IMF / 世界银行 / 中国外交部 / 英为财情 / 自定义

**多模型协作**：
| 阶段 | 模型 |
|------|------|
| 经济/政治/外交分析 | DeepSeek-V3 |
| 质量审核 | DeepSeek-V3 |
| 报告生成 | GLM-5 |

**核心特性**：
- 🔌 插拔式数据源配置（`backend/configs/country_data_sources.py`）
- 🕷️ Firecrawl 网页爬取（最大 5 并发）
- 📊 质量审核（数据来源标注、双币种展示、URL 检查）
- 🔄 SSE 流式输出 + 思维链节点展示
- ➕ 支持用户自定义补充数据源

---

### 6. 季度报告生成

**功能概述**：
自动生成《[国家名称]宏观经济与金融运行情况季报》，复用国别研究架构。

**工作流阶段**（8 阶段）：
1. 配置加载 → 2. 数据采集 → 3. 宏观经济分析 → 4. 金融市场分析 → 5. 政策分析 → 6. 风险评估 → 7. 报告生成 → 8. 质量审核

**技术实现**：
- 数据源配置：`backend/configs/country_data_sources.py`
- 爬虫服务：Firecrawl
- AI：DeepSeek-V3（分析）+ GLM-5（报告生成）
- 流式输出：SSE

---

### 7. 图片转译

**功能概述**：
将图片中的英文翻译为中文，保持原始布局和格式。

**技术实现**：
- AI：Gemini-3-Pro-Image-Preview（通过 OpenRouter）
- 图片处理：Pillow
- 支持格式：JPG / PNG / GIF / WebP / BMP
- 后台任务处理模式
- 原图/译图对比滑块（前端交互式查看器）
- 批量转译（最多 5 张）

---

### 8. 人行智汇（浏览器插件）

**功能概述**：
一键采集网页中的 PDF 文件，保存到本地或上传到报告库。基于 Manifest V3 规范。

**核心特性**：
- 🌐 **智能 PDF 识别**：自动扫描 `<a>` / `<embed>` / `<iframe>` / `<object>` 中的 PDF 链接
- ⚡ **批量操作**：支持多选批量下载或上传
- 📂 **报告库同步**：直接保存 PDF 到云端报告库
- ✏️ **标题行内编辑**：点击即可修改 PDF 标题
- 🔄 **多浏览器支持**：Chrome / Edge 完全支持
- 🖱️ **右键菜单**：下载 PDF / 保存到云端 / 扫描页面 / 预览 PDF
- ⌨️ **快捷键**：`Ctrl+Shift+P` 打开弹窗 / `Ctrl+Shift+S` 扫描页面 / `Ctrl+Shift+D` 下载全部
- 🏷️ **来源自动识别**：根据域名自动匹配报告来源（世界银行/IMF/联合国等 9 种来源）

**安装方法**：
1. 打开 `chrome://extensions/`
2. 开启「开发者模式」
3. 点击「加载解包的扩展程序」
4. 选择 `browser-extension` 文件夹

**项目结构**：
```
browser-extension/
├── manifest.json      # 扩展配置（Manifest V3）
├── popup/             # 弹窗页面（HTML + JS + CSS）
├── content/           # 网页注入脚本（PDF 嗅探器）
├── background/        # 后台服务（右键菜单、快捷键、上传）
└── icons/             # 图标（16/48/128px）
```

---

## 🏗️ 技术架构

### 后端技术栈

- **框架**: FastAPI 0.109+
- **数据库**: PostgreSQL 15+ (SQLAlchemy 2.0 异步)
- **缓存**: Redis 7+
- **AI 服务**: DeepSeek-V3 / Kimi-K2.5（硅基流动）+ Gemini-3.1-Pro / Gemini-3-Pro（OpenRouter）+ GLM-5
- **向量检索**: pgvector / Qdrant（预留）
- **网页抓取**: Firecrawl
- **文档处理**: PyMuPDF, python-docx, MinerU（高精度 PDF 解析）
- **云存储**: 腾讯云 COS（MinerU 文件上传）

### 前端技术栈

- **框架**: React 18.3 + TypeScript
- **构建**: Vite 6.3
- **UI**: Radix UI + shadcn/ui + Tailwind CSS 4
- **动画**: Motion (Framer Motion)
- **日历**: react-day-picker
- **分屏**: react-resizable-panels

### 浏览器插件技术栈

- **规范**: Manifest V3
- **API**: chrome.downloads / chrome.storage / chrome.contextMenus / chrome.notifications
- **通信**: chrome.runtime.sendMessage（Content Script ↔ Popup ↔ Background）

---

## 📁 项目结构

```
renhang_smartreport/
├── backend/
│   ├── api/
│   │   ├── dependencies.py         # 依赖注入（简化认证）
│   │   └── v1/
│   │       ├── api.py              # 路由聚合
│   │       └── endpoints/
│   │           ├── documents.py            # 文档管理 API
│   │           ├── official_documents.py   # 公文库 API
│   │           ├── workflows.py            # 工作流 API（翻译/写作/研究/报告）
│   │           ├── image_translation.py    # 图片转译 API
│   │           ├── document_translation.py # 公文翻译 API
│   │           ├── tasks.py                # 任务管理 API（待实现）
│   │           ├── knowledge.py            # 知识库 API（待实现）
│   │           └── storage.py              # 文件存储 API（待实现）
│   ├── core/
│   │   ├── config.py               # 配置管理
│   │   ├── database.py             # 数据库连接
│   │   ├── security.py             # 安全相关
│   │   ├── constants.py            # 常量
│   │   └── redis.py                # Redis 连接
│   ├── models/                     # SQLAlchemy 模型（7 个模型 + 1 关联表）
│   │   ├── user.py                 # 用户
│   │   ├── document.py             # 文档
│   │   ├── official_document.py    # 公文
│   │   ├── task.py                 # 任务
│   │   ├── tag.py                  # 标签
│   │   ├── image_translation.py    # 图片转译
│   │   └── document_translation.py # 文档翻译
│   ├── schemas/                    # Pydantic 模式
│   ├── services/                   # 业务逻辑（12 个服务模块）
│   │   ├── document_service.py             # 文档管理
│   │   ├── official_document_service.py    # 公文库管理
│   │   ├── file_service.py                 # 文件存储
│   │   ├── translation_workflow_service.py # 翻译工作流
│   │   ├── academic_to_official_service.py # 学术转公文（10 阶段）
│   │   ├── country_research_service.py     # 国别研究（7 阶段）
│   │   ├── quarterly_report_service.py     # 季度报告（8 阶段）
│   │   ├── image_translation_service.py    # 图片转译
│   │   ├── document_translation_service.py # 文档翻译
│   │   ├── mineru_service.py               # MinerU PDF 解析
│   │   ├── fitz_extractor.py               # PyMuPDF 提取器
│   │   └── web_crawler_service.py          # 网页爬取
│   ├── configs/
│   │   ├── country_data_sources.py  # 国别数据源配置（非洲 54 国）
│   │   └── prompts/                 # 提示词模块化管理
│   │       ├── __init__.py
│   │       ├── country_report.py    # 国别报告提示词 V3
│   │       └── quarterly_report.py  # 季度报告提示词 V3
│   ├── utils/
│   │   ├── debug_logger.py          # 调试日志系统
│   │   ├── llm_output_parser.py     # LLM 输出解析器
│   │   ├── markdown_to_word.py      # Markdown 转 Word
│   │   └── text_extraction.py       # 文本提取工具
│   └── main.py                      # FastAPI 入口
├── frontend/
│   └── src/
│       ├── api/                     # API 客户端
│       │   ├── client.ts            # 统一 API 封装
│       │   └── types.ts             # API 类型定义
│       ├── app/
│       │   ├── App.tsx              # 根组件（状态机路由）
│       │   ├── components/
│       │   │   ├── LibraryModule.tsx         # 前沿报告库（含 AI 写作舱）
│       │   │   ├── ResearchModule.tsx        # 国别深度研究
│       │   │   ├── ImageModule.tsx           # 图片转译
│       │   │   ├── HistoryPanel.tsx          # 历史记录
│       │   │   ├── features/
│       │   │   │   ├── doc-library/          # 公文库模块
│       │   │   │   └── quarterly/            # 季度报告模块（已开发未启用）
│       │   │   ├── layout/
│       │   │   │   ├── Sidebar.tsx           # 侧边栏导航
│       │   │   │   └── DataSourcePanel.tsx   # 数据源面板
│       │   │   └── ui/                       # shadcn/ui 组件集
│       │   ├── config/              # 应用配置
│       │   └── types/               # 类型定义
│       └── styles/                  # 样式（Tailwind CSS 4）
├── browser-extension/               # 浏览器插件
│   ├── manifest.json                # Manifest V3 配置
│   ├── popup/                       # 弹窗页面
│   ├── content/                     # 内容脚本（PDF 嗅探）
│   ├── background/                  # 后台服务
│   └── icons/                       # 图标
└── README.md
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 后端启动

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 文件，填入必要的 API 密钥和数据库连接信息
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 插件加载

```
1. 打开 chrome://extensions/
2. 开启开发者模式
3. 加载 browser-extension/ 文件夹
```

---

## 🔧 核心配置

### 插件 API 对接

插件上传到报告库需要后端运行在 `http://localhost:8000`，API 端点：`/api/v1/documents/`

### 环境变量

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/docwriting
DATABASE_URL_SYNC=postgresql://user:pass@localhost:5432/docwriting

# AI 服务 - 硅基流动
SILICONFLOW_API_KEY=your_siliconflow_key
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
DEEPSEEK_MODEL=Pro/deepseek-ai/DeepSeek-V3
DEEPSEEK_R1_MODEL=deepseek-ai/DeepSeek-R1
KIMI_MODEL=Pro/moonshotai/Kimi-K2.5

# AI 服务 - OpenRouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_IMAGE_MODEL=google/gemini-3-pro-image-preview
OPENROUTER_TEXT_MODEL=google/gemini-3.1-pro-preview

# 网页爬取
FIRECRAWL_API_KEY=your_firecrawl_key

# PDF 解析
MINERU_API_KEY=your_mineru_key
MINERU_ENABLED=true

# 安全
SECRET_KEY=your_secret_key

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

## 📡 API 端点概览

| 模块 | 端点前缀 | 状态 | 说明 |
|------|----------|------|------|
| 文档管理 | `/api/v1/documents/` | ✅ 已完成 | 完整 CRUD + 内容提取 |
| 公文库 | `/api/v1/official-documents/` | ✅ 已完成 | 完整 CRUD + 下载 |
| 工作流 | `/api/v1/workflows/` | ✅ 已完成 | 翻译/写作/研究/报告/MinerU |
| 图片转译 | `/api/v1/image-translation/` | ✅ 已完成 | 上传/状态/预览/下载/删除 |
| 公文翻译 | `/api/v1/document-translation/` | ✅ 已完成 | 创建/状态/多格式下载 |
| 任务管理 | `/api/v1/tasks/` | ⏳ 待实现 | 列表/详情/创建/取消 |
| 知识库 | `/api/v1/knowledge/` | ⏳ 待实现 | 检索/上传/删除 |
| 文件存储 | `/api/v1/storage/` | ⏳ 待实现 | 上传/下载 |
| 健康检查 | `/api/v1/health` | ✅ 已完成 | 服务状态检查 |

---

## 📚 文档

- [存储架构](./STORAGE_ARCHITECTURE.md) - 文件存储规范
- [MinerU 集成](./MINERU_INTEGRATION.md) - MinerU PDF 解析配置
- [OpenRouter 图片转译](./OPENROUTER_IMAGE_SETUP.md) - 图片转译 API 配置
- [OpenRouter API 指南](./OPENROUTER_API_GUIDE.md) - OpenRouter 使用说明
- [调试指南](./DEBUG_GUIDE.md) - 调试日志系统
- [LLM 输出格式](./LLM_OUTPUT_FORMAT_GUIDE.md) - LLM 输出解析规范
- [提示词参考](./PROMPTS_REFERENCE.md) - 提示词模块说明
- [浏览器插件](./browser-extension/README.md) - 插件使用文档

---

## 🐛 已修复问题

- ✅ UUID 类型比较错误导致文档删除失败
- ✅ DocumentService 类型不匹配（owner_id: uuid.UUID vs str）
- ✅ 前端删除功能缺失 API 调用
- ✅ 浏览器缓存导致数据不一致
- ✅ 公文库 API 未统一管理
- ✅ 哈希去重检查避免重复上传
- ✅ PDF 列表刷新后消失问题
- ✅ Content Script 页面刷新重置问题
- ✅ 学术转公文工作流从 8 阶段升级为 10 阶段多模型协作
- ✅ 翻译工作流支持两步工作流（提取→编辑→翻译）
- ✅ 图片转译模型从 Claude/GPT-4V 迁移至 Gemini-3-Pro

---

## 📊 项目状态

**当前版本**：v3.0
**最后更新**：2026-04-13
**开发阶段**：核心功能完善阶段

### ✅ 已完成的核心功能

1. **公文对照翻译工作流**
   - ✅ 两步工作流（提取→编辑→翻译）
   - ✅ MinerU 高质量 PDF 解析
   - ✅ 并发翻译（速度提升 3-5 倍）
   - ✅ 段落对照格式
   - ✅ 多格式导出（TXT / Word / Markdown）
   - ✅ 独立文档翻译服务

2. **学术报告转公文**
   - ✅ 10 阶段多模型协作工作流
   - ✅ 两种风格模式（严谨完整型 / 简洁概括型）
   - ✅ 大文档分层处理策略
   - ✅ 并发章节写作
   - ✅ Markdown 输出 + 导出 Word
   - ✅ 完整调试日志系统

3. **国别深度研究**
   - ✅ 7 阶段工作流（配置→采集→经济→政治→外交→报告→审核）
   - ✅ 非洲 54 国插拔式数据源配置
   - ✅ Firecrawl 并发爬取
   - ✅ 用户自定义补充数据源
   - ✅ 质量审核（数据来源标注、双币种展示）

4. **季度报告生成**
   - ✅ 8 阶段工作流（配置→采集→宏观→金融→政策→风险→报告→审核）
   - ✅ 复用国别研究架构
   - ✅ SSE 流式输出

5. **图片转译**
   - ✅ Gemini-3-Pro API 集成（OpenRouter）
   - ✅ 端到端流程完整
   - ✅ 支持预览和下载
   - ✅ 原图/译图对比滑块
   - ✅ 批量转译（最多 5 张）

6. **文档管理系统**
   - ✅ 前沿报告库（完整 CRUD + 日历筛选 + 来源分类）
   - ✅ 公文库（独立管理 + 审核状态 + 来源机构筛选）
   - ✅ 哈希去重
   - ✅ PDF 内容自动提取

7. **浏览器插件**
   - ✅ PDF 智能识别（`<a>` / `<embed>` / `<iframe>` / `<object>`）
   - ✅ 批量下载 / 上传到报告库
   - ✅ 右键菜单 + 快捷键
   - ✅ 来源自动识别

8. **基础设施**
   - ✅ MinerU 高精度 PDF 解析集成
   - ✅ 调试日志系统（每阶段记录输入/输出/模型/提示词）
   - ✅ LLM 输出解析器（JSON 解析 + 重试机制）
   - ✅ 提示词模块化管理
   - ✅ Markdown 转 Word（支持双语对照 / 报告两种模式）

### ⚠️ 待完善功能

- 任务管理 API（列表/详情/创建/取消）
- 知识库向量检索（pgvector / Qdrant）
- 文件存储 API（上传/下载）
- 参考文件选择功能
- Markdown 编辑器集成
- 历史记录面板（当前使用模拟数据）
- 季度报告独立模块启用（已开发未启用）
- Word 文档（.doc/.docx）翻译支持
- 浏览器插件设置界面（API 端点 / Token 配置）

### 📈 开发进度

- **Phase 1: 核心流程打通** - 95% 完成（对照翻译✅、公文写作✅、图片转译✅）
- **Phase 2: 基础功能完善** - 75% 完成（公文库✅、文档翻译✅、参考文件⏳、编辑器⏳）
- **Phase 3: 体验优化** - 65% 完成（日历筛选✅、数据源✅、Prompt 模块化✅、调试日志✅）
- **Phase 4: 扩展功能** - 40% 完成（插件✅、历史记录⏳、知识库⏳）

**总体进度**：约 70%

---

## 📄 License

MIT License
