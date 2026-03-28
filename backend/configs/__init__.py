"""
配置模块
"""

from configs.country_data_sources import (
    CountryDataSourceRegistry,
    CountryProfile,
    DataSourceConfig,
    DataSourceType,
    init_country_data_sources,
)

__all__ = [
    "CountryDataSourceRegistry",
    "CountryProfile",
    "DataSourceConfig",
    "DataSourceType",
    "init_country_data_sources",
]
