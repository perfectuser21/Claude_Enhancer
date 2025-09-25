#!/usr/bin/env python3
"""
Claude Enhancer 深度诊断工具
找出系统所有问题并生成优化方案
"""

import os
import json
import yaml
import subprocess
from pathlib import Path
from collections import defaultdict
import time


class ClaudeEnhancerDiagnostic:
    def __init__(self):
        self.base_path = Path(".claude")
        self.issues = defaultdict(list)
        self.stats = {}

    def diagnose_all(self):
        """运行所有诊断"""
        print("🔍 Claude Enhancer 深度诊断开始...\n")

        self.check_file_structure()
        self.check_configuration()
        self.check_hooks()
        self.check_performance()
        self.check_naming_consistency()
        self.check_documentation()

        self.generate_report()

    def check_file_structure(self):
        """检查文件结构问题"""
        print("📁 检查文件结构...")

        # 统计文件
        total_files = 0
        script_files = 0
        backup_files = 0
        deprecated_files = 0

        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                total_files += 1
                if file.endswith((".sh", ".py")):
                    script_files += 1
                if "backup" in file or ".bak" in file:
                    backup_files += 1
                    self.issues["冗余文件"].append(f"{root}/{file}")
                if "deprecated" in file or "old" in file:
                    deprecated_files += 1
                    self.issues["废弃文件"].append(f"{root}/{file}")

        self.stats["总文件数"] = total_files
        self.stats["脚本文件数"] = script_files
        self.stats["备份文件数"] = backup_files
        self.stats["废弃文件数"] = deprecated_files

        # 检查目录深度
        max_depth = 0
        for root, dirs, files in os.walk(self.base_path):
            depth = len(Path(root).relative_to(self.base_path).parts)
            max_depth = max(max_depth, depth)

        if max_depth > 3:
            self.issues["结构问题"].append(f"目录嵌套过深: {max_depth}层")

        print(f"  ✓ 发现 {total_files} 个文件，{backup_files} 个备份文件，{deprecated_files} 个废弃文件")

    def check_configuration(self):
        """检查配置一致性"""
        print("⚙️ 检查配置系统...")

        config_files = []

        # 查找所有配置文件
        for pattern in ["*.json", "*.yaml", "*.yml"]:
            config_files.extend(self.base_path.rglob(pattern))

        self.stats["配置文件数"] = len(config_files)

        # 检查配置冲突
        configs = {}
        for config_file in config_files:
            try:
                if config_file.suffix == ".json":
                    with open(config_file) as f:
                        configs[str(config_file)] = json.load(f)
                elif config_file.suffix in [".yaml", ".yml"]:
                    with open(config_file) as f:
                        configs[str(config_file)] = yaml.safe_load(f)
            except Exception as e:
                self.issues["配置错误"].append(f"{config_file}: {str(e)}")

        # 检查重复键
        all_keys = defaultdict(list)
        for file_path, config in configs.items():
            if isinstance(config, dict):
                for key in config.keys():
                    all_keys[key].append(file_path)

        for key, files in all_keys.items():
            if len(files) > 2:
                self.issues["配置冲突"].append(f"键'{key}'在{len(files)}个文件中重复")

        print(f"  ✓ 发现 {len(config_files)} 个配置文件")

    def check_hooks(self):
        """检查Hook系统"""
        print("🪝 检查Hook系统...")

        hooks_dir = self.base_path / "hooks"
        if hooks_dir.exists():
            hook_scripts = list(hooks_dir.glob("*.sh")) + list(hooks_dir.glob("*.py"))
            self.stats["Hook脚本数"] = len(hook_scripts)

            # 检查执行权限
            for script in hook_scripts:
                if not os.access(script, os.X_OK):
                    self.issues["权限问题"].append(f"{script} 缺少执行权限")

            # 检查危险脚本
            dangerous_patterns = ["hijacker", "destroyer", "interceptor"]
            for script in hook_scripts:
                for pattern in dangerous_patterns:
                    if pattern in script.name.lower():
                        self.issues["安全问题"].append(f"发现危险Hook: {script.name}")

            print(f"  ✓ 发现 {len(hook_scripts)} 个Hook脚本")

    def check_performance(self):
        """检查性能问题"""
        print("⚡ 检查性能...")

        # 测试脚本执行时间
        test_scripts = [
            ".claude/scripts/cleanup.sh",
            ".claude/scripts/ultra_optimized_cleanup.sh",
            ".claude/scripts/performance_optimized_cleanup.sh",
        ]

        for script in test_scripts:
            if os.path.exists(script):
                try:
                    start = time.time()
                    result = subprocess.run(
                        ["bash", script, "--dry-run"],
                        capture_output=True,
                        timeout=2,
                        text=True,
                    )
                    elapsed = time.time() - start

                    if elapsed > 0.5:
                        self.issues["性能问题"].append(f"{script} 执行时间过长: {elapsed:.2f}秒")

                except subprocess.TimeoutExpired:
                    self.issues["性能问题"].append(f"{script} 执行超时")
                except Exception as e:
                    self.issues["脚本错误"].append(f"{script}: {str(e)}")

        print("  ✓ 性能检查完成")

    def check_naming_consistency(self):
        """检查命名一致性"""
        print("📝 检查命名一致性...")

        # 检查品牌名称
        # 统一后的品牌检查
        brand_names = ["Claude Enhancer"]  # 已统一为 Claude Enhancer
        legacy_brands = ["Claude Enhancer", "claude-enhancer", "claude enhancer"]  # 遗留品牌检查
        brand_count = defaultdict(int)

        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith((".md", ".sh", ".py", ".yaml", ".json")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()
                            for brand in brand_names:
                                if brand in content:
                                    brand_count[brand] += content.count(brand)
                    except:
                        pass

        if len([k for k, v in brand_count.items() if v > 0]) > 1:
            self.issues["命名不一致"].append(f"发现多个品牌名称: {dict(brand_count)}")

        print(f"  ✓ 品牌名称统计: {dict(brand_count)}")

    def check_documentation(self):
        """检查文档问题"""
        print("📚 检查文档...")

        md_files = list(Path(".").rglob("*.md"))
        self.stats["文档文件数"] = len(md_files)

        # 检查文档大小
        large_docs = []
        for md_file in md_files:
            size = os.path.getsize(md_file)
            if size > 50000:  # 50KB
                large_docs.append((md_file, size))
                self.issues["文档问题"].append(f"{md_file} 过大: {size/1024:.1f}KB")

        # 检查重复文档
        doc_names = defaultdict(list)
        for md_file in md_files:
            doc_names[md_file.name].append(str(md_file))

        for name, paths in doc_names.items():
            if len(paths) > 1:
                self.issues["文档重复"].append(f"{name} 在多处重复: {paths}")

        print(f"  ✓ 发现 {len(md_files)} 个文档文件")

    def generate_report(self):
        """生成诊断报告"""
        print("\n" + "=" * 60)
        print("📊 Claude Enhancer 诊断报告")
        print("=" * 60)

        # 统计信息
        print("\n📈 系统统计:")
        for key, value in self.stats.items():
            print(f"  • {key}: {value}")

        # 问题列表
        print("\n⚠️ 发现的问题:")

        severity_map = {
            "安全问题": "🔴",
            "性能问题": "🟠",
            "配置冲突": "🟡",
            "配置错误": "🟡",
            "命名不一致": "🟡",
            "结构问题": "🟢",
            "权限问题": "🟢",
            "文档问题": "🔵",
            "文档重复": "🔵",
            "冗余文件": "⚪",
            "废弃文件": "⚪",
            "脚本错误": "🟡",
        }

        total_issues = 0
        for category, issues in self.issues.items():
            if issues:
                icon = severity_map.get(category, "❓")
                print(f"\n{icon} {category} ({len(issues)}个):")
                for issue in issues[:3]:  # 只显示前3个
                    print(f"    - {issue}")
                if len(issues) > 3:
                    print(f"    ... 还有 {len(issues)-3} 个问题")
                total_issues += len(issues)

        # 优化建议
        print("\n💡 优化建议:")

        suggestions = []

        if self.stats.get("备份文件数", 0) > 10:
            suggestions.append("清理备份文件，使用版本控制代替")

        if self.stats.get("配置文件数", 0) > 5:
            suggestions.append("整合配置文件，使用单一配置源")

        if "性能问题" in self.issues:
            suggestions.append("优化脚本性能，使用并行处理")

        if "命名不一致" in self.issues:
            suggestions.append("统一品牌名称，保持一致性")

        if self.stats.get("文档文件数", 0) > 50:
            suggestions.append("精简文档，删除重复和过时内容")

        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")

        # 严重程度评估
        print("\n🎯 整体评估:")

        if total_issues == 0:
            print("  ✅ 系统状态良好")
        elif total_issues < 10:
            print(f"  🟢 发现 {total_issues} 个小问题，建议优化")
        elif total_issues < 30:
            print(f"  🟡 发现 {total_issues} 个问题，需要清理和优化")
        else:
            print(f"  🔴 发现 {total_issues} 个问题，需要重大重构")

        # 保存报告
        report_path = "CLAUDE_ENHANCER_DIAGNOSTIC_REPORT.md"
        self.save_report(report_path)
        print(f"\n📝 详细报告已保存到: {report_path}")

    def save_report(self, filepath):
        """保存Markdown格式报告"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Claude Enhancer 诊断报告\n\n")
            f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## 系统统计\n\n")
            for key, value in self.stats.items():
                f.write(f"- {key}: {value}\n")

            f.write("\n## 发现的问题\n\n")
            for category, issues in self.issues.items():
                if issues:
                    f.write(f"### {category}\n\n")
                    for issue in issues:
                        f.write(f"- {issue}\n")
                    f.write("\n")


if __name__ == "__main__":
    diagnostic = ClaudeEnhancerDiagnostic()
    diagnostic.diagnose_all()
