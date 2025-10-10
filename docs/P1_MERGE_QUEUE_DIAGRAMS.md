# P1规划：Merge Queue架构图集

**版本**: 1.0
**日期**: 2025-10-10
**配套文档**: P1_MERGE_QUEUE_ARCHITECTURE.md

---

## 1. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Enhancer Workflow                     │
│                         (P0-P7 Phases)                          │
└────────────────────┬────────────────────────────────────────────┘
                     │ P6 (Release Phase)
                     ▼
         ┌───────────────────────┐
         │  Branch Protection    │
         │   (branch_helper.sh)  │
         └───────────┬───────────┘
                     │ Feature Branch Ready
                     ▼
    ┌────────────────────────────────────────┐
    │   Merge Queue Manager (NEW)            │
    │   ┌────────────────────────────────┐   │
    │   │  Queue Operations              │   │
    │   │  - enqueue()                   │   │
    │   │  - dequeue()                   │   │
    │   │  - status()                    │   │
    │   └────────────┬───────────────────┘   │
    │                ▼                        │
    │   ┌────────────────────────────────┐   │
    │   │  Conflict Pre-Check            │   │
    │   │  - git merge-tree              │   │
    │   │  - conflict_analyzer           │   │
    │   └────────────┬───────────────────┘   │
    │                ▼                        │
    │   ┌────────────────────────────────┐   │
    │   │  FIFO Scheduler                │   │
    │   │  - priority calculation        │   │
    │   │  - resource coordination       │   │
    │   └────────────┬───────────────────┘   │
    └────────────────┼────────────────────────┘
                     ▼
         ┌───────────────────────┐
         │  Mutex Lock (REUSE)   │
         │  (.workflow/lib/      │
         │   mutex_lock.sh)      │
         └───────────┬───────────┘
                     ▼
              ┌──────────────┐
              │  Git Merge   │
              │  to main     │
              └──────────────┘
```

---

## 2. 数据流图（Data Flow Diagram）

```
Terminal 1          Terminal 2          Terminal 3
    │                   │                   │
    │ feature/auth      │ feature/payment   │ feature/logging
    ▼                   ▼                   ▼
┌───────────────────────────────────────────────────┐
│           Merge Queue (queue.json)                │
│  ┌─────────────────────────────────────────────┐  │
│  │ Entry 1: {id: mq-001, status: QUEUED, ...} │  │
│  │ Entry 2: {id: mq-002, status: QUEUED, ...} │  │
│  │ Entry 3: {id: mq-003, status: QUEUED, ...} │  │
│  └─────────────────────────────────────────────┘  │
└───────────────────┬───────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   Processor Loop      │
        │   (Daemon Process)    │
        └───────────┬───────────┘
                    │ Dequeue Next
                    ▼
        ┌───────────────────────┐
        │  Conflict Pre-Check   │
        │  (git merge-tree)     │
        └───┬───────────────┬───┘
            │               │
     No Conflict      Has Conflict
            │               │
            ▼               ▼
    ┌──────────────┐   ┌─────────────────┐
    │   MERGING    │   │ CONFLICT_DETECTED│
    │   Status     │   │   Status         │
    └──────┬───────┘   └────────┬─────────┘
           │                    │
           │                    ▼
           │           ┌─────────────────┐
           │           │  Auto Rebase?   │
           │           └────┬────────┬───┘
           │                │ Yes    │ No
           │                ▼        ▼
           │        ┌───────────┐ ┌────────────────┐
           │        │  Rebase   │ │ MANUAL_REQUIRED│
           │        │  Success  │ │   Notify User  │
           │        └─────┬─────┘ └────────────────┘
           │              │
           │              ▼ Re-enqueue
           │        ┌───────────┐
           └───────>│   Mutex   │
                    │   Lock    │
                    └─────┬─────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  Git Merge    │
                  │  (Atomic Op)  │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │    MERGED     │
                  │   Status      │
                  └───────────────┘
```

---

## 3. 状态机详细转换图

```
                        ┌─────────────┐
                        │  User Input │
                        │ (merge req) │
                        └──────┬──────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │   SUBMITTED     │
                      │  Validation     │
                      └────┬────────┬───┘
                           │ Valid  │ Invalid
                           ▼        ▼
                  ┌─────────────┐ ┌──────────┐
                  │   QUEUED    │ │ REJECTED │
                  │  (waiting)  │ └──────────┘
                  └──────┬──────┘
                         │ Dequeued
                         ▼
              ┌───────────────────────┐
              │  CONFLICT_CHECK       │
              │  (git merge-tree)     │
              └───┬───────────────┬───┘
                  │ No Conflict   │ Has Conflict
                  ▼               ▼
        ┌──────────────────┐  ┌─────────────────────┐
        │    MERGING       │  │ CONFLICT_DETECTED   │
        │ (mutex locked)   │  │  Analyze conflicts  │
        └────┬────────┬────┘  └──────────┬──────────┘
             │ OK     │ Fail             │
             ▼        ▼                  ▼
     ┌─────────┐ ┌────────┐    ┌─────────────────────┐
     │ MERGED  │ │ FAILED │    │ Decision: Rebase?   │
     └─────────┘ └────────┘    └──┬──────────────┬───┘
                                  │ Auto         │ Manual
                                  ▼              ▼
                          ┌───────────────┐  ┌──────────────────┐
                          │REBASE_PENDING │  │ MANUAL_REQUIRED  │
                          │  (executing)  │  │ (wait for user)  │
                          └───┬───────┬───┘  └────────┬─────────┘
                              │ OK    │ Fail          │ Fixed
                              ▼       ▼               ▼
                         ┌─────────┐ ┌────────┐  ┌─────────┐
                         │ QUEUED  │ │ FAILED │  │ QUEUED  │
                         │ (retry) │ └────────┘  │ (retry) │
                         └─────────┘             └─────────┘


Legend:
━━━━━━━ Normal Flow
┄┄┄┄┄┄┄ Error Flow
━ ━ ━ ━ Retry Flow
```

---

## 4. 并发控制时序图（Sequence Diagram）

```
Terminal-1   Terminal-2   Queue Manager   Processor   Mutex Lock   Git
    │            │              │             │           │         │
    │ enqueue    │              │             │           │         │
    ├───────────────────────────>│             │           │         │
    │            │              │ Add Entry   │           │         │
    │            │              │ (mq-001)    │           │         │
    │<──────────────────────────┤             │           │         │
    │  Position:1│              │             │           │         │
    │            │ enqueue      │             │           │         │
    │            ├──────────────>│             │           │         │
    │            │              │ Add Entry   │           │         │
    │            │              │ (mq-002)    │           │         │
    │            │<─────────────┤             │           │         │
    │            │  Position:2  │             │           │         │
    │            │              │             │           │         │
    │            │              │   Dequeue   │           │         │
    │            │              │<────────────┤           │         │
    │            │              │  mq-001     │           │         │
    │            │              ├─────────────>│           │         │
    │            │              │             │           │         │
    │            │              │       Conflict Check    │         │
    │            │              │             ├───────────────────> │
    │            │              │             │           │  merge- │
    │            │              │             │           │  tree   │
    │            │              │             │<──────────────────┤ │
    │            │              │             │  No Conflict       │
    │            │              │             │           │         │
    │            │              │             │  Acquire Lock      │
    │            │              │             ├──────────>│         │
    │            │              │             │<──────────┤         │
    │            │              │             │  Locked   │         │
    │            │              │             │           │         │
    │            │              │             │      Execute Merge  │
    │            │              │             ├─────────────────────>│
    │            │              │             │           │  checkout│
    │            │              │             │           │  merge   │
    │            │              │             │           │  push    │
    │            │              │             │<────────────────────┤│
    │            │              │             │           │  Success │
    │            │              │             │           │         │
    │            │              │             │  Release Lock       │
    │            │              │             ├──────────>│         │
    │            │              │             │<──────────┤         │
    │            │              │   Update Status         │         │
    │            │              │<────────────┤           │         │
    │            │              │  MERGED     │           │         │
    │            │              │             │           │         │
    │ Notify     │              │             │           │         │
    │<──────────────────────────┤             │           │         │
    │  Success   │              │             │           │         │
    │            │              │   Dequeue Next          │         │
    │            │              │<────────────┤           │         │
    │            │              │  mq-002     │           │         │
    │            │              │             │           │         │
```

---

## 5. 模块依赖图

```
┌─────────────────────────────────────────────────────────┐
│             merge_queue_manager.sh (Main)               │
└──────────┬──────────────────────────────────────────────┘
           │
           ├──> queue_operations.sh
           │    ├─ enqueue()
           │    ├─ dequeue()
           │    ├─ update_status()
           │    └─ get_status()
           │
           ├──> state_machine.sh
           │    ├─ validate_transition()
           │    ├─ apply_state_change()
           │    └─ get_valid_transitions()
           │
           ├──> persistence.sh
           │    ├─ save_queue()
           │    ├─ load_queue()
           │    ├─ backup_queue()
           │    └─ restore_from_backup()
           │
           ├──> conflict_detection/
           │    │
           │    ├──> git_merge_tree.sh
           │    │    ├─ precheck_conflict()
           │    │    ├─ analyze_conflict_type()
           │    │    └─ extract_conflict_files()
           │    │
           │    ├──> conflict_analyzer.sh
           │    │    ├─ classify_conflict()
           │    │    ├─ estimate_complexity()
           │    │    └─ recommend_strategy()
           │    │
           │    └──> rebase_advisor.sh
           │         ├─ can_auto_rebase()
           │         ├─ execute_rebase()
           │         └─ rollback_on_failure()
           │
           ├──> scheduler/
           │    │
           │    ├──> fifo_scheduler.sh
           │    │    ├─ get_next_task()
           │    │    ├─ calculate_wait_time()
           │    │    └─ reorder_queue()
           │    │
           │    ├──> priority_engine.sh (FUTURE)
           │    │    ├─ calculate_priority()
           │    │    ├─ apply_priority_rules()
           │    │    └─ dynamic_adjustment()
           │    │
           │    └──> resource_manager.sh
           │         ├─ check_resource_availability()
           │         ├─ allocate_resource()
           │         └─ release_resource()
           │
           ├──> integration/
           │    │
           │    ├──> mutex_adapter.sh
           │    │    ├─ acquire_merge_lock()
           │    │    ├─ release_merge_lock()
           │    │    └─ check_lock_status()
           │    │    │
           │    │    └───> ../../.workflow/lib/mutex_lock.sh (REUSE)
           │    │
           │    ├──> workflow_hooks.sh
           │    │    ├─ integrate_with_p6()
           │    │    ├─ trigger_on_merge()
           │    │    └─ post_merge_actions()
           │    │
           │    └──> notification.sh
           │         ├─ send_notification()
           │         ├─ write_notification_file()
           │         └─ log_notification()
           │
           └──> utils/
                ├──> logger.sh
                │    ├─ log_info()
                │    ├─ log_warn()
                │    ├─ log_error()
                │    └─ log_success()
                │
                ├──> validator.sh
                │    ├─ validate_branch()
                │    ├─ validate_target()
                │    └─ validate_queue_entry()
                │
                └──> metrics.sh
                     ├─ record_metric()
                     ├─ calculate_percentile()
                     └─ generate_report()
```

---

## 6. 文件系统布局

```
Claude Enhancer 5.0/
├── .workflow/
│   ├── lib/
│   │   ├── mutex_lock.sh              # 现有（复用）
│   │   ├── conflict_detector.sh       # 现有（复用）
│   │   └── merge_queue_manager.sh     # 新增（主入口）
│   │
│   ├── merge_queue/                   # 新增目录
│   │   ├── queue.json                 # 队列主文件
│   │   │   └── Format: [
│   │   │         {queue_id, status, ...},
│   │   │         ...
│   │   │       ]
│   │   │
│   │   ├── locks/                     # 锁文件目录
│   │   │   ├── queue.lock             # 队列操作锁
│   │   │   └── processor.lock         # Processor互斥锁
│   │   │
│   │   ├── history/                   # 历史记录（按天）
│   │   │   ├── 2025-10-10.jsonl
│   │   │   └── 2025-10-11.jsonl
│   │   │
│   │   ├── checkpoints/               # 恢复检查点
│   │   │   ├── queue_backup_20251010_180000.json
│   │   │   └── queue_backup_20251010_181000.json
│   │   │
│   │   ├── notifications/             # Terminal通知文件
│   │   │   ├── terminal-1.txt
│   │   │   └── terminal-2.txt
│   │   │
│   │   ├── conflicts.log              # 冲突审计日志
│   │   └── metrics.jsonl              # 性能指标
│   │
│   └── modules/                       # 新增模块目录
│       └── merge_queue/
│           ├── core/
│           │   ├── queue_operations.sh
│           │   ├── state_machine.sh
│           │   └── persistence.sh
│           │
│           ├── conflict_detection/
│           │   ├── git_merge_tree.sh
│           │   ├── conflict_analyzer.sh
│           │   └── rebase_advisor.sh
│           │
│           ├── scheduler/
│           │   ├── fifo_scheduler.sh
│           │   ├── priority_engine.sh
│           │   └── resource_manager.sh
│           │
│           ├── integration/
│           │   ├── mutex_adapter.sh
│           │   ├── workflow_hooks.sh
│           │   └── notification.sh
│           │
│           └── utils/
│               ├── logger.sh
│               ├── validator.sh
│               └── metrics.sh
│
├── .claude/
│   └── hooks/
│       └── workflow_enforcer.sh       # 修改（添加P6集成）
│
└── docs/
    ├── P1_MERGE_QUEUE_ARCHITECTURE.md # 本规划文档
    └── P1_MERGE_QUEUE_DIAGRAMS.md     # 本架构图集
```

---

## 7. 性能监控仪表板设计

```
┌──────────────────────────────────────────────────────────────┐
│          Merge Queue Performance Dashboard                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  实时统计                                    当前时间: 18:45 │
│  ┌────────────┬────────────┬────────────┬────────────┐      │
│  │  QUEUED    │  MERGING   │  MERGED    │  FAILED    │      │
│  │     5      │     1      │    42      │     2      │      │
│  └────────────┴────────────┴────────────┴────────────┘      │
│                                                               │
│  等待时间分布 (过去1小时)                                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │ P50:  28s  ████████████████████░░░░░░░░░  Target│       │
│  │ P90:  55s  ███████████████████████████░░  Target│       │
│  │ P99: 115s  ████████████████████████████████████  │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
│  吞吐量趋势                                                    │
│  ┌──────────────────────────────────────────────────┐       │
│  │ 18:00  ██████  6 merges                          │       │
│  │ 18:15  ████    4 merges                          │       │
│  │ 18:30  ████████ 8 merges                         │       │
│  │ 18:45  ██████  6 merges                          │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
│  冲突检测统计                                                  │
│  ┌──────────────────────────────────────────────────┐       │
│  │ 总检测次数: 50                                    │       │
│  │ 发现冲突:   8  (16%)                              │       │
│  │ 自动Rebase: 5  (10%)                              │       │
│  │ 需人工介入: 3  (6%)                               │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
│  当前队列 (最近5条)                                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ID       Branch            Status    Wait Time       │  │
│  │ mq-001   feature/auth      MERGING   45s            │  │
│  │ mq-002   feature/payment   QUEUED    12s            │  │
│  │ mq-003   feature/logging   QUEUED    5s             │  │
│  │ mq-004   feature/search    QUEUED    2s             │  │
│  │ mq-005   feature/export    QUEUED    0s             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  [R] Refresh  [Q] Quit  [D] Details  [C] Clear History      │
└──────────────────────────────────────────────────────────────┘
```

**实现脚本**:
```bash
#!/bin/bash
# .workflow/cli/dashboard_merge_queue.sh

watch -n 1 '
clear
cat << EOF
┌──────────────────────────────────────────────────────────────┐
│          Merge Queue Performance Dashboard                   │
├──────────────────────────────────────────────────────────────┤
│  实时统计                                    当前时间: $(date +%H:%M) │
│  ┌────────────┬────────────┬────────────┬────────────┐      │
│  │  QUEUED    │  MERGING   │  MERGED    │  FAILED    │      │
│  │  $(jq "[.[] | select(.status == \"QUEUED\")] | length" queue.json | xargs printf "%5s") │  $(jq "[.[] | select(.status == \"MERGING\")] | length" queue.json | xargs printf "%5s") │  $(jq "[.[] | select(.status == \"MERGED\")] | length" queue.json | xargs printf "%5s") │  $(jq "[.[] | select(.status == \"FAILED\")] | length" queue.json | xargs printf "%5s") │      │
│  └────────────┴────────────┴────────────┴────────────┘      │
EOF
'
```

---

## 8. 错误恢复流程图

```
┌─────────────────────┐
│ 系统启动/重启       │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────┐
│ 检查队列完整性           │
│ validate_queue_integrity()│
└──────┬────────────┬──────┘
       │ Valid      │ Invalid
       ▼            ▼
┌─────────────┐  ┌─────────────────┐
│ 继续        │  │ 从备份恢复      │
└──────┬──────┘  │ restore_backup()│
       │         └────────┬─────────┘
       │                  │
       └──────────┬───────┘
                  ▼
       ┌────────────────────────┐
       │ 扫描MERGING状态任务    │
       │ find_incomplete_merges()│
       └──────┬─────────────────┘
              │
              ▼
       ┌─────────────────┐
       │ 有未完成任务？  │
       └──┬──────────┬───┘
          │ No       │ Yes
          ▼          ▼
    ┌─────────┐  ┌──────────────────┐
    │ 正常启动│  │ 检查Git状态      │
    └─────────┘  │ is_merge_active()│
                 └──┬──────────┬────┘
                    │ Clean    │ In Progress
                    ▼          ▼
           ┌────────────────┐ ┌──────────────────┐
           │ 重新入队       │ │ 标记MANUAL_      │
           │ → QUEUED       │ │ REQUIRED         │
           └────────────────┘ └──────────────────┘
                    │                  │
                    └──────────┬───────┘
                               ▼
                    ┌────────────────────┐
                    │ 清理孤儿锁         │
                    │ cleanup_orphan_    │
                    │ locks()            │
                    └──────────┬─────────┘
                               ▼
                    ┌────────────────────┐
                    │ 发送恢复通知       │
                    │ notify_recovery()  │
                    └──────────┬─────────┘
                               ▼
                    ┌────────────────────┐
                    │ 启动Processor      │
                    │ merge_queue_       │
                    │ process()          │
                    └────────────────────┘
```

---

## 9. 优先级队列扩展设计（预留）

```
当前FIFO队列:
┌────────┬────────┬────────┬────────┬────────┐
│ mq-001 │ mq-002 │ mq-003 │ mq-004 │ mq-005 │
│  P=5   │  P=5   │  P=5   │  P=5   │  P=5   │
└────────┴────────┴────────┴────────┴────────┘
         先入先出 (FIFO)

未来优先级队列:
┌────────┬────────┬────────┬────────┬────────┐
│ mq-006 │ mq-001 │ mq-003 │ mq-002 │ mq-004 │
│ P=8    │  P=7   │  P=5   │  P=5   │  P=3   │
│hotfix  │small   │normal  │normal  │experi- │
│        │change  │        │        │ment    │
└────────┴────────┴────────┴────────┴────────┘
         高优先级在前

优先级计算公式:
┌───────────────────────────────────────┐
│ priority = base_priority              │
│          + branch_type_weight         │
│          + small_change_bonus         │
│          + wait_time_bonus            │
│          - conflict_penalty           │
│                                       │
│ 例子:                                 │
│ hotfix/critical-bug:                  │
│   = 5 (base)                          │
│   + 3 (hotfix weight)                 │
│   + 2 (3 files changed)               │
│   + 0 (just queued)                   │
│   - 0 (no conflict)                   │
│   = 10 (高优先级)                     │
└───────────────────────────────────────┘
```

---

## 10. 测试拓扑图

```
测试金字塔:

              ┌──────────────┐
              │ E2E Tests    │  ← 混沌测试
              │ (Chaos)      │    进程crash恢复
              └──────────────┘    网络故障模拟
                     ▲
                     │
           ┌─────────────────────┐
           │ Integration Tests   │  ← 多Terminal场景
           │                     │    冲突检测+Rebase
           │                     │    完整merge流程
           └─────────────────────┘
                     ▲
                     │
        ┌────────────────────────────┐
        │   Unit Tests               │  ← 单个函数测试
        │   - enqueue()              │    状态转换
        │   - dequeue()              │    冲突检测
        │   - conflict_precheck()    │    数据持久化
        │   - auto_rebase()          │
        └────────────────────────────┘


测试矩阵:
┌─────────────┬──────────┬──────────┬──────────┬──────────┐
│ Scenario    │ Unit     │ Integr.  │ Perf.    │ Chaos    │
├─────────────┼──────────┼──────────┼──────────┼──────────┤
│ Enqueue     │    ✓     │    ✓     │    ✓     │          │
│ Dequeue     │    ✓     │    ✓     │    ✓     │          │
│ Conflict    │    ✓     │    ✓     │          │          │
│ Rebase      │    ✓     │    ✓     │          │    ✓     │
│ Merge       │          │    ✓     │    ✓     │    ✓     │
│ Crash       │          │          │          │    ✓     │
│ Network     │          │          │          │    ✓     │
│ Deadlock    │          │    ✓     │          │    ✓     │
│ 10 Conc.    │          │          │    ✓     │          │
│ 50 Conc.    │          │          │    ✓     │          │
└─────────────┴──────────┴──────────┴──────────┴──────────┘
```

---

## 附录：符号说明

```
图形符号:
┌─┐  ┌───┐
│ │  │   │  矩形框：进程/模块/组件
└─┘  └───┘

   ◆       菱形：决策点
  ╱ ╲
 ╱   ╲
╲     ╱
 ╲   ╱
  ╲ ╱

   ▼       箭头：流向/依赖

━━━━━━━   双线：强调/重要

┄┄┄┄┄┄┄   虚线：可选/预留

线条风格:
─────      直线：正常流程
━ ━ ━      间断：错误处理
┈┈┈┈┈      点线：数据流
═════      双线：并发/锁

状态标记:
✓  成功/完成
✗  失败/错误
⚠  警告
🔒 锁定
🔄 重试
📋 队列
⏱  超时
```

---

## 总结

本架构图集提供了Merge Queue Manager的10个核心视图：

1. **系统架构总览** - 组件关系
2. **数据流图** - 数据流转路径
3. **状态机转换图** - 完整状态流转
4. **并发控制时序图** - 多Terminal交互
5. **模块依赖图** - 代码组织结构
6. **文件系统布局** - 目录和文件组织
7. **性能监控仪表板** - 运维可视化
8. **错误恢复流程** - 异常处理机制
9. **优先级队列设计** - 未来扩展
10. **测试拓扑图** - 测试策略全景

这些图表将指导P2（骨架搭建）和P3（实现编码）阶段的工作。

---

**下一步行动**:
- [ ] P2：创建目录结构
- [ ] P2：实现核心接口（空函数）
- [ ] P3：逐模块实现功能
- [ ] P4：按测试矩阵编写测试

*生成时间: 2025-10-10*
*Claude Enhancer 5.3 - Production-Ready AI Programming*
