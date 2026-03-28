"""
PDF 内容提取工具
支持从 PDF 文件中提取文本、元数据等信息
"""

import io
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("[WARNING] PyPDF2 未安装，PDF 提取功能将不可用")


class PDFExtractor:
    """
    PDF 内容提取器
    """

    def __init__(self):
        """初始化 PDF 提取器"""
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 未安装，请运行: pip install PyPDF2")

    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        从文件路径提取 PDF 内容

        Args:
            file_path: PDF 文件路径

        Returns:
            包含文本内容和元数据的字典
        """
        try:
            with open(file_path, "rb") as file:
                return self.extract_from_bytes(file.read())

        except Exception as e:
            logger.error(f"[ERROR] 从文件提取 PDF 失败: {e}")
            raise

    def extract_from_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        从字节内容提取 PDF 内容

        Args:
            pdf_bytes: PDF 文件的字节内容

        Returns:
            包含以下键的字典：
            - content: 提取的文本内容
            - page_count: 页数
            - metadata: PDF 元数据
            - author: 作者
            - title: 标题
            - subject: 主题
        """
        try:
            # 创建 PDF 对象
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # 提取元数据
            metadata = pdf_reader.metadata
            info = {}

            if metadata:
                info = {
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "creator": metadata.get("/Creator", ""),
                    "producer": metadata.get("/Producer", ""),
                    "creation_date": metadata.get("/CreationDate", ""),
                }

            # 提取文本内容
            content_parts = []
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        content_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"[WARNING] 提取第 {page_num} 页失败: {e}")

            # 合并所有页面的文本
            content = "\n\n".join(content_parts)

            result = {
                "content": content,
                "page_count": len(pdf_reader.pages),
                "metadata": info,
                "author": info.get("author"),
                "title": info.get("title"),
                "subject": info.get("subject"),
            }

            logger.info(f"[OK] PDF 提取成功: {result['page_count']} 页, {len(content)} 字符")
            return result

        except Exception as e:
            logger.error(f"[ERROR] PDF 提取失败: {e}")
            raise

    def extract_preview(self, content: str, max_length: int = 500) -> str:
        """
        提取内容预览

        Args:
            content: 完整内容
            max_length: 最大长度

        Returns:
            内容预览
        """
        if len(content) <= max_length:
            return content

        # 截取前 max_length 个字符
        preview = content[:max_length]

        # 确保在单词边界截断
        last_space = preview.rfind(" ")
        if last_space > max_length * 0.8:  # 如果最后一个空格在前 80% 位置
            preview = preview[:last_space]

        return preview + "..."

    def extract_keywords(self, content: str, top_n: int = 10) -> list[str]:
        """
        从内容中提取关键词

        Args:
            content: 文本内容
            top_n: 返回前 N 个关键词

        Returns:
            关键词列表
        """
        # TODO: 实现更复杂的关键词提取算法
        # 这里只是一个简单的实现

        # 简单的分词和词频统计
        import re
        from collections import Counter

        # 移除特殊字符，保留中英文和数字
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', content)

        # 统计词频
        word_freq = Counter(words)

        # 过滤掉低频词
        min_freq = 2
        filtered_words = {word: freq for word, freq in word_freq.items() if freq >= min_freq}

        # 排序并返回前 N 个
        top_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:top_n]

        return [word for word, freq in top_words]


# 单例实例
pdf_extractor = PDFExtractor() if PYPDF2_AVAILABLE else None
