#!/usr/bin/env python3
"""
Perfect21 质量门 CLI
==================

命令行界面管理质量门
"""

import asyncio
import click
import json
import sys
from pathlib import Path
from datetime import datetime

from .quality_gate_engine import QualityGateEngine, QualityGateConfig
from .ci_integration import CIIntegration


@click.group()
def quality_gates():
    """Perfect21 自动化质量门管理"""
    pass


@quality_gates.command()
@click.option('--context', default='commit', help='执行上下文 (commit/merge/release/all)')
@click.option('--parallel/--no-parallel', default=True, help='是否并行执行')
@click.option('--fail-fast/--no-fail-fast', default=False, help='是否快速失败')
@click.option('--config-file', help='配置文件路径')
@click.option('--output', type=click.Choice(['text', 'json', 'html']), default='text', help='输出格式')
@click.option('--save-results/--no-save-results', default=True, help='是否保存结果')
async def check(context, parallel, fail_fast, config_file, output, save_results):
    """运行质量门检查"""
    try:
        # 加载配置
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            config = QualityGateConfig(**config_data)
        else:
            config = QualityGateConfig()

        config.parallel_execution = parallel
        config.fail_fast = fail_fast

        # 创建质量门引擎
        engine = QualityGateEngine('.', config)

        click.echo(f"🔍 运行质量门检查 - 上下文: {context}")

        # 执行检查
        start_time = datetime.now()
        if context == 'quick':
            results = await engine.run_quick_check()
        else:
            full_results = await engine.run_all_gates(context)
            results = full_results.get('overall')

        execution_time = (datetime.now() - start_time).total_seconds()

        # 输出结果
        if output == 'json':
            if context == 'quick':
                click.echo(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                click.echo(json.dumps({name: result.__dict__ for name, result in full_results.items()},
                                    indent=2, ensure_ascii=False, default=str))
        elif output == 'html':
            if context != 'quick':
                report = engine.generate_report(full_results)
                html_file = Path('.perfect21/quality_report.html')
                html_file.parent.mkdir(exist_ok=True)

                html_content = f"""
<!DOCTYPE html>
<html>
<head><title>Quality Report</title><meta charset="utf-8"></head>
<body><pre>{report}</pre></body>
</html>
                """

                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                click.echo(f"📄 HTML报告已保存: {html_file}")
            else:
                click.echo("HTML输出仅支持完整检查")
        else:  # text
            if context == 'quick':
                click.echo(f"状态: {results['status']}")
                click.echo(f"分数: {results['score']:.1f}")
                click.echo(f"消息: {results['message']}")
            else:
                report = engine.generate_report(full_results)
                click.echo(report)

        click.echo(f"⏱️ 执行时间: {execution_time:.2f}秒")

        # 保存结果
        if save_results and context != 'quick':
            results_file = Path('.perfect21/last_quality_check.json')
            results_file.parent.mkdir(exist_ok=True)

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'context': context,
                    'results': {name: result.__dict__ for name, result in full_results.items()},
                    'execution_time': execution_time
                }, f, indent=2, ensure_ascii=False, default=str)

        # 确定退出码
        if context == 'quick':
            exit_code = 0 if results['status'] == 'passed' else 1
        else:
            overall = full_results.get('overall')
            exit_code = 0 if overall and overall.status.value in ['passed', 'warning'] else 1

        sys.exit(exit_code)

    except Exception as e:
        click.echo(f"❌ 质量门检查失败: {str(e)}", err=True)
        sys.exit(1)


@quality_gates.command()
@click.option('--days', default=30, help='分析天数')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text', help='输出格式')
async def trends(days, output_format):
    """显示质量趋势"""
    try:
        engine = QualityGateEngine('.')
        trends_data = engine.get_quality_trends(days=days)

        if output_format == 'json':
            click.echo(json.dumps(trends_data, indent=2, ensure_ascii=False))
        else:
            click.echo(f"📊 质量趋势 (最近 {days} 天)")
            click.echo("=" * 50)

            click.echo(f"总执行次数: {trends_data.get('total_executions', 0)}")

            if trends_data.get('gate_performance'):
                click.echo("\n🏆 质量门性能:")
                for gate_name, performance in trends_data['gate_performance'].items():
                    click.echo(f"  {gate_name}: {performance['average_score']:.1f}分 "
                              f"(执行{performance['executions']}次)")

            if trends_data.get('common_violations'):
                click.echo("\n🔍 常见违规:")
                for violation_type, count in list(trends_data['common_violations'].items())[:5]:
                    click.echo(f"  {violation_type}: {count}次")

            if trends_data.get('improvement_suggestions'):
                click.echo("\n💡 改进建议:")
                for suggestion in trends_data['improvement_suggestions']:
                    click.echo(f"  • {suggestion}")

    except Exception as e:
        click.echo(f"❌ 获取质量趋势失败: {str(e)}", err=True)
        sys.exit(1)


@quality_gates.command()
@click.option('--limit', default=10, help='显示记录数量')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text', help='输出格式')
async def history(limit, output_format):
    """显示执行历史"""
    try:
        engine = QualityGateEngine('.')
        history_data = engine.get_execution_history(limit=limit)

        if output_format == 'json':
            click.echo(json.dumps(history_data, indent=2, ensure_ascii=False))
        else:
            click.echo(f"📋 执行历史 (最近 {len(history_data)} 条记录)")
            click.echo("=" * 60)

            for entry in reversed(history_data):  # 最新的在前
                timestamp = entry['timestamp'][:19].replace('T', ' ')
                summary = entry['summary']

                status_emoji = "✅" if summary['failed'] == 0 else "❌"
                click.echo(f"{status_emoji} {timestamp} | "
                          f"通过:{summary['passed']} 失败:{summary['failed']} "
                          f"分数:{summary['average_score']:.1f} "
                          f"上下文:{entry['context']}")

    except Exception as e:
        click.echo(f"❌ 获取执行历史失败: {str(e)}", err=True)
        sys.exit(1)


@quality_gates.group()
def setup():
    """设置和配置质量门"""
    pass


@setup.command()
async def hooks():
    """安装Git hooks"""
    try:
        ci = CIIntegration('.')
        result = await ci.setup_pre_commit_hooks()

        if result['status'] == 'success':
            click.echo("✅ Git hooks安装成功")
            click.echo(f"安装的hooks: {', '.join(result['hooks_installed'])}")
        else:
            click.echo(f"❌ Git hooks安装失败: {result['message']}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ 安装Git hooks失败: {str(e)}", err=True)
        sys.exit(1)


@setup.command()
async def ci():
    """设置CI/CD集成"""
    try:
        ci = CIIntegration('.')
        result = await ci.setup_all_integrations()

        click.echo(f"🚀 CI/CD集成设置: {result['message']}")

        for component, component_result in result['results'].items():
            status_emoji = "✅" if component_result['status'] == 'success' else "❌"
            click.echo(f"  {status_emoji} {component}: {component_result['message']}")

        if result['next_steps']:
            click.echo("\n📋 后续步骤:")
            for step in result['next_steps']:
                click.echo(f"  {step}")

    except Exception as e:
        click.echo(f"❌ 设置CI/CD集成失败: {str(e)}", err=True)
        sys.exit(1)


@setup.command()
async def monitoring():
    """设置持续监控"""
    try:
        ci = CIIntegration('.')
        result = await ci.setup_continuous_monitoring()

        if result['status'] == 'success':
            click.echo("✅ 持续监控设置成功")
            click.echo(f"监控脚本: {result['monitoring_script']}")
            click.echo(f"Cron配置: {result['cron_config']}")

            click.echo("\n📋 设置说明:")
            for instruction in result['instructions']:
                click.echo(f"  {instruction}")
        else:
            click.echo(f"❌ 持续监控设置失败: {result['message']}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ 设置持续监控失败: {str(e)}", err=True)
        sys.exit(1)


@quality_gates.command()
async def dashboard():
    """生成质量仪表板"""
    try:
        ci = CIIntegration('.')
        result = await ci.create_quality_dashboard()

        if result['status'] == 'success':
            click.echo("✅ 质量仪表板已生成")
            click.echo(f"使用说明: {result['usage']}")

            # 直接运行仪表板生成
            exec_result = await ci.generate_dashboard()
            click.echo("🌐 仪表板已更新")
        else:
            click.echo(f"❌ 生成质量仪表板失败: {result['message']}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ 生成质量仪表板失败: {str(e)}", err=True)
        sys.exit(1)


@quality_gates.command()
@click.option('--output', default='.perfect21/quality_config.json', help='配置文件路径')
@click.option('--template', type=click.Choice(['strict', 'balanced', 'lenient']),
              default='balanced', help='配置模板')
async def config(output, template):
    """生成质量门配置文件"""
    try:
        if template == 'strict':
            config = QualityGateConfig(
                min_line_coverage=95.0,
                min_branch_coverage=90.0,
                min_function_coverage=95.0,
                max_complexity=5,
                max_duplications=2.0,
                max_security_issues=0,
                max_response_time_p95=100.0,
                max_memory_usage=256.0,
                fail_fast=True
            )
        elif template == 'lenient':
            config = QualityGateConfig(
                min_line_coverage=60.0,
                min_branch_coverage=50.0,
                min_function_coverage=70.0,
                max_complexity=25,
                max_duplications=10.0,
                max_security_issues=5,
                max_response_time_p95=500.0,
                max_memory_usage=1024.0,
                fail_fast=False
            )
        else:  # balanced
            config = QualityGateConfig()

        config_dict = {
            'min_line_coverage': config.min_line_coverage,
            'min_branch_coverage': config.min_branch_coverage,
            'min_function_coverage': config.min_function_coverage,
            'max_complexity': config.max_complexity,
            'max_duplications': config.max_duplications,
            'max_security_issues': config.max_security_issues,
            'max_response_time_p95': config.max_response_time_p95,
            'max_memory_usage': config.max_memory_usage,
            'min_throughput': config.min_throughput,
            'max_coupling_score': config.max_coupling_score,
            'min_cohesion_score': config.min_cohesion_score,
            'max_cyclomatic_complexity': config.max_cyclomatic_complexity,
            'fail_fast': config.fail_fast,
            'parallel_execution': config.parallel_execution,
            'timeout_seconds': config.timeout_seconds,
            'allowed_security_levels': config.allowed_security_levels
        }

        output_path = Path(output)
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

        click.echo(f"✅ 配置文件已生成: {output_path}")
        click.echo(f"模板: {template}")
        click.echo("💡 可以编辑配置文件来调整质量标准")

    except Exception as e:
        click.echo(f"❌ 生成配置文件失败: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    # 使用asyncio运行命令
    def async_cli():
        import inspect

        # 修改click命令以支持async
        for command in quality_gates.commands.values():
            if inspect.iscoroutinefunction(command.callback):
                original_callback = command.callback
                def make_sync_wrapper(coro_func):
                    def sync_wrapper(*args, **kwargs):
                        return asyncio.run(coro_func(*args, **kwargs))
                    return sync_wrapper
                command.callback = make_sync_wrapper(original_callback)

        # 同样处理setup子组
        for command in setup.commands.values():
            if inspect.iscoroutinefunction(command.callback):
                original_callback = command.callback
                def make_sync_wrapper(coro_func):
                    def sync_wrapper(*args, **kwargs):
                        return asyncio.run(coro_func(*args, **kwargs))
                    return sync_wrapper
                command.callback = make_sync_wrapper(original_callback)

        quality_gates()

    async_cli()