"""
LLM输出解析器
提供增强的格式解析、验证和容错能力
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger


class LLMOutputParser:
    """LLM输出解析器，提供格式验证和容错机制"""

    # ==================== 标题提取（JSON格式） ====================

    @staticmethod
    def parse_json_with_retry(
        content: str,
        max_retries: int = 2,
        expected_structure: str = "dict_with_list_values"
    ) -> Tuple[bool, Any, str]:
        """
        解析JSON格式输出，支持重试和容错

        Args:
            content: LLM输出的文本
            max_retries: 最大重试次数
            expected_structure: 期望的结构类型

        Returns:
            (success, parsed_data, error_message)
        """
        for attempt in range(max_retries + 1):
            try:
                # 步骤1: 提取JSON部分
                json_str = LLMOutputParser._extract_json(content)

                # 步骤2: 解析JSON
                parsed = json.loads(json_str)

                # 步骤3: 验证结构
                if expected_structure == "dict_with_list_values":
                    validation_error = LLMOutputParser._validate_title_structure(parsed)
                    if validation_error:
                        return False, None, validation_error

                # 成功
                logger.info(f"[解析器] JSON解析成功 (尝试 {attempt + 1}/{max_retries + 1})")
                return True, parsed, ""

            except json.JSONDecodeError as e:
                logger.warning(f"[解析器] JSON解析失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                if attempt == max_retries:
                    return False, None, f"JSON解析失败: {str(e)}\n原始内容: {content[:500]}"

            except Exception as e:
                logger.error(f"[解析器] 未知错误: {e}")
                return False, None, f"解析错误: {str(e)}"

        return False, None, "超过最大重试次数"

    @staticmethod
    def _extract_json(content: str) -> str:
        """从文本中提取JSON部分"""
        # 尝试1: 直接解析（如果整个内容就是JSON）
        try:
            json.loads(content.strip())
            return content.strip()
        except:
            pass

        # 尝试2: 使用正则提取第一个完整的JSON对象
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json_match.group(0)

        # 尝试3: 提取markdown代码块中的JSON
        code_block_match = re.search(r'```(?:json)?\s*\n([\s\S]*?)\n```', content)
        if code_block_match:
            return code_block_match.group(1).strip()

        # 如果都失败了，返回原始内容
        return content

    @staticmethod
    def _validate_title_structure(data: Any) -> Optional[str]:
        """验证标题结构: {一级标题: [小标题列表]}"""
        if not isinstance(data, dict):
            return "结构错误: 期望字典类型"

        if len(data) == 0:
            return "结构错误: 字典为空"

        for key, value in data.items():
            # 检查键是否为字符串
            if not isinstance(key, str):
                return f"结构错误: 一级标题应为字符串，实际为 {type(key)}"

            # 检查值是否为列表
            if not isinstance(value, list):
                return f"结构错误: 小标题应为列表，实际为 {type(value)} (键: {key})"

            # 检查列表中的元素是否为字符串
            for i, item in enumerate(value):
                if not isinstance(item, str):
                    return f"结构错误: 小标题应为字符串，实际为 {type(item)} (键: {key}, 索引: {i})"

        return None  # 验证通过

    # ==================== 内容整理（分隔符格式） ====================

    @staticmethod
    def parse_sectioned_content(
        content: str,
        expected_sections: List[str],
        delimiter_pattern: str = r'===\s*(.+?)\s*==='
    ) -> Tuple[bool, Dict[str, str], str]:
        """
        解析分段内容（使用分隔符）

        Args:
            content: LLM输出的文本
            expected_sections: 期望的section标题列表
            delimiter_pattern: 分隔符正则模式

        Returns:
            (success, parsed_sections, error_message)
        """
        try:
            # 步骤1: 提取所有section
            sections = {}
            current_section = None
            current_content = []

            lines = content.split('\n')
            for line in lines:
                # 检查是否是分隔符行
                match = re.match(delimiter_pattern, line.strip())
                if match:
                    # 保存前一个section
                    if current_section is not None:
                        sections[current_section] = '\n'.join(current_content).strip()

                    # 开始新的section
                    current_section = match.group(1).strip()
                    current_content = []
                else:
                    if current_section is not None:
                        current_content.append(line)

            # 保存最后一个section
            if current_section is not None:
                sections[current_section] = '\n'.join(current_content).strip()

            # 步骤2: 验证
            if len(sections) == 0:
                return False, {}, "未找到任何section，可能是格式不正确"

            # 步骤3: 检查是否覆盖了所有期望的section
            missing_sections = set(expected_sections) - set(sections.keys())
            if missing_sections:
                logger.warning(f"[解析器] 缺少section: {missing_sections}")

            logger.info(f"[解析器] 成功解析 {len(sections)} 个section")
            return True, sections, ""

        except Exception as e:
            logger.error(f"[解析器] 解析失败: {e}")
            return False, {}, f"解析错误: {str(e)}"

    @staticmethod
    def parse_sectioned_content_flexible(
        content: str,
        expected_sections: List[str]
    ) -> Tuple[bool, Dict[str, str], str]:
        """
        解析分段内容（灵活模式，支持多种分隔符格式）

        支持的分隔符格式:
        - === 标题 ===
        - == 标题 ==
        - ==== 标题 ====
        - 【标题】
        - [标题]
        """
        # 尝试多种分隔符模式
        patterns = [
            r'={3,}\s*(.+?)\s*={3,}',  # === 标题 === 或更多等号
            r'={2}\s*(.+?)\s*={2}',      # == 标题 ==
            r'【(.+?)】',                 # 【标题】
            r'\[(.+?)\]',                 # [标题]
        ]

        for pattern in patterns:
            success, sections, error = LLMOutputParser.parse_sectioned_content(
                content, expected_sections, pattern
            )
            if success:
                logger.info(f"[解析器] 使用模式匹配成功: {pattern}")
                return True, sections, ""

        # 所有模式都失败
        return False, {}, f"无法匹配任何已知的分隔符格式，期望的section: {expected_sections}"

    # ==================== 通用辅助方法 ====================

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """清理多余的空白字符"""
        # 替换多个连续空格为单个空格
        text = re.sub(r' +', ' ', text)
        # 替换多个连续换行为最多两个换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def extract_code_blocks(content: str, language: Optional[str] = None) -> List[str]:
        """提取markdown代码块"""
        if language:
            pattern = f'```{language}\\s*\\n([\\s\\S]*?)\\n```'
        else:
            pattern = r'```(?:\w+)?\s*\n([\s\S]*?)\n```'

        matches = re.findall(pattern, content)
        return matches

    @staticmethod
    def remove_explanatory_text(content: str) -> str:
        """移除常见的说明性文字"""
        # 移除常见的说明性短语
        patterns = [
            r'以下是.*?[:：]\s*',
            r'根据.*?[:：]\s*',
            r'好的.*?[:：]\s*',
            r'我将.*?[:：]\s*',
        ]

        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)

        return content.strip()


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 测试JSON解析
    test_json = """
    根据大纲，我提取了以下标题结构：

    ```json
    {
      "一、宏观经济形势": ["（一）GDP增长", "（二）通胀水平"],
      "二、政策建议": ["（一）财政政策", "（二）货币政策"]
    }
    ```

    希望这对您有帮助！
    """

    success, data, error = LLMOutputParser.parse_json_with_retry(test_json)
    print(f"JSON解析: {success}")
    if success:
        print(f"结果: {data}")
    else:
        print(f"错误: {error}")

    # 测试分段内容解析
    test_sections = """
    === 一、宏观经济形势 ===
    这是关于宏观经济的内容...
    包括GDP增长和通胀水平。

    === 二、政策建议 ===
    这是政策建议的内容...
    """

    success, sections, error = LLMOutputParser.parse_sectioned_content_flexible(
        test_sections,
        ["一、宏观经济形势", "二、政策建议"]
    )
    print(f"\n分段解析: {success}")
    if success:
        print(f"结果: {sections}")
    else:
        print(f"错误: {error}")
