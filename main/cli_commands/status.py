"""
Perfect21状态命令处理
"""

def handle_status(p21) -> None:
    """打印系统状态"""
    result = p21.status()

    if result['success']:
        status = result['status']
        print("🚀 Perfect21系统状态")
        print("=" * 50)

        # Perfect21信息
        p21_info = status['perfect21']
        print(f"版本: {p21_info['version']}")
        print(f"模式: {p21_info['mode']}")
        print(f"核心Agent: {'✅ 可用' if p21_info['core_agents_available'] else '❌ 不可用'}")
        print(f"Agent数量: {p21_info['agent_count']}")

        # 项目信息
        project = status['project']
        print(f"\n📁 项目信息")
        print(f"Git仓库: {'✅ 是' if project['is_git_repo'] else '❌ 否'}")
        print(f"当前分支: {project.get('current_branch', '未知')}")
        print(f"Perfect21结构: {'✅ 完整' if project['perfect21_structure'] else '❌ 不完整'}")

        # 分支状态
        if 'branches' in status and status['branches'].get('current_branch'):
            branch_info = status['branches']['current_branch']
            print(f"\n🌿 当前分支")
            print(f"名称: {branch_info['name']}")
            print(f"类型: {branch_info['info']['type']}")
            print(f"保护级别: {branch_info['info']['protection_level']}")

    else:
        print(f"❌ 获取状态失败: {result.get('message', '未知错误')}")