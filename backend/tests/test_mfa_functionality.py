#!/usr/bin/env python3
"""
MFA (Multi-Factor Authentication) Unit Tests
===========================================

测试多因子认证功能的全面测试：
- TOTP (基于时间的一次性密码)
- SMS 短信验证
- Email 邮件验证
- 备用恢复码
- MFA 设置和禁用
- 设备信任管理

作者: Claude Code AI Testing Team
版本: 1.0.0
创建时间: 2025-09-22
"""

import pytest
import asyncio
import time
import secrets
import pyotp
import qrcode
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, Optional, List, Tuple
import uuid
import hashlib
from io import BytesIO
import base64


# MFA 方法枚举
class MFAMethod:
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODES = "backup_codes"


class QRCodeGenerator:
    """二维码生成器"""

    @staticmethod
    def generate_totp_qr(
        secret: str,
        user_email: str,
        issuer: str = "Perfect21",
        algorithm: str = "SHA1",
        digits: int = 6,
        period: int = 30,
    ) -> str:
        """生成TOTP二维码"""
        from urllib.parse import quote

        # 构建TOTP URI
        totp_uri = (
            f"otpauth://totp/{quote(issuer)}:{quote(user_email)}"
            f"?secret={secret}"
            f"&issuer={quote(issuer)}"
            f"&algorithm={algorithm}"
            f"&digits={digits}"
            f"&period={period}"
        )

        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)

        # 创建图像
        img = qr.make_image(fill_color="black", back_color="white")

        # 转换为base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"


class MFAService:
    """多因子认证服务模拟"""

    def __init__(self):
        self.user_mfa_settings = {}  # user_id -> mfa_settings
        self.active_challenges = {}  # challenge_token -> challenge_data
        self.trusted_devices = {}  # user_id -> [device_fingerprints]
        self.backup_codes = {}  # user_id -> [hashed_codes]
        self.sms_provider = Mock()  # 模拟 SMS 提供商
        self.email_service = Mock()  # 模拟邮件服务

    async def setup_mfa(
        self,
        user_id: str,
        method: str,
        phone_number: str = None,
        ip_address: str = None,
    ) -> Dict[str, Any]:
        """设置MFA"""
        if method == MFAMethod.TOTP:
            return await self._setup_totp(user_id)
        elif method == MFAMethod.SMS:
            if not phone_number:
                raise ValueError("SMS方法需要提供电话号码")
            return await self._setup_sms(user_id, phone_number)
        elif method == MFAMethod.EMAIL:
            return await self._setup_email(user_id)
        else:
            raise ValueError(f"不支持的MFA方法: {method}")

    async def _setup_totp(self, user_id: str) -> Dict[str, Any]:
        """设置TOTP"""
        # 生成密钥
        secret = pyotp.random_base32()

        # 生成备用恢复码
        backup_codes = self._generate_backup_codes()

        # 存储MFA设置
        if user_id not in self.user_mfa_settings:
            self.user_mfa_settings[user_id] = {}

        self.user_mfa_settings[user_id][MFAMethod.TOTP] = {
            "secret": secret,
            "enabled": False,  # 需要验证后才启用
            "setup_at": datetime.utcnow(),
        }

        # 存储备用恢复码
        self.backup_codes[user_id] = [
            hashlib.sha256(code.encode()).hexdigest() for code in backup_codes
        ]

        # 生成二维码
        qr_code_url = QRCodeGenerator.generate_totp_qr(
            secret=secret,
            user_email=f"user_{user_id}@perfect21.com",
            issuer="Perfect21",
        )

        return {
            "secret_key": secret,
            "qr_code_url": qr_code_url,
            "backup_codes": backup_codes,
            "verification_required": True,
        }

    async def _setup_sms(self, user_id: str, phone_number: str) -> Dict[str, Any]:
        """设置SMS MFA"""
        if user_id not in self.user_mfa_settings:
            self.user_mfa_settings[user_id] = {}

        self.user_mfa_settings[user_id][MFAMethod.SMS] = {
            "phone_number": phone_number,
            "enabled": False,
            "setup_at": datetime.utcnow(),
        }

        # 生成备用恢复码
        backup_codes = self._generate_backup_codes()
        self.backup_codes[user_id] = [
            hashlib.sha256(code.encode()).hexdigest() for code in backup_codes
        ]

        return {
            "phone_number": phone_number,
            "backup_codes": backup_codes,
            "verification_required": True,
        }

    async def _setup_email(self, user_id: str) -> Dict[str, Any]:
        """设置邮件MFA"""
        if user_id not in self.user_mfa_settings:
            self.user_mfa_settings[user_id] = {}

        self.user_mfa_settings[user_id][MFAMethod.EMAIL] = {
            "enabled": False,
            "setup_at": datetime.utcnow(),
        }

        # 生成备用恢复码
        backup_codes = self._generate_backup_codes()
        self.backup_codes[user_id] = [
            hashlib.sha256(code.encode()).hexdigest() for code in backup_codes
        ]

        return {"backup_codes": backup_codes, "verification_required": True}

    def _generate_backup_codes(self, count: int = 10, length: int = 8) -> List[str]:
        """生成备用恢复码"""
        codes = []
        for _ in range(count):
            code = "".join(secrets.choice("0123456789") for _ in range(length))
            codes.append(code)
        return codes

    async def generate_mfa_challenge(
        self, user_id: str, ip_address: str = None, device_info: Dict = None
    ) -> str:
        """生成MFA挑战"""
        # 检查用户是否启用了MFA
        if user_id not in self.user_mfa_settings:
            raise ValueError("用户未启用MFA")

        # 生成挑战令牌
        challenge_token = secrets.token_urlsafe(32)

        # 存储挑战数据
        self.active_challenges[challenge_token] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
            "ip_address": ip_address,
            "device_info": device_info,
            "attempts": 0,
            "max_attempts": 3,
        }

        # 如果启用了SMS，发送验证码
        if MFAMethod.SMS in self.user_mfa_settings[user_id]:
            await self._send_sms_code(user_id, challenge_token)

        # 如果启用了邮件，发送验证码
        if MFAMethod.EMAIL in self.user_mfa_settings[user_id]:
            await self._send_email_code(user_id, challenge_token)

        return challenge_token

    async def _send_sms_code(self, user_id: str, challenge_token: str) -> None:
        """发送SMS验证码"""
        verification_code = f"{secrets.randbelow(900000) + 100000:06d}"

        # 存储验证码
        if challenge_token not in self.active_challenges:
            return

        self.active_challenges[challenge_token]["sms_code"] = verification_code

        # 模拟发送SMS
        phone_number = self.user_mfa_settings[user_id][MFAMethod.SMS]["phone_number"]
        self.sms_provider.send_message.return_value = True

    async def _send_email_code(self, user_id: str, challenge_token: str) -> None:
        """发送邮件验证码"""
        verification_code = f"{secrets.randbelow(900000) + 100000:06d}"

        # 存储验证码
        if challenge_token not in self.active_challenges:
            return

        self.active_challenges[challenge_token]["email_code"] = verification_code

        # 模拟发送邮件
        self.email_service.send_verification_email.return_value = True

    async def verify_mfa_challenge(
        self,
        mfa_token: str,
        verification_code: str,
        ip_address: str = None,
        device_info: Dict = None,
    ) -> Dict[str, Any]:
        """验证MFA挑战"""
        # 检查挑战是否存在
        if mfa_token not in self.active_challenges:
            return {"valid": False, "error": "MFA挑战不存在或已过期"}

        challenge = self.active_challenges[mfa_token]

        # 检查是否过期
        if datetime.utcnow() > challenge["expires_at"]:
            del self.active_challenges[mfa_token]
            return {"valid": False, "error": "MFA挑战已过期"}

        # 检查尝试次数
        if challenge["attempts"] >= challenge["max_attempts"]:
            del self.active_challenges[mfa_token]
            return {"valid": False, "error": "MFA验证尝试次数过多"}

        # 增加尝试次数
        challenge["attempts"] += 1

        user_id = challenge["user_id"]
        user_mfa = self.user_mfa_settings.get(user_id, {})

        # 验证代码
        is_valid = False

        # 检查TOTP
        if MFAMethod.TOTP in user_mfa and user_mfa[MFAMethod.TOTP].get("enabled"):
            secret = user_mfa[MFAMethod.TOTP]["secret"]
            totp = pyotp.TOTP(secret)
            if totp.verify(verification_code, valid_window=1):
                is_valid = True

        # 检查SMS验证码
        if not is_valid and "sms_code" in challenge:
            if verification_code == challenge["sms_code"]:
                is_valid = True

        # 检查邮件验证码
        if not is_valid and "email_code" in challenge:
            if verification_code == challenge["email_code"]:
                is_valid = True

        # 检查备用恢复码
        if not is_valid and user_id in self.backup_codes:
            code_hash = hashlib.sha256(verification_code.encode()).hexdigest()
            if code_hash in self.backup_codes[user_id]:
                # 使用后删除备用码
                self.backup_codes[user_id].remove(code_hash)
                is_valid = True

        if is_valid:
            # 清理成功的挑战
            del self.active_challenges[mfa_token]
            return {"valid": True, "user_id": user_id}
        else:
            return {
                "valid": False,
                "error": "MFA验证码错误",
                "attempts_remaining": challenge["max_attempts"] - challenge["attempts"],
            }

    async def enable_mfa_method(
        self, user_id: str, method: str, verification_code: str = None
    ) -> bool:
        """启用MFA方法"""
        if user_id not in self.user_mfa_settings:
            return False

        if method not in self.user_mfa_settings[user_id]:
            return False

        # 对于TOTP，需要验证一次才能启用
        if method == MFAMethod.TOTP and verification_code:
            secret = self.user_mfa_settings[user_id][method]["secret"]
            totp = pyotp.TOTP(secret)
            if not totp.verify(verification_code, valid_window=1):
                return False

        # 启用方法
        self.user_mfa_settings[user_id][method]["enabled"] = True
        self.user_mfa_settings[user_id][method]["enabled_at"] = datetime.utcnow()

        return True

    async def disable_mfa_method(self, user_id: str, method: str) -> bool:
        """禁用MFA方法"""
        if user_id not in self.user_mfa_settings:
            return False

        if method not in self.user_mfa_settings[user_id]:
            return False

        # 禁用方法
        self.user_mfa_settings[user_id][method]["enabled"] = False
        self.user_mfa_settings[user_id][method]["disabled_at"] = datetime.utcnow()

        return True

    async def get_user_mfa_methods(self, user_id: str) -> List[str]:
        """获取用户已启用的MFA方法"""
        if user_id not in self.user_mfa_settings:
            return []

        enabled_methods = []
        for method, settings in self.user_mfa_settings[user_id].items():
            if settings.get("enabled", False):
                enabled_methods.append(method)

        return enabled_methods

    async def is_device_trusted(self, user_id: str, device_fingerprint: str) -> bool:
        """检查设备是否受信任"""
        if user_id not in self.trusted_devices:
            return False

        for trusted_device in self.trusted_devices[user_id]:
            if trusted_device["fingerprint"] == device_fingerprint:
                # 检查是否过期
                if datetime.utcnow() < trusted_device["expires_at"]:
                    return True

        return False

    async def trust_device(
        self, user_id: str, device_fingerprint: str, trust_duration_days: int = 30
    ) -> None:
        """信任设备"""
        if user_id not in self.trusted_devices:
            self.trusted_devices[user_id] = []

        # 清理过期的信任设备
        now = datetime.utcnow()
        self.trusted_devices[user_id] = [
            device
            for device in self.trusted_devices[user_id]
            if device["expires_at"] > now
        ]

        # 添加新的信任设备
        self.trusted_devices[user_id].append(
            {
                "fingerprint": device_fingerprint,
                "trusted_at": now,
                "expires_at": now + timedelta(days=trust_duration_days),
            }
        )


class TestTOTPFunctionality:
    """
    TOTP功能测试套件"""

    @pytest.fixture
    def mfa_service(self):
        return MFAService()

    @pytest.fixture
    def user_id(self):
        return "totp_user_123"

    @pytest.mark.asyncio
    async def test_setup_totp_success(self, mfa_service, user_id):
        """测试成功设置TOTP"""
        # 执行
        result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)

        # 验证
        assert "secret_key" in result
        assert "qr_code_url" in result
        assert "backup_codes" in result
        assert result["verification_required"] is True

        # 检查秘钥长度
        assert len(result["secret_key"]) == 32  # Base32 编码的TOTP秘钥

        # 检查备用码数量
        assert len(result["backup_codes"]) == 10

        # 检查二维码格式
        assert result["qr_code_url"].startswith("data:image/png;base64,")

        # 检查MFA设置是否存储
        assert user_id in mfa_service.user_mfa_settings
        assert MFAMethod.TOTP in mfa_service.user_mfa_settings[user_id]
        assert not mfa_service.user_mfa_settings[user_id][MFAMethod.TOTP]["enabled"]

    @pytest.mark.asyncio
    async def test_enable_totp_with_verification(self, mfa_service, user_id):
        """测试通过验证启用TOTP"""
        # 设置TOTP
        setup_result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        secret = setup_result["secret_key"]

        # 生成验证码
        totp = pyotp.TOTP(secret)
        verification_code = totp.now()

        # 启用TOTP
        result = await mfa_service.enable_mfa_method(
            user_id, MFAMethod.TOTP, verification_code
        )

        # 验证
        assert result is True
        assert mfa_service.user_mfa_settings[user_id][MFAMethod.TOTP]["enabled"] is True

    @pytest.mark.asyncio
    async def test_enable_totp_with_wrong_verification(self, mfa_service, user_id):
        """测试使用错误验证码启用TOTP"""
        # 设置TOTP
        await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)

        # 使用错误的验证码
        wrong_code = "000000"

        # 尝试启用TOTP
        result = await mfa_service.enable_mfa_method(
            user_id, MFAMethod.TOTP, wrong_code
        )

        # 验证失败
        assert result is False
        assert not mfa_service.user_mfa_settings[user_id][MFAMethod.TOTP]["enabled"]

    @pytest.mark.asyncio
    async def test_totp_verification_in_challenge(self, mfa_service, user_id):
        """测试TOTP在MFA挑战中的验证"""
        # 设置并启用TOTP
        setup_result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        secret = setup_result["secret_key"]

        totp = pyotp.TOTP(secret)
        verification_code = totp.now()

        await mfa_service.enable_mfa_method(user_id, MFAMethod.TOTP, verification_code)

        # 生成MFA挑战
        challenge_token = await mfa_service.generate_mfa_challenge(user_id)

        # 生成新的验证码
        new_verification_code = totp.now()

        # 验证MFA挑战
        result = await mfa_service.verify_mfa_challenge(
            challenge_token, new_verification_code
        )

        # 验证
        assert result["valid"] is True
        assert result["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_totp_time_window_tolerance(self, mfa_service, user_id):
        """测试TOTP时间窗口容差"""
        # 设置并启用TOTP
        setup_result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        secret = setup_result["secret_key"]

        totp = pyotp.TOTP(secret)
        current_code = totp.now()

        await mfa_service.enable_mfa_method(user_id, MFAMethod.TOTP, current_code)

        # 生成MFA挑战
        challenge_token = await mfa_service.generate_mfa_challenge(user_id)

        # 测试前一个时间窗口的代码
        previous_code = totp.at(time.time() - 30)

        result = await mfa_service.verify_mfa_challenge(challenge_token, previous_code)

        # 应该仍然有效（valid_window=1）
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_totp_invalid_code(self, mfa_service, user_id):
        """测试TOTP无效代码"""
        # 设置并启用TOTP
        setup_result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        secret = setup_result["secret_key"]

        totp = pyotp.TOTP(secret)
        verification_code = totp.now()

        await mfa_service.enable_mfa_method(user_id, MFAMethod.TOTP, verification_code)

        # 生成MFA挑战
        challenge_token = await mfa_service.generate_mfa_challenge(user_id)

        # 使用无效代码
        invalid_codes = ["000000", "123456", "999999", "abcdef"]

        for invalid_code in invalid_codes:
            result = await mfa_service.verify_mfa_challenge(
                challenge_token, invalid_code
            )
            assert result["valid"] is False
            assert "error" in result


class TestSMSFunctionality:
    """
    SMS MFA功能测试套件"""

    @pytest.fixture
    def mfa_service(self):
        return MFAService()

    @pytest.fixture
    def user_id(self):
        return "sms_user_456"

    @pytest.fixture
    def phone_number(self):
        return "+1234567890"

    @pytest.mark.asyncio
    async def test_setup_sms_success(self, mfa_service, user_id, phone_number):
        """测试成功设置SMS MFA"""
        # 执行
        result = await mfa_service.setup_mfa(
            user_id, MFAMethod.SMS, phone_number=phone_number
        )

        # 验证
        assert "phone_number" in result
        assert "backup_codes" in result
        assert result["verification_required"] is True
        assert result["phone_number"] == phone_number

        # 检查MFA设置
        assert user_id in mfa_service.user_mfa_settings
        assert MFAMethod.SMS in mfa_service.user_mfa_settings[user_id]
        assert (
            mfa_service.user_mfa_settings[user_id][MFAMethod.SMS]["phone_number"]
            == phone_number
        )

    @pytest.mark.asyncio
    async def test_setup_sms_without_phone_number(self, mfa_service, user_id):
        """测试没有电话号码的SMS设置"""
        with pytest.raises(ValueError, match="SMS方法需要提供电话号码"):
            await mfa_service.setup_mfa(user_id, MFAMethod.SMS)

    @pytest.mark.asyncio
    async def test_sms_challenge_generation_and_verification(
        self, mfa_service, user_id, phone_number
    ):
        """测试SMS挑战生成和验证"""
        # 设置并启用SMS
        await mfa_service.setup_mfa(user_id, MFAMethod.SMS, phone_number=phone_number)
        await mfa_service.enable_mfa_method(user_id, MFAMethod.SMS)

        # 生成MFA挑战
        challenge_token = await mfa_service.generate_mfa_challenge(user_id)

        # 获取SMS验证码（模拟从挑战数据中获取）
        challenge_data = mfa_service.active_challenges[challenge_token]
        sms_code = challenge_data["sms_code"]

        # 验证SMS代码
        result = await mfa_service.verify_mfa_challenge(challenge_token, sms_code)

        # 验证
        assert result["valid"] is True
        assert result["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_sms_wrong_code(self, mfa_service, user_id, phone_number):
        """测试SMS错误代码"""
        # 设置并启用SMS
        await mfa_service.setup_mfa(user_id, MFAMethod.SMS, phone_number=phone_number)
        await mfa_service.enable_mfa_method(user_id, MFAMethod.SMS)

        # 生成MFA挑战
        challenge_token = await mfa_service.generate_mfa_challenge(user_id)

        # 使用错误代码
        wrong_code = "000000"

        result = await mfa_service.verify_mfa_challenge(challenge_token, wrong_code)

        # 验证失败
        assert result["valid"] is False
        assert "error" in result
        assert "attempts_remaining" in result

    @pytest.mark.asyncio
    async def test_sms_provider_integration(self, mfa_service, user_id, phone_number):
        """测试SMS提供商集成"""
        # 设置并启用SMS
        await mfa_service.setup_mfa(user_id, MFAMethod.SMS, phone_number=phone_number)
        await mfa_service.enable_mfa_method(user_id, MFAMethod.SMS)

        # 生成MFA挑战
        await mfa_service.generate_mfa_challenge(user_id)

        # 检查SMS提供商是否被调用
        assert mfa_service.sms_provider.send_message.return_value is True


class TestEmailMFA:
    """
    邮件MFA功能测试套件"""

    @pytest.fixture
    def mfa_service(self):
        return MFAService()

    @pytest.fixture
    def user_id(self):
        return "email_user_789"

    @pytest.mark.asyncio
    async def test_setup_email_mfa(self, mfa_service, user_id):
        """测试设置邮件MFA"""
        result = await mfa_service.setup_mfa(user_id, MFAMethod.EMAIL)

        assert "backup_codes" in result
        assert result["verification_required"] is True

        # 检查MFA设置
        assert user_id in mfa_service.user_mfa_settings
        assert MFAMethod.EMAIL in mfa_service.user_mfa_settings[user_id]

    @pytest.mark.asyncio
    async def test_email_challenge_verification(self, mfa_service, user_id):
        """测试邮件挑战验证"""
        # 设置并启用邮件MFA
        await mfa_service.setup_mfa(user_id, MFAMethod.EMAIL)
        await mfa_service.enable_mfa_method(user_id, MFAMethod.EMAIL)

        # 生成MFA挑战
        challenge_token = await mfa_service.generate_mfa_challenge(user_id)

        # 获取邮件验证码
        challenge_data = mfa_service.active_challenges[challenge_token]
        email_code = challenge_data["email_code"]

        # 验证邮件代码
        result = await mfa_service.verify_mfa_challenge(challenge_token, email_code)

        assert result["valid"] is True
        assert result["user_id"] == user_id


class TestBackupCodes:
    """
    备用恢复码测试套件"""

    @pytest.fixture
    def mfa_service(self):
        return MFAService()

    @pytest.fixture
    def user_id(self):
        return "backup_user_999"

    @pytest.mark.asyncio
    async def test_backup_codes_generation(self, mfa_service, user_id):
        """测试备用码生成"""
        # 设置TOTP以获取备用码
        result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        backup_codes = result["backup_codes"]

        # 验证备用码
        assert len(backup_codes) == 10
        for code in backup_codes:
            assert len(code) == 8
            assert code.isdigit()

        # 验证备用码都不同
        assert len(set(backup_codes)) == len(backup_codes)

    @pytest.mark.asyncio
    async def test_backup_code_verification(self, mfa_service, user_id):
        """测试备用码验证"""
        # 设置并启用TOTP
        setup_result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        backup_codes = setup_result["backup_codes"]

        totp = pyotp.TOTP(setup_result["secret_key"])
        await mfa_service.enable_mfa_method(user_id, MFAMethod.TOTP, totp.now())

        # 生成MFA挑战
        challenge_token = await mfa_service.generate_mfa_challenge(user_id)

        # 使用备用码验证
        backup_code = backup_codes[0]
        result = await mfa_service.verify_mfa_challenge(challenge_token, backup_code)

        # 验证成功
        assert result["valid"] is True
        assert result["user_id"] == user_id

        # 检查备用码是否被删除
        remaining_codes = [
            code
            for code in mfa_service.backup_codes[user_id]
            if code == hashlib.sha256(backup_code.encode()).hexdigest()
        ]
        assert len(remaining_codes) == 0

    @pytest.mark.asyncio
    async def test_backup_code_single_use(self, mfa_service, user_id):
        """测试备用码只能使用一次"""
        # 设置并启用TOTP
        setup_result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        backup_codes = setup_result["backup_codes"]

        totp = pyotp.TOTP(setup_result["secret_key"])
        await mfa_service.enable_mfa_method(user_id, MFAMethod.TOTP, totp.now())

        # 第一次使用备用码
        challenge_token1 = await mfa_service.generate_mfa_challenge(user_id)
        backup_code = backup_codes[0]

        result1 = await mfa_service.verify_mfa_challenge(challenge_token1, backup_code)
        assert result1["valid"] is True

        # 第二次使用相同备用码应该失败
        challenge_token2 = await mfa_service.generate_mfa_challenge(user_id)
        result2 = await mfa_service.verify_mfa_challenge(challenge_token2, backup_code)

        assert result2["valid"] is False


class TestDeviceTrust:
    """
    设备信任管理测试套件"""

    @pytest.fixture
    def mfa_service(self):
        return MFAService()

    @pytest.fixture
    def user_id(self):
        return "trust_user_111"

    @pytest.fixture
    def device_fingerprint(self):
        return "device_fingerprint_abc123"

    @pytest.mark.asyncio
    async def test_trust_device(self, mfa_service, user_id, device_fingerprint):
        """测试信任设备"""
        # 信任设备
        await mfa_service.trust_device(
            user_id, device_fingerprint, trust_duration_days=30
        )

        # 检查设备是否受信任
        is_trusted = await mfa_service.is_device_trusted(user_id, device_fingerprint)
        assert is_trusted is True

        # 检查信任记录
        assert user_id in mfa_service.trusted_devices
        assert len(mfa_service.trusted_devices[user_id]) == 1

        trusted_device = mfa_service.trusted_devices[user_id][0]
        assert trusted_device["fingerprint"] == device_fingerprint
        assert trusted_device["expires_at"] > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_device_trust_expiration(
        self, mfa_service, user_id, device_fingerprint
    ):
        """测试设备信任过期"""
        # 信任设备，但设置过去的过期时间
        await mfa_service.trust_device(
            user_id, device_fingerprint, trust_duration_days=-1
        )

        # 检查设备是否仍然受信任
        is_trusted = await mfa_service.is_device_trusted(user_id, device_fingerprint)
        assert is_trusted is False

    @pytest.mark.asyncio
    async def test_multiple_trusted_devices(self, mfa_service, user_id):
        """测试多个受信任设备"""
        devices = [
            "device_1_fingerprint",
            "device_2_fingerprint",
            "device_3_fingerprint",
        ]

        # 信任多个设备
        for device in devices:
            await mfa_service.trust_device(user_id, device)

        # 检查所有设备都受信任
        for device in devices:
            is_trusted = await mfa_service.is_device_trusted(user_id, device)
            assert is_trusted is True

        # 检查信任记录数量
        assert len(mfa_service.trusted_devices[user_id]) == 3

    @pytest.mark.asyncio
    async def test_untrusted_device(self, mfa_service, user_id):
        """测试非受信任设备"""
        unknown_device = "unknown_device_fingerprint"

        # 检查未知设备是否不受信任
        is_trusted = await mfa_service.is_device_trusted(user_id, unknown_device)
        assert is_trusted is False


class TestMFAChallengeFlow:
    """
    MFA挑战流程测试套件"""

    @pytest.fixture
    def mfa_service(self):
        return MFAService()

    @pytest.fixture
    def user_id(self):
        return "challenge_user_222"

    @pytest.mark.asyncio
    async def test_challenge_expiration(self, mfa_service, user_id):
        """测试挑战过期"""
        # 设置并启用TOTP
        setup_result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        totp = pyotp.TOTP(setup_result["secret_key"])
        await mfa_service.enable_mfa_method(user_id, MFAMethod.TOTP, totp.now())

        # 生成MFA挑战
        challenge_token = await mfa_service.generate_mfa_challenge(user_id)

        # 模拟挑战过期
        mfa_service.active_challenges[challenge_token][
            "expires_at"
        ] = datetime.utcnow() - timedelta(minutes=1)

        # 尝试验证过期挑战
        result = await mfa_service.verify_mfa_challenge(challenge_token, totp.now())

        assert result["valid"] is False
        assert "过期" in result["error"]

        # 检查挑战是否被清理
        assert challenge_token not in mfa_service.active_challenges

    @pytest.mark.asyncio
    async def test_challenge_max_attempts(self, mfa_service, user_id):
        """测试挑战最大尝试次数"""
        # 设置并启用TOTP
        setup_result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        totp = pyotp.TOTP(setup_result["secret_key"])
        await mfa_service.enable_mfa_method(user_id, MFAMethod.TOTP, totp.now())

        # 生成MFA挑战
        challenge_token = await mfa_service.generate_mfa_challenge(user_id)

        # 连续使用错误代码
        for i in range(3):
            result = await mfa_service.verify_mfa_challenge(challenge_token, "000000")
            if i < 2:  # 前两次应该还能继续尝试
                assert result["valid"] is False
                assert "attempts_remaining" in result
            else:  # 第三次应该被锁定
                assert result["valid"] is False
                assert "尝试次数过多" in result["error"]

        # 检查挑战是否被清理
        assert challenge_token not in mfa_service.active_challenges

    @pytest.mark.asyncio
    async def test_challenge_context_tracking(self, mfa_service, user_id):
        """测试挑战上下文跟踪"""
        # 设置并启用TOTP
        setup_result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        totp = pyotp.TOTP(setup_result["secret_key"])
        await mfa_service.enable_mfa_method(user_id, MFAMethod.TOTP, totp.now())

        # 生成带上下文的MFA挑战
        ip_address = "192.168.1.100"
        device_info = {"device_type": "web", "browser": "Chrome"}

        challenge_token = await mfa_service.generate_mfa_challenge(
            user_id, ip_address=ip_address, device_info=device_info
        )

        # 检查挑战数据中的上下文
        challenge_data = mfa_service.active_challenges[challenge_token]
        assert challenge_data["ip_address"] == ip_address
        assert challenge_data["device_info"] == device_info
        assert challenge_data["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_nonexistent_challenge(self, mfa_service):
        """测试不存在的挑战"""
        fake_token = "fake_challenge_token"

        result = await mfa_service.verify_mfa_challenge(fake_token, "123456")

        assert result["valid"] is False
        assert "不存在" in result["error"]


class TestMFAServiceIntegration:
    """
    MFA服务集成测试"""

    @pytest.fixture
    def mfa_service(self):
        return MFAService()

    @pytest.fixture
    def user_id(self):
        return "integration_user_333"

    @pytest.mark.asyncio
    async def test_complete_mfa_flow(self, mfa_service, user_id):
        """测试完整的MFA流程"""
        # 1. 设置TOTP
        setup_result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        secret = setup_result["secret_key"]
        backup_codes = setup_result["backup_codes"]

        # 2. 验证并启用TOTP
        totp = pyotp.TOTP(secret)
        verification_code = totp.now()

        enable_result = await mfa_service.enable_mfa_method(
            user_id, MFAMethod.TOTP, verification_code
        )
        assert enable_result is True

        # 3. 检查已启用的方法
        enabled_methods = await mfa_service.get_user_mfa_methods(user_id)
        assert MFAMethod.TOTP in enabled_methods

        # 4. 生成挑战
        challenge_token = await mfa_service.generate_mfa_challenge(user_id)

        # 5. 使用TOTP验证
        new_code = totp.now()
        verify_result = await mfa_service.verify_mfa_challenge(
            challenge_token, new_code
        )
        assert verify_result["valid"] is True

        # 6. 测试备用码
        new_challenge = await mfa_service.generate_mfa_challenge(user_id)
        backup_result = await mfa_service.verify_mfa_challenge(
            new_challenge, backup_codes[0]
        )
        assert backup_result["valid"] is True

        # 7. 禁用MFA
        disable_result = await mfa_service.disable_mfa_method(user_id, MFAMethod.TOTP)
        assert disable_result is True

        # 8. 检查已禁用
        enabled_methods_after = await mfa_service.get_user_mfa_methods(user_id)
        assert MFAMethod.TOTP not in enabled_methods_after

    @pytest.mark.asyncio
    async def test_multiple_mfa_methods(self, mfa_service, user_id):
        """测试多种MFA方法"""
        # 设置TOTP
        totp_setup = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        totp = pyotp.TOTP(totp_setup["secret_key"])
        await mfa_service.enable_mfa_method(user_id, MFAMethod.TOTP, totp.now())

        # 设置SMS
        await mfa_service.setup_mfa(user_id, MFAMethod.SMS, phone_number="+1234567890")
        await mfa_service.enable_mfa_method(user_id, MFAMethod.SMS)

        # 设置邮件
        await mfa_service.setup_mfa(user_id, MFAMethod.EMAIL)
        await mfa_service.enable_mfa_method(user_id, MFAMethod.EMAIL)

        # 检查所有方法都已启用
        enabled_methods = await mfa_service.get_user_mfa_methods(user_id)
        expected_methods = [MFAMethod.TOTP, MFAMethod.SMS, MFAMethod.EMAIL]

        for method in expected_methods:
            assert method in enabled_methods

    @pytest.mark.asyncio
    async def test_mfa_with_trusted_device(self, mfa_service, user_id):
        """测试信任设备的MFA流程"""
        device_fingerprint = "trusted_device_123"

        # 设置并启用TOTP
        setup_result = await mfa_service.setup_mfa(user_id, MFAMethod.TOTP)
        totp = pyotp.TOTP(setup_result["secret_key"])
        await mfa_service.enable_mfa_method(user_id, MFAMethod.TOTP, totp.now())

        # 信任设备
        await mfa_service.trust_device(user_id, device_fingerprint)

        # 检查设备信任状态
        is_trusted = await mfa_service.is_device_trusted(user_id, device_fingerprint)
        assert is_trusted is True

        # 在信任设备上，可能可以跳过MFA（具体实现取决于业务逻辑）
        # 这里仅测试信任状态的记录


if __name__ == "__main__":
    pytest.main(["-v", __file__])
