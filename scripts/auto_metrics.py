#!/usr/bin/env python3
"""
Auto-Metrics: Automatically collect real metrics from codebase
Prevents documentation inflation

Usage:
    python3 scripts/auto_metrics.py [--check-only] [--update-docs]
"""

import json
import yaml
import re
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class MetricsCollector:
    """Collect real metrics from the codebase"""

    def __init__(self, project_root='.'):
        self.root = Path(project_root).resolve()
        self.metrics_cache = {}

    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all real metrics from the codebase"""
        metrics = {
            'version': self.get_version(),
            'performance_budgets': self.count_performance_budgets(),
            'slo_definitions': self.count_slo_definitions(),
            'bdd_scenarios': self.count_bdd_scenarios(),
            'bdd_feature_files': self.count_bdd_feature_files(),
            'ci_workflows': self.count_active_workflows(),
            'shell_scripts': self.count_shell_scripts(),
            'root_documents': self.count_root_documents(),
            'total_documents': self.count_total_documents(),
            'timestamp': datetime.now().isoformat(),
        }

        self.metrics_cache = metrics
        return metrics

    def get_version(self) -> str:
        """Extract version from package.json or default"""
        package_json = self.root / 'package.json'
        if package_json.exists():
            with open(package_json) as f:
                data = json.load(f)
                return data.get('version', '6.2.0')
        return '6.2.0'

    def count_performance_budgets(self) -> int:
        """Count actual performance budget entries"""
        perf_budget_file = self.root / 'metrics' / 'perf_budget.yml'
        if not perf_budget_file.exists():
            return 0

        with open(perf_budget_file) as f:
            data = yaml.safe_load(f)
            if 'performance_budgets' in data:
                return len(data['performance_budgets'])
        return 0

    def count_slo_definitions(self) -> int:
        """Count actual SLO definitions"""
        slo_file = self.root / 'observability' / 'slo' / 'slo.yml'
        if not slo_file.exists():
            return 0

        with open(slo_file) as f:
            data = yaml.safe_load(f)
            if 'slos' in data:
                return len(data['slos'])
        return 0

    def count_bdd_scenarios(self) -> int:
        """Count BDD scenarios across all feature files"""
        features_dir = self.root / 'acceptance' / 'features'
        if not features_dir.exists():
            return 0

        total_scenarios = 0
        for file in features_dir.glob('**/*.feature'):
            with open(file) as f:
                content = f.read()
                # Count "Scenario:" and "Scenario Outline:"
                total_scenarios += content.count('Scenario:')
                total_scenarios += content.count('Scenario Outline:')

        return total_scenarios

    def count_bdd_feature_files(self) -> int:
        """Count BDD feature files"""
        features_dir = self.root / 'acceptance' / 'features'
        if not features_dir.exists():
            return 0

        return len(list(features_dir.glob('**/*.feature')))

    def count_active_workflows(self) -> int:
        """Count active CI/CD workflow files"""
        workflows_dir = self.root / '.github' / 'workflows'
        if not workflows_dir.exists():
            return 0

        return len(list(workflows_dir.glob('*.yml')))

    def count_shell_scripts(self) -> int:
        """Count shell scripts in the project"""
        return len(list(self.root.glob('**/*.sh')))

    def count_root_documents(self) -> int:
        """Count markdown files in project root"""
        return len(list(self.root.glob('*.md')))

    def count_total_documents(self) -> int:
        """Count all markdown files in project"""
        return len(list(self.root.glob('**/*.md')))

    def update_documentation(self, metrics: Dict[str, Any]) -> None:
        """Update documentation with real metrics"""
        self._update_claude_md(metrics)
        self._update_readme(metrics)
        print("✅ Documentation updated with real metrics")

    def _update_claude_md(self, metrics: Dict[str, Any]) -> None:
        """Update CLAUDE.md with accurate metrics"""
        claude_md = self.root / 'CLAUDE.md'
        if not claude_md.exists():
            print("⚠️  CLAUDE.md not found")
            return

        with open(claude_md, 'r', encoding='utf-8') as f:
            content = f.read()

        # Version updates
        content = re.sub(
            r'# Claude Enhancer \d+\.\d+',
            f'# Claude Enhancer {metrics["version"]}',
            content
        )

        # Metrics updates
        replacements = {
            r'- \*\*BDD场景\*\*:\s*\d+个场景': f'- **BDD场景**: {metrics["bdd_scenarios"]}个场景',
            r'- \*\*性能指标\*\*:\s*\d+个性能预算指标': f'- **性能指标**: {metrics["performance_budgets"]}个性能预算指标',
            r'- \*\*SLO定义\*\*:\s*\d+个服务级别目标': f'- **SLO定义**: {metrics["slo_definitions"]}个服务级别目标',
            r'- \*\*CI Jobs\*\*:\s*\d+个核心验证任务': f'- **CI Jobs**: {metrics["ci_workflows"]}个核心验证任务',
        }

        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content)

        with open(claude_md, 'w', encoding='utf-8') as f:
            f.write(content)

    def _update_readme(self, metrics: Dict[str, Any]) -> None:
        """Update README.md with accurate metrics"""
        readme = self.root / 'README.md'
        if not readme.exists():
            print("⚠️  README.md not found")
            return

        with open(readme, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update title version
        content = re.sub(
            r'# Claude Enhancer \d+\.\d+',
            f'# Claude Enhancer {metrics["version"]}',
            content
        )

        # Update version badge
        content = re.sub(
            r'badge/version-[\d\.]+',
            f'badge/version-{metrics["version"]}',
            content
        )

        with open(readme, 'w', encoding='utf-8') as f:
            f.write(content)

    def verify_no_inflation(self) -> bool:
        """Verify claimed metrics don't exceed actual metrics"""
        real_metrics = self.collect_all_metrics()
        claimed_metrics = self._extract_claimed_metrics()

        inflated = []
        for key in real_metrics:
            if key in claimed_metrics and isinstance(real_metrics[key], (int, float)):
                if claimed_metrics[key] > real_metrics[key]:
                    inflated.append({
                        'metric': key,
                        'claimed': claimed_metrics[key],
                        'actual': real_metrics[key],
                        'inflation': claimed_metrics[key] - real_metrics[key]
                    })

        if inflated:
            print("\n❌ METRIC INFLATION DETECTED:\n")
            for item in inflated:
                print(f"  {item['metric']}:")
                print(f"    Claimed: {item['claimed']}")
                print(f"    Actual:  {item['actual']}")
                print(f"    Inflation: +{item['inflation']}\n")
            return False

        print("✅ All metrics accurate - no inflation detected")
        return True

    def _extract_claimed_metrics(self) -> Dict[str, int]:
        """Extract claimed metrics from documentation"""
        claimed = {}

        claude_md = self.root / 'CLAUDE.md'
        if claude_md.exists():
            with open(claude_md, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metrics using regex
            patterns = {
                'bdd_scenarios': r'BDD场景[：:]\s*(\d+)个场景',
                'performance_budgets': r'性能指标[：:]\s*(\d+)个性能预算指标',
                'slo_definitions': r'SLO定义[：:]\s*(\d+)个服务级别目标',
                'ci_workflows': r'CI Jobs[：:]\s*(\d+)个',
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    claimed[key] = int(match.group(1))

        return claimed

    def generate_report(self, metrics: Dict[str, Any]) -> str:
        """Generate a metrics report"""
        report = [
            "=" * 60,
            "📊 Claude Enhancer Metrics Report",
            "=" * 60,
            f"Generated: {metrics['timestamp']}",
            f"Version: {metrics['version']}",
            "",
            "Real Metrics from Codebase:",
            "-" * 60,
            f"  Performance Budgets:  {metrics['performance_budgets']:>4} entries",
            f"  SLO Definitions:      {metrics['slo_definitions']:>4} SLOs",
            f"  BDD Scenarios:        {metrics['bdd_scenarios']:>4} scenarios",
            f"  BDD Feature Files:    {metrics['bdd_feature_files']:>4} files",
            f"  CI Workflows:         {metrics['ci_workflows']:>4} workflows",
            f"  Shell Scripts:        {metrics['shell_scripts']:>4} scripts",
            f"  Root Documents:       {metrics['root_documents']:>4} files",
            f"  Total Documents:      {metrics['total_documents']:>4} files",
            "",
            "Documentation Status:",
            "-" * 60,
        ]

        # Check for discrepancies
        claimed = self._extract_claimed_metrics()
        if claimed:
            report.append("  Claimed vs Actual:")
            for key in ['bdd_scenarios', 'performance_budgets', 'slo_definitions', 'ci_workflows']:
                if key in claimed and key in metrics:
                    claimed_val = claimed[key]
                    actual_val = metrics[key]
                    status = "✅" if claimed_val == actual_val else "❌"
                    report.append(f"    {status} {key}: {claimed_val} claimed, {actual_val} actual")

        report.extend([
            "",
            "=" * 60,
        ])

        return "\n".join(report)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Collect and verify Claude Enhancer metrics')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check for inflation, don\'t update docs')
    parser.add_argument('--update-docs', action='store_true',
                       help='Update documentation with real metrics')
    parser.add_argument('--report', action='store_true',
                       help='Generate detailed report')

    args = parser.parse_args()

    collector = MetricsCollector()

    print("📊 Collecting real metrics from codebase...\n")
    metrics = collector.collect_all_metrics()

    if args.report:
        print(collector.generate_report(metrics))
    else:
        print("Real Metrics:")
        for key, value in metrics.items():
            if key != 'timestamp':
                print(f"  {key}: {value}")

    if args.check_only:
        print("\n🔍 Verifying metrics accuracy...")
        is_accurate = collector.verify_no_inflation()
        sys.exit(0 if is_accurate else 1)

    if args.update_docs:
        print("\n📝 Updating documentation...")
        collector.update_documentation(metrics)

    print("\n🔍 Verifying metrics accuracy...")
    collector.verify_no_inflation()


if __name__ == '__main__':
    main()
