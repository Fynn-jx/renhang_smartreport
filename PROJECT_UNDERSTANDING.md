# 项目理解文档

## 1. 项目一句话说明

这是一个面向央行公文写作场景的 AI 研究工作台，核心目标是把“资料收集、文档管理、翻译、公文写作、国别研究、图片转译”放进同一个系统里，形成从原始材料到正式输出的闭环。

它不是单一聊天应用，而是一个“文档库 + 多工作流引擎 + 流式前端工作台”的组合系统。

---

## 2. 从业务视角理解这个项目

项目目前主要承载 4 类业务：

1. 前沿报告管理
   把 PDF、Word、TXT、Markdown 等材料沉淀到“前沿报告库”，支持检索、预览、分类、去重和二次处理。

2. 公文模板沉淀
   把经过人工审核的正式公文沉淀到“公文库”，作为风格参考和知识积累。

3. AI 内容生产
   围绕已有材料做公文对照翻译、学术报告转公文、国别深度研究、季度报告生成、图片转译。

4. 外部资料采集
   通过浏览器插件或网页抓取，把外部网站上的 PDF 和研究材料导入系统。

从产品形态上看，它更像“研究员工作站”，不是纯后台服务。

---

## 3. 总体架构

项目分成 3 层：

1. 前端工作台
   `frontend/`
   使用 React + TypeScript + Vite，负责文档库界面、配置弹窗、思维链显示、SSE 结果展示、图片对比查看等交互。

2. 后端 API 与工作流层
   `backend/`
   使用 FastAPI + SQLAlchemy 异步模式，提供文档管理、公文库、工作流、图片转译、翻译、存储等接口。

3. 浏览器插件
   `browser-extension/`
   用于识别网页中的 PDF，支持下载或直接上传到系统。

核心运行方式是：

- 前端发起普通 CRUD 请求管理文档
- 前端发起 SSE 请求执行长流程工作流
- 后端工作流服务调用 LLM、解析文档、整合内容
- 结果以流式进度或最终文档回传

---

## 4. 前端怎么组织

前端主入口是 `frontend/src/app/App.tsx`，它负责切换几个主模块：

- 前沿报告库 `library`
- 公文库 `doc-library`
- 国别深度研究 `research`
- 图片转译 `image`
- 数据源面板
- 历史记录面板

当前实际使用的侧边栏组件在：

- `frontend/src/app/components/layout/Sidebar.tsx`

这个组件和主入口是一一对应的，说明当前真实页面结构已经从旧版组件路径迁移到 `components/layout` 与 `components/features/*` 这一套。

前端的主要特征：

- 以单页工作台的方式组织，而不是多页面路由应用
- 采用分屏布局处理“左侧原文 / 右侧 AI 结果”
- 长流程依赖 SSE 流式返回
- “思维链”本质上是前端把后端发来的 `message` 逐条展示出来

前端特征模块目录：

- `frontend/src/app/components/features/library`
- `frontend/src/app/components/features/doc-library`
- `frontend/src/app/components/features/research`
- `frontend/src/app/components/features/quarterly`
- `frontend/src/app/components/features/image`

这里要注意一点：季度报告组件目录是存在的，但当前 `App.tsx` 主入口没有把它挂进主界面导航，所以它更像“已开发但未完全接入主入口”的功能。

---

## 5. 后端怎么组织

后端主入口：

- `backend/main.py`

启动时会做几件事：

- 初始化 FastAPI 应用
- 注册 `api/v1` 路由
- 挂载 `/storage` 静态目录
- 在应用生命周期里初始化数据库连接

API 聚合入口：

- `backend/api/v1/api.py`

当前聚合的模块包括：

- `documents` 文档管理
- `official-documents` 公文库
- `workflows` 各类长流程
- `document-translation` 公文翻译
- `image-translation` 图片转译
- `storage` 文件存储
- `knowledge` 知识库预留
- `tasks` 任务管理预留

这说明后端并不是按“页面”切，而是按“资源 + 工作流”切分。

---

## 6. 核心服务分工

`backend/services/` 是项目最关键的目录，基本可以理解成业务能力中心：

- `document_service.py`
  处理前沿报告库文档的 CRUD、内容提取、去重等。

- `official_document_service.py`
  处理公文库文档的上传、审核状态、筛选与管理。

- `translation_workflow_service.py`
  负责公文对照翻译流程，支持提取、编辑、翻译、导出。

- `academic_to_official_service.py`
  负责“学术报告转公文”，是整个项目最复杂的工作流之一。

- `country_research_service.py`
  负责国别深度研究报告生成。

- `quarterly_report_service.py`
  负责季度经济报告生成。

- `image_translation_service.py`
  负责图片转译。

- `mineru_service.py`
  对接 MinerU 做高精度 PDF 提取。

- `web_crawler_service.py`
  对接 Firecrawl 等抓取能力。

- `file_service.py`
  负责文件保存、目录初始化、哈希计算、路径管理。

如果要理解项目，“先看 services，再看 endpoints”通常比反过来更快。

---

## 7. 数据模型怎么理解

后端模型主要在 `backend/models/`。

最重要的是两个文档域模型：

1. `Document`
   面向“前沿报告库”

   关键字段：
   - `title`
   - `original_filename`
   - `document_type`
   - `file_path`
   - `file_hash`
   - `content`
   - `content_preview`
   - `source_url`
   - `source_type`
   - `owner_id`
   - `is_shared`

   它更像“原始研究材料”。

2. `OfficialDocument`
   面向“公文库”

   关键字段：
   - `title`
   - `source`
   - `file_path`
   - `content`
   - `is_verified`
   - `verified_by`
   - `verified_at`

   它更像“经过审核、可作为模板参考的正式材料”。

此外还有：

- `User`
- `Tag`
- `Task`
- `DocumentTranslation`
- `ImageTranslation`

整体看下来，这个项目的数据中心仍然是“文档”，其他能力大多围绕文档展开。

---

## 8. 核心工作流怎么理解

### 8.1 公文对照翻译

这是一个相对直接的工作流：

1. 提取原文
2. 用户可编辑提取结果
3. 分段翻译
4. 输出对照文本或 Word

它适合做已有材料的保守加工。

### 8.2 学术报告转公文

这是当前最重的工作流，整体是“先拆解，再写作，再整合”：

1. 文档提取
2. 知识检索
3. 大纲生成
4. 标题提取
5. 内容整理
6. 章节并发写作
7. 模板转换
8. 内容整合
9. 内容检查
10. 最终调整

这个流程的特点：

- 不是一次性生成整篇文章
- 会让不同模型承担不同阶段
- 有较强的中间态和调试记录需求

### 8.3 国别深度研究

更像“抓数据 + 多段分析 + 汇总报告”的流水线：

1. 加载国家数据源配置
2. 并发抓取数据
3. 经济分析
4. 政治分析
5. 外交分析
6. 报告生成
7. 质量审核

### 8.4 季度报告生成

和国别研究是近亲，复用数据源配置与报告式生成思路，但主题换成宏观与金融季报。

### 8.5 图片转译

把图片中的英文内容提取并翻译，保留版式，结果不是纯文本，而是加工后的图片资产。

---

## 9. 模型与外部依赖怎么分工

从当前配置和 README 看，项目采用“多模型分工”而不是单模型统一完成：

- Kimi-K2.5
  更常用于大纲、结构化整理、检查、最终调整

- DeepSeek-V3
  更常用于章节写作、分析类生成

- Gemini / OpenRouter
  更常用于图片转译和部分整合场景

- GLM-5
  用于部分报告生成场景

外部依赖还包括：

- Firecrawl：网页抓取
- MinerU：PDF 高精度提取
- PostgreSQL / SQLite：数据存储
- Redis：缓存或任务相关能力
- 腾讯云 COS：部分文件存储能力

这意味着项目不是“本地纯推理”，而是高度依赖外部 API 协同。

---

## 10. 配置与运行机制

配置入口在：

- `backend/core/config.py`

可以看出系统关心几类配置：

- 应用配置：host、port、debug、API 前缀
- 数据库配置：`DATABASE_URL`
- Redis 配置
- 文件存储目录
- 多个模型 API Key 与 Base URL
- Firecrawl、MinerU、COS 等外部服务配置

数据库初始化逻辑在：

- `backend/core/database.py`

当前实现有一个明显的开发态特征：

- 如果 `ENVIRONMENT == development`，启动时会直接 `create_all`

也就是说，这个项目目前仍然保留了“开发期快速起项目”的设计，并不完全是严格的生产化迁移流程。

---

## 11. 文件与调试产物怎么理解

项目里有大量 `storage/` 与 `debug_outputs/` 内容，这不是噪音，而是工作流的一部分。

典型用途：

- 保存上传文件
- 保存缩略图、缓存文件
- 保存每一步工作流的输入、输出、提示词、模型信息
- 帮助追查长流程失败、超时、格式解析错误

这说明作者对“可调试性”是有意识设计的，尤其在“学术报告转公文”这种多阶段链路上非常重要。

相关说明文档包括：

- `DEBUG_GUIDE.md`
- `STORAGE_ARCHITECTURE.md`
- `MINERU_INTEGRATION.md`
- `OPENROUTER_API_GUIDE.md`
- `LLM_OUTPUT_FORMAT_GUIDE.md`

如果后续要继续维护工作流，这几个文档很值得配合代码一起看。

---

## 12. 当前项目的实现风格

从代码现状看，这个项目有几个鲜明特征：

1. 业务导向很强
   不是为了做通用平台，而是针对央行研究、公文写作这个具体场景定制。

2. 工作流导向强于资源导向
   文档管理只是入口，真正复杂度在工作流编排。

3. 对长文本和长链路有大量特殊处理
   包括分层摘要、分段整理、并发写作、流式进度、调试日志。

4. 工程化程度中等偏上，但仍保留快速迭代痕迹
   例如开发态默认用户、启动自动建表、部分功能已接近产品态，部分功能仍像持续演进中的实验模块。

---

## 13. 新人接手时建议先看什么

如果要快速接手，建议按这个顺序看：

1. `README.md`
   先建立功能全景。

2. `frontend/src/app/App.tsx`
   看前端主界面怎么切模块。

3. `backend/main.py`
   看后端如何启动和挂路由。

4. `backend/api/v1/api.py`
   看接口总入口。

5. `backend/api/endpoints/workflows.py`
   看长流程是怎么暴露给前端的。

6. `backend/services/academic_to_official_service.py`
   看最复杂的核心工作流。

7. `backend/services/document_service.py`
   看文档主链路和基础 CRUD。

8. `backend/core/config.py`
   看所有外部依赖和环境变量。

9. `frontend/src/app/components/features/library`
   看前端最核心业务交互。

10. `backend/storage/debug_outputs/`
   结合真实样例理解工作流中间态。

---

## 14. 这份项目的本质判断

如果用一句更工程化的话概括：

这是一个“以文档为中心、以工作流为核心、以多模型协作为生成引擎”的研究与公文生产系统。

它的真正难点不在页面，而在下面三件事：

- 如何把复杂材料拆成可控的中间步骤
- 如何让不同模型在不同阶段协作
- 如何让长流程在失败、超时、格式漂移时仍可调试、可回退

所以后续无论是优化性能、稳定性，还是扩展新模块，优先级通常都应该放在工作流编排、进度反馈、错误恢复和调试链路上。

