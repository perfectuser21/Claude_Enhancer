#!/bin/bash
# 测试Agent输出汇总机制

echo "🧪 测试Agent输出汇总器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 模拟多个Agent的输出
cat > /tmp/test_agent_output.json << 'EOF'
[
  {
    "agent": "backend-architect",
    "output": "设计了微服务架构\n- 使用Docker容器化\n- 采用Kong API网关\n- PostgreSQL作为主数据库\n- Redis缓存层\n- RabbitMQ消息队列\n详细的技术栈选择...\n更多架构细节...\n性能优化方案...\n扩展性设计...\n安全考虑...\n部署策略...",
    "status": "completed"
  },
  {
    "agent": "frontend-specialist",
    "output": "前端技术方案\n- React 18 + TypeScript\n- Redux Toolkit状态管理\n- Material-UI组件库\n- Webpack 5打包\n- Jest单元测试\n详细的组件设计...\n路由配置...\n状态管理方案...\n性能优化...\n响应式设计...",
    "status": "completed"
  },
  {
    "agent": "database-specialist",
    "output": "数据库设计方案\n- 用户表设计\n- 订单表设计\n- 产品表设计\n- 索引优化\n- 分区策略\n详细的表结构...\n关系设计...\n查询优化...\n备份策略...\n迁移方案...",
    "status": "completed"
  },
  {
    "agent": "test-engineer",
    "output": "测试策略\n- 单元测试覆盖率80%\n- 集成测试自动化\n- E2E测试场景\n- 性能测试基准\n- 安全测试清单\n测试用例设计...\n测试数据准备...\nCI/CD集成...\n测试报告...",
    "status": "completed"
  },
  {
    "agent": "devops-engineer",
    "output": "部署方案\n- Kubernetes编排\n- GitLab CI/CD\n- Prometheus监控\n- ELK日志收集\n- 自动扩缩容\n详细的部署流程...\n监控指标...\n告警规则...\n灾备方案...\n回滚策略...",
    "status": "completed"
  }
]
EOF

echo "📝 原始输出大小："
wc -l /tmp/test_agent_output.json

echo ""
echo "🔄 执行汇总..."
python3 /home/xx/dev/Perfect21/.claude/hooks/agent-summarizer.py /tmp/test_agent_output.json > /tmp/summary_result.json

echo ""
echo "📊 汇总结果大小："
wc -l /tmp/summary_result.json

echo ""
echo "✅ 汇总内容预览："
python3 -m json.tool /tmp/summary_result.json | head -30

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 对比："
echo "- 原始: $(wc -l < /tmp/test_agent_output.json) 行"
echo "- 汇总: $(wc -l < /tmp/summary_result.json) 行"
echo "- 压缩率: $(echo "scale=2; 100 - ($(wc -l < /tmp/summary_result.json) * 100 / $(wc -l < /tmp/test_agent_output.json))" | bc)%"

# 测试collector
echo ""
echo "🔄 测试Output Collector..."
echo '<function_calls><invoke name="Task"><parameter name="subagent_type">backend-architect</parameter></invoke></function_calls>' | python3 /home/xx/dev/Perfect21/.claude/hooks/agent-output-collector.py

echo ""
echo "✅ 测试完成！"