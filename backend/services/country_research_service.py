"""
国别研究工作流服务
支持数据源插拔式切换，提供关键节点思维链输出
"""

import json
import asyncio
import re
from typing import Optional, List, Dict, Any, Callable, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from openai import AsyncOpenAI
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from configs.country_data_sources import (
    CountryDataSourceRegistry,
    CountryProfile,
    DataSourceConfig,
    DataSourceType
)
from configs.prompts import COUNTRY_RESEARCH_SYSTEM_PROMPT_V3
from services.web_crawler_service import web_crawler_service, CrawlFormat
from utils.text_extraction import extract_marked_content


class CountryResearchStage(Enum):
    """国别研究工作流阶段"""
    STARTED = "started"                      # 工作流开始
    CONFIG_LOADING = "config_loading"        # 配置加载
    DATA_FETCHING = "data_fetching"          # 数据采集
    ECONOMIC_ANALYSIS = "economic_analysis"  # 经济分析
    POLITICAL_ANALYSIS = "political_analysis"# 政治分析
    DIPLOMACY_ANALYSIS = "diplomacy_analysis"# 外交分析
    REPORT_GENERATION = "report_generation"  # 报告生成
    QUALITY_REVIEW = "quality_review"        # 质量审核
    COMPLETED = "completed"                  # 完成
    FAILED = "failed"                        # 失败


@dataclass
class ThinkingChainNode:
    """思维链节点"""
    stage: CountryResearchStage
    node_id: str
    title: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    sub_nodes: List['ThinkingChainNode'] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "node_id": self.node_id,
            "title": self.title,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "sub_nodes": [n.to_dict() for n in self.sub_nodes]
        }


@dataclass
class ProgressUpdate:
    """进度更新消息"""
    stage: CountryResearchStage
    stage_name: str
    progress: float  # 0-100
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: Dict[str, Any] = field(default_factory=dict)
    thinking_node: Optional[ThinkingChainNode] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "stage": self.stage.value,
            "stage_name": self.stage_name,
            "progress": self.progress,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.data
        }
        if self.thinking_node:
            result["thinking_node"] = self.thinking_node.to_dict()
        return result

    def to_sse(self) -> str:
        """转换为 SSE 格式"""
        return f"data: {json.dumps(self.to_dict(), ensure_ascii=False)}\n\n"


class CountryResearchService:
    """
    国别研究工作流服务
    """

    # 模型配置
    DEEPSEEK_MODEL = "Pro/deepseek-ai/DeepSeek-V3"
    GLM_MODEL = "Pro/zai-org/GLM-5"

    # 并发配置
    MAX_CONCURRENT_FETCHES = 5  # 同时抓取的最大数据源数量

    # 进度分配
    PROGRESS_CONFIG = {
        CountryResearchStage.CONFIG_LOADING: (0, 5),
        CountryResearchStage.DATA_FETCHING: (5, 25),
        CountryResearchStage.ECONOMIC_ANALYSIS: (25, 45),
        CountryResearchStage.POLITICAL_ANALYSIS: (45, 60),
        CountryResearchStage.DIPLOMACY_ANALYSIS: (60, 75),
        CountryResearchStage.REPORT_GENERATION: (75, 90),
        CountryResearchStage.QUALITY_REVIEW: (90, 98),
    }

    # ============== 提示词模板 ==============

    # 国别研究总提示词（V3.0 - 固定格式 + 数据来源标注）
    COUNTRY_RESEARCH_SYSTEM_PROMPT = COUNTRY_RESEARCH_SYSTEM_PROMPT_V3

    # 旧版提示词（已弃用，保留用于兼容）
    COUNTRY_RESEARCH_SYSTEM_PROMPT_LEGACY = """角色设定：
你是一名政府智库的高级国别研究员。你的任务是根据提供的目标国家信息，撰写一份标准化的《[国家名称]经济与政治概况》。

写作原则：

1. 客观公文风：拒绝使用形容词堆砌（如"美丽的"、"令人惊叹的"），使用冷静、客观的描述性语言。

2. 数据高密度：文中必须包含具体的时间戳（如 2024.12）、精确数值（如 4030亿美元）和同比/环比变化率，且严格保证所提供的数据是最新的数据。

3. 结构复刻：严格遵守下方的输出模板，不要随意增减一级标题。

4. 时效性优先：优先选取知识库中最新的数据（2024年-2025年），若无最新数据，需标注数据年份。

输出模板（请严格按此格式生成）：

标题：[目标国家]经济与政治概况

一、基本信息

（请以列表或键值对形式呈现，确保包含以下要素）

国名：[全称]（英文全称）
面积：[数值] 万平方公里
人口：[数值]（数据年份/月份）
主要人种/民族：[主要构成]
官方语言：[语言名称]
宗教信仰：[主要宗教及占比]
首都：[名称]，人口约 [数值]
自然资源：[列举主要矿产或能源资源]
地理位置：[描述所在洲、接壤国家及临海情况]

二、经济

1. 核心指标（最新数据）

（请将以下数据整理为工整的排版，如无法获取某项具体数据，可留空或标注 N/A）

GDP总值：[数值]（年份） | 公共债务：[GDP占比%]（年份）
GDP增速：[百分比]（年份/季度） | 财政赤字：[GDP占比%]（年份）
人均GDP：[数值]（年份） | 基准利率：[百分比]（日期）
通胀水平：[百分比]（日期） | 外汇储备：[数值]（日期）
失业率：[百分比]（日期） | 国债收益率（10年期）：[百分比]（日期）
贸易规模：[数值]（日期） | 官方货币：[名称]
股指表现：[涨跌幅/点位]（日期） | 汇率表现：[涨跌幅/数值]（日期）

2. 经济概况

总体定位：描述该国的收入等级（如高收入/中等收入）及在区域经济中的地位。
近期走势：概括近两年的经济增长趋势（复苏/衰退/平稳）。
外部影响：分析地缘政治、全球大宗商品价格或供应链变动对该国经济的具体影响。
增长动力：列举当前驱动经济增长的核心因素（如消费、出口、特定行业投资）。

3. 主要产业

产业结构：描述农业、工业、服务业占GDP的大致比重。
支柱行业：详细列举该国的核心工业或服务业部门（如汽车制造、旅游、半导体、能源开采等）。
就业结构：如果数据允许，简述主要就业吸纳部门。

4. 对外贸易

贸易伙伴：列举前五大贸易伙伴国。
收支状况：描述贸易顺差或逆差的具体数值及变化趋势。
进出口结构：主要出口商品和主要进口商品。

5. 国际金融合作与重大项目

（注：若该国为受援国，重点描述IMF/世界银行项目、债务重组及提款情况；若该国为发达国家，重点描述其主导的重大国际投资或金融稳定性举措。）

合作进展：描述与国际金融机构的最新互动、评级调整或重大融资协议。
改革与挑战：涉及的结构性改革要求（如私有化、税制改革）或面临的宏观挑战。

6. 货币政策

政策基调：央行当前的政策立场（宽松/紧缩/中性）。
利率操作：描述最近一个周期的加息或降息路径（包括具体的基点数 bp 和操作时间）。
通胀与目标：当前的通胀率与央行设定的通胀目标区间的对比。
汇率与储备：汇率制度（浮动/固定/挂钩）及外汇储备的构成与变动情况。

三、政治

1. 国家元首/政府首脑

[职位名称]：[姓名]（外文名）。[就职年份]就职，[描述连任情况或任期]。

2. 对华关系

建交历史：建交日期及是否为该地区首个建交国等历史节点。
关系定位：当前的双边关系级别（如全面战略伙伴关系）。
经贸数据：最新的双边贸易额、中国在该国的投资或工程承包情况。
高层互访：近期的高层访问记录。

3. 对外关系

外交传统：奉行的主要外交原则（如结盟政策、中立、多边主义等）。
国际组织：参与的主要国际或地区组织（如欧盟、阿盟、东盟、北约、金砖国家等）。
地区角色：在所在区域的地缘政治影响力及主要关注的地区议题。

执行指令：
现在，请依据提供的资料，撰写**{country_name}**的国别概况。若资料中缺少某项三级指标（如"股指涨幅"），请跳过该细项，保持整体结构的完整性。
"""

    def __init__(self):
        """初始化服务"""
        self.api_key = settings.SILICONFLOW_API_KEY
        self.base_url = settings.SILICONFLOW_BASE_URL
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    async def process_country_research(
        self,
        country_code: str,
        reference_file: Optional[str] = None,
        user_sources: Optional[List[Dict[str, str]]] = None,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None,
        db: Optional[AsyncSession] = None,
    ) -> AsyncIterator[ProgressUpdate]:
        """
        执行国别研究工作流

        Args:
            country_code: 国家代码 (如 EG, KE, NG)
            reference_file: 参考文件路径（可选）
            user_sources: 用户补充的数据源列表，格式: [{"name": "名称", "url": "https://..."}]
            progress_callback: 进度回调函数（可选）
            db: 数据库会话（可选）

        Yields:
            ProgressUpdate: 进度更新
        """
        try:
            # 存储工作流上下文数据
            context = {
                "country_code": country_code,
                "country_profile": None,
                "fetched_data": {},
                "economic_analysis": "",
                "political_analysis": "",
                "diplomacy_analysis": "",
                "final_report": "",
            }

            # 处理用户补充数据源
            if user_sources:
                country_profile = CountryDataSourceRegistry.get_country_with_user_sources(
                    country_code,
                    user_sources
                )
            else:
                country_profile = CountryDataSourceRegistry.get_country(country_code)

            if not country_profile:
                raise ValueError(f"未找到国家代码: {country_code}，请先注册该国家")

            context["country_profile"] = country_profile

            # ========== 阶段1: 配置加载 ==========
            yield await self._emit_progress(
                CountryResearchStage.CONFIG_LOADING,
                f"正在加载 {country_code.upper()} 国家配置...",
                2,
                {"step": "配置加载"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=CountryResearchStage.CONFIG_LOADING,
                    node_id=f"config_{country_code}",
                    title="国家配置加载",
                    content=f"开始检索 {country_code.upper()} 的数据源配置" +
                           (f"，包含 {len(user_sources)} 个用户补充数据源" if user_sources else ""),
                    metadata={"country_code": country_code, "user_sources_count": len(user_sources) if user_sources else 0}
                )
            )

            yield await self._emit_progress(
                CountryResearchStage.CONFIG_LOADING,
                f"配置加载完成：{country_profile.country_name}，共 {len(country_profile.data_sources)} 个数据源",
                5,
                {
                    "country_name": country_profile.country_name,
                    "data_source_count": len(country_profile.data_sources),
                    "region": country_profile.region
                },
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=CountryResearchStage.CONFIG_LOADING,
                    node_id=f"config_loaded_{country_code}",
                    title=f"{country_profile.country_name}配置已加载",
                    content=f"国家: {country_profile.country_name}({country_profile.country_name_en})\n"
                           f"区域: {country_profile.region}\n"
                           f"收入等级: {country_profile.income_level}\n"
                           f"货币: {country_profile.currency}\n"
                           f"数据源数量: {len(country_profile.data_sources)}",
                    metadata={
                        "country": country_profile.country_name,
                        "region": country_profile.region,
                        "data_sources": [ds.label for ds in country_profile.data_sources[:5]]
                    }
                )
            )

            # ========== 阶段2: 数据采集 ==========
            yield await self._emit_progress(
                CountryResearchStage.DATA_FETCHING,
                "开始采集数据源...",
                6,
                {"step": "数据采集"},
                progress_callback
            )

            fetched_data = await self._fetch_data_sources(
                country_profile,
                progress_callback
            )
            context["fetched_data"] = fetched_data

            # ========== 阶段3: 经济分析 ==========
            yield await self._emit_progress(
                CountryResearchStage.ECONOMIC_ANALYSIS,
                "正在进行经济分析...",
                25,
                {"step": "经济分析"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=CountryResearchStage.ECONOMIC_ANALYSIS,
                    node_id="economic_start",
                    title="经济分析启动",
                    content=f"开始分析 {country_profile.country_name} 的经济状况，包括GDP、通胀、货币政策等核心指标",
                    metadata={"analysis_type": "economic"}
                )
            )

            economic_analysis = await self._analyze_economy(
                country_profile,
                fetched_data,
                progress_callback
            )
            context["economic_analysis"] = economic_analysis

            # ========== 阶段4: 政治分析 ==========
            yield await self._emit_progress(
                CountryResearchStage.POLITICAL_ANALYSIS,
                "正在进行政治分析...",
                45,
                {"step": "政治分析"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=CountryResearchStage.POLITICAL_ANALYSIS,
                    node_id="political_start",
                    title="政治分析启动",
                    content=f"开始分析 {country_profile.country_name} 的政治状况，包括国家元首、政府结构等",
                    metadata={"analysis_type": "political"}
                )
            )

            political_analysis = await self._analyze_politics(
                country_profile,
                fetched_data,
                progress_callback
            )
            context["political_analysis"] = political_analysis

            # ========== 阶段5: 外交分析 ==========
            yield await self._emit_progress(
                CountryResearchStage.DIPLOMACY_ANALYSIS,
                "正在进行外交关系分析...",
                60,
                {"step": "外交分析"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=CountryResearchStage.DIPLOMACY_ANALYSIS,
                    node_id="diplomacy_start",
                    title="外交关系分析启动",
                    content=f"开始分析 {country_profile.country_name} 的对外关系，特别是对华关系",
                    metadata={"analysis_type": "diplomacy"}
                )
            )

            diplomacy_analysis = await self._analyze_diplomacy(
                country_profile,
                fetched_data,
                progress_callback
            )
            context["diplomacy_analysis"] = diplomacy_analysis

            # ========== 阶段6: 报告生成 ==========
            yield await self._emit_progress(
                CountryResearchStage.REPORT_GENERATION,
                "正在生成最终报告...",
                75,
                {"step": "报告生成"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=CountryResearchStage.REPORT_GENERATION,
                    node_id="report_generation",
                    title="整合分析结果生成报告",
                    content="将经济、政治、外交分析整合为完整的国别研究报告",
                    metadata={"analysis_types": ["economic", "political", "diplomacy"]}
                )
            )

            final_report = await self._generate_report(
                country_profile,
                economic_analysis,
                political_analysis,
                diplomacy_analysis,
                reference_file,
                progress_callback
            )
            context["final_report"] = final_report

            # ========== 阶段7: 质量审核 ==========
            yield await self._emit_progress(
                CountryResearchStage.QUALITY_REVIEW,
                "正在进行质量审核...",
                90,
                {"step": "质量审核"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=CountryResearchStage.QUALITY_REVIEW,
                    node_id="quality_review",
                    title="报告质量审核",
                    content="检查报告的完整性、数据准确性和公文规范性",
                    metadata={"review_criteria": ["completeness", "accuracy", "format"]}
                )
            )

            reviewed_report = await self._quality_review(final_report, progress_callback)

            # ========== 完成 ==========
            yield await self._emit_progress(
                CountryResearchStage.COMPLETED,
                f"《{country_profile.country_name}经济与政治概况》生成完成！",
                100,
                {
                    "final_report": reviewed_report,
                    "stats": {
                        "country": country_profile.country_name,
                        "data_sources_used": len(fetched_data),
                        "report_length": len(reviewed_report),
                    }
                },
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=CountryResearchStage.COMPLETED,
                    node_id="completed",
                    title="国别研究报告生成完成",
                    content=f"成功生成《{country_profile.country_name}经济与政治概况》",
                    metadata={
                        "country": country_profile.country_name,
                        "word_count": len(reviewed_report)
                    }
                )
            )

            # Async generator 不需要返回值

        except Exception as e:
            logger.error(f"[ERROR] 国别研究工作流执行失败: {e}")
            yield await self._emit_progress(
                CountryResearchStage.FAILED,
                f"处理失败: {str(e)}",
                -1,
                {"error": str(e)},
                progress_callback
            )
            raise

    async def _emit_progress(
        self,
        stage: CountryResearchStage,
        message: str,
        progress: float,
        data: Dict[str, Any],
        callback: Optional[Callable[[ProgressUpdate], None]],
        thinking_node: Optional[ThinkingChainNode] = None,
    ) -> ProgressUpdate:
        """发送进度更新并返回更新对象"""
        update = ProgressUpdate(
            stage=stage,
            stage_name=stage.value,
            progress=progress,
            message=message,
            data=data,
            thinking_node=thinking_node
        )

        logger.info(f"[进度] {progress}% - {message}")
        if data:
            logger.debug(f"[数据] {json.dumps(data, ensure_ascii=False)[:500]}")

        if callback:
            if asyncio.iscoroutinefunction(callback):
                await callback(update)
            else:
                callback(update)

        return update

    # ========== 数据采集方法 ==========

    async def _fetch_data_sources(
        self,
        country_profile: CountryProfile,
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> Dict[str, str]:
        """采集所有数据源"""
        logger.info(f"[思维链] 开始采集数据，共 {len(country_profile.data_sources)} 个数据源")

        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_FETCHES)

        async def fetch_with_limit(source: DataSourceConfig, index: int) -> tuple[int, str]:
            """带并发限制的数据获取"""
            async with semaphore:
                logger.info(f"[思维链] [{index + 1}/{len(country_profile.data_sources)}] 采集: {source.label}")

                # 实际抓取数据
                content = await self._fetch_single_source(source)

                return (index, content)

        # 并发执行
        results = await asyncio.gather(
            *[fetch_with_limit(ds, i) for i, ds in enumerate(country_profile.data_sources)],
            return_exceptions=True
        )

        # 处理结果
        fetched_data = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"[ERROR] 数据源采集失败: {result}")
                continue
            index, content = result
            source = country_profile.data_sources[index]
            fetched_data[source.label] = content

        logger.info(f"[思维链] 数据采集完成，成功获取 {len(fetched_data)}/{len(country_profile.data_sources)} 个数据源")
        return fetched_data

    async def _fetch_single_source(self, source: DataSourceConfig) -> str:
        """
        获取单个数据源内容

        使用 Firecrawl 进行网页爬取
        """
        logger.info(f"[爬虫] 开始爬取: {source.label} - {source.url}")

        try:
            # 根据数据格式选择爬取方式
            formats = [CrawlFormat.MARKDOWN]

            # 如果是PDF文件，使用特殊处理
            if source.url.lower().endswith('.pdf'):
                # TODO: 实现PDF下载和解析
                logger.warning(f"[爬虫] PDF文件暂不支持直接爬取: {source.url}")
                return f"[PDF文件] {source.url}\n\n(注: PDF文件需要单独下载解析)"

            # 爬取网页
            result = await web_crawler_service.crawl_url(
                url=source.url,
                formats=formats,
                only_main_content=True
            )

            if result.success:
                content_length = len(result.content)
                logger.info(f"[爬虫] 成功爬取: {source.label}, 内容长度: {content_length}")

                # 返回带标签的内容
                return f"""# {source.label}

来源: {source.url}
标题: {result.title}

{result.content}
"""
            else:
                logger.warning(f"[爬虫] 爬取失败: {source.label}, 错误: {result.error}")
                return f"[爬取失败] {source.label}\n来源: {source.url}\n错误: {result.error}"

        except Exception as e:
            logger.error(f"[爬虫] 爬取异常: {source.url}, 错误: {e}")
            return f"[爬取异常] {source.label}\n来源: {source.url}\n异常: {str(e)}"

    # ========== 分析方法 ==========

    async def _analyze_economy(
        self,
        country_profile: CountryProfile,
        fetched_data: Dict[str, str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> str:
        """经济分析"""
        logger.info(f"[思维链] 开始经济分析")

        # 筛选经济相关数据源
        economic_sources = country_profile.get_data_sources_by_type(DataSourceType.TRADING_ECONOMICS)
        economic_sources.extend(country_profile.get_data_sources_by_type(DataSourceType.CENTRAL_BANK))

        prompt = f"""请基于以下数据，分析{country_profile.country_name}的经济状况：

关注以下方面：
1. GDP增速与规模
2. 通胀水平
3. 货币政策（利率变化）
4. 财政状况（债务、赤字）
5. 对外贸易
6. 主要产业结构

可用数据源：
{chr(10).join([f"- {label}" for label in fetched_data.keys() if any(es.label in label for es in economic_sources)])}

请以客观、简洁的公文风格撰写，包含具体数据和时间。"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是专业的经济分析师，擅长撰写公文级经济分析报告。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=120.0
        )

        result = response.choices[0].message.content
        logger.info(f"[思维链] 经济分析完成")
        return result

    async def _analyze_politics(
        self,
        country_profile: CountryProfile,
        fetched_data: Dict[str, str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> str:
        """政治分析"""
        logger.info(f"[思维链] 开始政治分析")

        prompt = f"""请分析{country_profile.country_name}的政治状况：

关注以下方面：
1. 国家元首和政府首脑
2. 政治体制
3. 主要政治动向

请以客观、简洁的公文风格撰写。"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是专业的政治分析师，擅长撰写公文级政治分析报告。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=120.0
        )

        result = response.choices[0].message.content
        logger.info(f"[思维链] 政治分析完成")
        return result

    async def _analyze_diplomacy(
        self,
        country_profile: CountryProfile,
        fetched_data: Dict[str, str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> str:
        """外交关系分析"""
        logger.info(f"[思维链] 开始外交分析")

        # 筛选外交相关数据源
        diplomacy_sources = country_profile.get_data_sources_by_type(DataSourceType.CHINA_MFA)

        prompt = f"""请分析{country_profile.country_name}的对外关系：

重点关注：
1. 对华关系（建交历史、关系定位、经贸数据）
2. 在国际组织中的角色
3. 地区外交政策

可用数据源：
{chr(10).join([f"- {label}" for label in fetched_data.keys() if any(ds.label in label for ds in diplomacy_sources)])}

请以客观、简洁的公文风格撰写。"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是专业的外交分析师，擅长撰写公文级外交关系报告。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=120.0
        )

        result = response.choices[0].message.content
        logger.info(f"[思维链] 外交分析完成")
        return result

    async def _generate_report(
        self,
        country_profile: CountryProfile,
        economic_analysis: str,
        political_analysis: str,
        diplomacy_analysis: str,
        reference_file: Optional[str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> str:
        """生成最终报告"""
        logger.info(f"[思维链] 开始生成最终报告")

        # 获取当前日期作为报告周期
        from datetime import datetime
        current_date = datetime.now()
        report_period = f"{current_date.year}年{current_date.month}月"

        # 使用提示词配置模块获取格式化后的提示词
        from configs.prompts import get_country_report_prompt_v3
        prompt = get_country_report_prompt_v3(
            country_name=country_profile.country_name,
            country_code=country_profile.country_code,
            country_english_name=country_profile.country_name_en,
            report_period=report_period
        )

        # 构建分析内容
        analysis_content = f"""以下是基于各数据源的分析结果：

【经济分析】
{economic_analysis}

【政治分析】
{political_analysis}

【外交关系分析】
{diplomacy_analysis}

请根据以上分析结果，严格按照系统提示词中的模板格式，生成《{country_profile.country_name}经济与政治概况》报告。"""

        response = await self.client.chat.completions.create(
            model=self.GLM_MODEL,  # 使用GLM-5进行长文本生成
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": analysis_content}
            ],
            temperature=0.3,
            max_tokens=98881,
            timeout=300.0
        )

        result = response.choices[0].message.content
        logger.info(f"[思维链] 最终报告生成完成")
        return result

    async def _quality_review(
        self,
        report: str,
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> str:
        """质量审核"""
        logger.info(f"[思维链] 开始质量审核")

        prompt = f"""请审核以下国别研究报告，确保：

1. 结构完整性：包含基本信息、经济、政治三大板块
2. 数据准确性：检查数据是否合理，时间标注是否清晰
3. **分析深度（关键）**：每个段落必须包含深入分析，不能只罗列数据
   - **原因分析**：说明经济现象的原因
   - **影响解读**：说明数据变化的影响
   - **趋势判断**：分析未来走势
   - **关联分析**：说明各指标间的关系
   - 每段应该有3-5句话的分析内容
4. **表格格式（重要）**：
   - 基本信息表必须是4列（项目 | 内容 | 数据来源机构 | 数据来源URL）
   - 核心指标表必须是5列（指标 | 数值（本币/美元） | 时间 | 数据来源机构 | 数据来源URL）
   - "数值（本币/美元）"列格式：[本币数值]/[美元数值]亿美元
   - **URL必须具体可访问**，不能使用"..."或占位符
5. 语言规范性：确保公文风格，避免口语化
6. 格式统一性：标题层次、序号使用规范
7. **数据来源汇总表（最重要）**：
   - 报告末尾必须包含完整的数据来源汇总表
   - 汇总表必须是5列：数据项、数值（本币/美元）、时间、数据来源机构、数据来源URL
   - **URL必须具体可访问**，不能使用"..."或占位符
   - 正文中不得出现[Data Source: ...]或【数据来源：...】标注
8. 双币种展示和URL检查：
   - 所有金额类数据必须同时显示本币和美元，格式：[本币数值]/[美元数值]亿美元
   - 所有表格的URL列必须使用https://完整格式
   - 检查每个URL是否可点击访问

【输出格式要求】
请严格按照以下格式输出：

===REPORT_START===
[这里输出修改后的报告全文，从标题开始]
===REPORT_END===

注意：
- 必须使用 ===REPORT_START=== 和 ===REPORT_END=== 标记包裹报告正文
- 标记之间只包含报告正文，不要包含任何审核意见或说明
- 直接输出修改后的报告全文

【待审核报告】
{report}"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是专业的公文审核专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=98881,
            timeout=180.0
        )

        raw_result = response.choices[0].message.content

        # 提取标记之间的内容
        result = self._extract_report_content(raw_result)

        logger.info(f"[思维链] 质量审核完成")
        return result

    def _extract_report_content(self, raw_output: str) -> str:
        """
        从LLM输出中提取报告正文

        使用通用提取工具函数
        """
        return extract_marked_content(raw_output)


# 单例实例
country_research_service = CountryResearchService()
