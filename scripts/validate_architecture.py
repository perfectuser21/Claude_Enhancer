#!/usr/bin/env python3
"""
架构验证脚本
检查代码是否符合Perfect21架构规范
"""

import os
import ast
import sys
from pathlib import Path
from typing import Set, List, Dict, Tuple

class ArchitectureValidator:
    """架构验证器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.path.dirname(os.path.dirname(__file__)))

        # 定义层次结构
        self.layers = {
            "main": 4,      # 最高层
            "features": 3,  # 功能层
            "core": 2,      # 核心层
            "modules": 1    # 工具层
        }

        self.violations = []
        self.warnings = []

    def validate(self) -> bool:
        """执行验证"""
        print("🔍 Perfect21 架构验证")
        print("=" * 50)

        # 1. 检查目录结构
        self.check_directory_structure()

        # 2. 检查依赖关系
        self.check_dependencies()

        # 3. 检查命名规范
        self.check_naming_conventions()

        # 4. 检查接口实现
        self.check_interfaces()

        # 输出结果
        self.print_results()

        return len(self.violations) == 0

    def check_directory_structure(self):
        """检查目录结构"""
        print("\n📁 检查目录结构...")

        required_dirs = [
            "main",
            "features",
            "core",
            "modules",
            "tests",
            "config",
            "docs",
        ]

        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                self.violations.append(f"缺少必需目录: {dir_name}/")
            elif not dir_path.is_dir():
                self.violations.append(f"{dir_name} 不是目录")

    def check_dependencies(self):
        """检查依赖关系"""
        print("\n🔗 检查依赖关系...")

        for py_file in self.project_root.rglob("*.py"):
            if "archive" in str(py_file) or "venv" in str(py_file):
                continue

            layer = self.get_layer(py_file)
            if not layer:
                continue

            imports = self.get_imports(py_file)

            for import_path in imports:
                imported_layer = self.get_layer_from_import(import_path)
                if imported_layer and self.layers.get(imported_layer, 0) > self.layers.get(layer, 0):
                    self.violations.append(
                        f"依赖违规: {layer}/{py_file.name} 不能导入 {imported_layer} 层"
                    )

    def check_naming_conventions(self):
        """检查命名规范"""
        print("\n📝 检查命名规范...")

        for py_file in self.project_root.rglob("*.py"):
            if "archive" in str(py_file) or "venv" in str(py_file):
                continue

            # 文件名应该是snake_case
            if not self.is_snake_case(py_file.stem) and py_file.stem != "__init__":
                self.warnings.append(f"文件名不符合规范: {py_file.name} (应该用snake_case)")

            # 检查类名（应该是PascalCase）
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            if not self.is_pascal_case(node.name):
                                self.warnings.append(
                                    f"类名不符合规范: {py_file.name}:{node.name} (应该用PascalCase)"
                                )
            except:
                pass

    def check_interfaces(self):
        """检查接口实现"""
        print("\n🔌 检查接口实现...")

        interface_file = self.project_root / "core" / "interfaces.py"
        if not interface_file.exists():
            self.warnings.append("未找到接口定义文件: core/interfaces.py")
            return

        # 检查features是否实现了标准接口
        features_dir = self.project_root / "features"
        for feature_dir in features_dir.iterdir():
            if feature_dir.is_dir() and not feature_dir.name.startswith("_"):
                # 检查是否有__init__.py
                init_file = feature_dir / "__init__.py"
                if not init_file.exists():
                    self.warnings.append(f"Feature缺少__init__.py: {feature_dir.name}")

    def get_layer(self, file_path: Path) -> str:
        """获取文件所属层"""
        relative_path = file_path.relative_to(self.project_root)
        parts = relative_path.parts
        if parts and parts[0] in self.layers:
            return parts[0]
        return None

    def get_imports(self, file_path: Path) -> Set[str]:
        """获取文件的导入"""
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module)
        except:
            pass
        return imports

    def get_layer_from_import(self, import_path: str) -> str:
        """从导入路径获取层"""
        parts = import_path.split('.')
        if parts[0] in self.layers:
            return parts[0]
        return None

    def is_snake_case(self, name: str) -> bool:
        """检查是否是snake_case"""
        return name.islower() and ('_' in name or len(name.split('_')) == 1)

    def is_pascal_case(self, name: str) -> bool:
        """检查是否是PascalCase"""
        return name[0].isupper() and '_' not in name

    def print_results(self):
        """打印结果"""
        print("\n" + "=" * 50)
        print("📊 验证结果")

        if self.violations:
            print(f"\n❌ 发现 {len(self.violations)} 个违规:")
            for violation in self.violations:
                print(f"  • {violation}")

        if self.warnings:
            print(f"\n⚠️ 发现 {len(self.warnings)} 个警告:")
            for warning in self.warnings[:10]:  # 只显示前10个
                print(f"  • {warning}")
            if len(self.warnings) > 10:
                print(f"  ... 还有 {len(self.warnings) - 10} 个警告")

        if not self.violations and not self.warnings:
            print("\n✅ 完美！架构完全符合规范")
        elif not self.violations:
            print("\n✅ 通过！架构基本符合规范，但有一些小问题需要注意")
        else:
            print("\n❌ 失败！需要修复架构违规")

if __name__ == "__main__":
    validator = ArchitectureValidator()
    success = validator.validate()
    sys.exit(0 if success else 1)