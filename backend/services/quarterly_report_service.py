"""
季度报告工作流服务
复用国别研究架构，支持动态国家选择、用户数据源、思维链输出
"""

import json
import asyncio
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
from services.web_crawler_service import web_crawler_service, CrawlFormat


class QuarterlyReportStage(Enum):
    """季度报告工作流阶段"""
    STARTED = "started"                      # 工作流开始
    CONFIG_LOADING = "config_loading"        # 配置加载
    DATA_FETCHING = "data_fetching"          # 数据采集
    MACRO_ANALYSIS = "macro_analysis"        # 宏观经济分析
    FINANCIAL_MARKET_ANALYSIS = "financial_market_analysis"  # 金融市场分析
    POLICY_ANALYSIS = "policy_analysis"      # 政策分析
    RISK_ASSESSMENT = "risk_assessment"      # 风险评估
    REPORT_GENERATION = "report_generation"  # 报告生成
    QUALITY_REVIEW = "quality_review"        # 质量审核
    COMPLETED = "completed"                  # 完成
    FAILED = "failed"                        # 失败


@dataclass
class ThinkingChainNode:
    """思维链节点"""
    stage: QuarterlyReportStage
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
    stage: QuarterlyReportStage
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


class QuarterlyReportService:
    """
    季度报告工作流服务

    基于国别研究架构，专注于生成《国别宏观经济与金融运行情况季报》
    """

    # 模型配置
    DEEPSEEK_MODEL = "Pro/deepseek-ai/DeepSeek-V3"
    GLM_MODEL = "Pro/zai-org/GLM-5"

    # 并发配置
    MAX_CONCURRENT_FETCHES = 5

    # 进度分配
    PROGRESS_CONFIG = {
        QuarterlyReportStage.CONFIG_LOADING: (0, 5),
        QuarterlyReportStage.DATA_FETCHING: (5, 25),
        QuarterlyReportStage.MACRO_ANALYSIS: (25, 40),
        QuarterlyReportStage.FINANCIAL_MARKET_ANALYSIS: (40, 55),
        QuarterlyReportStage.POLICY_ANALYSIS: (55, 70),
        QuarterlyReportStage.RISK_ASSESSMENT: (70, 80),
        QuarterlyReportStage.REPORT_GENERATION: (80, 92),
        QuarterlyReportStage.QUALITY_REVIEW: (92, 98),
    }

    # ============== 提示词模板 ==============

    QUARTERLY_REPORT_SYSTEM_PROMPT = """角色设定：
你是一名供职于中国人民银行系统（PBOC）的金融宏观研究员，专门从事国别宏观经济与金融形势分析。你的任务是将杂乱的抓取数据转化为专业、审慎、供内部决策参考的《国别宏观经济与金融运行情况季报》。

任务说明：
请基于提供的【数据来源文本】，撰写一篇关于 {country_name} 的季度经济报告。

写作总体要求：

行文风格：客观、中性、严谨。严禁情绪化表达，避免使用"本文认为"、"我们发现"等主观词汇。

逻辑结构：必须严格遵循下述的四大板块结构。

段落格式（核心要求）：禁止使用项目符号（如 *、-、●、1.2.3.）。每个小要点必须作为一个独立的自然段，且段落开头必须使用加粗的短句（概括核心结论），随后紧跟数据分析。

术语规范：使用"同比"、"环比"、"个基点（bps）"、"财年"等专业术语。

数据守则：仅使用提供的数据，若数据缺失，则该部分留空或跳过，不得自行编造。对预测性内容需使用"预计"、"可能"、"仍需关注"等审慎辞令。

时效性原则：优先使用最新的数据（2024-2025年），并在数据后标注具体时间（如2024年Q3、2024年10月）。

文章结构模版：

标题： {country_name}季报（报告日期）

【首段：核心摘要】
不加标题序号，直接以一个自然段概括该国当季经济的总体表现（如：增长势头、主要矛盾、市场情绪及信用评级变化）。

一、实体经济运行情况

经济增长与主要行业表现。
[描述GDP增长率、重点行业贡献度、环比/同比变化]

通胀水平与价格走势。
[描述CPI数据、物价波动原因、核心通胀趋势]

就业形势。
[描述失业率数据、劳动力市场结构性特征]

对外贸易与外汇相关情况。
[描述进出口额、贸易逆差/顺差、外汇储备余额及变动因素]

二、金融市场运行情况

股票指数表现。
[主要指数点位、涨跌幅、市场信心分析]

债券市场与利率变化。
[收益率曲线走势、国债表现]

汇率走势与资本流动。
[该国货币对美元汇率区间、升贬值幅度、外汇市场波动情况]

三、宏观经济政策

货币政策操作。
[加息/降息具体操作、基准利率水平、货币政策目标]

财政政策与结构性改革。
[财政赤字率、税收改革、重点扶持计划]

其他重要政策动向。
[最低工资调整、能源价格改革、主权债券发行等]

四、经济前景与风险分析

经济复苏支撑因素。
[国际机构评级、增长预测、正面驱动力]

经济运行面临的风险与挑战。
[至少包含三点风险分析：地缘政治影响、资本外流风险、内部结构性约束（如失业、工业薄弱等）]

执行指令：
现在，请依据提供的资料，撰写{country_name}的季度报告。若资料中缺少某项具体数据，请跳过该细项，保持整体结构的完整性。"""

    def __init__(self):
        """初始化服务"""
        self.api_key = settings.SILICONFLOW_API_KEY
        self.base_url = settings.SILICONFLOW_BASE_URL
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    async def process_quarterly_report(
        self,
        country_code: str,
        reference_file: Optional[str] = None,
        user_sources: Optional[List[Dict[str, str]]] = None,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None,
        db: Optional[AsyncSession] = None,
    ) -> AsyncIterator[ProgressUpdate]:
        """
        执行季度报告工作流

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
                "macro_analysis": "",
                "financial_market_analysis": "",
                "policy_analysis": "",
                "risk_assessment": "",
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
                QuarterlyReportStage.CONFIG_LOADING,
                f"正在加载 {country_code.upper()} 国家配置...",
                2,
                {"step": "配置加载"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=QuarterlyReportStage.CONFIG_LOADING,
                    node_id=f"config_{country_code}",
                    title="国家配置加载",
                    content=f"开始检索 {country_code.upper()} 的数据源配置" +
                           (f"，包含 {len(user_sources)} 个用户补充数据源" if user_sources else ""),
                    metadata={"country_code": country_code, "user_sources_count": len(user_sources) if user_sources else 0}
                )
            )

            yield await self._emit_progress(
                QuarterlyReportStage.CONFIG_LOADING,
                f"配置加载完成：{country_profile.country_name}，共 {len(country_profile.data_sources)} 个数据源",
                5,
                {
                    "country_name": country_profile.country_name,
                    "data_source_count": len(country_profile.data_sources),
                    "region": country_profile.region
                },
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=QuarterlyReportStage.CONFIG_LOADING,
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
                QuarterlyReportStage.DATA_FETCHING,
                "开始采集数据源...",
                6,
                {"step": "数据采集"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=QuarterlyReportStage.DATA_FETCHING,
                    node_id="data_fetching_start",
                    title="数据采集启动",
                    content=f"开始采集 {country_profile.country_name} 的经济金融数据源",
                    metadata={"total_sources": len(country_profile.data_sources)}
                )
            )

            fetched_data = await self._fetch_data_sources(
                country_profile,
                progress_callback
            )
            context["fetched_data"] = fetched_data

            # ========== 阶段3: 宏观经济分析 ==========
            yield await self._emit_progress(
                QuarterlyReportStage.MACRO_ANALYSIS,
                "正在进行宏观经济分析...",
                25,
                {"step": "宏观经济分析"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=QuarterlyReportStage.MACRO_ANALYSIS,
                    node_id="macro_analysis_start",
                    title="宏观经济分析启动",
                    content=f"开始分析 {country_profile.country_name} 的实体经济运行情况，包括GDP、通胀、就业、外贸等核心指标",
                    metadata={"analysis_type": "macro_economic"}
                )
            )

            macro_analysis = await self._analyze_macro_economy(
                country_profile,
                fetched_data,
                progress_callback
            )
            context["macro_analysis"] = macro_analysis

            # ========== 阶段4: 金融市场分析 ==========
            yield await self._emit_progress(
                QuarterlyReportStage.FINANCIAL_MARKET_ANALYSIS,
                "正在进行金融市场分析...",
                40,
                {"step": "金融市场分析"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=QuarterlyReportStage.FINANCIAL_MARKET_ANALYSIS,
                    node_id="financial_market_analysis_start",
                    title="金融市场分析启动",
                    content=f"开始分析 {country_profile.country_name} 的金融市场运行情况，包括股市、债市、汇率等",
                    metadata={"analysis_type": "financial_market"}
                )
            )

            financial_market_analysis = await self._analyze_financial_market(
                country_profile,
                fetched_data,
                progress_callback
            )
            context["financial_market_analysis"] = financial_market_analysis

            # ========== 阶段5: 政策分析 ==========
            yield await self._emit_progress(
                QuarterlyReportStage.POLICY_ANALYSIS,
                "正在进行政策分析...",
                55,
                {"step": "政策分析"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=QuarterlyReportStage.POLICY_ANALYSIS,
                    node_id="policy_analysis_start",
                    title="政策分析启动",
                    content=f"开始分析 {country_profile.country_name} 的宏观经济政策，包括货币政策、财政政策等",
                    metadata={"analysis_type": "policy"}
                )
            )

            policy_analysis = await self._analyze_policy(
                country_profile,
                fetched_data,
                progress_callback
            )
            context["policy_analysis"] = policy_analysis

            # ========== 阶段6: 风险评估 ==========
            yield await self._emit_progress(
                QuarterlyReportStage.RISK_ASSESSMENT,
                "正在进行风险评估...",
                70,
                {"step": "风险评估"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=QuarterlyReportStage.RISK_ASSESSMENT,
                    node_id="risk_assessment_start",
                    title="风险评估启动",
                    content=f"开始评估 {country_profile.country_name} 的经济前景与潜在风险",
                    metadata={"analysis_type": "risk"}
                )
            )

            risk_assessment = await self._assess_risks(
                country_profile,
                fetched_data,
                progress_callback
            )
            context["risk_assessment"] = risk_assessment

            # ========== 阶段7: 报告生成 ==========
            yield await self._emit_progress(
                QuarterlyReportStage.REPORT_GENERATION,
                "正在生成最终报告...",
                80,
                {"step": "报告生成"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=QuarterlyReportStage.REPORT_GENERATION,
                    node_id="report_generation",
                    title="整合分析结果生成报告",
                    content="将宏观经济、金融市场、政策分析和风险评估整合为完整的季度报告",
                    metadata={"analysis_types": ["macro", "financial", "policy", "risk"]}
                )
            )

            final_report = await self._generate_report(
                country_profile,
                macro_analysis,
                financial_market_analysis,
                policy_analysis,
                risk_assessment,
                reference_file,
                progress_callback
            )
            context["final_report"] = final_report

            # ========== 阶段8: 质量审核 ==========
            yield await self._emit_progress(
                QuarterlyReportStage.QUALITY_REVIEW,
                "正在进行质量审核...",
                92,
                {"step": "质量审核"},
                progress_callback,
                thinking_node=ThinkingChainNode(
                    stage=QuarterlyReportStage.QUALITY_REVIEW,
                    node_id="quality_review",
                    title="报告质量审核",
                    content="检查报告的完整性、数据准确性和公文规范性",
                    metadata={"review_criteria": ["completeness", "accuracy", "format"]}
                )
            )

            reviewed_report = await self._quality_review(final_report, progress_callback)

            # ========== 完成 ==========
            yield await self._emit_progress(
                QuarterlyReportStage.COMPLETED,
                f"《{country_profile.country_name}宏观经济与金融运行情况季报》生成完成！",
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
                    stage=QuarterlyReportStage.COMPLETED,
                    node_id="completed",
                    title="季度报告生成完成",
                    content=f"成功生成《{country_profile.country_name}宏观经济与金融运行情况季报》",
                    metadata={
                        "country": country_profile.country_name,
                        "word_count": len(reviewed_report)
                    }
                )
            )

        except Exception as e:
            logger.error(f"[ERROR] 季度报告工作流执行失败: {e}")
            yield await self._emit_progress(
                QuarterlyReportStage.FAILED,
                f"处理失败: {str(e)}",
                -1,
                {"error": str(e)},
                progress_callback
            )
            raise

    async def _emit_progress(
        self,
        stage: QuarterlyReportStage,
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
            formats = [CrawlFormat.MARKDOWN]

            # 如果是PDF文件，使用特殊处理
            if source.url.lower().endswith('.pdf'):
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

    async def _analyze_macro_economy(
        self,
        country_profile: CountryProfile,
        fetched_data: Dict[str, str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> str:
        """宏观经济分析 - 实体经济运行情况"""
        logger.info(f"[思维链] 开始宏观经济分析")

        # 筛选经济相关数据源
        economic_sources = country_profile.get_data_sources_by_type(DataSourceType.TRADING_ECONOMICS)

        prompt = f"""请基于以下数据，分析{country_profile.country_name}的实体经济运行情况：

重点关注以下方面：
1. 经济增长与主要行业表现（GDP增长率、重点行业贡献度、环比/同比变化）
2. 通胀水平与价格走势（CPI数据、物价波动原因、核心通胀趋势）
3. 就业形势（失业率数据、劳动力市场结构性特征）
4. 对外贸易与外汇相关情况（进出口额、贸易逆差/顺差、外汇储备余额及变动因素）

可用数据源：
{chr(10).join([f"- {label}" for label in fetched_data.keys() if any(es.label in label for es in economic_sources)])}

请以客观、简洁的公文风格撰写，包含具体数据和时间。每个小要点作为一个独立的自然段，段落开头使用加粗的短句概括核心结论。"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是专业的宏观经济分析师，擅长撰写央行级别的经济分析报告。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=120.0
        )

        result = response.choices[0].message.content
        logger.info(f"[思维链] 宏观经济分析完成")
        return result

    async def _analyze_financial_market(
        self,
        country_profile: CountryProfile,
        fetched_data: Dict[str, str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> str:
        """金融市场分析"""
        logger.info(f"[思维链] 开始金融市场分析")

        # 筛选金融相关数据源
        financial_sources = country_profile.get_data_sources_by_type(DataSourceType.INVESTING)
        financial_sources.extend(country_profile.get_data_sources_by_type(DataSourceType.TRADING_ECONOMICS))

        prompt = f"""请基于以下数据，分析{country_profile.country_name}的金融市场运行情况：

重点关注以下方面：
1. 股票指数表现（主要指数点位、涨跌幅、市场信心分析）
2. 债券市场与利率变化（收益率曲线走势、国债表现）
3. 汇率走势与资本流动（该国货币对美元汇率区间、升贬值幅度、外汇市场波动情况）

可用数据源：
{chr(10).join([f"- {label}" for label in fetched_data.keys() if any(es.label in label for es in financial_sources)])}

请以客观、简洁的公文风格撰写。每个小要点作为一个独立的自然段，段落开头使用加粗的短句概括核心结论。"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是专业的金融市场分析师，擅长撰写央行级别的金融市场分析报告。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=120.0
        )

        result = response.choices[0].message.content
        logger.info(f"[思维链] 金融市场分析完成")
        return result

    async def _analyze_policy(
        self,
        country_profile: CountryProfile,
        fetched_data: Dict[str, str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> str:
        """政策分析"""
        logger.info(f"[思维链] 开始政策分析")

        # 筛选政策相关数据源
        policy_sources = country_profile.get_data_sources_by_type(DataSourceType.CENTRAL_BANK)
        policy_sources.extend(country_profile.get_data_sources_by_type(DataSourceType.MINISTRY_FINANCE))

        prompt = f"""请基于以下数据，分析{country_profile.country_name}的宏观经济政策：

重点关注以下方面：
1. 货币政策操作（加息/降息具体操作、基准利率水平、货币政策目标）
2. 财政政策与结构性改革（财政赤字率、税收改革、重点扶持计划）
3. 其他重要政策动向（最低工资调整、能源价格改革、主权债券发行等）

可用数据源：
{chr(10).join([f"- {label}" for label in fetched_data.keys() if any(es.label in label for es in policy_sources)])}

请以客观、简洁的公文风格撰写。每个小要点作为一个独立的自然段，段落开头使用加粗的短句概括核心结论。"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是专业的政策分析师，擅长撰写央行级别的政策分析报告。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=120.0
        )

        result = response.choices[0].message.content
        logger.info(f"[思维链] 政策分析完成")
        return result

    async def _assess_risks(
        self,
        country_profile: CountryProfile,
        fetched_data: Dict[str, str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> str:
        """风险评估"""
        logger.info(f"[思维链] 开始风险评估")

        prompt = f"""请基于以下数据，评估{country_profile.country_name}的经济前景与风险：

重点关注以下方面：
1. 经济复苏支撑因素（国际机构评级、增长���测、正面驱动力）
2. 经济运行面临的风险与挑战（至少包含三点：地缘政治影响、资本外流风险、内部结构性约束）

可用数据源：
{chr(10).join([f"- {label}" for label in fetched_data.keys()])}

请以客观、简洁的公文风格撰写。每个小要点作为一个独立的自然段，段落开头使用加粗的短句概括核心结论。对预测性内容需使用"预计"、"可能"、"仍需关注"等审慎辞令。"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是专业的风险评估专家，擅长撰写央行级别的风险评估报告。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=120.0
        )

        result = response.choices[0].message.content
        logger.info(f"[思维链] 风险评估完成")
        return result

    async def _generate_report(
        self,
        country_profile: CountryProfile,
        macro_analysis: str,
        financial_market_analysis: str,
        policy_analysis: str,
        risk_assessment: str,
        reference_file: Optional[str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> str:
        """生成最终报告"""
        logger.info(f"[思维链] 开始生成最终报告")

        prompt = self.QUARTERLY_REPORT_SYSTEM_PROMPT.format(
            country_name=country_profile.country_name
        )

        # 构建分析内容
        analysis_content = f"""以下是基于各数据源的分析结果：

【实体经济运行情况】
{macro_analysis}

【金融市场运行情况】
{financial_market_analysis}

【宏观经济政策】
{policy_analysis}

【经济前景与风险分析】
{risk_assessment}

请根据以上分析结果，严格按照系统提示词中的模板格式，生成《{country_profile.country_name}宏观经济与金融运行情况季报》。"""

        response = await self.client.chat.completions.create(
            model=self.GLM_MODEL,
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

        prompt = f"""请审核以下季度报告，确保：

1. 结构完整性：包含核心摘要、实体经济、金融市场、宏观政策、风险分析五大板块
2. 数据准确性：检查数据是否合理，时间标注是否清晰
3. 语言规范性：确保央行公文风格，避免口语化和主观表述，段落开头使用加粗短句
4. 格式统一性：标题层次、序号使用规范，禁止使用项目符号

如发现问题，请修正；如无问题，直接返回原文。

【待审核报告】
{report}"""

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是专业的央行公文审核专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=98881,
            timeout=180.0
        )

        result = response.choices[0].message.content
        logger.info(f"[思维链] 质量审核完成")
        return result


# 单例实例
quarterly_report_service = QuarterlyReportService()
