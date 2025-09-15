#!/usr/bin/env python3
"""
语义化版本处理器
实现语义化版本规范 (Semantic Versioning 2.0.0)
"""

import re
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

@dataclass
class Version:
    """版本信息数据类"""
    major: int
    minor: int
    patch: int
    pre_release: Optional[str] = None
    build_metadata: Optional[str] = None

    def __str__(self) -> str:
        """转换为版本字符串"""
        version_str = f"{self.major}.{self.minor}.{self.patch}"

        if self.pre_release:
            version_str += f"-{self.pre_release}"

        if self.build_metadata:
            version_str += f"+{self.build_metadata}"

        return version_str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'major': self.major,
            'minor': self.minor,
            'patch': self.patch,
            'pre_release': self.pre_release,
            'build_metadata': self.build_metadata,
            'version_string': str(self)
        }

class SemanticVersion:
    """语义化版本处理器"""

    # 语义化版本正则表达式 (SemVer 2.0.0)
    SEMVER_PATTERN = re.compile(
        r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)'
        r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
        r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
        r'(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
    )

    @classmethod
    def parse(cls, version_string: str) -> Optional[Version]:
        """
        解析版本字符串

        Args:
            version_string: 版本字符串

        Returns:
            Optional[Version]: 解析后的版本对象，解析失败返回None
        """
        # 移除可能的 'v' 前缀
        if version_string.startswith('v'):
            version_string = version_string[1:]

        match = cls.SEMVER_PATTERN.match(version_string)
        if not match:
            return None

        return Version(
            major=int(match.group('major')),
            minor=int(match.group('minor')),
            patch=int(match.group('patch')),
            pre_release=match.group('prerelease'),
            build_metadata=match.group('buildmetadata')
        )

    @classmethod
    def is_valid(cls, version_string: str) -> bool:
        """
        验证版本字符串是否符合语义化版本规范

        Args:
            version_string: 版本字符串

        Returns:
            bool: 是否有效
        """
        return cls.parse(version_string) is not None

    @classmethod
    def compare(cls, version1: str, version2: str) -> int:
        """
        比较两个版本

        Args:
            version1: 版本1字符串
            version2: 版本2字符串

        Returns:
            int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        v1 = cls.parse(version1)
        v2 = cls.parse(version2)

        if not v1 or not v2:
            raise ValueError("Invalid version format")

        # 比较主版本号
        if v1.major != v2.major:
            return -1 if v1.major < v2.major else 1

        # 比较次版本号
        if v1.minor != v2.minor:
            return -1 if v1.minor < v2.minor else 1

        # 比较修订号
        if v1.patch != v2.patch:
            return -1 if v1.patch < v2.patch else 1

        # 比较预发布版本
        if v1.pre_release and v2.pre_release:
            return cls._compare_pre_release(v1.pre_release, v2.pre_release)
        elif v1.pre_release and not v2.pre_release:
            return -1  # 预发布版本 < 正式版本
        elif not v1.pre_release and v2.pre_release:
            return 1   # 正式版本 > 预发布版本

        return 0

    @classmethod
    def _compare_pre_release(cls, pre1: str, pre2: str) -> int:
        """比较预发布版本"""
        parts1 = pre1.split('.')
        parts2 = pre2.split('.')

        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else None
            p2 = parts2[i] if i < len(parts2) else None

            if p1 is None and p2 is not None:
                return -1
            elif p1 is not None and p2 is None:
                return 1
            elif p1 != p2:
                # 尝试数字比较
                try:
                    n1, n2 = int(p1), int(p2)
                    return -1 if n1 < n2 else 1
                except ValueError:
                    # 字符串比较
                    return -1 if p1 < p2 else 1

        return 0

    @classmethod
    def bump_version(cls, version_string: str, bump_type: str) -> str:
        """
        递增版本号

        Args:
            version_string: 当前版本字符串
            bump_type: 递增类型 ('major', 'minor', 'patch')

        Returns:
            str: 新版本字符串
        """
        version = cls.parse(version_string)
        if not version:
            raise ValueError(f"Invalid version format: {version_string}")

        if bump_type == 'major':
            return f"{version.major + 1}.0.0"
        elif bump_type == 'minor':
            return f"{version.major}.{version.minor + 1}.0"
        elif bump_type == 'patch':
            return f"{version.major}.{version.minor}.{version.patch + 1}"
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

    @classmethod
    def create_pre_release(cls, version_string: str, pre_type: str, number: int = 1) -> str:
        """
        创建预发布版本

        Args:
            version_string: 基础版本字符串
            pre_type: 预发布类型 ('alpha', 'beta', 'rc')
            number: 预发布版本号

        Returns:
            str: 预发布版本字符串
        """
        version = cls.parse(version_string)
        if not version:
            raise ValueError(f"Invalid version format: {version_string}")

        base_version = f"{version.major}.{version.minor}.{version.patch}"
        return f"{base_version}-{pre_type}.{number}"

    @classmethod
    def get_next_versions(cls, current_version: str) -> Dict[str, str]:
        """
        获取所有可能的下一个版本

        Args:
            current_version: 当前版本字符串

        Returns:
            Dict[str, str]: 各种递增类型对应的新版本
        """
        return {
            'major': cls.bump_version(current_version, 'major'),
            'minor': cls.bump_version(current_version, 'minor'),
            'patch': cls.bump_version(current_version, 'patch'),
            'alpha': cls.create_pre_release(current_version, 'alpha'),
            'beta': cls.create_pre_release(current_version, 'beta'),
            'rc': cls.create_pre_release(current_version, 'rc')
        }

    @classmethod
    def extract_version_info(cls, version_string: str) -> Dict[str, Any]:
        """
        提取版本详细信息

        Args:
            version_string: 版本字符串

        Returns:
            Dict[str, Any]: 版本详细信息
        """
        version = cls.parse(version_string)
        if not version:
            return {'valid': False, 'error': 'Invalid version format'}

        info = version.to_dict()
        info.update({
            'valid': True,
            'is_pre_release': version.pre_release is not None,
            'is_stable': version.pre_release is None,
            'version_tuple': (version.major, version.minor, version.patch),
            'next_versions': cls.get_next_versions(version_string)
        })

        return info

    @classmethod
    def format_for_git_tag(cls, version_string: str) -> str:
        """
        格式化为Git标签格式

        Args:
            version_string: 版本字符串

        Returns:
            str: Git标签格式 (v + 版本号)
        """
        if version_string.startswith('v'):
            return version_string
        return f"v{version_string}"

    @classmethod
    def get_version_range(cls, start_version: str, end_version: str) -> bool:
        """
        检查版本是否在指定范围内

        Args:
            start_version: 起始版本
            end_version: 结束版本

        Returns:
            bool: 是否在范围内
        """
        return (cls.compare(start_version, end_version) >= 0 and
                cls.compare(start_version, end_version) <= 0)

if __name__ == "__main__":
    # 测试示例
    print("语义化版本处理器测试:")

    # 解析测试
    versions = ["1.0.0", "2.1.3", "1.0.0-alpha.1", "2.0.0-beta.2+build.123"]
    for v in versions:
        parsed = SemanticVersion.parse(v)
        print(f"解析 {v}: {parsed}")

    # 比较测试
    comparisons = [
        ("1.0.0", "2.0.0"),
        ("2.1.0", "2.0.9"),
        ("1.0.0-alpha.1", "1.0.0"),
    ]
    for v1, v2 in comparisons:
        result = SemanticVersion.compare(v1, v2)
        op = "<" if result == -1 else ">" if result == 1 else "=="
        print(f"{v1} {op} {v2}")

    # 递增测试
    base_version = "1.2.3"
    for bump_type in ['major', 'minor', 'patch']:
        new_version = SemanticVersion.bump_version(base_version, bump_type)
        print(f"{base_version} -> {bump_type} -> {new_version}")