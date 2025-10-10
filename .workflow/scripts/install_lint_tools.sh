#!/bin/bash

# Install Lint Tools - CI工具安装脚本
# 自动安装所有需要的Linting工具
# Version: 1.0.0

set -euo pipefail

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔧 安装Linting工具..."

# 安装yq（YAML解析）
install_yq() {
    if command -v yq &> /dev/null; then
        echo -e "${GREEN}✓ yq already installed${NC}"
        return 0
    fi

    echo "Installing yq..."
    if command -v wget &> /dev/null; then
        wget -q https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /tmp/yq
        sudo mv /tmp/yq /usr/local/bin/yq
        sudo chmod +x /usr/local/bin/yq
        echo -e "${GREEN}✓ yq installed${NC}"
    else
        echo -e "${YELLOW}⚠️  wget not found, trying Python yq${NC}"
        pip3 install yq || echo -e "${YELLOW}⚠️  yq installation failed${NC}"
    fi
}

# 安装shellcheck（Shell检查）
install_shellcheck() {
    if command -v shellcheck &> /dev/null; then
        echo -e "${GREEN}✓ shellcheck already installed${NC}"
        return 0
    fi

    echo "Installing shellcheck..."
    sudo apt-get update -qq && sudo apt-get install -y -qq shellcheck
    echo -e "${GREEN}✓ shellcheck installed${NC}"
}

# 安装Node.js工具
install_node_tools() {
    if [ ! -f "package.json" ]; then
        echo -e "${YELLOW}⚠️  No package.json found, skipping Node.js tools${NC}"
        return 0
    fi

    echo "Installing Node.js dependencies..."
    npm install
    echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
}

# 安装Python工具
install_python_tools() {
    echo "Installing Python tools..."
    pip3 install flake8 pylint pytest || echo -e "${YELLOW}⚠️  Some Python tools failed to install${NC}"
    echo -e "${GREEN}✓ Python tools installed${NC}"
}

# 主函数
main() {
    install_yq
    install_shellcheck
    install_node_tools
    install_python_tools

    echo -e "${GREEN}✅ All tools installed${NC}"
}

main "$@"
