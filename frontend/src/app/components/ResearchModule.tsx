import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Globe2,
  ChevronDown,
  Search,
  CheckCircle2,
  Download,
  RotateCcw,
  AlertCircle,
} from "lucide-react";
import { api } from "../../api";

type ResearchState = "form" | "loading" | "result";

// 非洲区域分类
type AfricanRegion = "中非" | "西非" | "北非" | "南非" | "东非";

const regionConfig: Record<AfricanRegion, { color: string; bgColor: string }> = {
  "中非": { color: "#dc2626", bgColor: "#fef2f2" },
  "西非": { color: "#ea580c", bgColor: "#fff7ed" },
  "北非": { color: "#2563eb", bgColor: "#eff6ff" },
  "南非": { color: "#7c3aed", bgColor: "#f5f3ff" },
  "东非": { color: "#059669", bgColor: "#ecfdf5" },
};

const countriesByRegion: Record<AfricanRegion, string[]> = {
  "中非": ["喀麦隆", "刚果（金）", "刚果（布）", "中非共和国", "乍得", "加蓬", "赤道几内亚", "圣多美和普林西比"],
  "西非": ["尼日利亚", "加纳", "科特迪瓦", "塞内加尔", "塞拉利昂", "利比里亚", "马里", "布基纳法索", "尼日尔", "多哥", "贝宁", "冈比亚", "几内亚", "几内亚比绍"],
  "北非": ["埃及", "利比亚", "突尼斯", "阿尔及利亚", "摩洛哥", "苏丹", "南苏丹"],
  "南非": ["南非", "博茨瓦纳", "纳米比亚", "莱索托", "斯威士兰", "津巴布韦", "赞比亚", "马拉维", "莫桑比克", "安哥拉"],
  "东非": ["肯尼亚", "坦桑尼亚", "乌干达", "埃塞俄比亚", "卢旺达", "布隆迪", "索马里", "厄立特里亚", "吉布提", "塞舌尔", "毛里求斯"],
};

const countries = Object.values(countriesByRegion).flat();

// 国家名称到 ISO 3166-1 alpha-2 代码映射（仅非洲国家）
const countryToCode: Record<string, string> = {
  // 中非
  "喀麦隆": "CM",
  "刚果（金）": "CD",
  "刚果（布）": "CG",
  "中非共和国": "CF",
  "乍得": "TD",
  "加蓬": "GA",
  "赤道几内亚": "GQ",
  "圣多美和普林西比": "ST",

  // 西非
  "尼日利亚": "NG",
  "加纳": "GH",
  "科特迪瓦": "CI",
  "塞内加尔": "SN",
  "塞拉利昂": "SL",
  "利比里亚": "LR",
  "马里": "ML",
  "布基纳法索": "BF",
  "尼日尔": "NE",
  "多哥": "TG",
  "贝宁": "BJ",
  "冈比亚": "GM",
  "几内亚": "GN",
  "几内亚比绍": "GW",

  // 北非
  "埃及": "EG",
  "利比亚": "LY",
  "突尼斯": "TN",
  "阿尔及利亚": "DZ",
  "摩洛哥": "MA",
  "苏丹": "SD",
  "南苏丹": "SS",

  // 南非
  "南非": "ZA",
  "博茨瓦纳": "BW",
  "纳米比亚": "NA",
  "莱索托": "LS",
  "斯威士兰": "SZ",
  "津巴布韦": "ZW",
  "赞比亚": "ZM",
  "马拉维": "MW",
  "莫桑比克": "MZ",
  "安哥拉": "AO",

  // 东非
  "肯尼亚": "KE",
  "坦桑尼亚": "TZ",
  "乌干达": "UG",
  "埃塞俄比亚": "ET",
  "卢旺达": "RW",
  "布隆迪": "BI",
  "索马里": "SO",
  "厄立特里亚": "ER",
  "吉布提": "DJ",
  "塞舌尔": "SC",
  "毛里求斯": "MU",
};

const researchTypes = ["国别报告", "季度报告"];

const models = ["DeepSeek V3", "Claude 3.5 Sonnet", "GPT-4o", "Qwen-Max"];

// 国别研究的进度步骤
const countryResearchSteps = [
  {
    label: "配置加载",
    detail: "加载目标国家的数据源配置信息",
    stage: "config_loading",
  },
  {
    label: "数据采集",
    detail: "并发抓取各数据源内容（使用 Firecrawl）",
    stage: "data_fetching",
  },
  {
    label: "经济分析",
    detail: "分析 GDP、通胀、货币政策等核心指标",
    stage: "economic_analysis",
  },
  {
    label: "政治分析",
    detail: "分析国家元首、政府结构等政治状况",
    stage: "political_analysis",
  },
  {
    label: "外交分析",
    detail: "重点分析对华关系和对外关系",
    stage: "diplomacy_analysis",
  },
  {
    label: "报告生成",
    detail: "整合分析结果生成国别研究报告",
    stage: "report_generation",
  },
  {
    label: "质量审核",
    detail: "检查报告完整性、数据准确性和公文规范性",
    stage: "quality_review",
  },
];

// 季度报告的进度步骤
const quarterlyReportSteps = [
  {
    label: "配置加载",
    detail: "加载目标国家的数据源配置信息",
    stage: "config_loading",
  },
  {
    label: "数据采集",
    detail: "并发抓取各数据源内容（使用 Firecrawl）",
    stage: "data_fetching",
  },
  {
    label: "宏观经济分析",
    detail: "分析 GDP、通胀、就业、外贸等实体经济指标",
    stage: "macro_analysis",
  },
  {
    label: "金融市场分析",
    detail: "分析股市、债市、汇率等金融市场指标",
    stage: "financial_market_analysis",
  },
  {
    label: "政策分析",
    detail: "分析货币政策、财政政策动向",
    stage: "policy_analysis",
  },
  {
    label: "风险评估",
    detail: "评估经济前景与潜在风险",
    stage: "risk_assessment",
  },
  {
    label: "报告生成",
    detail: "整合分析结果生成季度报告",
    stage: "report_generation",
  },
  {
    label: "质量审核",
    detail: "检查报告完整性、数据准确性和公文规范性",
    stage: "quality_review",
  },
];

// 自定义下拉框组件
function CustomDropdown({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (val: string) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  // 当选项变化时，确保当前值在选项中
  useEffect(() => {
    if (options.length > 0 && !options.includes(value)) {
      onChange(options[0]);
    }
  }, [options, value, onChange]);

  return (
    <div ref={dropdownRef} className="relative">
      <label
        style={{ color: "#374151", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500, display: "block", marginBottom: 6 }}
      >
        {label}
      </label>
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ backgroundColor: "#f1f5f9" }}
        whileTap={{ scale: 0.99 }}
        className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg outline-none"
        style={{ border: "1px solid #e2e8f0", color: "#0f172a", fontSize: 13.5, fontFamily: "'Noto Sans SC', sans-serif", backgroundColor: "#fff" }}
      >
        <span>{value}</span>
        <motion.div animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.15 }}>
          <ChevronDown size={14} style={{ color: "#94a3b8" }} />
        </motion.div>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.1 }}
            className="absolute top-full left-0 right-0 mt-1 rounded-lg overflow-hidden z-50"
            style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", boxShadow: "0 4px 16px rgba(0,0,0,0.1)" }}
          >
            <div
              className="max-h-60 overflow-y-auto"
              style={{ scrollbarWidth: "thin", scrollbarColor: "#cbd5e1 #f1f5f9" }}
            >
              {options.map((opt) => (
                <button
                  key={opt}
                  onClick={() => {
                    onChange(opt);
                    setIsOpen(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-50 transition-colors"
                  style={{
                    color: opt === value ? "#9b1c1c" : "#0f172a",
                    backgroundColor: opt === value ? "#fef2f2" : "transparent",
                    fontFamily: "'Noto Sans SC', sans-serif",
                  }}
                >
                  {opt}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function ResearchModule() {
  const [state, setState] = useState<ResearchState>("form");
  const [country, setCountry] = useState("");
  const [resType, setResType] = useState("国别分析");
  const [model, setModel] = useState("DeepSeek V3");
  const [currentStep, setCurrentStep] = useState(-1);
  const [displayedResult, setDisplayedResult] = useState("");
  const [resultDone, setResultDone] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState<AfricanRegion | "全部">("全部");
  const [error, setError] = useState<string | null>(null);
  const [currentThinkingNode, setCurrentThinkingNode] = useState<{ title: string; content: string } | null>(null);

  // 根据研究类型选择对应的步骤
  const progressSteps = resType === "国别研究报告" ? countryResearchSteps : quarterlyReportSteps;

  // 根据选中区域过滤国家列表
  const filteredCountries = selectedRegion === "全部"
    ? countries
    : countriesByRegion[selectedRegion as AfricanRegion];

  const startResearch = async () => {
    setState("loading");
    setCurrentStep(0);
    setError(null);
    setDisplayedResult("");
    setResultDone(false);
    setCurrentThinkingNode(null);

    // 获取国家代码
    const countryCode = countryToCode[country];
    if (!countryCode) {
      setError(`未找到国家 "${country}" 的代码映射`);
      setState("form");
      return;
    }

    try {
      // 根据研究类型选择 API
      const stream = resType === "国别研究报告"
        ? await api.startCountryResearch({
            country_code: countryCode,
          })
        : await api.startQuarterlyReport({
            country_code: countryCode,
          });

      const reader = stream.getReader();
      const decoder = new TextDecoder();

      let buffer = "";
      let resultBuffer = "";

      // 后端 stage 到前端步骤的映射 - 根据研究类型选择不同的映射
      const stageToStepIndex: Record<string, number> = resType === "国别研究报告"
        ? {
            "config_loading": 0,
            "data_fetching": 1,
            "economic_analysis": 2,
            "political_analysis": 3,
            "diplomacy_analysis": 4,
            "report_generation": 5,
            "quality_review": 6,
            "completed": 7,
          }
        : {
            "config_loading": 0,
            "data_fetching": 1,
            "macro_analysis": 2,
            "financial_market_analysis": 3,
            "policy_analysis": 4,
            "risk_assessment": 5,
            "report_generation": 6,
            "quality_review": 7,
            "completed": 8,
          };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();

            if (data === "[DONE]") {
              setResultDone(true);
              setState("result");
              continue;
            }

            try {
              const parsed = JSON.parse(data);

              // 解析后端返回的进度更新
              const { stage, message, thinking_node, data: parsedData } = parsed;

              // 更新当前步骤
              const stepIndex = stageToStepIndex[stage] ?? 0;
              if (stepIndex < progressSteps.length) {
                setCurrentStep(stepIndex);
              }

              // 更新思维链节点（如果有）
              if (thinking_node) {
                setCurrentThinkingNode({
                  title: thinking_node.title || message,
                  content: thinking_node.content || "",
                });
              }

              // 如果完成了，提取最终报告
              if (stage === "completed" && parsedData?.final_report) {
                resultBuffer = parsedData.final_report;
                setDisplayedResult(resultBuffer);
                setResultDone(true);
                setState("result");
              }

            } catch (e) {
              console.warn("Failed to parse SSE data:", data, e);
            }
          }
        }
      }

      setResultDone(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "请求失败，请稍后重试";
      setError(errorMessage);
      setState("form");
    }
  };

  const reset = () => {
    setState("form");
    setCurrentStep(-1);
    setDisplayedResult("");
    setResultDone(false);
    setError(null);
    setCurrentThinkingNode(null);
  };

  return (
    <div className="h-full flex items-center justify-center overflow-auto p-8">
      <AnimatePresence mode="wait">
        {/* ── Form State ── */}
        {state === "form" && (
          <motion.div
            key="form"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ type: "spring", stiffness: 280, damping: 28 }}
            className="w-full max-w-2xl"
          >
            {/* Error Display */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mb-6 p-4 rounded-xl flex items-start gap-3"
                  style={{ backgroundColor: "#fef2f2", border: "1px solid #fecaca" }}
                >
                  <AlertCircle size={18} style={{ color: "#dc2626", flexShrink: 0, marginTop: 2 }} />
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500, color: "#dc2626", fontFamily: "'Noto Sans SC', sans-serif" }}>
                      请求失败
                    </div>
                    <div style={{ fontSize: 12, color: "#991b1b", fontFamily: "'Noto Sans SC', sans-serif", marginTop: 4 }}>
                      {error}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Header */}
            <div className="text-center mb-8">
              <div
                className="inline-flex items-center justify-center w-12 h-12 rounded-xl mb-4"
                style={{ backgroundColor: "#fef2f2", border: "1px solid #fecaca" }}
              >
                <Globe2 size={22} style={{ color: "#9b1c1c" }} />
              </div>
              <h1
                style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 600, fontSize: 24 }}
              >
                国别深度研究
              </h1>
              <p style={{ color: "#64748b", fontSize: 14, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 6 }}>
                配置研究参数，AI 将自动检索多方数据源并生成专业国别分析报告
              </p>
            </div>

            <div
              className="rounded-2xl p-7"
              style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", boxShadow: "0 1px 16px rgba(0,0,0,0.04)" }}
            >
              {/* 非洲区域 - 移到最上方 */}
              <div className="mb-6">
                <label
                  style={{ color: "#374151", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500, display: "block", marginBottom: 10 }}
                >
                  非洲区域
                </label>
                <div className="flex flex-wrap gap-2">
                  <motion.button
                    onClick={() => setSelectedRegion("全部")}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="px-4 py-2 rounded-lg text-xs"
                    style={{
                      border: selectedRegion === "全部" ? "1px solid #dc2626" : "1px solid #e2e8f0",
                      backgroundColor: selectedRegion === "全部" ? "#fef2f2" : "#f8fafc",
                      color: selectedRegion === "全部" ? "#dc2626" : "#64748b",
                      fontFamily: "'Noto Sans SC', sans-serif",
                    }}
                  >
                    全部
                  </motion.button>
                  {(Object.keys(regionConfig) as AfricanRegion[]).map((region) => {
                    const isSelected = selectedRegion === region;
                    return (
                      <motion.button
                        key={region}
                        onClick={() => setSelectedRegion(region)}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="px-4 py-2 rounded-lg text-xs"
                        style={{
                          border: isSelected ? "1px solid #dc2626" : "1px solid #e2e8f0",
                          backgroundColor: isSelected ? "#fef2f2" : "#f8fafc",
                          color: isSelected ? "#dc2626" : "#64748b",
                          fontFamily: "'Noto Sans SC', sans-serif",
                        }}
                      >
                        {region}
                      </motion.button>
                    );
                  })}
                </div>
              </div>

              {/* 研究国家 & 研究类型 - 对称布局 */}
              {/* 研究国家 & 研究类型 - 对称布局 */}
              <div className="grid grid-cols-2 gap-4 mb-5">
                {/* 研究国家 - 自定义下拉框 */}
                <CustomDropdown
                  label="研究国家"
                  value={country}
                  options={filteredCountries}
                  onChange={setCountry}
                />
                {/* 研究类型 - 自定义下拉框 */}
                <CustomDropdown
                  label="研究类型"
                  value={resType}
                  options={researchTypes}
                  onChange={setResType}
                />
              </div>

              {/* Model */}
              <div className="mb-5">
                <label style={{ color: "#374151", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500, display: "block", marginBottom: 6 }}>
                  调用模型
                </label>
                <div className="flex gap-2">
                  {models.map((m) => (
                    <motion.button
                      key={m}
                      onClick={() => setModel(m)}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.97 }}
                      className="flex-1 py-2 rounded-lg text-center text-xs"
                      style={{
                        border: model === m ? "1px solid #9b1c1c" : "1px solid #e2e8f0",
                        backgroundColor: model === m ? "#fef2f2" : "#f8fafc",
                        color: model === m ? "#9b1c1c" : "#64748b",
                        fontFamily: "'Noto Sans SC', sans-serif",
                        fontSize: 12,
                        fontWeight: model === m ? 500 : 400,
                        transition: "all 0.15s",
                      }}
                    >
                      {m}
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* Start Button */}
              <motion.button
                onClick={startResearch}
                whileHover={{ scale: 1.01, boxShadow: "0 4px 20px rgba(155,28,28,0.4)" }}
                whileTap={{ scale: 0.98 }}
                className="w-full py-3 rounded-xl flex items-center justify-center gap-2 text-white"
                style={{
                  backgroundColor: "#9b1c1c",
                  fontFamily: "'Noto Sans SC', sans-serif",
                  fontSize: 15,
                  fontWeight: 500,
                  boxShadow: "0 2px 12px rgba(155,28,28,0.35)",
                  transition: "box-shadow 0.2s",
                }}
              >
                <Search size={17} />
                开始研究分析
              </motion.button>
            </div>
          </motion.div>
        )}

        {/* ── Loading State ── */}
        {state === "loading" && (
          <motion.div
            key="loading"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 280, damping: 28 }}
            className="w-full max-w-md"
          >
            <div className="text-center mb-10">
              <h2 style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 22, fontWeight: 600 }}>
                正在分析：{country}
              </h2>
              <p style={{ color: "#64748b", fontSize: 13.5, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 6 }}>
                AI 研究引擎正在多路并行检索与分析……
              </p>
            </div>

            {/* Stepper */}
            <div className="space-y-0">
              {progressSteps.map((step, i) => {
                const isDone = currentStep > i;
                const isActive = currentStep === i;
                return (
                  <div key={i} className="flex gap-4">
                    {/* Icon + Line */}
                    <div className="flex flex-col items-center">
                      <div
                        className="relative flex items-center justify-center rounded-full flex-shrink-0"
                        style={{
                          width: 36,
                          height: 36,
                          backgroundColor: isDone ? "#f0fdf4" : isActive ? "#fef2f2" : "#f8fafc",
                          border: isDone
                            ? "1.5px solid #86efac"
                            : isActive
                            ? "1.5px solid #fca5a5"
                            : "1.5px solid #e2e8f0",
                        }}
                      >
                        {isDone ? (
                          <CheckCircle2 size={16} style={{ color: "#16a34a" }} />
                        ) : isActive ? (
                          <motion.div
                            animate={{ scale: [1, 1.3, 1], opacity: [0.7, 1, 0.7] }}
                            transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: "#9b1c1c" }}
                          />
                        ) : (
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: "#cbd5e1" }} />
                        )}
                      </div>
                      {i < progressSteps.length - 1 && (
                        <div
                          className="w-0.5 flex-1 my-1"
                          style={{
                            backgroundColor: isDone ? "#86efac" : "#e2e8f0",
                            minHeight: 32,
                            transition: "background-color 0.5s",
                          }}
                        />
                      )}
                    </div>

                    {/* Content */}
                    <div className="pb-8 pt-1.5">
                      <div
                        style={{
                          fontSize: 14.5,
                          fontFamily: "'Noto Sans SC', sans-serif",
                          fontWeight: isDone || isActive ? 500 : 400,
                          color: isDone ? "#16a34a" : isActive ? "#0f172a" : "#94a3b8",
                          marginBottom: 4,
                        }}
                      >
                        {step.label}
                        {isDone && (
                          <span style={{ fontSize: 11, color: "#86efac", marginLeft: 8 }}>已完成</span>
                        )}
                      </div>
                      {isActive && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          style={{
                            fontSize: 12,
                            color: "#94a3b8",
                            fontFamily: "'Noto Sans SC', sans-serif",
                            fontStyle: "italic",
                          }}
                        >
                          {currentThinkingNode ? (
                            <>
                              <div style={{ fontWeight: 500, marginBottom: 2, color: "#0f172a" }}>
                                {currentThinkingNode.title}
                              </div>
                              <div style={{ fontSize: 11, opacity: 0.8 }}>
                                {currentThinkingNode.content}
                              </div>
                            </>
                          ) : (
                            step.detail
                          )}
                        </motion.div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Thinking Chain Display */}
            <AnimatePresence>
              {currentThinkingNode && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                  className="mt-6 p-4 rounded-xl"
                  style={{
                    backgroundColor: "#f8fafc",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ fontSize: 11, color: "#64748b", marginBottom: 6, fontFamily: "'Noto Sans SC', sans-serif" }}>
                    💭 思维链
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: "#0f172a", marginBottom: 4, fontFamily: "'Noto Sans SC', sans-serif" }}>
                    {currentThinkingNode.title}
                  </div>
                  <div style={{ fontSize: 12, color: "#475569", lineHeight: 1.6, fontFamily: "'Noto Sans SC', sans-serif" }}>
                    {currentThinkingNode.content}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Overall progress */}
            <div className="mt-2">
              <div
                className="h-1 rounded-full overflow-hidden"
                style={{ backgroundColor: "#f1f5f9" }}
              >
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: "#9b1c1c" }}
                  animate={{ width: `${((currentStep + 1) / progressSteps.length) * 100}%` }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                />
              </div>
              <div className="flex justify-between mt-1.5">
                <span style={{ fontSize: 11, color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif" }}>
                  步骤 {Math.min(currentStep + 1, progressSteps.length)} / {progressSteps.length}
                </span>
              </div>
            </div>
          </motion.div>
        )}

        {/* ── Result State ── */}
        {state === "result" && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 26 }}
            className="w-full max-w-3xl h-full flex flex-col"
          >
            {/* Result header */}
            <div
              className="flex items-center justify-between px-5 py-3.5 rounded-t-xl flex-shrink-0"
              style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", borderBottom: "none" }}
            >
              <div className="flex items-center gap-3">
                <CheckCircle2 size={16} style={{ color: "#16a34a" }} />
                <span style={{ fontSize: 14, fontFamily: "'Noto Sans SC', sans-serif", color: "#374151", fontWeight: 500 }}>
                  {country} · {resType} · 已生成
                </span>
                <span
                  className="px-2 py-0.5 rounded-full text-xs"
                  style={{ backgroundColor: "#f0fdf4", color: "#16a34a", border: "1px solid #bbf7d0", fontSize: 11 }}
                >
                  {model}
                </span>
              </div>
              <div className="flex gap-2">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  onClick={reset}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm"
                  style={{ border: "1px solid #e2e8f0", color: "#64748b", fontSize: 12.5, fontFamily: "'Noto Sans SC', sans-serif" }}
                >
                  <RotateCcw size={12} />
                  重新研究
                </motion.button>
                {resultDone && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    whileHover={{ scale: 1.02 }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-white"
                    style={{ backgroundColor: "#9b1c1c", fontSize: 12.5, fontFamily: "'Noto Sans SC', sans-serif" }}
                  >
                    <Download size={13} />
                    导出为 Word
                  </motion.button>
                )}
              </div>
            </div>

            {/* Result content */}
            <div
              className="flex-1 overflow-auto p-8 rounded-b-xl"
              style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", borderTop: "none" }}
            >
              <div
                style={{
                  fontFamily: "'Noto Serif SC', 'SimSun', serif",
                  fontSize: 15,
                  lineHeight: 2.1,
                  color: "#1e293b",
                  whiteSpace: "pre-wrap",
                }}
              >
                {displayedResult}
                {state === "result" && !resultDone && (
                  <motion.span
                    animate={{ opacity: [1, 0] }}
                    transition={{ duration: 0.5, repeat: Infinity }}
                    style={{ display: "inline-block", width: 2, height: 17, backgroundColor: "#9b1c1c", marginLeft: 2, verticalAlign: "text-bottom" }}
                  />
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
