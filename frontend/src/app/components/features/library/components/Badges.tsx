import { CheckCircle2, Clock, Circle } from "lucide-react";
import { Doc } from "../../../../types";

// 状态徽章组件
export function StatusBadge({ status }: { status: Doc["aiStatus"] }) {
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

// 标签徽章组件
export function TagBadge({ label }: { label: string }) {
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-xs mr-1"
      style={{ backgroundColor: "#f1f5f9", color: "#64748b", border: "1px solid #e2e8f0", fontSize: 11 }}
    >
      {label}
    </span>
  );
}
