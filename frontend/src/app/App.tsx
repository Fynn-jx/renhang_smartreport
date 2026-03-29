import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Sidebar } from "./components/layout/Sidebar";
import { LibraryModule } from "./components/features/library";
import { DocLibraryModule } from "./components/features/doc-library";
import { ResearchModule } from "./components/features/research";
import { ImageModule } from "./components/features/image";
import { DataSourcePanel } from "./components/layout/DataSourcePanel";
import { HistoryPanel } from "./components/HistoryPanel";
import pbocLogo from "../assets/9d80b1a068fa275c0785a292f5a33bc94ff0f912.png";
import type { ActiveModule } from "./components/layout/Sidebar";

type ViewState =
  | { type: "module"; module: ActiveModule }
  | { type: "datasource"; sourceId: string }
  | { type: "history" };

export default function App() {
  const [activeModule, setActiveModule] = useState<ActiveModule>("library");
  const [collapsed, setCollapsed] = useState(false);
  const [viewState, setViewState] = useState<ViewState>({ type: "module", module: "library" });

  const handleModuleChange = (module: ActiveModule) => {
    setActiveModule(module);
    setViewState({ type: "module", module });
  };

  const handleDataSourceClick = (sourceId: string) => {
    if (sourceId === "dataSource") {
      setViewState((prev) =>
        prev.type === "datasource" && prev.sourceId === "dataSource"
          ? { type: "module", module: activeModule }
          : { type: "datasource", sourceId: "dataSource" }
      );
    } else {
      setViewState({ type: "datasource", sourceId });
    }
  };

  const handleHistoryClick = () => {
    setViewState((prev) =>
      prev.type === "history"
        ? { type: "module", module: activeModule }
        : { type: "history" }
    );
  };

  const handleBack = () => {
    setViewState({ type: "module", module: activeModule });
  };

  const renderContent = () => {
    if (viewState.type === "history") {
      return <HistoryPanel onBack={handleBack} />;
    }
    if (viewState.type === "datasource") {
      return <DataSourcePanel sourceId={viewState.sourceId} onBack={handleBack} />;
    }
    switch (viewState.module) {
      case "library":
        return <LibraryModule />;
      case "doc-library":
        return <DocLibraryModule />;
      case "research":
        return <ResearchModule />;
      case "image":
        return <ImageModule />;
      default:
        return <LibraryModule />;
    }
  };

  return (
    <div
      className="flex h-screen w-screen overflow-hidden"
      style={{ backgroundColor: "#f8fafc", fontFamily: "'Noto Sans SC', sans-serif" }}
    >
      {/* Sidebar */}
      <Sidebar
        activeModule={activeModule}
        onModuleChange={handleModuleChange}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed((c) => !c)}
        onDataSourceClick={handleDataSourceClick}
        activeDataSource={viewState.type === "datasource" ? viewState.sourceId : null}
        onHistoryClick={handleHistoryClick}
      />

      {/* Main Content */}
      <main className="flex-1 relative overflow-hidden">
        {/* Global Watermark */}
        <div
          className="absolute inset-0 flex items-center justify-center pointer-events-none select-none z-0"
          aria-hidden
        >
          <img
            src={pbocLogo}
            alt=""
            draggable={false}
            style={{ width: 520, height: 520, objectFit: "contain", opacity: 0.038, userSelect: "none" }}
          />
        </div>

        {/* Module Area */}
        <div className="relative z-10 h-full overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={viewState.type === "module" ? viewState.module : viewState.type === "datasource" ? `ds-${viewState.sourceId}` : "history"}
              className="absolute inset-0"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2, ease: "easeInOut" }}
            >
              {renderContent()}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
