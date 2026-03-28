import { useState, useRef } from "react";
import { motion } from "motion/react";
import {
  Upload,
  FileText,
  X,
  Cpu,
  CheckCircle2,
  Paperclip,
  Sparkles,
  Languages,
  PenLine,
} from "lucide-react";
import { AiMode, AiConfig, Doc } from "../../../../types";
import { models } from "../../../../config";

// AI 配置弹窗组件
export function ConfigModal({
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
    onConfirm({ model: models.find((m) => m.id === selectedModel)?.label ?? "DeepSeek V3", files: attachedFiles });
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
