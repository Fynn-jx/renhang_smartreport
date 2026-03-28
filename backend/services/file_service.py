"""
文件存储服务
处理文件的存储、检索和删除
"""

import os
import hashlib
import uuid
from pathlib import Path
from typing import Optional
from loguru import logger

from core.config import settings


class FileService:
    """
    文件存储服务
    """

    def __init__(self):
        """初始化文件服务"""
        self.storage_root = Path(settings.STORAGE_ROOT)
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.thumbnail_dir = Path(settings.THUMBNAIL_DIR)
        self.cache_dir = Path(settings.CACHE_DIR)

        # 创建必要的目录
        self._create_directories()

    def _create_directories(self):
        """创建存储目录"""
        for directory in [self.storage_root, self.upload_dir, self.thumbnail_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"[OK] 确保目录存在: {directory}")

    def get_file_hash(self, file_content: bytes) -> str:
        """
        计算文件的 SHA256 哈希值

        Args:
            file_content: 文件内容（字节）

        Returns:
            文件的 SHA256 哈希值（十六进制字符串）
        """
        return hashlib.sha256(file_content).hexdigest()

    def generate_file_path(
        self,
        original_filename: str,
        document_type: str,
        file_hash: Optional[str] = None,
    ) -> str:
        """
        生成文件存储路径

        Args:
            original_filename: 原始文件名
            document_type: 文档类型
            file_hash: 文件哈希（可选，用于去重）

        Returns:
            相对存储路径
        """
        # 获取文件扩展名
        ext = Path(original_filename).suffix

        # 生成唯一文件名
        if file_hash:
            # 使用哈希值去重
            filename = f"{file_hash}{ext}"
        else:
            # 使用 UUID
            filename = f"{uuid.uuid4()}{ext}"

        # ���文档类型分类存储
        type_dir = document_type.lower()
        if document_type == "markdown":
            type_dir = "docs"

        # 构建路径: uploads/{type}/{filename}
        relative_path = f"uploads/{type_dir}/{filename}"

        return relative_path

    async def save_file(
        self,
        file_content: bytes,
        original_filename: str,
        document_type: str,
    ) -> tuple[str, str, int]:
        """
        保存文件到磁盘

        Args:
            file_content: 文件内容（字节）
            original_filename: 原始文件名
            document_type: 文档类型

        Returns:
            (file_path, file_hash, file_size)
        """
        # 计算文件哈希和大小
        file_hash = self.get_file_hash(file_content)
        file_size = len(file_content)

        # 生成存储路径
        file_path = self.generate_file_path(original_filename, document_type, file_hash)

        # 完整路径
        full_path = self.storage_root / file_path

        try:
            # 确保目录存在
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(full_path, "wb") as f:
                f.write(file_content)

            logger.info(f"[OK] 文件保存成功: {file_path} ({file_size} bytes)")
            return file_path, file_hash, file_size

        except Exception as e:
            logger.error(f"[ERROR] 文件保存失败: {e}")
            raise

    def get_full_path(self, relative_path: str) -> Path:
        """
        获取文件的完整路径

        Args:
            relative_path: 相对路径

        Returns:
            完整路径（Path 对象）
        """
        return self.storage_root / relative_path

    def file_exists(self, relative_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            relative_path: 相对路径

        Returns:
            文件是否存在
        """
        full_path = self.get_full_path(relative_path)
        return full_path.exists() and full_path.is_file()

    def delete_file(self, relative_path: str) -> bool:
        """
        删除文件

        Args:
            relative_path: 相对路径

        Returns:
            是否删除成功
        """
        full_path = self.get_full_path(relative_path)

        try:
            if full_path.exists():
                full_path.unlink()
                logger.info(f"[OK] 文件删除成功: {relative_path}")
                return True
            else:
                logger.warning(f"[WARNING] 文件不存在: {relative_path}")
                return False

        except Exception as e:
            logger.error(f"[ERROR] 文件删除失败: {e}")
            return False

    def get_file_size(self, relative_path: str) -> int:
        """
        获取文件大小

        Args:
            relative_path: 相对路径

        Returns:
            文件大小（字节）
        """
        full_path = self.get_full_path(relative_path)
        return full_path.stat().st_size if full_path.exists() else 0

    def get_url(self, relative_path: str) -> str:
        """
        获取文件的访问 URL

        Args:
            relative_path: 相对路径

        Returns:
            文件的 URL
        """
        # 返回 /storage 前缀的 URL
        return f"/storage/{relative_path}"


# 单例实例
file_service = FileService()
