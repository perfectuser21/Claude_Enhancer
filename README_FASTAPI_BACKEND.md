# FastAPI任务管理系统后端 API

## 🎯 项目概述

这是一个基于 **FastAPI** 构建的现代化任务管理系统后端API，提供完整的RESTful API服务，支持任务管理、项目管理、用户认证、通知系统等核心功能。

### ✨ 核心特性

- 🚀 **高性能**: 基于FastAPI，支持异步处理和自动API文档生成
- 🔐 **安全认证**: JWT Token认证，bcrypt密码加密，角色权限管理
- 📊 **数据管理**: PostgreSQL + SQLAlchemy ORM，支持数据库迁移
- ⚡ **缓存优化**: Redis缓存提升响应速度
- 📝 **完整API**: 涵盖任务、项目、用户、通知等所有业务模块
- 🛡️ **中间件**: CORS、请求日志、错误处理、限流等安全中间件
- 📊 **仪表板**: 数据统计、趋势分析、智能推荐
- 🔔 **通知系统**: 实时通知、邮件提醒、自定义设置

## 🏗️ 技术架构

### 技术栈
- **后端框架**: FastAPI 0.104.1
- **ASGI服务器**: Uvicorn
- **数据库**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0
- **缓存**: Redis 7+
- **认证**: JWT + bcrypt
- **数据验证**: Pydantic
- **API文档**: Swagger/OpenAPI

### 项目结构
```
src/
├── main.py                    # FastAPI主应用
├── core/                      # 核心模块
│   ├── config.py             # 配置管理
│   ├── database.py           # 数据库连接
│   └── dependencies.py       # 依赖注入
├── api/                       # API层
│   ├── models/               # Pydantic数据模型
│   │   ├── auth.py          # 认证相关模型
│   │   ├── tasks.py         # 任务管理模型
│   │   ├── projects.py      # 项目管理模型
│   │   └── common.py        # 通用模型
│   └── routes/               # API路由
│       ├── auth.py          # 认证API
│       ├── tasks.py         # 任务管理API
│       ├── projects.py      # 项目管理API
│       ├── dashboard.py     # 仪表板API
│       └── notifications.py # 通知API
├── auth/                      # 认证模块
├── task_management/           # 任务管理业务逻辑
│   ├── models.py             # 数据库模型
│   ├── services.py           # 业务服务
│   └── repositories.py       # 数据访问层
└── ...
```

## 🚀 快速开始

### 环境要求
- Python 3.9+
- PostgreSQL 15+
- Redis 7+

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd Claude\ Enhancer\ 5.0
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等信息
```

4. **初始化数据库**
```bash
python start.py init
```

5. **启动服务**

开发模式（热重载）：
```bash
python start.py dev
```

生产模式：
```bash
python start.py prod
```

直接启动：
```bash
python start.py serve --host 0.0.0.0 --port 8000
```

### 使用Docker（推荐）
```bash
# 启动所有服务（包括数据库和Redis）
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

## 📋 API文档

启动服务后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔐 API认证

### 获取访问令牌

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "your_password"
     }'
```

### 使用令牌访问API

```bash
curl -X GET "http://localhost:8000/api/tasks" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📊 核心API端点

### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新令牌
- `GET /api/auth/profile` - 获取用户资料
- `PUT /api/auth/profile` - 更新用户资料

### 任务管理
- `GET /api/tasks` - 获取任务列表（支持分页、过滤、搜索）
- `POST /api/tasks` - 创建新任务
- `GET /api/tasks/{id}` - 获取任务详情
- `PUT /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务
- `PATCH /api/tasks/{id}/status` - 更新任务状态
- `PATCH /api/tasks/{id}/assign` - 分配任务

### 项目管理
- `GET /api/projects` - 获取项目列表
- `POST /api/projects` - 创建新项目
- `GET /api/projects/{id}` - 获取项目详情
- `PUT /api/projects/{id}` - 更新项目
- `DELETE /api/projects/{id}` - 删除项目
- `GET /api/projects/{id}/members` - 获取项目成员
- `POST /api/projects/{id}/members` - 添加项目成员

### 仪表板
- `GET /api/dashboard/overview` - 获取仪表板概览
- `GET /api/dashboard/recent-activities` - 获取最近活动
- `GET /api/dashboard/upcoming-tasks` - 获取即将到期任务
- `GET /api/dashboard/productivity-trend` - 获取生产力趋势

### 通知系统
- `GET /api/notifications` - 获取通知列表
- `PATCH /api/notifications/{id}/read` - 标记通知为已读
- `GET /api/notifications/settings` - 获取通知设置
- `PUT /api/notifications/settings` - 更新通知设置

## ⚙️ 配置说明

### 环境变量配置

主要配置项包括：

```bash
# 应用配置
APP_NAME="Task Management System"
ENVIRONMENT="development"  # development, testing, production
DEBUG=true

# 数据库配置
DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
DATABASE_POOL_SIZE=20

# Redis配置
REDIS_URL="redis://localhost:6379/0"

# JWT认证配置
SECRET_KEY="your-secret-key-32-chars-minimum"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS配置
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:3001"
```

## 🛠️ 开发指南

### 启动检查
```bash
# 检查系统配置和依赖
python start.py check

# 查看版本信息
python start.py version
```

### 数据库管理
```bash
# 初始化数据库
python start.py init

# 备份数据库
python start.py backup --backup-dir ./backups
```

### 开发模式特性
- ✅ 热重载 - 代码修改自动重启
- ✅ 详细日志 - 完整的请求响应日志
- ✅ API文档 - 自动生成的交互式文档
- ✅ 错误详情 - 详细的错误堆栈信息

## 🔧 高级功能

### 中间件支持
- **CORS中间件** - 跨域请求处理
- **请求日志中间件** - 记录所有API请求
- **错误处理中间件** - 统一错误响应格式
- **限流中间件** - API访问频率限制

### 安全特性
- **JWT认证** - 无状态令牌认证
- **密码加密** - bcrypt哈希加密
- **输入验证** - Pydantic数据验证
- **SQL注入防护** - SQLAlchemy ORM防护
- **HTTPS支持** - TLS/SSL加密传输

### 性能优化
- **异步处理** - FastAPI原生异步支持
- **连接池** - 数据库连接池管理
- **Redis缓存** - 热点数据缓存
- **查询优化** - 数据库索引和查询优化

## 📈 监控和日志

### 健康检查
```bash
curl http://localhost:8000/health
```

### 日志配置
- 支持文件和控制台输出
- 可配置日志级别
- 请求响应时间记录
- 错误异常详细记录

### 性能监控
- 响应时间监控
- 并发连接数统计
- 数据库连接池状态
- Redis缓存命中率

## 🧪 测试

```bash
# 运行测试
pytest

# 运行覆盖率测试
pytest --cov=src

# 运行特定测试
pytest tests/test_auth.py
```

## 📦 部署

### Docker部署
```bash
# 构建镜像
docker build -t task-manager-api .

# 运行容器
docker run -p 8000:8000 task-manager-api
```

### 生产环境部署
1. 设置环境变量 `ENVIRONMENT=production`
2. 配置安全的 `SECRET_KEY`
3. 设置正确的数据库连接
4. 配置HTTPS证书
5. 设置反向代理（如Nginx）

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如果您在使用过程中遇到问题，请：

1. 查看[API文档](http://localhost:8000/docs)
2. 检查[配置说明](#配置说明)
3. 提交[Issue](https://github.com/your-repo/issues)
4. 联系开发团队

---

🎉 **感谢使用任务管理系统API！**

这个FastAPI后端为您提供了完整、安全、高性能的任务管理API服务。通过现代化的架构设计和丰富的功能特性，帮助您快速构建优秀的任务管理应用。