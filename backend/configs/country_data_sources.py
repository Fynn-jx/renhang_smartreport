"""
国家数据源配置系统
插拔式设计，支持动态添加/切换国家数据源
预设非洲全部国家
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class DataSourceType(Enum):
    """数据源类��"""
    TRADING_ECONOMICS = "trading_economics"  # Trading Economics 经济数据
    CENTRAL_BANK = "central_bank"            # 央行官网
    MINISTRY_FINANCE = "ministry_finance"    # 财政部
    NEWS_AGENCY = "news_agency"              # 新闻社
    GOVERNMENT_PORTAL = "government_portal"  # 政府门户
    IMF_WORLD_BANK = "imf_world_bank"        # IMF/世界银行
    CHINA_MFA = "china_mfa"                  # 中国外交部
    INVESTING = "investing"                  # 英为财情
    CUSTOM = "custom"                        # 用户自定义补充数据源


@dataclass
class DataSourceConfig:
    """单个数据源配置"""
    name: str                          # 数据源名称
    type: DataSourceType              # 数据源类型
    url: str                           # 数据源URL
    label: str                         # 显示标签
    description: str = ""              # 描述
    enabled: bool = True               # 是否启用
    requires_auth: bool = False        # 是否需要认证
    data_format: str = "markdown"      # 数据格式 (markdown/json/html)


@dataclass
class CountryProfile:
    """国家配置"""
    country_code: str                  # 国家代码 (如 EG, SA, US)
    country_name: str                  # 国家中文名
    country_name_en: str               # 国家英文名
    region: str                        # 区域 (如 中东, 北非, 东南亚)
    income_level: str                  # 收入等级 (高收入/中等收入/低收入)
    currency: str = ""                 # 货币代码
    data_sources: List[DataSourceConfig] = field(default_factory=list)

    def get_data_sources_by_type(self, source_type: DataSourceType) -> List[DataSourceConfig]:
        """按类型获取数据源"""
        return [ds for ds in self.data_sources if ds.type == source_type and ds.enabled]

    def get_all_enabled_urls(self) -> Dict[str, str]:
        """获取所有启用的数据源URL（返回标签->URL的映射）"""
        return {ds.label: ds.url for ds in self.data_sources if ds.enabled}


# ============== 国家数据源配置 ==============

class CountryDataSourceRegistry:
    """国家数据源注册中心"""

    _countries: Dict[str, CountryProfile] = {}

    @classmethod
    def register_country(cls, country: CountryProfile):
        """注册国家配置"""
        cls._countries[country.country_code] = country

    @classmethod
    def get_country(cls, country_code: str) -> Optional[CountryProfile]:
        """获取国家配置"""
        return cls._countries.get(country_code.upper())

    @classmethod
    def list_countries(cls) -> List[Dict[str, Any]]:
        """列出所有已注册国家"""
        return [
            {
                "code": c.country_code,
                "name": c.country_name,
                "name_en": c.country_name_en,
                "region": c.region,
                "income_level": c.income_level,
                "currency": c.currency,
                "data_source_count": len([ds for ds in c.data_sources if ds.enabled])
            }
            for c in cls._countries.values()
        ]

    @classmethod
    def search_by_region(cls, region: str) -> List[CountryProfile]:
        """按区域搜索国家"""
        region_lower = region.lower()
        return [c for c in cls._countries.values() if region_lower in c.region.lower()]

    @classmethod
    def add_supplementary_data_source(
        cls,
        country_code: str,
        name: str,
        url: str,
        label: Optional[str] = None,
        description: str = "",
        data_format: str = "markdown"
    ) -> Optional[CountryProfile]:
        """
        为指定国家添加补充数据源（用户自定义）

        Args:
            country_code: 国家代码
            name: 数据源名称
            url: 数据源URL
            label: 显示标签（可选，默认使用name）
            description: 描述
            data_format: 数据格式 (markdown/json/html)

        Returns:
            更新后的国家配置，如果国家不存在返回None
        """
        country = cls.get_country(country_code)
        if not country:
            logger.warning(f"[数据源] 国家代码不存在: {country_code}")
            return None

        # 检查URL是否已存在
        for ds in country.data_sources:
            if ds.url == url:
                logger.info(f"[数据源] URL已存在，跳过: {url}")
                return country

        # 创建补充数据源
        new_source = DataSourceConfig(
            name=name,
            type=DataSourceType.CUSTOM,
            url=url,
            label=label or f"{name} (用户补充)",
            description=description or f"用户补充的数据源: {name}",
            enabled=True,
            data_format=data_format
        )

        country.data_sources.append(new_source)
        logger.info(f"[数据源] 已为 {country.country_name} 添加补充数据源: {name} ({url})")

        return country

    @classmethod
    def remove_supplementary_data_source(
        cls,
        country_code: str,
        url: str
    ) -> bool:
        """
        移除用户补充的数据源

        Args:
            country_code: 国家代码
            url: 数据源URL

        Returns:
            是否移除成功
        """
        country = cls.get_country(country_code)
        if not country:
            return False

        # 只能移除用户自定义的数据源
        for i, ds in enumerate(country.data_sources):
            if ds.url == url and ds.type == DataSourceType.CUSTOM:
                removed = country.data_sources.pop(i)
                logger.info(f"[数据源] 已移除补充数据源: {removed.name} ({url})")
                return True

        return False

    @classmethod
    def get_country_with_user_sources(
        cls,
        country_code: str,
        user_sources: List[Dict[str, str]]
    ) -> Optional[CountryProfile]:
        """
        获取包含用户补充数据源的国家配置（临时，不修改原配置）

        Args:
            country_code: 国家代码
            user_sources: 用户补充的数据源列表
                [{"name": "数据源名称", "url": "https://..."}, ...]

        Returns:
            包含补充数据源的国家配置副本
        """
        country = cls.get_country(country_code)
        if not country:
            return None

        # 创建数据源副本
        all_sources = list(country.data_sources)

        # 添加用户数据源
        for source in user_sources:
            url = source.get("url", "")
            name = source.get("name", "用户补充数据源")

            # 检查是否已存在
            if not any(ds.url == url for ds in all_sources):
                all_sources.append(DataSourceConfig(
                    name=name,
                    type=DataSourceType.CUSTOM,
                    url=url,
                    label=f"{name} (用户补充)",
                    description=f"用户补充的数据源",
                    enabled=True
                ))

        # 创建新的国家配置副本
        from dataclasses import replace
        return replace(country, data_sources=all_sources)


# ============== 非洲国家配置 ==============

def _create_african_country(
    code: str,
    name: str,
    name_en: str,
    sub_region: str,
    income_level: str,
    currency: str,
    has_trading_economics: bool = True
) -> CountryProfile:
    """
    创建非洲国家基础配置

    Args:
        code: ISO国家代码
        name: 国家中文名
        name_en: 国家英文名
        sub_region: 非洲子区域 (北非/东非/西非/中非/南非)
        income_level: 收入等级
        currency: 货币代码
        has_trading_economics: 是否有Trading Economics数据源
    """
    data_sources = []

    # 大多数非洲国家在Trading Economics有数据
    if has_trading_economics:
        # 将国家名转换为URL格式 (小写，空格替换为连字符)
        url_name = name_en.lower().replace(" ", "-")
        data_sources.extend([
            DataSourceConfig(
                name="GDP增速",
                type=DataSourceType.TRADING_ECONOMICS,
                url=f"https://zh.tradingeconomics.com/{url_name}/gdp-growth-annual",
                label=f"GDP增速 (Trading Economics)",
                description=f"{name}GDP年度增长率数据",
                enabled=True
            ),
            DataSourceConfig(
                name="通胀率",
                type=DataSourceType.TRADING_ECONOMICS,
                url=f"https://zh.tradingeconomics.com/{url_name}/inflation-cpi",
                label=f"通胀率CPI (Trading Economics)",
                enabled=True
            ),
            DataSourceConfig(
                name="失业率",
                type=DataSourceType.TRADING_ECONOMICS,
                url=f"https://zh.tradingeconomics.com/{url_name}/unemployment-rate",
                label=f"失业率 (Trading Economics)",
                enabled=True
            ),
        ])

    return CountryProfile(
        country_code=code,
        country_name=name,
        country_name_en=name_en,
        region=f"非洲, {sub_region}",
        income_level=income_level,
        currency=currency,
        data_sources=data_sources
    )


def _init_egypt_config() -> CountryProfile:
    """
    埃及数据源配置
    唯一一个拥有完整数据源配置的非洲国家
    """
    return CountryProfile(
        country_code="EG",
        country_name="埃及",
        country_name_en="Egypt",
        region="非洲, 北非",
        income_level="中等收入",
        currency="EGP",
        data_sources=[
            # Trading Economics 经济指标
            DataSourceConfig(
                name="GDP增速",
                type=DataSourceType.TRADING_ECONOMICS,
                url="https://zh.tradingeconomics.com/egypt/gdp-growth-annual",
                label="GDP增速 (Trading Economics)",
                description="埃及GDP年度增长率数据"
            ),
            DataSourceConfig(
                name="政府债务",
                type=DataSourceType.TRADING_ECONOMICS,
                url="https://zh.tradingeconomics.com/egypt/government-debt-to-gdp",
                label="政府债务占GDP比重 (Trading Economics)",
            ),
            DataSourceConfig(
                name="财政预算",
                type=DataSourceType.TRADING_ECONOMICS,
                url="https://zh.tradingeconomics.com/egypt/government-budget",
                label="财政预算 (Trading Economics)",
            ),
            DataSourceConfig(
                name="通胀率",
                type=DataSourceType.TRADING_ECONOMICS,
                url="https://zh.tradingeconomics.com/egypt/inflation-cpi",
                label="通胀率CPI (Trading Economics)",
            ),
            DataSourceConfig(
                name="失业率",
                type=DataSourceType.TRADING_ECONOMICS,
                url="https://zh.tradingeconomics.com/egypt/unemployment-rate",
                label="失业率 (Trading Economics)",
            ),
            DataSourceConfig(
                name="出口数据",
                type=DataSourceType.TRADING_ECONOMICS,
                url="https://zh.tradingeconomics.com/egypt/exports",
                label="出口数据 (Trading Economics)",
            ),
            DataSourceConfig(
                name="股市表现",
                type=DataSourceType.TRADING_ECONOMICS,
                url="https://zh.tradingeconomics.com/egypt/stock-market",
                label="股市表现 (Trading Economics)",
            ),
            DataSourceConfig(
                name="汇率",
                type=DataSourceType.TRADING_ECONOMICS,
                url="https://zh.tradingeconomics.com/egypt/currency",
                label="汇率表现 (Trading Economics)",
            ),
            # 英为财情
            DataSourceConfig(
                name="国债收益率",
                type=DataSourceType.INVESTING,
                url="https://cn.investing.com/rates-bonds/egypt-10-year-bond-yield-historical-data",
                label="国债收益率 (英为财情)",
            ),
            # 埃及财政部
            DataSourceConfig(
                name="财政月报",
                type=DataSourceType.MINISTRY_FINANCE,
                url="https://mof.gov.eg/en/archive/monthlyFinancialReport/general/Monthly%20Finance%20Report",
                label="人均GDP/财政月度报告 (埃及财政部)",
            ),
            # 埃及央行
            DataSourceConfig(
                name="利率决议",
                type=DataSourceType.CENTRAL_BANK,
                url="https://www.cbe.org.eg/en/news-publications/news/2025/10/02/14/43/mpc-press-release-2-october-2025",
                label="基准利率决议 (埃及央行)",
            ),
            DataSourceConfig(
                name="货币政策页面",
                type=DataSourceType.CENTRAL_BANK,
                url="https://www.cbe.org.eg/en/monetary-policy",
                label="货币政策页面 (埃及央行)",
            ),
            DataSourceConfig(
                name="货币政策报告PDF",
                type=DataSourceType.CENTRAL_BANK,
                url="https://www.cbe.org.eg/-/media/project/cbe/listing/publication/monetary-policy-report/2025/monetary-policy-report---q3-2025.pdf",
                label="Q3 2025货币政策报告 (埃及央行PDF)",
                data_format="pdf"
            ),
            # 埃及信息服务署 (SIS)
            DataSourceConfig(
                name="经济概况",
                type=DataSourceType.GOVERNMENT_PORTAL,
                url="https://sis.gov.eg/zh/媒体中心/新闻/规划部长介绍2024-2025财年埃及经济表现指标/",
                label="埃及经济概况 (埃及信息服务署SIS)",
            ),
            DataSourceConfig(
                name="贸易逆差",
                type=DataSourceType.GOVERNMENT_PORTAL,
                url="https://sis.gov.eg/en/media-center/news/egypt-trade-deficit-narrows-by-46-in-august/",
                label="贸易逆差收窄新闻 (埃及信息服务署SIS)",
            ),
            # IMF
            DataSourceConfig(
                name="IMF项目",
                type=DataSourceType.IMF_WORLD_BANK,
                url="https://www.imf.org/en/news/articles/2025/03/11/pr-2558-egypt-imf-completes-4th-rev-eff-arrangement-under-rsf-concl-2025-art-iv-consult",
                label="IMF项目第四次评估完成",
            ),
            # 新闻媒体
            DataSourceConfig(
                name="外汇储备新闻",
                type=DataSourceType.NEWS_AGENCY,
                url="https://www.dailynewsegypt.com/2025/11/09/egypts-net-international-reserves-surpass-50bn-for-first-time-in-october-cbe/",
                label="外汇储备新闻 (Daily News Egypt)",
            ),
            DataSourceConfig(
                name="环球杂志报道",
                type=DataSourceType.NEWS_AGENCY,
                url="https://www.xinhuanet.com/globe/2024-05/02/c_1310773186.htm",
                label="《环球》杂志报道",
            ),
            # 中国外交部
            DataSourceConfig(
                name="主要产业元首对外关系",
                type=DataSourceType.CHINA_MFA,
                url="https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/fz_677316/1206_677342/1206x0_677344/",
                label="主要产业/国家元首/对外关系 (中国外交部)",
            ),
            DataSourceConfig(
                name="对华关系",
                type=DataSourceType.CHINA_MFA,
                url="https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/fz_677316/1206_677342/sbgx_677346/",
                label="对华关系 (中国外交部)",
            ),
        ]
    )


# ============== 初始化注册中心 ==============

def init_country_data_sources():
    """
    初始化非洲国家数据源

    共54个非洲主权国家，其中：
    - 埃及 (EG): 拥有完整数据源配置 (18个数据源)
    - 其他国家: 基础框架配置，包含Trading Economics通用数据源
    """

    # ============== 北非国家 ==============
    north_african_countries = [
        # 埃及 - 完整配置
        _init_egypt_config(),

        # 其他北非国家 - 基础配置
        _create_african_country("DZ", "阿尔及利亚", "Algeria", "北非", "中等收入", "DZD"),
        _create_african_country("LY", "利比亚", "Libya", "北非", "中等收入", "LYD"),
        _create_african_country("MA", "摩洛哥", "Morocco", "北非", "中等收入", "MAD"),
        _create_african_country("TN", "突尼斯", "Tunisia", "北非", "中等收入", "TND"),
        _create_african_country("SD", "苏丹", "Sudan", "北非", "低收入", "SDG", has_trading_economics=False),
        _create_african_country("EH", "西撒哈拉", "Western Sahara", "北非", "低收入", "", has_trading_economics=False),
    ]

    # ============== 东非国家 ==============
    east_african_countries = [
        _create_african_country("ET", "埃塞俄比亚", "Ethiopia", "东非", "低收入", "ETB"),
        _create_african_country("KE", "肯尼亚", "Kenya", "东非", "中等收入", "KES"),
        _create_african_country("TZ", "坦桑尼亚", "Tanzania", "东非", "低收入", "TZS"),
        _create_african_country("UG", "乌干达", "Uganda", "东非", "低收入", "UGX"),
        _create_african_country("RW", "卢旺达", "Rwanda", "东非", "低收入", "RWF"),
        _create_african_country("BI", "布隆迪", "Burundi", "东非", "低收入", "BIF", has_trading_economics=False),
        _create_african_country("SO", "索马里", "Somalia", "东非", "低收入", "SOS", has_trading_economics=False),
        _create_african_country("DJ", "吉布提", "Djibouti", "东非", "中等收入", "DJF"),
        _create_african_country("ER", "厄立特里亚", "Eritrea", "东非", "低收入", "ERN", has_trading_economics=False),
        _create_african_country("SC", "塞舌尔", "Seychelles", "东非", "高收入", "SCR"),
        _create_african_country("MU", "毛里求斯", "Mauritius", "东非", "中等收入", "MUR"),
        _create_african_country("KM", "科摩罗", "Comoros", "东非", "低收入", "KMF", has_trading_economics=False),
        _create_african_country("MG", "马达加斯加", "Madagascar", "东非", "低收入", "MGA"),
        _create_african_country("MZ", "莫桑比克", "Mozambique", "东非", "低收入", "MZN"),
    ]

    # ============== 西非国家 ==============
    west_african_countries = [
        _create_african_country("NG", "尼日利亚", "Nigeria", "西非", "中等收入", "NGN"),
        _create_african_country("GH", "加纳", "Ghana", "西非", "中等收入", "GHS"),
        _create_african_country("CI", "科特迪瓦", "Ivory Coast", "西非", "低收入", "XOF"),
        _create_african_country("SN", "塞内加尔", "Senegal", "西非", "低收入", "XOF"),
        _create_african_country("ML", "马里", "Mali", "西非", "低收入", "XOF", has_trading_economics=False),
        _create_african_country("BF", "布基纳法索", "Burkina Faso", "西非", "低收入", "XOF", has_trading_economics=False),
        _create_african_country("NE", "尼日尔", "Niger", "西非", "低收入", "XOF", has_trading_economics=False),
        _create_african_country("GN", "几内亚", "Guinea", "西非", "低收入", "GNF", has_trading_economics=False),
        _create_african_country("SL", "塞拉利昂", "Sierra Leone", "西非", "低收入", "SLL"),
        _create_african_country("LR", "利比里亚", "Liberia", "西非", "低收入", "LRD", has_trading_economics=False),
        _create_african_country("CF", "中非", "Central African Republic", "中非", "低收入", "XAF", has_trading_economics=False),  # 通常归中非，但也属西非经济共同体
        _create_african_country("CM", "喀麦隆", "Cameroon", "中非", "中等收入", "XAF"),
        _create_african_country("TD", "乍得", "Chad", "中非", "低收入", "XAF", has_trading_economics=False),
        _create_african_country("CG", "刚果(布)", "Republic of the Congo", "中非", "低收入", "XAF"),
        _create_african_country("GA", "加蓬", "Gabon", "中非", "中等收入", "XAF"),
        _create_african_country("GQ", "赤道几内亚", "Equatorial Guinea", "中非", "中等收入", "XAF", has_trading_economics=False),
        _create_african_country("ST", "圣多美和普林西比", "Sao Tome and Principe", "中非", "低收入", "STN", has_trading_economics=False),
        _create_african_country("AO", "安哥拉", "Angola", "中非", "中等收入", "AOA"),
        _create_african_country("CD", "刚果(金)", "Democratic Republic of the Congo", "中非", "低收入", "CDF"),
    ]

    # ============== 南非国家 ==============
    southern_african_countries = [
        _create_african_country("ZA", "南非", "South Africa", "南非", "中等收入", "ZAR"),
        _create_african_country("NA", "纳米比亚", "Namibia", "南非", "中等收入", "NAD"),
        _create_african_country("BW", "博茨瓦纳", "Botswana", "南非", "中等收入", "BWP"),
        _create_african_country("ZW", "津巴布韦", "Zimbabwe", "南非", "低收入", "ZWL"),
        _create_african_country("ZM", "赞比亚", "Zambia", "南非", "低收入", "ZMW"),
        _create_african_country("MW", "马拉维", "Malawi", "南非", "低收入", "MWK"),
        _create_african_country("MO", "莫桑比克", "Mozambique", "南非", "低收入", "MZN"),  # 已在东非列出
        _create_african_country("LS", "莱索托", "Lesotho", "南非", "低收入", "LSL"),
        _create_african_country("SZ", "斯威士兰", "Eswatini", "南非", "低收入", "SZL"),
    ]

    # 合并所有非洲国家
    all_african_countries = (
        north_african_countries +
        east_african_countries +
        west_african_countries +
        southern_african_countries
    )

    # 去重（按国家代码）
    unique_countries = {}
    for country in all_african_countries:
        if country.country_code not in unique_countries:
            unique_countries[country.country_code] = country

    # 注册所有国家
    for country in unique_countries.values():
        CountryDataSourceRegistry.register_country(country)

    logger.info(f"""
    ============== 非洲国家数据源初始化完成 ==============
    总计: {len(unique_countries)} 个国家

    北非: {len([c for c in unique_countries.values() if '北非' in c.region])} 个
    东非: {len([c for c in unique_countries.values() if '东非' in c.region])} 个
    西非: {len([c for c in unique_countries.values() if '西非' in c.region])} 个
    中非: {len([c for c in unique_countries.values() if '中非' in c.region])} 个
    南非: {len([c for c in unique_countries.values() if '南非' in c.region])} 个

    完整数据源配置: 仅埃及 (EG) - 18个数据源
    基础数据源配置: 其他 {len(unique_countries)-1} 个国家 - 3个通用数据源
    ===================================================
    """)

    return CountryDataSourceRegistry()


# 自动初始化
init_country_data_sources()
