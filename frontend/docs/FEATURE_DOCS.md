# 文献与公文库 - 功能说明文档

## 概述

文献与公文库是 AI 研究工作站的核心模块之一，用于管理、浏览和处理金融经济类研报文档。支持文档列表展示、筛选、预览、AI 对照翻译和 AI 公文写作等功能。

---

## 模块入口

- **路径**: `/src/app/components/LibraryModule.tsx`
- **主组件**: `LibraryModule`
- **状态管理**: 使用 React `useState` 本地状态

---

## 数据结构

### 文档对象 (Doc)

```typescript
interface Doc {
  id: number;                    // 文档唯一标识
  title: string;                 // 文档标题
  institution: string;           // 发布机构
  date: string;                  // 上传日期 (YYYY-MM-DD 格式)
  tags: string[];                // 标签数组
  aiStatus: "已完成" | "处理中" | "待处理";  // AI 处理状态
  abstract: string;              // 摘要内容
  source: Source;                // 来源网站
}

// 来源网站类型
type Source =
  | "世界银行" | "IMF" | "联合国" | "联合国非洲经济委员会"
  | "非洲开发银行" | "WTO" | "OECD" | "尼尔森"
  | "麦肯锡" | "波士顿咨询" | "贝恩"
  | "中国人民银行" | "国家统计局" | "其他";

// 来源配置 (用于显示颜色)
const sourceConfig: Record<Source, { url: string; color: string }>
```

### 日期筛选

```typescript
type DateFilter = "全部" | string;  // string 为 YYYY-MM-DD 格式的具体日期

// 获取文档中的所有唯一日期 (按月分组)
const getDocumentDates = (): string[] => {
  const dates = documents.map((doc) => doc.date);
  return [...new Set(dates)].sort().reverse();
};
```

---

## 功能模块

### 1. 筛选面板 (FilterPanel)

**位置**: 搜索栏右侧的"筛选"按钮

**筛选条件**:
- **日期筛选**: 类似微信查找聊天记录的小日历，按月份分组显示有文档的日期
  - 有文档的日期为亮色，可点击
  - 无文档的日期显示为暗色，不可点击
  - 点击具体日期可筛选该日期的文档
  - 点击"清除"可取消日期筛选

- **来源筛选**: 多选来源网站
  - 点击可选中/取消选中
  - 来源使用颜色区分 (配置在 `sourceConfig` 中)

**实现要点**:
- 点击外部自动关闭筛选面板
- 筛选按钮在有筛选条件时显示红色 Badge 提示数量
- 清除全部按钮可一键重置所有筛选条件

---

### 2. 文档列表 (TableView)

**展示列**:
| 列名 | 说明 |
|------|------|
| 研报标题 | 文档标题，左侧带文件图标 |
| 来源 | 来源网站，颜色编码显示 |
| 上传日期 | 格式: YYYY-MM-DD |
| 标签 | 多个标签用 Badge 展示 |
| AI处理状态 | 已完成(绿) / 处理中(黄) / 待处理(灰) |
| 操作 | 更多操作按钮 |

**搜索功能**:
- 支持按标题、机构、标签模糊搜索
- 搜索结果实时过滤

**统计信息**:
- 显示文档总数和已完成 AI 处理的文档数
- 有筛选条件时显示"已筛选"提示

---

### 3. 文档预览 (DocumentPreview)

点击文档行进入预览模式，展示完整文档信息：

- 标题、机构、日期、摘要
- 标签和来源 Badge
- AI 处理状态 Badge
- **操作按钮**:
  - "对照翻译": 打开 AI 翻译配置
  - "公文写作": 打开 AI 写作配置

---

### 4. AI 处理功能

#### 配置弹窗 (ConfigModal)

选择 AI 模型和附加参考文件：

```typescript
interface AiConfig {
  model: string;       // 模型名称 (如 "DeepSeek V3")
  files: string[];     // 附加的参考文件名
}

// 可选模型
const models = [
  { id: "deepseek", label: "DeepSeek V3", desc: "综合性能最优" },
  { id: "claude", label: "Claude 3.5", desc: "长文本理解强" },
  { id: "gpt4o", label: "GPT-4o", desc: "多语言翻译精" },
  { id: "qwen", label: "Qwen-Max", desc: "中文专项优化" },
];
```

#### 翻译/写作模式

- **对照翻译**: 左侧显示原始文献，右侧显示 AI 翻译
- **公文写作**: 左侧显示原始文献，右侧显示 AI 生成的人民银行格式公文

**分屏视图**:
- 使用 `react-resizable-panels` 实现可拖拽的分屏
- 左右两侧可调整宽度比例
- 左侧: 原始文献阅读器 (OriginalDocViewer)
- 右侧: AI 写作舱 (AIWritingCabin)

#### 思维链 (ThinkingChain)

展示 AI 处理过程中的思考步骤：
- 动态显示思考步骤列表
- 步骤依次高亮出现
- 处理完成后显示生成内容

---

## 组件层级

```
LibraryModule
├── FilterPanel (筛选面板)
│   └── CalendarPicker (日历选择器)
├── TableView (文档列表)
│   └── StatusBadge, TagBadge
├── DocumentPreview (文档预览)
│   └── StatusBadge, TagBadge
├── ConfigModal (AI配置弹窗)
├── OriginalDocViewer (原始文献)
├── AIWritingCabin (AI写作舱)
│   └── ThinkingChain (思维链)
└── NarrowList (窄列表模式 - 预留)
```

---

## 状态流转

```
LibState = "A" | "B" | "C"

A: TableView (文档列表)
   └── 点击文档 → B

B: DocumentPreview (文档预览)
   ├── 点击"对照翻译"/"公文写作" → 弹出 ConfigModal
   │   └── 确认配置 → C
   └── 点击返回 → A

C: 分屏视图 (原始文献 + AI写作舱)
   └── 点击返回 → B
```

---

## API 接口需求 (后端)

后端需要实现以下接口供前端调用：

### 1. 获取文档列表

```http
GET /api/documents

Query Parameters:
- search?: string        # 搜索关键词
- source?: string[]      # 来源筛选 (可选多个)
- date?: string         # 日期筛选 (YYYY-MM-DD)
- page?: number         # 页码
- pageSize?: number     # 每页数量

Response:
{
  items: Doc[];
  total: number;
  page: number;
  pageSize: number;
}
```

### 2. 获取文档详情

```http
GET /api/documents/:id

Response: Doc
```

### 3. AI 翻译

```http
POST /api/ai/translate

Request Body:
{
  documentId: number;
  model: string;
  referenceFiles?: string[];
}

Response:
{
  thinkingChain: string[];
  result: string;  # 翻译内容
}
```

### 4. AI 公文写作

```http
POST /api/ai/write

Request Body:
{
  documentId: number;
  model: string;
  referenceFiles?: string[];
  outputFormat: "official" | "brief";  # 公文格式
}

Response:
{
  thinkingChain: string[];
  result: string;  # 生成的公文内容
}
```

### 5. 获取可筛选的日期列表

```http
GET /api/documents/dates

Response:
{
  dates: string[];  # YYYY-MM-DD 格式日期数组
}
```

### 6. 获取来源列表

```http
GET /api/sources

Response:
{
  sources: Array<{
    id: string;
    name: string;
    color: string;
    url: string;
  }>;
}
```

---

## 关键常量

### 来源配置

```typescript
const sourceConfig = {
  "世界银行": { url: "worldbank.org", color: "#ea580c" },
  "IMF": { url: "imf.org", color: "#2563eb" },
  // ... 其他来源
};
```

### 状态 Badge 配置

```typescript
const statusConfig = {
  "已完成": { color: "#16a34a", bg: "#f0fdf4", icon: CheckCircle2 },
  "处理中": { color: "#d97706", bg: "#fffbeb", icon: Clock },
  "待处理": { color: "#94a3b8", bg: "#f8fafc", icon: Circle },
};
```

---

## 样式规范

- **字体**: Noto Sans SC (中文)
- **主色调**: #9b1c1c (深红，人行主题色)
- **背景色**: #f8fafc (浅灰蓝)
- **边框色**: #e2e8f0
- **文字色**: #0f172a (标题), #64748b (次要)

---

## 注意事项

1. **日期格式**: 统一使用 `YYYY-MM-DD` 格式
2. **来源字段**: 需与 `sourceConfig` 中的键名完全匹配
3. **AI 处理**: 实际调用后端 API，前端仅做展示
4. **分屏**: 使用 `react-resizable-panels`，需设置 `minSize` 防止过小
