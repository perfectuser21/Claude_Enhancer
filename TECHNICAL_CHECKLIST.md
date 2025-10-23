# CE Comprehensive Dashboard v2 - Technical Checklist

**Version**: 7.2.0
**Created**: 2025-10-23
**Purpose**: Technical implementation guide for CE Dashboard v2 development

---

## 📋 Overview

This checklist defines the technical requirements, architecture decisions, and implementation tasks for building the Comprehensive CE Dashboard v2.

**Architecture**: Two-section dashboard extending existing dashboard.py

**Data Sources**:
- `.claude/DECISIONS.md` (7.9KB) - Decision history
- `.claude/memory-cache.json` (5.8KB) - Context cache
- `.claude/decision-index.json` - Archive index
- `docs/CAPABILITY_MATRIX.md` (479 lines) - C0-C9 capabilities
- `tools/web/dashboard.html` (1060 lines) - F001-F012 features
- `.temp/ce_events.jsonl` - Telemetry events (existing)

---

## 🏗️ Section 1: Architecture Design

### 1.1 System Architecture

**Decision**: Extend existing `tools/dashboard.py` (not rewrite)

**Rationale**:
- ✅ Telemetry system (v7.1.2) already working
- ✅ HTTP server infrastructure ready
- ✅ Auto-refresh mechanism in place
- ✅ API endpoint pattern established

**Integration Strategy**:
```python
# Current (v7.1.2): Single project monitoring
dashboard.py (660 lines)
├── /api/progress
├── /api/events
├── /api/stats
└── /api/health

# Target (v7.2.0): Comprehensive dashboard
dashboard.py (extended to ~1200 lines)
├── /                           # New: Two-section HTML
├── /api/capabilities           # New: CE能力数据
├── /api/learning               # New: 学习系统数据
├── /api/projects               # Renamed from /api/progress
├── /api/events                 # Keep: Event list
├── /api/stats                  # Keep: Statistics
└── /api/health                 # Keep: Health check
```

### 1.2 Data Layer Architecture

**Parsing Modules** (to be implemented):
```python
class CapabilityParser:
    """Parse CAPABILITY_MATRIX.md → Structured data"""
    def parse_capability_matrix(self) -> List[Capability]:
        # Extract C0-C9 capabilities with:
        # - Capability ID
        # - Name (Chinese + English)
        # - Type (Force/Validation/Protection)
        # - Assurance Level (保障力等级)
        # - Verification Logic
        # - Failure Symptoms
        # - Remediation Actions

class LearningSystemParser:
    """Parse learning system files → Structured data"""
    def parse_decisions(self) -> List[Decision]:
        # Parse DECISIONS.md markdown
        # Extract: date, title, decision, rationale, prohibited_ops, allowed_ops

    def parse_memory_cache(self) -> Dict:
        # Parse memory-cache.json
        # Extract: recent_decisions with importance levels

    def parse_decision_index(self) -> Dict:
        # Parse decision-index.json
        # Extract: archive references by month

class FeatureParser:
    """Parse tools/web/dashboard.html → Feature data"""
    def extract_features(self) -> List[Feature]:
        # Extract F001-F012 feature cards
        # Parse: ID, name, description, priority, category, icon

class ProjectMonitor:
    """Monitor multiple projects via telemetry"""
    def read_project_events(self, project_path: str) -> List[Event]:
        # Read .temp/ce_events.jsonl from each project
        # Support multiple project directories
```

### 1.3 Frontend Integration

**Reuse Approach**:
- Extract CSS/styles from `tools/web/dashboard.html`
- Reuse feature card HTML templates
- Adapt two-column layout for capabilities + monitoring

**Layout Structure**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="5">
    <style>
        /* Reuse styles from dashboard.html */
        .two-column-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
    </style>
</head>
<body>
    <div class="two-column-layout">
        <!-- Left: CE Capabilities -->
        <div class="ce-capabilities">
            <section id="core-stats">7-Phase / 97 Checkpoints / 100% Protection</section>
            <section id="capability-matrix">C0-C9 cards</section>
            <section id="features">F001-F012 cards</section>
            <section id="learning-system">
                <h3>Decision History</h3>
                <h3>Memory Cache</h3>
            </section>
        </div>

        <!-- Right: Project Monitoring -->
        <div class="project-monitoring">
            <section id="project-list">All monitored projects</section>
            <section id="active-project">Current progress</section>
            <section id="recent-events">Event timeline</section>
        </div>
    </div>
</body>
</html>
```

---

## 🔧 Section 2: Implementation Tasks

### Phase 2.1: Data Parsing Layer

**Task 2.1.1**: Implement `CapabilityParser`
- [ ] Parse CAPABILITY_MATRIX.md markdown structure
- [ ] Extract C0-C9 capability blocks
- [ ] Handle Chinese/English bilingual content
- [ ] Extract verification logic from code blocks
- [ ] Unit test with actual CAPABILITY_MATRIX.md

**Task 2.1.2**: Implement `LearningSystemParser`
- [ ] Parse DECISIONS.md markdown (date headers, decision blocks)
- [ ] Parse memory-cache.json (handle nested JSON structure)
- [ ] Parse decision-index.json (simple JSON)
- [ ] Handle file-not-found gracefully (some projects may not have all files)
- [ ] Unit test with actual files

**Task 2.1.3**: Implement `FeatureParser`
- [ ] Parse tools/web/dashboard.html (extract feature cards)
- [ ] Handle HTML parsing (BeautifulSoup or regex)
- [ ] Extract: ID, name, description, priority, category, icon
- [ ] Unit test with actual dashboard.html

**Task 2.1.4**: Extend `ProjectMonitor`
- [ ] Support multiple project directories (not just CE itself)
- [ ] Auto-discover projects (scan for .temp/ce_events.jsonl)
- [ ] Read events from multiple projects
- [ ] Aggregate statistics across projects
- [ ] Handle concurrent access (file locks)

### Phase 2.2: API Endpoint Implementation

**Task 2.2.1**: `/api/capabilities` endpoint
```python
GET /api/capabilities
Response:
{
    "core_stats": {
        "phases": 7,
        "checkpoints": 97,
        "quality_gates": 2,
        "branch_protection": "100%"
    },
    "capabilities": [
        {
            "id": "C0",
            "name_zh": "强制新分支",
            "name_en": "Force New Branch",
            "type": "Force",
            "assurance_level": "100%",
            "verification_logic": "...",
            "failure_symptoms": "...",
            "remediation": "..."
        },
        // ... C1-C9
    ],
    "features": [
        {
            "id": "F001",
            "name": "7-Phase Workflow",
            "description": "...",
            "priority": "P0",
            "category": "Core",
            "icon": "workflow"
        },
        // ... F002-F012
    ]
}
```

**Task 2.2.2**: `/api/learning` endpoint
```python
GET /api/learning
Response:
{
    "decisions": [
        {
            "date": "2025-10-13",
            "title": "系统定位明确",
            "decision": "专业级个人工具",
            "rationale": "用户是编程小白，个人使用",
            "importance": "critical",
            "prohibited_operations": ["添加团队协作", "多用户权限"],
            "allowed_operations": []
        },
        // ...
    ],
    "memory_cache": {
        "recent_decisions": {
            "2025-10-13_quality_gate_simplification": {
                "importance": "critical",
                "do_not_revert": true,
                "affected_files": ["scripts/static_checks.sh"]
            }
        }
    },
    "decision_index": {
        "archives": {
            "2025-10": "...",
            "2025-08": "..."
        },
        "total_archives": 1
    },
    "statistics": {
        "total_decisions": 25,
        "critical": 8,
        "warning": 10,
        "info": 7,
        "cache_size_kb": 5.8
    }
}
```

**Task 2.2.3**: `/api/projects` endpoint (renamed from `/api/progress`)
```python
GET /api/projects
Response:
{
    "projects": [
        {
            "name": "Claude Enhancer",
            "path": "/home/xx/dev/Claude Enhancer",
            "branch": "feature/comprehensive-dashboard-v2",
            "current_phase": "Phase1",
            "current_phase_name": "Discovery & Planning",
            "progress_percentage": 14,
            "status": "active",
            "task_name": "Comprehensive Dashboard v2",
            "start_time": "2025-10-23T10:30:00Z",
            "duration_seconds": 1200
        },
        {
            "name": "Other Project",
            "path": "/home/xx/dev/other-project",
            "branch": "main",
            "status": "idle",
            "last_activity": "2025-10-22T15:00:00Z"
        }
    ],
    "active_project": "Claude Enhancer",
    "total_projects": 2
}
```

**Task 2.2.4**: Update `/` endpoint (HTML dashboard)
- [ ] Replace single-column layout with two-column layout
- [ ] Integrate capability display (left column)
- [ ] Integrate project monitoring (right column)
- [ ] Reuse CSS from tools/web/dashboard.html
- [ ] Add feature card rendering
- [ ] Add learning system display

### Phase 2.3: Frontend HTML/CSS

**Task 2.3.1**: Extract and adapt styles from dashboard.html
- [ ] Copy relevant CSS rules
- [ ] Adapt for two-column layout
- [ ] Ensure responsive design (mobile support)
- [ ] Maintain visual consistency

**Task 2.3.2**: Create capability showcase section
- [ ] Core stats display (7-Phase / 97 / 100%)
- [ ] Capability matrix cards (C0-C9)
- [ ] Feature cards (F001-F012)
- [ ] Collapsible details (expand to see verification logic)

**Task 2.3.3**: Create learning system section
- [ ] Decision history list (scrollable)
- [ ] Memory cache display (importance badges)
- [ ] Decision index (archive links)
- [ ] Statistics dashboard (pie chart for importance distribution)

**Task 2.3.4**: Enhance project monitoring section
- [ ] Multi-project list (not just current project)
- [ ] Active project highlight
- [ ] Progress bars for each project
- [ ] Status badges (active/idle/completed)

### Phase 2.4: Multi-Project Support

**Task 2.4.1**: Project auto-discovery
- [ ] Scan configured directories for CE projects
- [ ] Detect `.temp/ce_events.jsonl` presence
- [ ] Read project metadata (name, branch)
- [ ] Cache project list (refresh every 30 seconds)

**Task 2.4.2**: Configuration file
```yaml
# .claude/dashboard_config.yml
monitored_projects:
  - path: /home/xx/dev/Claude Enhancer
    enabled: true
  - path: /home/xx/dev/other-project
    enabled: true
  - path: /root/dev/*
    enabled: true
    scan_subdirectories: true

refresh_interval_seconds: 5
max_projects: 10
```

**Task 2.4.3**: Concurrent event reading
- [ ] Thread-safe event reading from multiple projects
- [ ] File lock handling
- [ ] Graceful degradation if file access fails

---

## ⚡ Section 3: Performance Requirements

### 3.1 Response Time Targets

| Endpoint | Target | Reasoning |
|----------|--------|-----------|
| `/` (HTML) | <2 seconds | User-facing, must be fast |
| `/api/capabilities` | <500ms | Large data but cached |
| `/api/learning` | <300ms | Medium data, file I/O |
| `/api/projects` | <200ms | Real-time updates needed |
| `/api/events` | <100ms | Simple JSONL read |
| `/api/health` | <50ms | Health check, no heavy logic |

### 3.2 Caching Strategy

**Capability Data** (slow-changing):
- Cache duration: 60 seconds
- Invalidation: Manual refresh or file modification detection

**Learning System Data** (medium-changing):
- Cache duration: 30 seconds
- Invalidation: File modification detection

**Project Data** (fast-changing):
- Cache duration: 5 seconds
- Invalidation: New events detected

### 3.3 File Size Limits

- CAPABILITY_MATRIX.md: ~50KB (acceptable, parse once)
- DECISIONS.md: ~10KB (small, parse quickly)
- memory-cache.json: <5KB (target, fast parse)
- dashboard.html: ~100KB (extract once, cache)
- ce_events.jsonl: <10MB (rotation enforced)

### 3.4 Memory Usage

**Target**: <100MB total memory usage

**Breakdown**:
- HTTP server: ~20MB
- Data parsers: ~10MB
- Cached data: ~30MB
- Project events: ~40MB (up to 10 projects × 4MB each)

---

## 🧪 Section 4: Testing Requirements

### 4.1 Unit Tests

**Parser Tests**:
- [ ] `test_capability_parser.py` - Parse CAPABILITY_MATRIX.md
- [ ] `test_learning_parser.py` - Parse DECISIONS.md, memory-cache.json, decision-index.json
- [ ] `test_feature_parser.py` - Parse dashboard.html
- [ ] `test_project_monitor.py` - Read ce_events.jsonl from multiple projects

**API Tests**:
- [ ] `test_api_capabilities.py` - GET /api/capabilities
- [ ] `test_api_learning.py` - GET /api/learning
- [ ] `test_api_projects.py` - GET /api/projects
- [ ] `test_api_health.py` - GET /api/health

### 4.2 Integration Tests

**End-to-End Tests**:
- [ ] Start dashboard server
- [ ] Fetch all API endpoints
- [ ] Verify HTML rendering
- [ ] Verify auto-refresh (meta tag)
- [ ] Test multi-project monitoring
- [ ] Test concurrent access

### 4.3 Performance Tests

**Benchmarks**:
- [ ] Measure API response times (10 requests each)
- [ ] Measure HTML load time
- [ ] Measure memory usage after 1 hour
- [ ] Measure file parsing time (CAPABILITY_MATRIX.md)
- [ ] Measure cache hit rate

**Load Tests**:
- [ ] 10 concurrent requests to /api/capabilities
- [ ] 100 requests/second to /api/projects
- [ ] Auto-refresh with 10 browser tabs

### 4.4 Error Handling Tests

**Missing Files**:
- [ ] CAPABILITY_MATRIX.md not found → Graceful degradation
- [ ] DECISIONS.md not found → Show "No decisions yet"
- [ ] memory-cache.json not found → Show "No cache"
- [ ] ce_events.jsonl not found → Show "No events"

**Corrupt Data**:
- [ ] Invalid JSON in memory-cache.json → Show error message
- [ ] Malformed markdown in DECISIONS.md → Partial parsing
- [ ] Huge JSONL file (>100MB) → Pagination or truncation

---

## 🔒 Section 5: Security & Safety

### 5.1 File Access

**Allowed Paths**:
- `/home/xx/dev/Claude Enhancer/**` (current project)
- `/home/xx/dev/**` (other projects, read-only)
- `/root/dev/**` (alternative project directory)
- `.temp/**` (temporary data)

**Prohibited Paths**:
- System directories (`/etc`, `/usr`, `/bin`)
- User home (`~/.ssh`, `~/.aws`)
- Other sensitive areas

### 5.2 Data Sanitization

**HTML Output**:
- Escape user-generated content (project names, task names)
- Prevent XSS injection
- Use safe HTML rendering

**JSON Output**:
- Validate all JSON before sending
- Handle encoding issues (UTF-8)
- Truncate excessively long strings

### 5.3 Resource Limits

**File Reading**:
- Max file size: 10MB per file
- Max files per request: 20 files
- Timeout: 5 seconds per file read

**Memory**:
- Max cache size: 50MB
- Max event history: 1000 events per project
- Automatic cleanup when limits exceeded

---

## 📦 Section 6: Dependencies

### 6.1 Python Standard Library Only

**Required Modules** (all stdlib):
- `http.server` - HTTP server
- `json` - JSON parsing
- `pathlib` - Path handling
- `datetime` - Timestamp parsing
- `typing` - Type hints
- `re` - Regex for markdown parsing
- `html` - HTML escaping
- `threading` - Concurrent file access
- `functools` - Caching (@lru_cache)

**No External Dependencies**:
- ❌ No Flask, FastAPI, Django
- ❌ No BeautifulSoup (use regex for simple HTML parsing)
- ❌ No markdown libraries (manual parsing)
- ❌ No jq, yq (manual JSON/YAML parsing)

### 6.2 Compatibility

**Python Version**: ≥3.8
**OS**: Linux (primary), macOS (secondary)
**Browser**: Modern browsers with auto-refresh support

---

## 📝 Section 7: Documentation Requirements

### 7.1 User Documentation

**Update DASHBOARD_GUIDE.md**:
- [ ] Add Section 1 explanation (CE能力展示)
- [ ] Add Section 2 explanation (学习系统展示)
- [ ] Update API endpoint documentation
- [ ] Add multi-project monitoring guide
- [ ] Add troubleshooting for new features

### 7.2 Code Documentation

**Docstrings**:
- [ ] All parser classes with examples
- [ ] All API endpoint handlers with request/response formats
- [ ] All helper functions with type hints

**README Updates**:
- [ ] Update feature list (add comprehensive dashboard)
- [ ] Update architecture diagram (two-section layout)
- [ ] Update quick start guide

---

## ✅ Section 8: Acceptance Criteria Mapping

**Cross-reference with ACCEPTANCE_CHECKLIST.md**:

| Acceptance Criteria | Technical Implementation |
|---------------------|--------------------------|
| 显示7-Phase工作流系统 | Core stats API + HTML display |
| 显示97个检查点统计 | Parse CAPABILITY_MATRIX.md |
| 显示C0-C9能力 | CapabilityParser + API |
| 显示F001-F012功能 | FeatureParser + dashboard.html integration |
| 显示决策历史 | Parse DECISIONS.md → /api/learning |
| 显示上下文记忆 | Parse memory-cache.json → /api/learning |
| 多项目监控 | ProjectMonitor + /api/projects |
| 5秒自动刷新 | HTML meta refresh (existing) |
| 响应式布局 | CSS grid two-column layout |

---

## 🎯 Section 9: Success Metrics

**Completion Criteria**:
- [ ] All 27 acceptance criteria passed ✅
- [ ] All API endpoints return correct data ✅
- [ ] Page load time <2 seconds ✅
- [ ] No JavaScript errors in console ✅
- [ ] Multi-project monitoring works ✅
- [ ] Memory usage <100MB after 1 hour ✅
- [ ] All unit tests pass (≥80% coverage) ✅

**Quality Gates**:
- Phase 3: All tests pass, no linting errors
- Phase 4: Code review passed, documentation complete
- Phase 5: Performance benchmarks met, no critical bugs

---

**Generated**: 2025-10-23 Phase 1.3
**Next Phase**: 1.4 Impact Assessment → 1.5 Architecture Planning (with agents)
