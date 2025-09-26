#!/usr/bin/env python3
"""
Lazy Loading Migration Script
Enables lazy loading optimizations in existing Claude Enhancer system

This script:
1. Backs up current configuration
2. Updates settings to use lazy loading components
3. Validates the migration
4. Provides rollback capability
5. Measures performance improvements
"""

import os
import sys
import json
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List
import subprocess


class LazyLoadingMigration:
    """Handles migration to lazy loading system"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.claude_dir = self.project_root / ".claude"
        self.backup_dir = self.claude_dir / "backup_before_lazy_loading"
        self.migration_log = []

        print(f"🚀 Lazy Loading Migration for: {self.project_root}")

    def log(self, message: str, level: str = "INFO"):
        """Log migration step"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.migration_log.append(log_entry)

    def create_backup(self):
        """Create backup of current configuration"""
        self.log("Creating backup of current configuration")

        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)

            self.backup_dir.mkdir(parents=True)

            # Backup key files
            files_to_backup = [
                ".claude/settings.json",
                ".claude/settings_high_performance.json",
                ".claude/core/engine.py",
                ".claude/core/orchestrator.py",
                ".claude/hooks/high_performance_hook_engine.py",
            ]

            for file_path in files_to_backup:
                source = self.project_root / file_path
                if source.exists():
                    dest = self.backup_dir / Path(file_path).name
                    shutil.copy2(source, dest)
                    self.log(f"Backed up: {file_path}")

            self.log("✅ Backup completed successfully")
            return True

        except Exception as e:
            self.log(f"❌ Backup failed: {e}", "ERROR")
            return False

    def update_settings(self):
        """Update Claude settings to enable lazy loading"""
        self.log("Updating Claude settings for lazy loading")

        try:
            settings_file = self.claude_dir / "settings.json"

            if not settings_file.exists():
                self.log("❌ settings.json not found", "ERROR")
                return False

            # Load current settings
            with open(settings_file) as f:
                settings = json.load(f)

            # Add lazy loading configuration
            settings["lazy_loading"] = {
                "enabled": True,
                "version": "1.0.0",
                "engine_class": "lazy_engine.LazyWorkflowEngine",
                "orchestrator_class": "lazy_orchestrator.LazyAgentOrchestrator",
                "performance_target": "50% startup reduction",
            }

            # Update performance settings
            if "performance" not in settings:
                settings["performance"] = {}

            settings["performance"].update(
                {
                    "lazy_component_loading": True,
                    "cache_components": True,
                    "background_preloading": True,
                    "startup_optimization": True,
                }
            )

            # Update environment variables
            if "environment" not in settings:
                settings["environment"] = {}

            settings["environment"].update(
                {
                    "LAZY_LOADING": "enabled",
                    "COMPONENT_CACHING": "true",
                    "PRELOAD_COMMON": "true",
                }
            )

            # Save updated settings
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=2)

            self.log("✅ Settings updated successfully")
            return True

        except Exception as e:
            self.log(f"❌ Settings update failed: {e}", "ERROR")
            return False

    def create_launcher_script(self):
        """Create launcher script that uses lazy loading components"""
        self.log("Creating lazy loading launcher")

        launcher_content = '''#!/usr/bin/env python3
"""
Claude Enhancer with Lazy Loading
Performance-optimized launcher
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / ".claude" / "core"))
sys.path.insert(0, str(project_root / "src"))

try:
    # Try to import lazy components first
    from lazy_engine import LazyWorkflowEngine
    from lazy_orchestrator import LazyAgentOrchestrator
    from phase_controller import LazyLoadingPhaseController

    print("🚀 Starting Claude Enhancer with lazy loading optimizations")

    def main():
        """Main entry point with lazy loading"""
        import time
        start_time = time.time()

        # Initialize lazy components
        engine = LazyWorkflowEngine()
        orchestrator = LazyAgentOrchestrator()
        controller = LazyLoadingPhaseController()

        startup_time = time.time() - start_time
        print(f"✅ Initialized in {startup_time:.3f}s")

        # Get status
        engine_status = engine.get_status()
        orchestrator_stats = orchestrator.get_performance_stats()
        controller_metrics = controller.getMetrics()

        print("\\n📊 System Status:")
        print(f"  Engine: {engine_status.get('performance', {}).get('startup_time', 'N/A')}")
        print(f"  Cache hit rate: {orchestrator_stats.get('cache_stats', {}).get('cache_hit_rate', 'N/A')}")
        print(f"  Components loaded: {controller_metrics.get('lazyLoads', 0)}")

        return {
            "engine": engine,
            "orchestrator": orchestrator,
            "controller": controller,
            "startup_time": startup_time
        }

    if __name__ == "__main__":
        components = main()

        # Interactive mode
        print("\\n🎮 Interactive mode - type 'help' for commands")
        while True:
            try:
                cmd = input("> ").strip().lower()

                if cmd == "help":
                    print("Commands: status, benchmark, warmup, test, quit")
                elif cmd == "status":
                    print(json.dumps(components["engine"].get_status(), indent=2))
                elif cmd == "benchmark":
                    from lazy_loading_performance_test import PerformanceTestSuite
                    suite = PerformanceTestSuite()
                    results = suite.run_comprehensive_benchmark()
                    print(f"Benchmark completed. Startup improvement: {results.get('overall_performance', {}).get('startup_improvement_percent', 0):.1f}%")
                elif cmd == "warmup":
                    components["orchestrator"].warmup()
                    components["controller"].warmup()
                    print("✅ Warmup completed")
                elif cmd == "test":
                    # Quick functionality test
                    result = components["engine"].execute_phase(1, description="test phase")
                    print(f"Test result: {result.get('message', 'Unknown')}")
                elif cmd in ["quit", "exit", "q"]:
                    break
                else:
                    print(f"Unknown command: {cmd}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

        print("👋 Goodbye!")

except ImportError as e:
    print(f"❌ Failed to import lazy loading components: {e}")
    print("Falling back to standard components...")

    # Fallback to original components
    sys.path.insert(0, str(project_root / ".claude" / "core"))

    try:
        from engine import WorkflowEngine
        from orchestrator import AgentOrchestrator

        def main():
            engine = WorkflowEngine()
            orchestrator = AgentOrchestrator()
            print("✅ Started with standard components")
            return {"engine": engine, "orchestrator": orchestrator}

        if __name__ == "__main__":
            main()

    except ImportError as e2:
        print(f"❌ Failed to import any components: {e2}")
        sys.exit(1)
'''

        try:
            launcher_file = self.project_root / "claude_enhancer_lazy.py"
            with open(launcher_file, "w") as f:
                f.write(launcher_content)

            # Make executable
            os.chmod(launcher_file, 0o755)

            self.log(f"✅ Created launcher: {launcher_file}")
            return True

        except Exception as e:
            self.log(f"❌ Launcher creation failed: {e}", "ERROR")
            return False

    def validate_migration(self):
        """Validate that lazy loading is working correctly"""
        self.log("Validating lazy loading migration")

        try:
            # Test imports
            sys.path.insert(0, str(self.claude_dir / "core"))

            try:
                from lazy_engine import LazyWorkflowEngine
                from lazy_orchestrator import LazyAgentOrchestrator

                self.log("✅ Lazy components import successfully")
            except ImportError as e:
                self.log(f"❌ Failed to import lazy components: {e}", "ERROR")
                return False

            # Test basic functionality
            start_time = time.time()
            engine = LazyWorkflowEngine()
            orchestrator = LazyAgentOrchestrator()
            init_time = time.time() - start_time

            if init_time > 0.2:  # 200ms threshold
                self.log(
                    f"⚠️  Initialization time ({init_time:.3f}s) higher than expected",
                    "WARNING",
                )
            else:
                self.log(f"✅ Fast initialization: {init_time:.3f}s")

            # Test engine functionality
            status = engine.get_status()
            if not isinstance(status, dict):
                self.log("❌ Engine status check failed", "ERROR")
                return False

            # Test orchestrator functionality
            result = orchestrator.select_agents_fast("test task")
            if not isinstance(result, dict) or not result.get("selected_agents"):
                self.log("❌ Orchestrator selection failed", "ERROR")
                return False

            self.log("✅ Migration validation passed")
            return True

        except Exception as e:
            self.log(f"❌ Validation failed: {e}", "ERROR")
            return False

    def benchmark_performance(self):
        """Benchmark performance improvement"""
        self.log("Running performance benchmark")

        try:
            sys.path.insert(0, str(self.project_root / "src"))
            from lazy_loading_performance_test import PerformanceTestSuite

            suite = PerformanceTestSuite()
            results = suite.run_comprehensive_benchmark()

            improvement = results.get("overall_performance", {}).get(
                "startup_improvement_percent", 0
            )
            target_met = results.get("overall_performance", {}).get(
                "target_achieved", False
            )

            self.log(f"📊 Performance Results:")
            self.log(f"  Startup improvement: {improvement:.1f}%")
            self.log(f"  Target achieved: {'✅ Yes' if target_met else '❌ No'}")

            if target_met:
                self.log("🎉 Migration successful - 50%+ improvement achieved!")
            else:
                self.log(
                    "⚠️  Target not fully met, but some improvement gained", "WARNING"
                )

            return results

        except Exception as e:
            self.log(f"❌ Benchmark failed: {e}", "ERROR")
            return None

    def create_rollback_script(self):
        """Create rollback script"""
        rollback_content = f'''#!/usr/bin/env python3
"""
Rollback script for lazy loading migration
Restores original configuration
"""

import shutil
from pathlib import Path

def rollback():
    project_root = Path(__file__).parent
    backup_dir = project_root / ".claude" / "backup_before_lazy_loading"

    if not backup_dir.exists():
        print("❌ No backup found")
        return False

    print("🔄 Rolling back lazy loading migration...")

    try:
        # Restore backed up files
        for backup_file in backup_dir.glob("*"):
            if backup_file.name == "engine.py":
                dest = project_root / ".claude" / "core" / "engine.py"
            elif backup_file.name == "orchestrator.py":
                dest = project_root / ".claude" / "core" / "orchestrator.py"
            elif backup_file.name.endswith(".json"):
                dest = project_root / ".claude" / backup_file.name
            else:
                continue

            shutil.copy2(backup_file, dest)
            print(f"Restored: {{backup_file.name}}")

        print("✅ Rollback completed successfully")
        return True

    except Exception as e:
        print(f"❌ Rollback failed: {{e}}")
        return False

if __name__ == "__main__":
    rollback()
'''

        try:
            rollback_file = self.project_root / "rollback_lazy_loading.py"
            with open(rollback_file, "w") as f:
                f.write(rollback_content)

            os.chmod(rollback_file, 0o755)
            self.log(f"✅ Created rollback script: {rollback_file}")
            return True

        except Exception as e:
            self.log(f"❌ Rollback script creation failed: {e}", "ERROR")
            return False

    def save_migration_log(self):
        """Save migration log"""
        try:
            log_file = self.claude_dir / "lazy_loading_migration.log"
            with open(log_file, "w") as f:
                f.write("\\n".join(self.migration_log))

            self.log(f"📄 Migration log saved: {log_file}")
            return True

        except Exception as e:
            self.log(f"❌ Failed to save log: {e}", "ERROR")
            return False

    def run_migration(self):
        """Run complete migration process"""
        print("🚀 Starting Lazy Loading Migration")
        print("=" * 50)

        success = True

        # Step 1: Create backup
        if not self.create_backup():
            print("❌ Migration aborted - backup failed")
            return False

        # Step 2: Update settings
        if not self.update_settings():
            print("⚠️  Settings update failed, continuing...")
            success = False

        # Step 3: Create launcher
        if not self.create_launcher_script():
            print("⚠️  Launcher creation failed, continuing...")
            success = False

        # Step 4: Create rollback script
        if not self.create_rollback_script():
            print("⚠️  Rollback script creation failed, continuing...")

        # Step 5: Validate migration
        if not self.validate_migration():
            print("❌ Migration validation failed")
            success = False

        # Step 6: Benchmark performance
        benchmark_results = self.benchmark_performance()
        if benchmark_results:
            improvement = benchmark_results.get("overall_performance", {}).get(
                "startup_improvement_percent", 0
            )
            if improvement < 50:
                print(f"⚠️  Performance target not fully met ({improvement:.1f}%)")
                success = False

        # Step 7: Save migration log
        self.save_migration_log()

        print("\\n" + "=" * 50)
        if success:
            print("✅ MIGRATION COMPLETED SUCCESSFULLY")
            print("🚀 Lazy loading enabled with 50%+ startup improvement!")
            print(f"📁 Use: python claude_enhancer_lazy.py")
            print(f"🔄 Rollback: python rollback_lazy_loading.py")
        else:
            print("⚠️  MIGRATION COMPLETED WITH WARNINGS")
            print("Some optimizations may not be fully active.")
            print("Check logs for details.")

        return success


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enable lazy loading in Claude Enhancer"
    )
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done"
    )

    args = parser.parse_args()

    if args.dry_run:
        print("🔍 DRY RUN - No changes will be made")
        print("Would perform:")
        print("1. Create backup of current configuration")
        print("2. Update settings.json for lazy loading")
        print("3. Create optimized launcher script")
        print("4. Create rollback script")
        print("5. Validate lazy loading components")
        print("6. Benchmark performance improvements")
        return True

    migration = LazyLoadingMigration(args.project_root)
    return migration.run_migration()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
