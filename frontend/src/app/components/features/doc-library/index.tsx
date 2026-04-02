// 公文库模块
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FileText,
  Upload,
  Search,
  Filter,
  Download,
  Trash2,
  ChevronLeft,
  ChevronRight,
  X,
  ArrowLeft,
  BookOpen,
  MoreVertical,
} from "lucide-react";
import { Calendar } from "../../ui/calendar";
import {
  fetchOfficialDocuments as apiFetchOfficialDocuments,
  deleteOfficialDocument as apiDeleteOfficialDocument,
  downloadOfficialDocument as apiDownloadOfficialDocument,
  uploadOfficialDocument as apiUploadOfficialDocument,
} from "../../../../api/client";

// 编译报告来源分类
type SourceSource = "世界银行" | "IMF" | "联合国" | "联合国非洲经济委员会" | "非洲开发银行" | "WTO" | "OECD" | "中国人民银行" | "国家统计局" | "其他";

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
  source: SourceSource;
  uploadDate: string;
  description: string;
  fileFormat: "pdf" | "docx" | "txt" | "md";
  fileSize: number;
  file_path?: string;
  content?: string;
  content_preview?: string;
}

// API 基础 URL
const API_BASE = "http://localhost:8000/api/v1/official-documents";

// 获取认证 token
const getAuthToken = () => localStorage.getItem("token") || "";

// API 调用函数（使用统一的 API 客户端）
async function fetchOfficialDocuments(params: {
  page?: number;
  page_size?: number;
  source?: string;
  keyword?: string;
  sort_by?: string;
  sort_order?: string;
}) {
  return apiFetchOfficialDocuments(params);
}

async function deleteOfficialDocument(documentId: string): Promise<{ message: string }> {
  return apiDeleteOfficialDocument(documentId);
}

async function downloadOfficialDocument(documentId: string, filename: string): Promise<void> {
  return apiDownloadOfficialDocument(documentId, filename);
}

async function uploadOfficialDocument(file: File, metadata: {
  title: string;
  description?: string;
  source: string;
}): Promise<any> {
  return apiUploadOfficialDocument({ file, ...metadata });
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
                console.log("=== 删除按钮点击 ===");
                console.log("文档 ID:", docId);
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
      </div>
    </div>
  );
}

// ─── Filter Panel ──────────────────────────────────────────────────────────
function FilterPanel({
  selectedSource,
  selectedDate,
  onSourceChange,
  onDateChange,
  documentDates,
}: {
  selectedSource: SourceSource | "全部";
  selectedDate: string | null;
  onSourceChange: (source: SourceSource | "全部") => void;
  onDateChange: (date: string | null) => void;
  documentDates: string[];
}) {
  const [showCalendar, setShowCalendar] = useState(false);

  return (
    <div className="relative">
      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setShowCalendar(!showCalendar)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg"
        style={{ border: "1px solid #e2e8f0", backgroundColor: "#fff", color: "#374151", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}
      >
        <Filter size={14} style={{ color: "#64748b" }} />
        筛选
        {(selectedSource !== "全部" || selectedDate) && (
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: "#9b1c1c" }}
          />
        )}
      </motion.button>

      <AnimatePresence>
        {showCalendar && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full right-0 mt-2 w-80 rounded-xl overflow-hidden z-50"
            style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", boxShadow: "0 8px 24px rgba(0,0,0,0.12)" }}
          >
            <div className="p-4">
              {/* 来源筛选 */}
              <div className="mb-4">
                <div
                  className="text-xs mb-2"
                  style={{ color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}
                >
                  来源机构
                </div>
                <select
                  value={selectedSource}
                  onChange={(e) => onSourceChange(e.target.value as SourceSource | "全部")}
                  className="w-full px-3 py-2 rounded-lg text-sm"
                  style={{
                    border: "1px solid #e2e8f0",
                    outline: "none",
                    fontFamily: "'Noto Sans SC', sans-serif",
                    backgroundColor: "#f8fafc",
                    color: "#374151",
                  }}
                >
                  <option value="全部">全部来源</option>
                  {Object.keys(sourceConfig).map((source) => (
                    <option key={source} value={source}>
                      {source}
                    </option>
                  ))}
                </select>
              </div>

              {/* 日期筛选 */}
              <div>
                <div
                  className="text-xs mb-2"
                  style={{ color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}
                >
                  上传日期
                </div>
                <CalendarPicker
                  dates={documentDates}
                  selectedDate={selectedDate}
                  onDateSelect={(date) => {
                    onDateChange(date === "全部" ? null : date);
                  }}
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Upload Dialog ─────────────────────────────────────────────────────
interface UploadDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File, metadata: { title: string; description?: string; source: string }) => Promise<void>;
}

function UploadDialog({ isOpen, onClose, onUpload }: UploadDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [source, setSource] = useState<SourceSource>("世界银行");
  const [uploading, setUploading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      // 自动填充标题
      setTitle(e.target.files[0].name.replace(/\.[^/.]+$/, ""));
    }
  };

  const handleUpload = async () => {
    if (!file || !title) return;

    setUploading(true);
    try {
      await onUpload(file, { title, description, source });
      onClose();
      // 重置表单
      setFile(null);
      setTitle("");
      setDescription("");
      setSource("世界银行");
    } catch (error) {
      console.error("上传失败:", error);
      alert("上传失败，请重试");
    } finally {
      setUploading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-[9999]"
          style={{ backgroundColor: "rgba(15,23,42,0.45)", backdropFilter: "blur(4px)" }}
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.94, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: 10 }}
            transition={{ type: "spring", stiffness: 320, damping: 28 }}
            className="w-full max-w-md rounded-2xl overflow-hidden mx-auto mt-[10vh]"
            style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", boxShadow: "0 20px 60px rgba(0,0,0,0.18)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-6 py-4 border-b" style={{ backgroundColor: "#f8fafc" }}>
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold" style={{ fontFamily: "'Noto Sans SC', sans-serif" }}>
                  上传公文
                </h2>
                <button
                  onClick={onClose}
                  className="w-7 h-7 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: "#f1f5f9", color: "#64748b" }}
                >
                  <X size={14} />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              {/* 文件选择 */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ fontFamily: "'Noto Sans SC', sans-serif", color: "#374151" }}>
                  选择文件
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  onChange={handleFileSelect}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  style={{ fontFamily: "'Noto Sans SC', sans-serif", borderColor: "#e2e8f0" }}
                />
                {file && (
                  <p className="text-xs mt-1" style={{ color: "#64748b" }}>
                    已选择: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>

              {/* 标题 */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ fontFamily: "'Noto Sans SC', sans-serif", color: "#374151" }}>
                  公文标题 *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  style={{ fontFamily: "'Noto Sans SC', sans-serif", borderColor: "#e2e8f0" }}
                  placeholder="请输入公文标题"
                />
              </div>

              {/* 描述 */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ fontFamily: "'Noto Sans SC', sans-serif", color: "#374151" }}>
                  描述
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  style={{ fontFamily: "'Noto Sans SC', sans-serif", borderColor: "#e2e8f0" }}
                  placeholder="请输入公文描述（可选）"
                  rows={3}
                />
              </div>

              {/* 来源机构 */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ fontFamily: "'Noto Sans SC', sans-serif", color: "#374151" }}>
                  来源机构 *
                </label>
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value as SourceSource)}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  style={{ fontFamily: "'Noto Sans SC', sans-serif", borderColor: "#e2e8f0", backgroundColor: "#fff" }}
                >
                  {Object.keys(sourceConfig).map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              {/* 按钮 */}
              <div className="flex gap-3 pt-2">
                <motion.button
                  whileHover={{ backgroundColor: "#f1f5f9" }}
                  onClick={onClose}
                  className="flex-1 py-2.5 rounded-xl"
                  style={{ border: "1px solid #e2e8f0", color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 14 }}
                  disabled={uploading}
                >
                  取消
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.01, boxShadow: "0 4px 16px rgba(155,28,28,0.35)" }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleUpload}
                  disabled={!file || !title || uploading}
                  className="flex-1 py-2.5 rounded-xl text-white flex items-center justify-center gap-2"
                  style={{
                    backgroundColor: "#9b1c1c",
                    fontFamily: "'Noto Sans SC', sans-serif",
                    fontSize: 14,
                    fontWeight: 500,
                    boxShadow: "0 2px 10px rgba(155,28,28,0.3)",
                    opacity: (!file || !title || uploading) ? 0.5 : 1,
                  }}
                >
                  <Upload size={15} />
                  {uploading ? "上传中..." : "上传"}
                </motion.button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ─── Document Preview ──────────────────────────────────────────────────────────
function DocumentPreview({ doc, onBack, onDownload }: { doc: DocLibraryItem; onBack: () => void; onDownload: (docId: string, filename: string) => void }) {
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
            返回列表
          </motion.button>
          <div className="flex items-center gap-2">
            <BookOpen size={15} style={{ color: "#64748b" }} />
            <div>
              <span style={{ color: "#374151", fontSize: 13.5, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}>公文内容</span>
              <p style={{ color: "#94a3b8", fontSize: 11, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 1 }}>{doc.title}</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onDownload(doc.id, doc.title)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
            style={{ border: "1px solid #e2e8f0", backgroundColor: "#fff", color: "#374151", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13 }}
          >
            <Download size={14} />
            下载文件
          </motion.button>
        </div>
      </div>

      {/* 文档内容预览 */}
      <div className="flex-1 overflow-auto bg-gray-50 p-8">
        <div
          className="max-w-4xl mx-auto bg-white rounded-lg shadow-sm"
          style={{ padding: "48px", minHeight: "600px" }}
        >
          {/* 文档标题 */}
          <h1
            className="mb-6 pb-6"
            style={{
              fontSize: 28,
              fontWeight: 600,
              color: "#0f172a",
              fontFamily: "'Noto Sans SC', sans-serif",
              borderBottom: "3px solid #e2e8f0",
              textAlign: "center",
            }}
          >
            {doc.title}
          </h1>

          {/* 文档元信息 */}
          <div className="mb-8 flex justify-center gap-6" style={{ fontSize: 13, color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif" }}>
            <div className="flex items-center gap-2">
              <span style={{ fontWeight: 500 }}>来源:</span>
              <span>{doc.source}</span>
            </div>
            <div className="flex items-center gap-2">
              <span style={{ fontWeight: 500 }}>上传日期:</span>
              <span>{doc.uploadDate}</span>
            </div>
            <div className="flex items-center gap-2">
              <span style={{ fontWeight: 500 }}>文件类型:</span>
              <span style={{ textTransform: "uppercase" }}>{doc.fileFormat}</span>
            </div>
          </div>

          {/* 文档内容 */}
          {doc.content ? (
            <div
              style={{
                color: "#374151",
                fontFamily: "'Noto Sans SC', sans-serif",
                lineHeight: 2,
                fontSize: 15,
                whiteSpace: "pre-wrap",
              }}
            >
              {doc.content}
            </div>
          ) : doc.content_preview ? (
            <div
              style={{
                color: "#374151",
                fontFamily: "'Noto Sans SC', sans-serif",
                lineHeight: 2,
                fontSize: 15,
                whiteSpace: "pre-wrap",
              }}
            >
              {doc.content_preview}
            </div>
          ) : (
            <div className="text-center py-20">
              <FileText size={72} style={{ color: "#e2e8f0" }} />
              <p style={{ color: "#94a3b8", fontSize: 15, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 20, fontWeight: 500 }}>
                暂无内容预览
              </p>
              <p style={{ color: "#94a3b8", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 12 }}>
                请点击右上角下载按钮查看完整文件
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Table View ──────────────────────────────────────────────────────────
function TableView({
  onDocClick,
  docs,
  onDelete,
  onUploadClick,
}: {
  onDocClick: (doc: DocLibraryItem) => void;
  docs: DocLibraryItem[];
  onDelete: (docId: string) => void;
  onUploadClick: () => void;
}) {
  const [searchVal, setSearchVal] = useState("");
  const [selectedSource, setSelectedSource] = useState<SourceSource | "全部">("全部");
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  // 从文档列表中提取唯一日期
  const documentDates = [...new Set(docs.map((doc) => doc.uploadDate))].sort().reverse();

  const filtered = docs.filter((d) => {
    const matchSearch =
      d.title.toLowerCase().includes(searchVal.toLowerCase()) ||
      d.description.toLowerCase().includes(searchVal.toLowerCase());
    const matchSource = selectedSource === "全部" || d.source === selectedSource;
    const matchDate = !selectedDate || d.uploadDate === selectedDate;
    return matchSearch && matchSource && matchDate;
  });

  return (
    <div className="h-full flex flex-col p-6">
      <div className="flex items-center justify-between mb-5 flex-shrink-0">
        <div>
          <h1 className="text-xl" style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 600 }}>
            公文库
          </h1>
          <p style={{ color: "#64748b", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 2 }}>
            已验证的优质公文模板，供AI写作参考风格
            {(selectedSource !== "全部" || selectedDate) && (
              <span style={{ color: "#9b1c1c" }}>（已筛选）</span>
            )}
          </p>
          <p style={{ color: "#94a3b8", fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 1 }}>
            共 {filtered.length} 份公文
          </p>
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            onClick={onUploadClick}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-white"
            style={{ backgroundColor: "#9b1c1c", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13, boxShadow: "0 1px 6px rgba(155,28,28,0.3)" }}
          >
            <Upload size={14} />
            上传公文
          </motion.button>
        </div>
      </div>

      <div className="flex items-center gap-3 mb-4 flex-shrink-0">
        <div className="flex-1 relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#94a3b8" }} />
          <input
            type="text"
            placeholder="搜索公文标题或描述……"
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg text-sm outline-none"
            style={{ border: "1px solid #e2e8f0", backgroundColor: "#fff", color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13 }}
          />
        </div>
        <FilterPanel
          selectedSource={selectedSource}
          selectedDate={selectedDate}
          onSourceChange={setSelectedSource}
          onDateChange={setSelectedDate}
          documentDates={documentDates}
        />
      </div>

      <div className="flex-1 overflow-auto rounded-xl" style={{ border: "1px solid #e2e8f0" }}>
        <table className="w-full">
          <thead style={{ backgroundColor: "#f8fafc", position: "sticky", top: 0, zIndex: 1 }}>
            <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
              {["公文标题", "来源", "上传日期", "文件大小", ""].map((h) => (
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
            {filtered.map((doc) => {
              const sourceColor = sourceConfig[doc.source].color;
              const fileSizeMB = (doc.fileSize / 1024 / 1024).toFixed(2);
              return (
                <tr
                  key={doc.id}
                  onClick={() => {
                    console.log("Table row clicked:", doc.id, doc.title);
                    onDocClick(doc);
                  }}
                  className="cursor-pointer group"
                  style={{ borderBottom: "1px solid #f1f5f9", transition: "background-color 0.15s" }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "#fafcff";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "transparent";
                  }}
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
                        backgroundColor: `${sourceColor}11`,
                        color: sourceColor,
                        border: `1px solid ${sourceColor}22`,
                        fontFamily: "'Noto Sans SC', sans-serif",
                      }}
                    >
                      {doc.source}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span style={{ color: "#64748b", fontSize: 12.5, fontFamily: "'Noto Sans SC', sans-serif" }}>
                      {doc.uploadDate}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span style={{ color: "#64748b", fontSize: 12.5, fontFamily: "'Noto Sans SC', sans-serif" }}>
                      {fileSizeMB} MB
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <MoreVerticalButton docId={doc.id} onDelete={onDelete} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────
export function DocLibraryModule() {
  const [documents, setDocuments] = useState<DocLibraryItem[]>([]);
  const [viewState, setViewState] = useState<"list" | "preview">("list");
  const [selectedDoc, setSelectedDoc] = useState<DocLibraryItem | null>(null);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [loading, setLoading] = useState(false);

  // 加载公文列表
  const loadDocuments = async () => {
    setLoading(true);
    try {
      // 添加时间戳参数，强制绕过缓存
      const response = await fetchOfficialDocuments({
        page: 1,
        page_size: 100,
        sort_by: "created_at",
        sort_order: "desc",
      });

      // 转换数据格式
      const items = response.items.map((item: any) => ({
        id: item.id,
        title: item.title,
        source: item.source,
        uploadDate: new Date(item.created_at * 1000).toISOString().split('T')[0], // Unix 时间戳（秒）转为毫秒
        description: item.description || "",
        fileFormat: item.document_type as any,
        fileSize: item.file_size,
        file_path: item.file_path,
        content: item.content,
        content_preview: item.content_preview,
      }));

      setDocuments(items);
    } catch (error) {
      console.error("加载公文列表失败:", error);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    loadDocuments();
    console.log("=== 公文库组件已挂载 ===");
  }, []);

  // 处理文档点击
  const handleDocClick = (doc: DocLibraryItem) => {
    setSelectedDoc(doc);
    setViewState("preview");
  };

  // 处理返回
  const handleBack = () => {
    setSelectedDoc(null);
    setViewState("list");
  };

  // 处理上传
  const handleUpload = async (file: File, metadata: { title: string; description?: string; source: string }) => {
    await uploadOfficialDocument(file, metadata);
    await loadDocuments();
  };

  // 处理删除
  const handleDelete = async (docId: string) => {
    if (!confirm("确定要删除这个公文吗？")) return;

    console.log("=== 开始删除公文 ===");
    console.log("要删除的文档 ID:", docId);

    try {
      const result = await deleteOfficialDocument(docId);
      console.log("删除 API 响应:", result);

      // 等待一下，确保后端处理完成
      await new Promise(resolve => setTimeout(resolve, 100));

      console.log("重新加载文档列表...");
      await loadDocuments();
      console.log("文档列表已更新");
    } catch (error) {
      console.error("删除失败:", error);
      alert("删除失败，请重试");
    }
  };

  // 处理下载
  const handleDownload = async (docId: string, filename: string) => {
    try {
      await downloadOfficialDocument(docId, filename);
    } catch (error) {
      console.error("下载失败:", error);
      alert("下载失败，请重试");
    }
  };

  return (
    <div className="h-full relative overflow-hidden">
      {/* Upload Dialog */}
      <UploadDialog
        isOpen={showUploadDialog}
        onClose={() => setShowUploadDialog(false)}
        onUpload={handleUpload}
      />

      {/* List View */}
      <AnimatePresence mode="wait">
        {viewState === "list" && (
          <motion.div
            key="listView"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0"
          >
            {loading ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-sm" style={{ color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif" }}>
                  加载中...
                </div>
              </div>
            ) : (
              <TableView
                onDocClick={handleDocClick}
                docs={documents}
                onDelete={handleDelete}
                onUploadClick={() => setShowUploadDialog(true)}
              />
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Preview View */}
      <AnimatePresence mode="wait">
        {viewState === "preview" && selectedDoc && (
          <motion.div
            key="previewView"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0"
          >
            <DocumentPreview
              doc={selectedDoc}
              onBack={handleBack}
              onDownload={handleDownload}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
