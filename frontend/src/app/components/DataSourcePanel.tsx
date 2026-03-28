import { motion } from "motion/react";
import {
  ArrowLeft,
  ExternalLink,
  Globe2,
  BarChart2,
  TrendingUp,
  Database,
} from "lucide-react";

interface DataSourcePanelProps {
  sourceId: string;
  onBack: () => void;
}

interface Dataset {
  name: string;
  desc: string;
  frequency: string;
  coverage: string;
  lastUpdated: string;
  tags: string[];
}

interface SourceInfo {
  id: string;
  label: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  intro: string;
  url: string;
  datasets: Dataset[];
}

const sourcesData: SourceInfo[] = [
  {
    id: "uneca",
    label: "联合国非洲经济委员会 (UNECA)",
    icon: Globe2,
    color: "#059669",
    bgColor: "#ecfdf5",
    intro:
      "联合国非洲经济委员会（UNECA）聚焦非洲大陆特定区域或专题（如金融科技、普惠金融），分析深入，常包含详实的案例和数据。核心报告如《东非地区金融科技研究》等区域性深度报告。",
    url: "https://www.uneca.org",
    datasets: [
      {
        name: "东非地区金融科技研究",
        desc: "聚焦东非地区金融科技发展、数字化转型及普惠金融创新",
        frequency: "不定期",
        coverage: "东非地区",
        lastUpdated: "2024-10-15",
        tags: ["金融科技", "东非", "数字化"],
      },
      {
        name: "非洲经济展望",
        desc: "非洲大陆经济增长预测、区域发展及可持续发展目标进展",
        frequency: "年度",
        coverage: "非洲全境",
        lastUpdated: "2024-09-01",
        tags: ["经济展望", "GDP", "可持续发展"],
      },
    ],
  },
  {
    id: "afdb",
    label: "非洲开发银行 (AfDB)",
    icon: TrendingUp,
    color: "#0891b2",
    bgColor: "#ecfeff",
    intro:
      "非洲开发银行（AfDB）的年度《非洲经济展望》是其旗舰报告，涵盖经济增长、财政政策、债务可持续性等宏观金融议题。数据权威，预测性强，是研判非洲宏观经济和金融环境最重要的参考资料之一。",
    url: "https://www.afdb.org",
    datasets: [
      {
        name: "非洲经济展望",
        desc: "年度旗舰报告，涵盖经济增长、财政政策、债务可持续性等宏观金融议题",
        frequency: "年度",
        coverage: "非洲54国",
        lastUpdated: "2024-11-01",
        tags: ["经济展望", "财政", "债务"],
      },
      {
        name: "非洲发展展望",
        desc: "长期发展愿景、工业化进程及区域一体化分析",
        frequency: "年度",
        coverage: "非洲全境",
        lastUpdated: "2024-06-15",
        tags: ["发展", "工业化", "区域一体化"],
      },
    ],
  },
  {
    id: "worldbank",
    label: "世界银行 (World Bank)",
    icon: Database,
    color: "#ea580c",
    bgColor: "#fff7ed",
    intro:
      "世界银行（World Bank）的DataBank数据库和Open Knowledge Repository知识库提供海量的国别和时间序列数据，其研究报告（如《非洲银行业》等）基于严谨的实证分析，学术价值高。",
    url: "https://www.worldbank.org",
    datasets: [
      {
        name: "DataBank数据库",
        desc: "海量的国别和时间序列数据，覆盖经济发展、社会指标、环境等",
        frequency: "持续更新",
        coverage: "全球200+国家",
        lastUpdated: "2024-12-01",
        tags: ["数据库", "时间序列", "国别"],
      },
      {
        name: "Open Knowledge Repository",
        desc: "世界银行研究报告库，包含《非洲银行业》等深度研究",
        frequency: "持续更新",
        coverage: "全球",
        lastUpdated: "2024-12-01",
        tags: ["研究报告", "非洲", "银行"],
      },
    ],
  },
  {
    id: "imf",
    label: "国际货币基金组织 (IMF)",
    icon: BarChart2,
    color: "#2563eb",
    bgColor: "#eff6ff",
    intro:
      "国际货币基金组织（IMF）的IMF eLibrary和IMF DATA平台提供《地区经济展望》（含撒哈拉以南非洲）、《全球金融稳定报告》等，重点关注财政、债务、汇率及金融稳定等议题。",
    url: "https://www.imf.org",
    datasets: [
      {
        name: "IMF eLibrary",
        desc: "IMF官方出版物、研究报告及工作论文全文数据库",
        frequency: "持续更新",
        coverage: "全球",
        lastUpdated: "2024-12-01",
        tags: ["出版物", "研究", "报告"],
      },
      {
        name: "IMF DATA",
        desc: "宏观经济统计数据、国际收支、汇率及金融稳定指标",
        frequency: "持续更新",
        coverage: "全球190+国家",
        lastUpdated: "2024-12-01",
        tags: ["数据", "统计", "汇率"],
      },
      {
        name: "地区经济展望",
        desc: "撒哈拉以南非洲地区经济展望，关注财政、债务、汇率及金融稳定",
        frequency: "年度",
        coverage: "撒哈拉以南非洲",
        lastUpdated: "2024-10-15",
        tags: ["非洲", "经济展望", "债务"],
      },
    ],
  },
];

export function DataSourcePanel({ sourceId, onBack }: DataSourcePanelProps) {
  // Show all sources when sourceId is "dataSource"
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
          <h1
            style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 18, fontWeight: 600 }}
          >
            数据源
          </h1>
        </div>

        {/* All Sources List */}
        <div className="flex-1 overflow-auto p-6">
          <div className="grid gap-4">
            {sourcesData.map((source) => {
              const Icon = source.icon;
              return (
                <motion.a
                  key={source.id}
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-4 p-4 rounded-xl cursor-pointer"
                  style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0" }}
                  whileHover={{ backgroundColor: "#f8fafc", borderColor: "#cbd5e1" }}
                >
                  <div
                    className="flex items-center justify-center rounded-xl flex-shrink-0"
                    style={{ width: 48, height: 48, backgroundColor: source.bgColor, border: `1px solid ${source.color}22` }}
                  >
                    <Icon size={24} style={{ color: source.color }} />
                  </div>
                  <div className="flex-1">
                    <h3 style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 16, fontWeight: 600 }}>
                      {source.label}
                    </h3>
                    <p style={{ color: "#64748b", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 4 }}>
                      {source.intro.slice(0, 60)}...
                    </p>
                  </div>
                  <ExternalLink size={16} style={{ color: "#94a3b8" }} />
                </motion.a>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  const source = sourcesData.find((s) => s.id === sourceId);
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
          style={{ width: 40, height: 40, backgroundColor: source.bgColor, border: `1px solid ${source.color}22` }}
        >
          <Icon size={20} style={{ color: source.color }} />
        </div>
        <div>
          <h1
            style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 18, fontWeight: 600 }}
          >
            {source.label}
          </h1>
          <a
            href={source.url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 hover:underline"
            style={{ color: "#94a3b8", fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif" }}
          >
            {source.url}
            <ExternalLink size={10} />
          </a>
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
            访问数据库
          </motion.a>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {/* Intro Banner */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="rounded-xl p-5 mb-5"
          style={{ backgroundColor: source.bgColor, border: `1px solid ${source.color}22` }}
        >
          <p style={{ color: "#374151", fontSize: 14, fontFamily: "'Noto Sans SC', sans-serif", lineHeight: 1.85 }}>
            {source.intro}
          </p>
        </motion.div>

        {/* Datasets */}
        <div>
          <h2
            className="mb-4"
            style={{ color: "#1e293b", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 16, fontWeight: 600 }}
          >
            数据集
          </h2>
          <div className="grid gap-3">
            {source.datasets.map((dataset, index) => (
              <motion.div
                key={dataset.name}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="p-4 rounded-lg"
                style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0" }}
              >
                <div className="flex items-start justify-between mb-2">
                  <h3
                    style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 14, fontWeight: 600 }}
                  >
                    {dataset.name}
                  </h3>
                  <span
                    className="px-2 py-0.5 rounded text-xs"
                    style={{ backgroundColor: "#f1f5f9", color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif" }}
                  >
                    {dataset.frequency}
                  </span>
                </div>
                <p
                  className="mb-3"
                  style={{ color: "#64748b", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", lineHeight: 1.6 }}
                >
                  {dataset.desc}
                </p>
                <div className="flex items-center gap-4 text-xs" style={{ color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif" }}>
                  <span>覆盖范围: {dataset.coverage}</span>
                  <span>更新: {dataset.lastUpdated}</span>
                </div>
                <div className="flex gap-1.5 mt-2.5 flex-wrap">
                  {dataset.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 rounded text-xs"
                      style={{ backgroundColor: `${source.color}11`, color: source.color, fontFamily: "'Noto Sans SC', sans-serif" }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
