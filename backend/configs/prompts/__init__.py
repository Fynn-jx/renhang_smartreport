"""
提示词配置模块
加载各种AI任务的提示词模板
"""

import os
from pathlib import Path
from typing import Optional

# 提示词目录
PROMPTS_DIR = Path(__file__).parent


def load_prompt_template(prompt_name: str) -> str:
    """
    从文件加载提示词模板

    Args:
        prompt_name: 提示词文件名（不含扩展名）

    Returns:
        提示词字符串
    """
    prompt_file = PROMPTS_DIR / f"{prompt_name}.md"
    if not prompt_file.exists():
        prompt_file = PROMPTS_DIR / f"{prompt_name}.txt"

    if not prompt_file.exists():
        raise FileNotFoundError(f"提示词文件不存在: {prompt_name}")

    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()


def get_country_report_prompt_v3(
    country_name: str,
    country_code: str,
    country_english_name: str,
    report_period: str
) -> str:
    """
    获取国别报告提示词 V3.0

    Args:
        country_name: 国家中文名（如"埃及"）
        country_code: 国家代码（如"EG"）
        country_english_name: 国家英文名（如"Egypt"）
        report_period: 报告周期（如"2025年11月"）

    Returns:
        格式化后的提示词
    """
    try:
        from .country_report_prompt_v3 import get_country_report_prompt
        return get_country_report_prompt(country_name, country_code, country_english_name, report_period)
    except ImportError:
        # 备用提示词
        return f"""请生成{country_name}（{country_english_name}）的国别情况报告（{report_period}）。

报告结构：
1. 基本信息（国土、人口、首都、资源等）
2. 经济概况（GDP、通胀、失业率、利率、外汇储备等）
3. 政治情况（国家元首、对华关系、对外关系）

注意：所有数据必须标注来源，格式：数据（时间）[Data Source: 机构名称, URL]"""


def get_quarterly_report_prompt(
    country_name: str,
    report_date: str
) -> str:
    """
    获取季度报告提示词 V3.0

    Args:
        country_name: 国家中文名（如"埃及"）
        report_date: 报告日期（如"2026年4月"）

    Returns:
        格式化后的提示词
    """
    try:
        from .quarterly_report_prompt_v3 import QUARTERLY_REPORT_SYSTEM_PROMPT_V3
        return QUARTERLY_REPORT_SYSTEM_PROMPT_V3.format(
            country_name=country_name,
            report_date=report_date
        )
    except ImportError:
        # 备用提示词
        return f"""请生成{country_name} {report_date}季度报告。

报告结构：
1. 核心摘要
2. 实体经济运行情况
3. 金融市场运行���况
4. 宏观经济政策
5. 经济前景与风险分析

注意：所有数据必须标注来源，格式：数据（时间）【数据来源：机构名称，URL】"""


# 预定义的提示词常量
try:
    from .country_report_prompt_v3 import COUNTRY_RESEARCH_SYSTEM_PROMPT_V3
except ImportError:
    COUNTRY_RESEARCH_SYSTEM_PROMPT_V3 = """
角色设定：
你是一名政府智库的高级国别研究员。
"""

try:
    from .quarterly_report_prompt_v3 import QUARTERLY_REPORT_SYSTEM_PROMPT_V3
except ImportError:
    QUARTERLY_REPORT_SYSTEM_PROMPT_V3 = """
角色设定：
你是一名央行系统的宏观研究员。
"""


__all__ = [
    "load_prompt_template",
    "get_country_report_prompt_v3",
    "get_quarterly_report_prompt",
    "COUNTRY_RESEARCH_SYSTEM_PROMPT_V3",
]
