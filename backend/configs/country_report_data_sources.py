"""
国别报告数据源配置
定义每个数据指标的来源URL和获取方式
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class IndicatorType(Enum):
    """数据指标类型"""
    # 经济指标
    GDP_TOTAL = "gdp_total"  # GDP总值
    GDP_GROWTH = "gdp_growth"  # GDP增速
    GDP_PER_CAPITA = "gdp_per_capita"  # 人均GDP
    INFLATION = "inflation"  # 通胀水平
    UNEMPLOYMENT = "unemployment"  # 失业率
    FISCAL_DEFICIT = "fiscal_deficit"  # 财政赤字
    PUBLIC_DEBT = "public_debt"  # 公共债务
    POLICY_RATE = "policy_rate"  # 基准利率
    FOREIGN_RESERVES = "foreign_reserves"  # 外汇储备
    BOND_YIELD = "bond_yield"  # 国债收益率
    TRADE_VOLUME = "trade_volume"  # 贸易规模
    STOCK_MARKET = "stock_market"  # 股指表现
    EXCHANGE_RATE = "exchange_rate"  # 汇率表现

    # 政治指标
    LEADER = "leader"  # 国家元首
    DIPLOMATIC_CHINA = "diplomatic_china"  # 对华关系
    DIPLOMATIC_GENERAL = "diplomatic_general"  # 对外关系


@dataclass
class IndicatorSource:
    """单个指标的数据源配置"""
    indicator: IndicatorType
    name: str  # 指标中文名
    name_en: str  # 指标英文名
    source_name: str  # 数据源机构名称
    url_template: str  # URL模板，{country_code}会被替换为实际国家代码
    description: str = ""  # 描述
    update_frequency: str = ""  # 更新频率（月度/季度/年度）


# ============== 通用数据源配置 ==============

# 世界银行数据源
WORLD_BANK_SOURCES = [
    IndicatorSource(
        indicator=IndicatorType.GDP_TOTAL,
        name="GDP总值",
        name_en="GDP",
        source_name="世界银行",
        url_template="https://data.worldbank.org/indicator/NY.GDP.MKTP.CD?locations={country_code}",
        description="当前价格GDP",
        update_frequency="年度"
    ),
    IndicatorSource(
        indicator=IndicatorType.GDP_PER_CAPITA,
        name="人均GDP",
        name_en="GDP per Capita",
        source_name="世界银行",
        url_template="https://data.worldbank.org/indicator/NY.GDP.PCAP.CD?locations={country_code}",
        description="人均GDP",
        update_frequency="年度"
    ),
]

# IMF数据源
IMF_SOURCES = [
    IndicatorSource(
        indicator=IndicatorType.PUBLIC_DEBT,
        name="公共债务",
        name_en="General Government Gross Debt",
        source_name="IMF",
        url_template="https://www.imf.org/en/Data",
        description="一般政府总债务占GDP比重",
        update_frequency="年度"
    ),
]


# ============== 国家特定数据源配置 ==============

def get_egypt_sources() -> List[IndicatorSource]:
    """埃及数据源配置"""
    return [
        # GDP相关
        IndicatorSource(
            indicator=IndicatorType.GDP_TOTAL,
            name="GDP总值",
            name_en="GDP",
            source_name="埃及中央公共动员与统计局CAPMAS",
            url_template="https://www.capmas.gov.eg/",
            description="国内生产总值",
            update_frequency="季度"
        ),
        IndicatorSource(
            indicator=IndicatorType.GDP_GROWTH,
            name="GDP增速",
            name_en="GDP Growth",
            source_name="埃及规划与监测部MPM",
            url_template="https://www.mpm.gov.eg/",
            description="GDP同比增长率",
            update_frequency="季度"
        ),
        IndicatorSource(
            indicator=IndicatorType.GDP_PER_CAPITA,
            name="人均GDP",
            name_en="GDP per Capita",
            source_name="世界银行",
            url_template="https://data.worldbank.org/country/EGY",
            description="人均GDP",
            update_frequency="年度"
        ),

        # 通胀相关
        IndicatorSource(
            indicator=IndicatorType.INFLATION,
            name="通胀水平",
            name_en="Inflation Rate",
            source_name="埃及中央公共动员与统计局CAPMAS",
            url_template="https://www.capmas.gov.eg/",
            description="消费者价格指数CPI同比变化",
            update_frequency="月度"
        ),

        # 就业相关
        IndicatorSource(
            indicator=IndicatorType.UNEMPLOYMENT,
            name="失业率",
            name_en="Unemployment Rate",
            source_name="埃及中央公共动员与统计局CAPMAS",
            url_template="https://www.capmas.gov.eg/",
            description="劳动力调查失业率",
            update_frequency="季度"
        ),

        # 财政相关
        IndicatorSource(
            indicator=IndicatorType.FISCAL_DEFICIT,
            name="财政赤字",
            name_en="Fiscal Deficit",
            source_name="埃及财政部",
            url_template="https://www.mof.gov.eg/",
            description="财政赤字占GDP比重",
            update_frequency="年度"
        ),
        IndicatorSource(
            indicator=IndicatorType.PUBLIC_DEBT,
            name="公共债务",
            name_en="Public Debt",
            source_name="埃及财政部",
            url_template="https://www.mof.gov.eg/",
            description="公共债务占GDP比重",
            update_frequency="季度"
        ),

        # 货币政策
        IndicatorSource(
            indicator=IndicatorType.POLICY_RATE,
            name="基准利率",
            name_en="Policy Rate",
            source_name="埃及中央银行CBE",
            url_template="https://www.cbe.org.eg/",
            description="央行隔夜存款利率",
            update_frequency="月度"
        ),
        IndicatorSource(
            indicator=IndicatorType.FOREIGN_RESERVES,
            name="外汇储备",
            name_en="Foreign Reserves",
            source_name="埃及中央银行CBE",
            url_template="https://www.cbe.org.eg/",
            description="净国际储备（含黄金）",
            update_frequency="月度"
        ),
        IndicatorSource(
            indicator=IndicatorType.EXCHANGE_RATE,
            name="汇率表现",
            name_en="Exchange Rate",
            source_name="埃及中央银行CBE",
            url_template="https://www.cbe.org.eg/",
            description="美元/埃及镑汇率",
            update_frequency="日度"
        ),

        # 贸易相关
        IndicatorSource(
            indicator=IndicatorType.TRADE_VOLUME,
            name="贸易规模",
            name_en="Trade Volume",
            source_name="埃及中央公共动员与统计局CAPMAS",
            url_template="https://www.capmas.gov.eg/",
            description="对外贸易总额",
            update_frequency="月度"
        ),

        # 金融市场
        IndicatorSource(
            indicator=IndicatorType.BOND_YIELD,
            name="国债收益率",
            name_en="Bond Yield",
            source_name="埃及财政部",
            url_template="https://www.mof.gov.eg/",
            description="10年期国债收益率",
            update_frequency="日度"
        ),
        IndicatorSource(
            indicator=IndicatorType.STOCK_MARKET,
            name="股指涨幅",
            name_en="Stock Market",
            source_name="埃及交易所EGX",
            url_template="https://www.egx.com.eg/",
            description="EGX30指数年初至今涨跌幅",
            update_frequency="日度"
        ),

        # 政治相关
        IndicatorSource(
            indicator=IndicatorType.DIPLOMATIC_CHINA,
            name="对华关系",
            name_en="Relations with China",
            source_name="中国外交部",
            url_template="https://www.mfa.gov.cn/",
            description="双边关系、贸易额、高层互访",
            update_frequency="不定期"
        ),
    ]


def get_kenya_sources() -> List[IndicatorSource]:
    """肯尼亚数据源配置"""
    return [
        IndicatorSource(
            indicator=IndicatorType.GDP_TOTAL,
            name="GDP总值",
            name_en="GDP",
            source_name="肯尼亚国家统计局KNBS",
            url_template="https://www.knbs.or.ke/",
            description="国内生产总值",
            update_frequency="季度"
        ),
        IndicatorSource(
            indicator=IndicatorType.INFLATION,
            name="通胀水平",
            name_en="Inflation Rate",
            source_name="肯尼亚统计局KNBS",
            url_template="https://www.knbs.or.ke/",
            description="消费者价格指数CPI",
            update_frequency="月度"
        ),
        IndicatorSource(
            indicator=IndicatorType.POLICY_RATE,
            name="基准利率",
            name_en="Central Bank Rate",
            source_name="肯尼亚央行CBK",
            url_template="https://www.centralbank.go.ke/",
            description="央行基准利率",
            update_frequency="月度"
        ),
        IndicatorSource(
            indicator=IndicatorType.DIPLOMATIC_CHINA,
            name="对华关系",
            name_en="Relations with China",
            source_name="中国外交部",
            url_template="https://www.mfa.gov.cn/",
            description="双边关系、贸易额",
            update_frequency="不定期"
        ),
    ]


def get_nigeria_sources() -> List[IndicatorSource]:
    """尼日利亚数据源配置"""
    return [
        IndicatorSource(
            indicator=IndicatorType.GDP_TOTAL,
            name="GDP总值",
            name_en="GDP",
            source_name="尼日利亚国家统计局NBS",
            url_template="https://www.nigerianstat.gov.ng/",
            description="国内生产总值",
            update_frequency="季度"
        ),
        IndicatorSource(
            indicator=IndicatorType.INFLATION,
            name="通胀水平",
            name_en="Inflation Rate",
            source_name="尼日利亚统计局NBS",
            url_template="https://www.nigerianstat.gov.ng/",
            description="消费者价格指数CPI",
            update_frequency="月度"
        ),
        IndicatorSource(
            indicator=IndicatorType.POLICY_RATE,
            name="基准利率",
            name_en="Monetary Policy Rate",
            source_name="尼日利亚央行CBN",
            url_template="https://www.cbn.gov.ng/",
            description="货币政策利率",
            update_frequency="月度"
        ),
        IndicatorSource(
            indicator=IndicatorType.DIPLOMATIC_CHINA,
            name="对华关系",
            name_en="Relations with China",
            source_name="中国外交部",
            url_template="https://www.mfa.gov.cn/",
            description="双边关系、贸易额",
            update_frequency="不定期"
        ),
    ]


# ============== 数据源注册表 ==============

COUNTRY_DATA_SOURCES: Dict[str, List[IndicatorSource]] = {
    "EG": get_egypt_sources(),
    "KE": get_kenya_sources(),
    "NG": get_nigeria_sources(),
}


def get_indicator_source(country_code: str, indicator: IndicatorType) -> Optional[IndicatorSource]:
    """
    获取指定国家的指定指标的数据源配置

    Args:
        country_code: 国家代码（如EG、KE、NG）
        indicator: 指标类型

    Returns:
        指标数据源配置，如果未找到返回None
    """
    sources = COUNTRY_DATA_SOURCES.get(country_code.upper(), [])
    for source in sources:
        if source.indicator == indicator:
            return source
    return None


def get_all_indicator_sources(country_code: str) -> List[IndicatorSource]:
    """
    获取指定国家的所有指标数据源配置

    Args:
        country_code: 国家代码（如EG、KE、NG）

    Returns:
        指标数据源配置列表
    """
    return COUNTRY_DATA_SOURCES.get(country_code.upper(), [])


def format_data_source_citation(country_code: str, indicator: IndicatorType, value: str, date: str) -> str:
    """
    格式化数据来源引用

    Args:
        country_code: 国家代码
        indicator: 指标类型
        value: 数据值
        date: 数据日期

    Returns:
        格式化的数据引用字符串

    示例：
        "4030亿美元（2024年）【数据来源：世界银行，https://data.worldbank.org/indicator/NY.GDP.MKTP.CD】"
    """
    source = get_indicator_source(country_code, indicator)
    if source:
        url = source.url_template.format(country_code=country_code)
        return f"{value}（{date}）【数据来源：{source.source_name}，{url}】"
    else:
        # 如果没有找到特定数据源，返回通用格式
        return f"{value}（{date}）【数据来源：官方统计】"


# ============== 辅助函数 ==============

def get_data_source_url(country_code: str, indicator_name: str) -> str:
    """
    根据国家代码和指标名称获取数据源URL

    Args:
        country_code: 国家代码
        indicator_name: 指标名称（中文或英文）

    Returns:
        数据源URL
    """
    # 首先尝试通过指标英文名匹配
    for indicator in IndicatorType:
        if indicator.name == indicator_name.lower() or indicator.value == indicator_name.lower():
            source = get_indicator_source(country_code, indicator)
            if source:
                return source.url_template.format(country_code=country_code)

    # 如果未找到，返回通用世界银行URL
    return f"https://data.worldbank.org/country/{country_code.lower()}"


if __name__ == "__main__":
    # 测试代码
    print("=== 埃及数据源配置 ===")
    egypt_sources = get_all_indicator_sources("EG")
    for source in egypt_sources:
        print(f"{source.name}: {source.source_name} - {source.url_template}")

    print("\n=== 数据来源引用示例 ===")
    citation = format_data_source_citation("EG", IndicatorType.GDP_TOTAL, "4030亿美元", "2024年")
    print(citation)
