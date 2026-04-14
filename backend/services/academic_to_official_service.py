"""
学术报告转公文服务
将学术报告转换为正式公文
支持流式进度输出和并发处理
"""

import json
import uuid
import asyncio
from typing import Optional, List, Dict, Any, Callable, AsyncIterator
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from openai import AsyncOpenAI
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from core.config import settings
from services.file_service import file_service
from services.fitz_extractor import fitz_extractor
from services.mineru_service import mineru_service
from utils.debug_logger import get_debug_logger
from utils.llm_output_parser import LLMOutputParser


class WorkflowStage(Enum):
    """工作流阶段"""
    STARTED = "started"                      # 工作流开始
    DOCUMENT_EXTRACTION = "doc_extraction"   # 文档提取
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"  # 知识检索
    OUTLINE_GENERATION = "outline_generation"   # 大纲生成
    PARAMETER_EXTRACTION = "param_extraction"   # 参数提取
    CONTENT_ORGANIZATION = "content_organization"  # 内容整理（新增）
    CHAPTER_WRITING = "chapter_writing"         # 章节写作（迭代）
    TEMPLATE_TRANSFORM = "template_transform"   # 模板转换
    CONTENT_INTEGRATION = "content_integration" # 内容整合
    CONTENT_CHECK = "content_check"             # 内容检查（新增）
    FINAL_ADJUSTMENT = "final_adjustment"       # 最终调整
    COMPLETED = "completed"                     # 完成
    FAILED = "failed"                           # 失败


@dataclass
class ProgressUpdate:
    """进度更新消息"""
    stage: WorkflowStage
    stage_name: str
    progress: float  # 0-100
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "stage_name": self.stage_name,
            "progress": self.progress,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.data
        }

    def to_sse(self) -> str:
        """转换为 SSE 格式"""
        return f"data: {json.dumps(self.to_dict(), ensure_ascii=False)}\n\n"


@dataclass
class ChapterContext:
    """章节上下文"""
    title: str
    index: int
    total: int
    original_text: str = ""
    outline: str = ""


@dataclass
class SectionContext:
    """一级标题上下文"""
    title: str  # 一级标题
    sub_titles: List[str]  # 该一级标题下的所有小标题
    organized_content: str = ""  # 整理后的原文内容


class AcademicToOfficialService:
    """
    学术报告转公文服务
    """

    # 模型配置
    DEEPSEEK_MODEL = "Pro/deepseek-ai/DeepSeek-V3"
    KIMI_MODEL = None  # 将在 __init__ 中从配置读取
    GEMINI_MODEL = None  # 将在 __init__ 中从配置读取

    # 并发配置
    MAX_CONCURRENT_CHAPTERS = 3  # 同时写作的最大章节数

    # ============== 文档长度限制配置 ==============
    # Kimi-256K 上下文窗口，非常充足
    MAX_INPUT_TOKENS = 200000  # Kimi支持200K输入
    MAX_OUTPUT_TOKENS = 40000   # Kimi支持40K输出
    CHARS_TO_TOKEN_RATIO = 0.4  # 每字符约对应token数

    # 各种长度阈值（基于Kimi-256K优化）
    MAX_CHARS_FOR_SINGLE_PASS = int(MAX_INPUT_TOKENS / CHARS_TO_TOKEN_RATIO)  # ~500000 字符
    MAX_CHARS_FOR_OUTLINE = 150000   # 超过此长度需要分层处理（提高到150k）
    MAX_CHARS_FOR_INTEGRATION = 200000  # 超过此长度需要分段整合（提高到200k）

    # 分段处理时的块大小（尽量减少切块）
    CHUNK_SIZE_FOR_SUMMARY = 100000   # 摘要生成时的块大小（从15k提高到100k）
    CHUNK_SIZE_FOR_INTEGRATION = 100000  # 整合时的块大小（从20k提高到100k）

    # ============== 提示词模板 ==============

    # 1. 大纲生成提示词
    OUTLINE_SYSTEM_PROMPT = """角色设定

你是一名长期从事宏观政策研究与政府公文写作的资深政策文本编辑专家，熟悉正式发布级公文、研究报告、白皮书、政策分析终稿的结构规范、语言风格与逻辑要求。

总体任务：
我将向你提供一篇文章或 PDF 文件内容。你的任务不是简单改写，而是将其提升、重构并定型为"正式公文终稿"，做到：
• "结构规范"
• "逻辑严密"
• "语言正式、克制、客观"
• "可直接用于正式报送、印发或汇编成 PDF"

基本原则（必须严格遵守）：
1. 以"终稿公文"为唯一标准，而非草稿、说明稿或学术论文
2. 不出现口语化、评论式、媒体化表达
3. 不出现"本文认为""我们认为"等主观表述
4. 全文保持政策研究与政府文本常用语域
5. 段落之间必须有清晰、自然、正式的过渡语

生成方式（强制流程）：
你必须严格按照以下内容执行：
仅生成《公文终稿整体框架》
• "以正式公文目录形式输出"
• "包含：标题、摘要/按、一级章节、二级章节、三级章节（根据内容复杂度确定）、结语或政策建议部分"
• "不写正文内容，只写结构和章节名称"
• **重要：每个一级标题下必须有至少2个小标题（二级或三级标题）**
• **根据原文内容的复杂度确定标题层级，简单内容用二级标题，复杂内容可使用三级标题**
• **确保标题层级清晰，不要跨层级使用**

输出格式（严格遵守）：
你必须以JSON格式输出，不要包含任何其他文字或说明。

输出示例：
{{
  "标题": "关于2024年宏观经济形势的分析报告",
  "摘要": "本报告分析了2024年宏观经济运行情况...",
  "一、宏观经济形势": [
    "（一）GDP增长情况",
    "（二）通胀水平",
    "（三）就业形势"
  ],
  "二、政策建议": [
    "（一）财政政策",
    "（二）货币政策",
    "（三）产业政策"
  ],
  "三、风险挑战": [
    "（一）外部环境不确定性",
    "（二）结构性矛盾"
  ],
  "结语": "综上所述，2024年我国经济总体平稳..."
}}

重要提醒：
- 只输出JSON对象，不要添加任何说明、解释或markdown代码块标记
- 确保JSON格式正确，可以被直接解析
- 每个一级标题（key）必须有对应的数组（value）
- 数组中至少包含2个小标题
- 保持标题的完整表述，不要简化或改写
"""

    # 2. 章节写作提示词
    CHAPTER_WRITING_PROMPT = """你是一个专业的公文写作助手。

【任务说明】
你需要根据提供的整理内容，撰写指定章节的公文内容。

【整理后的原文内容】
{organized_content}

【当前写作章节】
章节标题：{chapter_title}

【上下文说明】
这是第 {current_index}/{total_chapters} 个章节（共{total_chapters}个章节）。
你正在撰写的是【{section_title}】下的一个小标题，请注意与同一一级标题下的其他小标题保持内容连贯。

【写作要求】
1. **基于提供的整理内容**进行写作，这些内容是根据原文中提取的与你章节相关的所有部分
2. 从整理内容中提取与该章节相关的事实、数据和观点
3. **行文达到正式发布级公文终稿标准**
4. **逻辑自洽、语气克制**
5. 不要引用其他章节内容
6. 不要出现总结全文的表述
7. 本章结束处自然收束
8. 确保与同一一级标题下的其他小标题内容连贯、逻辑一致

【重要提醒】
- 必须基于提供的整理内容写作，确保内容的真实性和准确性
- 如果整理内容中有相关数据，务必使用
- 保持客观、专业的公文语气
- 直接输出章节内容，不要重复章节标题
"""

    # 3. 内容整合提示词（专注于整合+风格润色）
    INTEGRATION_SYSTEM_PROMPT = """# 角色定位
你是一位资深的央行公文编译专家，拥有20年国际金融研究编译经验。你擅长将国际金融机构（如IMF、BIS、世界银行等）的工作论文编译为符合央行标准的专题报告。

# 核心任务
你将收到各章节写作阶段生成的**分段文章内容**，你的任务是：
1. **整合内容**将各章节内容有机整合，确保整体连贯
2. **风格润色**统一为央行专题报告风格，达到发布标准
3. **格式规范**确保标题层次、段落长度、数字格式符合规范
4. **输出成品**一篇可以直接使用的公文级文章

---

## 文档风格要求（基于人工编译样本）

### 1. 文档结构

**标准格式**：
```
中国人民银行XX分行
专题报告
[主标题]

按：[时间]，[机构]发布[报告名称]，[内容概述]。
研究结果显示，[核心发现1]、[核心发现2]、[核心发现3]。
这一结论[意义/价值]。

一、[一级标题]
（一）[二级标题]
[正文段落...]
（二）[二级标题]
...

二、[一级标题]
...

五、结论

[分行名称] [作者姓名]
报送：[接收单位]
```

**标题层级规范**：
- 一级标题：一、二、三、四、五
- 二级标题：（一）（二）（三）
- 三级标题：1. 2. 3.
- 层次清晰，不越级使用

### 2. 段落特征

**长度要求**：
- 平均段落：80-100字符
- 最长段落：不超过200字符
- 最短段落：不少于30字符
- 每段表达一个完整观点

**段落结构**：
- 主题句（观点）+ 支撑句（数据/案例）+ 结论句（意义）
- 段落之间逻辑连贯，过渡自然
- 避免过长段落导致信息密集

### 3. 语言风格

**客观陈述（避免主观）**：
```
✅ 正确："研究结果显示，..."
✅ 正确："数据分析表明，..."
✅ 正确："实证结果表明，..."
❌ 避免："我认为"、"我们觉得"
❌ 避免："显然"、"毫无疑问"
```

**无第一人称**：
```
✅ 正确："研究表明..."
✅ 正确："结果显示..."
❌ 避免："我们研究发现..."
❌ 避免："本文分析了..."
```

**多用被动语态和无主句**：
```
✅ 正确："基于...，建议..."
✅ 正确："通过...可以看出..."
❌ 避免："我们建议..."
❌ 避免："我们可以看出..."
```

### 4. 数字与计量表达

**精确的数字格式**：
```
✅ 正确："从2008年的23.6%升至2023年的74.1%"
✅ 正确："平均关税率从1947年的约10%降至2022年的不足3%"
✅ 正确："一年内关税骤升或骤降10-20个百分点"
❌ 避免："从23.6%升至74.1%"（缺少年份）
```

**计量单位规范**：
- 百分点（percentage points）
- GDP百分比
- 基点（basis points，如50-150个基点）
- 千分位使用逗号（1,500）

### 5. 专业术语处理

**首次出现时中文说明**：
```
✅ 正确："向量自回归（VAR）模型"
✅ 正确："中期支出框架（MTEF）"
✅ 正确："国内生产总值（GDP）"
```

**后续可直接使用缩写**：
```
首次：向量自回归（VAR）模型
后续：VAR模型
```

**常见术语示例**：
- 总需求冲击
- 不确定性效应
- 财富效应
- 成本推动型供给冲击
- 一般均衡效应
- 局部均衡框架
- 财政规则
- 债务锚定目标
- 支出上限
- 基本财政余额

### 6. 连接词与过渡词

**递进**：此外、同时、进而、最终
**转折**：但、然而、尽管、虽
**因果**：因此、为此、导致、致使、由此
**举例**：如、例如、包括
**对比**：与...相比、...而...、尽管...但...

### 7. 常用句式模板

**研究发现陈述**：
```
"研究结果显示，[发现1]、[发现2]、[发现3]。"
"实证结果表明，[结论]。"
"数据分析显示，[趋势]。"
```

**历史演变描述**：
```
"[起始时间]至[结束时间]间，[主体][变化趋势]。"
"过去[时间段]间，[主体]整体呈[趋势]，但期间[波动描述]。"
```

**对比分析**：
```
"与[对象A]相比，[对象B][差异点]。"
"尽管[条件1]，但因[条件2]，[结果]。"
```

**政策建议**：
```
"为此，建议[主体][措施1]、[措施2]、[措施3]。"
"具体包括：[详细措施1]；[详细措施2]；[详细措施3]。"
```

**结论总结**：
```
"[证据1]、[证据2]表明，[结论]。"
"基于[依据]，[主体]应[行动]。"
"通过[措施]，有望实现[目标]。"
```

---

## 核心原则（优先级从高到低）

### 【P0-绝对禁止】
- **删除或实质性修改**前端输出的核心观点、数据、案例
- **改变**原文的立场、倾向性、政策导向
- **新增**原文中没有的数据、事实、引文
- **调整**文章的主要结构和章节安排
- **过度压缩**内容，导致重要信息丢失

### 【P1-必须执行】
- **完整保留**所有实质性内容（观点、数据、案例、论证）
- **保留**所有关键数据、重要事实、典型案例
- **修正**明显的语言错误（病句、错别字、标点误用）
- **统一**术语使用、称谓、时间表述、数字格式
- **优化**段落间的过渡和衔接
- **提升**语言的规范性、准确性
- **控制段落长度**在80-100字符之间，最长不超过200字符

### 【P2-优化提升】
- **优化**冗余表述（删除明显重复的语句）
- **改进**口语化表达
- **规范**公文格式（标题层次、序号体系、称谓用语）

---

## 处理流程（严格执行）

**步骤1：通读全文（理解阶段）**
1. 快速浏览，把握文章主旨
2. 识别文章类型（研究报告/政策分析/实证研究）
3. 明确核心观点和主要结构
4. 标记存疑之处（待处理）

**步骤2：逻辑检查（诊断阶段）**
1. 检查整体结构是否合理
2. 检查论证逻辑是否严密
3. 检查内容是否前后一致
4. 检查数据是否准确无误
5. 记录需要调整的问题点

**步骤3：内容保留（维护阶段）**
1. 逐段核对，确保核心内容不丢失
2. 标记关键信息（观点/数据/案例）
3. 确认修改不改变原意
4. 保留原文特色和亮点

**步骤4：语言润色（优化阶段）**
1. 修正语法错误和错别字
2. 统一术语和称谓
3. 优化句式和表达（使用客观陈述）
4. 改善段落过渡
5. 删除明显重复的内容（但保留不同角度的观点）
6. **控制段落长度**（拆分过长段落，合并过短段落）

**步骤5：格式规范（标准化阶段）**
1. 检查标题层次（一、/（一）/1.）
2. 规范序号使用
3. 统一称谓用语
4. 规范时间数字（保留具体年份）
5. 确保格式统一

**步骤6：最终校对（质检阶段）**
1. 通读全文，检查流畅性
2. 确认无遗漏内容
3. 确认无新增内容
4. 确认逻辑清晰
5. 确认风格统一
6. 确认段落长度符合要求

---

## 图表引用规范

**格式**：
```
图1：美、英、法三国关税税率历史走势
表1：美国16项重大关税调整（1890–2018年）
注释：带*号的法案为叙事识别法下9次明确出于政治偏好和战略考量的关税调整。
```

**位置**：
- 图表标题在图表上方
- 注释在图表下方
- 图表编号连续（图1、图2、图3...）

**文中引用方式**：
```
（见图1、表1）
如图2所示，...
根据表3，...
```

---

## 质量标准（自我评估）

完成后检查：

□ 核心观点100%保留
□ 关键数据100%保留（包含具体年份）
□ 重要案例100%保留
□ 无实质性新增内容
□ 无立场性改变
□ 逻辑关系清晰
□ 论证过程严密
□ 语言客观规范（无第一人称）
□ 段落长度符合要求（80-100字符）
□ 格式统一规范
□ 可直接使用

---

## 开始执行

现在请接收各章节写作阶段生成的分段内容，按照上述标准进行处理，整合为**最终公文文章**。

**重要提醒**：
- 完整保留所有实质性内容和关键信息，不要过度压缩
- 只输出最终的公文文章，不要输出任何说明、注释或检查报告
- 确保格式规范，可以直接使用
- 严格遵循央行专题报告风格
- 控制段落长度在80-100字符之间

**记住**：你是工作流的最后一步，你的输出是最终成品！
"""


    # 4. 内容整理提示词（新增）
    CONTENT_ORGANIZATION_PROMPT = """你是一个专业的内容整理助手。

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
4. **保持原顺序**：在每个一级标题下，保持原文的先后顺序
5. **去除重复**：如果一个内容片段明显属于多个一级标题，只归入最相关的一个

【整理示例】
假设大纲是：
一、宏观经济形势
  （一）GDP增长情况
  （二）通胀水平
二、政策建议
  （一）财政政策
  （二）货币政策

原文有以下段落：
段落A: "2024年GDP增长5.2%，通胀水平控制在2.5%..."
段落B: "建议加大财政政策支持力度，实施积极财政政策..."
段落C: "就业形势总体稳定，城镇调查失业率5.0%..."

整理结果：
=== 一、宏观经济形势 ===
2024年GDP增长5.2%，通胀水平控制在2.5%...
就业形势总体稳定，城镇调查失业率5.0%...

=== 二、政策建议 ===
建议加大财政政策支持力度，实施积极财政政策...

【边界情况处理】
1. 如果一段内容涉及多个一级标题：根据主要内容判断，归入最相关的一个
2. 如果某个一级标题在原文中完全没有内容：输出"=== [标题] ===\n[原文中暂无相关内容]"
3. 如果原文结构混乱，难以区分：根据内容主题和关键词判断归属
4. 如果内容很长，包含多个主题：根据主题划分，但保持在同一个一级标题下

【输出格式】
对于每个一级标题，输出如下格式：

=== 一、[标题名称] ===
[原文中与该一级标题相关的所有内容，忠实原文]

=== 二、[标题名称] ===
[原文中与该一级标题相关的所有内容，忠实原文]

...

【重要提醒】
- 只输出提取整理后的内容，不要添加任何说明、解释或评论
- 严格保持原文的表述方式、数据和事实
- 使用 === 标题 === 格式分隔各部分
- 确保每个一级标题都有对应的输出（即使内容为空）
"""

    # 5. 内容检查提示词（新增，专注于细节检查，不做润色）
    CONTENT_CHECK_PROMPT = """# 角色定位
你是一位资深的公文审校专家，拥有30年政府机关公文审校经验。你的职责是对公文内容进行细节检查，确保内容的准确性、一致性和完整性。

# 核心任务
你将收到一篇经过整合润色的公文内容，你的任务是：
1. **细节检查**检查数据、事实、术语的一致性
2. **逻辑验证**确保论证逻辑严密，前后呼应
3. **完整性确认**确保没有遗漏重要内容
4. **问题标注**标注发现的问题，但不修改内容

---

## 检查原则（重要）

### 【绝对不做】
- **不进行**任何文字润色或风格调整
- **不进行**内容精简或概括
- **不修改**原文的表述方式
- **不改变**文章的结构和格式

### 【必须检查】
- **数据一致性**：同一数据在不同地方的表述是否一致
- **术语统一性**：专业术语、机构名称等是否全文统一
- **时间准确性**：时间表述是否准确、一致
- **逻辑严密性**：论证是否前后呼应，有无矛盾
- **引用完整性**：引用的数据、案例是否完整
- **格式规范性**：标题层次、序号使用是否规范

---

## 检查清单

请按照以下清单逐项检查：

### 内容层面
- [ ] 核心观点是否明确、一致
- [ ] 关键数据是否准确、一致
- [ ] 重要事实是否完整、准确
- [ ] 论证逻辑是否严密、连贯
- [ ] 有无前后矛盾之处

### 格式层面
- [ ] 标题层次是否清晰、规范
- [ ] 序号使用是否统一、规范
- [ ] 时间表述是否统一格式
- [ ] 数字表述是否统一格式
- [ ] 专业术语是否全文统一

### 细节层面
- [ ] 有无明显错别字
- [ ] 标点符号使用是否规范
- [ ] 机构名称是否完整、准确
- [ ] 人名、地名是否准确
- [ ] 引用数据是否准确

---

## 输出格式

请按以下格式输出检查结果：

【检查报告】

一、内容检查
1. 数据一致性：[检查结果]
2. 逻辑严密性：[检查结果]
3. 完整性：[检查结果]

二、格式检查
1. 标题层次：[检查结果]
2. 序号使用：[检查结果]
3. 术语统一：[检查结果]

三、问题清单
[列出发现的所有问题，标注位置和具体内容]

四、检查结论
通过检查 / 发现问题需要修改

---

## 开始执行

现在请接收公文内容，按照上述标准进行检查，输出检查报告。

**重要**：只进行检查和问题标注，不修改任何内容！
"""

    # 6. 最终调整提示词
    FINAL_ADJUSTMENT_PROMPT = """对以下公文内容进行格式调整：

1. 除常见专业名词如gdp、cpi、ppi等其余名词不要出现英文缩写或英文翻译
2. 不要用括号注明的形式（如"中文（英文）"改为只保留中文）
3. 把"引言"改成"按"
4. 后续大标题从"一、"开始（不要有"引言"作为标题）
5. **保持内容的完整性，不要概括或精简**

【调整原则】
- 只做格式调整，不改变内容
- 保持所有实质性内容和数据
- 统一术语和格式规范

Input：{content}

Output：只能输出修改后的正文部分
"""

    def __init__(self):
        """初始化服务"""
        # 硅基流动客户端（用于大纲生成、章节写作、最终调整）
        self.api_key = settings.SILICONFLOW_API_KEY
        self.base_url = settings.SILICONFLOW_BASE_URL
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        # OpenRouter 客户端（用于内容整合）
        self.openrouter_client = AsyncOpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
        )

        # 模型配置
        self.KIMI_MODEL = settings.KIMI_MODEL
        self.GEMINI_MODEL = settings.OPENROUTER_TEXT_MODEL

    async def process_academic_to_official(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None,
        db: Optional[AsyncSession] = None,
        style: str = "complete",  # 风格参数：complete=严谨完整型，concise=简洁概括型
    ) -> AsyncIterator[ProgressUpdate]:
        """
        执行学术报告转公文工作流

        Args:
            file_path: 输入文件路径
            progress_callback: 进度回调函数（可选）
            db: 数据库会话（可选）
            style: 公文风格（complete=严谨完整型，concise=简洁概括型）

        Yields:
            ProgressUpdate: 进度更新
        """
        try:
            # 存储工作流上下文数据
            context = {
                "original_text": "",
                "outline_json": "",
                "all_titles": [],
                "section_dict": {},
                "chapters_content": [],
                "integrated_content": "",
                "check_report": "",
                "final_content": "",
            }

            # 初始化调试日志
            debug_logger = get_debug_logger()
            logger.info(f"[调试] 调试会话目录: {debug_logger.get_session_path()}")

            # ========== 阶段1: 文档提取 ==========
            yield await self._emit_progress(
                WorkflowStage.DOCUMENT_EXTRACTION,
                "正在提取文档内容...",
                5,
                {"step": "提取文档"},
                progress_callback
            )

            original_text = await self._extract_document(file_path)
            context["original_text"] = original_text

            yield await self._emit_progress(
                WorkflowStage.DOCUMENT_EXTRACTION,
                f"文档提取完成，共 {len(original_text)} 字符",
                10,
                {"text_length": len(original_text)},
                progress_callback
            )

            # ========== 阶段2: 知识检索 ==========
            yield await self._emit_progress(
                WorkflowStage.KNOWLEDGE_RETRIEVAL,
                "正在检索相关知识库内容...",
                15,
                {"step": "知识检索"},
                progress_callback
            )

            knowledge_context = await self._retrieve_knowledge(original_text, db)

            yield await self._emit_progress(
                WorkflowStage.KNOWLEDGE_RETRIEVAL,
                f"知识检索完成，检索到 {len(knowledge_context)} 条相关内容",
                20,
                {"knowledge_count": len(knowledge_context)},
                progress_callback
            )

            # ========== 阶段3: 大纲生成（JSON格式） ==========
            yield await self._emit_progress(
                WorkflowStage.OUTLINE_GENERATION,
                "正在生成公文大纲...",
                25,
                {"step": "生成大纲"},
                progress_callback
            )

            outline_json = await self._generate_outline(original_text, knowledge_context)
            context["outline"] = outline_json

            yield await self._emit_progress(
                WorkflowStage.OUTLINE_GENERATION,
                "公文大纲生成完成",
                30,
                {"outline": json.dumps(outline_json, ensure_ascii=False)[:500]},
                progress_callback
            )

            # ========== 阶段4: 提取章节标题（从JSON解析） ==========
            yield await self._emit_progress(
                WorkflowStage.PARAMETER_EXTRACTION,
                "正在提取章节标题...",
                35,
                {"step": "提取标题"},
                progress_callback
            )

            all_titles, section_dict = self._extract_chapter_titles_from_outline(outline_json)
            context["all_titles"] = all_titles
            context["section_dict"] = section_dict

            yield await self._emit_progress(
                WorkflowStage.PARAMETER_EXTRACTION,
                f"提取到 {len(section_dict)} 个一级标题，共 {len(all_titles)} 个标题",
                40,
                {
                    "section_count": len(section_dict),
                    "total_titles": len(all_titles),
                    "structure": section_dict
                },
                progress_callback
            )

            # ========== 阶段5: 内容整理（新增） ==========
            yield await self._emit_progress(
                WorkflowStage.CONTENT_ORGANIZATION,
                "正在按一级标题整理原文内容...",
                42,
                {"step": "内容整理"},
                progress_callback
            )

            # 提取一级标题列表
            section_titles = list(section_dict.keys())
            organized_content = await self._organize_content_by_sections(
                original_text,
                outline_json,  # 传递JSON对象而非字符串
                section_titles
            )
            context["organized_content"] = organized_content

            yield await self._emit_progress(
                WorkflowStage.CONTENT_ORGANIZATION,
                f"内容整理完成，整理了 {len(organized_content)} 个一级标题的内容",
                44,
                {
                    "organized_sections": len(organized_content),
                    "section_lengths": {k: len(v) for k, v in organized_content.items()}
                },
                progress_callback
            )

            # ========== 阶段6: 迭代写作（改进） ==========
            yield await self._emit_progress(
                WorkflowStage.CHAPTER_WRITING,
                f"开始写作 {len(all_titles)} 个章节...",
                45,
                {"step": "章节写作", "total": len(all_titles)},
                progress_callback
            )

            chapters_content = await self._write_chapters_concurrent_v2(
                all_titles,
                section_dict,
                organized_content,
                progress_callback
            )
            context["chapters_content"] = chapters_content

            yield await self._emit_progress(
                WorkflowStage.CHAPTER_WRITING,
                f"所有章节写作完成",
                65,
                {"completed": len(chapters_content)},
                progress_callback
            )

            # ========== 阶段7: 模板转换 ==========
            yield await self._emit_progress(
                WorkflowStage.TEMPLATE_TRANSFORM,
                "正在整合章节内容...",
                70,
                {"step": "模板转换"},
                progress_callback
            )

            combined_content = self._transform_template(chapters_content)

            yield await self._emit_progress(
                WorkflowStage.TEMPLATE_TRANSFORM,
                "章节内容整合完成",
                75,
                {},
                progress_callback
            )

            # ========== 阶段8: 内容整合 ==========
            yield await self._emit_progress(
                WorkflowStage.CONTENT_INTEGRATION,
                "正在进行内容整合和润色...",
                80,
                {"step": "内容整合", "content_length": len(combined_content)},
                progress_callback
            )

            # 根据内容长度选择整合策略
            if len(combined_content) > self.MAX_CHARS_FOR_INTEGRATION:
                logger.info(f"[思维链] 内容较长，使用渐进式整合策略")
                integrated_content = await self._integrate_content_incremental(
                    combined_content,
                    progress_callback,
                    style  # 传递风格参数
                )
            else:
                logger.info(f"[思维链] 内容长度适中，直接整合")
                integrated_content = await self._integrate_content(
                    combined_content,
                    style  # 传递风格参数
                )

            context["integrated_content"] = integrated_content

            yield await self._emit_progress(
                WorkflowStage.CONTENT_INTEGRATION,
                "内容整合完成",
                85,
                {"integrated_length": len(integrated_content)},
                progress_callback
            )

            # ========== 阶段9: 内容检查 ==========
            yield await self._emit_progress(
                WorkflowStage.CONTENT_CHECK,
                "正在进行内容细节检查...",
                87,
                {"step": "内容检查"},
                progress_callback
            )

            check_report, checked_content = await self._check_content(integrated_content)
            context["check_report"] = check_report

            yield await self._emit_progress(
                WorkflowStage.CONTENT_CHECK,
                "内容检查完成",
                90,
                {
                    "check_report_length": len(check_report),
                    "checked_content_length": len(checked_content)
                },
                progress_callback
            )

            # ========== 阶段10: 最终调整 ==========
            yield await self._emit_progress(
                WorkflowStage.FINAL_ADJUSTMENT,
                "正在进行最终格式调整...",
                92,
                {"step": "最终调整"},
                progress_callback
            )

            final_content = await self._final_adjustment(checked_content)
            context["final_content"] = final_content

            yield await self._emit_progress(
                WorkflowStage.FINAL_ADJUSTMENT,
                "最终调整完成",
                95,
                {},
                progress_callback
            )

            # ========== 完成 ==========
            # 保存调试会话总结
            get_debug_logger().save_summary()

            yield await self._emit_progress(
                WorkflowStage.COMPLETED,
                "学术报告转公文完成！",
                100,
                {
                    "final_content": final_content,
                    "stats": {
                        "original_length": len(original_text),
                        "final_length": len(final_content),
                        "title_count": len(all_titles),
                        "section_count": len(section_dict),
                    },
                    "debug_session": str(get_debug_logger().get_session_path()),
                },
                progress_callback
            )

        except Exception as e:
            logger.error(f"[ERROR] 工作流执行失败: {e}")
            yield await self._emit_progress(
                WorkflowStage.FAILED,
                f"处理失败: {str(e)}",
                -1,
                {"error": str(e)},
                progress_callback
            )
            raise

    async def _emit_progress(
        self,
        stage: WorkflowStage,
        message: str,
        progress: float,
        data: Dict[str, Any],
        callback: Optional[Callable[[ProgressUpdate], None]] = None,
    ):
        """发送进度更新（生成器）"""
        update = ProgressUpdate(
            stage=stage,
            stage_name=stage.value,
            progress=progress,
            message=message,
            data=data
        )

        # 打印到控制台（用于调试）
        logger.info(f"[进度] {progress}% - {message}")
        if data:
            logger.debug(f"[数据] {json.dumps(data, ensure_ascii=False)[:500]}")

        # 调用回调（如果提供）
        if callback:
            if asyncio.iscoroutinefunction(callback):
                await callback(update)
            else:
                callback(update)

        # 返回 update（让调用者 yield）
        return update

    # ========== 具体实现方法 ==========

    async def _extract_document(self, file_path: str) -> str:
        """提取文档内容"""
        logger.info(f"\n{'='*60}")
        logger.info(f"[公文写作] 开始提取文档: {file_path}")
        logger.info(f"{'='*60}\n")

        full_path = file_service.get_full_path(file_path)
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(full_path, "rb") as f:
            file_bytes = f.read()

        # 根据文件类型提取
        file_ext = Path(file_path).suffix.lower()

        if file_ext == ".pdf":
            # 优先使用 MinerU 进行高质量提取
            if settings.MINERU_ENABLED and settings.MINERU_API_KEY:
                try:
                    logger.info(f"\n{'🔷'*30}")
                    logger.info(f"📄 PDF提取器: MinerU (高质量)")
                    logger.info(f"{'🔷'*30}\n")
                    logger.info(f"[公文写作] 正在使用 MinerU 提取 PDF...")
                    logger.info(f"[公文写作] 文件: {file_path}")
                    logger.info(f"[公文写作] 模型: vlm (视觉语言模型)")

                    content = await mineru_service.parse_pdf_to_markdown(
                        file_path=full_path,
                        progress_callback=None,
                        model_version="vlm"
                    )

                    logger.info(f"\n{'✅'*30}")
                    logger.info(f"[公文写作] PDF提取完成 (MinerU)！")
                    logger.info(f"[公文写作] 提取长度: {len(content)} 字符")
                    logger.info(f"{'✅'*30}\n")
                    return content
                except Exception as e:
                    logger.warning(f"\n{'❌'*30}")
                    logger.warning(f"[公文写作] MinerU PDF提取失败: {e}")
                    logger.warning(f"[公文写作] 正在回退到 PyMuPDF...")
                    logger.warning(f"{'❌'*30}\n")

            # 使用 PyMuPDF 提取
            if fitz_extractor is None:
                raise EnvironmentError(
                    "PyMuPDF 不可用，请先安装 PyMuPDF:\n"
                    "运行: pip install PyMuPDF"
                )

            logger.info(f"\n{'🔶'*30}")
            logger.info(f"📄 PDF提取器: PyMuPDF (本地)")
            logger.info(f"{'🔶'*30}\n")
            logger.info(f"[公文写作] 正在使用 PyMuPDF 提取 PDF...")
            logger.info(f"[公文写作] 文件: {file_path}")

            result = fitz_extractor.extract_from_bytes(file_bytes, Path(file_path).name)
            content = result.get("content", "")

            logger.info(f"\n{'✅'*30}")
            logger.info(f"[公文写作] PDF提取完成 (PyMuPDF)！")
            logger.info(f"[公文写作] 提取段落数: {result.get('paragraphs', 0)} 个")
            logger.info(f"{'✅'*30}\n")
        elif file_ext in {".txt", ".md"}:
            content = file_bytes.decode("utf-8", errors="ignore")
            logger.info(f"[公文写作] 文本文件提取完成，长度: {len(content)} 字符")
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")

        return content

    async def _retrieve_knowledge(
        self,
        query_text: str,
        db: Optional[AsyncSession]
    ) -> str:
        """检索知识库"""
        logger.info(f"[思维链] 开始知识检索")

        # TODO: 实现真实的知识库检索
        # 这里先返回空，后续可以集成向量检索
        knowledge = ""

        logger.info(f"[思维链] 知识检索完成")
        return knowledge

    async def _generate_outline(
        self,
        original_text: str,
        knowledge_context: str,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None
    ) -> str:
        """
        生成公文大纲

        根据文档长度自动选择策略：
        - 小文档（<30000字符）：直接生成
        - 大文档（≥30000字符）：分层摘要后生成

        Args:
            original_text: 原始文本
            knowledge_context: 知识库上下文
            progress_callback: 进度回调

        Returns:
            大纲内容
        """
        logger.info(f"[思维链] 开始生成大纲")
        logger.info(f"[思维链] 输入文本长度: {len(original_text)} 字符")

        # 根据文档长度选择策略
        if len(original_text) > self.MAX_CHARS_FOR_OUTLINE:
            logger.info(f"[思维链] 文档较长，使用分层摘要策略")
            return await self._generate_outline_hierarchical(
                original_text,
                knowledge_context,
                progress_callback
            )
        else:
            logger.info(f"[思维链] 文档长度适中，直接生成大纲")
            return await self._generate_outline_direct(
                original_text,
                knowledge_context
            )

    async def _generate_outline_direct(
        self,
        original_text: str,
        knowledge_context: str
    ) -> Dict[str, Any]:
        """
        直接生成大纲（用于中小文档）

        Returns:
            Dict[str, Any]: 大纲JSON对象，包含标题、摘要、章节等
        """
        user_prompt = f"请将以下内容执行上述操作\n\n{original_text[:self.MAX_CHARS_FOR_OUTLINE]}"

        if len(original_text) > self.MAX_CHARS_FOR_OUTLINE:
            user_prompt += f"\n\n[注: 原文共 {len(original_text)} 字符，以上为前{self.MAX_CHARS_FOR_OUTLINE}字符]"

        response = await self.client.chat.completions.create(
            model=self.KIMI_MODEL,  # 使用 Kimi-256K 模型
            messages=[
                {"role": "system", "content": self.OUTLINE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            timeout=180.0
        )

        content = response.choices[0].message.content.strip()
        logger.info(f"[思维链] 大纲生成完成，长度: {len(content)} 字符")
        logger.info(f"[思维链] 大纲预览:\n{content[:500]}...")

        # 解析JSON
        success, outline_json, error = LLMOutputParser.parse_json_with_retry(
            content,
            max_retries=0,
            expected_structure="dict"  # 接受任何字典结构
        )

        if not success:
            logger.error(f"[ERROR] 大纲JSON解析失败: {error}")
            logger.error(f"[ERROR] 原始输出: {content}")
            get_debug_logger().log_stage(
                stage_name="01_大纲生成_失败",
                input_text=original_text[:self.MAX_CHARS_FOR_OUTLINE],
                output_text=f"解析失败: {error}\n原始输出: {content}",
                model=self.KIMI_MODEL,
                prompt=self.OUTLINE_SYSTEM_PROMPT[:500] + "...",
                metadata={"错误": error}
            )
            raise ValueError(f"大纲生成失败，JSON解析错误: {error}")

        # 验证必要字段
        if not any(key in outline_json for key in ["标题", "摘要", "结语"]):
            logger.warning(f"[思维链] 大纲JSON缺少标准字段，结构: {list(outline_json.keys())}")

        logger.info(f"[思维链] 大纲JSON解析成功，包含 {len(outline_json)} 个字段")

        # 记录调试信息
        get_debug_logger().log_stage(
            stage_name="01_大纲生成",
            input_text=original_text[:self.MAX_CHARS_FOR_OUTLINE],
            output_text=json.dumps(outline_json, ensure_ascii=False, indent=2),
            model=self.KIMI_MODEL,
            prompt=self.OUTLINE_SYSTEM_PROMPT[:500] + "...",
            metadata={
                "策略": "直接生成JSON",
                "输入长度": len(original_text),
                "输出长度": len(content),
                "字段数量": len(outline_json),
                "文档标题": outline_json.get("标题", ""),
                "一级标题数量": len([k for k in outline_json.keys() if k not in ["标题", "摘要", "结语"]])
            }
        )

        return outline_json

    def _extract_chapter_titles_from_outline(
        self,
        outline_json: Dict[str, Any]
    ) -> tuple[List[str], Dict[str, List[str]]]:
        """
        从大纲JSON中提取章节标题（不再调用LLM）

        Args:
            outline_json: 大纲LLM输出的JSON对象

        Returns:
            (all_titles, section_dict):
            - all_titles: 所有标题的扁平列表（按顺序）
            - section_dict: {一级标题: [该一级标题下的所有小标题]}
        """
        logger.info(f"[思维链] 从大纲JSON提取章节标题")

        # 提取结构化数据
        title = outline_json.get("标题", "")
        abstract = outline_json.get("摘要", "")
        conclusion = outline_json.get("结语", "")

        # 提取一级标题和小标题
        section_dict = {}
        for key, value in outline_json.items():
            # 跳过非章节字段
            if key in ["标题", "摘要", "结语"]:
                continue

            # 检查是否是一级标题（key应该是字符串，value应该是列表）
            if isinstance(key, str) and isinstance(value, list):
                # 验证列表元素都是字符串
                if all(isinstance(item, str) for item in value):
                    section_dict[key] = value
                else:
                    logger.warning(f"[思维链] 跳过无效的章节: {key} = {value}")

        # 构建所有标题的扁平列表
        all_titles = []
        for section_title, sub_titles in section_dict.items():
            all_titles.append(section_title)
            all_titles.extend(sub_titles)

        logger.info(f"[思维链] 提取到 {len(section_dict)} 个一级标题")
        logger.info(f"[思维链] 提取到 {len(all_titles)} 个总标题")

        # 记录调试信息
        get_debug_logger().log_stage(
            stage_name="04_标题提取",
            input_text=json.dumps(outline_json, ensure_ascii=False, indent=2)[:1000],
            output_text=json.dumps(section_dict, ensure_ascii=False, indent=2),
            model="代码解析（无LLM调用）",
            prompt="直接解析JSON",
            metadata={
                "一级标题数量": len(section_dict),
                "总标题数量": len(all_titles),
                "标题结构": section_dict,
                "文档标题": title,
                "有摘要": bool(abstract),
                "有结语": bool(conclusion)
            }
        )

        return all_titles, section_dict

    async def _write_chapters_concurrent(
        self,
        original_text: str,
        chapter_titles: List[str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> List[str]:
        """并发写作各章节"""
        logger.info(f"[思维链] 开始并发写作 {len(chapter_titles)} 个章节")

        # 准备全文上下文（用于章节写作）
        # 如果文档不超长，直接使用全文；如果超长，使用截断版本
        if len(original_text) <= 50000:
            article_context = original_text
            logger.info(f"[思维链] 使用全文作为章节写作上下文，长度: {len(original_text)} 字符")
        else:
            article_context = original_text[:50000] + "\n\n[...原文较长，以上为前50000字符...]"
            logger.info(f"[思维链] 原文较长，使用前50000字符作为上下文")

        # 创建章节上下文
        chapters = [
            ChapterContext(
                title=title,
                index=i,
                total=len(chapter_titles)
            )
            for i, title in enumerate(chapter_titles)
        ]

        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_CHAPTERS)

        async def write_with_limit(chapter: ChapterContext) -> tuple[int, str]:
            """带并发限制的写作函数"""
            async with semaphore:
                logger.info(f"[思维链] 开始写作第 {chapter.index + 1}/{chapter.total} 章: {chapter.title}")

                content = await self._write_single_chapter(article_context, chapter.title, chapter.index, len(chapters))

                logger.info(f"[思维链] 完成第 {chapter.index + 1}/{chapter.total} 章")

                return (chapter.index, content)

        # 并发执行
        results = await asyncio.gather(
            *[write_with_limit(ch) for ch in chapters],
            return_exceptions=True
        )

        # 处理结果
        chapters_content = [""] * len(chapter_titles)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"[ERROR] 章节写作失败: {result}")
                continue
            index, content = result
            chapters_content[index] = content

        logger.info(f"[思维链] 所有章节写作完成")
        return chapters_content

    async def _write_chapters_concurrent_v2(
        self,
        all_titles: List[str],
        section_dict: Dict[str, List[str]],
        organized_content: Dict[str, str],
        progress_callback: Optional[Callable[[ProgressUpdate], None]]
    ) -> List[str]:
        """
        并发写作各章节（改进版）

        Args:
            all_titles: 所有标题的扁平列表（包括一级标题和小标题）
            section_dict: {一级标题: [小标题列表]}
            organized_content: {一级标题: 整理后的原文内容}
            progress_callback: 进度回调
        """
        logger.info(f"[思维链] 开始并发写作（改进版）")
        logger.info(f"[思维链] 总标题数: {len(all_titles)}")
        logger.info(f"[思维链] 一级标题数: {len(section_dict)}")

        # 构建标题到所属一级标题的映射
        title_to_section = {}
        for section_title, sub_titles in section_dict.items():
            # 一级标题本身
            title_to_section[section_title] = section_title
            # 小标题
            for sub_title in sub_titles:
                title_to_section[sub_title] = section_title

        # 创建章节上下文
        chapters = [
            ChapterContext(
                title=title,
                index=i,
                total=len(all_titles)
            )
            for i, title in enumerate(all_titles)
        ]

        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_CHAPTERS)

        async def write_with_limit(chapter: ChapterContext) -> tuple[int, str]:
            """带并发限制的写作函数"""
            async with semaphore:
                # 找到该标题所属的一级标题
                section_title = title_to_section.get(chapter.title, list(organized_content.keys())[0])
                # 获取该一级标题的整理内容
                section_organized_text = organized_content.get(section_title, "")

                logger.info(f"[思维链] 开始写作第 {chapter.index + 1}/{chapter.total} 章: {chapter.title}")
                logger.info(f"[思维链]   - 所属一级标题: {section_title}")
                logger.info(f"[思维链]   - 整理内容长度: {len(section_organized_text)} 字符")

                content = await self._write_single_chapter(
                    section_organized_text,  # 使用整理后的内容
                    chapter.title,
                    section_title,  # 传递所属一级标题
                    chapter.index,
                    len(all_titles)
                )

                logger.info(f"[思维链] 完成第 {chapter.index + 1}/{chapter.total} 章")

                return (chapter.index, content)

        # 并发执行
        results = await asyncio.gather(
            *[write_with_limit(ch) for ch in chapters],
            return_exceptions=True
        )

        # 处理结果
        chapters_content = [""] * len(all_titles)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"[ERROR] 章节写作失败: {result}")
                continue
            index, content = result
            chapters_content[index] = content

        logger.info(f"[思维链] 所有章节写作完成（改进版）")
        return chapters_content

    async def _write_single_chapter(
        self,
        organized_content: str,
        chapter_title: str,
        section_title: str,
        chapter_index: int = 0,
        total_chapters: int = 1
    ) -> str:
        """
        写作单个章节

        Args:
            organized_content: 整理后的原文内容（只包含相关部分）
            chapter_title: 章节标题（当前要写的小标题）
            section_title: 所属一级标题
            chapter_index: 章节序号
            total_chapters: 总章节数
        """
        prompt = self.CHAPTER_WRITING_PROMPT.format(
            organized_content=organized_content,
            chapter_title=chapter_title,
            current_index=chapter_index + 1,
            total_chapters=total_chapters,
            section_title=section_title
        )

        response = await self.client.chat.completions.create(
            model=self.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的公文写作助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            timeout=120.0
        )

        result = response.choices[0].message.content

        # 记录调试信息（每个章节）
        get_debug_logger().log_stage(
            stage_name=f"05_章节写作_{chapter_title[:30]}",
            input_text=organized_content[:5000],  # 只记录前5000字符，避免日志过大
            output_text=result,
            model=self.DEEPSEEK_MODEL,
            prompt=self.CHAPTER_WRITING_PROMPT.format(
                organized_content="...",
                chapter_title=chapter_title,
                current_index=chapter_index + 1,
                total_chapters=total_chapters,
                section_title=section_title
            ),
            metadata={
                "章节标题": chapter_title,
                "所属一级标题": section_title,
                "章节序号": f"{chapter_index + 1}/{total_chapters}",
                "整理内容长度": len(organized_content),
                "输入长度": len(organized_content),
                "输出长度": len(result)
            }
        )

        return result

    async def _organize_content_by_sections(
        self,
        original_text: str,
        outline_json: Dict[str, Any],
        section_titles: List[str]
    ) -> Dict[str, str]:
        """
        按一级标题整理原文内容

        Args:
            original_text: 完整原文
            outline_json: 大纲JSON对象
            section_titles: 一级标题列表

        Returns:
            Dict[str, str]: {一级标题: 整理后的原文内容}
        """
        logger.info(f"[思维链] 开始按一级标题整理原文内容")
        logger.info(f"[思维链] 一级标题数量: {len(section_titles)}")

        # 将outline_json转换为字符串格式（用于提示词）
        outline_str = json.dumps(outline_json, ensure_ascii=False, indent=2)

        # 构建提示词
        prompt = self.CONTENT_ORGANIZATION_PROMPT.format(
            original_text=original_text,
            outline=outline_str
        )

        response = await self.client.chat.completions.create(
            model=self.KIMI_MODEL,  # 使用Kimi模型进行内容整理
            messages=[
                {"role": "system", "content": "你是一个专业的内容整理助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # 使用较低温度，确保忠实原文
            timeout=300.0  # 内容整理可能需要更长时间
        )

        organized_content = response.choices[0].message.content

        # 使用增强的解析器（支持多种分隔符格式）
        success, result, error = LLMOutputParser.parse_sectioned_content_flexible(
            organized_content,
            section_titles
        )

        if not success:
            logger.error(f"[ERROR] 内容整理解析失败: {error}")
            logger.error(f"[ERROR] 原始输��: {organized_content[:1000]}...")
            # 记录失败
            get_debug_logger().log_stage(
                stage_name="03_内容整理_失败",
                input_text=f"原文长度: {len(original_text)}\n大纲:\n{outline_str}\n一级标题: {section_titles}",
                output_text=f"解析失败: {error}\n原始输出: {organized_content[:1000]}...",
                model=self.KIMI_MODEL,
                prompt=prompt[:1000] + "...",
                metadata={"错误": error}
            )
            raise ValueError(f"内容整理失败，LLM输出格式不正确: {error}")

        logger.info(f"[思维链] 内容整理完成，整理了 {len(result)} 个一级标题")
        for section, content in result.items():
            logger.info(f"[思维链]   - {section}: {len(content)} 字符")

        # 记录调试信息
        get_debug_logger().log_stage(
            stage_name="03_内容整理",
            input_text=f"原文长度: {len(original_text)}\n大纲:\n{outline_str}\n一级标题: {section_titles}",
            output_text=organized_content,
            model=self.KIMI_MODEL,
            prompt=prompt[:1000] + "...",
            metadata={
                "策略": "按一级标题整理",
                "一级标题数量": len(section_titles),
                "整理后标题数量": len(result),
                "各部分长度": {k: len(v) for k, v in result.items()}
            }
        )

        return result

    def _transform_template(self, chapters_content: List[str]) -> str:
        """模板转换：组合各章节"""
        logger.info(f"[思维链] 开始模板转换")

        # 使用分隔符组合各章节
        result = "\n\n---\n\n".join([ch for ch in chapters_content if ch])

        logger.info(f"[思维链] 模板转换完成，总长度: {len(result)} 字符")
        return result

    async def _integrate_and_polish(self, combined_content: str) -> str:
        """
        内容整合与润色（一步完成，使用Gemini）

        Args:
            combined_content: 各章节合并后的内容

        Returns:
            str: 最终的公文文章（已整合、润色、格式调整）
        """
        logger.info(f"[思维链] 开始内容整合与润色（一步完成）")
        logger.info(f"[思维链] 使用模型: {self.GEMINI_MODEL} (OpenRouter)")
        logger.info(f"[思维链] 输入长度: {len(combined_content)} 字符")

        response = await self.openrouter_client.chat.completions.create(
            model=self.GEMINI_MODEL,  # 使用 Gemini（长上下文）
            messages=[
                {"role": "system", "content": self.INTEGRATION_SYSTEM_PROMPT},
                {"role": "user", "content": combined_content}
            ],
            temperature=0.3,  # 较低温度，确保稳定性
            max_tokens=98881,  # 允许长输出
            timeout=300.0,  # 5分钟超时
            extra_body={"reasoning": {"enabled": True}}  # 启用推理功能
        )

        result = response.choices[0].message.content

        logger.info(f"[思维链] 内容整合与润色完成，输出长度: {len(result)} 字符")

        # 记录调试信息
        get_debug_logger().log_stage(
            stage_name="06_内容整合与润色",
            input_text=combined_content[:5000] + "...\n[总长度: " + str(len(combined_content)) + "]",
            output_text=result,
            model=self.GEMINI_MODEL,
            prompt=self.INTEGRATION_SYSTEM_PROMPT[:500] + "...",
            metadata={
                "输入长度": len(combined_content),
                "输出长度": len(result),
                "长度变化": f"{len(result) - len(combined_content):+,} 字符",
                "压缩率": f"{((1 - len(result) / len(combined_content)) * 100):.1f}%" if len(combined_content) > 0 else "0%"
            }
        )

        return result

    async def _integrate_content(self, combined_content: str, style: str = "complete") -> str:
        """
        内容整合和润色

        Args:
            combined_content: 待整合的内容
            style: 风格参数（complete=严谨完整型，concise=简洁概括型）
        """
        logger.info(f"[思维链] 开始内容整合，风格: {style}")
        logger.info(f"[思维链] 使用模型: {self.GEMINI_MODEL} (Gemini)")

        # 根据风格调整提示词
        system_prompt = self.INTEGRATION_SYSTEM_PROMPT
        if style == "concise":
            # 简洁概括型：添加精简指令
            system_prompt += """

\n## 简洁概括风格要求

**当前风格模式：简洁概括型**

请按照以下要求进行整合：

1. **精炼表达**：删除冗余表述，保留核心观点
2. **段落控制**：每段控制在50-80字符，更加简洁
3. **概括优先**：优先使用概括性语句，减少详细论述
4. **重点突出**：突出结论和关键数据，省略过程性描述
5. **语言精练**：删除修饰性词语，使用简洁表达

**目标**：输出一篇精炼、简洁的公文，字数约为严谨完整型的60-70%。
"""
        else:  # complete
            system_prompt += """

\n## 严谨完整风格要求

**当前风格模式：严谨完整型**

请严格按照上述央行专题报告标准进行整合：
- 段落长度：80-100字符
- 详细论述：保留完整论证过程
- 数据精确：包含具体年份和来源
- 格式规范：严格遵循标题层次和公文格式
"""

        response = await self.openrouter_client.chat.completions.create(
            model=self.GEMINI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": combined_content}
            ],
            temperature=0.3,
            max_tokens=98881,
            timeout=600.0  # 10分钟超时（Gemini更快）
        )

        result = response.choices[0].message.content

        logger.info(f"[思维链] 内容整合完成，输出长度: {len(result)} 字符，风格: {style}")

        # 记录调试信息
        get_debug_logger().log_stage(
            stage_name="05_内容整合",
            input_text=combined_content,
            output_text=result,
            model=self.GEMINI_MODEL,
            prompt=system_prompt[:500] + "...",
            metadata={
                "输入长度": len(combined_content),
                "输出长度": len(result),
                "风格": style,
                "压缩率": f"{((1 - len(result) / len(combined_content)) * 100):.1f}%"
            }
        )

        return result

    async def _check_content(self, content: str) -> tuple[str, str]:
        """
        内容检查（细节检查，不做润色）

        Returns:
            (检查报告, 原内容): 检查报告和原始内容
        """
        logger.info(f"[思维链] 开始内容检查")

        response = await self.client.chat.completions.create(
            model=self.KIMI_MODEL,  # 使用Kimi进行检查
            messages=[
                {"role": "system", "content": "你是一位资深的公文审校专家。"},
                {"role": "user", "content": self.CONTENT_CHECK_PROMPT + "\n\n【公文内容】\n" + content}
            ],
            temperature=0.3,  # 降低温度，确保检查客观
            timeout=300.0
        )

        check_report = response.choices[0].message.content

        logger.info(f"[思维链] 内容检查完成")

        # 记录调试信息
        get_debug_logger().log_stage(
            stage_name="07_内容检查",
            input_text=content[:5000] + "...\n[内容过长，只记录前5000字符]",
            output_text=check_report,
            model=self.KIMI_MODEL,
            prompt=self.CONTENT_CHECK_PROMPT[:500] + "...",
            metadata={
                "检查策略": "细节检查，不做润色",
                "内容长度": len(content),
                "报告长度": len(check_report)
            }
        )

        # 返回检查报告和原内容（不修改）
        return check_report, content

    async def _final_adjustment(self, content: str) -> str:
        """最终调整（使用Kimi）"""
        logger.info(f"[思维链] 开始最终调整")
        logger.info(f"[思维链] 使用模型: {self.KIMI_MODEL}")

        prompt = self.FINAL_ADJUSTMENT_PROMPT.format(content=content)

        response = await self.client.chat.completions.create(
            model=self.KIMI_MODEL,  # 改用Kimi
            messages=[
                {"role": "system", "content": "你是一个公文格式调整专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            timeout=120.0
        )

        result = response.choices[0].message.content

        logger.info(f"[思维链] 最终调整完成，输出长度: {len(result)} 字符")

        # 记录调试信息
        get_debug_logger().log_stage(
            stage_name="06_最终调整",
            input_text=content[:2000] + "...\n[总长度: " + str(len(content)) + "]",
            output_text=result,
            model=self.KIMI_MODEL,  # 改为Kimi
            prompt=self.FINAL_ADJUSTMENT_PROMPT.format(content="...")[:200],
            metadata={
                "输入长度": len(content),
                "输出长度": len(result),
                "长度变化": f"{len(result) - len(content):+,} 字符"
            }
        )

        return result

    # ========== 大文档处理方法 ==========

    def _split_text_by_structure(self, text: str, max_chars: int) -> List[str]:
        """
        按结构分割文本（保持段落完整性）

        Args:
            text: 待分割的文本
            max_chars: 每块的最大字符数

        Returns:
            分割后的文本块列表
        """
        logger.info(f"[思维链] 按结构分割文本，最大块大小: {max_chars}")

        # 规范化换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 按双换行分割（段落分隔）
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = ""
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_length = len(para)

            # 如果单个段落就超过限制，需要进一步分割
            if para_length > max_chars:
                # 先保存当前积累的内容
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_length = 0

                # 按句子分割超长段落
                sentences = self._split_long_paragraph(para, max_chars)
                chunks.extend(sentences)
                continue

            # 检查添加此段落后是否会超出限制
            if current_length + para_length + 2 <= max_chars:
                if current_chunk:
                    current_chunk += "\n\n" + para
                    current_length += para_length + 2
                else:
                    current_chunk = para
                    current_length = para_length
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
                current_length = para_length

        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.info(f"[思维链] 文本已分割为 {len(chunks)} 个块")
        return chunks

    def _split_long_paragraph(self, paragraph: str, max_chars: int) -> List[str]:
        """分割过长的段落（按句子/分句分割）"""
        import re

        # 先尝试按中文句号、问号、感叹号分割
        sentences = re.split(r'([。！？])', paragraph)

        chunks = []
        current_chunk = ""

        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and sentences[i + 1] in '。！？':
                sentence = sentences[i] + sentences[i + 1]
                i += 2
            else:
                sentence = sentences[i]
                i += 1

            if not sentence.strip():
                continue

            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    async def _generate_summary_for_chunk(self, chunk: str, chunk_index: int, total_chunks: int) -> str:
        """
        为文本块生成摘要

        Args:
            chunk: 文本块
            chunk_index: 块索引
            total_chunks: 总块数

        Returns:
            摘要内容
        """
        logger.info(f"[思维链] 生成第 {chunk_index + 1}/{total_chunks} 块的摘要")

        prompt = f"""请为以下文本内容生成简洁的摘要，用于后续生成公文大纲。

要求：
1. 保留主要观点、数据、结论
2. 简明扼要，约200-300字
3. 不要添加原文没有的内容
4. 标注这是第{chunk_index + 1}部分的摘要

【文本内容】
{chunk}
"""

        response = await self.client.chat.completions.create(
            model=self.KIMI_MODEL,  # 使用 Kimi-K2.5 模型
            messages=[
                {"role": "system", "content": "你是一个文本摘要专家，擅长提取核心信息。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=60.0
        )

        return response.choices[0].message.content

    async def _generate_outline_hierarchical(
        self,
        original_text: str,
        knowledge_context: str,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None
    ) -> str:
        """
        分层生成大纲（用于大文档）

        策略：
        1. 将文档分成若干块
        2. 为每块生成摘要
        3. 基于所有摘要生成整体大纲
        4. 基于整体大纲对每部分进行细化

        Args:
            original_text: 原始文本
            knowledge_context: 知识库上下文
            progress_callback: 进度回调

        Returns:
            大纲内容
        """
        logger.info(f"[思维链] 使用分层策略生成大纲")
        logger.info(f"[思维链] 原文长度: {len(original_text)} 字符")

        # 步骤1: 分割文档
        chunks = self._split_text_by_structure(
            original_text,
            self.CHUNK_SIZE_FOR_SUMMARY
        )

        logger.info(f"[思维链] 文档已分为 {len(chunks)} 个部分")

        # 步骤2: 为每块生成摘要（并发）
        logger.info(f"[思维链] 开始生成各部分摘要...")

        semaphore = asyncio.Semaphore(3)  # 控制并发数

        async def summarize_with_limit(idx: int, chunk: str) -> tuple[int, str]:
            async with semaphore:
                summary = await self._generate_summary_for_chunk(chunk, idx, len(chunks))
                return (idx, summary)

        results = await asyncio.gather(
            *[summarize_with_limit(i, chunk) for i, chunk in enumerate(chunks)],
            return_exceptions=True
        )

        # 整理摘要结果
        summaries = [""] * len(chunks)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"[ERROR] 摘要生成失败: {result}")
                continue
            idx, summary = result
            summaries[idx] = summary

        combined_summary = "\n\n".join([s for s in summaries if s])

        logger.info(f"[思维链] 所有摘要生成完成，总长度: {len(combined_summary)} 字符")

        # 步骤3: 基于摘要生成整体大纲
        logger.info(f"[思维链] 基于摘要生成整体大纲...")

        outline_prompt = f"""我将向你提供一篇文章的各部分摘要。请基于这些摘要生成公文整体框架。

{self.OUTLINE_SYSTEM_PROMPT}

【文章各部分摘要】
{combined_summary}
"""

        response = await self.client.chat.completions.create(
            model=self.KIMI_MODEL,  # 使用 Kimi-K2.5 模型
            messages=[
                {"role": "system", "content": self.OUTLINE_SYSTEM_PROMPT},
                {"role": "user", "content": outline_prompt}
            ],
            temperature=0.3,
            timeout=180.0
        )

        outline = response.choices[0].message.content

        logger.info(f"[思维链] 整体大纲生成完成，长度: {len(outline)} 字符")
        logger.info(f"[思维链] 大纲预览:\n{outline[:500]}...")

        return outline

    async def _integrate_content_incremental(
        self,
        combined_content: str,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None,
        style: str = "complete"  # 添加风格参数
    ) -> str:
        """
        整合内容（优化版，减少迭代次数）

        策略：
        1. 如果内容长度适中（≤MAX_CHARS_FOR_INTEGRATION），直接整合
        2. 如果内容较长，分割后尽量一次性整合

        Args:
            combined_content: 待整合的内容
            progress_callback: 进度回调
            style: 风格参数（complete=严谨完整型，concise=简洁概括型）

        Returns:
            整合后的内容
        """
        logger.info(f"[思维链] 开始整合内容，风格: {style}")
        logger.info(f"[思维链] 输入长度: {len(combined_content)} 字符")

        # 如果内容不太长，直接整合（使用Kimi长上下文）
        if len(combined_content) <= self.MAX_CHARS_FOR_INTEGRATION:
            logger.info(f"[思维链] 内容长度适中（{len(combined_content)} ≤ {self.MAX_CHARS_FOR_INTEGRATION}），直接整合")
            return await self._integrate_content(combined_content, style)

        # 内容较长，需要分割处理
        logger.info(f"[思维链] 内容较长（{len(combined_content)} > {self.MAX_CHARS_FOR_INTEGRATION}），需要分割处理")

        # 分割成块
        chunks = self._split_text_by_structure(
            combined_content,
            self.CHUNK_SIZE_FOR_INTEGRATION
        )

        logger.info(f"[思维链] 内容已分为 {len(chunks)} 个块，每块约 {self.CHUNK_SIZE_FOR_INTEGRATION} 字符")

        # 优化策略：如果块数较少（≤4块），尝试一次性整合
        if len(chunks) <= 4:
            logger.info(f"[思维链] 块数较少（{len(chunks)} 块），尝试一次性整合所有块")

            # 合并所有块
            merged_content = "\n\n".join(chunks)

            # 尝试一次性整合
            try:
                result = await self._integrate_content(merged_content)
                logger.info(f"[思维链] 一次性整合成功！")
                return result
            except Exception as e:
                logger.warning(f"[思维链] 一次性整合失败: {e}，回退到迭代整合")
                # 回退到原来的迭代策略

        # 原来的迭代策略（作为回退方案）
        logger.info(f"[思维链] 使用迭代整合策略（块数: {len(chunks)}）")

        # 第一轮：相邻两块合并整合
        logger.info(f"[思维链] 第一轮：相邻块整合")

        integrated = []

        for i in range(0, len(chunks), 2):
            if i + 1 < len(chunks):
                # 合并两块
                merged = chunks[i] + "\n\n" + chunks[i + 1]
                result = await self._integrate_chunk_pair(merged, i // 2, (len(chunks) + 1) // 2)
                integrated.append(result)
            else:
                # 最后一块单独处理
                integrated.append(chunks[i])

        logger.info(f"[思维链] 第一轮完成，剩余 {len(integrated)} 个块")

        # 第二轮：如果仍然超过限制，继续合并
        while len(integrated) > 1 and len("\n\n".join(integrated)) > self.MAX_CHARS_FOR_INTEGRATION:
            logger.info(f"[思维链] 下一轮：继续合并，当前 {len(integrated)} 个块")

            next_round = []

            for i in range(0, len(integrated), 2):
                if i + 1 < len(integrated):
                    merged = integrated[i] + "\n\n" + integrated[i + 1]
                    result = await self._integrate_chunk_pair(merged, i // 2, (len(integrated) + 1) // 2)
                    next_round.append(result)
                else:
                    next_round.append(integrated[i])

            integrated = next_round

        # 最终整合
        if len(integrated) == 1:
            result = integrated[0]
        else:
            final_merged = "\n\n".join(integrated)
            result = await self._integrate_content(final_merged)

        logger.info(f"[思维链] 渐进式整合完成，输出长度: {len(result)} 字符")
        return result

    async def _integrate_chunk_pair(self, content: str, index: int, total: int, style: str = "complete") -> str:
        """
        整合一对相邻的内容块

        Args:
            content: 待整合的内容
            index: 当前块索引
            total: 总块数
            style: 风格参数（complete=严谨完整型，concise=简洁概括型）
        """
        logger.info(f"[思维链] 整合块对 {index + 1}/{total}，风格: {style}")

        # 根据风格调整提示词
        if style == "concise":
            style_instruction = """
5. 简洁概括：精炼表达，删除冗余，保留核心
6. 段落控制：每段50-80字符
"""
        else:
            style_instruction = """
5. 严谨完整：详细论述，保留完整论证过程
6. 段落长度：80-100字符
"""

        prompt = f"""请对以下内容进行逻辑检查和语言润色，使其符合公文标准。

要求：
1. 保持两个部分之间的逻辑连贯性
2. 统一语言风格
3. 修正明显的语言错误
4. 不要实质性修改内容
{style_instruction}
【内容】
{content}
"""

        response = await self.client.chat.completions.create(
            model=self.KIMI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个公文写作专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=20000,
            timeout=120.0
        )

        return response.choices[0].message.content

    async def _export_to_word(
        self,
        markdown_content: str,
        output_filename: str
    ) -> tuple[bytes, str]:
        """
        导出为Word文档

        Args:
            markdown_content: Markdown格式的内容
            output_filename: 输出文件名

        Returns:
            (文件字节流, MIME类型)
        """
        logger.info(f"[思维链] 开始导出Word文档")

        try:
            from utils.markdown_to_word import MarkdownToWordConverter

            converter = MarkdownToWordConverter()

            # 转换为Word
            doc_bytes = converter.convert(markdown_content)

            logger.info(f"[思维链] Word文档生成完成，大小: {len(doc_bytes)} 字节")

            return doc_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        except ImportError as e:
            logger.error(f"[ERROR] Word导出功能不可用: {e}")
            raise ImportError(
                "python-docx 未安装，请运行: pip install python-docx"
            ) from e


# 单例实例
academic_to_official_service = AcademicToOfficialService()
