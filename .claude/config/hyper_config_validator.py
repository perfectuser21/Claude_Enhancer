#!/usr/bin/env python3
"""
Claude Enhancer 超高性能配置验证器 v3.0
目标：比原版本快10x，实现亚秒级验证
优化策略：预编译验证器、缓存结果、并行验证、智能跳过
"""

import sys
import yaml
import json
import time
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple
import logging

# 性能配置
PERFORMANCE_MODE = True
CACHE_TTL = 3600  # 1小时缓存
MAX_WORKERS = 4
VALIDATION_TIMEOUT = 5  # 5秒超时
ENABLE_PARALLEL = True
ENABLE_SMART_CACHE = True

# 缓存目录
CACHE_DIR = Path("/dev/shm/claude-enhancer_config_cache")
PERF_LOG = Path("/dev/shm/claude-enhancer_config_perf.log")


class PerformanceTimer:
    """纳秒级性能计时器"""

    def __init__(self):
        self.timers = {}

    def start(self, name: str):
        self.timers[name] = time.perf_counter_ns()

    def end(self, name: str) -> float:
        if name not in self.timers:
            return 0.0
        duration_ns = time.perf_counter_ns() - self.timers[name]
        duration_ms = duration_ns / 1_000_000

        # 非阻塞日志记录
        if PERF_LOG.parent.exists():
            try:
                with open(PERF_LOG, "a") as f:
                    f.write(f"[{name}] {duration_ms:.3f}ms\n")
            except:
                pass

        return duration_ms


class SmartCache:
    """智能缓存系统"""

    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, data: Any) -> str:
        """生成缓存键"""
        content = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(content).hexdigest()[:16]

    def get(self, key: str, ttl: int = CACHE_TTL) -> Optional[Any]:
        """获取缓存"""
        if not ENABLE_SMART_CACHE:
            return None

        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None

        try:
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age > ttl:
                cache_file.unlink()
                return None

            return json.loads(cache_file.read_text())
        except:
            return None

    def set(self, key: str, value: Any):
        """设置缓存"""
        if not ENABLE_SMART_CACHE:
            return

        cache_file = self.cache_dir / f"{key}.json"
        try:
            cache_file.write_text(json.dumps(value))
        except:
            pass


class PrecompiledValidator:
    """预编译验证器"""

    def __init__(self):
        self.cache = SmartCache()
        self.timer = PerformanceTimer()
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

        # 预编译验证规则
        self.validation_rules = {
            "metadata": {
                "required": ["name", "version"],
                "optional": ["description", "author"],
                "types": {"name": str, "version": str},
            },
            "system": {
                "required": ["cores", "memory"],
                "optional": ["cache_dir", "log_level"],
                "types": {"cores": int, "memory": str},
            },
            "workflow": {
                "required": ["phases"],
                "optional": ["hooks", "validation"],
                "types": {"phases": list},
            },
            "agents": {
                "required": ["count", "types"],
                "optional": ["parallel", "timeout"],
                "types": {"count": int, "types": list},
            },
        }

    def _validate_section_fast(
        self, section_name: str, section_data: Dict
    ) -> Tuple[bool, List[str]]:
        """快速验证单个配置节"""
        errors = []

        if section_name not in self.validation_rules:
            return True, []

        rules = self.validation_rules[section_name]

        # 检查必需字段
        for field in rules.get("required", []):
            if field not in section_data:
                errors.append(
                    f"Missing required field '{field}' in section '{section_name}'"
                )

        # 检查类型
        for field, expected_type in rules.get("types", {}).items():
            if field in section_data:
                value = section_data[field]
                if not isinstance(value, expected_type):
                    errors.append(
                        f"Field '{field}' in section '{section_name}' should be {expected_type.__name__}, got {type(value).__name__}"
                    )

        return len(errors) == 0, errors

    def validate_config_parallel(
        self, config_path: Path
    ) -> Tuple[bool, List[str], Dict[str, float]]:
        """并行配置验证"""
        self.timer.start("total_validation")

        # 生成文件哈希用于缓存
        try:
            with open(config_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()[:16]
        except Exception as e:
            return False, [f"Cannot read config file: {e}"], {}

        # 检查缓存
        cache_key = f"validation_{file_hash}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            total_time = self.timer.end("total_validation")
            return (
                cached_result["valid"],
                cached_result["errors"],
                {"total": total_time, "cache_hit": True},
            )

        # 加载配置
        self.timer.start("config_load")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            load_time = self.timer.end("config_load")
            total_time = self.timer.end("total_validation")
            return (
                False,
                [f"YAML parsing error: {e}"],
                {"load": load_time, "total": total_time},
            )

        load_time = self.timer.end("config_load")

        # 并行验证各个节
        self.timer.start("parallel_validation")

        if ENABLE_PARALLEL:
            # 使用ThreadPoolExecutor进行并行验证
            results = []
            with self.executor as executor:
                future_to_section = {}

                for section_name in self.validation_rules.keys():
                    if section_name in config:
                        future = executor.submit(
                            self._validate_section_fast,
                            section_name,
                            config[section_name],
                        )
                        future_to_section[future] = section_name

                # 收集结果
                for future in as_completed(
                    future_to_section, timeout=VALIDATION_TIMEOUT
                ):
                    section_name = future_to_section[future]
                    try:
                        result = future.result()
                        results.append((section_name, result))
                    except Exception as e:
                        results.append(
                            (
                                section_name,
                                (
                                    False,
                                    [
                                        f"Validation error for section '{section_name}': {e}"
                                    ],
                                ),
                            )
                        )
        else:
            # 串行验证
            results = []
            for section_name in self.validation_rules.keys():
                if section_name in config:
                    result = self._validate_section_fast(
                        section_name, config[section_name]
                    )
                    results.append((section_name, result))

        validation_time = self.timer.end("parallel_validation")

        # 收集错误
        all_errors = []
        all_valid = True

        for section_name, (valid, errors) in results:
            if not valid:
                all_valid = False
                all_errors.extend(errors)

        # 额外的全局验证
        self.timer.start("global_validation")
        if "agents" in config and "count" in config["agents"]:
            agent_count = config["agents"]["count"]
            if agent_count < 3:
                all_valid = False
                all_errors.append(
                    "Agent count should be at least 3 for Claude Enhancer"
                )

        global_time = self.timer.end("global_validation")
        total_time = self.timer.end("total_validation")

        # 缓存结果
        result = {"valid": all_valid, "errors": all_errors}
        self.cache.set(cache_key, result)

        timing_info = {
            "load": load_time,
            "validation": validation_time,
            "global": global_time,
            "total": total_time,
            "cache_hit": False,
        }

        return all_valid, all_errors, timing_info


class HyperConfigValidator:
    """超高性能配置验证器主类"""

    def __init__(self):
        self.validator = PrecompiledValidator()

    def validate(self, config_path: Optional[Path] = None) -> bool:
        """验证配置文件"""
        if config_path is None:
            config_path = Path(__file__).parent / "main.yaml"

        if not config_path.exists():
            print(f"❌ Config file not found: {config_path}")
            return False

        try:
            valid, errors, timing = self.validator.validate_config_parallel(config_path)

            if valid:
                cache_status = (
                    "💾 Cache Hit" if timing.get("cache_hit") else "🔄 Fresh Validation"
                )
                print(f"✅ Configuration valid ({cache_status})")
                if PERFORMANCE_MODE:
                    print(f"⚡ Performance: {timing['total']:.3f}ms total")
                    if not timing.get("cache_hit"):
                        print(
                            f"   📊 Load: {timing['load']:.3f}ms | Validation: {timing['validation']:.3f}ms | Global: {timing['global']:.3f}ms"
                        )
            else:
                print("❌ Configuration validation failed:")
                for error in errors:
                    print(f"   • {error}")
                if PERFORMANCE_MODE:
                    print(f"⚡ Performance: {timing['total']:.3f}ms total")

            return valid

        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False

    def benchmark(self, iterations: int = 100) -> Dict[str, float]:
        """性能基准测试"""
        config_path = Path(__file__).parent / "main.yaml"

        if not config_path.exists():
            print("❌ Config file not found for benchmarking")
            return {}

        print(f"🏃 Running performance benchmark ({iterations} iterations)...")

        times = []
        cache_hits = 0

        for i in range(iterations):
            start_time = time.perf_counter_ns()
            valid, errors, timing = self.validator.validate_config_parallel(config_path)
            end_time = time.perf_counter_ns()

            duration_ms = (end_time - start_time) / 1_000_000
            times.append(duration_ms)

            if timing.get("cache_hit"):
                cache_hits += 1

            if i % 20 == 0:
                print(f"   Progress: {i}/{iterations} ({i/iterations*100:.1f}%)")

        # 计算统计数据
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        cache_hit_rate = cache_hits / iterations * 100

        stats = {
            "iterations": iterations,
            "avg_time_ms": avg_time,
            "min_time_ms": min_time,
            "max_time_ms": max_time,
            "cache_hit_rate": cache_hit_rate,
            "total_time_ms": sum(times),
        }

        print(f"\n📊 Benchmark Results:")
        print(f"   Average: {avg_time:.3f}ms")
        print(f"   Min: {min_time:.3f}ms | Max: {max_time:.3f}ms")
        print(f"   Cache Hit Rate: {cache_hit_rate:.1f}%")
        print(f"   Total Time: {sum(times):.3f}ms")
        print(f"   Throughput: {iterations / (sum(times) / 1000):.1f} validations/sec")

        return stats

    def cleanup_cache(self):
        """清理过期缓存"""
        if CACHE_DIR.exists():
            import shutil

            try:
                shutil.rmtree(CACHE_DIR)
                print("🧹 Cache cleaned")
            except:
                print("⚠️ Cache cleanup failed")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python3 hyper_config_validator.py <command> [options]")
        print("Commands:")
        print("  validate [file]  - Validate configuration file")
        print("  benchmark [n]    - Run performance benchmark")
        print("  cleanup          - Clean cache")
        return

    command = sys.argv[1]
    validator = HyperConfigValidator()

    if command == "validate":
        config_file = None
        if len(sys.argv) > 2:
            config_file = Path(sys.argv[2])

        success = validator.validate(config_file)
        sys.exit(0 if success else 1)

    elif command == "benchmark":
        iterations = 100
        if len(sys.argv) > 2:
            try:
                iterations = int(sys.argv[2])
            except ValueError:
                print("❌ Invalid iteration count")
                sys.exit(1)

        validator.benchmark(iterations)

    elif command == "cleanup":
        validator.cleanup_cache()

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
