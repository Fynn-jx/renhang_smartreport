"""
Markdown 转 Word 工具
将翻译结果的 Markdown 格式转换为 Word 文档
"""

import re
import io
from typing import List, Tuple
from loguru import logger

try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
    from docx.oxml.ns import qn
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("[WARNING] python-docx 未安装，Word 导出功能将不可用")


class MarkdownToWordConverter:
    """
    Markdown 转 Word 转换器
    ��门用于处理公文翻译的对照格式
    """

    def __init__(self):
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx 未安装，请运行: pip install python-docx")

    def convert(self, markdown_text: str) -> bytes:
        """
        将 Markdown 文本转换为 Word 文档字节流

        Args:
            markdown_text: Markdown 格式的文本

        Returns:
            Word 文档的字节流
        """
        doc = Document()

        # 设置文档默认字体
        self._setup_document_styles(doc)

        # 解析 Markdown 并添加到文档
        blocks = self._parse_markdown_blocks(markdown_text)

        for block_type, content in blocks:
            self._add_block_to_doc(doc, block_type, content)

        # 保存到字节流
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output.read()

    def _setup_document_styles(self, doc: Document):
        """
        设置文档样式

        Args:
            doc: Word 文档对象
        """
        # 设置默认字体
        style = doc.styles['Normal']
        font = style.font
        font.name = '宋体'
        font.size = Pt(10.5)
        font.color.rgb = RGBColor(0, 0, 0)

        # 设置中文字体
        style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

        # 设置段落间距
        paragraph_format = style.paragraph_format
        paragraph_format.line_spacing = 1.5
        paragraph_format.space_before = Pt(6)
        paragraph_format.space_after = Pt(6)

    def _parse_markdown_blocks(self, markdown_text: str) -> List[Tuple[str, str]]:
        """
        解析 Markdown 文本为块列表

        Args:
            markdown_text: Markdown 文本

        Returns:
            (块类型, 内容) 的列表
            块类型: 'heading', 'chinese', 'english', 'separator'
        """
        blocks = []
        lines = markdown_text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 跳过空行
            if not line:
                i += 1
                continue

            # 标题 (# ## ###)
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title_text = line.lstrip('#').strip()
                blocks.append(('heading', f"{level}|{title_text}"))
                i += 1
                continue

            # 分隔线 (---)
            if line.startswith('---') or line.startswith('***'):
                blocks.append(('separator', ''))
                i += 1
                continue

            # 中文译文标记
            if line.startswith('**中文译文**') or line.startswith('**译文**'):
                # 提取冒号后的内容
                if ':' in line or '：' in line:
                    content_start = max(line.find(':'), line.find('：')) + 1
                    content = line[content_start:].strip()
                    if content:
                        blocks.append(('chinese', content))
                    else:
                        # 内容在下一行
                        i += 1
                        if i < len(lines):
                            blocks.append(('chinese', lines[i].strip()))
                i += 1
                continue

            # 英文原文标记
            if line.startswith('**英文原文**') or line.startswith('**原文**'):
                # 提取冒号后的内容
                if ':' in line or '：' in line:
                    content_start = max(line.find(':'), line.find('：')) + 1
                    content = line[content_start:].strip()
                    if content:
                        blocks.append(('english', content))
                    else:
                        # 内容在下一行
                        i += 1
                        if i < len(lines):
                            blocks.append(('english', lines[i].strip()))
                i += 1
                continue

            # 普通文本段落（可能是中英文对照的延续）
            # 判断是否为中文或英文
            if self._is_chinese_text(line):
                blocks.append(('chinese', line))
            else:
                blocks.append(('english', line))

            i += 1

        return blocks

    def _is_chinese_text(self, text: str) -> bool:
        """
        判断文本是否主要为中文

        Args:
            text: 待判断的文本

        Returns:
            是否为中文
        """
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(re.findall(r'[^\s]', text))
        if total_chars == 0:
            return False
        return chinese_chars / total_chars > 0.3

    def _add_block_to_doc(self, doc: Document, block_type: str, content: str):
        """
        将块添加到 Word 文档

        Args:
            doc: Word 文档对象
            block_type: 块类型
            content: 块内容
        """
        if block_type == 'separator':
            # 添加分隔线
            paragraph = doc.add_paragraph()
            paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            run = paragraph.add_run('─' * 30)
            run.font.color.rgb = RGBColor(128, 128, 128)

        elif block_type == 'heading':
            # 添加标题
            level, title = content.split('|', 1)
            level = min(int(level), 3)  # 最多3级

            heading_map = {1: 'Heading 1', 2: 'Heading 2', 3: 'Heading 3'}
            doc.add_heading(title, level=level)

        elif block_type == 'chinese':
            # 添加中文译文
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(f"【译文】{content}")
            run.font.name = '宋体'
            run.font.size = Pt(10.5)
            run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
            run.font.bold = False

        elif block_type == 'english':
            # 添加英文原文
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(f"【原文】{content}")
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(80, 80, 80)
            run.font.italic = True

    def convert_bilingual(self, markdown_text: str) -> bytes:
        """
        转换双语文档（更精美的格式）

        Args:
            markdown_text: Markdown 文本

        Returns:
            Word 文档字节流
        """
        doc = Document()

        # 设置文档属性
        core_props = doc.core_properties
        core_props.title = "公文翻译"
        core_props.comments = "由 AI 公文翻译系统生成"

        # 设置默认字体
        self._setup_document_styles(doc)

        # 添加标题
        title = doc.add_heading('公文翻译结果', level=1)
        title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # 解析并添加内容
        blocks = self._parse_markdown_blocks(markdown_text)

        # 逐块处理
        current_chinese = []
        current_english = []

        for block_type, content in blocks:
            if block_type == 'separator':
                # 遇到分隔符，输出当前累积的内容
                if current_chinese or current_english:
                    self._add_bilingual_block(doc, current_chinese, current_english)
                    current_chinese = []
                    current_english = []
                # 添加空行
                doc.add_paragraph()

            elif block_type == 'heading':
                # 先输出之前累积的内容
                if current_chinese or current_english:
                    self._add_bilingual_block(doc, current_chinese, current_english)
                    current_chinese = []
                    current_english = []
                # 添加标题
                level, title = content.split('|', 1)
                doc.add_heading(title, level=min(int(level), 2))

            elif block_type == 'chinese':
                current_chinese.append(content)

            elif block_type == 'english':
                current_english.append(content)

        # 输出最后的内容
        if current_chinese or current_english:
            self._add_bilingual_block(doc, current_chinese, current_english)

        # 保存到字节流
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output.read()

    def _add_bilingual_block(self, doc: Document, chinese_lines: List[str], english_lines: List[str]):
        """
        添加双语文本块

        Args:
            doc: Word 文档对象
            chinese_lines: 中文行列表
            english_lines: 英文行列表
        """
        # 中文段落
        if chinese_lines:
            para = doc.add_paragraph()
            run = para.add_run(''.join(chinese_lines))
            run.font.name = '宋体'
            run.font.size = Pt(10.5)
            run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

        # 英文段落
        if english_lines:
            para = doc.add_paragraph()
            run = para.add_run(''.join(english_lines))
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(100, 100, 100)
            run.font.italic = True


# 单例实例
markdown_to_word_converter = MarkdownToWordConverter() if DOCX_AVAILABLE else None


def convert_markdown_to_word(markdown_text: str, use_bilingual_format: bool = True) -> bytes:
    """
    将 Markdown 文本转换为 Word 文档

    Args:
        markdown_text: Markdown 格式的文本
        use_bilingual_format: 是否使用双语对照格式

    Returns:
        Word 文档的字节流
    """
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx 未安装，请运行: pip install python-docx")

    converter = MarkdownToWordConverter()

    if use_bilingual_format:
        return converter.convert_bilingual(markdown_text)
    else:
        return converter.convert(markdown_text)
