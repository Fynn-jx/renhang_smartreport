# 央行公文写作 AI 系统

## 📖 项目简介

这是一个基于 FastAPI + React 的企业级文档管理与 AI 处理平台，提供 Zotero 式的文档管理能力和五大 AI 工作流，专为央行公文写作场景设计。

### 核心功能

1. **前沿报告库** - Zotero 风格的文档管理系统，支持 PDF、Word、TXT、Markdown 等多种格式
2. **公文库** - 独立的知识库，用于管理经过人工审核的高质量公文模板
3. **国别深度研究** - 自动化国别研究报告生成，支持多数据源插拔式配置
4. **季度报告生成** - 金融市场与宏观经济分析报告自动生成
5. **公文翻译** - 专业公文对照翻译，支持段落对照格式，两步工作流（预览→编辑→翻译）
6. **学术报告转公文** - 学术报告自动转换为公文格式
7. **图片转译** - 图片中的文字提取与翻译
8. **浏览器插件** - 人行智汇，一键采集网页 PDF 到报告库

---

## 🎯 功能详解

### 1. 前沿报告库（核心文档管理）

**功能概述**：
前沿报告库是系统的核心文档管理模块，用户可以从本地电脑上传或通过浏览器插件直接爬取前沿报告。

**核心特性**：
- 📁 **多种上传方式**：本地上传 / 浏览器插件一键爬取
- 📅 **日历风格筛选**：按时间维度可视化展示
- 🏷️ **来源分类管理**：按信息来源自动分类
- 👁️ **PDF 实时预览**：点击报告后左侧显示 PDF 预览
- 🔄 **两大核心功能**：对照翻译 / 公文写作
- 🗑️ **文档管理**：完整的 CRUD 操作，支持删除、下载

**技术实现**：
- 前端：React + TypeScript + Tailwind CSS
- 后端：FastAPI + SQLAlchemy 2.0 异步
- AI：DeepSeek V3 / R1（通过硅基流动）
- PDF 提取：MinerU / PyMuPDF

---

### 2. 公文库（独立知识库）

**功能概述**：
独立的知识库模块，用于管理经过人工审核的高质量公文模板，作为 AI 写作的风格参考库。

**核心特性**：
- ✅ 独立管理界面
- ✅ 风格参考
- ✅ 知识积累
- ✅ DOCX 格式支持

---

### 3. 国别研究 / 季度报告

**功能概述**：
基于固定模板和插拔式数据源配置，系统自动爬取数据、分析数据、生成报告。

**支持国家**：埃及(EG)、肯尼亚(KE)、尼日利亚(NG)等

**技术实现**：
- 数据源配置：`backend/configs/country_data_sources.py`
- 爬虫服务：Firecrawl
- AI：DeepSeek R1（深度推理）
- 流式输出：SSE

---

### 4. 图片转译

**功能概述**：
将图片中的英文翻译为中文，保持原始布局和格式。

**技术实现**：
- AI：OpenRouter (Claude/GPT-4V)
- 图片处理：Pillow

---

### 5. 人行智汇（浏览器插件）

**功能概述**：
一键采集网页中的 PDF 文件，保存到本地或上传到报告库。

**核心特性**：
- 🌐 **智能 PDF 识别**：自动扫描网页中的 PDF 链接
- ⚡ **批量操作**：支持多选批量下载或上传
- 📂 **报告库同步**：直接保存 PDF 到云端报告库
- ✏️ **标题编辑**：点击即可修改 PDF 标题
- 🔄 **多浏览器支持**：Chrome / Edge 完全支持

**安装方法**：
1. 打开 `chrome://extensions/`
2. 开启「开发者模式」
3. 点击「加载解包的扩展程序」
4. 选择 `browser-extension` 文件夹

**项目结构**：
```
browser-extension/
├── manifest.json      # 扩展配置
├── popup/            # 弹窗页面
├── content/          # 网页注入脚本
├── background/       # 后台脚本
└── icons/           # 图标
```

---

## 🏗️ 技术架构

### 后端技术栈

- **框架**: FastAPI 0.109+
- **数据库**: PostgreSQL 15+ (SQLAlchemy 2.0 异步)
- **缓存**: Redis 7+
- **AI 服务**: DeepSeek V3 / R1, OpenRouter
- **向量检索**: pgvector / Qdrant
- **网页抓取**: Firecrawl
- **文档处理**: PyMuPDF, python-docx

### 前端技术栈

- **框架**: React 18.3 + TypeScript
- **构建**: Vite 6.3
- **UI**: Radix UI + shadcn/ui + Tailwind CSS
- **动画**: Framer Motion

---

## 📁 项目结构

```
renhang_smartreport/
├── backend/
│   ├── api/endpoints/     # API 路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic 模式
│   ├── services/          # 业务逻辑
│   └── main.py            # 入口
├── frontend/
│   └── src/
│       ├── api/           # API 客户端
│       ├── app/components/ # 组件
│       └── styles/        # 样式
├── browser-extension/     # 浏览器插件
│   ├── manifest.json
│   ├── popup/             # 弹窗
│   ├── content/            # 内容脚本
│   └── icons/             # 图标
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
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 插件加载

```bash
# Chrome
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
# .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/docwriting
SILICONFLOW_API_KEY=your_key
DEEPSEEK_MODEL=Pro/deepseek-ai/DeepSeek-V3
```

---

## 📚 文档

- [存储架构](./STORAGE_ARCHITECTURE.md) - 文件存储规范
- [浏览器插件](./browser-extension/README.md) - 插件使用文档
- [国别研究配置](./backend/configs/README_COUNTRY_RESEARCH.md) - 数据源配置

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

---

## 📊 项目状态

**当前版本**：v2.5
**最后更新**：2026-04-02
**开发阶段**：基础功能完善阶段

### ✅ 已完成的核心功能

1. **对照翻译工作流**
   - ✅ 两步工作流（预览→编辑→翻译）
   - ✅ MinerU 高质量 PDF 解析
   - ✅ 并发翻译（速度提升 3-5 倍）
   - ✅ 段落对照格式

2. **学术报告转公文**
   - ✅ 8 个工作流阶段
   - ✅ Markdown 输出
   - ✅ 导出 Word 功能

3. **图片转译**
   - ✅ OpenRouter API 集成
   - ✅ 端到端流程完整
   - ✅ 支持预览和下载

4. **文档管理系统**
   - ✅ 前沿报告库（完整 CRUD）
   - ✅ 公文库（独立管理）
   - ✅ 日历风格筛选
   - ✅ 文档删除功能（已修复）

### ⚠️ 待完善功能

- 参考文件选择功能
- Markdown 编辑器集成
- 浏览器插件（代码已提取，需集成）
- 数据源后端配置

### 📈 开发进度

- **Phase 1: 核心流程打通** - 90% 完成（对照翻译✅、公文写作⏳、图片转译✅）
- **Phase 2: 基础功能完善** - 50% 完成（公文库✅、参考文件⏳、编辑器⏳）
- **Phase 3: 体验优化** - 40% 完成（日历筛选✅、数据源✅、Prompt⏳）
- **Phase 4: 扩展功能** - 10% 完成（插件⏳、历史记录⏳）

**总体进度**：约 45%

---

## 📄 License

MIT License
