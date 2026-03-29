// 公文库模块
import { useState } from "react";
import { motion } from "motion/react";
import {
  FileText,
  Upload,
  Search,
  Filter,
  Download,
  Eye,
  Trash2,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
} from "lucide-react";
import { Calendar } from "../../ui/calendar";

// 编译报告来源分类
type SourceSource = "世界银行" | "IMF" | "联合国" | "联合国非洲经济委员会" | "非洲开发银行" | "WTO" | "OECD" | "中国人民银行" | "国家统计局" | "���他";

const sourceConfig: Record<SourceSource, { color: string }> = {
  "世界银行": { color: "#ea580c" },
  "IMF": { color: "#2563eb" },
  "联合国": { color: "#059669" },
  "联合国非洲经济委员会": { color: "#0891b2" },
  "非洲开发银行": { color: "#8b5cf6" },
  "WTO": { color: "#06b6d4" },
  "OECD": { color: "#10b981" },
  "中国人民银行": { color: "#dc2626" },
  "国家统计局": { color: "#f97316" },
  "其他": { color: "#6b7280" },
};

interface DocLibraryItem {
  id: string;
  title: string;
  sourceSource: SourceSource; // 编译报告来源
  uploadDate: string;
  description: string;
  fileFormat: "pdf" | "docx" | "txt" | "md";
  fileSize: string;
}

// 示例公文库数据
const sampleDocLibrary: DocLibraryItem[] = [
  {
    id: "1",
    title: "全球金融稳定报告要点摘编",
    sourceSource: "IMF",
    uploadDate: "2024-11-08",
    description: "国际货币基金组织《全球金融稳定报告》核心观点和政策建议摘编",
    fileFormat: "docx",
    fileSize: "1.8 MB",
  },
];

// ─── Calendar Picker (传统日历视图) ───────────────────────────────────
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

  // ���份导航
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

export function DocLibraryModule() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSource, setSelectedSource] = useState<SourceSource | "全部">("全部");
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"date" | "name" | "size">("date");
  const [showCalendar, setShowCalendar] = useState(false);

  // 从文档列表中提取唯一日期
  const documentDates = Array.from(
    new Set(sampleDocLibrary.map((doc) => doc.uploadDate))
  ).sort((a, b) => new Date(b).getTime() - new Date(a).getTime());

  // 过滤和排序文档
  const filteredDocs = sampleDocLibrary
    .filter((doc) => {
      const matchSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchSource = selectedSource === "全部" || doc.sourceSource === selectedSource;
      const matchDate = !selectedDate || doc.uploadDate === selectedDate;
      return matchSearch && matchSource && matchDate;
    })
    .sort((a, b) => {
      if (sortBy === "date") return new Date(b.uploadDate).getTime() - new Date(a.uploadDate).getTime();
      if (sortBy === "name") return a.title.localeCompare(b.title, "zh");
      if (sortBy === "size") return parseFloat(b.fileSize) - parseFloat(a.fileSize);
      return 0;
    });

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div
        className="flex-shrink-0 flex items-center justify-between px-6 py-4"
        style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#fff" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="flex items-center justify-center rounded-xl"
            style={{ width: 40, height: 40, backgroundColor: "#fef2f2", border: "1px solid #fecaca" }}
          >
            <FileText size={20} style={{ color: "#9b1c1c" }} />
          </div>
          <div>
            <h1 style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 18, fontWeight: 600 }}>
              公文库
            </h1>
            <p style={{ color: "#94a3b8", fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 2 }}>
              已验证的优质公文模板，供AI写作参考风格
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-white"
            style={{ backgroundColor: "#9b1c1c", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}
          >
            <Upload size={14} />
            上传公文
          </motion.button>
        </div>
      </div>

      {/* Filters Bar */}
      <div
        className="flex-shrink-0 flex items-center gap-4 px-6 py-3"
        style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}
      >
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#94a3b8" }} />
          <input
            type="text"
            placeholder="搜索公文标题或描述..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 pl-9 rounded-lg text-sm"
            style={{
              border: "1px solid #e2e8f0",
              outline: "none",
              fontFamily: "'Noto Sans SC', sans-serif",
              backgroundColor: "#fff",
            }}
          />
        </div>

        {/* Source Filter */}
        <div className="flex items-center gap-2">
          <Filter size={14} style={{ color: "#94a3b8" }} />
          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value as SourceSource | "全部")}
            className="px-3 py-2 rounded-lg text-sm"
            style={{
              border: "1px solid #e2e8f0",
              outline: "none",
              fontFamily: "'Noto Sans SC', sans-serif",
              backgroundColor: "#fff",
              color: "#374151",
            }}
          >
            <option value="全部">全部编译报告来源</option>
            {Object.keys(sourceConfig).map((source) => (
              <option key={source} value={source}>
                {source}
              </option>
            ))}
          </select>
        </div>

        {/* Date Filter */}
        <div className="relative">
          <motion.button
            onClick={() => setShowCalendar(!showCalendar)}
            whileHover={{ backgroundColor: "#f1f5f9" }}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm"
            style={{
              border: "1px solid #e2e8f0",
              fontFamily: "'Noto Sans SC', sans-serif",
              backgroundColor: "#fff",
              color: "#374151",
            }}
          >
            <CalendarIcon size={14} style={{ color: "#94a3b8" }} />
            <span>{selectedDate || "全部日期"}</span>
            {selectedDate && (
              <span
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedDate(null);
                }}
                className="ml-1 hover:text-red-600"
                style={{ cursor: "pointer" }}
              >
                ×
              </span>
            )}
          </motion.button>

          {/* Calendar Dropdown */}
          {showCalendar && (
            <div
              className="absolute top-full left-0 mt-2 p-4 rounded-xl shadow-lg z-50"
              style={{
                backgroundColor: "#fff",
                border: "1px solid #e2e8f0",
                width: 320,
              }}
            >
              <CalendarPicker
                dates={documentDates}
                selectedDate={selectedDate}
                onDateSelect={(date) => {
                  setSelectedDate(date === "全部" ? null : date);
                  setShowCalendar(false);
                }}
              />
            </div>
          )}
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <span style={{ fontSize: 12, color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif" }}>
            排序:
          </span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "date" | "name" | "size")}
            className="px-3 py-2 rounded-lg text-sm"
            style={{
              border: "1px solid #e2e8f0",
              outline: "none",
              fontFamily: "'Noto Sans SC', sans-serif",
              backgroundColor: "#fff",
              color: "#374151",
            }}
          >
            <option value="date">按日期</option>
            <option value="name">按名称</option>
            <option value="size">按大小</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div
        className="flex-shrink-0 flex items-center gap-4 px-6 py-2"
        style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#fff" }}
      >
        <div className="flex items-center gap-2">
          <CheckCircle2 size={14} style={{ color: "#16a34a" }} />
          <span style={{ fontSize: 12, color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif" }}>
            已验证公文 {sampleDocLibrary.length} 篇
          </span>
        </div>
        <div style={{ width: 1, height: 16, backgroundColor: "#e2e8f0" }} />
        <span style={{ fontSize: 12, color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif" }}>
          显示 {filteredDocs.length} 条结果
        </span>
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-auto p-6">
        <div className="grid gap-3">
          {filteredDocs.map((doc, index) => {
            const sourceColor = sourceConfig[doc.sourceSource].color;
            return (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className="p-4 rounded-xl"
                style={{
                  backgroundColor: "#fff",
                  border: "1px solid #e2e8f0",
                  boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
                }}
              >
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div
                    className="flex items-center justify-center rounded-lg flex-shrink-0"
                    style={{
                      width: 48,
                      height: 48,
                      backgroundColor: `${sourceColor}10`,
                      border: `1px solid ${sourceColor}22`,
                    }}
                  >
                    <FileText size={22} style={{ color: sourceColor }} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex-1">
                        <h3
                          className="text-base font-medium mb-1"
                          style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif" }}
                        >
                          {doc.title}
                        </h3>
                        <p
                          className="text-sm line-clamp-2"
                          style={{ color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif" }}
                        >
                          {doc.description}
                        </p>
                      </div>
                    </div>

                    {/* Metadata */}
                    <div className="flex items-center gap-3 text-xs" style={{ color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif" }}>
                      <span
                        className="px-2 py-0.5 rounded"
                        style={{
                          backgroundColor: `${sourceColor}10`,
                          color: sourceColor,
                          fontWeight: 500,
                        }}
                      >
                        {doc.sourceSource}
                      </span>
                      <span>•</span>
                      <span>{doc.uploadDate}</span>
                      <span>•</span>
                      <span>{doc.fileSize}</span>
                      <span>•</span>
                      <span className="uppercase">{doc.fileFormat}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-1">
                    <motion.button
                      whileHover={{ backgroundColor: "#f1f5f9" }}
                      className="p-2 rounded-lg"
                      title="预览"
                    >
                      <Eye size={15} style={{ color: "#64748b" }} />
                    </motion.button>
                    <motion.button
                      whileHover={{ backgroundColor: "#f1f5f9" }}
                      className="p-2 rounded-lg"
                      title="下载"
                    >
                      <Download size={15} style={{ color: "#64748b" }} />
                    </motion.button>
                    <motion.button
                      whileHover={{ backgroundColor: "#fee2e2" }}
                      className="p-2 rounded-lg"
                      title="删除"
                    >
                      <Trash2 size={15} style={{ color: "#dc2626" }} />
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {filteredDocs.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16">
            <FileText size={48} style={{ color: "#e2e8f0" }} />
            <p style={{ color: "#94a3b8", fontSize: 14, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 12 }}>
              没有找到匹配的公文
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
