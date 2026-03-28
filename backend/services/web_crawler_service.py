"""
网页爬取服务
使用 Firecrawl 进行网页内容提取
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

import httpx
from loguru import logger

from core.config import settings


class CrawlFormat(Enum):
    """爬取结果格式"""
    MARKDOWN = "markdown"      # Markdown格式
    HTML = "html"              # HTML格式
    RAW_HTML = "rawHtml"       # 原始HTML
    EXTRACT = "extract"        # 提取的内容
    LINKS = "links"            # 只获取链接
    SCREENSHOT = "screenshot"  # 截图
    SCREENSHOT_FULL = "screenshot@fullPage"  # 全页截图


@dataclass
class CrawlResult:
    """爬取结果"""
    success: bool
    url: str
    content: str = ""
    title: str = ""
    markdown: str = ""
    html: str = ""
    links: List[Dict[str, str]] = None
    error: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.links is None:
            self.links = []
        if self.metadata is None:
            self.metadata = {}


class WebCrawlerService:
    """
    网页爬取服务

    支持:
    - Firecrawl API (需要配置 FIRECRAWL_API_KEY)
    - 后备方案: httpx 直接爬取
    """

    def __init__(self):
        """初始化服务"""
        self.firecrawl_api_key = settings.FIRECRAWL_API_KEY
        self.firecrawl_base_url = settings.FIRECRAWL_BASE_URL
        self.use_firecrawl = bool(self.firecrawl_api_key)

        # HTTP客户端（后备方案）
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            follow_redirects=True
        )

        logger.info(f"[爬虫服务] 初始化完成, 使用Firecrawl: {self.use_firecrawl}")

    async def crawl_url(
        self,
        url: str,
        formats: Optional[List[CrawlFormat]] = None,
        only_main_content: bool = True,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
    ) -> CrawlResult:
        """
        爬取单个URL

        Args:
            url: 目标URL
            formats: 需要的格式列表，默认 [MARKDOWN]
            only_main_content: 是否只提取主要内容
            include_tags: 包含的HTML标签
            exclude_tags: 排除的HTML标签

        Returns:
            CrawlResult: 爬取结果
        """
        if formats is None:
            formats = [CrawlFormat.MARKDOWN]

        if self.use_firecrawl:
            return await self._crawl_with_firecrawl(
                url=url,
                formats=formats,
                only_main_content=only_main_content,
                include_tags=include_tags,
                exclude_tags=exclude_tags,
            )
        else:
            logger.warning(f"[爬虫服务] Firecrawl未配置，使用httpx后备方案: {url}")
            return await self._crawl_with_httpx(url)

    async def _crawl_with_firecrawl(
        self,
        url: str,
        formats: List[CrawlFormat],
        only_main_content: bool,
        include_tags: Optional[List[str]],
        exclude_tags: Optional[List[str]],
    ) -> CrawlResult:
        """使用Firecrawl API爬取"""
        try:
            endpoint = f"{self.firecrawl_base_url}/v1/scrape"

            payload = {
                "url": url,
                "formats": [f.value for f in formats],
            }

            # 可选参数
            if only_main_content:
                payload["onlyMainContent"] = only_main_content
            if include_tags:
                payload["includeTags"] = include_tags
            if exclude_tags:
                payload["excludeTags"] = exclude_tags

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.firecrawl_api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()

            # 解析结果
            if not data.get("success", False):
                return CrawlResult(
                    success=False,
                    url=url,
                    error=data.get("error", "爬取失败")
                )

            # Firecrawl 响应格式: {success: true, data: {markdown: "...", metadata: {...}}}
            crawl_data = data.get("data", {})
            metadata = crawl_data.get("metadata", {})

            result = CrawlResult(
                success=True,
                url=url,
                title=metadata.get("title", ""),
                markdown=crawl_data.get("markdown", ""),
                html=crawl_data.get("html", ""),
                content=crawl_data.get("markdown", "") or crawl_data.get("html", ""),
                links=crawl_data.get("links", []),
                metadata=metadata
            )

            logger.info(f"[Firecrawl] 成功爬取: {url}, 内容长度: {len(result.content)}")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"[Firecrawl] HTTP错误: {e.response.status_code} - {url}")
            if e.response.status_code == 401:
                logger.error("[Firecrawl] API密钥无效，请检查FIRECRAWL_API_KEY配置")
            return CrawlResult(
                success=False,
                url=url,
                error=f"HTTP {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"[Firecrawl] 爬取失败: {url}, 错误: {e}")
            # 降级到httpx
            logger.info(f"[爬虫服务] 降级到httpx方案: {url}")
            return await self._crawl_with_httpx(url)

    async def _crawl_with_httpx(self, url: str) -> CrawlResult:
        """使用httpx直接爬取（后备方案）"""
        try:
            response = await self.client.get(url)
            response.raise_for_status()

            # 简单提取HTML
            html = response.text

            # 简单的标题提取
            title = ""
            if "<title>" in html:
                start = html.find("<title>") + 7
                end = html.find("</title>", start)
                title = html[start:end].strip()

            # 转换为简单的Markdown（非常基础）
            content = self._html_to_simple_markdown(html, title)

            result = CrawlResult(
                success=True,
                url=url,
                title=title,
                html=html,
                content=content,
                markdown=content,
                metadata={
                    "method": "httpx",
                    "content_length": len(content)
                }
            )

            logger.info(f"[httpx] 成功爬取: {url}, 内容长度: {len(content)}")
            return result

        except Exception as e:
            logger.error(f"[httpx] 爬取失败: {url}, 错误: {e}")
            return CrawlResult(
                success=False,
                url=url,
                error=str(e)
            )

    def _html_to_simple_markdown(self, html: str, title: str) -> str:
        """将HTML转换为简单的Markdown"""
        from html.parser import HTMLParser
        import re

        class SimpleHTMLParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.in_script = False
                self.in_style = False
                self.last_href = ""  # 初始化，避免属性不存在

            def handle_starttag(self, tag, attrs):
                if tag in ['script', 'style', 'nav', 'footer', 'header']:
                    self.in_script = True
                elif tag == 'p':
                    self.text.append('\n\n')
                elif tag == 'br':
                    self.text.append('\n')
                elif tag == 'h1':
                    self.text.append('\n\n# ')
                elif tag == 'h2':
                    self.text.append('\n\n## ')
                elif tag == 'h3':
                    self.text.append('\n\n### ')
                elif tag in ['strong', 'b']:
                    self.text.append('**')
                elif tag in ['em', 'i']:
                    self.text.append('*')
                elif tag == 'a':
                    for attr, value in attrs:
                        if attr == 'href':
                            self.text.append(f' [')
                            self.last_href = value
                            break
                    else:
                        # 没有href属性的情况
                        self.last_href = ""

            def handle_endtag(self, tag):
                if tag in ['script', 'style', 'nav', 'footer', 'header']:
                    self.in_script = False
                elif tag in ['strong', 'b']:
                    self.text.append('**')
                elif tag in ['em', 'i']:
                    self.text.append('*')
                elif tag == 'a':
                    self.text.append(f']({self.last_href})')
                elif tag in ['p', 'h1', 'h2', 'h3']:
                    self.text.append('\n')

            def handle_data(self, data):
                if not self.in_script:
                    self.text.append(data.strip())

        parser = SimpleHTMLParser()
        parser.feed(html)

        # 清理结果
        result = ''.join(parser.text)
        result = re.sub(r'\n{3,}', '\n\n', result)  # 合并多个换行
        result = result.strip()

        if title:
            result = f"# {title}\n\n{result}"

        return result

    async def crawl_batch(
        self,
        urls: List[str],
        formats: Optional[List[CrawlFormat]] = None,
        max_concurrent: int = 3,
    ) -> List[CrawlResult]:
        """
        批量爬取URL

        Args:
            urls: URL列表
            formats: 需要的格式
            max_concurrent: 最大并发数

        Returns:
            List[CrawlResult]: 爬取结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_with_limit(url: str) -> CrawlResult:
            async with semaphore:
                return await self.crawl_url(url, formats)

        results = await asyncio.gather(
            *[crawl_with_limit(url) for url in urls],
            return_exceptions=True
        )

        # 处理异常
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(CrawlResult(
                    success=False,
                    url=urls[i],
                    error=str(result)
                ))
            else:
                final_results.append(result)

        success_count = sum(1 for r in final_results if r.success)
        logger.info(f"[爬虫服务] 批量爬取完成: {success_count}/{len(urls)} 成功")

        return final_results

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


# 单例实例
web_crawler_service = WebCrawlerService()
