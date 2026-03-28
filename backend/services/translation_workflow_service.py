"""
公文对照翻译工作流服务
支持 SSE 流式进度输出
"""

import json
import re
from typing import Optional, List, Dict, Any, Callable, AsyncIterator, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from openai import AsyncOpenAI
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from services.fitz_extractor import fitz_extractor


class TranslationStage(Enum):
    """翻译工作流阶段"""
    STARTED = "started"                    # 工作流开始
    DOCUMENT_EXTRACTION = "doc_extraction"  # 文档提取
    TEXT_ANALYSIS = "text_analysis"        # 文本分析
    TRANSLATING = "translating"            # 翻译处理
    CHUNK_PROCESSING = "chunk_processing"  # 分块处理
    COMPLETED = "completed"                # 完成
    FAILED = "failed"                      # 失败


@dataclass
class TranslationProgressUpdate:
    """翻译进度更新消息"""
    stage: TranslationStage
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


class TranslationWorkflowService:
    """
    公文对照翻译工作流服务
    使用 DeepSeek-V3 模型进行翻译
    """

    # 模型配置
    DEFAULT_MODEL = "deepseek-ai/DeepSeek-V3"

    # 翻译提示词模板（Markdown 格式输出）
    TRANSLATION_PROMPT = """【任务说明】 请将以下文本翻译为【简体中文】。

【输出格式：Markdown段落对照模式】 必须严格遵守以下排版规则：

1. 每个段落对照使用以下格式（不要使用代码块）：

## [可选标题]

**中文译文**：中文翻译内容

**英文原文**：English original content

---

2. 先中后英：每个对照块中，先输出中文译文，后输出英文原文。

3. 段落完整性：以原文的自然段落为单位进行组织。

4. 分隔符：每组"中英对照段落"之间使用 `---` 分隔。

【翻译质量要求】

1. 准确性：完整保留政策含义、逻辑结构、数据与判断。

2. 行文优化：中文表达需符合专业公文习惯。

3. 术语处理：专业术语首次出现时采用"中文译名（英文全称）"标注。

【严格禁令】

• 直接输出Markdown内容，不要用 ``` 包裹

• 不要输出开场白、说明、注释或任何元文本

• 不要输出"后续内容"、"因篇幅限制"、"此处仅展示"等说明文字

• 必须翻译原文的每一个段落，直到最后一个段落为止

• 禁止省略、概括或跳过任何内容

【原文内容】
{content}"""

    # 分批翻译时的简化提示词
    CHUNK_TRANSLATION_PROMPT = """请将以下文本翻译为简体中文。每个段落按以下格式输出：

**中文译文**：中文翻译内容

**英文原文**：English original content

---

【严格要求】
• 直接输出Markdown格式，不要用代码块包裹
• 必须翻译每个段落，不要省略任何内容
• 不要输出"后续内容"、"此处仅展示"等说明文字
• 继续保持相同的格式直到文本结束

【原文内容】
{content}"""

    def __init__(self):
        self.api_key = settings.SILICONFLOW_API_KEY
        self.base_url = settings.SILICONFLOW_BASE_URL
        self.model = self.DEFAULT_MODEL
        # 创建 OpenAI 客户端
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    async def process_translation(
        self,
        file_content: bytes,
        original_filename: str,
        source_language: str = "auto",
        target_language: str = "zh",
        model: str = None,
        progress_callback: Optional[Callable] = None,
        db: AsyncSession = None,
    ) -> AsyncIterator[Union[TranslationProgressUpdate, str]]:
        """
        处理翻译工作流

        Args:
            file_content: 文件内容（字节）
            original_filename: 原始文件名
            source_language: 源语言
            target_language: 目标语言
            model: 翻译模型
            progress_callback: 进度回调函数
            db: 数据库会话

        Yields:
            TranslationProgressUpdate: 进度更新
        """
        try:
            if model:
                self.model = model

            # 1. 文档提取阶段
            yield TranslationProgressUpdate(
                stage=TranslationStage.DOCUMENT_EXTRACTION,
                stage_name="doc_extraction",
                progress=5.0,
                message="正在提取文档内容...",
            )

            original_text = await self._extract_text_from_document(
                file_content,
                original_filename
            )

            text_length = len(original_text)
            logger.info(f"[翻译工作流] 文本提取完成，长度: {text_length} 字符")

            # 2. 文本分析阶段
            yield TranslationProgressUpdate(
                stage=TranslationStage.TEXT_ANALYSIS,
                stage_name="text_analysis",
                progress=15.0,
                message=f"文本分析完成，共 {text_length} 个字符",
                data={"text_length": text_length}
            )

            # 3. 翻译处理阶段
            yield TranslationProgressUpdate(
                stage=TranslationStage.TRANSLATING,
                stage_name="translating",
                progress=20.0,
                message="开始翻译处理...",
            )

            # 根据文本长度决定翻译策略
            # 新策略：逐段翻译，确保每个段落都被处理
            # 先分割成单独的段落，然后逐个翻译

            paragraphs_list = self._split_into_paragraphs(original_text)
            total_paragraphs = len(paragraphs_list)

            logger.info(f"[翻译工作流] 文档共 {total_paragraphs} 个段落，采用逐段翻译策略")

            yield TranslationProgressUpdate(
                stage=TranslationStage.CHUNK_PROCESSING,
                stage_name="chunk_processing",
                progress=5.0,
                message=f"开始逐段翻译，共 {total_paragraphs} 个段落",
                data={"total_paragraphs": total_paragraphs}
            )

            translated_paragraphs = []

            # 逐段翻译
            for i, paragraph in enumerate(paragraphs_list, 1):
                para_progress = 5.0 + (i / total_paragraphs) * 90.0  # 5% - 95%

                # 发送段落开始消息
                yield TranslationProgressUpdate(
                    stage=TranslationStage.CHUNK_PROCESSING,
                    stage_name="chunk_processing",
                    progress=para_progress,
                    message=f"正在翻译第 {i}/{total_paragraphs} 段...",
                    data={"current_paragraph": i, "total_paragraphs": total_paragraphs, "paragraph_preview": paragraph[:100]}
                )

                try:
                    # 翻译单个段落
                    translated_para = await self._translate_single_paragraph(
                        paragraph,
                        paragraph_number=i
                    )
                    translated_paragraphs.append(translated_para)
                    logger.info(f"[翻译工作流] 第 {i}/{total_paragraphs} 段翻译完成")

                    # 实时发送已翻译的段落
                    yield TranslationProgressUpdate(
                        stage=TranslationStage.CHUNK_PROCESSING,
                        stage_name="chunk_processing",
                        progress=para_progress,
                        message=f"第 {i}/{total_paragraphs} 段翻译完成",
                        data={"translated_paragraph": translated_para, "paragraph_number": i}
                    )

                except Exception as e:
                    logger.error(f"[翻译工作流] 第 {i}/{total_paragraphs} 段翻译失败: {e}")
                    # 失败时保留原文
                    translated_paragraphs.append(f"\n\n[翻译失败：第 {i} 段]\n\n{paragraph}\n\n")

            # 合并所有段落
            translated_text = "\n\n".join(translated_paragraphs)

            yield TranslationProgressUpdate(
                stage=TranslationStage.CHUNK_PROCESSING,
                stage_name="chunk_processing",
                progress=98.0,
                message="所有段落翻译完成，正在整合...",
            )

            # 4. 完成阶段
            logger.info(f"[翻译工作流] 翻译完成，总长度: {len(translated_text)} 字符")

            yield TranslationProgressUpdate(
                stage=TranslationStage.COMPLETED,
                stage_name="completed",
                progress=100.0,
                message="翻译完成！",
                data={
                    "original_text": original_text,
                    "translated_text": translated_text,
                    "original_length": text_length,
                    "translated_length": len(translated_text),
                }
            )

            # 发送结束信号
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"[翻译工作流] 处理失败: {e}")
            yield TranslationProgressUpdate(
                stage=TranslationStage.FAILED,
                stage_name="failed",
                progress=-1,
                message=f"翻译失败: {str(e)}",
                data={"error": str(e)}
            )
            # 发送结束信号
            yield "data: [DONE]\n\n"

    def _split_text_by_paragraphs(self, text: str, max_chars: int) -> List[str]:
        """按段落智能分割文本"""
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = ""
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_length = len(para)

            if para_length > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_length = 0
                sub_chunks = self._split_long_paragraph(para, max_chars)
                chunks.extend(sub_chunks)
                continue

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

        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.info(f"[翻译工作流] 文本已分割为 {len(chunks)} 个块")
        return chunks

    def _split_long_paragraph(self, paragraph: str, max_chars: int) -> List[str]:
        """分割过长的段落"""
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', paragraph)

        chunks = []
        current_chunk = ""
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence)

            if sentence_length > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i:i + max_chars])
                current_chunk = ""
                current_length = 0
                continue

            if current_length + sentence_length + 1 <= max_chars:
                if current_chunk:
                    current_chunk += " " + sentence
                    current_length += sentence_length + 1
                else:
                    current_chunk = sentence
                    current_length = sentence_length
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_length = sentence_length

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    async def _extract_text_from_document(
        self,
        document_bytes: bytes,
        filename: str,
    ) -> str:
        """
        从文档中提取文本（使用 PyMuPDF）

        Args:
            document_bytes: 文档字节内容
            filename: 文件名

        Returns:
            提取并清理后的 Markdown 文本
        """
        # 使用 PyMuPDF (fitz) 提取 PDF
        if fitz_extractor is None:
            raise EnvironmentError(
                "PyMuPDF 不可用，请先安装 PyMuPDF:\n"
                "运行: pip install PyMuPDF"
            )

        # 调用 PyMuPDF 提取 PDF 为 Markdown
        extraction_result = fitz_extractor.extract_from_bytes(
            document_bytes,
            extract_images=False,
            extract_tables=True
        )

        markdown_content = extraction_result["content"]

        # 清理内容：移除参考文献部分
        cleaned_content = self._clean_markdown_content(markdown_content)

        logger.info(f"[PyMuPDF] 文档提取完成，原文长度: {len(markdown_content)}, 清理后长度: {len(cleaned_content)}")

        return cleaned_content

    def _clean_markdown_content(self, markdown: str) -> str:
        """
        清理 Markdown 内容

        处理规则：
        1. 移除参考文献部分
        2. 移除目录部分
        3. 移除页眉页脚残留
        4. 保留表格和正文

        Args:
            markdown: 原始 Markdown 内容

        Returns:
            清理后的 Markdown 内容
        """
        lines = markdown.split('\n')
        cleaned_lines = []
        in_references = False
        skip_next = False

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # 空行保留
            if not line_stripped:
                cleaned_lines.append(line)
                continue

            # 检测参考文献部分开始
            if self._is_references_start(line_stripped):
                logger.info(f"[PyMuPDF] 检测到参考文献开始位置（第 {i+1} 行）")
                in_references = True
                break

            # 跳过目录
            if line_stripped.startswith("## Contents") or line_stripped.startswith("## 目录"):
                in_references = True
                continue

            # 跳过页眉页脚（启发式规则）
            if self._is_header_footer(line_stripped):
                continue

            # 保留正文内容
            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _is_references_start(self, line: str) -> bool:
        """检测是否是参考文献开始位置"""
        line_lower = line.lower()
        references_keywords = [
            "references",
            "参考文献",
            "bibliography",
            "参考书目"
        ]
        return any(keyword in line_lower for keyword in references_keywords)

    def _is_header_footer(self, line: str) -> bool:
        """检测是否是页眉或页脚"""
        # 规则1：包含@符号（邮箱）
        if "@" in line:
            return True

        # 规则2：短文本且包含特定关键词
        short_keywords = ["imf", "world bank", "working paper", "wp/", "sip/"]
        if len(line) < 50 and any(kw in line.lower() for kw in short_keywords):
            return True

        # 规则3：纯数字或日期格式
        if line.strip().isdigit() or len(line.strip()) <= 4:
            return True

        # 规则4：包含大量符号的页眉
        if len(line) < 80 and line.count('|') >= 3:
            return True

        return False

    async def _call_deepseek_api(self, text: str, use_full_prompt: bool = True):
        """调用 DeepSeek API 进行文本翻译（流式输出）

        Yields:
            str: 翻译的内容片段
        """
        try:
            if use_full_prompt:
                prompt = self.TRANSLATION_PROMPT.format(content=text)
            else:
                prompt = self.CHUNK_TRANSLATION_PROMPT.format(content=text)

            logger.info(f"[翻译工作流] 正在调用 DeepSeek API，模型: {self.model}，文本长度: {len(text)}")

            # 计算需要的最大token数
            # API 限制：max_tokens <= 163840
            # 中英对照翻译大约需要输入字符数的 2 倍 token
            # 为了安全，设置为 输入字符数 * 2.0，且不超过 150000
            input_chars = len(text)
            estimated_max_tokens = min(150000, max(8000, int(input_chars * 2.0)))

            logger.info(f"[翻译工作流] 输入字符数: {input_chars}, 设置max_tokens: {estimated_max_tokens}")

            # 使用流式API
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=estimated_max_tokens,
                timeout=300.0,
                stream=True  # ✅ 启用流式输出
            )

            logger.info(f"[翻译工作流] DeepSeek API 流式调用开始")

            # 收集完整响应用于返回
            full_content = []

            # 实时流式处理
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        content_piece = delta.content
                        full_content.append(content_piece)
                        # 实时yield内容片段
                        yield content_piece

            # 流式接收完成
            complete_content = "".join(full_content)
            logger.info(f"[翻译工作流] 流式接收完成，总长度: {len(complete_content)}")
            # 注意：在async generator中不能return值，调用者需要自行收集

        except Exception as e:
            logger.error(f"[翻译工作流] DeepSeek API 调用失败: {e}")
            raise

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """将文本分割成单独的段落

        按照以下规则分割：
        1. 空行分割
        2. 识别标题（## 开头）
        3. 保留段落完整性

        Returns:
            List[str]: 段落列表
        """
        # 按空行分割
        raw_paragraphs = text.split('\n\n')

        paragraphs = []
        for para in raw_paragraphs:
            para = para.strip()
            if not para:
                continue

            # 检查是否是标题（Markdown格式）
            if para.startswith('##'):
                # 标题单独作为一段
                paragraphs.append(para)
            else:
                # 普通段落
                paragraphs.append(para)

        logger.info(f"[翻译工作流] 文本分割为 {len(paragraphs)} 个段落")
        return paragraphs

    async def _translate_single_paragraph(self, paragraph: str, paragraph_number: int) -> str:
        """翻译单个段落

        Args:
            paragraph: 待翻译的段落
            paragraph_number: 段落编号

        Returns:
            str: 翻译后的段落（中英对照格式）
        """
        # 构建单段翻译提示词
        prompt = f"""请将以下段落翻译为简体中文，严格按照中英对照格式输出：

【段落编号】{paragraph_number}

**中文译文**：（在此输出中文翻译）

**英文原文**：
{paragraph}

---

【严格要求】
• 必须翻译完整段落，不要省略任何内容
• 不要输出"后续内容"、"此处仅展示"等说明文字
• 保持原文的格式和标点
• 直接输出，不要用代码块包裹
"""

        try:
            # 调用API（不使用流式，单段翻译速度更快）
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=8000,  # 单段翻译不需要太多tokens
                timeout=60.0,
                stream=False  # 单段翻译使用非流式，更稳定
            )

            if completion.choices and len(completion.choices) > 0:
                message = completion.choices[0].message
                if message.content:
                    return message.content.strip()

            raise ValueError("API did not return expected content")

        except Exception as e:
            logger.error(f"[翻译工作流] 第 {paragraph_number} 段翻译失败: {e}")
            raise


# 单例实例
translation_workflow_service = TranslationWorkflowService()
