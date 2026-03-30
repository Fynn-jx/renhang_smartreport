"""
MinerU PDF转Markdown服务
使用MinerU精准解析API将PDF转换为高质量Markdown
支持页眉、页脚、脚注等元素的自动去除
"""

import asyncio
import hashlib
import hmac
import json
import os
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

import httpx
from loguru import logger

from core.config import settings


@dataclass
class MineruProgressUpdate:
    """进度更新"""
    stage: str  # uploading, submitting, processing, downloading, done, failed
    progress: float  # 0-100
    message: str
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            **self.data
        }

    def to_sse(self) -> str:
        return f"data: {json.dumps(self.to_dict(), ensure_ascii=False)}\n\n"


class MineruService:
    """MinerU PDF转Markdown服务"""

    # API配置
    BASE_URL = settings.MINERU_BASE_URL or "https://mineru.net"
    API_KEY = settings.MINERU_API_KEY

    # 默认参数
    DEFAULT_MODEL_VERSION = "vlm"  # vlm 或 pipeline

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json",
        }

    async def parse_pdf_to_markdown(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[MineruProgressUpdate], None]] = None,
        model_version: str = DEFAULT_MODEL_VERSION,
    ) -> str:
        """
        将PDF文件转换为Markdown

        Args:
            file_path: PDF文件路径
            progress_callback: 进度回调函数
            model_version: 模型版本，"vlm"或"pipeline"

        Returns:
            Markdown内容的字符串
        """
        logger.info(f"[MinerU] 开始解析PDF: {file_path}")

        # 1. 上传文件到可访问的URL
        await self._emit_progress(
            "uploading",
            10,
            "上传文件...",
            {},
            progress_callback
        )

        file_url = await self._upload_file(file_path)
        if not file_url:
            raise Exception("文件上传失败")

        logger.info(f"[MinerU] 文件已上传: {file_url}")

        # 2. 创建解析任务
        await self._emit_progress(
            "submitting",
            30,
            "提交解析任务...",
            {"file_url": file_url},
            progress_callback
        )

        task_id = await self._create_task(file_url, model_version)
        if not task_id:
            raise Exception("创建解析任务失败")

        logger.info(f"[MinerU] 任务已创建: {task_id}")

        # 3. 轮询等待完成
        await self._emit_progress(
            "processing",
            50,
            "正在解析PDF...",
            {"task_id": task_id},
            progress_callback
        )

        result_url = await self._wait_for_completion(task_id, progress_callback)
        if not result_url:
            raise Exception("解析任务超时或失败")

        logger.info(f"[MinerU] 解析完成: {result_url}")

        # 4. 下载并解压结果
        await self._emit_progress(
            "downloading",
            90,
            "下载解析结果...",
            {"result_url": result_url},
            progress_callback
        )

        markdown_content = await self._download_and_extract(result_url, file_path)

        await self._emit_progress(
            "done",
            100,
            "解析完成",
            {"content_length": len(markdown_content)},
            progress_callback
        )

        return markdown_content

    async def parse_pdf_by_url(
        self,
        pdf_url: str,
        progress_callback: Optional[Callable[[MineruProgressUpdate], None]] = None,
        model_version: str = DEFAULT_MODEL_VERSION,
    ) -> str:
        """
        通过URL解析PDF

        Args:
            pdf_url: PDF的URL地址
            progress_callback: 进度回调函数
            model_version: 模型版本

        Returns:
            Markdown内容的字符串
        """
        logger.info(f"[MinerU] 开始解析URL: {pdf_url}")

        await self._emit_progress(
            "submitting",
            20,
            "提交解析任务...",
            {"url": pdf_url},
            progress_callback
        )

        task_id = await self._create_task(pdf_url, model_version)
        if not task_id:
            raise Exception("创建解析任务失败")

        await self._emit_progress(
            "processing",
            40,
            "正在解析PDF...",
            {"task_id": task_id},
            progress_callback
        )

        result_url = await self._wait_for_completion(task_id, progress_callback)
        if not result_url:
            raise Exception("解析任务超时或失败")

        await self._emit_progress(
            "downloading",
            80,
            "下载解析结果...",
            {"result_url": result_url},
            progress_callback
        )

        markdown_content = await self._download_and_extract_by_url(result_url)

        await self._emit_progress(
            "done",
            100,
            "解析完成",
            {"content_length": len(markdown_content)},
            progress_callback
        )

        return markdown_content

    async def _upload_to_cos(self, file_path: str) -> Optional[str]:
        """
        上传文件到腾讯云COS，返回公开访问URL

        Returns:
            文件的公开URL地址
        """
        try:
            from qcloud_cos import CosConfig, CosS3Client

            file_name = os.path.basename(file_path)
            timestamp = int(time.time())
            object_key = f"mineru/{timestamp}_{file_name}"

            # COS配置
            config = CosConfig(
                Region=settings.TENCENT_COS_REGION,
                SecretId=settings.TENCENT_COS_SECRET_ID,
                SecretKey=settings.TENCENT_COS_SECRET_KEY,
                Token=None,
                Scheme='https'
            )

            # 创建客户端
            cos_client = CosS3Client(config)

            # 同步上传（在线程池中执行避免阻塞）
            def upload_sync():
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                response = cos_client.put_object(
                    Bucket=settings.TENCENT_COS_BUCKET,
                    Body=file_content,
                    Key=object_key,
                    ContentType='application/pdf'
                )
                return response

            # 使用 asyncio.to_thread 执行同步IO
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, upload_sync)

            logger.info(f"[COS] 上传响应: {response}")

            # 生成公开访问URL
            public_url = f"https://{settings.TENCENT_COS_BUCKET}.cos.{settings.TENCENT_COS_REGION}.myqcloud.com/{object_key}"

            logger.info(f"[COS] 文件上传成功: {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"[COS] 上传文件异常: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _upload_file(self, file_path: str) -> Optional[str]:
        """
        将文件上传到可访问的URL

        优先使用腾讯云COS上传（稳定），失败则使用MinerU内置上传

        Returns:
            文件的URL地址
        """
        # 优先使用腾讯云COS
        cos_url = await self._upload_to_cos(file_path)
        if cos_url:
            return cos_url

        # 回退到MinerU内置上传
        logger.warning("[MinerU] COS上传失败，回退到MinerU内置上传")
        return await self._upload_file_mineru(file_path)

    async def _upload_file_mineru(self, file_path: str) -> Optional[str]:
        """
        将文件上传到MinerU（内置方式）

        Returns:
            文件的URL地址
        """
        try:
            # 首先获取上传URL
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            # 如果文件太大，先上传到URL
            # 使用批量上传接口
            async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
                # 申请上传链接
                batch_url = f"{self.BASE_URL}/api/v4/file-urls/batch"
                payload = {
                    "files": [{"name": file_name, "data_id": self._generate_data_id(file_path)}],
                    "model_version": self.DEFAULT_MODEL_VERSION,
                }

                response = await client.post(
                    batch_url,
                    headers=self.headers,
                    json=payload
                )

                if response.status_code != 200:
                    logger.error(f"[MinerU] 申请上传URL失败: {response.text}")
                    return None

                result = response.json()
                if result.get("code") != 0:
                    logger.error(f"[MinerU] 申请上传URL失败: {result.get('msg')}")
                    return None

                batch_id = result["data"]["batch_id"]
                upload_urls = result["data"]["file_urls"]

                if not upload_urls:
                    logger.error("[MinerU] 未获取到上传URL")
                    return None

                upload_url = upload_urls[0]

                # 上传文件
                with open(file_path, "rb") as f:
                    upload_response = await client.put(
                        upload_url,
                        content=f.read()
                    )

                if upload_response.status_code != 200:
                    logger.error(f"[MinerU] 文件上传失败: {upload_response.status_code}")
                    return None

                # 返回文件URL（通常是CDN地址）
                # MinerU会从上传的URL拉取文件
                return upload_url

        except Exception as e:
            logger.error(f"[MinerU] 上传文件异常: {e}")
            return None

    def _generate_data_id(self, file_path: str) -> str:
        """生成唯一data_id"""
        timestamp = str(int(time.time()))
        file_hash = hashlib.md5(f"{file_path}{timestamp}".encode()).hexdigest()[:8]
        return f"mineru_{file_hash}"

    async def _create_task(self, file_url: str, model_version: str) -> Optional[str]:
        """创建解析任务"""
        try:
            url = f"{self.BASE_URL}/api/v4/extract/task"
            payload = {
                "url": file_url,
                "model_version": model_version,
                "enable_formula": True,
                "enable_table": True,
                "language": "ch",
            }

            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload
                )

                if response.status_code != 200:
                    logger.error(f"[MinerU] 创建任务失败: {response.text}")
                    return None

                result = response.json()
                if result.get("code") != 0:
                    logger.error(f"[MinerU] 创建任务失败: {result.get('msg')}")
                    return None

                return result["data"]["task_id"]

        except Exception as e:
            logger.error(f"[MinerU] 创建任务异常: {e}")
            return None

    async def _wait_for_completion(
        self,
        task_id: str,
        progress_callback: Optional[Callable[[MineruProgressUpdate], None]] = None,
        max_wait: int = 300,
        poll_interval: int = 5,
    ) -> Optional[str]:
        """
        轮询等待任务完成

        Returns:
            完成后的结果URL
        """
        start_time = time.time()
        last_state = None

        while time.time() - start_time < max_wait:
            try:
                url = f"{self.BASE_URL}/api/v4/extract/task/{task_id}"

                async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                    response = await client.get(url, headers=self.headers)

                    if response.status_code != 200:
                        logger.error(f"[MinerU] 查询任务失败: {response.text}")
                        await asyncio.sleep(poll_interval)
                        continue

                    result = response.json()
                    if result.get("code") != 0:
                        logger.error(f"[MinerU] 查询任务失败: {result.get('msg')}")
                        await asyncio.sleep(poll_interval)
                        continue

                    data = result.get("data", {})
                    state = data.get("state")

                    if state != last_state:
                        logger.info(f"[MinerU] 任务状态: {state}")
                        last_state = state

                    if state == "done":
                        full_zip_url = data.get("full_zip_url")
                        if full_zip_url:
                            return full_zip_url
                        else:
                            logger.error("[MinerU] 任务完成但无结果URL")
                            return None

                    elif state == "failed":
                        err_msg = data.get("err_msg", "未知错误")
                        logger.error(f"[MinerU] 任务失败: {err_msg}")
                        return None

                    elif state == "running":
                        # 更新进度
                        progress_info = data.get("extract_progress", {})
                        extracted = progress_info.get("extracted_pages", 0)
                        total = progress_info.get("total_pages", 0)
                        if total > 0:
                            current_progress = 40 + int((extracted / total) * 40)
                            await self._emit_progress(
                                "processing",
                                current_progress,
                                f"正在解析... ({extracted}/{total}页)",
                                {"extracted": extracted, "total": total},
                                progress_callback
                            )

                    # 等待
                    await asyncio.sleep(poll_interval)

            except Exception as e:
                logger.error(f"[MinerU] 查询任务异常: {e}")
                await asyncio.sleep(poll_interval)

        logger.error("[MinerU] 等待超时")
        return None

    async def _download_and_extract(
        self,
        zip_url: str,
        original_file_path: str,
    ) -> str:
        """
        下载并解压结果ZIP，提取Markdown内容
        """
        try:
            async with httpx.AsyncClient(timeout=120.0, verify=False) as client:
                response = await client.get(zip_url)

                if response.status_code != 200:
                    logger.error(f"[MinerU] 下载结果失败: {response.status_code}")
                    return ""

                # 保存到临时文件
                temp_zip = f"/tmp/mineru_result_{int(time.time())}.zip"
                with open(temp_zip, "wb") as f:
                    f.write(response.content)

                # 解压
                extract_dir = temp_zip.replace(".zip", "")
                with zipfile.ZipFile(temp_zip, "r") as zf:
                    zf.extractall(extract_dir)

                # 查找full.md文件
                md_path = os.path.join(extract_dir, "full.md")
                if os.path.exists(md_path):
                    with open(md_path, "r", encoding="utf-8") as f:
                        content = f.read()
                else:
                    # 查找其他md文件
                    md_files = list(Path(extract_dir).glob("**/*.md"))
                    if md_files:
                        with open(md_files[0], "r", encoding="utf-8") as f:
                            content = f.read()
                    else:
                        logger.error("[MinerU] 未找到Markdown文件")
                        content = ""

                # 清理临时文件
                try:
                    os.remove(temp_zip)
                    import shutil
                    shutil.rmtree(extract_dir)
                except:
                    pass

                return content

        except Exception as e:
            logger.error(f"[MinerU] 下载解压异常: {e}")
            return ""

    async def _download_and_extract_by_url(self, zip_url: str) -> str:
        """通过URL下载并提取"""
        return await self._download_and_extract(zip_url, "")

    async def _emit_progress(
        self,
        stage: str,
        progress: float,
        message: str,
        data: Dict[str, Any],
        callback: Optional[Callable[[MineruProgressUpdate], None]],
    ):
        """发送进度更新"""
        if callback:
            update = MineruProgressUpdate(
                stage=stage,
                progress=progress,
                message=message,
                data=data
            )
            if asyncio.iscoroutinefunction(callback):
                await callback(update)
            else:
                callback(update)


# 单例
mineru_service = MineruService()
