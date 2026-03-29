"""
PyMuPDF (fitz) PDF 提取器
高性能 PDF 处理，支持文本、图片、表格提取
"""

import io
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    logger.warning("[WARNING] PyMuPDF 未安装，PDF 提取功能将不可用")
    logger.info("[INFO] 安装方法: pip install PyMuPDF")


class FitzExtractor:
    """
    基于 PyMuPDF 的 PDF 提取器

    功能：
    - 提取文本内容（保留结构）
    - 提取图片
    - 提取表格（检测表格结构）
    - 提取元数据
    - 生成 Markdown 输出
    """

    def __init__(self):
        """初始化 PDF 提取器"""
        if not FITZ_AVAILABLE:
            raise ImportError(
                "PyMuPDF 未安装。\n"
                "请运行: pip install PyMuPDF\n"
                "或: pip install pymupdf"
            )

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

    def extract_from_bytes(
        self,
        pdf_bytes: bytes,
        extract_images: bool = False,
        extract_tables: bool = True
    ) -> Dict[str, Any]:
        """
        从字节内容提取 PDF 内容

        Args:
            pdf_bytes: PDF 文件的字节内容
            extract_images: 是否提取图片
            extract_tables: 是否检测表格

        Returns:
            包含以下键的字典：
            - content: Markdown 格式内容
            - page_count: 页数
            - metadata: PDF 元数据
            - author: 作者
            - title: 标题
            - subject: 主题
            - images: 图片数量（如果 extract_images=True）
            - tables: 表格数量（如果 extract_tables=True）
        """
        try:
            # 打开 PDF 文档
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

            # 提取元数据
            metadata = pdf_document.metadata
            info = {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
            }

            # 获取页数（pdf_document.page_count 是属性，不是方法）
            page_count = pdf_document.page_count

            # 提取内容并转换为 Markdown
            markdown_parts = []
            total_images = 0
            total_tables = 0

            for page_num in range(page_count):
                try:
                    page = pdf_document[page_num]

                    # 直接提取文本（最简单可靠的方法）
                    text = page.get_text().strip()

                    if text:
                        markdown_parts.append(text)

                    # 统计图片
                    if extract_images:
                        try:
                            images = page.get_images()
                            if images:
                                total_images += len(images)
                        except Exception as e:
                            logger.debug(f"[DEBUG] 获取图片列表失败（可忽略）: {e}")

                    # 检测表格（简单检测：多列文本）
                    if extract_tables:
                        if self._detect_table(text):
                            total_tables += 1
                            # 可以选择使用更复杂的表格提取
                            # tables = page.find_tables()

                    # 页面之间添加分隔
                    if page_num < page_count - 1:
                        markdown_parts.append("\n\n---\n\n")

                except Exception as e:
                    logger.warning(f"[WARNING] 提取第 {page_num} 页失败: {e}")

            # 合并所有页面的内容
            content = "\n".join(markdown_parts)

            # 清理内容
            content = self._clean_content(content)

            result = {
                "content": content,
                "page_count": page_count,
                "metadata": info,
                "author": info.get("author"),
                "title": info.get("title"),
                "subject": info.get("subject"),
                "paragraphs": len([p for p in content.split("\n\n") if p.strip()]),
            }

            if extract_images:
                result["images"] = total_images

            if extract_tables:
                result["tables"] = total_tables

            logger.info(
                f"[OK] PDF 提取成功: {result['page_count']} 页, "
                f"{result.get('paragraphs', 0)} 个段落"
            )

            return result

        except Exception as e:
            logger.error(f"[ERROR] PDF 提取失败: {e}")
            raise

    def _detect_table(self, text: str) -> bool:
        """
        简单的表格检测

        Args:
            text: 页面文本

        Returns:
            是否可能包含表格
        """
        # 简单启发式：如果有多列对齐的文本，可能是表格
        lines = text.split("\n")
        if len(lines) < 3:
            return False

        # 检查是否有连续的行包含多个空白分隔的字段
        table_like_lines = 0
        for line in lines[:10]:  # 检查前10行
            if len(line.split()) >= 3:  # 至少3个字段
                table_like_lines += 1

        return table_like_lines >= 3

    def _clean_content(self, content: str) -> str:
        """
        清理提取的内容

        Args:
            content: 原始内容

        Returns:
            清理后的内容
        """
        # 移除过多的空行
        import re
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 移除行首行尾空格
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(lines)

        return content.strip()

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

    def extract_tables_advanced(self, file_path: str) -> list:
        """
        高级表格提取（需要安装 camelot 或 tabula-py）

        Args:
            file_path: PDF 文件路径

        Returns:
            表格列表
        """
        try:
            # 尝试使用 PyMuPDF 的表格检测
            import fitz
            doc = fitz.open(file_path)
            tables = []

            for page in doc:
                tables_found = page.find_tables()
                if tables_found.tables:
                    tables.extend(tables_found.tables)

            return tables
        except Exception as e:
            logger.warning(f"[WARNING] 高级表格提取失败: {e}")
            return []

    def extract_images(self, pdf_bytes: bytes, output_dir: Optional[str] = None) -> list:
        """
        提取 PDF 中的图片

        Args:
            pdf_bytes: PDF 字节内容
            output_dir: 输出目录（可选）

        Returns:
            图片信息列表
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            images = []

            for page_num, page in enumerate(doc):
                image_list = page.get_images()
                for img_index, img in enumerate(image_list, 1):
                    xref = img[0]
                    base_image = doc.extract_image(xref)

                    if base_image:
                        image_info = {
                            "page": page_num + 1,
                            "index": img_index,
                            "xref": xref,
                            "width": base_image["width"],
                            "height": base_image["height"],
                            "format": base_image["ext"],
                        }

                        # 如果指定了输出目录，保存图片
                        if output_dir:
                            import os
                            os.makedirs(output_dir, exist_ok=True)
                            image_path = os.path.join(
                                output_dir,
                                f"page_{page_num + 1}_img_{img_index}.{base_image['ext']}"
                            )
                            with open(image_path, "wb") as f:
                                f.write(base_image["image"])
                            image_info["path"] = image_path

                        images.append(image_info)

            return images
        except Exception as e:
            logger.error(f"[ERROR] 图片提取失败: {e}")
            return []


# 单例实例
fitz_extractor = FitzExtractor() if FITZ_AVAILABLE else None
