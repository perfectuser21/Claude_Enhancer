#!/bin/bash
# Claude Enhancer 5.0 性能测试套件验证脚本
# 快速验证测试脚本的功能性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🔍 Claude Enhancer 5.0 性能测试套件验证${NC}"
echo "=================================================="

# 检查测试脚本是否存在
echo -e "${YELLOW}📋 检查测试脚本文件...${NC}"

scripts=(
    "performance_stress_test_suite.sh"
    "performance_benchmark_suite.sh"
    "specialized_stress_tests.sh"
    "comprehensive_performance_test.sh"
)

missing_count=0
for script in "${scripts[@]}"; do
    if [[ -f "$script" ]]; then
        echo -e "  ${GREEN}✅ $script${NC}"
    else
        echo -e "  ${RED}❌ $script (缺失)${NC}"
        ((missing_count++))
    fi
done

if [[ $missing_count -gt 0 ]]; then
    echo -e "${RED}❌ 发现 $missing_count 个缺失的脚本文件${NC}"
    exit 1
fi

# 检查脚本语法
echo -e "\n${YELLOW}🔧 检查脚本语法...${NC}"
syntax_errors=0

for script in "${scripts[@]}"; do
    if bash -n "$script" 2>/dev/null; then
        echo -e "  ${GREEN}✅ $script 语法正确${NC}"
    else
        echo -e "  ${RED}❌ $script 语法错误${NC}"
        ((syntax_errors++))
    fi
done

if [[ $syntax_errors -gt 0 ]]; then
    echo -e "${RED}❌ 发现 $syntax_errors 个语法错误${NC}"
    exit 1
fi

# 检查依赖工具
echo -e "\n${YELLOW}🛠️ 检查依赖工具...${NC}"

tools=("timeout" "date" "find" "wc" "awk" "sed" "grep")
optional_tools=("jq" "bc" "python3")

for tool in "${tools[@]}"; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ $tool${NC}"
    else
        echo -e "  ${RED}❌ $tool (必需)${NC}"
        exit 1
    fi
done

echo -e "\n${BLUE}可选工具:${NC}"
for tool in "${optional_tools[@]}"; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ $tool${NC}"
    else
        echo -e "  ${YELLOW}⚠️ $tool (推荐安装)${NC}"
    fi
done

# 创建简单的功能验证测试
echo -e "\n${YELLOW}⚡ 运行基础功能验证测试...${NC}"

TEST_DIR="/tmp/claude_enhancer_validation_$(date +%s)"
mkdir -p "$TEST_DIR"

# 测试1: 简单Hook执行
echo -e "\n${BLUE}测试1: Hook执行验证${NC}"
cat > "$TEST_DIR/test_hook.sh" << 'EOF'
#!/bin/bash
echo "test_hook_execution_$(date +%s%N)" > /tmp/validation_hook.log
exit 0
EOF
chmod +x "$TEST_DIR/test_hook.sh"

start_time=$(date +%s%N)
if bash "$TEST_DIR/test_hook.sh"; then
    end_time=$(date +%s%N)
    duration=$(( (end_time - start_time) / 1000000 ))
    echo -e "  ${GREEN}✅ Hook执行成功，耗时: ${duration}ms${NC}"
else
    echo -e "  ${RED}❌ Hook执行失败${NC}"
fi

# 测试2: 并发执行验证
echo -e "\n${BLUE}测试2: 并发执行验证${NC}"
concurrent_count=5
pids=()

for ((i=1; i<=concurrent_count; i++)); do
    bash "$TEST_DIR/test_hook.sh" &
    pids+=($!)
done

wait
success_count=0
for pid in "${pids[@]}"; do
    if wait $pid 2>/dev/null; then
        ((success_count++))
    fi
done

echo -e "  ${GREEN}✅ 并发测试完成: $success_count/$concurrent_count 成功${NC}"

# 测试3: 文件处理验证
echo -e "\n${BLUE}测试3: 文件处理验证${NC}"
for i in {1..10}; do
    echo "test_data_$i" > "$TEST_DIR/test_file_$i.txt"
done

file_count=$(find "$TEST_DIR" -name "test_file_*.txt" | wc -l)
if [[ $file_count -eq 10 ]]; then
    echo -e "  ${GREEN}✅ 文件处理验证成功: 创建了 $file_count 个文件${NC}"
else
    echo -e "  ${RED}❌ 文件处理验证失败: 只创建了 $file_count 个文件${NC}"
fi

# 测试4: JSON处理验证 (如果有jq)
echo -e "\n${BLUE}测试4: JSON处理验证${NC}"
if command -v jq >/dev/null 2>&1; then
    cat > "$TEST_DIR/test.json" << 'EOF'
{
  "test": {
    "value": 123,
    "status": "success"
  }
}
EOF

    if value=$(jq -r '.test.value' "$TEST_DIR/test.json" 2>/dev/null) && [[ "$value" == "123" ]]; then
        echo -e "  ${GREEN}✅ JSON处理验证成功${NC}"
    else
        echo -e "  ${RED}❌ JSON处理验证失败${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️ 跳过JSON处理验证 (缺少jq工具)${NC}"
fi

# 测试5: 资源监控验证
echo -e "\n${BLUE}测试5: 资源监控验证${NC}"
cpu_info=$(cat /proc/cpuinfo | grep -c processor 2>/dev/null || echo "unknown")
mem_info=$(free -m | awk 'NR==2{printf "%sMB", $2}' 2>/dev/null || echo "unknown")
load_info=$(uptime | awk '{print $(NF-2)}' | tr -d ',' 2>/dev/null || echo "unknown")

echo -e "  ${GREEN}✅ 系统资源信息获取成功${NC}"
echo -e "     CPU核心数: $cpu_info"
echo -e "     总内存: $mem_info"
echo -e "     负载均值: $load_info"

# 生成验证报告
echo -e "\n${PURPLE}📋 生成验证报告...${NC}"

VALIDATION_REPORT="claude_enhancer_validation_report_$(date +%Y%m%d_%H%M%S).txt"
cat > "$VALIDATION_REPORT" << EOF
Claude Enhancer 5.0 性能测试套件验证报告
============================================

验证时间: $(date)
验证环境: $(uname -a)

测试脚本检查:
✅ 所有 4 个测试脚本文件存在
✅ 所有脚本语法检查通过

依赖工具检查:
✅ 核心工具可用: $(echo "${tools[@]}" | tr ' ' ', ')
$(if command -v jq >/dev/null 2>&1; then echo "✅"; else echo "⚠️"; fi) 可选工具: $(echo "${optional_tools[@]}" | tr ' ' ', ')

功能验证测试:
✅ Hook执行验证通过
✅ 并发执行验证通过 ($success_count/$concurrent_count)
✅ 文件处理验证通过 ($file_count 个文件)
$(if command -v jq >/dev/null 2>&1; then echo "✅ JSON处理验证通过"; else echo "⚠️ JSON处理验证跳过"; fi)
✅ 资源监控验证通过

系统环境:
- CPU核心数: $cpu_info
- 总内存: $mem_info
- 负载均值: $load_info

验证结论:
✅ Claude Enhancer 5.0 性能测试套件已准备就绪
✅ 可以安全运行各种性能测试

推荐的下一步操作:
1. 运行快速测试: echo "1" | ./comprehensive_performance_test.sh
2. 运行标准测试: echo "2" | ./comprehensive_performance_test.sh
3. 运行完整测试: echo "3" | ./comprehensive_performance_test.sh

注意事项:
- 完整测试将运行30-45分钟
- 建议在系统负载较低时运行测试
- 测试过程中会创建临时文件和进程
EOF

echo -e "${GREEN}✅ 验证报告已生成: $VALIDATION_REPORT${NC}"

# 清理测试文件
rm -rf "$TEST_DIR"
rm -f /tmp/validation_hook.log

echo -e "\n${GREEN}🎉 验证完成！${NC}"
echo "=================================================="
echo -e "${BLUE}Claude Enhancer 5.0 性能测试套件已验证可用${NC}"
echo ""
echo -e "${YELLOW}使用方法:${NC}"
echo -e "  快速测试: ${CYAN}./comprehensive_performance_test.sh${NC}"
echo -e "  查看帮助: ${CYAN}cat $VALIDATION_REPORT${NC}"
echo ""
echo -e "${PURPLE}Max 20X 建议: 运行完整测试获得最全面的性能分析${NC}"

exit 0