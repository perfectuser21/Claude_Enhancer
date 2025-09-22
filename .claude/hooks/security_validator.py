#!/usr/bin/env python3
"""
Claude Enhancer Security Validator
Validates commands for security risks before execution
"""

import sys
import os
import json
import re
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=os.getenv('CLAUDE_ENHANCER_LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_enhancer.security')

class SecurityValidator:
    """Security validation for commands and operations"""

    def __init__(self):
        self.blocked_commands = self._load_blocked_commands()
        self.protected_paths = self._load_protected_paths()
        self.sensitive_patterns = self._compile_sensitive_patterns()

    def _load_blocked_commands(self) -> List[re.Pattern]:
        """Load blocked command patterns"""
        patterns = [
            r"rm\s+-rf\s+/(?:\s|$)",  # rm -rf /
            r"rm\s+-rf\s+/\*",  # rm -rf /*
            r"sudo\s+rm\s+-rf",  # sudo rm -rf
            r"chmod\s+777",  # chmod 777
            r"chmod\s+-R\s+777",  # chmod -R 777
            r"curl.*\|\s*sh",  # curl | sh
            r"wget.*\|\s*bash",  # wget | bash
            r">\s*/dev/sda",  # Write to disk device
            r"dd\s+if=/dev/zero\s+of=/",  # Overwrite with zeros
            r"mkfs\.",  # Format filesystem
            r":()\s*{\s*:\|\s*:&\s*}",  # Fork bomb
            r"/dev/tcp/",  # Reverse shell
            r"nc\s+-l.*-e\s*/bin/",  # Netcat backdoor
            r"base64\s+-d.*\|\s*bash",  # Encoded payload execution
            r"eval\s*\$\(",  # Eval with command substitution
            r"python.*-c.*(__import__|eval|exec)",  # Python eval/exec
        ]
        return [re.compile(p, re.IGNORECASE) for p in patterns]

    def _load_protected_paths(self) -> List[str]:
        """Load protected system paths"""
        return [
            "/etc",
            "/usr",
            "/boot",
            "/sys",
            "/proc",
            "/dev",
            "/lib",
            "/lib64",
            "/bin",
            "/sbin",
            os.path.expanduser("~/.ssh"),
            os.path.expanduser("~/.aws"),
            os.path.expanduser("~/.config"),
            os.path.expanduser("~/.gnupg"),
        ]

    def _compile_sensitive_patterns(self) -> List[re.Pattern]:
        """Compile patterns for sensitive information"""
        patterns = [
            r"(password|passwd|pwd)\s*=\s*['\"]?[^'\"]+",  # Passwords
            r"(api[_-]?key|apikey)\s*=\s*['\"]?[^'\"]+",  # API keys
            r"(secret|token)\s*=\s*['\"]?[^'\"]+",  # Secrets/tokens
            r"(private[_-]?key)\s*=\s*['\"]?[^'\"]+",  # Private keys
            r"BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY",  # Private key blocks
            r"(aws[_-]?access[_-]?key[_-]?id)\s*=",  # AWS credentials
            r"(aws[_-]?secret[_-]?access[_-]?key)\s*=",  # AWS secrets
            r"mongodb://[^:]+:[^@]+@",  # MongoDB connection strings
            r"postgres://[^:]+:[^@]+@",  # PostgreSQL connection strings
            r"mysql://[^:]+:[^@]+@",  # MySQL connection strings
            r"[a-f0-9]{32}",  # Potential MD5 hashes
            r"[a-f0-9]{40}",  # Potential SHA1 hashes
            r"[a-f0-9]{64}",  # Potential SHA256 hashes
        ]
        return [re.compile(p, re.IGNORECASE) for p in patterns]

    def validate_command(self, command: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a command for security risks
        Returns: (is_safe, errors, warnings)
        """
        errors = []
        warnings = []

        # Check for blocked commands
        for pattern in self.blocked_commands:
            if pattern.search(command):
                errors.append(f"危险命令被阻止: {pattern.pattern}")

        # Check for operations on protected paths
        for path in self.protected_paths:
            # Check for direct operations on protected paths
            if re.search(rf"(rm|mv|chmod|chown).*\s+{re.escape(path)}(?:/|\s|$)", command):
                errors.append(f"不允许操作受保护路径: {path}")

            # Check for recursive operations that might affect protected paths
            if re.search(rf"(rm|chmod|chown).*-[rR].*{re.escape(os.path.dirname(path))}", command):
                warnings.append(f"递归操作可能影响受保护路径: {path}")

        # Check for sensitive information exposure
        for pattern in self.sensitive_patterns:
            if pattern.search(command):
                warnings.append("检测到可能的敏感信息，请确认是否应该包含在命令中")
                break

        # Check for sudo usage
        if re.search(r"^\s*sudo\s+", command):
            warnings.append("使用sudo需要特别注意权限")

        # Check for network operations
        if re.search(r"(curl|wget|nc|telnet|ssh)", command):
            warnings.append("网络操作请确认目标地址的安全性")

        # Check for script downloads
        if re.search(r"(curl|wget).*\.(sh|bash|py|rb|pl)(\s|$|\?)", command):
            errors.append("不允许直接下载和执行脚本")

        is_safe = len(errors) == 0

        return is_safe, errors, warnings

    def validate_file_operation(self, operation: str, file_path: str) -> Tuple[bool, str]:
        """
        Validate file operations
        Returns: (is_allowed, reason)
        """
        # Normalize path
        abs_path = os.path.abspath(os.path.expanduser(file_path))

        # Check if path is in protected locations
        for protected in self.protected_paths:
            if abs_path.startswith(protected):
                return False, f"路径 {abs_path} 在受保护区域"

        # Check for suspicious file extensions
        suspicious_extensions = ['.sh', '.bash', '.exe', '.dll', '.so', '.dylib']
        if any(abs_path.endswith(ext) for ext in suspicious_extensions):
            if operation in ['write', 'modify']:
                return False, f"不允许修改可执行文件: {abs_path}"

        # Check for hidden files in home directory
        if abs_path.startswith(os.path.expanduser("~/.")) and operation == 'delete':
            return False, f"不允许删除home目录下的隐藏文件: {abs_path}"

        return True, "操作允许"

    def scan_for_secrets(self, content: str) -> List[str]:
        """Scan content for potential secrets"""
        findings = []

        # Common secret patterns
        secret_patterns = [
            (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
            (r"[0-9a-zA-Z/+=]{40}", "AWS Secret Key (potential)"),
            (r"AIza[0-9A-Za-z\\-_]{35}", "Google API Key"),
            (r"sk_live_[0-9a-zA-Z]{24}", "Stripe Live Key"),
            (r"sk_test_[0-9a-zA-Z]{24}", "Stripe Test Key"),
            (r"github_pat_[0-9a-zA-Z]{22}_[0-9a-zA-Z]{59}", "GitHub Personal Access Token"),
            (r"ghp_[0-9a-zA-Z]{36}", "GitHub Personal Access Token"),
            (r"ghr_[0-9a-zA-Z]{36}", "GitHub Refresh Token"),
            (r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "UUID (potential secret)"),
        ]

        for pattern, description in secret_patterns:
            matches = re.findall(pattern, content)
            if matches:
                findings.append(f"{description}: Found {len(matches)} instance(s)")

        # Check for hardcoded passwords
        if re.search(r"password\s*=\s*['\"][^'\"]{6,}", content, re.IGNORECASE):
            findings.append("Hardcoded password detected")

        return findings

def main():
    """Main entry point for command validation"""
    if not sys.stdin.isatty():
        input_data = sys.stdin.read()
    else:
        input_data = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else ""

    if not input_data:
    # print("No input provided")
        sys.exit(0)

    validator = SecurityValidator()

    # Try to parse as JSON first (for structured input)
    try:
        data = json.loads(input_data)
        command = data.get('command', input_data)
    except json.JSONDecodeError:
        command = input_data

    # Validate the command
    is_safe, errors, warnings = validator.validate_command(command)

    # Output results
    if not is_safe:
    # print("🛑 安全验证失败")
        for error in errors:
    # print(f"  ❌ {error}")
        for warning in warnings:
    # print(f"  ⚠️ {warning}")

    # print("\n💡 建议:")
    # print("  • 检查命令是否包含危险操作")
    # print("  • 避免在受保护的系统目录执行操作")
    # print("  • 使用更安全的替代方案")

        logger.warning(f"Blocked command: {command[:100]}...")
        sys.exit(1)
    else:
        if warnings:
    # print("⚠️ 安全警告:")
            for warning in warnings:
    # print(f"  • {warning}")
    # print("\n命令将被执行，但请注意上述警告")
        else:
            logger.info(f"Command validated: {command[:50]}...")

        # Return success
        sys.exit(0)

if __name__ == "__main__":
    main()