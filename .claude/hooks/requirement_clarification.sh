#!/bin/bash
# Claude Hook: 需求澄清阶段
# 触发时机：UserPromptSubmit（用户每次发送消息时）
# 目的：提醒AI通过多轮对话问清楚所有业务决策点

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"

# 检查是否已经澄清需求
if [[ -f "$WORKFLOW_DIR/REQUIREMENTS_CLARIFIED" ]]; then
    # 已澄清，跳过
    exit 0
fi

# CRITICAL FIX: Check if trying to code without clarification
# If in execution mode WITHOUT clarification = HARD BLOCK
if [[ -f "$WORKFLOW_DIR/ACTIVE" ]] && [[ ! -f "$WORKFLOW_DIR/REQUIREMENTS_CLARIFIED" ]]; then
    # Coding without clarification - HARD BLOCK
    LOG_FILE="$WORKFLOW_DIR/logs/enforcement_violations.log"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$(date +'%F %T')] [requirement_clarification.sh] [BLOCK] Requirements not clarified before coding task" >> "$LOG_FILE"

    echo "🚨 Requirements not clarified before coding!" >&2
    echo "   Please complete requirement discussion first" >&2
    exit 1
fi

# If in execution mode WITH clarification, allow
if [[ -f "$WORKFLOW_DIR/ACTIVE" ]]; then
    exit 0
fi

# 输出AI提醒（这会在AI的上下文中显示）
cat <<'EOF'

╔═══════════════════════════════════════════════════════════════╗
║  ⚠️  需求澄清阶段 - AI行为指南                               ║
╚═══════════════════════════════════════════════════════════════╝

【重要】用户刚提出一个需求，你必须先通过多轮对话问清楚！

══════════════════════════════════════════════════════════════

【核心原则】

1️⃣  用人话，不用技术术语
   ❌ 错误："需要OAuth2.0吗？"
   ✅ 正确："需要微信登录吗？就是点一个按钮用微信账号登录，像很多App那样"

2️⃣  给例子和类比
   ✅ "像淘宝那样，下次打开直接进去，不用再输密码"
   ✅ "像银行卡密码，错3次就锁住"
   ✅ "像12306买票那样，需要输那种扭曲的验证码"

3️⃣  解释为什么要问
   ✅ "💡 为什么需要验证码？防止机器人疯狂试密码"
   ✅ "💡 为什么要锁定？防止有人用程序试10000次密码"
   ✅ "💡 为什么要复杂密码？简单密码像123456，几秒就能破解"

4️⃣  给选项，不要开放式问题
   ❌ 错误："您想要什么登录方式？"
   ✅ 正确："用什么登录？
           - A. 邮箱（像Gmail那样，输入xx@xx.com）
           - B. 手机号（输入11位手机号）
           - C. 用户名（自己起个名字，像QQ号那样）
           - D. 多种方式都可以"

══════════════════════════════════════════════════════════════

【你应该问什么】

✅ 只问用户需要决策的点：
   - 功能要不要？（要/不要）
   - 多个方案选哪个？（A/B/C/D）
   - 规则定多严？（宽松/严格）
   - 用户看到什么？（提示信息、按钮文字）
   - 特殊情况怎么处理？（给选项）

❌ 不要问技术实现细节：
   - "用JWT还是Session？"          ← 这是你自己决定
   - "数据库用MySQL还是MongoDB？"   ← 这是你自己决定
   - "前端用React还是Vue？"         ← 这是你自己决定
   - "用RESTful还是GraphQL？"       ← 这是你自己决定

用户不懂这些技术，你自己根据需求选择最合适的技术方案。

══════════════════════════════════════════════════════════════

【分轮提问策略】

第1轮：基础功能（3-5个问题）
  目的：了解核心功能要不要
  例如：
   - 用什么登录？
   - 需要"记住我"功能吗？
   - 需要"忘记密码"功能吗？
   - 需要第三方登录吗？（微信/QQ/Google）

第2轮：用户体验（3-5个问题）
  目的：了解交互流程和提示信息
  例如：
   - 密码输错了，提示什么？
   - 登录成功后去哪里？
   - 已登录状态访问登录页怎么办？
   - 需要退出登录按钮吗？

第3轮：特殊情况（3-5个问题）
  目的：了解边界情况处理
  例如：
   - 如果用户已经登录，再访问登录页面怎么办？
   - 允许同时多处登录吗？（同一账号在多个设备）
   - 需要登录历史记录吗？

第4轮：安全规则（3-5个问题，必须解释原因！）
  目的：了解安全策略（用户可能不懂为什么，要解释）
  例如：
   Q: "密码要多复杂？"
      A/B/C/D四个选项
      💡 为什么要复杂？简单密码容易被猜到...

   Q: "登录失败多次要锁定吗？"
      选项 + 💡 为什么要锁定？...

   Q: "'记住我'记多久？"
      选项 + 💡 为什么不永久？...

第5轮：总结确认
  目的：确保理解正确
  格式：
   ════════════════════════════════════════
   **您要的XX功能**：

   📧 **XX方面**
   - 具体内容

   ✅ **需要的**
   - 列表

   🚫 **不需要的**
   - 列表

   🔒 **规则**
   - 列表

   🎯 **交互流程**
   - 步骤

   ════════════════════════════════════════
   这样对吗？
   如果有不对的地方，请告诉我。
   如果都对，我就生成验收清单。

══════════════════════════════════════════════════════════════

【何时结束提问】

当满足以下条件时，结束提问：
✅ 用户说：没问题了 / 对的 / 确认 / 可以了
✅ 你问完了所有决策点
✅ 用户确认你的理解是正确的

【结束后要做什么】

1. 保存对话记录
   echo "完整对话" > .workflow/REQUIREMENTS_DIALOGUE.md

2. 生成验收清单（Checklist）
   根据对话生成验收项目
   保存到 .workflow/CHECKLIST.md

3. 标记需求已澄清
   touch .workflow/REQUIREMENTS_CLARIFIED

4. 启用自动模式
   touch .workflow/AUTO_MODE_ACTIVE

5. 开始Phase 2-7自动执行
   不再问用户，全自动完成

══════════════════════════════════════════════════════════════

【详细提问模板】

参考：.claude/requirement_questions.yml

══════════════════════════════════════════════════════════════

【记住】
- 用户是编程小白，不懂技术
- 多用例子、类比、生活化的说法
- 解释为什么要问（用💡标记）
- 给选项，不要让用户自己想
- 分多轮问，不要一次问太多（3-5个问题一轮）
- 确认理解后再开始实现

══════════════════════════════════════════════════════════════

EOF

# If in auto mode, skip prompting (requirements already clarified)
if [[ "${CE_AUTO_MODE:-false}" == "true" ]]; then
    exit 0
fi

# In manual mode, show the guidance above and allow discussion
exit 0
