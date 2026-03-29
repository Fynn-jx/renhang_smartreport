import { motion } from "motion/react";
import {
  ArrowLeft,
  ExternalLink,
  Globe2,
  BarChart2,
  TrendingUp,
  Database,
  BookOpen,
} from "lucide-react";

interface DataSourcePanelProps {
  sourceId: string;
  onBack: () => void;
}

// 数据源条目接口（长条细格子展示）
interface DataSourceItem {
  id: string;
  name: string;
  number: string; // 编号
  url: string;
  icon: React.ElementType;
  color: string;
  description?: string;
}

// 数据源列表（长条细格子风格）
const dataSourceList: DataSourceItem[] = [
  {
    id: "imf",
    name: "国际货币基金组织 (IMF)",
    number: "IMF-001",
    url: "https://www.imf.org",
    icon: BarChart2,
    color: "#2563eb",
    description: "全球经济监测、金融稳定、地区经济展望报告",
  },
  {
    id: "uneca",
    name: "联合国非洲经济委员会 (UNECA)",
    number: "UN-001",
    url: "https://www.uneca.org",
    icon: Globe2,
    color: "#059669",
    description: "非洲区域经济研究、金融科技、可持续发展",
  },
  {
    id: "afdb",
    name: "非洲开发银行 (AfDB)",
    number: "AFDB-001",
    url: "https://www.afdb.org",
    icon: TrendingUp,
    color: "#0891b2",
    description: "非洲经济展望、发展政策、宏观经济分析",
  },
  {
    id: "worldbank",
    name: "世界银行 (World Bank)",
    number: "WB-001",
    url: "https://www.worldbank.org",
    icon: Database,
    color: "#ea580c",
    description: "全球发展数据、国别研究、开放知识库",
  },
  {
    id: "wto",
    name: "世界贸易组织 (WTO)",
    number: "WTO-001",
    url: "https://www.wto.org",
    icon: TrendingUp,
    color: "#06b6d4",
    description: "全球贸易统计、贸易政策、经济研究",
  },
  {
    id: "oecd",
    name: "经合组织 (OECD)",
    number: "OECD-001",
    url: "https://www.oecd.org",
    icon: Database,
    color: "#10b981",
    description: "经济政策分析、统计数据、展望报告",
  },
  {
    id: "un",
    name: "联合国 (United Nations)",
    number: "UN-002",
    url: "https://www.un.org",
    icon: Globe2,
    color: "#059669",
    description: "全球发展议程、可持续发展目标、政策报告",
  },
  {
    id: "pbc",
    name: "中国人民银行",
    number: "PBC-001",
    url: "https://www.pbc.gov.cn",
    icon: BarChart2,
    color: "#dc2626",
    description: "货币政策、金融稳定、统计报告",
  },
  {
    id: "stats",
    name: "国家统计局",
    number: "STATS-001",
    url: "https://www.stats.gov.cn",
    icon: Database,
    color: "#f97316",
    description: "宏观经济数据、统计年鉴、国民经济核算",
  },
  {
    id: "mckinsey",
    name: "麦肯锡全球研究院",
    number: "MGI-001",
    url: "https://www.mckinsey.com",
    icon: BookOpen,
    color: "#6366f1",
    description: "经济研究、行业分析、全球趋势",
  },
  {
    id: "bcg",
    name: "波士顿咨询 (BCG)",
    number: "BCG-001",
    url: "https://www.bcg.com",
    icon: BookOpen,
    color: "#ec4899",
    description: "战略咨询、行业洞察、经济研究",
  },
  {
    id: "bain",
    name: "贝恩公司",
    number: "BAIN-001",
    url: "https://www.bain.com",
    icon: BookOpen,
    color: "#14b8a6",
    description: "全球商业趋势、市场研究、战略咨询",
  },
];

export function DataSourcePanel({ sourceId, onBack }: DataSourcePanelProps) {
  // Show all sources when sourceId is "dataSource" (长条细格子展示)
  if (sourceId === "dataSource") {
    return (
      <div className="h-full flex flex-col overflow-hidden">
        {/* Header */}
        <div
          className="flex-shrink-0 flex items-center gap-4 px-6 py-4"
          style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#fff" }}
        >
          <motion.button
            whileHover={{ backgroundColor: "#f1f5f9" }}
            whileTap={{ scale: 0.95 }}
            onClick={onBack}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
            style={{ border: "1px solid #e2e8f0", color: "#64748b", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}
          >
            <ArrowLeft size={14} />
            返回
          </motion.button>
          <div>
            <h1
              style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 18, fontWeight: 600 }}
            >
              数据源
            </h1>
            <p style={{ color: "#94a3b8", fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 2 }}>
              点击数据源跳转访问，通过浏览器插件下载报告到前沿报告库
            </p>
          </div>
        </div>

        {/* Data Source Grid - 长条细格子风格 */}
        <div className="flex-1 overflow-auto p-6">
          {/* 表头 */}
          <div
            className="grid gap-3 px-4 pb-3 mb-3 border-b text-xs font-medium"
            style={{
              display: "grid",
              gridTemplateColumns: "80px 2fr 2.5fr 80px",
              color: "#64748b",
              fontFamily: "'Noto Sans SC', sans-serif",
              borderBottom: "1px solid #e2e8f0",
            }}
          >
            <div>编号</div>
            <div>网址名称</div>
            <div>URL</div>
            <div style={{ textAlign: "center" }}>操作</div>
          </div>

          {/* 数据源列表 */}
          <div className="space-y-1.5">
            {dataSourceList.map((source, index) => {
              const Icon = source.icon;
              return (
                <motion.a
                  key={source.id}
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03 }}
                  className="grid gap-3 px-4 py-3 rounded-lg items-center group"
                  style={{
                    display: "grid",
                    gridTemplateColumns: "80px 2fr 2.5fr 80px",
                    backgroundColor: "#fff",
                    border: "1px solid #e2e8f0",
                    transition: "all 0.15s",
                  }}
                  whileHover={{
                    borderColor: source.color,
                    backgroundColor: `${source.color}04`,
                    boxShadow: `0 2px 8px ${source.color}15`,
                  }}
                >
                  {/* 编号 */}
                  <div
                    className="text-xs font-mono rounded px-2 py-1 text-center"
                    style={{
                      color: source.color,
                      backgroundColor: `${source.color}10`,
                      fontFamily: "'JetBrains Mono', monospace",
                      fontWeight: 500,
                    }}
                  >
                    {source.number}
                  </div>

                  {/* 网址名称 */}
                  <div className="flex items-center gap-2">
                    <div
                      className="flex items-center justify-center rounded flex-shrink-0"
                      style={{
                        width: 28,
                        height: 28,
                        backgroundColor: `${source.color}10`,
                      }}
                    >
                      <Icon size={14} style={{ color: source.color }} />
                    </div>
                    <span
                      className="text-sm font-medium truncate"
                      style={{
                        color: "#0f172a",
                        fontFamily: "'Noto Sans SC', sans-serif",
                      }}
                    >
                      {source.name}
                    </span>
                  </div>

                  {/* URL */}
                  <div
                    className="text-xs truncate flex items-center gap-1"
                    style={{
                      color: "#64748b",
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    {source.url}
                  </div>

                  {/* 操作 */}
                  <div className="flex justify-center">
                    <motion.div
                      className="flex items-center justify-center rounded-full"
                      style={{
                        width: 28,
                        height: 28,
                        backgroundColor: "#f8fafc",
                        border: "1px solid #e2e8f0",
                      }}
                      whileHover={{
                        backgroundColor: source.color,
                        borderColor: source.color,
                      }}
                      transition={{ duration: 0.15 }}
                    >
                      <ExternalLink
                        size={13}
                        style={{
                          color: "#94a3b8",
                          transition: "color 0.15s",
                        }}
                        className="group-hover/[a]:text-white"
                      />
                    </motion.div>
                  </div>
                </motion.a>
              );
            })}
          </div>

          {/* 使用提示 */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mt-6 p-4 rounded-lg"
            style={{
              backgroundColor: "#fef2f2",
              border: "1px solid #fecaca",
            }}
          >
            <div className="flex gap-3">
              <div
                className="flex-shrink-0 flex items-center justify-center rounded-full"
                style={{
                  width: 32,
                  height: 32,
                  backgroundColor: "rgba(155, 28, 28, 0.1)",
                }}
              >
                <ExternalLink size={16} style={{ color: "#9b1c1c" }} />
              </div>
              <div className="flex-1">
                <div
                  className="text-sm font-medium mb-1"
                  style={{
                    color: "#9b1c1c",
                    fontFamily: "'Noto Sans SC', sans-serif",
                  }}
                >
                  使用链路
                </div>
                <div
                  className="text-xs leading-relaxed"
                  style={{
                    color: "#b91c1c",
                    fontFamily: "'Noto Sans SC', sans-serif",
                  }}
                >
                  登录平台 → 点击数据源跳转 → 浏览报告 → 使用浏览器插件下载到前沿报告库 →
                  选择功能（对照翻译/公文写作）→ AI 处理 → 导出 Word
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  // 单个数据源详情视图（如果点击了某个具体数据源）
  const source = dataSourceList.find((s) => s.id === sourceId);
  if (!source) return null;
  const Icon = source.icon;

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div
        className="flex-shrink-0 flex items-center gap-4 px-6 py-4"
        style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#fff" }}
      >
        <motion.button
          whileHover={{ backgroundColor: "#f1f5f9" }}
          whileTap={{ scale: 0.95 }}
          onClick={onBack}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
          style={{ border: "1px solid #e2e8f0", color: "#64748b", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}
        >
          <ArrowLeft size={14} />
          返回
        </motion.button>
        <div
          className="flex items-center justify-center rounded-xl flex-shrink-0"
          style={{ width: 40, height: 40, backgroundColor: `${source.color}10`, border: `1px solid ${source.color}22` }}
        >
          <Icon size={20} style={{ color: source.color }} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h1
              style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 18, fontWeight: 600 }}
            >
              {source.name}
            </h1>
            <span
              className="px-2 py-0.5 rounded text-xs font-mono"
              style={{
                color: source.color,
                backgroundColor: `${source.color}10`,
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              {source.number}
            </span>
          </div>
          {source.description && (
            <p style={{ color: "#64748b", fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 2 }}>
              {source.description}
            </p>
          )}
        </div>
        <div className="ml-auto">
          <motion.a
            whileHover={{ scale: 1.02 }}
            href={source.url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-white"
            style={{
              backgroundColor: source.color,
              fontFamily: "'Noto Sans SC', sans-serif",
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            <ExternalLink size={14} />
            访问网站
          </motion.a>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="rounded-xl p-6"
          style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0" }}
        >
          <div className="flex items-start gap-4">
            <div
              className="flex items-center justify-center rounded-xl flex-shrink-0"
              style={{
                width: 56,
                height: 56,
                backgroundColor: `${source.color}10`,
                border: `1px solid ${source.color}22`,
              }}
            >
              <Icon size={28} style={{ color: source.color }} />
            </div>
            <div className="flex-1">
              <h2
                className="mb-2"
                style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 16, fontWeight: 600 }}
              >
                {source.name}
              </h2>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span
                    className="text-xs px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: "#f1f5f9",
                      color: "#64748b",
                      fontFamily: "'Noto Sans SC', sans-serif",
                    }}
                  >
                    编号
                  </span>
                  <span
                    className="text-xs font-mono"
                    style={{
                      color: source.color,
                      fontFamily: "'JetBrains Mono', monospace",
                      fontWeight: 500,
                    }}
                  >
                    {source.number}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className="text-xs px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: "#f1f5f9",
                      color: "#64748b",
                      fontFamily: "'Noto Sans SC', sans-serif",
                    }}
                  >
                    网址
                  </span>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs hover:underline flex items-center gap-1"
                    style={{
                      color: source.color,
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    {source.url}
                    <ExternalLink size={10} />
                  </a>
                </div>
                {source.description && (
                  <div className="mt-3 p-3 rounded-lg" style={{ backgroundColor: "#f8fafc" }}>
                    <p
                      className="text-sm leading-relaxed"
                      style={{ color: "#475569", fontFamily: "'Noto Sans SC', sans-serif" }}
                    >
                      {source.description}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
