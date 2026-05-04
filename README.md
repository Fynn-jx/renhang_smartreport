# 央行公文写作 AI 系统

## 📖 项目简介

这是一个面向央行研究与公文写作场景的 AI 研究工作台，核心目标是把“资料收集、文档管理、对照翻译、公文写作、国别研究、季度研究、图片转译、数据源推送”放进同一个系统，形成从外部材料到正式输出的闭环。

项目不是单一聊天应用，而是一个 **文档库 + 多工作流引擎 + 流式前端工作台 + 外部资料采集能力** 的组合系统。系统采用 FastAPI + React 架构，支持 SSE 流式进度、多模型协作、Word 可编辑输出、调试产物留存和插拔式数据源配置。

### 核心功能

1. **前沿报告库** - Zotero 风格的文档管理系统，支持本地上传、数据源导入、公文库参考文件选择、PDF 预览与 AI 写作
2. **公文库** - 独立的正式公文知识库，用于沉淀高质量模板，支持审核状态、来源筛选和参考文件复用
3. **公文对照翻译** - 提取、编辑、翻译三段式工作流，支持暂停、段落对照和 Word 导出
4. **学术报告转公文** - 多阶段公文写作工作流，支持章节并发写作、模型选择、暂停和可编辑 Word 输出
5. **国别深度研究** - 自动采集并生成标准化国别情况报告，经济、政治、外交分析并发执行
6. **季度报告生成** - 复用国别研究的数据源体系，生成宏观经济与金融运行季报
7. **图片转译** - 图片英文内容识别、翻译和版式保持，支持原图/译图对比
8. **数据源推送** - 定时或手动从权威站点抓取资料，支持深度检索、站点筛选、收录与仅链接管理
9. **浏览器插件** - 人行智汇，一键识别网页 PDF 并保存到报告库

---

## 🎯 功能详解

### 1. 前沿报告库（核心文档管理）

**功能概述**：
前沿报告库是系统的核心资料入口，负责管理外部研究报告、PDF、Word、TXT、Markdown 等材料，并把这些材料接入翻译、公文写作和参考文件选择流程。

**核心特性**：
- 📁 **多种上传方式**：本地上传 / 数据源推送导入 / 浏览器插件采集
- 📅 **日期筛选**：按时间维度筛选报告
- 🏷️ **来源分类管理**：按 IMF、世界银行、联合国、央行、统计局等来源分类
- 👁️ **文档预览**：支持 PDF 预览与内容查看
- 🔄 **两大核心操作**：对照翻译 / 公文写作
- 📚 **参考文件选择**：公文写作可选择本地文件，也可从公文库选择正式公文作为参考
- 🧠 **AI 写作舱**：展示工作流进度、思维链节点和最终可编辑内容
- 🔍 **哈希去重**：通过文件哈希避免重复上传

---

### 2. 公文库（正式公文知识库）

**功能概述**：
公文库用于管理经过人工审核的正式公文模板，是公文写作流程的重要参考来源。

**核心特性**：
- ✅ 与前沿报告库独立管理
- ✅ 支持 DOCX / PDF / TXT / Markdown
- ✅ 审核状态管理：`is_verified` / `verified_by` / `verified_at`
- ✅ 来源机构筛选
- ✅ 日期筛选与标题检索
- ✅ 可作为公文写作参考文件来源
- ✅ 上传成功后可退出当前上传界面

---

### 3. 公文对照翻译

**功能概述**：
面向公文场景的对照翻译工作流，强调可控、可编辑和可导出。

**工作流**：
1. **提取阶段**：使用 MinerU 或 PyMuPDF 提取原文
2. **编辑阶段**：用户确认或修改提取文本，点击“编辑内容”前不可误编辑
3. **翻译阶段**：调用模型逐段翻译，输出段落对照结果

**核心特性**：
- 📝 提取 → 编辑 → 翻译的明确阶段
- ⏸️ 支持暂停
- 📄 段落对照格式
- 📥 支持 TXT / Markdown / Word 导出
- 🔄 SSE 流式进度
- 🧹 文本清理：页眉页脚、目录、参考文献等噪音处理

---

### 4. 学术报告转公文

**功能概述**：
将学术论文、研究报告或政策材料转换为正式公文格式。系统按“提取、整理、写作、整合、检查、导出”组织长流程，并保留调试产物。

**工作流阶段**：
1. 文档提取
2. 知识检索
3. 大纲生成
4. 标题提取
5. 内容整理
6. 章节并发写作
7. 模板转换
8. 内容整合润色
9. 内容检查
10. 最终调整

**模型分工**：
| 阶段 | 默认模型 | 说明 |
|------|----------|------|
| 大纲生成 / 内容整理 / 检查 / 最终调整 | Kimi 月之暗面 | 长上下文、结构整理与检查 |
| 章节写作 | DeepSeek 深度求索 / Qwen 千问 / GLM 智谱 / Kimi 月之暗面 | 用户可选；只替换章节写作模型 |
| 内容整合 | DeepSeek 深度求索 | 负责长文整合与润色 |
| 数据来源标注 | Kimi 月之暗面 | 负责数据定位与来源整理 |

**核心特性**：
- 🎨 严谨完整型 / 简洁概括型两种风格
- ⚡ 章节并发写作
- ⏸️ 支持暂停
- 🧾 生成结果为可编辑内容
- 📥 Word 导出可直接编辑
- 🔍 调试日志记录每阶段输入、输出、模型和提示词

---

### 5. 国别深度研究

**功能概述**：
基于国家数据源配置，自动采集公开数据并生成《[国家名称]国别情况报告》。报告格式包含基本信息表、经济核心指标表、经济正文、政治正文和数据来源汇总表。

**工作流阶段**：
1. 配置加载
2. 数据采集
3. 经济分析
4. 政治分析
5. 外交分析
6. 报告生成
7. 质量审核

**当前实现状态**：
- ✅ 非洲国家数据源配置
- ✅ 埃及精细化权威数据源配置
- ✅ 用户自定义补充数据源
- ✅ Firecrawl 网页抓取
- ✅ Trading Economics 结构化指标解析
- ✅ 经济、政治、外交分析并发执行
- ✅ 国别研究与季度研究保持一致的编辑保护逻辑
- ✅ 标准 Word 样板格式：基本信息表、核心指标表、数据来源汇总表

**数据源类型**：
Trading Economics / 各国央行 / 各国财政部 / 各国统计局 / IMF / 世界银行 / 中国外交部 / 政府门户 / 自定义来源。

---

### 6. 季度报告生成

**功能概述**：
季度报告生成模块复用国别研究的数据源配置和报告生成思路，面向宏观经济、金融市场、政策和风险评估生成季度研究报告。

**工作流阶段**：
1. 配置加载
2. 数据采集
3. 宏观经济分析
4. 金融市场分析
5. 政策分析
6. 风险评估
7. 报告生成
8. 质量审核

**当前实现状态**：
- ✅ 后端工作流已实现
- ✅ 前端季度模块已接入
- ✅ 与国别研究共享编辑保护和 Word 导出逻辑

---

### 7. 图片转译

**功能概述**：
识别图片中的英文文字并翻译为中文，同时尽量保持原始布局。

**核心特性**：
- 🖼️ 支持 JPG / PNG / GIF / WebP / BMP
- 🔎 原图/译图对比滑块
- 📦 后台任务处理
- 📥 支持预览、下载和删除
- 🧩 批量转译

---

### 8. 数据源推送

**功能概述**：
数据源推送用于定时或手动抓取权威站点资料，将新增报告推送到系统中，减少人工巡检网站的成本。

**核心特性**：
- 🕘 每周五 09:00 自动推送
- 🔍 深度检索入口
- 🧭 检索站点和爬取站点分离
- 📥 支持收录到前沿报告库
- 🔗 支持仅保存链接
- 🧾 支持标题检索、站点筛选和时间筛选
- ⚡ 页面图标与列表即时显示

---

### 9. 人行智汇（浏览器插件）

**功能概述**：
识别网页中的 PDF 链接，支持下载或上传到报告库。

**核心特性**：
- 🌐 自动扫描 `<a>` / `<embed>` / `<iframe>` / `<object>` 中的 PDF 链接
- ⚡ 支持批量下载和批量上传
- 📂 与报告库同步
- ✏️ 标题可编辑
- 🖱️ 右键菜单
- ⌨️ 快捷键
- 🏷️ 来源自动识别

---

## 🏗️ 技术架构

### 后端技术栈

- **框架**：FastAPI
- **数据库**：SQLAlchemy 2.0 异步模型，开发环境可使用 SQLite，生产环境可接 PostgreSQL
- **缓存**：Redis 预留
- **网页抓取**：Firecrawl
- **文档处理**：PyMuPDF、python-docx、MinerU
- **AI 服务**：硅基流动 / OpenRouter
- **流式输出**：Server-Sent Events（SSE）
- **调试链路**：工作流阶段输入、输出、提示词、模型信息落盘

### 前端技术栈

- **框架**：React + TypeScript
- **构建工具**：Vite
- **样式**：Tailwind CSS 4 + 自定义 Word-like 编辑器样式
- **UI**：Radix UI / shadcn/ui
- **动画**：Motion
- **分屏**：react-resizable-panels
- **长流程展示**：SSE 进度、思维链节点、动态加载状态

### 模型配置

| 显示名称 | 实际模型 |
|----------|----------|
| DeepSeek 深度求索 | `deepseek-ai/DeepSeek-V4-Flash` |
| Qwen 千问 | `Qwen/Qwen3-235B-A22B-Instruct-2507` |
| GLM 智谱 | `zai-org/GLM-5.1` |
| Kimi 月之暗面 | `moonshotai/Kimi-K2.6` |

> 公文写作中，用户选择不同模型时，只替换“章节写作”阶段；内容整理、整合、检查等阶段仍按工作流默认分工执行。

---

## 📁 项目结构

```text
renhang_smartreport/
├── backend/
│   ├── api/
│   │   ├── endpoints/                  # API 路由
│   │   └── v1/api.py                   # 路由聚合
│   ├── configs/
│   │   ├── country_data_sources.py      # 国别/季度数据源配置
│   │   ├── data_source_push_sources.py  # 数据源推送站点配置
│   │   └── prompts/                     # 国别、季度、公文写作提示词
│   ├── core/
│   │   ├── config.py                    # 环境变量与应用配置
│   │   ├── database.py                  # 数据库连接与开发态建表
│   │   └── model_registry.py            # 模型别名与实际模型映射
│   ├── models/                          # SQLAlchemy 模型
│   ├── schemas/                         # Pydantic Schema
│   ├── services/                        # 业务服务与工作流
│   │   ├── academic_to_official_service.py
│   │   ├── country_research_service.py
│   │   ├── quarterly_report_service.py
│   │   ├── data_source_push_service.py
│   │   ├── data_source_push_scheduler.py
│   │   ├── document_service.py
│   │   ├── image_translation_service.py
│   │   └── web_crawler_service.py
│   ├── storage/                         # 上传文件、缓存、调试输出
│   ├── utils/
│   │   ├── markdown_to_word.py           # Markdown/HTML 转 Word
│   │   └── trading_economics_parser.py   # Trading Economics 指标解析
│   └── main.py
├── frontend/
│   ├── src/api/                         # API 客户端
│   ├── src/app/
│   │   ├── App.tsx                      # 工作台主入口
│   │   ├── components/
│   │   │   ├── common/                  # Word-like 编辑器等通用组件
│   │   │   ├── features/                # 公文库、季度等功能模块
│   │   │   └── layout/                  # 侧边栏、数据源面板
│   │   ├── config/                      # 前端配置
│   │   └── contexts/                    # 前端上下文
│   └── src/styles/                      # 全局样式
├── browser-extension/                   # 浏览器插件
├── PROJECT_UNDERSTANDING.md             # 接手阅读文档
└── README.md
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- npm

### 后端启动

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入模型、Firecrawl、MinerU 等 API Key
python3.11 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

默认前端地址：

```text
http://localhost:5173/
```

默认后端地址：

```text
http://127.0.0.1:8000/
```

### 浏览器插件加载

```text
1. 打开 chrome://extensions/
2. 开启「开发者模式」
3. 点击「加载解包的扩展程序」
4. 选择 browser-extension 文件夹
```

---

## 🔧 核心配置

### 环境变量

```env
# 应用
ENVIRONMENT=development
API_V1_STR=/api/v1

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./app.db
DATABASE_URL_SYNC=sqlite:///./app.db

# 硅基流动
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
DEEPSEEK_MODEL=deepseek-ai/DeepSeek-V4-Flash
DEEPSEEK_R1_MODEL=deepseek-ai/DeepSeek-R1
KIMI_MODEL=moonshotai/Kimi-K2.6
CONTENT_INTEGRATION_MODEL=deepseek-ai/DeepSeek-V4-Flash
SOURCE_ANNOTATION_MODEL=moonshotai/Kimi-K2.6

# OpenRouter / Gemini
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_IMAGE_MODEL=google/gemini-3-pro-image-preview
GEMINI_IMAGE_MODEL=gemini-3-pro-image-preview

# 网页抓取
FIRECRAWL_API_KEY=your_firecrawl_key

# PDF 解析
MINERU_API_KEY=your_mineru_key
MINERU_ENABLED=true

# 安全
SECRET_KEY=your_secret_key
```

---

## 📡 API 端点概览

| 模块 | 端点前缀 | 状态 | 说明 |
|------|----------|------|------|
| 文档管理 | `/api/v1/documents/` | ✅ 已完成 | 前沿报告库 CRUD、上传、下载、内容提取 |
| 公文库 | `/api/v1/official-documents/` | ✅ 已完成 | 公文模板管理、审核状态、下载 |
| 工作流 | `/api/v1/workflows/` | ✅ 已完成 | 翻译、公文写作、国别研究、季度报告 |
| 图片转译 | `/api/v1/image-translation/` | ✅ 已完成 | 上传、状态、预览、下载、删除 |
| 公文翻译 | `/api/v1/document-translation/` | ✅ 已完成 | 文档翻译任务与多格式下载 |
| 数据源推送 | `/api/v1/data-source-push/` | ✅ 已完成 | 站点检索、爬取、收录、定时推送 |
| 任务管理 | `/api/v1/tasks/` | ⏳ 预留 | 任务列表、详情、取消 |
| 知识库 | `/api/v1/knowledge/` | ⏳ 预留 | 向量检索与知识库管理 |
| 健康检查 | `/api/v1/health` | ✅ 已完成 | 服务状态检查 |

---

## 📚 文档

- [项目理解文档](./PROJECT_UNDERSTANDING.md) - 面向新人接手的项目定位、结构、服务和阅读顺序
- [后端说明](./backend/README.md) - 后端运行与接口说明
- [国别研究配置说明](./backend/configs/README_COUNTRY_RESEARCH.md) - 国别数据源与提示词说明

---

## 🐛 近期已修复与优化

- ✅ 前沿报告库、公文库、数据源推送 hover 样式统一
- ✅ 删除左下角默认研究员信息块
- ✅ 数据源推送图标即时显示
- ✅ 数据源推送入口改为深度检索，检索/爬取筛选拆分
- ✅ 公文写作增加暂停能力
- ✅ 公文写作加载状态改为动态转圈
- ✅ 公文写作 Word 导出空内容、`[object Object]`、空行过多问题修复
- ✅ Word-like 编辑器长 URL 和宽表自动换行，避免撑出页面
- ✅ 国别研究经济、政治、外交分析并发执行
- ✅ 国别研究报告格式恢复为样板 Word：基本信息表、核心指标表、数据来源汇总表
- ✅ 公文写作模型选择接入 DeepSeek、Qwen、GLM、Kimi，且只影响章节写作阶段
- ✅ 前端模块懒加载与已访问模块保活，减少初始内存占用
- ✅ API 下载文件名解析、Blob 下载逻辑统一

---

## 📊 项目状态

**当前版本**：v3.1  
**最后更新**：2026-05-04  
**开发阶段**：核心功能完善与体验优化阶段

### ✅ 已完成的核心能力

1. **文档管理**
   - ✅ 前沿报告库
   - ✅ 公文库
   - ✅ 文件上传、下载、预览、筛选、去重

2. **AI 工作流**
   - ✅ 公文对照翻译
   - ✅ 学术报告转公文
   - ✅ 国别深度研究
   - ✅ 季度报告生成
   - ✅ 图片转译

3. **数据采集**
   - ✅ 浏览器插件采集 PDF
   - ✅ Firecrawl 网页抓取
   - ✅ 数据源推送
   - ✅ Trading Economics 指标解析

4. **输出与编辑**
   - ✅ 生成内容可编辑
   - ✅ 编辑前保护
   - ✅ Word 导出
   - ✅ 表格和长 URL 换行

5. **工程化**
   - ✅ SSE 流式进度
   - ✅ 工作流调试产物
   - ✅ 模型注册表
   - ✅ 模块懒加载

### ⚠️ 待完善功能

- 知识库向量检索正式接入
- 任务中心从预留接口升级为可视化管理
- 历史记录真实数据接入
- 更完整的权限与用户体系
- 生产环境数据库迁移机制
- 浏览器插件设置页完善

### 📈 开发进度

- **Phase 1：核心流程打通** - 95%
- **Phase 2：基础功能完善** - 85%
- **Phase 3：体验优化** - 75%
- **Phase 4：扩展功能** - 50%

**总体进度**：约 78%

---

## 🧭 接手阅读顺序

建议按以下顺序理解项目：

1. `README.md`
2. `PROJECT_UNDERSTANDING.md`
3. `frontend/src/app/App.tsx`
4. `backend/main.py`
5. `backend/api/v1/api.py`
6. `backend/api/endpoints/workflows.py`
7. `backend/services/academic_to_official_service.py`
8. `backend/services/country_research_service.py`
9. `backend/services/data_source_push_service.py`
10. `backend/core/config.py`

---

## 📄 License

MIT License
