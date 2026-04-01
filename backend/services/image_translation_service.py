"""
图片转译服务
调用 OpenRouter API 进行图片文本翻译
"""

import uuid
import base64
from pathlib import Path
from typing import Optional, Tuple

from openai import OpenAI
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import ImageTranslation, ImageTranslationStatus
from core.config import settings
from services.file_service import file_service


class ImageTranslationService:
    """
    图片转译服务
    """

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.OPENROUTER_IMAGE_MODEL
        # 创建 OpenAI 客户端（用于调用 OpenRouter）- 同步客户端
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    async def create_translation_task(
        self,
        original_filename: str,
        image_content: bytes,
        owner_id: str,
        db: AsyncSession,
    ) -> ImageTranslation:
        """
        创建图片转译任务

        Args:
            original_filename: 原始文件名
            image_content: 图片内容（字节）
            owner_id: 所有者 ID
            db: 数据库会话

        Returns:
            创建的转译任务对象
        """
        try:
            # 1. 保存原图
            original_path, file_hash, file_size = await file_service.save_file(
                file_content=image_content,
                original_filename=original_filename,
                document_type="image",
            )

            # 2. 创建转译任务记录
            translation = ImageTranslation(
                original_filename=original_filename,
                original_image_path=original_path,
                status=ImageTranslationStatus.PENDING.value,  # 使用枚举的值
                file_size=len(image_content),  # 直接使用整数
                mime_type=self._get_mime_type(original_filename),
                owner_id=owner_id,
            )

            db.add(translation)
            await db.commit()
            await db.refresh(translation)

            logger.info(f"[OK] 图片转译任务创建成功: {translation.id}")
            return translation

        except Exception as e:
            logger.error(f"[ERROR] 创建图片转译任务失败: {e}")
            await db.rollback()
            raise

    async def process_translation(
        self,
        translation_id: str,
        db: AsyncSession,
    ) -> ImageTranslation:
        """
        处理图片转译（需要传入数据库会话）

        Args:
            translation_id: 转译任务 ID
            db: 数据库会话

        Returns:
            更新后的转译任务对象
        """
        return await self._process_translation_impl(translation_id, db)

    async def process_translation_background(
        self,
        translation_id: str,
    ) -> ImageTranslation:
        """
        后台处理图片转译（自动创建独立的数据库会话）

        注意：此方法用于��台任务，会创建独立的数据库会话

        Args:
            translation_id: 转译任务 ID

        Returns:
            更新后的转译任务对象
        """
        from core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            try:
                # _process_translation_impl 内部已经处理了 commit
                result = await self._process_translation_impl(translation_id, db)
                return result
            except Exception as e:
                logger.error(f"[ERROR] 后台转译任务失败: {e}")
                raise

    async def _process_translation_impl(
        self,
        translation_id: str,
        db: AsyncSession,
    ) -> ImageTranslation:
        """
        处理图片转译

        Args:
            translation_id: 转译任务 ID
            db: 数据库会话

        Returns:
            更新后的转译任务对象
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"[图片转译] 开始处理转译任务: {translation_id}")
        logger.info(f"{'='*60}\n")

        try:
            # 1. 获取转译任务
            result = await db.execute(
                select(ImageTranslation).where(ImageTranslation.id == translation_id)
            )
            translation = result.scalar_one_or_none()

            if not translation:
                raise ValueError(f"转译任务不存在: {translation_id}")

            # 2. 更新状态为处理中
            translation.status = ImageTranslationStatus.PROCESSING.value
            await db.commit()

            # 3. 读取原图
            from pathlib import Path
            import os

            # 使用file_service获取完整路径
            full_path = file_service.get_full_path(translation.original_image_path)

            if not full_path.exists():
                # 如果路径不存在，尝试其他可能的路径
                base_dir = Path(os.getcwd())
                alt_paths = [
                    base_dir / translation.original_image_path,
                    base_dir / 'storage' / translation.original_image_path,
                    Path('storage') / translation.original_image_path,
                ]
                for alt_path in alt_paths:
                    if alt_path.exists():
                        full_path = alt_path
                        break
                else:
                    raise FileNotFoundError(f"原图文件不存在: {translation.original_image_path}")

            original_path = full_path

            with open(original_path, "rb") as f:
                image_bytes = f.read()

            # 4. 调用 OpenRouter API 进行转译（同步调用）
            logger.info(f"[图片转译] 准备调用 OpenRouter API，图片大小: {len(image_bytes)} 字节")
            translated_image_bytes = self._call_openrouter_api(image_bytes)
            logger.info(f"[图片转译] ✅ OpenRouter API 调用成功，返回图片大小: {len(translated_image_bytes)} 字节")

            # 5. 保存转译后的图片
            translated_filename = f"translated_{translation.original_filename}"
            translated_path, _, _ = await file_service.save_file(
                file_content=translated_image_bytes,
                original_filename=translated_filename,
                document_type="image",
            )

            # 6. 更新转译任务
            translation.translated_image_path = translated_path
            translation.status = ImageTranslationStatus.COMPLETED.value
            await db.commit()
            await db.refresh(translation)

            logger.info(f"[OK] 图片转译完成: {translation.id}")
            return translation

        except Exception as e:
            logger.error(f"[ERROR] 图片转译失败: {e}")

            # 更新为失败状态
            if translation:
                translation.status = ImageTranslationStatus.FAILED.value
                translation.error_message = str(e)
                await db.commit()

            raise

    def _call_openrouter_api(self, image_bytes: bytes) -> bytes:
        """
        调用 OpenRouter API 进行图片转译

        Args:
            image_bytes: 图片字节

        Returns:
            转译后的图片字节
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"[OpenRouter API] 开始调用，图片大小: {len(image_bytes)} 字节")
        logger.info(f"[OpenRouter API] 使用模型: {self.model}")
        logger.info(f"{'='*60}\n")

        try:
            # 将图片转换为 base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            mime_type = self._detect_mime_type(image_bytes)
            data_url = f"data:{mime_type};base64,{image_base64}"

            # 调用 OpenRouter API（使用 OpenAI 客户端）- 同步调用
            logger.info(f"[INFO] 正在调用 OpenRouter API，模型: {self.model}")

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Please translate all English text in this image to Chinese. "
                                "Keep the original layout, colors, and design unchanged. "
                                "Only translate the English text to Chinese. "
                                "Return the modified image."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            }
                        }
                    ]
                }],
                max_tokens=1000,  # 设置较小的 max_tokens 以节省费用
                extra_headers={
                    "HTTP-Referer": "https://docwriting.system",
                    "X-Title": "DocWriting AI System"
                },
                extra_body={
                    "modalities": ["image", "text"]
                },
                timeout=300.0
            )

            logger.info(f"[INFO] OpenRouter API 调用成功")

            # 调试：打印完整响应
            logger.info(f"[DEBUG] completion 类型: {type(completion)}")
            logger.info(f"[DEBUG] choices 数量: {len(completion.choices)}")

            # 按照官方文档解析响应
            response = completion.choices[0].message
            logger.info(f"[DEBUG] response 类型: {type(response)}")
            logger.info(f"[DEBUG] response.content: {response.content}")
            logger.info(f"[DEBUG] response.images: {getattr(response, 'images', '属性不存在')}")
            logger.info(f"[DEBUG] response 所有属性: {dir(response)}")

            # 检查是否有 images 数组
            if response.images:
                logger.info(f"[INFO] 找到 {len(response.images)} 张图片")
                for image in response.images:
                    logger.info(f"[DEBUG] image 类型: {type(image)}, 内容: {image}")
                    # 提取 base64 data URL（严格按照官方文档格式）
                    image_url = image['image_url']['url']
                    logger.info(f"[INFO] 成功提取转译后的图片，URL长度: {len(image_url)}")

                    # 处理 data:image/xxx;base64, 格式
                    if image_url.startswith("data:image"):
                        _, base64_data = image_url.split(",", 1)
                        return base64.b64decode(base64_data)
                    else:
                        # 纯 base64
                        return base64.b64decode(image_url)

            # 如果没有返回图片，抛出错误
            logger.error(f"[ERROR] API 未返回图片")
            logger.error(f"[ERROR] response.images: {getattr(response, 'images', None)}")
            logger.error(f"[ERROR] response.content: {response.content[:500] if response.content else None}")
            raise ValueError("API did not return an image in the expected format")

        except Exception as e:
            logger.error(f"[ERROR] OpenRouter API 调用失败: {e}")
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
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        return mime_types.get(ext, "image/jpeg")

    def _detect_mime_type(self, image_bytes: bytes) -> str:
        """
        通过文件头检测 MIME 类型

        Args:
            image_bytes: 图片字节

        Returns:
            MIME 类型字符串
        """
        # 检查文件头
        if image_bytes.startswith(b"\xFF\xD8\xFF"):
            return "image/jpeg"
        elif image_bytes.startswith(b"\x89PNG\r\n\x1A\n"):
            return "image/png"
        elif image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
            return "image/gif"
        elif image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        else:
            return "image/jpeg"  # 默认


# 单例实例
image_translation_service = ImageTranslationService()
