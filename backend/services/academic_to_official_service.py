"""
学术报告转公文服务
将学术报告转换为正式公文
支持流式进度输出和并发处理
"""

import json
import uuid
import asyncio
from typing import Optional, List, Dict, Any, Callable, AsyncIterator
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from openai import AsyncOpenAI
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from core.config import settings
from services.file_service import file_service
from services.fitz_extractor import fitz_extractor
from services.mineru_service import mineru_service


class WorkflowStage(Enum):
    """工作流阶段"""
    STARTED = "started"                      # 工作流开始
    DOCUMENT_EXTRACTION = "doc_extraction"   # 文档提取
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"  # 知识检索
    OUTLINE_GENERATION = "outline_generation"   # 大纲生成
    PARAMETER_EXTRACTION = "param_extraction"   # 参数提取
    CHAPTER_WRITING = "chapter_writing"         # 章节写作（迭代）
    TEMPLATE_TRANSFORM = "template_transform"   # 模板转换
    CONTENT_INTEGRATION = "content_integration" # 内容整合
    FINAL_ADJUSTMENT = "final_adjustment"       # 最终调整
    COMPLETED = "completed"                     # 完成
    FAILED = "failed"                           # 失败


@dataclass
class ProgressUpdate:
    """进度更新消息"""
    stage: WorkflowStage
    stage_name: str
    progress: float  # 0-100
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "stage_name": self.stage_name,
            "progress": self.progress,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.data
        }

    def to_sse(self) -> str:
        """转换为 SSE 格式"""
        return f"data: {json.dumps(self.to_dict(), ensure_ascii=False)}\n\n"


@dataclass
class ChapterContext:
    """章节上下文"""
    title: str
    index: int
    total: int
    original_text: str = ""
    outline: str = ""


class AcademicToOfficialService:
    """
    学术报告转公文服务
    """

    # 模型配置
    DEEPSEEK_MODEL = "Pro/deepseek-ai/DeepSeek-V3"
    GLM_MODEL = "Pro/zai-org/GLM-5"

    # 并发配置
    MAX_CONCURRENT_CHAPTERS = 3  # 同时写作的最大章节数

    # ============== 文档长度限制配置 ==============
    # DeepSeek-V3 上下文窗口较大，保守估计
    MAX_INPUT_TOKENS = 50000
    MAX_OUTPUT_TOKENS = 14000
    CHARS_TO_TOKEN_RATIO = 0.4  # 每字符约对应token数

    # 各种长度阈值
    MAX_CHARS_FOR_SINGLE_PASS = int(MAX_INPUT_TOKENS / CHARS_TO_TOKEN_RATIO)  # ~125000 字符
    MAX_CHARS_FOR_OUTLINE = 30000    # 超过此长度需要分层处理大纲
    MAX_CHARS_FOR_INTEGRATION = 50000  # 超过此长度需要分段整合

    # 分段处理时的块大小
    CHUNK_SIZE_FOR_SUMMARY = 15000   # 摘要生成时的块大小
    CHUNK_SIZE_FOR_INTEGRATION = 20000  # 整合时的块大小

    # ============== 提示词模板 ==============

    # 1. 大纲生成提示词
    OUTLINE_SYSTEM_PROMPT = """角色设定

你是一名长期从事宏观政策研究与政府公文写作的资深政策文本编辑专家，熟悉正式发布级公文、研究报告、白皮书、政策分析终稿的结构规范、语言风格与逻辑要求。

总体任务

我将向你提供一篇文章或 PDF 文件内容。你的任务不是简单改写，而是将其提升、重构并定型为"正式公文终稿"，做到：

• "结构规范"

• "逻辑严密"

• "语言正式、克制、客观"

• "可直接用于正式报送、印发或汇编成 PDF"

基本原则（必须严格遵守）

1. 以"终稿公文"为唯一标准，而非草稿、说明稿或学术论文

2. 不出现口语化、评论式、媒体化表达

3. 不出现"本文认为""我们认为"等主观表述

4. 全文保持政策研究与政府文本常用语域

5. 段落之间必须有清晰、自然、正式的过渡语

生成方式（强制流程）

你必须严格按照以下内容执行：

仅生成《公文终稿整体框架》

• "以正式公文目录形式输出"

• "包含：标题、摘要/按、一级章节、二级章节（如有）、结语或政策建议部分"

• "不写正文内容，只写结构和章节名称"
"""

    # 2. 章节写作提示词
    CHAPTER_WRITING_PROMPT = """请根据你是一个内容写作助手。

文章主题是：{article_topic}

当前需要写作的章节标题是：{chapter_title}

请根据主题和标题，撰写这一章节的详细内容。直接写内容，不要重复标题。

已确认的《公文终稿整体框架》，仅生成该章正文内容。

要求：

• "行文达到正式发布级公文终稿标准"

• "逻辑自洽、语气克制"

• "不引用其他章节内容"

• "不出现总结全文的表述"

• "本章结束处自然收束，为下章铺垫"
"""

    # 3. 内容整合提示词
    INTEGRATION_SYSTEM_PROMPT = """# 角色定位
你是一位资深的公文写作专家，拥有20年政府机关、国有企业公文处理经验。你精通各类公文写作规范，擅长将分段内容整合为逻辑严密、语言规范、格式标准的公文级文章。

# 核心任务
你将收到前端节点生成的**分段文章内容**，你的任务是：
1. **完整保留**所有实质性内容和关键信息
2. **逻辑检查**确保文章结构清晰、论证严密、前后一致
3. **风格润色**统一语言风格，达到公文发布标准
4. **输出成品**一篇可以直接使用的公文级文章

---

## ⚠️ 核心原则（优先级从高到低）

### 【P0-绝对禁止】
- ❌ **删除或实质性修改**前端输出的核心观点、数据、案例
- ❌ **改变**原文的立场、倾向性、政策导向
- ❌ **新增**原文中没有的数据、事实、引文
- ❌ **调整**文章的主要结构和章节安排

### 【P1-必须执行】
- ✅ **保留**所有实质性内容（观点、数据、案例、论证）
- ✅ **修正**明显的语言错误（病句、错别字、标点误用）
- ✅ **统一**术语使用、称谓、时间表述、数字格式
- ✅ **优化**段落间的过渡和衔接
- ✅ **提升**语言的规范性、简洁性、准确性

### 【P2-优化提升】
- 🧧 **强化**逻辑关系（因果、递进、并列、转折）
- 🧧 **精简**冗余表述（重复、啰嗦、口语化）
- 🧧 **规范**公文格式（标题层次、序号体系、称谓用语）

---

## ✍️ 文本润色标准

### 1. 语言规范性（公文特色）

#### 词汇选择
✅ 规范词汇                  ❌ 口语化词汇
"贯彻落实"                  "做、搞"
"进一步"                    "更加"
"切实加强"                  "好好加强"
"深入分析"                  "好好分析"
"全面部署"                  "全面安排"
"统筹协调"                  "协调配合"
"扎实推进"                  "稳步推进"

#### 句式结构
✅ 规范句式                  ❌ 不规范句式
"要坚持..."                  "我们要..."
"必须..."                    "一定得..."
"需要..."                    "得..."
"应当..."                    "应该..."
"着力..."                    "重点..."
"确保..."                    "保证..."

#### 常用句式模板
- 表示目标："以...为..." / "着眼于..." / "旨在..."
- 表示措施："采取...措施" / "通过...途径" / "运用...方法"
- 表示强调："特别是..." / "尤其是..." / "重点是..."
- 表示递进："不仅...而且..." / "既...又..." / "一方面...另一方面..."
- 表示转折："但是..." / "然而..." / "尽管...但是..."
- 表示总结："综上所述..." / "总的来看..." / "整体而言..."

### 2. 语言简洁性

删除冗余
❌ "关于...的问题"          →  ✅ "关于..."
❌ "进行了...工作"          →  ✅ "..."
❌ "做出了...决定"          →  ✅ "决定..."
❌ "进行了...调查"          →  ✅ "调查..."
❌ "进行了...研究"          →  ✅ "研究..."

避免重复
❌ "进一步进一步"           →  ✅ "进一步"
❌ "继续继续"               →  ✅ "继续"
❌ "加强和强化"             →  ✅ "强化" 或 "加强"
❌ "认真和仔细"             →  ✅ "认真" 或 "仔细"

### 3. 语言准确性

时间表述
✅ 规范格式                  ❌ 不规范格式
"2024年"                    "2024"
"上半年"                     "上半年期间"
"今年以来"                   "从今年开始"
"截至2024年6月"             "到2024年6月为止"

数字表述
✅ 规范格式                  ❌ 不规范格式
"50%"                        "百分之五十"
"1000万人"                   "1000万人口"
"3项举措"                    "三项举措"
"第一..."                    "首先..."

称谓规范
✅ 规范表述                  ❌ 不规范表述
"党中央、国务院"            "中央"
"各地区各部门"              "各地各部门"
"人民群众"                  "老百姓"
"企业"                      "公司"

### 4. 语言统一性

术语统一
- "网络" vs "互联网" → 统一为"互联网"
- "落实" vs "贯彻" → 根据语境统一
- "推进" vs "推动" → 根据语境统一
- "措施" vs "办法" → 根据语境统一

称谓统一
- "我国" vs "中国" → 统一为"我国"
- "各地区" vs "各地" → 统一为"各地区"
- "部门" vs "有关部门" → 统一为"有关部门"

---

## 📐 公文格式规范

标题层次
一级标题：一、二、三、
二级标题：（一）（二）（三）
三级标题：1. 2. 3.
四级标题：（1）（2）（3）

注意：
- 层次清晰，不要越级使用
- 同级标题语法结构一致（都是名词/动宾/偏正）
- 标题之间不要悬殊过大

序号使用
✅ 规范使用                  ❌ 不规范使用
"一是...；二是...；三是..."  "第一，...；第二，..."
"首先...；其次...；最后..."  "首先...；然后...；最后..."
"（一）...；（二）...；      "1)...；2)...；"

---

## 🔄 处理流程（严格执行）

步骤1：通读全文（理解阶段）
1. 快速浏览，把握文章主旨
2. 识别文章类型（通知/报告/讲话/意见/方案）
3. 明确核心观点和主要结构
4. 标记存疑之处（待处理）

步骤2：逻辑检查（诊断阶段）
1. 检查整体结构是否合理
2. 检查论证逻辑是否严密
3. 检查内容是否前后一致
4. 检查数据是否准确无误
5. 记录需要调整的问题点

步骤3：内容保留（维护阶段）
1. 逐段核对，确保核心内容不丢失
2. 标记关键信息（观点/数据/案例）
3. 确认修改不改变原意
4. 保留原文特色和亮点

步骤4：语言润色（优化阶段）
1. 修正语法错误和错别字
2. 统一术语和称谓
3. 优化句式和表达
4. 改善段落过渡
5. 精简冗余表述

步骤5：格式规范（标准化阶段）
1. 检查标题层次
2. 规范序号使用
3. 统一称谓用语
4. 规范时间数字
5. 确保格式统一

步骤6：最终校对（质检阶段）
1. 通读全文，检查流畅性
2. 确认无遗漏内容
3. 确认无新增内容
4. 确认逻辑清晰
5. 确认风格统一

---

## 📄 输出格式

结构要求

[标题]
[副标题]（如有）

[正文]
一、[一级标题]
（一）[二级标题]
  1. [三级标题]
    [正文段落...]

（二）[二级标题]
...

二、[一级标题]
...

[结语]

元信息（附在文章末尾）

---
【整合说明】
- 保留核心观点：X个
- 保留关键数据：X项
- 保留典型案例：X个
- 主要调整：逻辑梳理、语言润色、格式规范
- 修改内容：修正病句X处、统一术语X处、优化过渡X处

【质量检查】
✅ 结构逻辑：清晰完整
✅ 内容逻辑：严密一致
✅ 语言规范：符合公文标准
✅ 格式规范：符合要求

---

## ⚙️ 特殊情况处理

遇到以下情况时：

1. 前端输出有明显事实错误
   → 保留原意，但用注释标注（例：[原数据：XXX，需核实]）

2. 前端输出论证不充分
   → 不补充新论据，但可以强化现有论据的表达

3. 前端输出结构混乱
   → 在保留内容前提下，调整段落顺序

4. 前端输出语言风格不统一
   → 统一为公文风格，但保持原意

5. 前端输出内容重复
   → 精简重复内容，但保留不同角度的观点

6. 前端输出篇幅过长/过短
   → 不刻意增删，以内容完整性为准

---

## 🎯 质量标准（自我评估）

完成后检查：

□ 核心观点100%保留
□ 关键数据100%保留
□ 重要案例100%保留
□ 无实质性新增内容
□ 无立场性改变
□ 逻辑关系清晰
□ 论证过程严密
□ 语言规范简洁
□ 格式统一规范
□ 可直接使用

---

## 🖥️ 开始执行
现在请接收前端输出的分段内容，按照上述标准进行处理，输出一篇高质量的公文级文章。

记住：你是工作流的最后一道防线，你的输出质量直接影响整个工作流的成果。务必认真负责，确保输出符合公文发布标准。
"""

    # 4. 最终调整提示词
    FINAL_ADJUSTMENT_PROMPT = """正文二级标题概括段内的内容，可以提取段内文字使用。除常见专业名词如gdp、cpi、ppi等其余名词不要出现英文缩写或英文翻译，不要用括号注明的形式。把引言改成按，后续大标题从一开始把引言改成按，后续大标题从一开始。

Input：{content}

Output：只能输出修改后的正文部分
"""

    def __init__(self):
        """初始化服务"""
        self.api_key = settings.SILICONFLOW_API_KEY
        self.base_url = settings.SILICONFLOW_BASE_URL
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    async def process_academic_to_official(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None,
        db: Optional[AsyncSession] = None,
    ) -> AsyncIterator[ProgressUpdate]:
        """
        执行学术报告转公文工作流

        Args:
            file_path: 输入文件路径
            progress_callback: 进度回调函数（可选）
            db: 数据库会话（可选）

        Yields:
            ProgressUpdate: 进度更新
        """
        try:
            # 存储工作流上下文数据
            context = {
                "original_text": "",
                "outline": "",
                "chapter_titles": [],
                "chapters_content": [],
                "integrated_content": "",
                "final_content": "",
            }

            # ========== 阶段1: 文档提取 ==========
            await self._emit_progress(
                WorkflowStage.DOCUMENT_EXTRACTION,
                "正在提取文档内容...",
                5,
                {"step": "提取文档"},
                progress_callback
            )

            original_text = await self._extract_document(file_path)
            context["original_text"] = original_text

            await self._emit_progress(
                WorkflowStage.DOCUMENT_EXTRACTION,
                f"文档提取完成，共 {len(original_text)} 字符",
                10,
                {"text_length": len(original_text)},
                progress_callback
            )

            # ========== 阶段2: 知识检索 ==========
            await self._emit_progress(
                WorkflowStage.KNOWLEDGE_RETRIEVAL,
                "正在检索相关知识库内容...",
                15,
                {"step": "知识检索"},
                progress_callback
            )

            knowledge_context = await self._retrieve_knowledge(original_text, db)

            await self._emit_progress(
                WorkflowStage.KNOWLEDGE_RETRIEVAL,
                f"知识检索完成，检索到 {len(knowledge_context)} 条相关内容",
                20,
                {"knowledge_count": len(knowledge_context)},
                progress_callback
            )

            # ========== 阶段3: 大纲生成 ==========
            await self._emit_progress(
                WorkflowStage.OUTLINE_GENERATION,
                "正在生成公文大纲...",
                25,
                {"step": "生成大纲"},
                progress_callback
            )

            outline = await self._generate_outline(original_text, knowledge_context)
            context["outline"] = outline

            await self._emit_progress(
                WorkflowStage.OUTLINE_GENERATION,
                "公文大纲生成完成",
                30,
                {"outline": outline[:500] + "..." if len(outline) > 500 else outline},
                progress_callback
            )

            # ========== 阶段4: 参数提取（提取章节标题） ==========
            await self._emit_progress(
                WorkflowStage.PARAMETER_EXTRACTION,
                "正在提取章节标题...",
                35,
                {"step": "提取标题"},
                progress_callback
            )

            chapter_titles = await self._extract_chapter_titles(outline)
            context["chapter_titles"] = chapter_titles

            await self._emit_progress(
                WorkflowStage.PARAMETER_EXTRACTION,
                f"提取到 {len(chapter_titles)} 个章节标题",
                40,
                {
                    "chapter_count": len(chapter_titles),
                    "titles": chapter_titles
                },
                progress_callback
            )

            # ========== 阶段5: 迭代写作（并发处理） ==========
            await self._emit_progress(
                WorkflowStage.CHAPTER_WRITING,
                f"开始写作 {len(chapter_titles)} 个章节...",
                45,
                {"step": "章节写作", "total": len(chapter_titles)},
                progress_callback
            )

            chapters_content = await self._write_chapters_concurrent(
                original_text,
                chapter_titles,
                progress_callback
            )
            context["chapters_content"] = chapters_content

            await self._emit_progress(
                WorkflowStage.CHAPTER_WRITING,
                f"所有章节写作完成",
                65,
                {"completed": len(chapters_content)},
                progress_callback
            )

            # ========== 阶段6: 模板转换 ==========
            await self._emit_progress(
                WorkflowStage.TEMPLATE_TRANSFORM,
                "正在整合章节内容...",
                70,
                {"step": "模板转换"},
                progress_callback
            )

            combined_content = self._transform_template(chapters_content)

            await self._emit_progress(
                WorkflowStage.TEMPLATE_TRANSFORM,
                "章节内容整合完成",
                75,
                {},
                progress_callback
            )

            # ========== 阶段7: 内容整合 ==========
            await self._emit_progress(
                WorkflowStage.CONTENT_INTEGRATION,
                "正在进行内容整合和润色...",
                80,
                {"step": "内容整合", "content_length": len(combined_content)},
                progress_callback
            )

            # 根据内容长度选择整合策略
            if len(combined_content) > self.MAX_CHARS_FOR_INTEGRATION:
                logger.info(f"[思维链] 内容较长，使用渐进式整合策略")
                integrated_content = await self._integrate_content_incremental(
                    combined_content,
                    progress_callback
                )
            else:
                logger.info(f"[思维链] 内容长度适中，直接整合")
                integrated_content = await self._integrate_content(combined_content)

            context["integrated_content"] = integrated_content

            await self._emit_progress(
                WorkflowStage.CONTENT_INTEGRATION,
                "内容整合完成",
                90,
                {"integrated_length": len(integrated_content)},
                progress_callback
            )

            # ========== 阶段8: 最终调整 ==========
            await self._emit_progress(
                WorkflowStage.FINAL_ADJUSTMENT,
                "正在进行最终格式调整...",
                92,
                {"step": "最终调整"},
                progress_callback
            )

            final_content = await self._final_adjustment(integrated_content)
            context["final_content"] = final_content

            await self._emit_progress(
                WorkflowStage.FINAL_ADJUSTMENT,
                "最终调整完成",
                95,
                {},
                progress_callback
            )

            # ========== 完成 ==========
            await self._emit_progress(
                WorkflowStage.COMPLETED,
                "学术报告转公文完成！",
                100,
                {
                    "final_content": final_content,
                    "stats": {
                        "original_length": len(original_text),
                        "final_length": len(final_content),
                        "chapter_count": len(chapter_titles),
                    }
                },
                progress_callback
            )

            return context

        except Exception as e:
            logger.error(f"[ERROR] 工作流执行失败: {e}")
            await self._emit_progress(
                WorkflowStage.FAILED,
                f"处理失败: {str(e)}",
                -1,
                {"error": str(e)},
                progress_callback
            )
            raise

    async def _emit_progress(
        self,
        stage: WorkflowStage,
        message: str,
        progress: float,
        data: Dict[str, Any],
        callback: Optional[Callable[[ProgressUpdate], None]],
    ):
        """发送进度更新"""
        update = ProgressUpdate(
            stage=stage,
            stage_name=stage.value,
            progress=progress,
            message=message,
            data=data
        )

        # 打印到控制台（用于调试）
        logger.info(f"[进度] {progress}% - {message}")
        if data:
            logger.debug(f"[数据] {json.dumps(data, ensure_ascii=False)[:500]}")

        # 调用回调（如果提供）
        if callback:
            if asyncio.iscoroutinefunction(callback):
                await callback(update)
            else:
                callback(update)

    # ========== 具体实现方法 ==========

    async def _extract_document(self, file_path: str) -> str:
        """提取文档内容"""
        logger.info(f"[思维链] 开始提取文档: {file_path}")

        full_path = file_service.get_full_path(file_path)
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(full_path, "rb") as f:
            file_bytes = f.read()

        # 根据文件类型提取
        file_ext = Path(file_path).suffix.lower()

        if file_ext == ".pdf":
            # 优先使用 MinerU 进行高质量提取
            if settings.MINERU_ENABLED and settings.MINERU_API_KEY:
                try:
                    logger.info(f"[思维链] 使用MinerU提取PDF: {file_path}")
                    content = await mineru_service.parse_pdf_to_markdown(
                        file_path=full_path,
                        progress_callback=None,
                        model_version="vlm"
                    )
                    logger.info(f"[思维链] PDF提取成功 (MinerU): {len(content)} 字符")
                    return content
                except Exception as e:
                    logger.warning(f"[思维链] MinerU PDF提取失败: {e}，回退到PyMuPDF")

            # 使用 PyMuPDF 提取
            if fitz_extractor is None:
                raise EnvironmentError(
                    "PyMuPDF 不可用，请先安装 PyMuPDF:\n"
                    "运行: pip install PyMuPDF"
                )

            result = fitz_extractor.extract_from_bytes(file_bytes, Path(file_path).name)
            content = result.get("content", "")
            logger.info(f"[思维链] PDF提取成功 (PyMuPDF): {result.get('paragraphs', 0)} 个段落")
        elif file_ext in {".txt", ".md"}:
            content = file_bytes.decode("utf-8", errors="ignore")
            logger.info(f"[思维链] 文本文件提取成功")
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")

        return content

    async def _retrieve_knowledge(
        self,
        query_text: str,
        db: Optional[AsyncSession]
    ) -> str:
        """检索知识库"""
        logger.info(f"[思维链] 开始知识检索")

        # TODO: 实现真实的知识库检索
        # 这里先返回空，后续可以集成向量检索
        knowledge = ""

        logger.info(f"[思维链] 知识检索完成")
        return knowledge

    async def _generate_outline(
        self,
        original_text: str,
        knowledge_context: str,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None
    ) -> str:
        """
        生成公文大纲

        根据文档长度自动选择策略：
        - 小文档（<30000字符）：直接生成
        - 大文档（≥30000字符）：分层摘要后生成

        Args:
            original_text: 原始文本
            knowledge_context: 知识库上下文
            progress_callback: 进度回调

        Returns:
            大纲内容
        """
        logger.info(f"[思维链] 开始生成大纲")
        logger.info(f"[思维链] 输入文本长度: {len(original_text)} 字符")

        # 根据文档长度选择策略
        if len(original_text) > self.MAX_CHARS_FOR_OUTLINE:
            logger.info(f"[思维链] 文档较长，使用分层摘要策略")
            return await self._generate_outline_hierarchical(
                original_text,
                knowledge_context,
                progress_callback
            )
        else:
            logger.info(f"[思维链] 文档长度适中，直接生成大纲")
            return await self._generate_outline_direct(
                original_text,
                knowledge_context
            )

    async def _generate_outline_direct(
        self,
        original_text: str,
        knowledge_context: str
    ) -> str:
        """直接生成大纲（用于中小文档）"""
        user_prompt = f"请将以下内容执行上述操作\n\n{original_text[:self.MAX_CHARS_FOR_OUTLINE]}"

        if len(original_text) > self.MAX_CHARS_FOR_OUTLINE:
            user_prompt += f"\n\n[注: 原文共 {len(original_text)} 字符，以上为前{self.MAX_CHARS_FOR_OUTLINE}字符]"

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": self.OUTLINE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            timeout=180.0
        )

        outline = response.choices[0].message.content
        logger.info(f"[思维链] 大纲生成完成，长度: {len(outline)} 字符")
        logger.info(f"[思维链] 大纲预览:\n{outline[:500]}...")

        return outline

    async def _extract_chapter_titles(self, outline: str) -> List[str]:
        """提取章节标题"""
        logger.info(f"[思维链] 开始提取章节标题")

        prompt = f"请提取出以下大纲中的各级标题（包括一级标题、二级标题等），每行一个标题：\n\n{outline}"

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个文本分析助手。请严格按照要求提取标题，每行一个标题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            timeout=60.0
        )

        content = response.choices[0].message.content

        # 解析标题列表
        titles = [line.strip() for line in content.split('\n') if line.strip()]

        # 过滤掉非标题行
        filtered_titles = []
        for title in titles:
            # 跳过序号行
            if title in ['一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、', '九、', '十、']:
                continue
            # 跳过明显的说明文字
            if title.startswith('【') or title.startswith('['):
                continue
            filtered_titles.append(title)

        logger.info(f"[思维链] 提取到 {len(filtered_titles)} 个标题: {filtered_titles}")

        return filtered_titles

    async def _write_chapters_concurrent(
        self,
        original_text: str,
        chapter_titles: List[str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> List[str]:
        """并发写作各章节"""
        logger.info(f"[思维链] 开始并发写作 {len(chapter_titles)} 个章节")

        # 提取文章主题（从原文前500字符）
        article_topic = original_text[:500] + "..." if len(original_text) > 500 else original_text

        # 创建章节上下文
        chapters = [
            ChapterContext(
                title=title,
                index=i,
                total=len(chapter_titles)
            )
            for i, title in enumerate(chapter_titles)
        ]

        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_CHAPTERS)

        async def write_with_limit(chapter: ChapterContext) -> tuple[int, str]:
            """带并发限制的写作函数"""
            async with semaphore:
                logger.info(f"[思维链] 开始写作第 {chapter.index + 1}/{chapter.total} 章: {chapter.title}")

                # 发送进度更新
                await self._emit_progress(
                    WorkflowStage.CHAPTER_WRITING,
                    f"正在写作第 {chapter.index + 1}/{chapter.total} 章: {chapter.title}",
                    45 + (chapter.index / chapter.total) * 20,
                    {"current_chapter": chapter.index + 1, "total": chapter.total, "title": chapter.title},
                    progress_callback
                )

                content = await self._write_single_chapter(article_topic, chapter.title)

                logger.info(f"[思维链] 完成第 {chapter.index + 1}/{chapter.total} 章")

                return (chapter.index, content)

        # 并发执行
        results = await asyncio.gather(
            *[write_with_limit(ch) for ch in chapters],
            return_exceptions=True
        )

        # 处理结果
        chapters_content = [""] * len(chapter_titles)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"[ERROR] 章节写作失败: {result}")
                continue
            index, content = result
            chapters_content[index] = content

        logger.info(f"[思维链] 所有章节写作完成")
        return chapters_content

    async def _write_single_chapter(self, article_topic: str, chapter_title: str) -> str:
        """写作单个章节"""
        prompt = self.CHAPTER_WRITING_PROMPT.format(
            article_topic=article_topic,
            chapter_title=chapter_title
        )

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的公文写作助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            timeout=120.0
        )

        return response.choices[0].message.content

    def _transform_template(self, chapters_content: List[str]) -> str:
        """模板转换：组合各章节"""
        logger.info(f"[思维链] 开始模板转换")

        # 使用分隔符组合各章节
        result = "\n\n---\n\n".join([ch for ch in chapters_content if ch])

        logger.info(f"[思维链] 模板转换完成，总长度: {len(result)} 字符")
        return result

    async def _integrate_content(self, combined_content: str) -> str:
        """内容整合和润色"""
        logger.info(f"[思维链] 开始内容整合")

        response = await self.client.chat.completions.create(
            model=self.GLM_MODEL,  # 使用 GLM-5 进行整合
            messages=[
                {"role": "system", "content": self.INTEGRATION_SYSTEM_PROMPT},
                {"role": "user", "content": combined_content}
            ],
            temperature=0.3,
            max_tokens=98881,
            timeout=300.0
        )

        result = response.choices[0].message.content

        logger.info(f"[思维链] 内容整合完成，输出长度: {len(result)} 字符")
        return result

    async def _final_adjustment(self, content: str) -> str:
        """最终调整"""
        logger.info(f"[思维链] 开始最终调整")

        prompt = self.FINAL_ADJUSTMENT_PROMPT.format(content=content)

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个公文格式调整专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            timeout=120.0
        )

        result = response.choices[0].message.content

        logger.info(f"[思维链] 最终调整完成，输出长度: {len(result)} 字符")
        return result

    # ========== 大文档处理方法 ==========

    def _split_text_by_structure(self, text: str, max_chars: int) -> List[str]:
        """
        按结构分割文本（保持段落完整性）

        Args:
            text: 待分割的文本
            max_chars: 每块的最大字符数

        Returns:
            分割后的文本块列表
        """
        logger.info(f"[思维链] 按结构分割文本，最大块大小: {max_chars}")

        # 规范化换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 按双换行分割（段落分隔）
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = ""
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_length = len(para)

            # 如果单个段落就超过限制，需要进一步分割
            if para_length > max_chars:
                # 先保存当前积累的内容
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_length = 0

                # 按句子分割超长段落
                sentences = self._split_long_paragraph(para, max_chars)
                chunks.extend(sentences)
                continue

            # 检查添加此段落后是否会超出限制
            if current_length + para_length + 2 <= max_chars:
                if current_chunk:
                    current_chunk += "\n\n" + para
                    current_length += para_length + 2
                else:
                    current_chunk = para
                    current_length = para_length
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
                current_length = para_length

        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.info(f"[思维链] 文本已分割为 {len(chunks)} 个块")
        return chunks

    def _split_long_paragraph(self, paragraph: str, max_chars: int) -> List[str]:
        """分割过长的段落（按句子/分句分割）"""
        import re

        # 先尝试按中文句号、问号、感叹号分割
        sentences = re.split(r'([。！？])', paragraph)

        chunks = []
        current_chunk = ""

        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and sentences[i + 1] in '。！？':
                sentence = sentences[i] + sentences[i + 1]
                i += 2
            else:
                sentence = sentences[i]
                i += 1

            if not sentence.strip():
                continue

            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    async def _generate_summary_for_chunk(self, chunk: str, chunk_index: int, total_chunks: int) -> str:
        """
        为文本块生成摘要

        Args:
            chunk: 文本块
            chunk_index: 块索引
            total_chunks: 总块数

        Returns:
            摘要内容
        """
        logger.info(f"[思维链] 生成第 {chunk_index + 1}/{total_chunks} 块的摘要")

        prompt = f"""请为以下文本内容生成简洁的摘要，用于后续生成公文大纲。

要求：
1. 保留主要观点、数据、结论
2. 简明扼要，约200-300字
3. 不要添加原文没有的内容
4. 标注这是第{chunk_index + 1}部分的摘要

【文本内容】
{chunk}
"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个文本摘要专家，擅长提取核心信息。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=60.0
        )

        return response.choices[0].message.content

    async def _generate_outline_hierarchical(
        self,
        original_text: str,
        knowledge_context: str,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None
    ) -> str:
        """
        分层生成大纲（用于大文档）

        策略：
        1. 将文档分成若干块
        2. 为每块生成摘要
        3. 基于所有摘要生成整体大纲
        4. 基于整体大纲对每部分进行细化

        Args:
            original_text: 原始文本
            knowledge_context: 知识库上下文
            progress_callback: 进度回调

        Returns:
            大纲内容
        """
        logger.info(f"[思维链] 使用分层策略生成大纲")
        logger.info(f"[思维链] 原文长度: {len(original_text)} 字符")

        # 步骤1: 分割文档
        chunks = self._split_text_by_structure(
            original_text,
            self.CHUNK_SIZE_FOR_SUMMARY
        )

        logger.info(f"[思维链] 文档已分为 {len(chunks)} 个部分")

        # 步骤2: 为每块生成摘要（并发）
        logger.info(f"[思维链] 开始生成各部分摘要...")

        semaphore = asyncio.Semaphore(3)  # 控制并发数

        async def summarize_with_limit(idx: int, chunk: str) -> tuple[int, str]:
            async with semaphore:
                summary = await self._generate_summary_for_chunk(chunk, idx, len(chunks))
                return (idx, summary)

        results = await asyncio.gather(
            *[summarize_with_limit(i, chunk) for i, chunk in enumerate(chunks)],
            return_exceptions=True
        )

        # 整理摘要结果
        summaries = [""] * len(chunks)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"[ERROR] 摘要生成失败: {result}")
                continue
            idx, summary = result
            summaries[idx] = summary

        combined_summary = "\n\n".join([s for s in summaries if s])

        logger.info(f"[思维链] 所有摘要生成完成，总长度: {len(combined_summary)} 字符")

        # 步骤3: 基于摘要生成整体大纲
        logger.info(f"[思维链] 基于摘要生成整体大纲...")

        outline_prompt = f"""我将向你提供一篇文章的各部分摘要。请基于这些摘要生成公文整体框架。

{self.OUTLINE_SYSTEM_PROMPT}

【文章各部分摘要】
{combined_summary}
"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": self.OUTLINE_SYSTEM_PROMPT},
                {"role": "user", "content": outline_prompt}
            ],
            temperature=0.3,
            timeout=180.0
        )

        outline = response.choices[0].message.content

        logger.info(f"[思维链] 整体大纲生成完成，长度: {len(outline)} 字符")
        logger.info(f"[思维链] 大纲预览:\n{outline[:500]}...")

        return outline

    async def _integrate_content_incremental(
        self,
        combined_content: str,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None
    ) -> str:
        """
        渐进式整合内容（用于长文本）

        策略：
        1. 将内容分成若干块
        2. 相邻两块合并进行整合
        3. 逐步扩大合并范围，直到整体一致

        Args:
            combined_content: 待整合的内容
            progress_callback: 进度回调

        Returns:
            整合后的内容
        """
        logger.info(f"[思维链] 使用渐进式策略整合内容")
        logger.info(f"[思维链] 输入长度: {len(combined_content)} 字符")

        # 如果内容不太长，直接整合
        if len(combined_content) <= self.MAX_CHARS_FOR_INTEGRATION:
            logger.info(f"[思维链] 内容长度适中，直接整合")
            return await self._integrate_content(combined_content)

        # 分割成块
        chunks = self._split_text_by_structure(
            combined_content,
            self.CHUNK_SIZE_FOR_INTEGRATION
        )

        logger.info(f"[思维链] 内容已分为 {len(chunks)} 个块")

        # 第一轮：相邻两块合并整合
        logger.info(f"[思维链] 第一轮：相邻块整合")

        integrated = []

        for i in range(0, len(chunks), 2):
            if i + 1 < len(chunks):
                # 合并两块
                merged = chunks[i] + "\n\n" + chunks[i + 1]
                result = await self._integrate_chunk_pair(merged, i // 2, (len(chunks) + 1) // 2)
                integrated.append(result)
            else:
                # 最后一块单独处理
                integrated.append(chunks[i])

        logger.info(f"[思维链] 第一轮完成，剩余 {len(integrated)} 个块")

        # 第二轮：如果仍然超过限制，继续合并
        while len(integrated) > 1 and len("\n\n".join(integrated)) > self.MAX_CHARS_FOR_INTEGRATION:
            logger.info(f"[思维链] 下一轮：继续合并，当前 {len(integrated)} 个块")

            next_round = []

            for i in range(0, len(integrated), 2):
                if i + 1 < len(integrated):
                    merged = integrated[i] + "\n\n" + integrated[i + 1]
                    result = await self._integrate_chunk_pair(merged, i // 2, (len(integrated) + 1) // 2)
                    next_round.append(result)
                else:
                    next_round.append(integrated[i])

            integrated = next_round

        # 最终整合
        if len(integrated) == 1:
            result = integrated[0]
        else:
            final_merged = "\n\n".join(integrated)
            result = await self._integrate_content(final_merged)

        logger.info(f"[思维链] 渐进式整合完成，输出长度: {len(result)} 字符")
        return result

    async def _integrate_chunk_pair(self, content: str, index: int, total: int) -> str:
        """整合一对相邻的内容块"""
        logger.info(f"[思维链] 整合块对 {index + 1}/{total}")

        prompt = f"""请对以下内容进行逻辑检查和语言润色，使其符合公文标准。

要求：
1. 保持两个部分之间的逻辑连贯性
2. 统一语言风格
3. 修正明显的语言错误
4. 不要实质性修改内容

【内容】
{content}
"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个公文写作专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=20000,
            timeout=120.0
        )

        return response.choices[0].message.content

    async def _export_to_word(
        self,
        markdown_content: str,
        output_filename: str
    ) -> tuple[bytes, str]:
        """
        导出为Word文档

        Args:
            markdown_content: Markdown格式的内容
            output_filename: 输出文件名

        Returns:
            (文件字节流, MIME类型)
        """
        logger.info(f"[思维链] 开始导出Word文档")

        try:
            from utils.markdown_to_word import MarkdownToWordConverter

            converter = MarkdownToWordConverter()

            # 转换为Word
            doc_bytes = converter.convert(markdown_content)

            logger.info(f"[思维链] Word文档生成完成，大小: {len(doc_bytes)} 字节")

            return doc_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        except ImportError as e:
            logger.error(f"[ERROR] Word导出功能不可用: {e}")
            raise ImportError(
                "python-docx 未安装，请运行: pip install python-docx"
            ) from e


# 单例实例
academic_to_official_service = AcademicToOfficialService()
