"""
文本提取工具
用于从LLM输出中提取特定内容
"""

import re
from loguru import logger


def extract_marked_content(raw_output: str, start_marker: str = "===REPORT_START===", end_marker: str = "===REPORT_END===") -> str:
    """
    从LLM输出中提取标记之间的内容

    Args:
        raw_output: LLM原始输出
        start_marker: 开始标记
        end_marker: 结束标记

    Returns:
        提取的内容，如果找不到标记则使用备用策略

    备用策略（按优先级）：
    1. 查找 # 标题
    2. 查找章节标记（一、、第一章、核心摘要等）
    3. 返回原文
    """
    # 策略1: 提取标记之间的内容
    pattern = f'{re.escape(start_marker)}(.*?){re.escape(end_marker)}'
    match = re.search(pattern, raw_output, re.DOTALL)

    if match:
        content = match.group(1).strip()
        logger.info(f"[提取] 成功提取标记内容，长度: {len(content)} 字符")
        return content

    # 策略2: 查找第一个#标题
    title_match = re.search(r'^#\s+.+', raw_output, re.MULTILINE)
    if title_match:
        start_pos = title_match.start()
        content = raw_output[start_pos:].strip()
        logger.info(f"[提取] 使用标题提取，长度: {len(content)} 字符")
        return content

    # 策略3: 查找章节标记
    section_patterns = [
        r'(一、|二、|三、|四、|五、)',  # 中文章节
        r'(第[一二三四五六七八九十]章|Chapter [IVX]+)',  # 中文章节
        r'(核心摘要|【首段|Executive Summary)',  # 摘要标记
    ]

    for pattern in section_patterns:
        section_match = re.search(pattern, raw_output)
        if section_match:
            start_pos = section_match.start()
            content = raw_output[start_pos:].strip()
            logger.info(f"[提取] 使用章节标记提取（{pattern}），长度: {len(content)} 字符")
            return content

    # 策略4: 都找不到，返回原文但记录警告
    logger.warning(f"[提取] 未能使用任何策略提取��容，返回原文（长度: {len(raw_output)} 字符）")
    return raw_output


def clean_llm_output(text: str) -> str:
    """
    清理LLM输出，移除常见的前缀和后缀

    Args:
        text: LLM原始输出

    Returns:
        清理后的文本
    """
    # 移除常见的前缀
    prefixes_to_remove = [
        r'^以下是修改后的报告[：:]\s*',
        r'^报告如下[：:]\s*',
        r'^审核意见[：:]\s*',
        r'^经审核.*?，建议直接采用原文[。,]?\s*',
        r'^以下是.*?：\s*',
    ]

    for prefix in prefixes_to_remove:
        text = re.sub(prefix, '', text, flags=re.MULTILINE)

    # 移除常见的后缀
    suffixes_to_remove = [
        r'\n[修改]*完成[。,]?\s*$',
        r'\n以上[。,]?\s*$',
    ]

    for suffix in suffixes_to_remove:
        text = re.sub(suffix, '', text)

    return text.strip()


def extract_thinking_process(text: str) -> tuple[str, str]:
    """
    分离思维过程和最终输出

    Args:
        text: 包含思维过程和最终输出的文本

    Returns:
        (thinking_process, final_output) 元组
    """
    # 查找思维过程标记
    thinking_patterns = [
        r'<thinking>(.*?)</thinking>',
        r'【思考过程】(.*?)【/思考过程】',
        r'思维链[：:](.*?)(?=\n\n|\n#|\Z)',
    ]

    for pattern in thinking_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            thinking = match.group(1).strip()
            # 移除思维过程部分，获取最终输出
            final = re.sub(pattern, '', text, flags=re.DOTALL).strip()
            return thinking, final

    # 没有找到思维过程标记
    return "", text


if __name__ == "__main__":
    # 测试代码
    test_output = """经审核，该季度报告结构完整、数据准确、语言规范、格式统一，符合央行公文要求。

===REPORT_START===
# 埃及宏观经济与金融运行情况季报（2025年Q3）

埃及经济在经历前期剧烈调整后...
===REPORT_END===

建议直接采用原文，无需修改。"""

    result = extract_marked_content(test_output)
    print("提取结果:")
    print(result[:200])
    print("...")
