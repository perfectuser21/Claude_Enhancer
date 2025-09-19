#!/usr/bin/env python3
"""
Perfect21 质量门数据模型
======================

定义质量门系统中使用的数据结构
"""

from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class GateStatus(Enum):
    """质量门状态"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class GateSeverity(Enum):
    """质量门严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class GateResult:
    """质量门检查结果"""
    gate_name: str
    status: GateStatus
    severity: GateSeverity
    score: float  # 0-100分
    message: str
    details: Dict[str, Any]
    violations: List[Dict[str, Any]]
    suggestions: List[str]
    execution_time: float
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class QualityGateConfig:
    """质量门配置"""
    # 代码质量阈值
    min_code_quality_score: float = 85.0
    max_complexity: int = 15
    max_duplications: float = 5.0

    # 测试覆盖率阈值
    min_line_coverage: float = 85.0
    min_branch_coverage: float = 80.0
    min_function_coverage: float = 90.0

    # 安全阈值
    max_security_issues: int = 0
    allowed_security_levels: List[str] = None

    # 性能阈值
    max_response_time_p95: float = 200.0  # ms
    max_memory_usage: float = 512.0  # MB
    min_throughput: float = 100.0  # requests/second

    # 架构阈值
    max_coupling_score: float = 0.3
    min_cohesion_score: float = 0.7
    max_cyclomatic_complexity: int = 10

    # 执行配置
    fail_fast: bool = False
    parallel_execution: bool = True
    timeout_seconds: int = 300

    def __post_init__(self):
        if self.allowed_security_levels is None:
            self.allowed_security_levels = ["low", "info"]