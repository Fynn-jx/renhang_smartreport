import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { api, type Document as ApiDocument } from "../../api";
import {
  Search,
  Upload,
  Plug,
  Filter,
  FileText,
  CheckCircle2,
  Clock,
  Circle,
  Languages,
  PenLine,
  ChevronUp,
  ChevronDown,
  Download,
  Cpu,
  Paperclip,
  ArrowLeft,
  MoreHorizontal,
  BookOpen,
  X,
  Settings2,
  Sparkles,
  Trash2,
  MoreVertical,
} from "lucide-react";

type LibState = "A" | "B" | "C";
type AiMode = "translate" | "write" | null;

// 获取认证 Token
const getAuthToken = (): string => {
  return localStorage.getItem("auth_token") || "";
};

// 来源网站分类
type Source = "世界银行" | "IMF" | "联合国" | "联合国非洲经济委员会" | "非洲开发银行" | "WTO" | "OECD" | "尼尔森" | "麦肯锡" | "波士顿咨询" | "贝恩" | "中国人民银行" | "国家统计局" | "其他";

const sourceConfig: Record<Source, { url: string; color: string }> = {
  "世界银行": { url: "worldbank.org", color: "#ea580c" },
  "IMF": { url: "imf.org", color: "#2563eb" },
  "联合国": { url: "un.org", color: "#059669" },
  "联合国非洲经济委员会": { url: "uneca.org", color: "#0891b2" },
  "非洲开发银行": { url: "afdb.org", color: "#8b5cf6" },
  "WTO": { url: "wto.org", color: "#06b6d4" },
  "OECD": { url: "oecd.org", color: "#10b981" },
  "尼尔森": { url: "nielsen.com", color: "#f59e0b" },
  "麦肯锡": { url: "mckinsey.com", color: "#6366f1" },
  "波士顿咨询": { url: "bcg.com", color: "#ec4899" },
  "贝恩": { url: "bain.com", color: "#14b8a6" },
  "中国人民银行": { url: "pbc.gov.cn", color: "#dc2626" },
  "国家统计局": { url: "stats.gov.cn", color: "#f97316" },
  "其他": { url: "", color: "#6b7280" },
};

// 日期分类
type DateFilter = "全部" | string; // string is a specific date in YYYY-MM-DD format

// 日期范围筛选
type DateRange = "全部" | "最近一周" | "最近一月" | "最近三月" | "更早";

interface Doc {
  id: string;
  title: string;
  institution: string;
  date: string;
  tags: string[];
  aiStatus: "已完成" | "处理中" | "待处理";
  abstract: string;
  source: Source;
  document_type?: string;
  original_filename?: string;
  file_path?: string;
}

interface AiConfig {
  model: string;
  files: string[];
}

// AI 模型配置
const models = [
  { id: "deepseek", label: "DeepSeek V3", value: "Pro/deepseek-ai/DeepSeek-V3", desc: "综合性能最优" },
  { id: "claude", label: "Claude 3.5", value: "Pro/deepseek-ai/DeepSeek-V3", desc: "长文本理解强" },
  { id: "gpt4o", label: "GPT-4o", value: "Pro/deepseek-ai/DeepSeek-V3", desc: "多语言翻译精" },
  { id: "qwen", label: "Qwen-Max", value: "Pro/deepseek-ai/DeepSeek-V3", desc: "中文专项优化" },
];

// AI 输出示例文本（用于演示 AI 写作功能）
const aiOutputText = `人民银行国际司研究报告

关于美联储2024年货币政策执行情况的专题分析

（内部参考，密级：机密）

一、执行摘要

2024年，美国联邦储备委员会在通胀持续回落的背景下启动了自2022年紧缩周期以来的首次降息进程。联邦公开市场委员会（FOMC）于9月、11月、12月三次下调联邦基金利率目标区间，累计降幅100个基点，政策利率降至4.25%~4.50%区间。总体而言，美联储货币政策正式进入"数据依赖型"渐进宽松阶段，但其前瞻指引措辞趋于审慎，市场对2025年降息幅度的预期有所收窄。

二、宏观背景与政策逻辑

（一）通胀数据的持续改善

2024年全年，美国核心个人消费支出（PCE）价格指数同比增速从年初的2.9%逐步回落至年末的2.4%，呈现稳定的下行通道。美联储官员多次强调，通胀向2%目标靠拢的趋势"已基本确立"，但"最后一公里"问题仍存在不确定性，尤其是住房通胀的粘性超出预期，成为制约更快降息的关键因素。

（二）劳动力市场的韧性与降温

就业市场在2024年呈现"有序降温"特征：非农就业月均新增人数从上年的25万人降至约17万人；失业率温和上升至4.2%，仍处于历史相对低位。美联储认为劳动力市场"已基本回归平衡"，供需两端的过度紧张状态已明显缓解，这为货币政策转向提供了必要的政策空间。

三、对中国的影响与政策启示

（一）跨境资本流动压力有所缓解

美联储降息周期的开启，在一定程度上收窄了中美利差的负偏离幅度，对人民币汇率贬值压力形成阶段性对冲。建议密切跟踪后续美联储点阵图变化及美国长端利率走势，动态评估跨境资金流动对国内货币政策操作空间的影响。

（二）外汇储备管理的结构优化窗口

美元阶段性走弱为我国优化外汇储备结构提供了操作窗口，宜适时评估黄金、特别提款权（SDR）及非美元储备资产的配置比例。

四、结论与建议

综上，美联储政策转向总体符合预期，但降息节奏较年初市场预期明显偏缓，"高利率维持更长时间"逻辑并未彻底退出。建议我行国际司持续密切追踪，结合每季度FOMC声明及鲍威尔讲话，形成专题简报，适时为货币政策委员会提供决策参考。`;

// AI 思维链示例（用于演示 AI 处理过程）
const thinkingChain = [
  "正在解析原始文献语义结构与核心论点……",
  "识别关键经济指标：联邦基金利率、核心PCE、非农就业……",
  "匹配中国人民银行内部公文写作规范（GF/T 22000-2008）……",
  "构建报告逻辑框架：执行摘要 → 宏观背景 → 影响评估 → 结论……",
  "正在对照参考文献，校验关键数据与政策描述准确性……",
  "生成草稿，应用正式公文排版规范……",
];

function StatusBadge({ status }: { status: Doc["aiStatus"] }) {
  const config = {
    已完成: { color: "#16a34a", bg: "#f0fdf4", icon: CheckCircle2 },
    处理中: { color: "#d97706", bg: "#fffbeb", icon: Clock },
    待处理: { color: "#94a3b8", bg: "#f8fafc", icon: Circle },
  };
  const c = config[status];
  const Icon = c.icon;
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs"
      style={{ backgroundColor: c.bg, color: c.color, border: `1px solid ${c.color}22` }}
    >
      <Icon size={10} />
      {status}
    </span>
  );
}

// ─── More Vertical Button with Delete Menu ─────────────────────────────────────
function MoreVerticalButton({ docId, onDelete }: { docId: string; onDelete: (docId: string) => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  return (
    <div className="relative" ref={menuRef}>
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        className="w-8 h-8 rounded-lg flex items-center justify-center"
        style={{ color: "#94a3b8" }}
      >
        <MoreVertical size={14} />
      </motion.button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -4 }}
            transition={{ duration: 0.1 }}
            className="absolute right-0 top-full mt-1 rounded-lg overflow-hidden z-50"
            style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", boxShadow: "0 4px 16px rgba(0,0,0,0.12)", minWidth: 120 }}
            onClick={(e) => e.stopPropagation()}
          >
            <motion.button
              whileHover={{ backgroundColor: "#fef2f2" }}
              onClick={(e) => {
                e.stopPropagation();
                onDelete(docId);
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-left"
              style={{ fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", color: "#dc2626" }}
            >
              <Trash2 size={13} />
              删除
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function TagBadge({ label }: { label: string }) {
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-xs mr-1"
      style={{ backgroundColor: "#f1f5f9", color: "#64748b", border: "1px solid #e2e8f0", fontSize: 11 }}
    >
      {label}
    </span>
  );
}

// ─── Config Modal ──────────────────────────────────────────────────────────────
function ConfigModal({
  mode,
  doc,
  onCancel,
  onConfirm,
}: {
  mode: AiMode;
  doc: Doc | null;
  onCancel: () => void;
  onConfirm: (config: AiConfig) => void;
}) {
  const [selectedModel, setSelectedModel] = useState("deepseek");
  const [attachedFiles, setAttachedFiles] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachedFiles((prev) => [...prev, ...files.map((f) => f.name)]);
  };

  const removeFile = (i: number) => setAttachedFiles((prev) => prev.filter((_, idx) => idx !== i));

  const handleConfirm = () => {
    onConfirm({ model: models.find((m) => m.id === selectedModel)?.value ?? "Pro/deepseek-ai/DeepSeek-V3", files: attachedFiles });
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: "rgba(15,23,42,0.45)", backdropFilter: "blur(4px)" }}
      onClick={onCancel}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.94, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.94, y: 10 }}
        transition={{ type: "spring", stiffness: 320, damping: 28 }}
        className="w-full max-w-lg rounded-2xl overflow-hidden"
        style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", boxShadow: "0 20px 60px rgba(0,0,0,0.18)" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ backgroundColor: "#fef2f2", border: "1px solid #fecaca" }}
            >
              {mode === "translate" ? (
                <Languages size={16} style={{ color: "#9b1c1c" }} />
              ) : (
                <PenLine size={16} style={{ color: "#9b1c1c" }} />
              )}
            </div>
            <div>
              <div style={{ fontSize: 14.5, fontFamily: "'Noto Sans SC', sans-serif", color: "#0f172a", fontWeight: 600 }}>
                {mode === "translate" ? "配置 AI 对照翻译" : "配置 AI 公文写作"}
              </div>
              <div style={{ fontSize: 11.5, color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif", marginTop: 1 }}>
                {doc?.title}
              </div>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: "#f1f5f9", color: "#64748b" }}
          >
            <X size={14} />
          </button>
        </div>

        <div className="px-6 py-5">
          {/* Model Selection */}
          <div className="mb-5">
            <div
              className="flex items-center gap-1.5 mb-3"
              style={{ color: "#374151", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}
            >
              <Cpu size={13} style={{ color: "#64748b" }} />
              选择模型引擎
            </div>
            <div className="grid grid-cols-2 gap-2">
              {models.map((m) => {
                const active = selectedModel === m.id;
                return (
                  <motion.button
                    key={m.id}
                    onClick={() => setSelectedModel(m.id)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.97 }}
                    className="flex flex-col items-start p-3 rounded-xl text-left"
                    style={{
                      border: active ? "1.5px solid #9b1c1c" : "1px solid #e2e8f0",
                      backgroundColor: active ? "#fef2f2" : "#f8fafc",
                      transition: "all 0.15s",
                    }}
                  >
                    <div className="flex items-center justify-between w-full mb-0.5">
                      <span style={{ fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", color: active ? "#9b1c1c" : "#0f172a", fontWeight: active ? 600 : 400 }}>
                        {m.label}
                      </span>
                      {active && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="w-4 h-4 rounded-full flex items-center justify-center"
                          style={{ backgroundColor: "#9b1c1c" }}
                        >
                          <CheckCircle2 size={10} style={{ color: "#fff" }} />
                        </motion.div>
                      )}
                    </div>
                    <span style={{ fontSize: 11, color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif" }}>
                      {m.desc}
                    </span>
                  </motion.button>
                );
              })}
            </div>
          </div>

          {/* File Upload (Optional) */}
          <div className="mb-6">
            <div
              className="flex items-center gap-1.5 mb-2"
              style={{ color: "#374151", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}
            >
              <Paperclip size={13} style={{ color: "#64748b" }} />
              上传参考文件
              <span style={{ color: "#94a3b8", fontSize: 11, fontWeight: 400 }}>（可选）</span>
            </div>
            <input ref={fileInputRef} type="file" multiple className="hidden" onChange={handleFileChange} />
            <motion.button
              whileHover={{ backgroundColor: "#f1f5f9" }}
              onClick={() => fileInputRef.current?.click()}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg"
              style={{
                border: "1.5px dashed #e2e8f0",
                color: "#64748b",
                fontFamily: "'Noto Sans SC', sans-serif",
                fontSize: 13,
                backgroundColor: "#f8fafc",
              }}
            >
              <Upload size={14} />
              点击上传参考文件（PDF、Word、TXT）
            </motion.button>
            {attachedFiles.length > 0 && (
              <div className="mt-2 space-y-1">
                {attachedFiles.map((f, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                    style={{ backgroundColor: "#f0fdf4", border: "1px solid #bbf7d0" }}
                  >
                    <FileText size={12} style={{ color: "#16a34a", flexShrink: 0 }} />
                    <span className="flex-1 truncate" style={{ fontSize: 12, color: "#374151", fontFamily: "'Noto Sans SC', sans-serif" }}>
                      {f}
                    </span>
                    <button onClick={() => removeFile(i)}>
                      <X size={12} style={{ color: "#94a3b8" }} />
                    </button>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <motion.button
              whileHover={{ backgroundColor: "#f1f5f9" }}
              onClick={onCancel}
              className="flex-1 py-2.5 rounded-xl"
              style={{ border: "1px solid #e2e8f0", color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 14 }}
            >
              取消
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.01, boxShadow: "0 4px 16px rgba(155,28,28,0.35)" }}
              whileTap={{ scale: 0.98 }}
              onClick={handleConfirm}
              className="flex-[2] py-2.5 rounded-xl text-white flex items-center justify-center gap-2"
              style={{
                backgroundColor: "#9b1c1c",
                fontFamily: "'Noto Sans SC', sans-serif",
                fontSize: 14,
                fontWeight: 500,
                boxShadow: "0 2px 10px rgba(155,28,28,0.3)",
              }}
            >
              <Sparkles size={15} />
              开始执行
            </motion.button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Calendar Picker (传统日历视图) ───────────────────────────────────
import { Calendar } from "./ui/calendar";
import { ChevronLeft, ChevronRight } from "lucide-react";

function CalendarPicker({
  dates,
  selectedDate,
  onDateSelect,
}: {
  dates: string[];
  selectedDate: string | null;
  onDateSelect: (date: string) => void;
}) {
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());

  // 将日期字符串转换为 Date 对象集合
  const documentDates = new Set(
    dates.map((date) => new Date(date).toDateString())
  );

  // 当前选中日期的 Date 对象
  const selectedDateObj = selectedDate ? new Date(selectedDate) : undefined;

  // 检查某个日期是否有文档
  const hasDocument = (date: Date) => {
    return documentDates.has(date.toDateString());
  };

  // 月份导航
  const previousMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1));
  };

  const formatMonthYear = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    return `${year}年 ${month}月`;
  };

  return (
    <div className="space-y-3">
      {/* 月份导航 */}
      <div className="flex items-center justify-between">
        <button
          onClick={previousMonth}
          className="p-1 rounded hover:bg-gray-100 transition-colors"
          title="上个月"
        >
          <ChevronLeft size={16} style={{ color: "#64748b" }} />
        </button>
        <div
          className="text-sm font-medium"
          style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif" }}
        >
          {formatMonthYear(currentMonth)}
        </div>
        <button
          onClick={nextMonth}
          className="p-1 rounded hover:bg-gray-100 transition-colors"
          title="下个月"
        >
          <ChevronRight size={16} style={{ color: "#64748b" }} />
        </button>
      </div>

      {/* 日历 */}
      <Calendar
        mode="single"
        month={currentMonth}
        onMonthChange={setCurrentMonth}
        selected={selectedDateObj}
        onSelect={(date) => {
          if (date) {
            // 格式化为 YYYY-MM-DD
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const dateStr = `${year}-${month}-${day}`;

            // 如果点击已选中的日期，则取消选择
            if (selectedDate === dateStr) {
              onDateSelect("全部");
            } else {
              onDateSelect(dateStr);
            }
          } else {
            // 如果 date 为 null，说明取消了选择
            onDateSelect("全部");
          }
        }}
        modifiers={{
          hasDocument: hasDocument,
        }}
        modifiersStyles={{
          hasDocument: {
            fontWeight: "700",
            color: "#0f172a",
            backgroundColor: "#dbeafe", // 淡蓝色背景，更明显
            border: "1px solid #93c5fd",
          },
        }}
        className="rounded-md border"
        style={{
          fontSize: 13,
          fontFamily: "'Noto Sans SC', sans-serif",
        }}
      />

      {/* 提示 */}
      <div className="flex items-center gap-3 text-xs" style={{ color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif" }}>
        <div className="flex items-center gap-1">
          <div
            className="w-3 h-3 rounded"
            style={{ backgroundColor: "#dbeafe", border: "1px solid #93c5fd" }}
          />
          <span>有文档</span>
        </div>
        <div className="flex items-center gap-1">
          <div
            className="w-3 h-3 rounded"
            style={{ backgroundColor: "#9b1c1c" }}
          />
          <span>已选中</span>
        </div>
      </div>
    </div>
  );
}

// ─── Filter Panel ───────────────────────────────────────────────────────────────
function FilterPanel({
  selectedSources,
  selectedDateRange,
  onSourceChange,
  onDateRangeChange,
  documentDates,
}: {
  selectedSources: Source[];
  selectedDateRange: DateFilter;
  onSourceChange: (sources: Source[]) => void;
  onDateRangeChange: (range: DateFilter) => void;
  documentDates: string[];
}) {
  const [isOpen, setIsOpen] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  const toggleSource = (src: Source) => {
    if (selectedSources.includes(src)) {
      onSourceChange(selectedSources.filter((s) => s !== src));
    } else {
      onSourceChange([...selectedSources, src]);
    }
  };

  const clearAll = () => {
    onSourceChange([]);
    onDateRangeChange("全部");
  };

  const hasFilters = selectedSources.length > 0 || selectedDateRange !== "全部";

  return (
    <div className="relative" ref={filterRef}>
      <motion.button
        whileHover={{ backgroundColor: "#f1f5f9" }}
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg"
        style={{
          border: hasFilters ? "1px solid #9b1c1c" : "1px solid #e2e8f0",
          backgroundColor: hasFilters ? "#fef2f2" : "#fff",
          color: hasFilters ? "#9b1c1c" : "#374151",
          fontSize: 13,
          fontFamily: "'Noto Sans SC', sans-serif",
        }}
      >
        <Filter size={13} style={{ color: hasFilters ? "#9b1c1c" : "#64748b" }} />
        筛选
        {hasFilters && (
          <span className="ml-1 px-1.5 py-0.5 rounded text-xs" style={{ backgroundColor: "#9b1c1c", color: "#fff" }}>
            {selectedSources.length + (selectedDateRange !== "全部" ? 1 : 0)}
          </span>
        )}
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full right-0 mt-2 w-80 rounded-xl overflow-hidden z-50"
            style={{
              backgroundColor: "#fff",
              border: "1px solid #e2e8f0",
              boxShadow: "0 10px 40px rgba(0,0,0,0.12)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-4 py-3" style={{ borderBottom: "1px solid #f1f5f9" }}>
              <div className="flex items-center justify-between">
                <span style={{ fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", color: "#0f172a", fontWeight: 500 }}>
                  筛选条件
                </span>
                {hasFilters && (
                  <button
                    onClick={clearAll}
                    style={{ fontSize: 12, color: "#9b1c1c", fontFamily: "'Noto Sans SC', sans-serif" }}
                  >
                    清除全部
                  </button>
                )}
              </div>
            </div>

            <div className="p-4 max-h-80 overflow-auto">
              {/* 日期日历 */}
              <div className="mb-4">
                <div
                  className="text-xs mb-2 flex items-center justify-between"
                  style={{ color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}
                >
                  <span>日期</span>
                  {selectedDateRange !== "全部" && (
                    <button
                      onClick={() => onDateRangeChange("全部")}
                      style={{ color: "#9b1c1c", fontSize: 11 }}
                    >
                      清除
                    </button>
                  )}
                </div>
                <CalendarPicker
                  dates={documentDates}
                  selectedDate={selectedDateRange === "全部" ? null : selectedDateRange}
                  onDateSelect={onDateRangeChange}
                />
              </div>

              {/* 来源网站 */}
              <div>
                <div
                  className="text-xs mb-2"
                  style={{ color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}
                >
                  来源网站
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(Object.keys(sourceConfig) as Source[]).map((src) => {
                    const active = selectedSources.includes(src);
                    const cfg = sourceConfig[src];
                    return (
                      <button
                        key={src}
                        onClick={() => toggleSource(src)}
                        className="px-2.5 py-1 rounded-lg text-xs transition-all"
                        style={{
                          border: active ? `1px solid ${cfg.color}` : "1px solid #e2e8f0",
                          backgroundColor: active ? `${cfg.color}11` : "#f8fafc",
                          color: active ? cfg.color : "#64748b",
                          fontFamily: "'Noto Sans SC', sans-serif",
                        }}
                      >
                        {src}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ���── State A: Full Table View ──────────────────────────────────────────────────
function TableView({ onDocClick, docs, onDelete, onUpload }: { onDocClick: (doc: Doc) => void; docs: Doc[]; onDelete: (docId: string) => void; onUpload: (files: FileList) => void }) {
  const [searchVal, setSearchVal] = useState("");
  const [selectedSources, setSelectedSources] = useState<Source[]>([]);
  const [selectedDateRange, setSelectedDateRange] = useState<DateFilter>("全部");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 从文档列表中提取唯一日期
  const documentDates = [...new Set(docs.map((doc) => doc.date))].sort().reverse();

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onUpload(files);
    }
  };

  // Helper to check if a date matches the selected date filter
  const isInDateRange = (docDate: string, range: DateFilter): boolean => {
    if (range === "全部") return true;
    return docDate === range;
  };

  const filtered = docs.filter((d) => {
    const matchSearch =
      d.title.includes(searchVal) ||
      d.institution.includes(searchVal) ||
      d.tags.some((t) => t.includes(searchVal));
    const matchSource = selectedSources.length === 0 || selectedSources.includes(d.source);
    const matchDate = isInDateRange(d.date, selectedDateRange);
    return matchSearch && matchSource && matchDate;
  });

  return (
    <div className="h-full flex flex-col p-6">
      <div className="flex items-center justify-between mb-5 flex-shrink-0">
        <div>
          <h1 className="text-xl" style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 600 }}>
            前沿报告库
          </h1>
          <p style={{ color: "#64748b", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 2 }}>
            从本地上传或浏览器插件下载的前沿报告，支持按时间和来源筛选
            {selectedSources.length > 0 || selectedDateRange !== "全部" ? (
              <span style={{ color: "#9b1c1c" }}>（已筛选）</span>
            ) : null}
          </p>
          <p style={{ color: "#94a3b8", fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 1 }}>
            共 {filtered.length} 份报告 · {filtered.filter((d) => d.aiStatus === "已完成").length} 份已完成AI处理
          </p>
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm"
            style={{ border: "1px solid #e2e8f0", backgroundColor: "#fff", color: "#374151", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13 }}
          >
            <Plug size={14} style={{ color: "#64748b" }} />
            插件导入
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleUploadClick}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-white"
            style={{ backgroundColor: "#9b1c1c", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13, boxShadow: "0 1px 6px rgba(155,28,28,0.3)" }}
          >
            <Upload size={14} />
            上传本地研报
          </motion.button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>
      </div>

      <div className="flex items-center gap-3 mb-4 flex-shrink-0">
        <div className="flex-1 relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#94a3b8" }} />
          <input
            type="text"
            placeholder="搜索研报标题、发布机构或标签……"
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg text-sm outline-none"
            style={{ border: "1px solid #e2e8f0", backgroundColor: "#fff", color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13 }}
          />
        </div>
        <FilterPanel
          selectedSources={selectedSources}
          selectedDateRange={selectedDateRange}
          onSourceChange={setSelectedSources}
          onDateRangeChange={setSelectedDateRange}
          documentDates={documentDates}
        />
      </div>

      <div className="flex-1 overflow-auto rounded-xl" style={{ border: "1px solid #e2e8f0" }}>
        <table className="w-full">
          <thead style={{ backgroundColor: "#f8fafc", position: "sticky", top: 0, zIndex: 1 }}>
            <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
              {["研报标题", "来源", "上传日期", "标签", "AI处理状态", ""].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left"
                  style={{ color: "#64748b", fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500, letterSpacing: "0.04em", whiteSpace: "nowrap" }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((doc, i) => (
              <motion.tr
                key={doc.id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                onClick={() => onDocClick(doc)}
                className="cursor-pointer group"
                style={{ borderBottom: "1px solid #f1f5f9" }}
                whileHover={{ backgroundColor: "#fafcff" }}
              >
                <td className="px-4 py-3.5">
                  <div className="flex items-center gap-2">
                    <FileText size={14} style={{ color: "#94a3b8", flexShrink: 0 }} />
                    <span
                      className="group-hover:text-[#9b1c1c] transition-colors duration-150"
                      style={{ color: "#1e293b", fontSize: 13.5, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}
                    >
                      {doc.title}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3.5">
                  <span
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs"
                    style={{
                      backgroundColor: `${sourceConfig[doc.source].color}11`,
                      color: sourceConfig[doc.source].color,
                      border: `1px solid ${sourceConfig[doc.source].color}22`,
                      fontFamily: "'Noto Sans SC', sans-serif",
                    }}
                  >
                    {doc.source}
                  </span>
                </td>
                <td className="px-4 py-3.5">
                  <span style={{ color: "#64748b", fontSize: 12.5, fontFamily: "'Noto Sans SC', sans-serif" }}>
                    {doc.date}
                  </span>
                </td>
                <td className="px-4 py-3.5">
                  <div className="flex flex-wrap gap-1">
                    {doc.tags.map((t) => <TagBadge key={t} label={t} />)}
                  </div>
                </td>
                <td className="px-4 py-3.5">
                  <StatusBadge status={doc.aiStatus} />
                </td>
                <td className="px-4 py-3.5">
                  <MoreVerticalButton docId={doc.id} onDelete={onDelete} />
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── State B: Narrow List ──────────────────────────────────────────────────────
function NarrowList({ selected, onSelect, docs, onDelete }: { selected: Doc | null; onSelect: (doc: Doc) => void; docs: Doc[]; onDelete: (docId: string) => void }) {
  return (
    <div className="h-full overflow-y-auto flex flex-col" style={{ scrollbarWidth: "none" }}>
      <div className="px-3 py-3 flex-shrink-0" style={{ borderBottom: "1px solid #f1f5f9" }}>
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: "#94a3b8" }} />
          <input
            className="w-full pl-8 pr-3 py-1.5 rounded-md text-xs outline-none"
            placeholder="快速检索…"
            style={{ border: "1px solid #e2e8f0", backgroundColor: "#f8fafc", color: "#374151", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 12 }}
          />
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-1" style={{ scrollbarWidth: "none" }}>
        {docs.map((doc) => (
          <div key={doc.id} className="relative">
            <motion.button
              onClick={() => onSelect(doc)}
              className="w-full text-left p-3 rounded-lg mb-0.5"
              style={{
                backgroundColor: selected?.id === doc.id ? "#fef2f2" : "transparent",
                border: selected?.id === doc.id ? "1px solid #fecaca" : "1px solid transparent",
              }}
              whileHover={{ backgroundColor: selected?.id === doc.id ? "#fef2f2" : "#f8fafc" }}
              transition={{ duration: 0.1 }}
            >
              <div
                className="truncate mb-1"
                style={{ color: selected?.id === doc.id ? "#9b1c1c" : "#1e293b", fontSize: 12.5, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: selected?.id === doc.id ? 500 : 400 }}
              >
                {doc.title}
              </div>
              <div className="flex items-center gap-1.5 mb-1">
                <span
                  className="px-1.5 py-0.5 rounded text-[10px]"
                  style={{
                    backgroundColor: `${sourceConfig[doc.source].color}11`,
                    color: sourceConfig[doc.source].color,
                    fontFamily: "'Noto Sans SC', sans-serif",
                  }}
                >
                  {doc.source}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span style={{ color: "#94a3b8", fontSize: 11, fontFamily: "'Noto Sans SC', sans-serif" }}>
                  {doc.institution}
                </span>
                <StatusBadge status={doc.aiStatus} />
              </div>
            </motion.button>
            <div className="absolute top-2 right-2">
              <MoreVerticalButton docId={doc.id} onDelete={onDelete} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Document Preview ──────────────────────────────────────────────────────────
function DocumentPreview({ doc, onAction, onBack }: { doc: Doc; onAction: (mode: AiMode) => void; onBack: () => void }) {
  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: "#fff" }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-6 py-4 flex-shrink-0"
        style={{ borderBottom: "1px solid #e2e8f0" }}
      >
        <div className="flex items-center gap-4">
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
          <div className="flex items-center gap-2">
            <BookOpen size={15} style={{ color: "#64748b" }} />
            <span style={{ color: "#374151", fontSize: 13.5, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}>文档预览</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onAction("translate")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
            style={{ border: "1px solid #bbf7d0", backgroundColor: "#f0fdf4", color: "#16a34a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13 }}
          >
            <Languages size={14} />
            对照翻译
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onAction("write")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white"
            style={{ backgroundColor: "#9b1c1c", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13, boxShadow: "0 1px 4px rgba(155,28,28,0.3)" }}
          >
            <PenLine size={14} />
            公文写作
          </motion.button>
        </div>
      </div>

      {/* PDF 预览 */}
      <div className="flex-1 bg-gray-100">
        {doc.file_path ? (
          <iframe
            src={`${doc.file_path}#view=FitH`}
            className="w-full h-full border-0"
            title={doc.title}
            style={{ backgroundColor: "#525659" }}
          />
        ) : (
          <div className="h-full flex items-center justify-center" style={{ color: "#94a3b8", fontSize: 14 }}>
            暂无预览可用
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Thinking Chain ─────────────────────────────────────────────────────────────
function ThinkingChain({ active, progressSteps }: { active: boolean; progressSteps: string[] }) {
  const [open, setOpen] = useState(true);
  const [visibleThoughts, setVisibleThoughts] = useState<string[]>([]);

  useEffect(() => {
    if (!active) {
      setVisibleThoughts([]);
      return;
    }
    // 使用真实的后端进度消息
    setVisibleThoughts(progressSteps);
  }, [active, progressSteps]);

  return (
    <div className="mx-4 mt-3 mb-1 rounded-lg overflow-hidden" style={{ border: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}>
      <button
        className="w-full flex items-center justify-between px-3 py-2"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-2">
          <Cpu size={13} style={{ color: "#94a3b8" }} />
          <span style={{ fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif", color: "#64748b" }}>思维链 (Thinking Chain)</span>
          {active && visibleThoughts.length < thinkingChain.length && (
            <motion.span
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ duration: 1.2, repeat: Infinity }}
              className="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block"
            />
          )}
        </div>
        {open ? <ChevronUp size={13} style={{ color: "#94a3b8" }} /> : <ChevronDown size={13} style={{ color: "#94a3b8" }} />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 space-y-1">
              {visibleThoughts.map((thought, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                  style={{ fontStyle: "italic", fontSize: 11.5, color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif", paddingLeft: 8, borderLeft: "2px solid #e2e8f0" }}
                >
                  {thought}
                </motion.div>
              ))}
              {!active && visibleThoughts.length === 0 && (
                <div style={{ color: "#cbd5e1", fontSize: 11.5, fontStyle: "italic", fontFamily: "'Noto Sans SC', sans-serif" }}>等待AI引擎启动……</div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── AI Writing Cabin ──────────────────────────────────────────────────────────
function AIWritingCabin({ doc, mode, config, onBack }: { doc: Doc | null; mode: AiMode; config: AiConfig; onBack: () => void }) {
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [displayedText, setDisplayedText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [progressSteps, setProgressSteps] = useState<string[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 两步翻译工作流状态
  const [extractedContent, setExtractedContent] = useState<string>("");
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState<string>("");
  const [extracting, setExtracting] = useState(false);

  // 写作模式可编辑状态
  const [isWriteEditing, setIsWriteEditing] = useState(false);
  const [editedWriteContent, setEditedWriteContent] = useState<string>("");

  // 第一步：提取文档内容
  const extractDocumentContent = async () => {
    if (!doc) {
      setError("未选择文档");
      return;
    }

    setExtracting(true);
    setError(null);

    const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

    try {
      console.log("[文档提取] 开始提取文档:", doc.id);
      const formData = new FormData();
      formData.append("document_id", doc.id);

      const response = await fetch(`${API_BASE}/api/v1/workflows/translation/extract`, {
        method: "POST",
        headers: {
          ...(getAuthToken() ? { "Authorization": `Bearer ${getAuthToken()}` } : {}),
        },
        body: formData,
      });

      console.log("[文档提取] 响应状态:", response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("[文档提取] 错误响应:", errorText);
        throw new Error(`提取失败: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log("[文档提取] 响应数据:", data);

      const content = data.data?.content || "";

      if (!content) {
        console.error("[文档提取] 内容为空:", data);
        setError("提取的内容为空，请检查文档是否有效");
        return;
      }

      console.log("[文档提取] 提取成功，内容长度:", content.length);
      setExtractedContent(content);
      setEditedContent(content);
      setIsEditing(true);
    } catch (err) {
      console.error("[文档提取] 失败:", err);
      setError(err instanceof Error ? err.message : "提取失败");
    } finally {
      setExtracting(false);
    }
  };

  // 第二步：翻译用户确认的文本
  const translateConfirmedText = async () => {
    if (!editedContent) {
      setError("没有可翻译的内容");
      return;
    }

    setGenerating(true);
    setDisplayedText("");
    setError(null);
    setProgressSteps([]);
    setCurrentStep(0);
    setIsEditing(false);

    abortControllerRef.current = new AbortController();
    const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

    try {
      const formData = new FormData();
      formData.append("content", editedContent);
      formData.append("source_language", "auto");
      formData.append("target_language", "zh");
      formData.append("model", config.model);

      const response = await fetch(`${API_BASE}/api/v1/workflows/translation/text`, {
        method: "POST",
        headers: {
          ...(getAuthToken() ? { "Authorization": `Bearer ${getAuthToken()}` } : {}),
        },
        body: formData,
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`API 请求失败: ${response.status} ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("无法读取响应流");
      }

      let buffer = "";
      let accumulatedText = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || !trimmedLine.startsWith("data: ")) continue;

          const dataStr = trimmedLine.slice(6);

          if (dataStr === "[DONE]") {
            setGenerating(false);
            setGenerated(true);
            continue;
          }

          try {
            const data = JSON.parse(dataStr);

            // 处理进度步骤（思维链）
            if (data.message) {
              setProgressSteps((prev) => {
                // 检查是否已存在相同消息
                if (!prev.includes(data.message)) {
                  const newSteps = [...prev, data.message];
                  setCurrentStep(newSteps.length);
                  return newSteps;
                }
                return prev;
              });
            }

            // 翻译模式：处理逐段翻译的完整段落
            if (data.stage === "chunk_processing" && data.data?.translated_paragraph) {
              // 追加已翻译的段落
              accumulatedText += data.data.translated_paragraph + "\n\n";
              setDisplayedText(accumulatedText);
              continue;
            }

            // 翻译模式：处理流式翻译的内容片段（逐字/逐片段）- 保留用于其他功能
            if (data.stage === "translating" && data.data?.content_piece) {
              // 实时追加翻译的内容片段
              accumulatedText += data.data.content_piece;
              setDisplayedText(accumulatedText);
              continue;
            }

            // 翻译模式：处理完成时的翻译结果
            if (data.stage === "completed") {
              // 使用完整的翻译文本
              setDisplayedText(data.data?.translated_text || accumulatedText);
              setGenerating(false);
              setGenerated(true);
              continue;
            }

            // 写作模式：处理生成的内容
            if (data.content) {
              accumulatedText += data.content;
              setDisplayedText(accumulatedText);
            }

            // 处理完整内容（一次性返回的情况）
            if (data.output) {
              setDisplayedText(data.output);
            }

            // 处理错误
            if (data.stage === "failed" || data.error) {
              setError(data.message || data.error || "处理失败");
              setGenerating(false);
            }
          } catch (e) {
            console.warn("解析 SSE 数据失败:", dataStr, e);
          }
        }
      }

      setGenerating(false);
      setGenerated(true);
    } catch (err) {
      if (err instanceof Error) {
        if (err.name === "AbortError") {
          setError("请求已取消");
        } else {
          setError(err.message);
        }
      } else {
        setError("未知错误");
      }
      setGenerating(false);
    }
  };

  // 旧版写作模式的生成函数（保持不变）
  const startGeneration = async () => {
    if (!doc) {
      setError("未选择文档");
      return;
    }

    setGenerating(true);
    setDisplayedText("");
    setError(null);
    setProgressSteps([]);
    setCurrentStep(0);

    abortControllerRef.current = new AbortController();
    const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

    // 写作模式使用 SSE 流式
    const endpoint = "/api/v1/workflows/academic-to-official";

    try {
      const formData = new FormData();
      formData.append("document_id", doc.id);
      formData.append("model", config.model);

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: {
          ...(getAuthToken() ? { "Authorization": `Bearer ${getAuthToken()}` } : {}),
        },
        body: formData,
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`API 请求失败: ${response.status} ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("无法读取响应流");
      }

      let buffer = "";
      let accumulatedText = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || !trimmedLine.startsWith("data: ")) continue;

          const dataStr = trimmedLine.slice(6);

          if (dataStr === "[DONE]") {
            setGenerating(false);
            setGenerated(true);
            continue;
          }

          try {
            const data = JSON.parse(dataStr);

            // 处理进度步骤（思维链）
            if (data.message) {
              setProgressSteps((prev) => {
                if (!prev.includes(data.message)) {
                  const newSteps = [...prev, data.message];
                  setCurrentStep(newSteps.length);
                  return newSteps;
                }
                return prev;
              });
            }

            // 写作模式：处理生成的内容
            if (mode === "write") {
              // 处理流式内容
              if (data.content) {
                accumulatedText += data.content;
                setDisplayedText(accumulatedText);
              }

              // 处理完整内容（一次性返回的情况）
              if (data.output) {
                setDisplayedText(data.output);
              }

              // 处理完成时的最终内容
              if (data.stage === "completed" && data.data?.final_content) {
                setDisplayedText(data.data.final_content);
                setEditedWriteContent(data.data.final_content);
                setGenerating(false);
                setGenerated(true);
                continue;
              }
            }

            // 处理错误
            if (data.stage === "failed" || data.error) {
              setError(data.message || data.error || "处理失败");
              setGenerating(false);
            }
          } catch (e) {
            console.warn("解析 SSE 数据失败:", dataStr, e);
          }
        }
      }

      setGenerating(false);
      setGenerated(true);
    } catch (err) {
      if (err instanceof Error) {
        if (err.name === "AbortError") {
          setError("请求已取消");
        } else {
          setError(err.message);
        }
      } else {
        setError("未知错误");
      }
      setGenerating(false);
    }
  };

  // 导出为 Word
  const handleExportWord = async () => {
    // 根据模式选择要导出的内容
    const contentToExport = mode === "write" ? editedWriteContent : displayedText;

    if (!contentToExport) {
      setError("没有可导出的内容");
      return;
    }

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

      const formData = new FormData();
      formData.append("content", contentToExport);
      formData.append("filename", `${doc?.title || "结果"}.docx`);

      const response = await fetch(`${API_BASE}/api/v1/workflows/academic-to-official/export-word`, {
        method: "POST",
        headers: {
          ...(getAuthToken() ? { "Authorization": `Bearer ${getAuthToken()}` } : {}),
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`导出失败: ${response.status}`);
      }

      // 下载文件
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${doc?.title || "结果"}.docx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "导出失败");
    }
  };

  useEffect(() => {
    // 翻译模式：先提取内容
    if (mode === "translate") {
      extractDocumentContent();
    } else {
      // 写作模式：直接开始生成
      startGeneration();
    }

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: "#fff", borderLeft: "1px solid #e2e8f0" }}>
      <div className="flex-shrink-0 px-4 py-3" style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}>
        <div className="flex items-center justify-between">
          <span style={{ fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", color: "#374151", fontWeight: 500 }}>
            {mode === "translate" ? "AI 对照翻译" : "AI 公文写作"}
          </span>
          <div className="flex items-center gap-2">
            <span
              className="px-2 py-0.5 rounded-full text-xs"
              style={{ backgroundColor: "#fef2f2", color: "#9b1c1c", border: "1px solid #fecaca", fontSize: 11 }}
            >
              {config.model}
            </span>
            {config.files.length > 0 && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs" style={{ backgroundColor: "#f0fdf4", color: "#16a34a", border: "1px solid #bbf7d0", fontSize: 11 }}>
                <Paperclip size={9} />
                {config.files.length} 个参考文件
              </span>
            )}
          </div>
        </div>
      </div>

      <ThinkingChain active={(generating || generated) && !extracting} progressSteps={progressSteps} />

      {/* 错误显示 */}
      {error && (
        <div className="mx-4 mt-4 p-3 rounded-lg" style={{ backgroundColor: "#fef2f2", border: "1px solid #fecaca" }}>
          <div className="flex items-center gap-2" style={{ color: "#991b1b", fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif" }}>
            <X size={14} />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* 翻译模式：提取中 */}
      {mode === "translate" && extracting && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <motion.div
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.8, repeat: Infinity }}
              className="w-8 h-8 rounded-full border-2 mx-auto mb-3"
              style={{ borderColor: "#16a34a", borderTopColor: "transparent" }}
            />
            <p style={{ color: "#94a3b8", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}>正在提取文档内容...</p>
          </div>
        </div>
      )}

      {/* 翻译模式：编辑界面 */}
      {mode === "translate" && isEditing && !extracting && (
        <div className="flex-1 overflow-auto p-4">
          <div className="mb-3">
            <div className="flex items-center justify-between mb-2">
              <span style={{ fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", color: "#374151", fontWeight: 500 }}>
                提取的文档内容
              </span>
              <span style={{ fontSize: 11, fontFamily: "'Noto Sans SC', sans-serif", color: "#64748b" }}>
                {editedContent.length} 字符
              </span>
            </div>
            <div className="p-2 rounded-lg mb-3" style={{ backgroundColor: "#f0fdf4", border: "1px solid #bbf7d0" }}>
              <p style={{ fontSize: 11.5, fontFamily: "'Noto Sans SC', sans-serif", color: "#166534", lineHeight: 1.6 }}>
                ✅ 请检查并编辑提取的内容。删除页眉、页脚、图表标签等不需要翻译的文字，然后点击"确认并翻译"按钮。
              </p>
            </div>
          </div>

          <textarea
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            className="w-full h-full p-4 rounded-lg resize-none focus:outline-none focus:ring-2"
            style={{
              fontFamily: "'Noto Serif SC', 'SimSun', serif",
              fontSize: 14,
              lineHeight: 2,
              color: "#1e293b",
              backgroundColor: "#f8fafc",
              border: "1px solid #e2e8f0",
              minHeight: 400
            }}
            placeholder="提取的内容将显示在这里..."
          />
        </div>
      )}

      {/* 翻译模式：生成中/已完成的界面 */}
      {mode === "translate" && !isEditing && (
        <div className="flex-1 overflow-auto p-4">
          {displayedText ? (
            <div style={{ fontFamily: "'Noto Serif SC', 'SimSun', serif", fontSize: 14, lineHeight: 2.1, color: "#1e293b", whiteSpace: "pre-wrap" }}>
              {displayedText}
              {generating && (
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                  style={{ display: "inline-block", width: 2, height: 16, backgroundColor: "#9b1c1c", marginLeft: 2, verticalAlign: "text-bottom" }}
                />
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <motion.div
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.8, repeat: Infinity }}
                  className="w-8 h-8 rounded-full border-2 mx-auto mb-3"
                  style={{ borderColor: "#9b1c1c", borderTopColor: "transparent" }}
                />
                <p style={{ color: "#94a3b8", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}>AI 引擎正在思考与生成……</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 写作模式：生成中/可编辑界面 */}
      {mode === "write" && (
        <div className="flex-1 overflow-auto p-4">
          {generating && !displayedText ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <motion.div
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.8, repeat: Infinity }}
                  className="w-8 h-8 rounded-full border-2 mx-auto mb-3"
                  style={{ borderColor: "#9b1c1c", borderTopColor: "transparent" }}
                />
                <p style={{ color: "#94a3b8", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}>AI 引擎正在思考与生成……</p>
              </div>
            </div>
          ) : displayedText && !isWriteEditing ? (
            <div style={{ fontFamily: "'Noto Serif SC', 'SimSun', serif", fontSize: 14, lineHeight: 2.1, color: "#1e293b", whiteSpace: "pre-wrap" }}>
              {displayedText}
              {generating && (
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                  style={{ display: "inline-block", width: 2, height: 16, backgroundColor: "#9b1c1c", marginLeft: 2, verticalAlign: "text-bottom" }}
                />
              )}
            </div>
          ) : displayedText && isWriteEditing ? (
            <textarea
              value={editedWriteContent}
              onChange={(e) => setEditedWriteContent(e.target.value)}
              className="w-full h-full p-4 rounded-lg resize-none focus:outline-none focus:ring-2"
              style={{
                fontFamily: "'Noto Serif SC', 'SimSun', serif",
                fontSize: 14,
                lineHeight: 2,
                color: "#1e293b",
                backgroundColor: "#f8fafc",
                border: "1px solid #e2e8f0",
                minHeight: 400
              }}
              placeholder="生成的公文内容将显示在这里..."
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <motion.div
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.8, repeat: Infinity }}
                  className="w-8 h-8 rounded-full border-2 mx-auto mb-3"
                  style={{ borderColor: "#9b1c1c", borderTopColor: "transparent" }}
                />
                <p style={{ color: "#94a3b8", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}>AI 引擎正在思考与生成……</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 翻译模式：编辑确认按钮 */}
      {mode === "translate" && isEditing && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-shrink-0 px-4 py-3 flex justify-between items-center"
          style={{ borderTop: "1px solid #e2e8f0" }}
        >
          <button
            onClick={() => {
              setIsEditing(false);
              onBack();
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg"
            style={{ border: "1px solid #e2e8f0", color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13 }}
          >
            <X size={14} />
            取消
          </button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={translateConfirmedText}
            disabled={!editedContent || generating}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-white"
            style={{
              backgroundColor: (!editedContent || generating) ? "#cbd5e1" : "#9b1c1c",
              fontFamily: "'Noto Sans SC', sans-serif",
              fontSize: 13,
              boxShadow: "0 1px 4px rgba(155,28,28,0.3)",
              cursor: (!editedContent || generating) ? "not-allowed" : "pointer"
            }}
          >
            {generating ? (
              <>
                <motion.div
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1, repeat: Infinity }}
                  className="w-3 h-3 rounded-full border"
                  style={{ borderColor: "#fff", borderTopColor: "transparent" }}
                />
                翻译中...
              </>
            ) : (
              <>
                <Languages size={14} />
                确认并翻译
              </>
            )}
          </motion.button>
        </motion.div>
      )}

      {/* 写作模式：编辑和导出按钮 */}
      {mode === "write" && generated && !isWriteEditing && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-shrink-0 px-4 py-3 flex justify-between items-center"
          style={{ borderTop: "1px solid #e2e8f0" }}
        >
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              setEditedWriteContent(displayedText);
              setIsWriteEditing(true);
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg"
            style={{ border: "1px solid #e2e8f0", color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13 }}
          >
            <PenLine size={14} />
            编辑内容
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleExportWord}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-white"
            style={{ backgroundColor: "#9b1c1c", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13, boxShadow: "0 1px 4px rgba(155,28,28,0.3)" }}
          >
            <Download size={14} />
            导出为 Word
          </motion.button>
        </motion.div>
      )}

      {/* 写作模式：编辑确认按钮 */}
      {mode === "write" && isWriteEditing && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-shrink-0 px-4 py-3 flex justify-between items-center"
          style={{ borderTop: "1px solid #e2e8f0" }}
        >
          <button
            onClick={() => setIsWriteEditing(false)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg"
            style={{ border: "1px solid #e2e8f0", color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13 }}
          >
            <X size={14} />
            取消
          </button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              setDisplayedText(editedWriteContent);
              setIsWriteEditing(false);
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-white"
            style={{ backgroundColor: "#16a34a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13, boxShadow: "0 1px 4px rgba(22,163,74,0.3)" }}
          >
            <CheckCircle2 size={14} />
            确认修改
          </motion.button>
        </motion.div>
      )}

      {/* 翻译模式：完成导出按钮 */}
      {mode === "translate" && generated && !isEditing && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-shrink-0 px-4 py-3 flex justify-end gap-2"
          style={{ borderTop: "1px solid #e2e8f0" }}
        >
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleExportWord}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-white"
            style={{ backgroundColor: "#9b1c1c", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13, boxShadow: "0 1px 4px rgba(155,28,28,0.3)" }}
          >
            <Download size={14} />
            导出为 Word
          </motion.button>
        </motion.div>
      )}
    </div>
  );
}

// ─── Original Document Viewer ──────────────────────────────────────────────────
function OriginalDocViewer({ doc, onBack }: { doc: Doc | null; onBack?: () => void }) {
  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: "#f8fafc" }}>
      <div className="flex items-center gap-4 px-6 py-4 flex-shrink-0" style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#fff" }}>
        {onBack && (
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
        )}
        <div className="flex items-center gap-2">
          <FileText size={15} style={{ color: "#64748b" }} />
          <span style={{ color: "#374151", fontSize: 13.5, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}>原始文献</span>
        </div>
      </div>
      <div className="flex-1 bg-gray-100">
        {doc?.file_path ? (
          <iframe
            src={`${doc.file_path}#view=FitH`}
            className="w-full h-full border-0"
            title={doc?.title}
            style={{ backgroundColor: "#525659" }}
          />
        ) : (
          <div className="h-full flex items-center justify-center" style={{ color: "#94a3b8", fontSize: 14 }}>
            暂无预览可用
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Library Module Main ───────────────────────────────────────────────��───────
export function LibraryModule() {
  const [libState, setLibState] = useState<LibState>("A");
  const [selectedDoc, setSelectedDoc] = useState<Doc | null>(null);
  const [aiMode, setAiMode] = useState<AiMode>(null);
  const [aiConfig, setAiConfig] = useState<AiConfig>({ model: "DeepSeek V3", files: [] });
  const [showConfig, setShowConfig] = useState(false);
  const [pendingMode, setPendingMode] = useState<AiMode>(null);
  const [docsList, setDocsList] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDocClick = (doc: Doc) => {
    setSelectedDoc(doc);
    setLibState("B");
  };

  const handleDeleteDoc = (docId: string) => {
    setDocsList((prev) => prev.filter((d) => d.id !== docId));
    if (selectedDoc?.id === docId) {
      setSelectedDoc(null);
      setLibState("A");
    }
  };

  // API 文档类型转换为组件内部 Doc 类型
  const apiDocToDoc = (apiDoc: ApiDocument): Doc => ({
    id: apiDoc.id,
    title: apiDoc.title,
    institution: apiDoc.author || "未知机构",
    date: apiDoc.created_at.split("T")[0],
    tags: apiDoc.keywords || [],
    aiStatus: "待处理",
    abstract: apiDoc.content_preview || "暂无摘要",
    source: "其他",
    document_type: apiDoc.document_type,
    original_filename: apiDoc.original_filename,
    // 文件路径格式: storage/uploads/{type}/{hash}{ext}
    // 后端通过 /storage 静态路径提供服务
    file_path: `${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}/storage/${apiDoc.file_path || ""}`,
  });

  // 组件加载时获取文档列表
  useEffect(() => {
    const fetchDocs = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.fetchDocuments();
        const docs = response.items.map(apiDocToDoc);
        setDocsList(docs);
      } catch (err) {
        console.error("获取文档列表失败:", err);
        setError(err instanceof Error ? err.message : "获取文档列表失败");
      } finally {
        setLoading(false);
      }
    };
    fetchDocs();
  }, []);

  const handleUpload = async (files: FileList) => {
    const fileArray = Array.from(files);
    for (const file of fileArray) {
      try {
        await api.uploadDocument({
          file,
          title: file.name,
        });
        // 重新获取文档列表
        const response = await api.fetchDocuments();
        const docs = response.items.map(apiDocToDoc);
        setDocsList(docs);
      } catch (err) {
        console.error("上传文档失败:", err);
        setError(err instanceof Error ? err.message : "上传文档失败");
      }
    }
  };

  // Step 1: open config modal
  const handleActionClick = (mode: AiMode) => {
    setPendingMode(mode);
    setShowConfig(true);
  };

  // Step 2: user confirmed config → start AI
  const handleConfigConfirm = (config: AiConfig) => {
    setAiConfig(config);
    setAiMode(pendingMode);
    setShowConfig(false);
    setLibState("C");
  };

  const handleConfigCancel = () => {
    setShowConfig(false);
    setPendingMode(null);
  };

  const goBack = () => {
    if (libState === "C") {
      setLibState("B");
      setAiMode(null);
    } else if (libState === "B") {
      setLibState("A");
      setSelectedDoc(null);
    }
  };

  return (
    <div className="h-full flex overflow-hidden relative">
      {/* Config Modal */}
      <AnimatePresence>
        {showConfig && (
          <ConfigModal
            mode={pendingMode}
            doc={selectedDoc}
            onCancel={handleConfigCancel}
            onConfirm={handleConfigConfirm}
          />
        )}
      </AnimatePresence>

      {/* ── State A ── */}
      <AnimatePresence mode="wait">
        {libState === "A" && (
          <motion.div
            key="stateA"
            className="w-full h-full"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 280, damping: 28 }}
          >
            <TableView onDocClick={handleDocClick} docs={docsList} onDelete={handleDeleteDoc} onUpload={handleUpload} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── State B: Document Preview Only ── */}
      <AnimatePresence mode="wait">
        {libState === "B" && selectedDoc && (
          <motion.div
            key="docPreview"
            className="absolute inset-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <DocumentPreview doc={selectedDoc} onAction={handleActionClick} onBack={goBack} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── State C: Document Preview + AI Writing (Split View) ── */}
      <AnimatePresence mode="wait">
        {libState === "C" && selectedDoc && (
          <motion.div
            key="splitView"
            className="absolute inset-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <PanelGroup direction="horizontal" className="h-full">
              <Panel defaultSize={50} minSize={30}>
                <OriginalDocViewer doc={selectedDoc} onBack={goBack} />
              </Panel>
              <PanelResizeHandle>
                <div
                  className="w-1 h-full relative flex items-center justify-center"
                  style={{ backgroundColor: "#e2e8f0", cursor: "col-resize" }}
                >
                  <div className="w-0.5 h-8 rounded-full" style={{ backgroundColor: "#cbd5e1" }} />
                </div>
              </PanelResizeHandle>
              <Panel defaultSize={50} minSize={30}>
                <AIWritingCabin doc={selectedDoc} mode={aiMode} config={aiConfig} onBack={goBack} />
              </Panel>
            </PanelGroup>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
