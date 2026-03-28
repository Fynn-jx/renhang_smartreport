"""
国家数据源配置示例
展示如何添加新的国家数据源
"""

from configs.country_data_sources import (
    CountryDataSourceRegistry,
    CountryProfile,
    DataSourceConfig,
    DataSourceType
)


def add_custom_country():
    """
    添加自定义国家配置示例

    按照以下步骤添加新国家：
    1. 定义国家基本属性
    2. 添加各类型数据源
    3. 注册到数据源注册中心
    """

    # 示例：添加阿联酋 (United Arab Emirates)
    uae_config = CountryProfile(
        country_code="AE",  # ISO国家代码
        country_name="阿联酋",
        country_name_en="United Arab Emirates",
        region="中东",
        income_level="高收入",
        currency="AED",
        data_sources=[
            # Trading Economics 经济指标
            DataSourceConfig(
                name="GDP增速",
                type=DataSourceType.TRADING_ECONOMICS,
                url="https://zh.tradingeconomics.com/united-arab-emirates/gdp-growth-annual",
                label="GDP增速 (Trading Economics)",
                description="阿联酋GDP年度增长率数据"
            ),
            DataSourceConfig(
                name="通胀率",
                type=DataSourceType.TRADING_ECONOMICS,
                url="https://zh.tradingeconomics.com/united-arab-emirates/inflation-cpi",
                label="通胀率CPI (Trading Economics)",
            ),
            # 央行数据
            DataSourceConfig(
                name="货币政策",
                type=DataSourceType.CENTRAL_BANK,
                url="https://www.centralbank.ae/en/",
                label="货币政策 (阿联酋央行)",
            ),
            # 中国外交部
            DataSourceConfig(
                name="国家概况",
                type=DataSourceType.CHINA_MFA,
                url="https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/fz_677316/1206_677342/1206x0_677344/",
                label="国家概况 (中国外交部)",
            ),
        ]
    )

    # 注册到数据源注册中心
    CountryDataSourceRegistry.register_country(uae_config)

    print(f"已添加国家: {uae_config.country_name} ({uae_config.country_code})")
    print(f"数据源数量: {len(uae_config.data_sources)}")


# ============== 数据源类型说明 ==============

"""
DataSourceType 可用类型：

1. TRADING_ECONOMICS - Trading Economics 经济指标数据
   适用：GDP、通胀、失业率等宏观经济指标

2. CENTRAL_BANK - 央行官网
   适用：货币政策、利率决议、金融报告

3. MINISTRY_FINANCE - 财政部
   适用：财政预算、税收政策、债务数据

4. NEWS_AGENCY - 新闻社
   适用：最新经济新闻、政策解读

5. GOVERNMENT_PORTAL - 政府门户
   适用：官方统计数据、经济概况

6. IMF_WORLD_BANK - IMF/世界银行
   适用：国际金融合作、项目评估

7. CHINA_MFA - 中国外交部
   适用：国家概况、对华关系

8. INVESTING - 英为财情
   适用：国债收益率、股市数据
"""


# ============== 批量添加国家的模板 ==============

def add_multiple_countries():
    """批量添加多个国家的示例"""

    # 示例：添加多个海湾国家
    gulf_countries = [
        CountryProfile(
            country_code="QA",
            country_name="卡塔尔",
            country_name_en="Qatar",
            region="中东",
            income_level="高收入",
            currency="QAR",
            data_sources=[
                DataSourceConfig(
                    name="GDP增速",
                    type=DataSourceType.TRADING_ECONOMICS,
                    url="https://zh.tradingeconomics.com/qatar/gdp-growth-annual",
                    label="GDP增速 (Trading Economics)",
                ),
                # 添加更多数据源...
            ]
        ),
        CountryProfile(
            country_code="KW",
            country_name="科威特",
            country_name_en="Kuwait",
            region="中东",
            income_level="高收入",
            currency="KWD",
            data_sources=[
                DataSourceConfig(
                    name="GDP增速",
                    type=DataSourceType.TRADING_ECONOMICS,
                    url="https://zh.tradingeconomics.com/kuwait/gdp-growth-annual",
                    label="GDP增速 (Trading Economics)",
                ),
                # 添加更多数据源...
            ]
        ),
    ]

    # 批量注册
    for country in gulf_countries:
        CountryDataSourceRegistry.register_country(country)
        print(f"已添加: {country.country_name}")


# ============== 从配置文件加载 ==============

def load_countries_from_json(json_file_path: str):
    """
    从JSON配置文件加载国家数据

    JSON格式示例：
    {
        "countries": [
            {
                "country_code": "AE",
                "country_name": "阿联酋",
                "country_name_en": "United Arab Emirates",
                "region": "中东",
                "income_level": "高收入",
                "currency": "AED",
                "data_sources": [
                    {
                        "name": "GDP增速",
                        "type": "trading_economics",
                        "url": "https://...",
                        "label": "GDP增速"
                    }
                ]
            }
        ]
    }
    """
    import json

    with open(json_file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    for country_data in config.get("countries", []):
        data_sources = []
        for ds_data in country_data.get("data_sources", []):
            ds = DataSourceConfig(
                name=ds_data["name"],
                type=DataSourceType(ds_data["type"]),
                url=ds_data["url"],
                label=ds_data.get("label", ds_data["name"]),
                description=ds_data.get("description", ""),
                enabled=ds_data.get("enabled", True)
            )
            data_sources.append(ds)

        country = CountryProfile(
            country_code=country_data["country_code"],
            country_name=country_data["country_name"],
            country_name_en=country_data["country_name_en"],
            region=country_data["region"],
            income_level=country_data["income_level"],
            currency=country_data.get("currency", ""),
            data_sources=data_sources
        )

        CountryDataSourceRegistry.register_country(country)


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 添加单个国家
    add_custom_country()

    # 批量添加
    # add_multiple_countries()

    # 从JSON加载
    # load_countries_from_json("countries_config.json")

    # 列出所有已注册国家
    print("\n已注册的国家列表：")
    for country in CountryDataSourceRegistry.list_countries():
        print(f"  {country['code']} - {country['name']} ({country['data_source_count']} 个数据源)")
