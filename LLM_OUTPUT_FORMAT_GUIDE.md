# LLM输出格式准确性保证方案

## 📊 问题分析

### 原有流程的问题

1. **JSON解析脆弱**
   - 使用简单正则 `re.search(r'\{[\s\S]*\}')` 提取JSON
   - 模型输出包含说明文字时容易失败
   - 解析失败直接返回空，没有重试机制

2. **分隔符解析僵化**
   - 只支持 `=== 标题 ===` 格式
   - 模型使用 `==` 或 `=====` 时解析失败
   - 没有格式验证

3. **缺乏容错机制**
   - 没有输出格式验证
   - 没有错误恢复
   - 调试信息不足

## ✅ 改进方案

### 1. 增强的解析器 (`utils/llm_output_parser.py`)

#### 功能特性

```python
class LLMOutputParser:
    # JSON解析（标题提取）
    + parse_json_with_retry()
    + _extract_json()  # 支持3种提取方式
    + _validate_title_structure()  # 结构验证

    # 分段内容解析（内容整理）
    + parse_sectioned_content()
    + parse_sectioned_content_flexible()  # 支持4种分隔符格式
```

#### JSON解析增强

**支持的格式**:
1. 纯JSON: `{"key": "value"}`
2. 正则提取: 从文本中提取 `{...}`
3. Markdown代码块: ```json ... ```

**验证规则**:
- 必须是字典类型
- 键必须是字符串（一级标题）
- 值必须是列表（小标题数组）
- 列表元素必须是字符串

**错误处理**:
```python
success, data, error = LLMOutputParser.parse_json_with_retry(
    content,
    max_retries=2,
    expected_structure="dict_with_list_values"
)

if not success:
    # 详细的错误信息
    raise ValueError(f"标题提取失败: {error}")
```

#### 分段内容解析增强

**支持的分隔符格式**:
1. `=== 标题 ===`
2. `== 标题 ==`
3. `==== 标题 ====` (更多等号)
4. `【标题】`
5. `[标题]`

**灵活模式**:
```python
success, sections, error = LLMOutputParser.parse_sectioned_content_flexible(
    content,
    expected_sections=["一、宏观经济", "二、政策建议"]
)

# 自动尝试所有格式，直到成功
```

### 2. 改进的提示词设计

#### 标题提取提示词

```python
prompt = f"""请分析以下大纲，提取标题结构：

要求：
1. 识别所有一级标题（格式：一、二、三、等）
2. 提取每个一级标题下的所有小标题（二级、三级标题）
3. **以JSON格式输出，不要包含任何其他文字**

输出格式（严格遵守）：
{{
  "一、标题1": ["（一）小标题1", "（二）小标题2"],
  "二、标题2": ["（一）小标题1", "（二）小标题2"]
}}

⚠️ 重要：只输出JSON，不要添加任何说明或解释！

大纲：
{outline}
"""
```

**关键改进**:
- ✅ 明确要求"不要包含任何其他文字"
- ✅ 提供明确的JSON示例
- ✅ 强调格式严格遵守

#### 内容整理提示词

```python
prompt = f"""你是一个专业的内容整理助手。

【任务说明】
你需要将原文中与各个一级标题相关的内容提取并整理在一起。

【原文内容】
{original_text}

【大纲结构】
{outline}

【整理要求】
1. **只提取，不修改**：严格忠实原文，不做任何改写、润色或总结
2. **按一级标题分类**：将原文中与每个一级标题相关的所有内容提取出来
3. **保持完整性**：确保提取的内容片段完整，不截断句意

【输出格式】（严格遵守）
对于每个一级标题，按以下格式输出：

=== 一、[标题名称] ===
[原文中与该一级标题相关的所有内容]

=== 二、[标题名称] ===
[原文中与该一级标题相关的所有内容]

⚠️ 重要：
- 使用 === 标题 === 格式分隔各部分
- 只输出整理后的内容，不要添加任何说明
- 如果某个标题在原文中没有内容，输出: === [标题] ===\n[原文中暂无相关内容]
"""
```

**关键改进**:
- ✅ 明确分隔符格式 `=== 标题 ===`
- ✅ 强调"不要添加任何说明"
- ✅ 提供空内容处理示例

### 3. 温度参数优化

```python
# 需要严格格式的任务使用低温度
response = await client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=0.3,  # 低温度 = 更稳定的输出
    timeout=300.0
)
```

**温度设置建议**:
- 标题提取: `0.3` (需要精确的JSON格式)
- 内容整理: `0.3` (需要严格的分隔符)
- 章节写作: `0.7` (需要创造性)
- 内容整合: `0.7` (需要润色)
- 内容检查: `0.3` (需要客观分析)

### 4. 错误处理和重试

#### 当前实现（无重试）

```python
success, section_dict, error = LLMOutputParser.parse_json_with_retry(
    content,
    max_retries=0,  # 不重试，直接失败
    expected_structure="dict_with_list_values"
)

if not success:
    raise ValueError(f"标题提取失败: {error}")
```

#### 可选：添加重试机制

```python
async def _extract_chapter_titles_with_retry(
    self,
    outline: str,
    max_retries: int = 2
) -> tuple[List[str], Dict[str, List[str]]]:
    """带重试的标题提取"""

    for attempt in range(max_retries + 1):
        try:
            # 调用LLM
            response = await self.client.chat.completions.create(...)

            # 解析
            success, section_dict, error = LLMOutputParser.parse_json_with_retry(
                response.choices[0].message.content,
                max_retries=0
            )

            if success:
                return all_titles, section_dict

            # 如果是最后一次尝试，抛出异常
            if attempt == max_retries:
                raise ValueError(f"标题提取失败（已重试{max_retries}次）: {error}")

            logger.warning(f"标题提取失败，正在重试 ({attempt+1}/{max_retries}): {error}")

        except Exception as e:
            if attempt == max_retries:
                raise
            logger.warning(f"请求失败，正在重试 ({attempt+1}/{max_retries}): {e}")
```

### 5. 调试和监控

#### 结构化日志

```python
get_debug_logger().log_stage(
    stage_name="04_标题提取",
    input_text=outline,
    output_text=json.dumps(section_dict, ensure_ascii=False, indent=2),
    model=self.DEEPSEEK_MODEL,
    prompt=prompt,
    metadata={
        "一级标题数量": len(section_dict),
        "总标题数量": len(all_titles),
        "标题结构": section_dict
    }
)
```

#### 失败记录

```python
if not success:
    get_debug_logger().log_stage(
        stage_name="04_标题提取_失败",
        input_text=outline,
        output_text=f"解析失败: {error}\n原始输出: {content}",
        model=self.DEEPSEEK_MODEL,
        prompt=prompt,
        metadata={"错误": error}
    )
```

## 📈 准确性提升效果

### 预期改进

| 场景 | 改进前 | 改进后 |
|------|--------|--------|
| 模型输出纯JSON | ✅ 100% | ✅ 100% |
| 模型输出带说明文字 | ❌ 60% | ✅ 95% |
| 模型输出在代码块中 | ❌ 70% | ✅ 95% |
| 分隔符格式变化 | ❌ 40% | ✅ 90% |
| 整体成功率 | ~70% | ~95% |

### 关键改进点

1. **多格式支持**: 从1种格式增加到5种格式
2. **结构验证**: 从无验证到完整验证
3. **错误恢复**: 从直接失败到详细错误信息
4. **调试能力**: 从简单日志到结构化调试信息

## 🧪 测试建议

### 测试用例

```python
# 测试1: 纯JSON
test_case_1 = '{"一、标题": ["（一）小标题"]}'

# 测试2: JSON + 说明文字
test_case_2 = '''
根据大纲分析，标题结构如下：

{"一、标题": ["（一）小标题"]}

希望这有帮助！
'''

# 测试3: Markdown代码块
test_case_3 = '''
```json
{
  "一、标题": ["（一）小标题"]
}
```
'''

# 测试4: 分隔符变化
test_case_4 = '''
== 一、标题 ==
内容...

==== 二、标题 ====
内容...
'''
```

## 🎯 最佳实践

1. **使用低温度** (0.3) 用于需要严格格式的任务
2. **明确输出要求** 在提示词中强调格式
3. **提供示例** 在提示词中给出格式示例
4. **结构化日志** 记录每次解析的详细信息
5. **失败快速反馈** 解析失败立即报错，不要继续
6. **定期审查日志** 查看失败案例，优化提示词

## 📝 后续优化方向

1. **添加示例库**: 在提示词中提供更多成功/失败示例
2. **Few-shot学习**: 给模型2-3个正确的输入输出示例
3. **Output Schema**: 使用支持JSON Schema的模型（如GPT-4）
4. **后验证**: 解析后用另一个LLM验证格式正确性
5. **自动修复**: 检测到格式问题时自动重新调用LLM
