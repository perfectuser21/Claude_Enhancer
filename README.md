# 🚀 Perfect21 - AI驱动的开发工作流系统

**基于 core-main-modules-features 的全新架构重建**

## 🏗️ 架构概览

```
Perfect21/
├── core/                    # 全局核心基础设施
│   ├── ai_pool.py          # AI实例池管理
│   ├── router.py           # 智能路由系统
│   └── project_manager.py  # 项目管理器
├── main/                   # 全局入口点
│   ├── app.py             # 主应用入口
│   ├── cli.py             # 命令行入口
│   └── web_server.py      # Web服务器入口
├── modules/                # 全局共享模块
│   ├── claude_bridge/     # Claude Code桥接
│   ├── config_manager/    # 配置管理
│   └── utils/             # 工具函数
├── features/              # 功能特性
│   ├── ai_butler/         # AI管家功能（简单结构）
│   ├── workspace_manager/ # 工作空间管理（复杂结构：core-main-modules）
│   └── perfect21/         # Perfect21界面（复杂结构：core-main-modules）
└── config/                # 配置文件
    ├── vibepilot.yaml
    └── ai_instances.yaml
```

## 🎯 核心特性

- ✅ **多AI并行开发**：支持多个Claude Code/Codex同时工作
- ✅ **工作空间隔离**：每个项目独立的开发环境
- ✅ **Vibe Coding优化**：AI友好的开发工具链
- ✅ **混合架构**：简单功能直接组织，复杂功能core-main-modules结构
- ✅ **项目管理**：支持VibePilot自我完善 + 外部项目开发

## 🚀 快速开始

```bash
# 启动Perfect21
./start_perfect21.sh

# 或者直接启动
python3 main/app.py

# Web界面
http://localhost:8001
```

## 📋 功能模块

### AI Butler（简单功能）
- 自然语言任务处理
- 自动Claude Code调用
- 智能对话管理

### Workspace Manager（复杂功能）
- 多项目并行开发
- AI实例池管理
- 项目环境隔离

### Perfect21（复杂功能）
- 多项目仪表板
- 实时状态监控
- 可视化工作空间管理

---

*重建于 2025-09-13*
*基于经过验证的AI管家系统*