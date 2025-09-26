#!/bin/bash
# Claude Enhancer 5.1 快速诊断脚本

set -e

NAMESPACE="claude-enhancer"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Claude Enhancer 5.1 快速诊断"
echo "================================"

# 1. 基础健康检查
echo ""
echo "1. 基础健康检查"
echo "----------------"

# 健康端点检查
if curl -f -s -m 10 http://claude-enhancer.example.com/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康检查端点正常${NC}"
else
    echo -e "${RED}❌ 健康检查端点异常${NC}"
fi

# 2. Pod状态检查
echo ""
echo "2. Pod状态检查"
echo "---------------"
kubectl get pods -n "$NAMESPACE" -o wide | head -10

# 3. 服务状态检查
echo ""
echo "3. 服务状态检查"
echo "---------------"
kubectl get services -n "$NAMESPACE"

# 4. 资源使用检查
echo ""
echo "4. 资源使用检查"
echo "---------------"
echo "节点资源:"
kubectl top nodes 2>/dev/null || echo "无法获取节点资源信息"

echo ""
echo "Pod资源:"
kubectl top pods -n "$NAMESPACE" 2>/dev/null || echo "无法获取Pod资源信息"

# 5. 最近错误日志
echo ""
echo "5. 最近错误日志 (最近5分钟)"
echo "-------------------------"
kubectl logs -l app=claude-enhancer -n "$NAMESPACE" --since=5m | grep -i error | tail -10 || echo "未发现错误日志"

# 6. 数据库连接检查
echo ""
echo "6. 数据库连接检查"
echo "----------------"
if kubectl get pod postgres-0 -n "$NAMESPACE" > /dev/null 2>&1; then
    if kubectl exec -it postgres-0 -n "$NAMESPACE" -- psql -U claude_enhancer -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 数据库连接正常${NC}"
    else
        echo -e "${RED}❌ 数据库连接失败${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  数据库Pod未找到${NC}"
fi

echo ""
echo "诊断完成！如需详细分析，请查看具体日志。"
