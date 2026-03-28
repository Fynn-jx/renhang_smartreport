import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  ImageIcon,
  Upload,
  Download,
  CheckCircle2,
  RotateCcw,
  Languages,
  RefreshCw,
  Plus,
  X,
  Clock,
  Loader2,
} from "lucide-react";

interface ImageItem {
  id: string;
  url: string;
  name: string;
  status: "pending" | "translating" | "done";
  progress: number;
}

type ImgState = "empty" | "preview" | "processing" | "results";

const MAX_IMAGES = 5;

export function ImageModule() {
  const [imgState, setImgState] = useState<ImgState>("empty");
  const [images, setImages] = useState<ImageItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [sliderPos, setSliderPos] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const sliderRef = useRef<HTMLDivElement>(null);
  const intervalsRef = useRef<Record<string, number>>({});

  const selectedImage = images.find((img) => img.id === selectedId) ?? null;

  const addFiles = (files: File[]) => {
    const remaining = MAX_IMAGES - images.length;
    const toAdd = files.slice(0, remaining).filter((f) => f.type.startsWith("image/"));
    const newItems: ImageItem[] = [];
    toAdd.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const item: ImageItem = {
          id: Math.random().toString(36).slice(2),
          url: e.target?.result as string,
          name: file.name,
          status: "pending",
          progress: 0,
        };
        setImages((prev) => {
          const updated = [...prev, item];
          if (!selectedId) setSelectedId(item.id);
          return updated;
        });
        if (!selectedId) setSelectedId(toAdd[0]?.name ?? "");
      };
      reader.readAsDataURL(file);
    });
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const files = Array.from(e.dataTransfer.files);
      addFiles(files);
      setImgState("preview");
    },
    [images.length, selectedId]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    addFiles(files);
    setImgState("preview");
    e.target.value = "";
  };

  const removeImage = (id: string) => {
    setImages((prev) => {
      const updated = prev.filter((img) => img.id !== id);
      if (selectedId === id) setSelectedId(updated[0]?.id ?? null);
      return updated;
    });
    if (images.length <= 1) setImgState("empty");
  };

  const translateImage = (id: string) => {
    setImages((prev) =>
      prev.map((img) => (img.id === id ? { ...img, status: "translating", progress: 0 } : img))
    );
    let p = 0;
    intervalsRef.current[id] = window.setInterval(() => {
      p += Math.random() * 5 + 1.5;
      if (p >= 100) {
        p = 100;
        clearInterval(intervalsRef.current[id]);
        setImages((prev) =>
          prev.map((img) => (img.id === id ? { ...img, status: "done", progress: 100 } : img))
        );
      } else {
        setImages((prev) =>
          prev.map((img) => (img.id === id ? { ...img, progress: p } : img))
        );
      }
    }, 100);
  };

  const startAll = () => {
    setImgState("processing");
    images.forEach((img, i) => {
      setTimeout(() => translateImage(img.id), i * 800);
    });
  };

  useEffect(() => {
    if (imgState === "processing") {
      const allDone = images.length > 0 && images.every((img) => img.status === "done");
      if (allDone) {
        setTimeout(() => {
          setImgState("results");
          setSliderPos(50);
        }, 500);
      }
    }
  }, [images, imgState]);

  // Slider drag logic
  const handleSliderMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !sliderRef.current) return;
      const rect = sliderRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const pct = Math.max(2, Math.min(98, (x / rect.width) * 100));
      setSliderPos(pct);
    };
    const handleMouseUp = () => setIsDragging(false);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging]);

  const reset = () => {
    Object.values(intervalsRef.current).forEach(clearInterval);
    intervalsRef.current = {};
    setImages([]);
    setSelectedId(null);
    setImgState("empty");
    setSliderPos(50);
  };

  const regenerate = (id: string) => {
    setImages((prev) =>
      prev.map((img) => (img.id === id ? { ...img, status: "pending", progress: 0 } : img))
    );
    setTimeout(() => translateImage(id), 300);
  };

  // ── Empty ──────────────────────────────────────────────────────────────────
  if (imgState === "empty") {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-xl"
        >
          <div className="text-center mb-7">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl mb-4" style={{ backgroundColor: "#fef2f2", border: "1px solid #fecaca" }}>
              <Languages size={22} style={{ color: "#9b1c1c" }} />
            </div>
            <h1 style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 600, fontSize: 24 }}>图片转译</h1>
            <p style={{ color: "#64748b", fontSize: 14, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 6 }}>
              支持一次上传最多 5 张图片，AI 将批量识别并翻译外文内容
            </p>
          </div>

          <motion.div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onClick={() => fileInputRef.current?.click()}
            animate={{ borderColor: isDragOver ? "#9b1c1c" : "#e2e8f0", backgroundColor: isDragOver ? "#fef2f2" : "#fff" }}
            className="rounded-2xl p-16 cursor-pointer flex flex-col items-center justify-center"
            style={{ border: "2px dashed #e2e8f0", transition: "all 0.2s", boxShadow: "0 1px 12px rgba(0,0,0,0.03)" }}
            whileHover={{ borderColor: "#cbd5e1", backgroundColor: "#fafafa" }}
          >
            <motion.div
              animate={{ scale: isDragOver ? 1.1 : 1 }}
              transition={{ type: "spring", stiffness: 400, damping: 20 }}
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
              style={{ backgroundColor: isDragOver ? "#fef2f2" : "#f8fafc", border: "1px solid #e2e8f0" }}
            >
              <Upload size={28} style={{ color: isDragOver ? "#9b1c1c" : "#94a3b8" }} />
            </motion.div>
            <p style={{ color: "#374151", fontSize: 15, fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500, marginBottom: 6 }}>
              {isDragOver ? "松开即可上传" : "拖放图片至此，或点击上传"}
            </p>
            <p style={{ color: "#94a3b8", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}>
              支持 JPG、PNG，最多 {MAX_IMAGES} 张
            </p>
            <div className="mt-6 flex gap-3 flex-wrap justify-center">
              {["英语→中文", "日语→中文", "法语→中文", "德语→中文"].map((lang) => (
                <span key={lang} className="px-2.5 py-1 rounded-full text-xs" style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif" }}>
                  {lang}
                </span>
              ))}
            </div>
          </motion.div>

          <input ref={fileInputRef} type="file" accept="image/*" multiple className="hidden" onChange={handleFileChange} />
        </motion.div>
      </div>
    );
  }

  // ── Preview ────────────────────────────────────────────────────────────────
  if (imgState === "preview") {
    return (
      <div className="h-full flex flex-col p-6">
        <input ref={fileInputRef} type="file" accept="image/*" multiple className="hidden" onChange={handleFileChange} />

        <div className="flex items-center justify-between mb-4 flex-shrink-0">
          <div>
            <h2 style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 20, fontWeight: 600 }}>
              图片预览
            </h2>
            <p style={{ color: "#64748b", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 3 }}>
              已选 {images.length} / {MAX_IMAGES} 张 · 确认无误后开始批量转译
            </p>
          </div>
          <div className="flex gap-2">
            <motion.button whileHover={{ scale: 1.02 }} onClick={reset} className="flex items-center gap-1.5 px-3 py-2 rounded-lg" style={{ border: "1px solid #e2e8f0", color: "#64748b", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}>
              <RotateCcw size={13} />
              清空重选
            </motion.button>
            {images.length < MAX_IMAGES && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg"
                style={{ border: "1px solid #e2e8f0", backgroundColor: "#f8fafc", color: "#374151", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}
              >
                <Plus size={14} />
                添加图片
              </motion.button>
            )}
            <motion.button
              whileHover={{ scale: 1.01, boxShadow: "0 4px 16px rgba(155,28,28,0.4)" }}
              whileTap={{ scale: 0.97 }}
              onClick={startAll}
              className="flex items-center gap-2 px-5 py-2 rounded-lg text-white"
              style={{ backgroundColor: "#9b1c1c", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 13, boxShadow: "0 2px 10px rgba(155,28,28,0.3)" }}
            >
              <Languages size={15} />
              开始批量转译（{images.length} 张）
            </motion.button>
          </div>
        </div>

        <div className="flex-1 overflow-auto">
          <div className="grid grid-cols-2 gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
            {images.map((img, i) => (
              <motion.div
                key={img.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className="group relative rounded-xl overflow-hidden"
                style={{ border: "1px solid #e2e8f0", backgroundColor: "#fff", boxShadow: "0 1px 4px rgba(0,0,0,0.04)" }}
              >
                <img src={img.url} alt={img.name} className="w-full object-cover" style={{ height: 180 }} />
                <div className="p-3">
                  <p className="truncate" style={{ fontSize: 12.5, color: "#374151", fontFamily: "'Noto Sans SC', sans-serif" }}>{img.name}</p>
                </div>
                <button
                  onClick={() => removeImage(img.id)}
                  className="absolute top-2 right-2 w-6 h-6 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
                >
                  <X size={12} style={{ color: "#fff" }} />
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ── Processing ─────────────────────────────────────────────────────────────
  if (imgState === "processing") {
    return (
      <div className="h-full flex flex-col p-6">
        <div className="mb-5 flex-shrink-0">
          <h2 style={{ color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 20, fontWeight: 600 }}>正在批量转译</h2>
          <p style={{ color: "#64748b", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif", marginTop: 3 }}>AI 引擎正在处理 {images.length} 张图片……</p>
        </div>

        <div className="flex-1 overflow-auto">
          <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))" }}>
            {images.map((img, i) => (
              <motion.div
                key={img.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                className="rounded-xl overflow-hidden"
                style={{ border: "1px solid #e2e8f0", backgroundColor: "#fff", boxShadow: "0 1px 4px rgba(0,0,0,0.04)" }}
              >
                <div className="relative">
                  <img src={img.url} alt={img.name} className="w-full object-cover" style={{ height: 160 }} />
                  {img.status === "translating" && (
                    <div className="absolute inset-0 flex items-center justify-center" style={{ backgroundColor: "rgba(15,23,42,0.5)" }}>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
                      >
                        <Loader2 size={32} style={{ color: "#fff" }} />
                      </motion.div>
                    </div>
                  )}
                  {img.status === "done" && (
                    <div className="absolute inset-0 flex items-center justify-center" style={{ backgroundColor: "rgba(22,163,74,0.25)" }}>
                      <CheckCircle2 size={36} style={{ color: "#fff" }} />
                    </div>
                  )}
                </div>

                <div className="p-3">
                  <div className="flex items-center justify-between mb-2">
                    <p className="truncate flex-1 mr-2" style={{ fontSize: 12.5, color: "#374151", fontFamily: "'Noto Sans SC', sans-serif" }}>{img.name}</p>
                    {img.status === "pending" && (
                      <span className="flex items-center gap-1 text-xs" style={{ color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 11, flexShrink: 0 }}>
                        <Clock size={10} />排队中
                      </span>
                    )}
                    {img.status === "translating" && (
                      <span className="flex items-center gap-1 text-xs" style={{ color: "#d97706", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 11, flexShrink: 0 }}>
                        <Loader2 size={10} />处理中
                      </span>
                    )}
                    {img.status === "done" && (
                      <span className="flex items-center gap-1 text-xs" style={{ color: "#16a34a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 11, flexShrink: 0 }}>
                        <CheckCircle2 size={10} />完成
                      </span>
                    )}
                  </div>

                  <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: "#f1f5f9" }}>
                    <motion.div
                      className="h-full rounded-full"
                      style={{ backgroundColor: img.status === "done" ? "#16a34a" : "#9b1c1c" }}
                      animate={{ width: `${img.progress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                  <div className="text-right mt-1">
                    <span style={{ fontSize: 11, color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif" }}>
                      {Math.round(img.progress)}%
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ── Results ─────────────────────────────────────────────────────────────────
  return (
    <div className="h-full flex overflow-hidden">
      {/* Left: thumbnail list */}
      <div
        className="flex-shrink-0 flex flex-col overflow-hidden"
        style={{ width: 200, borderRight: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}
      >
        <div className="px-3 py-3 flex-shrink-0" style={{ borderBottom: "1px solid #e2e8f0" }}>
          <div style={{ fontSize: 12.5, color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 500 }}>
            转译结果 · {images.length} 张
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2" style={{ scrollbarWidth: "none" }}>
          {images.map((img) => (
            <motion.button
              key={img.id}
              onClick={() => { setSelectedId(img.id); setSliderPos(50); }}
              className="w-full rounded-xl overflow-hidden mb-2 text-left"
              style={{
                border: selectedId === img.id ? "2px solid #9b1c1c" : "1px solid #e2e8f0",
                backgroundColor: "#fff",
                boxShadow: selectedId === img.id ? "0 2px 8px rgba(155,28,28,0.15)" : "none",
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ duration: 0.1 }}
            >
              <img src={img.url} alt={img.name} className="w-full object-cover" style={{ height: 90 }} />
              <div className="p-2">
                <p className="truncate" style={{ fontSize: 11, color: "#374151", fontFamily: "'Noto Sans SC', sans-serif", marginBottom: 4 }}>
                  {img.name}
                </p>
                <div className="flex items-center justify-between gap-1">
                  <span
                    className="flex items-center gap-0.5 text-xs"
                    style={{ color: "#16a34a", fontFamily: "'Noto Sans SC', sans-serif", fontSize: 10.5, flexShrink: 0 }}
                  >
                    <CheckCircle2 size={9} />已完成
                  </span>
                  <motion.button
                    whileHover={{ color: "#9b1c1c" }}
                    onClick={(e) => { e.stopPropagation(); regenerate(img.id); }}
                    className="flex items-center gap-0.5"
                    style={{ color: "#94a3b8", fontSize: 10.5, fontFamily: "'Noto Sans SC', sans-serif" }}
                    title="重新生成"
                  >
                    <RefreshCw size={9} />
                    重新生成
                  </motion.button>
                </div>
              </div>
            </motion.button>
          ))}

          {/* Reset button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            onClick={reset}
            className="w-full py-2 rounded-xl mt-1 flex items-center justify-center gap-1.5"
            style={{ border: "1px dashed #e2e8f0", color: "#94a3b8", fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif" }}
          >
            <Plus size={12} />
            新建任务
          </motion.button>
        </div>
      </div>

      {/* Right: comparison slider */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedImage ? (
          <>
            {/* Top bar */}
            <div
              className="flex-shrink-0 flex items-center justify-between px-5 py-3"
              style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#fff" }}
            >
              <div className="flex items-center gap-3">
                <CheckCircle2 size={16} style={{ color: "#16a34a" }} />
                <div>
                  <div style={{ fontSize: 14, fontFamily: "'Noto Sans SC', sans-serif", color: "#0f172a", fontWeight: 600 }}>
                    {selectedImage.name}
                  </div>
                  <div style={{ fontSize: 11.5, color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif" }}>
                    左右拖拽中线对比原图与译图
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  onClick={() => regenerate(selectedImage.id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
                  style={{ border: "1px solid #e2e8f0", color: "#64748b", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}
                >
                  <RefreshCw size={13} />
                  重新生成
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white"
                  style={{ backgroundColor: "#9b1c1c", fontSize: 13, fontFamily: "'Noto Sans SC', sans-serif" }}
                >
                  <Download size={13} />
                  下载译图
                </motion.button>
              </div>
            </div>

            {/* Before/After labels */}
            <div className="flex justify-between px-5 py-2 flex-shrink-0">
              <span className="px-2 py-0.5 rounded text-xs" style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", color: "#64748b", fontFamily: "'Noto Sans SC', sans-serif" }}>
                原图
              </span>
              <span className="px-2 py-0.5 rounded text-xs" style={{ backgroundColor: "#fef2f2", border: "1px solid #fecaca", color: "#9b1c1c", fontFamily: "'Noto Sans SC', sans-serif" }}>
                AI 译图
              </span>
            </div>

            {/* Comparison slider */}
            <div className="flex-1 overflow-hidden px-5 pb-4">
              <div
                ref={sliderRef}
                className="relative overflow-hidden rounded-xl h-full select-none"
                style={{
                  border: "1px solid #e2e8f0",
                  cursor: isDragging ? "col-resize" : "crosshair",
                  boxShadow: "0 2px 20px rgba(0,0,0,0.06)",
                }}
              >
                {/* Original */}
                <img src={selectedImage.url} alt="original" className="absolute inset-0 w-full h-full object-contain" draggable={false} style={{ backgroundColor: "#f8fafc" }} />

                {/* Translated (clipped) */}
                <div className="absolute inset-0 overflow-hidden" style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}>
                  <img
                    src={selectedImage.url}
                    alt="translated"
                    className="absolute inset-0 w-full h-full object-contain"
                    draggable={false}
                    style={{
                      backgroundColor: "#f0f9ff",
                      filter: "sepia(0.15) hue-rotate(15deg) saturate(1.15) brightness(1.03)",
                    }}
                  />
                  <div className="absolute bottom-3 right-3 px-2 py-1 rounded-md text-xs" style={{ backgroundColor: "rgba(155,28,28,0.85)", color: "#fff", fontFamily: "'Noto Sans SC', sans-serif" }}>
                    AI 译图
                  </div>
                </div>

                {/* Divider line + handle */}
                <div
                  className="absolute inset-y-0 flex items-center justify-center z-10"
                  style={{ left: `${sliderPos}%`, transform: "translateX(-50%)" }}
                >
                  <div className="absolute inset-y-0 w-0.5" style={{ backgroundColor: "#fff", boxShadow: "0 0 8px rgba(0,0,0,0.3)" }} />
                  <motion.div
                    onMouseDown={handleSliderMouseDown}
                    whileHover={{ scale: 1.12 }}
                    className="relative z-10 flex items-center justify-center rounded-full cursor-col-resize"
                    style={{ width: 36, height: 36, backgroundColor: "#fff", boxShadow: "0 2px 12px rgba(0,0,0,0.2)", border: "2px solid #e2e8f0" }}
                  >
                    <div className="flex gap-0.5">
                      {[0, 1, 2].map((n) => (
                        <div key={n} className="w-0.5 h-3 rounded-full" style={{ backgroundColor: "#94a3b8" }} />
                      ))}
                    </div>
                  </motion.div>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="flex-shrink-0 px-5 pb-4 flex gap-3">
              {[
                { label: "识别文字块", value: "23", unit: "处" },
                { label: "翻译语言", value: "英→中", unit: "" },
                { label: "处理时长", value: "8.4", unit: "秒" },
                { label: "置信度", value: "97.3", unit: "%" },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="flex-1 px-3 py-2 rounded-lg text-center"
                  style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0" }}
                >
                  <div style={{ fontSize: 18, color: "#0f172a", fontFamily: "'Noto Sans SC', sans-serif", fontWeight: 600 }}>
                    {stat.value}
                    <span style={{ fontSize: 12, color: "#94a3b8", fontWeight: 400 }}>{stat.unit}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "#94a3b8", fontFamily: "'Noto Sans SC', sans-serif", marginTop: 2 }}>
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <ImageIcon size={40} style={{ color: "#e2e8f0", marginBottom: 12 }} />
              <p style={{ color: "#94a3b8", fontSize: 14, fontFamily: "'Noto Sans SC', sans-serif" }}>
                从左侧选择一张图片预览
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
