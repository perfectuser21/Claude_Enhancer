# Perfect21 API 错误码体系定义

## 📋 错误码分类概览

### 错误码命名规范
- **格式**: `CATEGORY_SPECIFIC_ERROR`
- **分类**: 按功能模块和错误类型分组
- **一致性**: 相同错误类型使用统一错误码

### HTTP状态码映射
| HTTP状态码 | 错误类别 | 描述 |
|-----------|----------|------|
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 认证失败 |
| 403 | Forbidden | 权限不足 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 422 | Unprocessable Entity | 数据验证失败 |
| 429 | Too Many Requests | 请求频率超限 |
| 500 | Internal Server Error | 服务器内部错误 |

## 🏷️ 错误码详细定义

### 1. 通用错误码 (GENERAL_*)

#### GENERAL_BAD_REQUEST
- **HTTP状态码**: 400
- **描述**: 请求格式错误或参数缺失
- **场景**:
  - JSON格式错误
  - 必需参数缺失
  - 请求方法不支持
- **解决方案**: 检查请求格式和参数

```json
{
  "success": false,
  "error": {
    "code": "GENERAL_BAD_REQUEST",
    "message": "请求参数格式错误",
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

#### GENERAL_INTERNAL_ERROR
- **HTTP状态码**: 500
- **描述**: 服务器内部错误
- **场景**:
  - 数据库连接失败
  - 外部服务调用失败
  - 系统异常
- **解决方案**: 稍后重试，联系技术支持

```json
{
  "success": false,
  "error": {
    "code": "GENERAL_INTERNAL_ERROR",
    "message": "服务器内部错误，请稍后重试",
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

#### GENERAL_SERVICE_UNAVAILABLE
- **HTTP状态码**: 503
- **描述**: 服务暂时不可用
- **场景**:
  - 系统维护
  - 服务过载
  - 依赖服务故障
- **解决方案**: 稍后重试

### 2. 认证错误码 (AUTH_*)

#### AUTH_INVALID_CREDENTIALS
- **HTTP状态码**: 401
- **描述**: 用户名或密码错误
- **场景**:
  - 密码错误
  - 用户名不存在
  - 账户被锁定
- **解决方案**: 检查用户名和密码

```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "用户名或密码错误",
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

#### AUTH_TOKEN_EXPIRED
- **HTTP状态码**: 401
- **描述**: 访问令牌已过期
- **场景**:
  - JWT令牌过期
  - 刷新令牌过期
- **解决方案**: 使用刷新令牌获取新的访问令牌

```json
{
  "success": false,
  "error": {
    "code": "AUTH_TOKEN_EXPIRED",
    "message": "访问令牌已过期，请重新登录",
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

#### AUTH_TOKEN_INVALID
- **HTTP状态码**: 401
- **描述**: 令牌格式错误或签名无效
- **场景**:
  - JWT签名验证失败
  - 令牌格式错误
  - 令牌被篡改
- **解决方案**: 重新登录获取有效令牌

#### AUTH_TOKEN_REVOKED
- **HTTP状态码**: 401
- **描述**: 令牌已被撤销
- **场景**:
  - 用户主动登出
  - 管理员撤销令牌
  - 安全策略撤销
- **解决方案**: 重新登录

#### AUTH_TOKEN_MISSING
- **HTTP状态码**: 401
- **描述**: 缺少认证令牌
- **场景**:
  - Authorization头缺失
  - 令牌格式错误
- **解决方案**: 在请求头中添加有效的Bearer令牌

#### AUTH_REFRESH_TOKEN_INVALID
- **HTTP状态码**: 401
- **描述**: 刷新令牌无效
- **场景**:
  - 刷新令牌过期
  - 刷新令牌格式错误
  - 刷新令牌不存在
- **解决方案**: 重新登录

#### AUTH_ACCOUNT_LOCKED
- **HTTP状态码**: 423
- **描述**: 账户被锁定
- **场景**:
  - 多次登录失败
  - 管理员锁定
  - 安全策略锁定
- **解决方案**: 联系管理员或等待解锁

#### AUTH_ACCOUNT_DISABLED
- **HTTP状态码**: 403
- **描述**: 账户已禁用
- **场景**:
  - 管理员禁用账户
  - 违规行为导致禁用
- **解决方案**: 联系管理员

### 3. 权限错误码 (PERMISSION_*)

#### PERMISSION_DENIED
- **HTTP状态码**: 403
- **描述**: 权限不足
- **场景**:
  - 用户角色不足
  - 缺少特定权限
  - 资源访问限制
- **解决方案**: 联系管理员申请权限

```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "权限不足，无法执行此操作",
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

#### PERMISSION_ROLE_REQUIRED
- **HTTP状态码**: 403
- **描述**: 需要特定角色权限
- **场景**:
  - 管理员接口访问
  - 特殊功能使用
- **解决方案**: 确保账户具有所需角色

#### PERMISSION_RESOURCE_ACCESS_DENIED
- **HTTP状态码**: 403
- **描述**: 资源访问被拒绝
- **场景**:
  - 访问他人私有资源
  - 跨组织资源访问
- **解决方案**: 检查资源访问权限

### 4. 验证错误码 (VALIDATION_*)

#### VALIDATION_ERROR
- **HTTP状态码**: 422
- **描述**: 请求数据验证失败
- **场景**:
  - 字段格式错误
  - 必需字段缺失
  - 数据类型错误
- **解决方案**: 根据详细错误信息修正数据

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确",
        "code": "INVALID_FORMAT"
      },
      {
        "field": "password",
        "message": "密码长度至少8位",
        "code": "MIN_LENGTH"
      }
    ],
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

#### VALIDATION_FIELD_REQUIRED
- **HTTP状态码**: 422
- **描述**: 必需字段缺失
- **字段错误码**:
  - `FIELD_REQUIRED`: 字段为空
  - `FIELD_MISSING`: 字段未提供

#### VALIDATION_FIELD_FORMAT
- **HTTP状态码**: 422
- **描述**: 字段格式错误
- **字段错误码**:
  - `INVALID_FORMAT`: 格式不正确
  - `INVALID_EMAIL`: 邮箱格式错误
  - `INVALID_PHONE`: 电话格式错误
  - `INVALID_URL`: URL格式错误

#### VALIDATION_FIELD_LENGTH
- **HTTP状态码**: 422
- **描述**: 字段长度错误
- **字段错误码**:
  - `MIN_LENGTH`: 长度不足
  - `MAX_LENGTH`: 长度超限
  - `EXACT_LENGTH`: 长度不匹配

#### VALIDATION_FIELD_VALUE
- **HTTP状态码**: 422
- **描述**: 字段值错误
- **字段错误码**:
  - `INVALID_VALUE`: 值不在允许范围
  - `WEAK_PASSWORD`: 密码强度不足
  - `INVALID_ENUM`: 枚举值无效

### 5. 资源错误码 (RESOURCE_*)

#### RESOURCE_NOT_FOUND
- **HTTP状态码**: 404
- **描述**: 请求的资源不存在
- **场景**:
  - 用户ID不存在
  - 文件未找到
  - 接口路径错误
- **解决方案**: 检查资源ID或路径

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "请求的资源不存在",
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

#### RESOURCE_ALREADY_EXISTS
- **HTTP状态码**: 409
- **描述**: 资源已存在
- **场景**:
  - 用户名重复
  - 邮箱重复
  - 重复创建资源
- **解决方案**: 使用不同的标识符

#### RESOURCE_CONFLICT
- **HTTP状态码**: 409
- **描述**: 资源状态冲突
- **场景**:
  - 并发修改冲突
  - 状态不允许操作
- **解决方案**: 刷新资源状态后重试

#### RESOURCE_LOCKED
- **HTTP状态码**: 423
- **描述**: 资源被锁定
- **场景**:
  - 资源正在处理
  - 管理员锁定
- **解决方案**: 等待解锁或联系管理员

### 6. 业务错误码 (BUSINESS_*)

#### BUSINESS_USER_EXISTS
- **HTTP状态码**: 409
- **描述**: 用户已存在
- **场景**:
  - 注册时用户名重复
  - 邮箱已被注册
- **解决方案**: 使用不同的用户名或邮箱

```json
{
  "success": false,
  "error": {
    "code": "BUSINESS_USER_EXISTS",
    "message": "用户名或邮箱已存在",
    "details": [
      {
        "field": "email",
        "message": "该邮箱已被注册",
        "code": "EMAIL_EXISTS"
      }
    ],
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

#### BUSINESS_EMAIL_NOT_VERIFIED
- **HTTP状态码**: 403
- **描述**: 邮箱未验证
- **场景**:
  - 需要邮箱验证的操作
- **解决方案**: 先验证邮箱

#### BUSINESS_PASSWORD_RESET_EXPIRED
- **HTTP状态码**: 400
- **描述**: 密码重置令牌已过期
- **场景**:
  - 重置链接过期
- **解决方案**: 重新申请密码重置

#### BUSINESS_OPERATION_NOT_ALLOWED
- **HTTP状态码**: 400
- **描述**: 当前状态不允许此操作
- **场景**:
  - 状态机限制
  - 业务规则限制
- **解决方案**: 检查前置条件

### 7. 速率限制错误码 (RATE_LIMIT_*)

#### RATE_LIMIT_EXCEEDED
- **HTTP状态码**: 429
- **描述**: 请求频率超过限制
- **场景**:
  - API调用过于频繁
  - 短时间内多次重试
- **解决方案**: 等待后重试

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超过限制，请稍后重试",
    "retryAfter": 300,
    "limit": {
      "type": "per_hour",
      "max": 100,
      "remaining": 0,
      "resetTime": "2024-01-20T11:00:00Z"
    },
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

#### RATE_LIMIT_LOGIN_EXCEEDED
- **HTTP状态码**: 429
- **描述**: 登录尝试次数过多
- **场景**:
  - 暴力破解防护
- **解决方案**: 等待冷却时间

#### RATE_LIMIT_REGISTRATION_EXCEEDED
- **HTTP状态码**: 429
- **描述**: 注册请求过多
- **场景**:
  - 防止批量注册
- **解决方案**: 等待后重试

### 8. 文件错误码 (FILE_*)

#### FILE_TOO_LARGE
- **HTTP状态码**: 413
- **描述**: 文件大小超过限制
- **场景**:
  - 头像上传过大
  - 文档上传超限
- **解决方案**: 压缩文件或选择更小的文件

```json
{
  "success": false,
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "上传文件大小超过限制",
    "maxSize": "5MB",
    "actualSize": "8MB",
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

#### FILE_INVALID_TYPE
- **HTTP状态码**: 400
- **描述**: 文件类型不支持
- **场景**:
  - 上传不支持的文件格式
- **解决方案**: 使用支持的文件类型

#### FILE_UPLOAD_FAILED
- **HTTP状态码**: 500
- **描述**: 文件上传失败
- **场景**:
  - 存储服务错误
  - 网络传输失败
- **解决方案**: 重试上传

## 🔍 错误码使用指南

### 1. 错误响应格式标准

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "人类可读的错误描述",
    "details": [
      {
        "field": "fieldName",
        "message": "字段特定错误",
        "code": "FIELD_ERROR_CODE"
      }
    ],
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789",
    "documentation": "https://docs.perfect21.dev/errors/ERROR_CODE"
  }
}
```

### 2. 错误处理最佳实践

#### 客户端处理
```javascript
// JavaScript 错误处理示例
const handleApiError = (error) => {
  switch (error.code) {
    case 'AUTH_TOKEN_EXPIRED':
      // 刷新令牌或重新登录
      refreshToken();
      break;
    case 'VALIDATION_ERROR':
      // 显示字段验证错误
      showValidationErrors(error.details);
      break;
    case 'RATE_LIMIT_EXCEEDED':
      // 显示重试提示
      showRetryMessage(error.retryAfter);
      break;
    default:
      // 显示通用错误信息
      showGenericError(error.message);
  }
};
```

#### 服务端日志
```json
{
  "level": "error",
  "timestamp": "2024-01-20T10:30:00Z",
  "requestId": "req_abc123xyz789",
  "errorCode": "AUTH_INVALID_CREDENTIALS",
  "userId": "usr_1234567890",
  "ip": "192.168.1.100",
  "userAgent": "Mozilla/5.0...",
  "details": {
    "attemptCount": 3,
    "lockoutRemaining": 600
  }
}
```

### 3. 错误监控指标

#### 关键指标
- **错误率**: 按错误码统计
- **响应时间**: 错误请求的处理时间
- **错误趋势**: 时间序列错误分布
- **用户影响**: 受影响的用户数量

#### 告警规则
- 总错误率 > 5%
- 认证错误率 > 10%
- 5XX错误 > 1%
- 特定错误码激增

## 📊 错误码统计分析

### 常见错误码排名 (预期)
1. `AUTH_TOKEN_EXPIRED` - 25%
2. `VALIDATION_ERROR` - 20%
3. `PERMISSION_DENIED` - 15%
4. `RESOURCE_NOT_FOUND` - 10%
5. `RATE_LIMIT_EXCEEDED` - 8%
6. `AUTH_INVALID_CREDENTIALS` - 7%
7. `BUSINESS_USER_EXISTS` - 5%
8. 其他错误码 - 10%

### 错误处理性能指标
- **检测时间**: < 10ms
- **响应时间**: < 100ms
- **错误日志延迟**: < 50ms
- **告警响应时间**: < 30s

## 🛠️ 错误码维护

### 新增错误码流程
1. 确定错误分类和命名
2. 定义HTTP状态码映射
3. 编写错误描述和解决方案
4. 更新API文档
5. 添加测试用例
6. 更新客户端处理逻辑

### 错误码废弃策略
1. 标记为废弃 (6个月通知期)
2. 添加替代错误码说明
3. 逐步迁移现有代码
4. 监控使用情况
5. 最终移除 (确保零使用)