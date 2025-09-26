#!/bin/bash
# Claude Enhancer 5.0 - 新手引导系统
# 为初次使用者提供友好的入门体验

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 显示欢迎横幅
show_welcome_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
    
    ╔══════════════════════════════════════════════════════════╗
    ║                🎉 欢迎使用 Claude Enhancer 5.0！           ║
    ║                                                          ║
    ║        你的AI驱动开发工作流智能助手已准备就绪               ║
    ╚══════════════════════════════════════════════════════════╝
    
EOF
    echo -e "${NC}"
    
    echo -e "${YELLOW}🤖 我是你的AI开发助手！让我用几分钟时间帮你快速上手。${NC}\n"
}

# 检查系统环境
check_environment() {
    echo -e "${BLUE}🔍 正在检查你的开发环境...${NC}\n"
    
    local git_ok=false
    local node_ok=false
    local python_ok=false
    
    # 检查Git
    if command -v git >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Git: $(git --version | cut -d' ' -f3)${NC}"
        git_ok=true
    else
        echo -e "${RED}❌ Git: 未安装${NC}"
    fi
    
    # 检查Node.js
    if command -v node >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Node.js: $(node --version)${NC}"
        node_ok=true
    else
        echo -e "${YELLOW}⚠️  Node.js: 未安装 (某些功能需要)${NC}"
    fi
    
    # 检查Python
    if command -v python3 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Python: $(python3 --version | cut -d' ' -f2)${NC}"
        python_ok=true
    else
        echo -e "${YELLOW}⚠️  Python: 未安装 (某些Hook需要)${NC}"
    fi
    
    echo ""
    
    if $git_ok; then
        echo -e "${GREEN}🎉 基础环境检查通过！你可以开始使用Claude Enhancer了。${NC}\n"
        return 0
    else
        echo -e "${RED}❌ 基础环境不完整。请先安装Git再继续。${NC}\n"
        return 1
    fi
}

# 显示学习路径选择
show_learning_paths() {
    echo -e "${MAGENTA}📚 请选择你的学习路径:${NC}\n"
    
    cat << 'EOF'
    ┌─────────────────────────────────────────────────────────────┐
    │ 1) 🚀 快速体验模式 - 30秒快速设置，立即开始项目               │
    │    适合: 急于尝试、有一定经验的开发者                        │
    │                                                             │
    │ 2) 📖 详细教程模式 - 5分钟深入了解工作原理                   │
    │    适合: 想要理解系统原理的学习者                            │
    │                                                             │
    │ 3) 🎯 项目向导模式 - 基于具体项目的引导式设置                 │
    │    适合: 有明确项目目标的用户                               │
    │                                                             │
    │ 4) ❓ 智能推荐模式 - 让AI帮你选择最合适的路径                 │
    │    适合: 不确定选择哪个的用户                               │
    │                                                             │
    │ 5) 📋 查看完整功能清单                                       │
    │                                                             │
    │ 0) 🚪 退出                                                   │
    └─────────────────────────────────────────────────────────────┘
EOF
    
    echo ""
    echo -n -e "${CYAN}请输入数字 (0-5): ${NC}"
}

# 快速体验模式
quick_experience_mode() {
    echo -e "${GREEN}🚀 快速体验模式启动！${NC}\n"
    
    echo -e "${BLUE}正在为你设置Claude Enhancer...${NC}"
    
    # 检查是否已经安装
    if [ -f ".git/hooks/pre-commit" ]; then
        echo -e "${YELLOW}检测到已安装的Git Hooks，跳过安装步骤。${NC}"
    else
        echo -e "${BLUE}正在安装Git Hooks...${NC}"
        if ./.claude/install.sh >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Git Hooks安装成功！${NC}"
        else
            echo -e "${YELLOW}⚠️  Git Hooks安装可能有问题，但可以继续体验。${NC}"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}🎉 设置完成！现在你可以：${NC}\n"
    
    cat << 'EOF'
    ✨ 立即开始体验:
    
    # 创建一个简单的Web应用
    echo "我想创建一个用户登录页面" | ./.claude/hooks/smart_agent_selector.sh
    
    # 查看推荐的Agent组合
    ./.claude/hooks/smart_agent_selector.sh --help
    
    # 运行完整的工作流
    echo "开发一个博客系统" | ./.claude/hooks/smart_agent_selector.sh
EOF
    
    echo ""
    echo -e "${CYAN}💡 提示: 随时运行 '.claude/help.sh' 获取帮助${NC}\n"
}

# 详细教程模式
detailed_tutorial_mode() {
    echo -e "${GREEN}📖 详细教程模式启动！${NC}\n"
    
    echo -e "${BLUE}🎓 让我们从基础概念开始...${NC}\n"
    
    cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════════╗
    ║                    🤖 什么是 Claude Enhancer?                  ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║                                                               ║
    ║  想象一下，你有一个由多个AI专家组成的开发团队：                 ║
    ║                                                               ║
    ║  🏗️  建筑师Agent     → 设计整体架构和技术方案                 ║
    ║  🎨 前端专家Agent    → 制作漂亮的用户界面                     ║
    ║  ⚙️  后端工程师Agent  → 处理服务器逻辑和API                   ║
    ║  🗄️  数据库专家Agent  → 设计数据存储方案                     ║
    ║  🔒 安全审计Agent    → 确保系统安全可靠                      ║
    ║  🧪 测试工程师Agent   → 保证代码质量                        ║
    ║                                                               ║
    ║  你只需要告诉我们 "我想做一个博客网站"，                        ║
    ║  这些AI专家就会自动协作，为你构建整个项目！                      ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
EOF
    
    echo ""
    echo -n -e "${CYAN}按Enter继续，了解工作流程... ${NC}"
    read -r
    
    show_workflow_explanation
}

# 显示工作流程解释
show_workflow_explanation() {
    clear
    echo -e "${MAGENTA}📋 Claude Enhancer 8-Phase 工作流程${NC}\n"
    
    cat << 'EOF'
    ┌─ Phase 0: 分支管理 ────────────────────────────────────────┐
    │ 🌿 自动创建feature分支，准备开发环境                        │
    │    → git checkout -b feature/your-feature                  │
    └──────────────────────────────────────────────────────────┘
            ↓
    ┌─ Phase 1: 需求分析 ────────────────────────────────────────┐
    │ 📋 AI分析你的需求，明确项目目标和范围                       │
    │    → 理解要做什么，为什么要做，成功标准是什么                 │
    └──────────────────────────────────────────────────────────┘
            ↓
    ┌─ Phase 2: 设计规划 ────────────────────────────────────────┐
    │ 🎨 设计系统架构，选择技术栈，规划实现方案                   │
    │    → 如何实现，用什么技术，架构怎么设计                      │
    └──────────────────────────────────────────────────────────┘
            ↓
    ┌─ Phase 3: 代码实现 ────────────────────────────────────────┐
    │ ⚡ 4-6-8个AI Agent并行工作，快速实现功能                   │
    │    → 真正的编码工作，多个专家同时协作                        │
    └──────────────────────────────────────────────────────────┘
            ↓
    ┌─ Phase 4: 本地测试 ────────────────────────────────────────┐
    │ 🧪 运行各种测试，确保功能正常、性能良好                      │
    │    → 单元测试、集成测试、性能测试                           │
    └──────────────────────────────────────────────────────────┘
            ↓
    ┌─ Phase 5: 代码提交 ────────────────────────────────────────┐
    │ 📝 Git Hooks自动检查代码质量，规范提交信息                  │
    │    → 代码风格、测试覆盖率、安全检查                         │
    └──────────────────────────────────────────────────────────┘
            ↓
    ┌─ Phase 6: 代码审查 ────────────────────────────────────────┐
    │ 👥 创建Pull Request，团队审查，收集反馈                    │
    │    → 同事review、修改建议、质量把关                         │
    └──────────────────────────────────────────────────────────┘
            ↓
    ┌─ Phase 7: 合并部署 ────────────────────────────────────────┐
    │ 🚀 合并到主分支，自动化部署到生产环境                       │
    │    → 最终上线，用户可以使用                               │
    └──────────────────────────────────────────────────────────┘
EOF
    
    echo ""
    echo -n -e "${CYAN}按Enter继续，了解Agent选择策略... ${NC}"
    read -r
    
    show_agent_strategy
}

# 显示Agent选择策略
show_agent_strategy() {
    clear
    echo -e "${GREEN}🤖 4-6-8 Agent选择策略${NC}\n"
    
    cat << 'EOF'
    ╔══════════════════════════════════════════════════════════════════╗
    ║                        智能Agent选择                              ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║  🟢 简单任务 (4 Agents) - 5-10分钟                               ║
    ║     └─ Bug修复、小功能、文档更新                                  ║
    ║     └─ 例如: "修复登录页面的CSS样式问题"                          ║
    ║                                                                  ║
    ║  🟡 标准任务 (6 Agents) - 15-20分钟                              ║
    ║     └─ 新功能开发、API端点、页面创建                              ║
    ║     └─ 例如: "创建用户注册和登录功能"                             ║
    ║                                                                  ║
    ║  🔴 复杂任务 (8+ Agents) - 25-30分钟                             ║
    ║     └─ 完整应用、系统集成、架构重构                               ║
    ║     └─ 例如: "构建一个完整的电商平台"                             ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    💡 AI会自动分析你的需求，选择最合适的Agent组合！
    
    例如，当你说 "我想创建一个博客网站" 时：
    
    ┌─ AI分析 ──────────────────────────────────────────────────────┐
    │ 🔍 任务分析: 博客网站 = 中等复杂度                            │
    │ 📊 推荐: 6个Agent (标准任务)                                 │
    │ ⏱️  预估时间: 15-20分钟                                      │
    └─────────────────────────────────────────────────────────────┘
    
    👥 自动选择的Agent团队:
      1. 🏗️  backend-architect    - 设计后端架构
      2. 🎨 frontend-specialist  - 创建用户界面  
      3. 🗄️  database-specialist  - 设计数据库
      4. 🔒 security-auditor     - 安全审查
      5. 🧪 test-engineer        - 质量保证
      6. 📝 technical-writer     - 编写文档
EOF
    
    echo ""
    echo -n -e "${CYAN}太棒了！现在你了解基本原理了。按Enter开始实际操作... ${NC}"
    read -r
    
    echo -e "${GREEN}🎉 教程完成！你现在可以开始使用Claude Enhancer了。${NC}\n"
    show_next_steps
}

# 项目向导模式  
project_wizard_mode() {
    echo -e "${GREEN}🎯 项目向导模式启动！${NC}\n"
    
    echo -e "${BLUE}让我帮你分析项目需求...${NC}\n"
    
    echo -n -e "${CYAN}请描述你想要创建的项目 (例如: 博客网站、电商平台、管理系统): ${NC}"
    read -r project_description
    
    if [ -z "$project_description" ]; then
        echo -e "${YELLOW}没有输入项目描述，使用示例项目...${NC}\n"
        project_description="博客网站"
    fi
    
    echo ""
    echo -e "${BLUE}🤖 AI正在分析你的项目: "$project_description"${NC}\n"
    
    # 模拟AI分析过程
    echo -n -e "${YELLOW}分析中"
    for i in {1..3}; do
        sleep 1
        echo -n "."
    done
    echo -e "${NC}\n"
    
    # 显示分析结果
    show_project_analysis "$project_description"
}

# 显示项目分析结果
show_project_analysis() {
    local project="$1"
    
    echo -e "${GREEN}📊 项目分析结果:${NC}\n"
    
    # 简单的关键词匹配来确定复杂度
    local complexity="standard"
    local agent_count=6
    local time_estimate="15-20分钟"
    
    case "$project" in
        *"电商"*|*"平台"*|*"系统"*|*"架构"*)
            complexity="complex"
            agent_count=8
            time_estimate="25-30分钟"
            ;;
        *"修复"*|*"bug"*|*"简单"*|*"小"*)
            complexity="simple"
            agent_count=4
            time_estimate="5-10分钟"
            ;;
    esac
    
    cat << EOF
    ┌─ 项目信息 ──────────────────────────────────────────────────────┐
    │ 📝 项目描述: $project
    │ 📊 复杂度: $complexity
    │ 🤖 推荐Agent数量: $agent_count 个
    │ ⏱️  预估开发时间: $time_estimate
    └───────────────────────────────────────────────────────────────┘
EOF
    
    echo ""
    echo -e "${MAGENTA}👥 为此项目推荐的AI专家团队:${NC}\n"
    
    case "$complexity" in
        "simple")
            cat << 'EOF'
            1. 🏗️  backend-architect  - 快速架构设计
            2. 🧪 test-engineer       - 质量保证
            3. 🔒 security-auditor    - 安全检查
            4. 📝 technical-writer    - 文档编写
EOF
            ;;
        "complex")
            cat << 'EOF'
            1. 🏗️  system-architect    - 系统整体设计
            2. 🎨 frontend-specialist - 用户界面设计
            3. ⚙️  backend-architect   - 后端服务架构
            4. 🗄️  database-specialist - 数据库设计
            5. 🔒 security-specialist - 深度安全审计
            6. 🧪 test-engineer       - 全面质量保证
            7. 🚀 devops-engineer     - 部署和运维
            8. 📝 technical-writer    - 完整文档体系
EOF
            ;;
        *)
            cat << 'EOF'
            1. 🏗️  backend-architect   - 后端架构设计
            2. 🎨 frontend-specialist - 前端界面开发
            3. 🗄️  database-specialist - 数据存储方案
            4. 🔒 security-auditor    - 安全性检查
            5. 🧪 test-engineer       - 测试和验证
            6. 📝 technical-writer    - 项目文档
EOF
            ;;
    esac
    
    echo ""
    echo -n -e "${CYAN}看起来不错？按Enter开始设置项目环境... ${NC}"
    read -r
    
    # 设置项目环境
    setup_project_environment "$project" "$complexity"
}

# 设置项目环境
setup_project_environment() {
    local project="$1"
    local complexity="$2"
    
    echo -e "${BLUE}🔧 正在为你的项目设置环境...${NC}\n"
    
    # 安装Git Hooks
    if [ ! -f ".git/hooks/pre-commit" ]; then
        echo -e "${BLUE}正在安装Git Hooks...${NC}"
        if ./.claude/install.sh >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Git Hooks安装成功！${NC}"
        else
            echo -e "${YELLOW}⚠️  Git Hooks安装可能有问题，请稍后手动检查。${NC}"
        fi
    else
        echo -e "${GREEN}✅ Git Hooks已安装${NC}"
    fi
    
    # 创建项目配置文件
    echo -e "${BLUE}正在创建项目配置...${NC}"
    
    cat > .claude/project_config.json << EOF
{
  "project_name": "$project",
  "complexity": "$complexity",
  "created_at": "$(date -Iseconds)",
  "wizard_completed": true
}
EOF
    
    echo -e "${GREEN}✅ 项目配置创建完成${NC}"
    
    echo ""
    echo -e "${GREEN}🎉 项目环境设置完成！${NC}\n"
    
    show_next_steps
}

# 智能推荐模式
smart_recommendation_mode() {
    echo -e "${GREEN}❓ 智能推荐模式启动！${NC}\n"
    
    echo -e "${BLUE}让我问几个问题来为你推荐最合适的路径...${NC}\n"
    
    local experience="beginner"
    local urgency="normal"
    local project_type="unknown"
    
    # 问题1: 经验水平
    echo -e "${CYAN}1. 你的开发经验如何？${NC}"
    echo "   a) 刚开始学编程 (新手)"
    echo "   b) 有一些经验，但是第一次用AI工具"
    echo "   c) 经验丰富，想快速上手"
    echo ""
    echo -n "请选择 (a/b/c): "
    read -r exp_choice
    
    case "$exp_choice" in
        "a"|"A") experience="beginner" ;;
        "b"|"B") experience="intermediate" ;;
        "c"|"C") experience="expert" ;;
        *) experience="intermediate" ;;
    esac
    
    echo ""
    
    # 问题2: 时间紧急程度
    echo -e "${CYAN}2. 你现在的时间情况？${NC}"
    echo "   a) 有充足时间，想仔细学习"
    echo "   b) 时间一般，想快速了解"
    echo "   c) 很急，需要立即开始项目"
    echo ""
    echo -n "请选择 (a/b/c): "
    read -r urgency_choice
    
    case "$urgency_choice" in
        "a"|"A") urgency="relaxed" ;;
        "b"|"B") urgency="normal" ;;
        "c"|"C") urgency="urgent" ;;
        *) urgency="normal" ;;
    esac
    
    echo ""
    
    # 问题3: 项目类型
    echo -e "${CYAN}3. 你想要创建什么类型的项目？${NC}"
    echo "   a) 我还不确定，想先了解系统"
    echo "   b) 网站或Web应用"
    echo "   c) API或后端服务"
    echo "   d) 完整的应用系统"
    echo ""
    echo -n "请选择 (a/b/c/d): "
    read -r project_choice
    
    case "$project_choice" in
        "a"|"A") project_type="exploration" ;;
        "b"|"B") project_type="web" ;;
        "c"|"C") project_type="api" ;;
        "d"|"D") project_type="full_system" ;;
        *) project_type="web" ;;
    esac
    
    echo ""
    
    # 生成推荐
    generate_smart_recommendation "$experience" "$urgency" "$project_type"
}

# 生成智能推荐
generate_smart_recommendation() {
    local experience="$1"
    local urgency="$2"
    local project_type="$3"
    
    echo -e "${BLUE}🤖 AI正在分析你的回答...${NC}"
    
    # 模拟分析过程
    sleep 2
    
    echo -e "${GREEN}📊 为你量身定制的推荐:${NC}\n"
    
    # 基于回答生成推荐
    if [ "$urgency" = "urgent" ]; then
        echo -e "${YELLOW}⚡ 检测到你时间紧急，推荐：${NC}"
        echo -e "${GREEN}选择 '1) 🚀 快速体验模式'${NC}"
        echo "   → 30秒快速设置，立即开始项目"
        echo ""
        quick_experience_mode
    elif [ "$experience" = "beginner" ] && [ "$project_type" = "exploration" ]; then
        echo -e "${BLUE}📚 检测到你是新手且想先了解系统，推荐：${NC}"
        echo -e "${GREEN}选择 '2) 📖 详细教程模式'${NC}"
        echo "   → 5分钟深入了解，建立正确的理解"
        echo ""
        detailed_tutorial_mode
    elif [ "$project_type" != "exploration" ]; then
        echo -e "${MAGENTA}🎯 检测到你有明确的项目目标，推荐：${NC}"
        echo -e "${GREEN}选择 '3) 🎯 项目向导模式'${NC}"
        echo "   → 基于你的项目需求提供定制化指导"
        echo ""
        project_wizard_mode
    else
        echo -e "${CYAN}🎭 根据你的情况，推荐：${NC}"
        echo -e "${GREEN}选择 '2) 📖 详细教程模式'${NC}"
        echo "   → 全面了解系统，然后选择具体项目"
        echo ""
        detailed_tutorial_mode
    fi
}

# 显示功能清单
show_feature_list() {
    clear
    echo -e "${MAGENTA}📋 Claude Enhancer 5.0 完整功能清单${NC}\n"
    
    cat << 'EOF'
    ╔══════════════════════════════════════════════════════════════════╗
    ║                          核心功能                                 ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║ 🤖 智能Agent系统                                                  ║
    ║    ├─ 56+ 专业AI Agent (后端、前端、数据库、安全、测试等)            ║
    ║    ├─ 4-6-8 动态选择策略                                          ║
    ║    └─ 并行协作执行                                                ║
    ║                                                                  ║
    ║ 📋 8-Phase工作流                                                  ║
    ║    ├─ Phase 0: Git分支管理                                        ║
    ║    ├─ Phase 1: 需求分析                                           ║
    ║    ├─ Phase 2: 设计规划                                           ║
    ║    ├─ Phase 3: 代码实现                                           ║
    ║    ├─ Phase 4: 本地测试                                           ║
    ║    ├─ Phase 5: 代码提交                                           ║
    ║    ├─ Phase 6: 代码审查                                           ║
    ║    └─ Phase 7: 合并部署                                           ║
    ║                                                                  ║
    ║ 🔧 质量保证系统                                                    ║
    ║    ├─ 自动化Git Hooks                                             ║
    ║    ├─ 代码质量检查                                                 ║
    ║    ├─ 安全漏洞扫描                                                 ║
    ║    ├─ 测试覆盖率监控                                               ║
    ║    └─ 性能基准测试                                                 ║
    ║                                                                  ║
    ║ 🌐 多语言和可访问性                                                 ║
    ║    ├─ 中英文双语支持                                               ║
    ║    ├─ WCAG 2.1 可访问性                                          ║
    ║    ├─ 屏幕阅读器兼容                                               ║
    ║    └─ 键盘导航支持                                                 ║
    ║                                                                  ║
    ║ 📊 监控和报告                                                     ║
    ║    ├─ 实时性能监控                                                 ║
    ║    ├─ 详细执行报告                                                 ║
    ║    ├─ 错误追踪和恢复                                               ║
    ║    └─ 使用统计分析                                                 ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    支持的项目类型:
    ├─ 🌐 Web应用 (React, Vue, Angular, 原生HTML/CSS/JS)
    ├─ ⚙️  API服务 (REST, GraphQL, 微服务)
    ├─ 🗄️  数据库 (PostgreSQL, MongoDB, Redis, MySQL)
    ├─ 📱 移动应用 (React Native, Flutter, 原生)
    ├─ 🏢 企业系统 (ERP, CRM, 业务流程自动化)
    ├─ 🛒 电商平台 (商品管理, 支付集成, 订单系统)
    ├─ 🏥 医疗系统 (HIPAA合规, 患者管理)
    ├─ 💰 金融科技 (支付, 风控, 合规)
    ├─ 🎮 游戏应用 (Web游戏, 移动游戏)
    └─ 🔗 区块链 (智能合约, DeFi, NFT)
EOF
    
    echo ""
    echo -n -e "${CYAN}按Enter返回主菜单... ${NC}"
    read -r
}

# 显示下一步操作
show_next_steps() {
    echo -e "${GREEN}🚀 接下来你可以：${NC}\n"
    
    cat << 'EOF'
    ┌─ 立即开始 ────────────────────────────────────────────────────────┐
    │                                                                   │
    │  # 快速体验 - 创建一个简单项目                                       │
    │  echo "我想创建一个用户登录页面" | ./.claude/hooks/smart_agent_selector.sh
    │                                                                   │
    │  # 查看可用的帮助                                                   │
    │  ./.claude/help.sh                                                │
    │                                                                   │
    │  # 运行项目健康检查                                                  │
    │  ./.claude/scripts/health_check.py                               │
    │                                                                   │
    │  # 查看可用的Agent                                                  │
    │  ls .claude/agents/                                               │
    │                                                                   │
    └───────────────────────────────────────────────────────────────────┘
EOF
    
    echo ""
    echo -e "${BLUE}💡 提示: 随时运行 '.claude/welcome.sh' 重新打开此向导${NC}"
    echo -e "${BLUE}📚 文档: 查看 README.md 获取完整信息${NC}"
    echo ""
}

# 主函数
main() {
    # 检查是否在正确的目录
    if [ ! -d ".claude" ]; then
        echo -e "${RED}错误: 请在Claude Enhancer项目根目录中运行此脚本${NC}"
        echo -e "${YELLOW}提示: 确保当前目录包含.claude文件夹${NC}"
        exit 1
    fi
    
    show_welcome_banner
    
    # 检查环境
    if ! check_environment; then
        echo -e "${RED}环境检查失败。请先解决环境问题再继续。${NC}"
        exit 1
    fi
    
    while true; do
        show_learning_paths
        read -r choice
        
        case "$choice" in
            "1")
                clear
                quick_experience_mode
                break
                ;;
            "2")
                clear
                detailed_tutorial_mode
                break
                ;;
            "3")
                clear
                project_wizard_mode
                break
                ;;
            "4")
                clear
                smart_recommendation_mode
                break
                ;;
            "5")
                show_feature_list
                clear
                ;;
            "0")
                echo -e "${GREEN}👋 感谢使用Claude Enhancer！祝你开发愉快！${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}无效选择，请输入0-5之间的数字。${NC}"
                sleep 1
                clear
                show_welcome_banner
                ;;
        esac
    done
}

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi