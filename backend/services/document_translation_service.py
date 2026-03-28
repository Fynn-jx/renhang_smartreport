"""
公文翻译服务
调用 DeepSeek-V3 模型进行文档文本翻译
支持智能段落切割，处理大文档
"""

import uuid
import io
import re
from pathlib import Path
from typing import Optional, Tuple, List

from openai import AsyncOpenAI
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import DocumentTranslation, DocumentTranslationStatus
from core.config import settings
from services.file_service import file_service

try:
    from services.fitz_extractor import fitz_extractor
    FITZ_AVAILABLE = True
except Exception:
    FITZ_AVAILABLE = False
    logger.warning("[WARNING] PyMuPDF 提取器不可用，请运行: pip install PyMuPDF")


class DocumentTranslationService:
    """
    公文翻译服务
    """

    # 模型上下文限制（DeepSeek-V3 支持较长上下文）
    # 保守估计：输入 + 输出不超过 64000 tokens
    MAX_INPUT_TOKENS = 50000
    MAX_OUTPUT_TOKENS = 14000

    # 每个字符大约对应多少 token（英文约 0.25，中文约 0.5，取保守值）
    CHARS_TO_TOKEN_RATIO = 0.4

    # 每块文本的最大字符数（保守估计）
    MAX_CHARS_PER_CHUNK = int(MAX_INPUT_TOKENS / CHARS_TO_TOKEN_RATIO)  # 约 125000 字符

    # 翻译提示词模板（Markdown���式输出）
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

【重要禁令】

• 直接输出Markdown内容，不要用 ``` 包裹

• 不要输出开场白、说明或注释

【原文内容】
{content}"""

    # 分批翻译时的简化提示词（不需要重复说明格式）
    CHUNK_TRANSLATION_PROMPT = """请将以下文本翻译为简体中文。每个段落按以下格式输出：

**中文译文**：中文翻译内容

**英文原文**：English original content

---

直接输出Markdown格式，不要用代码块包裹。

【原文内容】
{content}"""

    def __init__(self):
        self.api_key = settings.SILICONFLOW_API_KEY
        self.base_url = settings.SILICONFLOW_BASE_URL
        self.model = settings.DEEPSEEK_MODEL
        # 创建 OpenAI 客户端（用于调用 SiliconFlow）
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    async def create_translation_task(
        self,
        original_filename: str,
        document_content: bytes,
        owner_id: str,
        db: AsyncSession,
        source_language: str = "auto",
        target_language: str = "zh",
    ) -> DocumentTranslation:
        """
        创建公文翻译任务

        Args:
            original_filename: 原始文件名
            document_content: 文档内容（字节）
            owner_id: 所有者 ID
            db: 数据库会话
            source_language: 源语言
            target_language: 目标语言

        Returns:
            创建的翻译任务对象
        """
        try:
            # 1. 保存原文档
            original_path, file_hash, file_size = await file_service.save_file(
                file_content=document_content,
                original_filename=original_filename,
                document_type="document",
            )

            # 2. 创建翻译任务记录
            translation = DocumentTranslation(
                original_filename=original_filename,
                original_document_path=original_path,
                status=DocumentTranslationStatus.PENDING.value,
                file_size=len(document_content),
                mime_type=self._get_mime_type(original_filename),
                owner_id=owner_id,
                source_language=source_language,
                target_language=target_language,
            )

            db.add(translation)
            await db.commit()
            await db.refresh(translation)

            logger.info(f"[OK] 公文翻译任务创建成功: {translation.id}")
            return translation

        except Exception as e:
            logger.error(f"[ERROR] 创建公文翻译任务失败: {e}")
            await db.rollback()
            raise

    async def process_translation(
        self,
        translation_id: str,
        db: AsyncSession,
    ) -> DocumentTranslation:
        """
        处理公文翻译（需要传入数据库会话）

        Args:
            translation_id: 翻译任务 ID
            db: 数据库会话

        Returns:
            更新后的翻译任务对象
        """
        return await self._process_translation_impl(translation_id, db)

    async def process_translation_background(
        self,
        translation_id: str,
    ) -> DocumentTranslation:
        """
        后台处理公文翻译（自动创建独立的数据库会话）

        注意：此方法用于后台任务，会创建独立的数据库会话

        Args:
            translation_id: 翻译任务 ID

        Returns:
            更新后的翻译任务对象
        """
        from core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            try:
                result = await self._process_translation_impl(translation_id, db)
                return result
            except Exception as e:
                logger.error(f"[ERROR] 后台翻译任务失败: {e}")
                raise

    async def _process_translation_impl(
        self,
        translation_id: str,
        db: AsyncSession,
    ) -> DocumentTranslation:
        """
        处理公文翻译

        Args:
            translation_id: 翻译任务 ID
            db: 数据库会话

        Returns:
            更新后的翻译任务对象
        """
        translation = None
        try:
            # 1. 获取翻译任务
            result = await db.execute(
                select(DocumentTranslation).where(DocumentTranslation.id == translation_id)
            )
            translation = result.scalar_one_or_none()

            if not translation:
                raise ValueError(f"翻译任务不存在: {translation_id}")

            # 2. 更新状态为处理中
            translation.status = DocumentTranslationStatus.PROCESSING.value
            await db.commit()

            # 3. 读取原文档并提取文本
            full_path = file_service.get_full_path(translation.original_document_path)

            if not full_path.exists():
                # 如果路径不存在，尝试其他可能的路径
                import os
                base_dir = Path(os.getcwd())
                alt_paths = [
                    base_dir / translation.original_document_path,
                    base_dir / 'storage' / translation.original_document_path,
                    Path('storage') / translation.original_document_path,
                ]
                for alt_path in alt_paths:
                    if alt_path.exists():
                        full_path = alt_path
                        break
                else:
                    raise FileNotFoundError(f"原文档文件不存在: {translation.original_document_path}")

            with open(full_path, "rb") as f:
                document_bytes = f.read()

            # 4. 提取文本
            original_text = await self._extract_text_from_document(
                document_bytes,
                translation.original_filename
            )
            translation.original_text = original_text
            await db.commit()

            logger.info(f"[INFO] 文本提取完成，长度: {len(original_text)} 字符")

            # 5. 根据文本长度决定翻译策略
            if len(original_text) <= self.MAX_CHARS_PER_CHUNK:
                # 小文档，直接翻译
                logger.info(f"[INFO] 小文档，直接翻译")
                translated_text = await self._call_deepseek_api(original_text, use_full_prompt=True)
            else:
                # 大文档，分块翻译
                logger.info(f"[INFO] 大文档，启用分块翻译")
                translated_text = await self._translate_large_document(original_text)

            # 6. 保存翻译结果
            translation.translated_text = translated_text
            translation.status = DocumentTranslationStatus.COMPLETED.value
            await db.commit()
            await db.refresh(translation)

            logger.info(f"[OK] 公文翻译完成: {translation.id}")
            return translation

        except Exception as e:
            logger.error(f"[ERROR] 公文翻译失败: {e}")

            # 更新为失败状态
            if translation:
                translation.status = DocumentTranslationStatus.FAILED.value
                translation.error_message = str(e)
                await db.commit()

            raise

    def _split_text_by_paragraphs(self, text: str, max_chars: int = None) -> List[str]:
        """
        按段落智能分割文本，保持语义完整性

        Args:
            text: 待分割的文本
            max_chars: 每块的最大字符数

        Returns:
            分割后的文本块列表
        """
        if max_chars is None:
            max_chars = self.MAX_CHARS_PER_CHUNK

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

                # 对超长段落进行句子级分割
                sub_chunks = self._split_long_paragraph(para, max_chars)
                chunks.extend(sub_chunks)
                continue

            # 检查添加此段落后是否会超出限制
            if current_length + para_length + 2 <= max_chars:  # +2 是为了两个换行符
                # 可以加入当前块
                if current_chunk:
                    current_chunk += "\n\n" + para
                    current_length += para_length + 2
                else:
                    current_chunk = para
                    current_length = para_length
            else:
                # 不能加入，保存当前块，开始新块
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
                current_length = para_length

        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.info(f"[INFO] 文本已分割为 {len(chunks)} 个块")
        return chunks

    def _split_long_paragraph(self, paragraph: str, max_chars: int) -> List[str]:
        """
        分割过长的段落（按句子分割）

        Args:
            paragraph: 过长的段落
            max_chars: 每块的最大字符数

        Returns:
            分割后的文本块列表
        """
        # 按句子分割（句号、问号、感叹号后跟空格或换行）
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', paragraph)

        chunks = []
        current_chunk = ""
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence)

            # 如果单个句子就超过限制，强制按字符分割（极少情况）
            if sentence_length > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # 按字符强制分割
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i:i + max_chars])
                current_chunk = ""
                current_length = 0
                continue

            if current_length + sentence_length + 1 <= max_chars:  # +1 是为了空格
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

    async def _translate_large_document(self, text: str) -> str:
        """
        翻译大文档（分块处理）

        Args:
            text: 待翻译的文本

        Returns:
            翻译后的完整文本
        """
        # 分割文本
        chunks = self._split_text_by_paragraphs(text)
        total_chunks = len(chunks)

        logger.info(f"[INFO] 开始分块翻译，共 {total_chunks} 块")

        translated_chunks = []

        for i, chunk in enumerate(chunks, 1):
            logger.info(f"[INFO] 正在翻译第 {i}/{total_chunks} 块，字符数: {len(chunk)}")

            # 第一块使用完整提示词，后续块使用简化提示词
            use_full_prompt = (i == 1)

            try:
                translated_chunk = await self._call_deepseek_api(
                    chunk,
                    use_full_prompt=use_full_prompt
                )
                translated_chunks.append(translated_chunk)
                logger.info(f"[INFO] 第 {i}/{total_chunks} 块翻译完成")
            except Exception as e:
                logger.error(f"[ERROR] 第 {i}/{total_chunks} 块翻译失败: {e}")
                # 可以选择跳过或重试，这里选择跳过并标记
                translated_chunks.append(f"\n\n[翻译错误：第 {i} 块翻译失败]\n\n")

        # 合并所有翻译块
        result = "\n\n".join(translated_chunks)
        logger.info(f"[INFO] 所有块翻译完成，总长度: {len(result)} 字符")

        return result

    async def _extract_text_from_document(
        self,
        document_bytes: bytes,
        filename: str,
    ) -> str:
        """
        从文档中提取文本

        Args:
            document_bytes: 文档字节
            filename: 文件名

        Returns:
            提取的文本内容
        """
        file_ext = Path(filename).suffix.lower()

        if file_ext == ".pdf":
            if not FITZ_AVAILABLE:
                raise EnvironmentError(
                    "PyMuPDF 不可用，请先安装 PyMuPDF:\n"
                    "运行: pip install PyMuPDF"
                )

            # 使用 PyMuPDF 提取 PDF
            result = fitz_extractor.extract_from_bytes(document_bytes, filename)
            return result.get("content", "")

        elif file_ext in {".txt", ".md"}:
            # 纯文本文件直接读取
            return document_bytes.decode("utf-8", errors="ignore")

        elif file_ext in {".doc", ".docx"}:
            # TODO: 支持 Word 文档
            raise ValueError("Word 文档暂不支持，请转换为 PDF 或 TXT 格式")

        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")

    async def _call_deepseek_api(self, text: str, use_full_prompt: bool = True) -> str:
        """
        调用 DeepSeek API 进行文本翻译

        Args:
            text: 待翻译的文本
            use_full_prompt: 是否使用完整提示词（第一块使用完整版，后续块使用简化版）

        Returns:
            翻译后的文本
        """
        try:
            # 选择提示词
            if use_full_prompt:
                prompt = self.TRANSLATION_PROMPT.format(content=text)
            else:
                prompt = self.CHUNK_TRANSLATION_PROMPT.format(content=text)

            logger.info(f"[INFO] 正在调用 DeepSeek API，模型: {self.model}，文本长度: {len(text)}")

            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                timeout=300.0
            )

            logger.info(f"[INFO] DeepSeek API 调用成功")

            # 解析响应
            if completion.choices and len(completion.choices) > 0:
                message = completion.choices[0].message
                if message.content:
                    return message.content

            raise ValueError("API did not return expected content")

        except Exception as e:
            logger.error(f"[ERROR] DeepSeek API 调用失败: {e}")
            raise

    def _get_mime_type(self, filename: str) -> str:
        """
        根据文件名获取 MIME 类型

        Args:
            filename: 文件名

        Returns:
            MIME 类型字符串
        """
        ext = Path(filename).suffix.lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return mime_types.get(ext, "application/octet-stream")


# 单例实例
document_translation_service = DocumentTranslationService()
