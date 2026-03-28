import { useState } from "react";
import { motion } from "motion/react";
import {
  ArrowLeft,
  Search,
  Download,
  Eye,
  Trash2,
  CheckSquare,
  Square,
} from "lucide-react";

interface HistoryItem {
  id: number;
  title: string;
  date: string;
  group: "今天" | "昨天" | "更早";
}

interface HistoryPanelProps {
  onBack: () => void;
}

const initialHistory: HistoryItem[] = [
  { id: 1, title: "美联储利率决议深度分析", date: "2024-12-01", group: "今天" },
  { id: 2, title: "越南经济体外资政策研究", date: "2024-12-01", group: "今天" },
  { id: 3, title: "2024年Q3东盟货币形势", date: "2024-12-01", group: "今天" },
  { id: 4, title: "日本央行YCC政策终止影响", date: "2024-11-30", group: "昨天" },
  { id: 5, title: "欧元区通胀传导机制研究", date: "2024-11-30", group: "昨天" },
  { id: 6, title: "全球外汇储备结构转变", date: "2024-11-15", group: "更早" },
  { id: 7, title: "新兴市场债务风险评估报告", date: "2024-11-10", group: "更早" },
];

export function HistoryPanel({ onBack }: HistoryPanelProps) {
  const [history, setHistory] = useState<HistoryItem[]>(initialHistory);
  const [searchVal, setSearchVal] = useState("");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [isSelectMode, setIsSelectMode] = useState(false);

  const filteredHistory = history.filter((item) =>
    item.title.toLowerCase().includes(searchVal.toLowerCase())
  );

  const groupedHistory = {
    "今天": filteredHistory.filter((item) => item.group === "今天"),
    "昨天": filteredHistory.filter((item) => item.group === "昨天"),
    "更早": filteredHistory.filter((item) => item.group === "更早"),
  };

  const handleSelectAll = () => {
    if (selectedIds.length === filteredHistory.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredHistory.map((item) => item.id));
    }
  };

  const handleToggleSelect = (id: number) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((i) => i !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleDeleteSelected = () => {
    setHistory(history.filter((item) => !selectedIds.includes(item.id)));
    setSelectedIds([]);
    setIsSelectMode(false);
  };

  const handleDeleteOne = (id: number) => {
    setHistory(history.filter((item) => item.id !== id));
  };

  return (
    <div className="h-full flex flex-col overflow-hidden" style={{ backgroundColor: "#fff" }}>
      {/* Header */}
      <div
        className="flex-shrink-0 flex items-center gap-4 px-6 py-4"
        style={{ borderBottom: "1px solid #e2e8f0" }}
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
          历史记录
        </h1>
      </div>

      {/* Search Bar */}
      <div className="flex-shrink-0 px-6 py-3" style={{ borderBottom: "1px solid #e2e8f0" }}>
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#94a3b8" }} />
          <input
            type="text"
            placeholder="搜索历史记录..."
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            className="w-full px-4 py-2 pl-10 rounded-lg text-sm"
            style={{
              border: "1px solid #e2e8f0",
              outline: "none",
              fontFamily: "'Noto Sans SC', sans-serif",
            }}
          />
        </div>
      </div>

      {/* Toolbar */}
      <div
        className="flex-shrink-0 flex items-center justify-between px-6 py-2"
        style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}
      >
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ backgroundColor: "#e2e8f0" }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsSelectMode(!isSelectMode)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm"
            style={{
              border: "1px solid #e2e8f0",
              backgroundColor: isSelectMode ? "#e2e8f0" : "#fff",
              color: "#64748b",
              fontFamily: "'Noto Sans SC', sans-serif",
            }}
          >
            {isSelectMode ? <CheckSquare size={14} /> : <Square size={14} />}
            选择
          </motion.button>
          {isSelectMode && selectedIds.length > 0 && (
            <motion.button
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              whileHover={{ backgroundColor: "#fee2e2" }}
              whileTap={{ scale: 0.95 }}
              onClick={handleDeleteSelected}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm"
              style={{ border: "1px solid #fecaca", backgroundColor: "#fef2f2", color: "#dc2626", fontFamily: "'Noto Sans SC', sans-serif" }}
            >
              <Trash2 size={14} />
              删除已选 ({selectedIds.length})
            </motion.button>
          )}
          {isSelectMode && (
            <motion.button
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              whileHover={{ backgroundColor: "#e2e8f0" }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSelectAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm"
              style={{ border: "1px solid #e2e8f0", backgroundColor: "#fff", color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif" }}
            >
              {selectedIds.length === filteredHistory.length ? "取消全选" : "全选"}
            </motion.button>
          )}
        </div>
        <span style={{ color: "#94a3b8", fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif" }}>
          共 {filteredHistory.length} 条记录
        </span>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-auto p-4">
        {Object.entries(groupedHistory).map(([group, items]) => {
          if (items.length === 0) return null;
          return (
            <div key={group} className="mb-4">
              <div
                className="px-2 py-1 text-xs"
                style={{ color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}
              >
                {group}
              </div>
              {items.map((item) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-3 p-3 rounded-lg mb-2"
                  style={{
                    backgroundColor: selectedIds.includes(item.id) ? "#f1f5f9" : "#fff",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  {isSelectMode && (
                    <button
                      onClick={() => handleToggleSelect(item.id)}
                      className="flex-shrink-0"
                    >
                      {selectedIds.includes(item.id) ? (
                        <CheckSquare size={16} style={{ color: "#9b1c1c" }} />
                      ) : (
                        <Square size={16} style={{ color: "#94a3b8" }} />
                      )}
                    </button>
                  )}
                  <div className="flex-1 min-w-0">
                    <div
                      className="text-sm truncate"
                      style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif" }}
                    >
                      {item.title}
                    </div>
                    <div
                      className="text-xs"
                      style={{ color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif" }}
                    >
                      {item.date}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <motion.button
                      whileHover={{ backgroundColor: "#f1f5f9" }}
                      className="p-1.5 rounded"
                      title="预览"
                    >
                      <Eye size={14} style={{ color: "#64748b" }} />
                    </motion.button>
                    <motion.button
                      whileHover={{ backgroundColor: "#f1f5f9" }}
                      className="p-1.5 rounded"
                      title="下载"
                    >
                      <Download size={14} style={{ color: "#64748b" }} />
                    </motion.button>
                    <motion.button
                      whileHover={{ backgroundColor: "#fee2e2" }}
                      onClick={() => handleDeleteOne(item.id)}
                      className="p-1.5 rounded"
                      title="删除"
                    >
                      <Trash2 size={14} style={{ color: "#dc2626" }} />
                    </motion.button>
                  </div>
                </motion.div>
              ))}
            </div>
          );
        })}
        {filteredHistory.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12">
            <Search size={32} style={{ color: "#cbd5e1" }} />
            <p style={{ color: "#94a3b8", fontSize: 14, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 8 }}>
              没有找到相关历史记录
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
