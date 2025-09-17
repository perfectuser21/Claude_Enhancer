# Perfect21 最佳实践库

## 🎯 认证系统最佳实践

### JWT认证模式
```yaml
pattern: JWT双令牌模式
scenario: 需要无状态认证的Web应用
agents: [backend-architect, security-auditor]
implementation:
  access_token: 短期有效(15分钟)
  refresh_token: 长期有效(7天)
  security: httpOnly cookies + CSRF token
lessons:
  - 永远不要在localStorage存储JWT
  - 刷新机制必须有sliding window
  - 必须有令牌黑名单机制
```

### Session认证模式
```yaml
pattern: Redis会话存储
scenario: 传统Web应用，需要服务端状态
agents: [backend-architect, database-specialist]
implementation:
  storage: Redis cluster
  expiry: 30分钟滑动过期
  csrf: 每次请求验证CSRF token
lessons:
  - 会话ID必须足够随机(UUID v4)
  - 必须有会话固定攻击防护
  - 登出必须真正销毁会话
```

## 🏗️ API设计最佳实践

### RESTful API设计
```yaml
pattern: 标准REST + HATEOAS
scenario: 公开API或微服务间调用
agents: [api-designer, backend-architect]
implementation:
  naming: 名词复数形式(/users, /orders)
  http_methods:
    - GET: 查询
    - POST: 创建
    - PUT: 完整更新
    - PATCH: 部分更新
    - DELETE: 删除
  status_codes:
    - 200: 成功
    - 201: 创建成功
    - 400: 客户端错误
    - 401: 未认证
    - 403: 权限不足
    - 404: 资源不存在
    - 500: 服务器错误
lessons:
  - 版本控制通过Accept header
  - 分页使用limit+offset或cursor
  - 错误响应必须包含error_code和message
  - 所有时间使用ISO 8601格式
```

### GraphQL API设计
```yaml
pattern: Schema First设计
scenario: 复杂数据关系，需要灵活查询
agents: [api-designer, frontend-specialist]
implementation:
  schema: 先定义schema.graphql
  resolvers: 按业务域分离
  auth: 字段级权限控制
  caching: 按query复杂度缓存
lessons:
  - N+1查询问题必须用DataLoader解决
  - 深度限制防止恶意查询
  - 查询复杂度分析和限流
  - 订阅使用WebSocket，注意内存泄露
```

## 🎨 前端架构最佳实践

### React应用架构
```yaml
pattern: 特性驱动的模块化架构
scenario: 中大型React应用
agents: [frontend-specialist, react-pro, typescript-pro]
structure:
  src/
    features/          # 按功能模块组织
      auth/
        components/    # UI组件
        hooks/        # 自定义hooks
        services/     # API调用
        store/        # 状态管理
        types/        # TypeScript类型
    shared/           # 共享代码
      components/     # 通用组件
      utils/         # 工具函数
      constants/     # 常量
implementation:
  state: Zustand或Redux Toolkit
  routing: React Router v6
  styling: Tailwind CSS + Headless UI
  testing: Vitest + React Testing Library
lessons:
  - 组件职责单一，最多3层props传递
  - 状态尽量局部化，全局状态最少化
  - 异步状态用React Query管理
  - 错误边界必须在feature级别设置
```

## 📊 数据库设计最佳实践

### PostgreSQL模式设计
```yaml
pattern: 领域驱动的表设计
scenario: 关系型数据，ACID要求高
agents: [database-specialist, backend-architect]
implementation:
  naming: snake_case，表名复数
  primary_key: UUID v4，避免自增ID泄露信息
  timestamps: created_at, updated_at必须有
  soft_delete: deleted_at字段，避免物理删除
  indexing:
    - 外键必须有索引
    - 查询字段组合索引
    - 唯一约束用唯一索引
lessons:
  - 事务边界要明确，避免长事务
  - 分页查询必须用游标，不用OFFSET
  - JSON字段谨慎使用，考虑查询需求
  - 迁移脚本必须可回滚
```

## 🧪 测试策略最佳实践

### 测试金字塔
```yaml
pattern: 70%单元 + 20%集成 + 10%E2E
scenario: 高质量软件交付
agents: [test-engineer, e2e-test-specialist]
implementation:
  unit_tests:
    framework: Jest/Vitest
    coverage: >90%语句覆盖
    mocking: 外部依赖全部mock
  integration_tests:
    framework: Supertest + TestContainers
    database: 真实数据库，事务回滚
    external_apis: WireMock模拟
  e2e_tests:
    framework: Playwright
    environment: 独立测试环境
    data: 种子数据，测试后清理
lessons:
  - 测试要独立，不依赖执行顺序
  - 测试数据要可重现，使用工厂模式
  - 失败测试必须有明确错误信息
  - CI环境测试必须可靠，避免flaky tests
```

## 🚀 部署和运维最佳实践

### Docker容器化
```yaml
pattern: 多阶段构建 + 非root运行
scenario: 云原生应用部署
agents: [devops-engineer, deployment-manager]
implementation:
  dockerfile:
    - 多阶段构建减少镜像大小
    - 非root用户运行提高安全性
    - 健康检查端点
    - 优雅关闭信号处理
  compose:
    - 开发环境快速启动
    - 数据卷持久化
    - 网络隔离
lessons:
  - 不要在镜像中存储机密
  - 使用.dockerignore减少构建上下文
  - 标签使用语义化版本
  - 镜像扫描安全漏洞
```

### Kubernetes部署
```yaml
pattern: Helm Chart + GitOps
scenario: 生产环境容器编排
agents: [kubernetes-expert, cloud-architect]
implementation:
  resources:
    - Deployment: 应用部署
    - Service: 服务发现
    - Ingress: 流量路由
    - ConfigMap: 配置管理
    - Secret: 机密管理
  monitoring:
    - Prometheus: 指标收集
    - Grafana: 可视化
    - Alertmanager: 告警
lessons:
  - 资源限制必须设置，防止OOM
  - 健康检查配置正确的路径和超时
  - 滚动更新策略要考虑服务可用性
  - 备份策略包括配置和持久数据
```

## 📋 代码质量检查清单

### 代码审查清单
- [ ] 代码符合项目编码规范
- [ ] 函数职责单一，复杂度合理
- [ ] 错误处理完整，不忽略异常
- [ ] 安全性检查（SQL注入、XSS等）
- [ ] 性能考虑（N+1查询、内存泄露等）
- [ ] 测试覆盖核心逻辑
- [ ] 文档和注释准确且必要
- [ ] 向后兼容性考虑

### 发布前检查清单
- [ ] 所有测试通过（单元、集成、E2E）
- [ ] 代码审查完成且批准
- [ ] 数据库迁移脚本测试
- [ ] 配置文件更新完整
- [ ] 监控告警规则配置
- [ ] 回滚计划准备
- [ ] 发布公告准备
- [ ] 相关文档更新

---

*此最佳实践库由Perfect21 agents执行经验积累而成，持续更新中...*