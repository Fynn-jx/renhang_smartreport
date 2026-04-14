"""
公文写作调试工具
记录每个阶段的输入输出，用于问题诊断和提示词优化
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger


class WorkflowDebugLogger:
    """工作流调试日志记录器"""

    def __init__(self, enabled: bool = True, output_dir: str = "./storage/debug_outputs"):
        """
        初始化调试日志记录器

        Args:
            enabled: 是否启用调试模式
            output_dir: 输出目录
        """
        self.enabled = enabled
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 当前会话信息
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)

        # 阶段记录
        self.stages = []

        logger.info(f"[调试] 调试模式: {'启用' if enabled else '禁用'}")
        logger.info(f"[调试] 输出目录: {self.session_dir}")

    def log_stage(self, stage_name: str, input_text: str, output_text: str,
                 model: str, prompt: str = None, metadata: Dict[str, Any] = None):
        """
        记录一个阶段的输入输出

        Args:
            stage_name: 阶段名称
            input_text: 输入文本
            output_text: 输出文本
            model: 使用的模型
            prompt: 提示词（可选）
            metadata: 额外的元数据（可选）
        """
        if not self.enabled:
            return

        try:
            # 保存详细记录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 毫秒精度
            filename = f"{timestamp}_{stage_name}.md"
            filepath = self.session_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {stage_name}\n\n")
                f.write(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n\n")
                f.write(f"**模型**: {model}\n\n")

                # 元数据
                if metadata:
                    f.write("## 元数据\n\n")
                    for key, value in metadata.items():
                        f.write(f"- **{key}**: {value}\n")
                    f.write("\n")

                # 统计信息
                f.write("## 统计信息\n\n")
                f.write(f"- 输入长度: {len(input_text):,} 字符\n")
                f.write(f"- 输出长度: {len(output_text):,} 字符\n")
                f.write(f"- 压缩率: {((1 - len(output_text) / len(input_text)) * 100) if input_text else 0:.1f}%\n\n")

                # 输入
                f.write("## 输入\n\n")
                f.write("---\n\n")
                self._write_content(f, input_text, max_chars=8000)

                # 提示词
                if prompt:
                    f.write("\n\n## 提示词\n\n")
                    f.write("---\n\n")
                    self._write_content(f, prompt, max_chars=3000, label="提示词")

                # 输出
                f.write("\n\n## 输出\n\n")
                f.write("---\n\n")
                self._write_content(f, output_text, max_chars=10000)

            # 记录到内存
            stage_record = {
                "name": stage_name,
                "timestamp": datetime.now().isoformat(),
                "model": model,
                "input_length": len(input_text),
                "output_length": len(output_text),
                "file": str(filepath)
            }
            self.stages.append(stage_record)

            logger.info(f"[调试] 已保存阶段: {stage_name} -> {filepath.name}")

        except Exception as e:
            logger.error(f"[调试] 保存阶段失败: {stage_name}, 错误: {e}")

    def _write_content(self, f, content: str, max_chars: int = 10000, label: str = "内容"):
        """写入内容（自动截断）"""
        if len(content) <= max_chars:
            f.write(content)
        else:
            f.write(content[:max_chars])
            f.write(f"\n\n```\n")
            f.write(f"... 省略 {len(content) - max_chars:,} 字符 ...\n")
            f.write(f"```\n")

    def save_summary(self):
        """保存会话总结"""
        if not self.enabled or not self.stages:
            return

        try:
            summary_path = self.session_dir / "00_会话总结.md"

            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("# 公文写作会话总结\n\n")
                f.write(f"**会话ID**: {self.session_id}\n\n")
                f.write(f"**开始时间**: {self.stages[0]['timestamp'] if self.stages else 'N/A'}\n\n")
                f.write(f"**结束时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**总阶段数**: {len(self.stages)}\n\n")

                f.write("## 阶段概览\n\n")
                f.write("| 阶段 | 模型 | 输入长度 | 输出长度 | 文件 |\n")
                f.write("|------|------|----------|----------|------|\n")

                for stage in self.stages:
                    f.write(f"| {stage['name']} | {stage['model']} | ")
                    f.write(f"{stage['input_length']:,} | {stage['output_length']:,} | ")
                    f.write(f"[{Path(stage['file']).name}]({Path(stage['file']).name}) |\n")

                f.write("\n## 快速分析\n\n")

                # 计算总长度变化
                total_input = sum(s['input_length'] for s in self.stages)
                total_output = self.stages[-1]['output_length'] if self.stages else 0
                compression = ((1 - total_output / total_input) * 100) if total_input else 0

                f.write(f"- **总输入长度**: {total_input:,} 字符\n")
                f.write(f"- **最终输出长度**: {total_output:,} 字符\n")
                f.write(f"- **总体压缩率**: {compression:.1f}%\n\n")

                # 问题检测
                f.write("## 潜在问题检测\n\n")

                issues = []

                # 检测输出异常膨胀
                for stage in self.stages:
                    if stage['output_length'] > stage['input_length'] * 1.5:
                        issues.append(f"⚠️ **{stage['name']}**: 输出异常膨胀 "
                                   f"({stage['input_length']:,} → {stage['output_length']:,})")

                # 检测输出异常收缩
                for stage in self.stages:
                    if stage['output_length'] < stage['input_length'] * 0.3:
                        issues.append(f"⚠️ **{stage['name']}**: 输出异常收缩 "
                                   f"({stage['input_length']:,} → {stage['output_length']:,})")

                # 检测空输出
                for stage in self.stages:
                    if stage['output_length'] < 100:
                        issues.append(f"❌ **{stage['name']}**: 输出过短 ({stage['output_length']} 字符)")

                if issues:
                    for issue in issues:
                        f.write(f"{issue}\n\n")
                else:
                    f.write("✅ 未检测到明显问题\n\n")

                f.write("## 文件列表\n\n")
                f.write("按时间顺序查看每个阶段的详细输出：\n\n")
                for i, stage in enumerate(self.stages, 1):
                    f.write(f"{i}. [{stage['name']}]({Path(stage['file']).name})\n")

            logger.info(f"[调试] 已保存会话总结: {summary_path}")

            # 同时保存JSON格式（便于程序分析）
            json_path = self.session_dir / "00_会话总结.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "session_id": self.session_id,
                    "stages": self.stages,
                    "statistics": {
                        "total_stages": len(self.stages),
                        "total_input_length": total_input,
                        "final_output_length": total_output,
                        "compression_rate": compression
                    }
                }, f, ensure_ascii=False, indent=2)

            logger.info(f"[调试] 已保存JSON总结: {json_path}")

        except Exception as e:
            logger.error(f"[调试] 保存总结失败: {e}")

    def get_session_path(self) -> Path:
        """获取当前会话目录路径"""
        return self.session_dir


# 全局调试日志实例
_debug_logger: Optional[WorkflowDebugLogger] = None


def get_debug_logger() -> WorkflowDebugLogger:
    """获取全局调试日志实例"""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = WorkflowDebugLogger(enabled=True)
    return _debug_logger


def reset_debug_logger():
    """重置调试日志实例"""
    global _debug_logger
    _debug_logger = None
