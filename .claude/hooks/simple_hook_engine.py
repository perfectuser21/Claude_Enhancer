#!/usr/bin/env python3
"""
Claude Enhancer - 简化版Hook引擎
轻量级版本，专注核心功能，确保兼容性

核心特性：
- 快速执行（目标<200ms）
- 简单缓存
- 基本错误处理
- 最小依赖
"""

import os
import sys
import time
import json
import subprocess
import hashlib
from pathlib import Path


class SimpleHookCache:
    """简单的文件缓存系统"""

    def __init__(self, cache_dir="/tmp/claude_simple_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = 300  # 5分钟

    def _get_cache_path(self, key):
        """获取缓存文件路径"""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"cache_{hash_key}.json"

    def get(self, key):
        """获取缓存"""
        cache_file = self._get_cache_path(key)
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                data = json.load(f)

            # 检查TTL
            if time.time() - data["timestamp"] > self.ttl:
                cache_file.unlink()
                return None

            return data["result"]
        except Exception:
            return None

    def set(self, key, result):
        """设置缓存"""
        cache_file = self._get_cache_path(key)
        try:
            data = {"timestamp": time.time(), "result": result}
            with open(cache_file, "w") as f:
                json.dump(data, f)
        except Exception:
            pass  # 缓存失败不影响主流程


class SimpleHookEngine:
    """简化版Hook引擎"""

    def __init__(self):
        self.cache = SimpleHookCache()
        # 修复路径问题 - 使用正确的项目路径
        self.hooks_dir = Path("/home/xx/dev/Claude Enhancer 5.0/.claude/hooks")
        self.timeout = 3.0  # 增加到3秒超时，更合理

    def execute_hook(self, hook_name, context=None):
        """执行单个Hook"""
        start_time = time.time()

        # 生成缓存键
        cache_key = f"{hook_name}_{context or ''}"

        # 检查缓存
        cached_result = self.cache.get(cache_key)
        if cached_result:
            cached_result["cached"] = True
            return cached_result

        # 确定Hook脚本路径
        hook_script = self._get_hook_script(hook_name)
        if not hook_script:
            return self._error_result(hook_name, "Hook script not found", start_time)

        # 执行Hook
        try:
            env = os.environ.copy()
            if context:
                env["HOOK_CONTEXT"] = (
                    json.dumps(context) if isinstance(context, dict) else str(context)
                )

            # 修复路径空格问题 - 使用引号包裹
            result = subprocess.run(
                f'bash "{hook_script}"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
            )

            execution_time = time.time() - start_time

            hook_result = {
                "hook_name": hook_name,
                "success": result.returncode == 0,
                "execution_time": execution_time,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "cached": False,
            }

            # 缓存成功结果
            if hook_result["success"]:
                self.cache.set(cache_key, hook_result)

            return hook_result

        except subprocess.TimeoutExpired:
            return self._error_result(
                hook_name, f"Timeout after {self.timeout}s", start_time
            )
        except Exception as e:
            return self._error_result(hook_name, str(e), start_time)

    def _get_hook_script(self, hook_name):
        """获取Hook脚本路径"""
        script_mappings = {
            "ultra_fast_agent_selector": "ultra_fast_agent_selector.sh",
            "optimized_performance_monitor": "optimized_performance_monitor.sh",
            "smart_error_recovery": "smart_error_recovery.sh",
            "concurrent_optimizer": "concurrent_optimizer.sh",
            "quality_gate": "quality_gate.sh",
            "task_type_detector": "task_type_detector.sh",
        }

        script_name = script_mappings.get(hook_name, f"{hook_name}.sh")
        script_path = self.hooks_dir / script_name

        if script_path.exists():
            return script_path

        # 回退到Python脚本
        python_script = self.hooks_dir / f"{hook_name}.py"
        if python_script.exists():
            return python_script

        return None

    def _error_result(self, hook_name, error_msg, start_time):
        """创建错误结果"""
        return {
            "hook_name": hook_name,
            "success": False,
            "execution_time": time.time() - start_time,
            "output": "",
            "error": error_msg,
            "cached": False,
        }

    def execute_multiple_hooks(self, hook_names, context=None):
        """执行多个Hook（串行，保证稳定性）"""
        results = []

        for hook_name in hook_names:
            result = self.execute_hook(hook_name, context)
            results.append(result)

            # 如果是关键Hook失败，继续执行其他Hook
            if not result["success"]:
                print(
                    f"Warning: Hook {hook_name} failed: {result['error']}",
                    file=sys.stderr,
                )

        return results

    def get_stats(self):
        """获取统计信息"""
        cache_files = list(self.cache.cache_dir.glob("cache_*.json"))
        return {
            "cache_entries": len(cache_files),
            "cache_dir": str(self.cache.cache_dir),
            "engine_version": "simple-1.0",
            "supported_hooks": [
                "ultra_fast_agent_selector",
                "optimized_performance_monitor",
                "smart_error_recovery",
                "concurrent_optimizer",
                "quality_gate",
                "task_type_detector",
            ],
        }


def main():
    """主函数"""
    engine = SimpleHookEngine()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--stats":
            stats = engine.get_stats()
            print(json.dumps(stats, indent=2))
            return

        if sys.argv[1] == "--test":
            # 测试模式
            test_hooks = ["ultra_fast_agent_selector", "optimized_performance_monitor"]
            results = engine.execute_multiple_hooks(test_hooks, {"test_mode": True})

            print("Test Results:")
            for result in results:
                status = "✅" if result["success"] else "❌"
                cached = " (cached)" if result.get("cached") else ""
                print(
                    f"  {status} {result['hook_name']}: {result['execution_time']:.3f}s{cached}"
                )
            return

        # 执行指定Hook
        hook_name = sys.argv[1]
        context = {"args": sys.argv[2:]} if len(sys.argv) > 2 else None

        result = engine.execute_hook(hook_name, context)

        if result["output"]:
            print(result["output"])

        if not result["success"]:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Simple Hook Engine - Usage:")
        print("  python3 simple_hook_engine.py <hook_name> [args...]")
        print("  python3 simple_hook_engine.py --stats")
        print("  python3 simple_hook_engine.py --test")


if __name__ == "__main__":
    main()
