import { motion, AnimatePresence } from "motion/react";
import {
  BookOpen,
  Globe2,
  ImageIcon,
  ChevronRight,
  Landmark,
  ChevronsLeft,
  ChevronsRight,
  FileText,
} from "lucide-react";
import pbocLogo from "../../../assets/9d80b1a068fa275c0785a292f5a33bc94ff0f912.png";

export type ActiveModule = "library" | "doc-library" | "research" | "image";

interface SidebarProps {
  activeModule: ActiveModule;
  onModuleChange: (module: ActiveModule) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  onDataSourceClick: (sourceId: string) => void;
  activeDataSource: string | null;
  onHistoryClick: () => void;
}

const navItems = [
  { id: "library" as ActiveModule, label: "前沿报告库", icon: BookOpen },
  { id: "doc-library" as ActiveModule, label: "公文库", icon: FileText },
  { id: "research" as ActiveModule, label: "国别深度研究", icon: Globe2 },
  { id: "image" as ActiveModule, label: "图片转译", icon: ImageIcon },
];

export function Sidebar({
  activeModule,
  onModuleChange,
  collapsed,
  onToggleCollapse,
  onDataSourceClick,
  activeDataSource,
  onHistoryClick,
}: SidebarProps) {
  return (
    <motion.div
      animate={{ width: collapsed ? 60 : 250 }}
      transition={{ type: "spring", stiffness: 320, damping: 32 }}
      className="flex flex-col h-full overflow-hidden select-none flex-shrink-0"
      style={{
        backgroundColor: "#0f172a",
        borderRight: "1px solid rgba(255,255,255,0.06)",
        minWidth: collapsed ? 60 : 250,
      }}
    >
      {/* Branding */}
      <div
        className="flex items-center gap-3 px-3 py-4 flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.07)", minHeight: 64 }}
      >
        <div
          className="relative flex items-center justify-center rounded-md overflow-hidden flex-shrink-0"
          style={{ width: 36, height: 36, backgroundColor: "rgba(255,255,255,0.06)" }}
        >
          <img src={pbocLogo} alt="央行行徽" className="w-7 h-7 object-contain" />
        </div>

        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.18 }}
              className="flex flex-col leading-none overflow-hidden whitespace-nowrap"
            >
              <span
                className="text-xs tracking-wider"
                style={{ color: "rgba(255,255,255,0.4)", fontFamily: "'Noto Sans SC', sans-serif", marginBottom: 2 }}
              >
                中国人民银行
              </span>
              <span
                style={{
                  color: "rgba(255,255,255,0.92)",
                  fontFamily: "'Noto Sans SC', sans-serif",
                  fontSize: 15,
                  fontWeight: 600,
                  letterSpacing: "0.05em",
                }}
              >
                人行智汇
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Toggle Button - always visible at top */}
      <div
        className="flex-shrink-0 px-3 py-2"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
      >
        <motion.button
          onClick={onToggleCollapse}
          className="w-full flex items-center justify-center rounded-md"
          style={{ height: 28, backgroundColor: "rgba(255,255,255,0.05)" }}
          whileHover={{ backgroundColor: "rgba(255,255,255,0.12)" }}
          transition={{ duration: 0.12 }}
          title={collapsed ? "展开侧边栏" : "收起侧边栏"}
        >
          {collapsed ? (
            <ChevronsRight size={14} style={{ color: "rgba(255,255,255,0.45)" }} />
          ) : (
            <ChevronsLeft size={14} style={{ color: "rgba(255,255,255,0.45)" }} />
          )}
        </motion.button>
      </div>

      {/* Navigation */}
      <div className="px-2 pt-4 pb-2 flex-shrink-0">
        {!collapsed && (
          <div
            className="px-2 pb-2 text-xs tracking-widest uppercase whitespace-nowrap"
            style={{ color: "rgba(255,255,255,0.25)", fontFamily: "'Noto Sans SC', sans-serif" }}
          >
            核心模块
          </div>
        )}
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = activeModule === item.id && !activeDataSource;
          return (
            <motion.button
              key={item.id}
              onClick={() => onModuleChange(item.id)}
              className="w-full flex items-center mb-0.5 rounded-lg relative"
              style={{
                backgroundColor: active ? "rgba(185,28,28,0.18)" : "transparent",
                padding: collapsed ? "10px 0" : "10px 12px",
                justifyContent: collapsed ? "center" : "flex-start",
                gap: collapsed ? 0 : 12,
              }}
              whileHover={{ backgroundColor: active ? "rgba(185,28,28,0.2)" : "rgba(255,255,255,0.06)" }}
              transition={{ duration: 0.12 }}
              title={collapsed ? item.label : undefined}
            >
              {active && (
                <motion.div
                  layoutId="activeIndicator"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full"
                  style={{ backgroundColor: "#ef4444" }}
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
              <Icon
                size={16}
                strokeWidth={active ? 2 : 1.5}
                style={{ color: active ? "#f87171" : "rgba(255,255,255,0.4)", flexShrink: 0 }}
              />
              <AnimatePresence>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    style={{
                      fontWeight: active ? 500 : 400,
                      color: active ? "#fecaca" : "rgba(255,255,255,0.6)",
                      fontFamily: "'Noto Sans SC', sans-serif",
                      fontSize: 13.5,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>
          );
        })}
      </div>

      {/* Divider */}
      <div style={{ height: 1, backgroundColor: "rgba(255,255,255,0.06)", margin: "4px 10px", flexShrink: 0 }} />

      {/* Data Source - Clickable to show panel */}
      <div className="px-2 pt-2 flex-shrink-0">
        {!collapsed && (
          <motion.button
            onClick={() => onDataSourceClick("dataSource")}
            className="w-full flex items-center justify-between px-2 py-2 rounded-lg"
            style={{
              backgroundColor: activeDataSource === "dataSource" ? "rgba(255,255,255,0.1)" : "transparent",
            }}
            whileHover={{ backgroundColor: "rgba(255,255,255,0.06)" }}
            transition={{ duration: 0.12 }}
          >
            <div
              className="text-xs tracking-widest uppercase whitespace-nowrap"
              style={{ color: "rgba(255,255,255,0.25)", fontFamily: "'Noto Sans SC', sans-serif" }}
            >
              数据源
            </div>
            <ChevronRight size={12} style={{ color: "rgba(255,255,255,0.3)" }} />
          </motion.button>
        )}
      </div>

      {/* Divider */}
      <div style={{ height: 1, backgroundColor: "rgba(255,255,255,0.06)", margin: "4px 10px", flexShrink: 0 }} />

      {/* History - Clickable to show panel */}
      <div className="px-2 pt-2 flex-shrink-0">
        {!collapsed && (
          <motion.button
            onClick={onHistoryClick}
            className="w-full flex items-center justify-between px-2 py-2 rounded-lg"
            whileHover={{ backgroundColor: "rgba(255,255,255,0.06)" }}
            transition={{ duration: 0.12 }}
          >
            <div
              className="text-xs tracking-widest uppercase whitespace-nowrap"
              style={{ color: "rgba(255,255,255,0.25)", fontFamily: "'Noto Sans SC', sans-serif" }}
            >
              历史记录
            </div>
            <ChevronRight size={12} style={{ color: "rgba(255,255,255,0.3)" }} />
          </motion.button>
        )}
      </div>

      {!collapsed && <div style={{ flex: collapsed ? 0 : 1 }} />}

      {/* Footer */}
      <div
        className="flex-shrink-0 flex items-center gap-2 py-3"
        style={{
          borderTop: "1px solid rgba(255,255,255,0.06)",
          padding: collapsed ? "12px 0" : "12px 16px",
          justifyContent: collapsed ? "center" : "flex-start",
        }}
      >
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: "rgba(185,28,28,0.3)" }}
        >
          <Landmark size={13} style={{ color: "#f87171" }} />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <div style={{ color: "rgba(255,255,255,0.65)", fontSize: 12, fontFamily: "'Noto Sans SC', sans-serif" }}>
                研究员·小明
              </div>
              <div style={{ color: "rgba(255,255,255,0.25)", fontSize: 10, fontFamily: "'Noto Sans SC', sans-serif" }}>
                国际司 · 高级研究员
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
