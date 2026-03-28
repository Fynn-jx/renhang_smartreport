# 国别研究工作流设计文档

## 概述

国别研究工作流实现了数据源插拔式设计，支持动态添加/切换国家数据源，并提供关键节点思维链输出用于前端展示。

## 架构设计

```
┌──────────────────────────────────────────────────────────���──────┐
│                        前端 API 层                                │
│  /workflows/country-research                                      │
│  /workflows/country-research/countries                            │
│  /workflows/country-research/countries/{code}                     │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     工作流服务层                                  │
│  CountryResearchService                                          │
│  - process_country_research()                                    │
│  - _fetch_data_sources()                                         │
│  - _analyze_economy()                                            │
│  - _analyze_politics()                                           │
│  - _analyze_diplomacy()                                          │
│  - _generate_report()                                            │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    数据源配置层                                   │
│  CountryDataSourceRegistry                                       │
│  - register_country()                                            │
│  - get_country()                                                 │
│  - list_countries()                                              │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    数据源配置存储                                 │
│  CountryProfile                                                  │
│  - country_code, country_name                                    │
│  - region, income_level, currency                                │
│  - data_sources: List[DataSourceConfig]                          │
└─────────────────────────────────────────────────────────────────┘
```

## 工作流阶段

| 阶段 | 进度范围 | 说明 | 思维链节点 |
|------|----------|------|------------|
| CONFIG_LOADING | 0-5% | 加载国家配置和数据源列表 | ✅ |
| DATA_FETCHING | 5-25% | 并发抓取各数据源内容 | ✅ 每个数据源一个节点 |
| ECONOMIC_ANALYSIS | 25-45% | 分析GDP、通胀、货币政策等 | ✅ |
| POLITICAL_ANALYSIS | 45-60% | 分析国家元首、政治体制 | ✅ |
| DIPLOMACY_ANALYSIS | 60-75% | 重点分析对华关系 | ✅ |
| REPORT_GENERATION | 75-90% | 整合分析结果生成报告 | ✅ |
| QUALITY_REVIEW | 90-98% | 检查完整性和规范性 | ✅ |

## 思维链节点结构

```json
{
  "stage": "data_fetching",
  "node_id": "fetch_0",
  "title": "采集数据源: GDP增速",
  "content": "URL: https://...\n类型: trading_economics",
  "timestamp": "2024-01-01T12:00:00",
  "metadata": {
    "source_type": "trading_economics",
    "url": "https://..."
  }
}
```

## API 端点

### 1. 执行国别研究工作流

```
POST /api/v1/workflows/country-research

参数:
- country_code: 国家代码 (如 EG, SA, BR)
- reference_file: 参考文件（可选）

返回: SSE 流式输出
```

### 2. 获取国家列表

```
GET /api/v1/workflows/country-research/countries

返回:
{
  "countries": [
    {
      "code": "EG",
      "name": "埃及",
      "name_en": "Egypt",
      "region": "中东, 北非",
      "income_level": "中等收入",
      "currency": "EGP",
      "data_source_count": 18
    }
  ]
}
```

### 3. 获取国家详情

```
GET /api/v1/workflows/country-research/countries/{country_code}

返回: 指定国家的数据源配置详情
```

### 4. 获取工作流阶段

```
GET /api/v1/workflows/country-research/stages

返回: 所有工作流阶段信息
```

## 添加新国家

### 方法一：通过代码添加

```python
from configs.country_data_sources import (
    CountryDataSourceRegistry,
    CountryProfile,
    DataSourceConfig,
    DataSourceType
)

# 创建国家配置
uae_config = CountryProfile(
    country_code="AE",
    country_name="阿联酋",
    country_name_en="United Arab Emirates",
    region="中东",
    income_level="高收入",
    currency="AED",
    data_sources=[
        DataSourceConfig(
            name="GDP增速",
            type=DataSourceType.TRADING_ECONOMICS,
            url="https://zh.tradingeconomics.com/united-arab-emirates/gdp-growth-annual",
            label="GDP增速 (Trading Economics)",
        ),
        # 添加更多数据源...
    ]
)

# 注册
CountryDataSourceRegistry.register_country(uae_config)
```

### 方法二：通过JSON配置文件

1. 编辑 `configs/countries_config.json`
2. 添加国家配置
3. 使用 `load_countries_from_json()` 加载

## 数据源类型

| 类型 | 说明 | 示例 |
|------|------|------|
| trading_economics | Trading Economics 经济指标 | GDP、通胀、失业率 |
| central_bank | 央行官网 | 货币政策、利率决议 |
| ministry_finance | 财政部 | 财政预算、税收政策 |
| news_agency | 新闻社 | 最新经济新闻 |
| government_portal | 政府门户 | 官方统计数据 |
| imf_world_bank | IMF/世界银行 | 国际金融合作 |
| china_mfa | 中国外交部 | 国家概况、对华关系 |
| investing | 英为财情 | 国债收益率 |

## 文件结构

```
backend/
├── configs/
│   ├── __init__.py
│   ├── country_data_sources.py          # 数据源配置系统
│   ├── country_data_sources_example.py   # 添加国家示例
│   └── countries_config_example.json     # JSON配置示例
├── services/
│   └── country_research_service.py       # 国别研究服务
└── api/endpoints/
    └── workflows.py                       # API端点
```

## 前端集成

### 获取国家列表选择器

```javascript
const response = await fetch('/api/v1/workflows/country-research/countries');
const data = await response.json();
// 渲染国家选择器
```

### 执行工作流并接收思维链

```javascript
const formData = new FormData();
formData.append('country_code', 'EG');

// 可选：添加用户补充数据源
const userSources = [
  {name: "央行最新报告", url: "https://centralbank.example.com/report"},
  {name: "经济新闻", url: "https://news.example.com/economy"}
];
formData.append('user_sources', JSON.stringify(userSources));

const response = await fetch('/api/v1/workflows/country-research', {
  method: 'POST',
  body: formData
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));

      // 更新进度条
      updateProgress(data.progress);

      // 显示思维链节点
      if (data.thinking_node) {
        addThinkingNode(data.thinking_node);
      }

      console.log(data.message);
    }
  }
}
```

### 思维链展示组件

```javascript
function addThinkingNode(node) {
  // node 包含:
  // - title: 节点标题
  // - content: 节点内容
  // - timestamp: 时间戳
  // - metadata: 元数据

  const nodeElement = document.createElement('div');
  nodeElement.className = 'thinking-node';
  nodeElement.innerHTML = `
    <div class="node-title">${node.title}</div>
    <div class="node-content">${node.content}</div>
    <div class="node-time">${node.timestamp}</div>
  `;

  document.getElementById('thinking-chain').appendChild(nodeElement);
}
```

## 预置国家

当前已预置**49个非洲国家**：

| 国家代码 | 国家中文名 | 数据源数量 | 说明 |
|---------|-----------|-----------|------|
| **EG** | **埃及** | **18个** | ✅ **唯一完整配置** |
| 其他48国 | 如: KE(肯尼亚), NG(尼日利亚), ZA(南非) 等 | 3个 | 基础配置 (GDP增速、通胀率、失业率) |

### 按区域分布：
- **北非**: 7国 (埃及、阿尔及利亚、利比亚、摩洛哥、突尼斯、苏丹、西撒哈拉)
- **东非**: 14国 (埃塞俄比亚、肯尼亚、坦桑尼亚等)
- **西非**: 10国 (尼日利亚、加纳、科特迪瓦等)
- **中非**: 9国 (喀麦隆、刚果布、加蓬等)
- **南非**: 9国 (南非、纳米比亚、博茨瓦纳等)

## 用户补充数据源

前端可以允许用户为任意国家添加补充数据源：

```javascript
// 用户添加的数据源格式
const userSources = [
  {
    name: "央行2024年度报告",
    url: "https://centralbank.example.com/2024-report.pdf"
  },
  {
    name: "最新经济新闻",
    url: "https://news.example.com/economy-latest"
  }
];

// 通过API发送
formData.append('user_sources', JSON.stringify(userSources));
```

## 爬虫配置

使用 **Firecrawl** 进行网页内容提取：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| API Key | `fc-35ad753d0ef8430e9109612903220c72` | 已配置 |
| Base URL | `https://api.firecrawl.dev` | Firecrawl API |
| 后备方案 | httpx | 当Firecrawl不可用时 |

爬取格式：
- **Markdown** (默认) - 适合AI处理
- HTML - 原始HTML
- Extract - 结构化提取
