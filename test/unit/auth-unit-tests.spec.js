/**
 * 用户认证系统 - 单元测试套件
 * 目标覆盖率: >90%
 *
 * 测试哲学: 每个函数都像乐高积木 - 单独测试确保每块都完美
 */

const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const {
  hashPassword,
  verifyPassword,
  generateJWT,
  verifyJWT,
  validateEmail,
  validatePassword,
  sanitizeInput,
  rateLimit
} = require('../../src/auth/auth-utils');

describe('Authentication Utils - Unit Tests', () => {

  // =============================================
  // 密码哈希与验证测试 (Password Hashing & Verification)
  // =============================================

  describe('Password Security', () => {

    describe('hashPassword()', () => {
      test('should hash password with bcrypt', async () => {
        // Arrange (准备) - 像准备食材
        const plainPassword = 'SecurePass123!';

        // Act (执行) - 像烹饪过程
        const hashedPassword = await hashPassword(plainPassword);

        // Assert (断言) - 像品尝结果
        expect(hashedPassword).toBeDefined();
        expect(hashedPassword).not.toBe(plainPassword);
        expect(hashedPassword.length).toBeGreaterThan(50); // bcrypt hash长度检查
        expect(hashedPassword.startsWith('$2b$')).toBe(true); // bcrypt格式检查
      });

      test('should generate different hashes for same password', async () => {
        const password = 'SamePassword123!';

        const hash1 = await hashPassword(password);
        const hash2 = await hashPassword(password);

        expect(hash1).not.toBe(hash2); // 盐值确保每次不同
      });

      test('should handle empty password gracefully', async () => {
        await expect(hashPassword('')).rejects.toThrow('Password cannot be empty');
      });

      test('should handle null/undefined password', async () => {
        await expect(hashPassword(null)).rejects.toThrow('Invalid password input');
        await expect(hashPassword(undefined)).rejects.toThrow('Invalid password input');
      });
    });

    describe('verifyPassword()', () => {
      test('should verify correct password', async () => {
        const password = 'CorrectPassword123!';
        const hashedPassword = await hashPassword(password);

        const isValid = await verifyPassword(password, hashedPassword);

        expect(isValid).toBe(true);
      });

      test('should reject incorrect password', async () => {
        const correctPassword = 'CorrectPassword123!';
        const wrongPassword = 'WrongPassword123!';
        const hashedPassword = await hashPassword(correctPassword);

        const isValid = await verifyPassword(wrongPassword, hashedPassword);

        expect(isValid).toBe(false);
      });

      test('should handle malformed hash', async () => {
        const password = 'AnyPassword123!';
        const malformedHash = 'not-a-real-hash';

        await expect(verifyPassword(password, malformedHash))
          .rejects.toThrow('Invalid hash format');
      });
    });
  });

  // =============================================
  // JWT令牌测试 (JWT Token Tests)
  // =============================================

  describe('JWT Token Management', () => {

    describe('generateJWT()', () => {
      test('should generate valid JWT token', () => {
        // Arrange
        const payload = {
          userId: 'user123',
          email: 'test@example.com',
          role: 'user'
        };
        const secret = 'test-secret-key';
        const expiresIn = '1h';

        // Act
        const token = generateJWT(payload, secret, expiresIn);

        // Assert
        expect(token).toBeDefined();
        expect(typeof token).toBe('string');
        expect(token.split('.')).toHaveLength(3); // JWT格式: header.payload.signature
      });

      test('should include correct payload in token', () => {
        const payload = { userId: 'user456', role: 'admin' };
        const secret = 'test-secret';

        const token = generateJWT(payload, secret);
        const decoded = jwt.decode(token);

        expect(decoded.userId).toBe('user456');
        expect(decoded.role).toBe('admin');
        expect(decoded.iat).toBeDefined(); // issued at
        expect(decoded.exp).toBeDefined(); // expires at
      });

      test('should set correct expiration time', () => {
        const payload = { userId: 'user789' };
        const secret = 'test-secret';
        const expiresIn = '2h';

        const token = generateJWT(payload, secret, expiresIn);
        const decoded = jwt.decode(token);

        const expectedExp = Math.floor(Date.now() / 1000) + (2 * 60 * 60); // 2小时后
        expect(decoded.exp).toBeCloseTo(expectedExp, -2); // 允许2秒误差
      });
    });

    describe('verifyJWT()', () => {
      test('should verify valid token', () => {
        const payload = { userId: 'user999' };
        const secret = 'verification-secret';

        const token = generateJWT(payload, secret);
        const verified = verifyJWT(token, secret);

        expect(verified.userId).toBe('user999');
        expect(verified.iat).toBeDefined();
        expect(verified.exp).toBeDefined();
      });

      test('should reject token with wrong secret', () => {
        const payload = { userId: 'user888' };
        const correctSecret = 'correct-secret';
        const wrongSecret = 'wrong-secret';

        const token = generateJWT(payload, correctSecret);

        expect(() => verifyJWT(token, wrongSecret))
          .toThrow('Invalid token signature');
      });

      test('should reject expired token', () => {
        const payload = { userId: 'user777' };
        const secret = 'test-secret';
        const expiresIn = '-1h'; // 过期时间设为过去

        const token = generateJWT(payload, secret, expiresIn);

        expect(() => verifyJWT(token, secret))
          .toThrow('Token has expired');
      });

      test('should reject malformed token', () => {
        const malformedToken = 'not.a.valid.jwt.token';
        const secret = 'test-secret';

        expect(() => verifyJWT(malformedToken, secret))
          .toThrow('Invalid token format');
      });
    });
  });

  // =============================================
  // 输入验证测试 (Input Validation Tests)
  // =============================================

  describe('Input Validation', () => {

    describe('validateEmail()', () => {
      test('should validate correct email formats', () => {
        const validEmails = [
          'test@example.com',
          'user.name@domain.co.uk',
          'user+tag@example.org',
          'user123@sub.domain.com'
        ];

        validEmails.forEach(email => {
          expect(validateEmail(email)).toBe(true);
        });
      });

      test('should reject invalid email formats', () => {
        const invalidEmails = [
          'invalid-email',
          '@example.com',
          'user@',
          'user@.com',
          'user..name@example.com',
          'user name@example.com', // 空格
          'user@exam ple.com'
        ];

        invalidEmails.forEach(email => {
          expect(validateEmail(email)).toBe(false);
        });
      });

      test('should handle edge cases', () => {
        expect(validateEmail('')).toBe(false);
        expect(validateEmail(null)).toBe(false);
        expect(validateEmail(undefined)).toBe(false);
      });
    });

    describe('validatePassword()', () => {
      test('should validate strong passwords', () => {
        const strongPasswords = [
          'StrongPass123!',
          'MyP@ssw0rd',
          'Secure#2023',
          'Complex$Pass1'
        ];

        strongPasswords.forEach(password => {
          const result = validatePassword(password);
          expect(result.isValid).toBe(true);
          expect(result.strength).toBeGreaterThanOrEqual(80);
        });
      });

      test('should reject weak passwords', () => {
        const weakPasswords = [
          'password',      // 太简单
          '123456',        // 纯数字
          'abcdefgh',      // 纯字母
          'Pass1',         // 太短
          'PASSWORD123'    // 缺少特殊字符
        ];

        weakPasswords.forEach(password => {
          const result = validatePassword(password);
          expect(result.isValid).toBe(false);
          expect(result.errors).toBeInstanceOf(Array);
          expect(result.errors.length).toBeGreaterThan(0);
        });
      });

      test('should provide detailed validation feedback', () => {
        const weakPassword = 'weak';
        const result = validatePassword(weakPassword);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Password too short (minimum 8 characters)');
        expect(result.errors).toContain('Missing uppercase letter');
        expect(result.errors).toContain('Missing number');
        expect(result.errors).toContain('Missing special character');
      });
    });

    describe('sanitizeInput()', () => {
      test('should remove dangerous characters', () => {
        const dangerousInput = '<script>alert("XSS")</script>';
        const sanitized = sanitizeInput(dangerousInput);

        expect(sanitized).not.toContain('<script>');
        expect(sanitized).not.toContain('</script>');
      });

      test('should preserve safe content', () => {
        const safeInput = 'Normal user input with numbers 123 and symbols !@#';
        const sanitized = sanitizeInput(safeInput);

        expect(sanitized).toBe(safeInput);
      });

      test('should handle SQL injection attempts', () => {
        const sqlInjection = "'; DROP TABLE users; --";
        const sanitized = sanitizeInput(sqlInjection);

        expect(sanitized).not.toContain('DROP TABLE');
        expect(sanitized).not.toContain('--');
      });
    });
  });

  // =============================================
  // 速率限制测试 (Rate Limiting Tests)
  // =============================================

  describe('Rate Limiting', () => {

    describe('rateLimit()', () => {
      beforeEach(() => {
        // 每个测试前清除速率限制缓存
        rateLimit.clearCache();
      });

      test('should allow requests within limit', async () => {
        const clientId = 'test-client-1';
        const limit = 5;
        const windowMs = 60000; // 1分钟

        // 执行限制内的请求
        for (let i = 0; i < limit; i++) {
          const result = await rateLimit.check(clientId, limit, windowMs);
          expect(result.allowed).toBe(true);
          expect(result.remaining).toBe(limit - i - 1);
        }
      });

      test('should block requests exceeding limit', async () => {
        const clientId = 'test-client-2';
        const limit = 3;
        const windowMs = 60000;

        // 执行到达限制的请求
        for (let i = 0; i < limit; i++) {
          await rateLimit.check(clientId, limit, windowMs);
        }

        // 超出限制的请求应被阻止
        const exceededResult = await rateLimit.check(clientId, limit, windowMs);
        expect(exceededResult.allowed).toBe(false);
        expect(exceededResult.remaining).toBe(0);
        expect(exceededResult.resetTime).toBeDefined();
      });

      test('should reset after time window', async () => {
        const clientId = 'test-client-3';
        const limit = 2;
        const windowMs = 100; // 100ms窗口期便于测试

        // 用完所有请求
        await rateLimit.check(clientId, limit, windowMs);
        await rateLimit.check(clientId, limit, windowMs);

        // 验证被阻止
        const blockedResult = await rateLimit.check(clientId, limit, windowMs);
        expect(blockedResult.allowed).toBe(false);

        // 等待窗口期结束
        await new Promise(resolve => setTimeout(resolve, 150));

        // 验证重置后可以再次请求
        const resetResult = await rateLimit.check(clientId, limit, windowMs);
        expect(resetResult.allowed).toBe(true);
        expect(resetResult.remaining).toBe(limit - 1);
      });
    });
  });
});

// =============================================
// 测试覆盖率报告配置
// =============================================

/*
覆盖率目标:
- 语句覆盖率: ≥ 95%
- 分支覆盖率: ≥ 90%
- 函数覆盖率: ≥ 95%
- 行覆盖率: ≥ 95%

运行命令:
npm test -- --coverage --collectCoverageFrom="src/auth/**/*.js"

期望输出:
✅ All tests passed
✅ Coverage threshold met
✅ No security vulnerabilities found
*/