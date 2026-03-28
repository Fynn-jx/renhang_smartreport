// 文献文档相关类型

// 来源网站分类
export type Source =
  | "世界银行"
  | "IMF"
  | "联合国"
  | "联合国非洲经济委员会"
  | "非洲开发银行"
  | "WTO"
  | "OECD"
  | "尼尔森"
  | "麦肯锡"
  | "波士顿咨询"
  | "贝恩"
  | "中国人民银行"
  | "国家统计局"
  | "其他";

// 日期筛选类型
export type DateFilter = "全部" | string;

// 文档接口
export interface Doc {
  id: number;
  title: string;
  institution: string;
  date: string;
  tags: string[];
  aiStatus: "已完成" | "处理中" | "待处理";
  abstract: string;
  source: Source;
}

// AI 配置接口
export interface AiConfig {
  model: string;
  files: string[];
}

// AI 模式
export type AiMode = "translate" | "write" | null;

// 文献库状态
export type LibState = "A" | "B" | "C";
