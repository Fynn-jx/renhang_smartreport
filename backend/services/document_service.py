"""
文档管理服务
处理文档的 CRUD 操作
"""

import uuid
from typing import Optional, List
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from models import Document, Tag, User
from schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentListQuery,
)
from services.file_service import file_service
from utils.pdf_extractor import pdf_extractor


class DocumentService:
    """
    文档管理服务
    """

    async def create_document(
        self,
        document_data: DocumentCreate,
        file_content: bytes,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ) -> Document:
        """
        创建新文档

        Args:
            document_data: 文档数据
            file_content: 文件内容（字节）
            owner_id: 所有者 ID
            db: 数据库会话

        Returns:
            创建的文档对象
        """
        try:
            # 0. 先计算哈希检查是否已存在
            file_hash_check = file_service.get_file_hash(file_content)
            existing_result = await db.execute(
                select(Document).where(Document.file_hash == file_hash_check)
            )
            existing_doc = existing_result.scalar_one_or_none()
            if existing_doc:
                logger.info(f"[OK] 文档已存在（哈希重复）: {existing_doc.id} - {existing_doc.title}")
                return existing_doc

            # 1. 保存文件
            file_path, file_hash, file_size = await file_service.save_file(
                file_content=file_content,
                original_filename=document_data.original_filename,
                document_type=document_data.document_type,
            )

            # 2. 提取内容（如果是 PDF）
            content = None
            content_preview = None
            page_count = None
            author = document_data.author
            subject = document_data.subject

            if document_data.document_type == "pdf" and pdf_extractor:
                try:
                    extracted = pdf_extractor.extract_from_bytes(file_content)
                    content = extracted["content"]
                    content_preview = pdf_extractor.extract_preview(content)
                    page_count = extracted["page_count"]

                    # 如果未提供作者和主题，尝试从元数据提取
                    if not author:
                        author = extracted["author"]
                    if not subject:
                        subject = extracted["subject"]

                    logger.info(f"[OK] PDF 内容提取成功: {page_count} 页")

                except Exception as e:
                    logger.warning(f"[WARNING] PDF 内容提取失败: {e}")

            # 3. 创建文档记录
            document = Document(
                title=document_data.title,
                original_filename=document_data.original_filename,
                document_type=document_data.document_type,
                file_path=file_path,
                file_size=file_size,
                file_hash=file_hash,
                mime_type=self._get_mime_type(document_data.document_type),
                content=content,
                content_preview=content_preview,
                page_count=page_count,
                author=author,
                subject=subject,
                keywords=document_data.keywords,
                source_url=document_data.source_url,
                source_type=document_data.source_type,
                owner_id=owner_id,
                parent_id=document_data.parent_id,
                is_shared=document_data.is_shared if document_data.is_shared is not None else False,
            )

            # 4. 关联标签
            if document_data.tag_ids:
                # 加载标签
                result = await db.execute(
                    select(Tag).where(Tag.id.in_(document_data.tag_ids))
                )
                tags = result.scalars().all()
                document.tags = tags

            # 5. 保存到数据库
            db.add(document)
            await db.commit()
            await db.refresh(document)

            logger.info(f"[OK] 文档创建成功: {document.id} - {document.title}")
            return document

        except Exception as e:
            # 处理并发插入导致的唯一约束冲突
            if "duplicate key" in str(e).lower() or "uniqueviolation" in str(e).lower():
                logger.warning(f"[WARNING] 并发插入冲突，返回已存在的文档")
                await db.rollback()
                # 重新查询已存在的文档
                file_hash_check = file_service.get_file_hash(file_content)
                existing_result = await db.execute(
                    select(Document).where(Document.file_hash == file_hash_check)
                )
                existing_doc = existing_result.scalar_one_or_none()
                if existing_doc:
                    return existing_doc
            logger.error(f"[ERROR] 文档创建失败: {e}")
            await db.rollback()
            raise

    async def get_document(
        self,
        document_id: uuid.UUID,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ) -> Optional[Document]:
        """
        获取单个文档

        Args:
            document_id: 文档 ID
            owner_id: 所有者 ID
            db: 数据库会话

        Returns:
            文档对象，如果不存在返回 None
        """
        try:
            result = await db.execute(
                select(Document)
                .where(
                    and_(
                        Document.id == str(document_id),
                        Document.owner_id == str(owner_id),
                    )
                )
                .options(selectinload(Document.tags))
            )
            document = result.scalar_one_or_none()

            if document:
                logger.debug(f"[OK] 文档获取成功: {document.id}")
            else:
                logger.warning(f"[WARNING] 文档不存在: {document_id}")

            return document

        except Exception as e:
            logger.error(f"[ERROR] 获取文档失败: {e}")
            raise

    async def list_documents(
        self,
        query_params: DocumentListQuery,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ) -> tuple[List[Document], int]:
        """
        获取文档列表（分页）

        Args:
            query_params: 查询参数
            owner_id: 所有者 ID
            db: 数据库会话

        Returns:
            (文档列表, 总数量)
        """
        try:
            # 构建查询：返回自己的文档 + 所有人共享的文档
            stmt = select(Document).where(
                or_(
                    Document.owner_id == owner_id,      # 自己的文档
                    Document.is_shared == True          # 共享的文档
                )
            )

            # 筛选条件
            if query_params.document_type:
                stmt = stmt.where(Document.document_type == query_params.document_type)

            if query_params.keyword:
                keyword = f"%{query_params.keyword}%"
                stmt = stmt.where(
                    or_(
                        Document.title.ilike(keyword),
                        Document.author.ilike(keyword),
                        Document.subject.ilike(keyword),
                    )
                )

            if query_params.tag_id:
                # 通过标签筛选
                stmt = stmt.join(Document.tags).where(Tag.id == query_params.tag_id)

            # 排序
            sort_column = getattr(Document, query_params.sort_by, Document.created_at)
            if query_params.sort_order == "desc":
                stmt = stmt.order_by(sort_column.desc())
            else:
                stmt = stmt.order_by(sort_column.asc())

            # 加载标签关系
            stmt = stmt.options(selectinload(Document.tags))

            # 计算总数
            count_stmt = select(Document.id).where(
                or_(
                    Document.owner_id == owner_id,      # 自己的文档
                    Document.is_shared == True          # 共享的文档
                )
            )
            if query_params.document_type:
                count_stmt = count_stmt.where(Document.document_type == query_params.document_type)
            if query_params.keyword:
                keyword = f"%{query_params.keyword}%"
                count_stmt = count_stmt.where(
                    or_(
                        Document.title.ilike(keyword),
                        Document.author.ilike(keyword),
                        Document.subject.ilike(keyword),
                    )
                )
            if query_params.tag_id:
                count_stmt = count_stmt.join(Document.tags).where(Tag.id == query_params.tag_id)

            total_result = await db.execute(select(count_stmt.c.id).select_from(count_stmt))
            total = len(total_result.all())

            # 分页
            offset = (query_params.page - 1) * query_params.page_size
            stmt = stmt.offset(offset).limit(query_params.page_size)

            # 执行查询
            result = await db.execute(stmt)
            documents = result.scalars().all()

            logger.debug(f"[OK] 文档列表获取成功: {len(documents)}/{total}")
            return documents, total

        except Exception as e:
            logger.error(f"[ERROR] 获取文档列表失败: {e}")
            raise

    async def update_document(
        self,
        document_id: uuid.UUID,
        document_data: DocumentUpdate,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ) -> Optional[Document]:
        """
        更新文档

        Args:
            document_id: 文档 ID
            document_data: 更新数据
            owner_id: 所有者 ID
            db: 数据库会话

        Returns:
            更新后的文档对象，如果不存在返回 None
        """
        try:
            # 获取文档
            document = await self.get_document(document_id, owner_id, db)
            if not document:
                return None

            # 更新字段
            if document_data.title is not None:
                document.title = document_data.title
            if document_data.author is not None:
                document.author = document_data.author
            if document_data.subject is not None:
                document.subject = document_data.subject
            if document_data.keywords is not None:
                document.keywords = document_data.keywords
            if document_data.is_shared is not None:
                document.is_shared = document_data.is_shared

            # 更新标签
            if document_data.tag_ids is not None:
                result = await db.execute(
                    select(Tag).where(Tag.id.in_(document_data.tag_ids))
                )
                tags = result.scalars().all()
                document.tags = tags

            await db.commit()
            await db.refresh(document)

            logger.info(f"[OK] 文档更新成功: {document.id}")
            return document

        except Exception as e:
            logger.error(f"[ERROR] 文档更新失败: {e}")
            await db.rollback()
            raise

    async def delete_document(
        self,
        document_id: uuid.UUID,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ) -> bool:
        """
        删除文档

        Args:
            document_id: 文档 ID
            owner_id: 所有者 ID
            db: 数据库会话

        Returns:
            是否删除成功
        """
        try:
            # 获取文档
            document = await self.get_document(document_id, owner_id, db)
            if not document:
                return False

            # 删除文件
            file_service.delete_file(document.file_path)

            # 删除缩略图（如果有）
            if document.thumbnail_path:
                file_service.delete_file(document.thumbnail_path)

            # 删除数据库记录
            await db.delete(document)
            await db.commit()

            logger.info(f"[OK] 文档删除成功: {document_id}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] 文档删除失败: {e}")
            await db.rollback()
            raise

    def _get_mime_type(self, document_type: str) -> str:
        """
        获取文档类型的 MIME 类型

        Args:
            document_type: 文档类型

        Returns:
            MIME 类型字符串
        """
        mime_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain",
            "markdown": "text/markdown",
            "image": "image/jpeg",
        }

        return mime_types.get(document_type, "application/octet-stream")


# 单例实例
document_service = DocumentService()
