# CE Dashboard User Guide

**Version**: 7.1.2
**Purpose**: Real-time monitoring of Claude Enhancer workflow progress
**Dependencies**: None (Python standard library only)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Dashboard Features](#dashboard-features)
5. [API Endpoints](#api-endpoints)
6. [Remote Access (SSH Tunnel)](#remote-access-ssh-tunnel)
7. [Troubleshooting](#troubleshooting)
8. [Technical Details](#technical-details)

---

## 🎯 Overview

The CE Dashboard provides **real-time visibility** into your Claude Enhancer workflow progress. It's designed for the common use case where you run CE workflow in **Terminal 1** and monitor progress in **Terminal 2** via a web browser.

### Key Features

- ✅ **Real-time progress tracking** (Phase 1-7)
- ✅ **Auto-refresh every 5 seconds** (no manual refresh needed)
- ✅ **Current task and phase display**
- ✅ **Recent events timeline**
- ✅ **Statistics dashboard** (total tasks, errors, average duration)
- ✅ **Zero external dependencies** (standard library only)
- ✅ **SSH tunnel support** (remote access)

### Architecture

```
Terminal 1 (CE Workflow)          Terminal 2 (Dashboard)
┌─────────────────────┐           ┌──────────────────────┐
│ Claude Code         │           │ Browser              │
│   ↓                 │           │ http://localhost:8888│
│ Phase 1 → Phase 2   │           │   ↑                  │
│   ↓                 │           │   │ Auto-refresh 5s  │
│ Telemetry Hook      │           │   │                  │
│   ↓                 │           └───┼──────────────────┘
│ .temp/              │               │
│  ce_events.jsonl    │───────────────┘
└─────────────────────┘           Python http.server
                                  (tools/dashboard.py)
```

---

## 🚀 Installation

The dashboard is **automatically installed** with Claude Enhancer v7.1.2+. No additional setup required!

### Verify Installation

```bash
# Check telemetry hook exists
ls -l .claude/hooks/telemetry_logger.sh

# Check dashboard exists
ls -l tools/dashboard.py

# Check settings.json includes telemetry hook
grep "telemetry_logger.sh" .claude/settings.json
```

Expected output:
```bash
-rwxr-xr-x 1 user group 4567 Oct 22 10:30 .claude/hooks/telemetry_logger.sh
-rwxr-xr-x 1 user group 23456 Oct 22 10:30 tools/dashboard.py
      ".claude/hooks/telemetry_logger.sh"
```

---

## ⚡ Quick Start

### Method 1: Foreground (Simple)

**Terminal 2**:
```bash
cd /home/xx/dev/Claude\ Enhancer
python3 tools/dashboard.py
```

Expected output:
```
CE Dashboard v7.1.2
Project Root: /home/xx/dev/Claude Enhancer
Events File: /home/xx/dev/Claude Enhancer/.temp/ce_events.jsonl
Starting server on http://localhost:8888
Press Ctrl+C to stop
------------------------------------------------------------
```

**Browser**: Open `http://localhost:8888`

**Terminal 1**: Start your CE workflow as usual. Dashboard will auto-update!

**Stop**: Press `Ctrl+C` in Terminal 2

### Method 2: Background (Daemon)

```bash
# Start in background
nohup python3 tools/dashboard.py > /tmp/ce_dashboard.log 2>&1 &

# Check it's running
ps aux | grep dashboard.py

# Open browser
open http://localhost:8888  # macOS
xdg-open http://localhost:8888  # Linux

# Stop later
pkill -f dashboard.py
```

### Method 3: tmux/screen (Recommended)

```bash
# Create new tmux session
tmux new-session -s ce-dashboard

# Inside tmux session
cd /home/xx/dev/Claude\ Enhancer
python3 tools/dashboard.py

# Detach from tmux: Ctrl+B, then D
# Reattach later: tmux attach -t ce-dashboard
```

---

## 📊 Dashboard Features

### 1. Current Task Progress Card

Shows:
- **Status Badge**: `ACTIVE` (green) / `COMPLETED` (blue) / `IDLE` (gray)
- **Task Name**: Current task being worked on
- **Progress Bar**: Visual 0-100% progress
- **Current Phase**: Phase1-Phase7 with name
- **Duration**: How long the task has been running
- **Start Time**: When the task started (UTC)

**Example**:
```
Status: ACTIVE
Task: Dashboard Implementation
Progress: 29% | Phase2 | Implementation
Duration: 15m 30s
Start Time: 2025-10-22 10:30:00 UTC
```

### 2. Statistics Card

Shows:
- **Total Tasks**: Number of tasks started
- **Phases Done**: Number of phases completed across all tasks
- **Avg Duration**: Average task completion time
- **Errors**: Total error events logged

**Example**:
```
Total Tasks: 12
Phases Done: 47
Avg Duration: 1h 23m
Errors: 2
```

### 3. Recent Events List

Shows last 20 events in reverse chronological order (most recent first):
- **Event Type**: `TASK_START`, `PHASE_START`, `PHASE_END`, `ERROR`
- **Timestamp**: When the event occurred (UTC)
- **Details**: Task name and phase information

**Example**:
```
PHASE_START  2025-10-22 10:45:00 UTC
Task: Dashboard Implementation | Phase: Phase2

TASK_START  2025-10-22 10:30:00 UTC
Task: Dashboard Implementation
```

### 4. Auto-Refresh

The dashboard automatically refreshes every **5 seconds** using HTML meta refresh. No JavaScript, no WebSocket, just simple and reliable.

---

## 🔌 API Endpoints

The dashboard provides JSON APIs for programmatic access:

### `GET /`
**Description**: HTML dashboard (default)
**Response**: HTML page with auto-refresh

### `GET /api/progress`
**Description**: Current task progress
**Response**:
```json
{
  "status": "active",
  "task_name": "Dashboard Implementation",
  "current_phase": "Phase2",
  "current_phase_name": "Implementation",
  "progress_percentage": 29,
  "start_time": "2025-10-22T10:30:00Z",
  "duration_seconds": 930,
  "recent_event": { ... }
}
```

### `GET /api/events`
**Description**: Recent events (last 100)
**Response**:
```json
[
  {
    "timestamp": "2025-10-22T10:45:00Z",
    "event_type": "phase_start",
    "project_name": "Claude Enhancer",
    "task_name": "Dashboard Implementation",
    "phase_id": "Phase2",
    "phase_name": "Implementation",
    "metadata": {}
  },
  ...
]
```

### `GET /api/stats`
**Description**: Statistics summary
**Response**:
```json
{
  "total_tasks": 12,
  "total_errors": 2,
  "average_duration": 4980,
  "phases_completed": 47
}
```

### `GET /api/health`
**Description**: Health check
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-22T10:50:00Z",
  "events_file_exists": true,
  "version": "7.1.2"
}
```

### Usage Examples

```bash
# Get current progress
curl http://localhost:8888/api/progress | jq

# Get recent events
curl http://localhost:8888/api/events | jq '.[0:5]'

# Health check
curl http://localhost:8888/api/health
```

---

## 🌐 Remote Access (SSH Tunnel)

If CE is running on a **remote server**, you can access the dashboard on your laptop via SSH tunnel.

### Setup SSH Tunnel

**On your laptop**:
```bash
ssh -L 8888:localhost:8888 user@remote-server.com
```

**Explanation**:
- `-L 8888:localhost:8888`: Forward local port 8888 to remote localhost:8888
- Dashboard runs on remote server's `localhost:8888`
- You access it on your laptop's `http://localhost:8888`

**Open browser** on your laptop:
```
http://localhost:8888
```

You'll see the dashboard as if CE was running locally! 🎉

### Keep Tunnel Alive

**Option 1: SSH config** (`~/.ssh/config`):
```
Host ce-server
  HostName remote-server.com
  User your-username
  LocalForward 8888 localhost:8888
  ServerAliveInterval 60
  ServerAliveCountMax 3
```

Then connect: `ssh ce-server`

**Option 2: autossh** (auto-reconnect):
```bash
autossh -M 0 -L 8888:localhost:8888 user@remote-server.com
```

---

## 🔧 Troubleshooting

### Issue 1: "Port 8888 already in use"

**Symptoms**:
```
ERROR: Could not start server on port 8888
OSError: [Errno 48] Address already in use
```

**Solution**:
```bash
# Find what's using port 8888
lsof -i :8888
# or
netstat -tuln | grep 8888

# Kill the process (example PID: 12345)
kill 12345

# Or use a different port
# Edit tools/dashboard.py, change: PORT = 8888
```

### Issue 2: Dashboard shows "No active tasks"

**Symptoms**: Dashboard loads but shows "No active tasks" even when CE is running.

**Possible Causes**:
1. **Telemetry hook not triggered yet**: Wait 5-10 seconds for first tool use.
2. **Events file doesn't exist**: Check `.temp/ce_events.jsonl` exists.
3. **Wrong project directory**: Make sure dashboard.py runs from CE root directory.

**Solution**:
```bash
# Check events file
ls -lh .temp/ce_events.jsonl

# Check file content
tail -5 .temp/ce_events.jsonl

# Check telemetry hook is in settings.json
grep "telemetry_logger" .claude/settings.json
```

### Issue 3: Events not updating in real-time

**Symptoms**: Dashboard loads but events stop updating.

**Possible Causes**:
1. **File rotation in progress**: Wait 5 seconds.
2. **File permission issue**: Check `.temp/` is writable.
3. **Hook error**: Check telemetry hook is executable.

**Solution**:
```bash
# Check hook permissions
ls -l .claude/hooks/telemetry_logger.sh
# Should show: -rwxr-xr-x (executable)

# Make executable if needed
chmod +x .claude/hooks/telemetry_logger.sh

# Check .temp/ is writable
ls -ld .temp/
# Should show: drwxr-xr-x

# Test telemetry hook manually
TOOL_NAME="Test" TASK_NAME="Manual Test" bash .claude/hooks/telemetry_logger.sh
tail -1 .temp/ce_events.jsonl
```

### Issue 4: Dashboard is slow

**Symptoms**: Dashboard takes >2 seconds to load.

**Possible Causes**:
1. **JSONL file is huge** (>50MB): File rotation failed.
2. **Too many events**: Limit not enforced.

**Solution**:
```bash
# Check file size
ls -lh .temp/ce_events.jsonl

# If >10MB, manually rotate
cd .temp
gzip -c ce_events.jsonl > ce_events_$(date +%Y%m%d_%H%M%S).jsonl.gz
> ce_events.jsonl  # Truncate file

# Adjust MAX_RECENT_EVENTS in dashboard.py if needed
# Default: 100 events
```

### Issue 5: SSH tunnel disconnects

**Symptoms**: SSH tunnel drops after 5 minutes of inactivity.

**Solution**: Add to `~/.ssh/config`:
```
Host *
  ServerAliveInterval 60
  ServerAliveCountMax 3
```

Or use `autossh`:
```bash
autossh -M 0 -L 8888:localhost:8888 user@remote-server.com
```

---

## 🔬 Technical Details

### Event Schema (JSONL)

Each line in `.temp/ce_events.jsonl` is a JSON event:

```json
{
  "timestamp": "2025-10-22T10:30:00Z",
  "event_type": "task_start|task_end|phase_start|phase_end|error",
  "project_name": "Claude Enhancer",
  "task_name": "Dashboard Implementation",
  "phase_id": "Phase1|Phase2|...|Phase7|null",
  "phase_name": "Discovery & Planning|Implementation|...|null",
  "metadata": {
    "key": "value"
  }
}
```

**Event Types**:
- `task_start`: New task begins (Phase 1.1)
- `phase_start`: New phase begins (Phase 1 → Phase 2)
- `phase_end`: Phase completes
- `task_end`: Task completes (Phase 7 done)
- `error`: Error occurred during workflow

### Phase Progress Mapping

| Phase   | Name                  | Progress % |
|---------|-----------------------|------------|
| Phase1  | Discovery & Planning  | 14%        |
| Phase2  | Implementation        | 29%        |
| Phase3  | Testing               | 43%        |
| Phase4  | Review                | 57%        |
| Phase5  | Release               | 71%        |
| Phase6  | Acceptance            | 86%        |
| Phase7  | Closure               | 100%       |

**Calculation**: `Progress = (Phase Number / 7) * 100`

### File Rotation

**Trigger**: When `ce_events.jsonl` exceeds **10MB**

**Process**:
1. Acquire file lock (`.temp/ce_events.jsonl.lock`)
2. Compress current file: `gzip -c ce_events.jsonl > ce_events_20251022_103000.jsonl.gz`
3. Truncate current file: `> ce_events.jsonl`
4. Release lock

**Retention**: Rotated files are kept for **7 days** (manual cleanup).

### Performance Targets

| Metric                 | Target    | How to Measure                     |
|------------------------|-----------|------------------------------------|
| Event Logging Overhead | <100ms    | `time bash telemetry_logger.sh`    |
| Dashboard Load Time    | <1 second | Browser DevTools Network tab       |
| JSONL Read (1000 lines)| <50ms     | Python `timeit` module             |
| File Rotation          | <200ms    | Test with 10MB file                |
| Memory Usage           | <50MB     | `ps aux | grep dashboard.py`       |

### Security Considerations

- ✅ **Localhost only**: Dashboard binds to `localhost`, not accessible from network
- ✅ **No authentication**: Trusted environment (single user)
- ✅ **No sensitive data**: Events contain task names and phase IDs only
- ✅ **No XSS risk**: No user input, server-side rendering only
- ✅ **No SQL injection**: JSONL files, no database
- ✅ **File permissions**: JSONL files are `0644`, scripts are `0755`

---

## 🎓 Examples

### Example 1: Monitor a Simple Task

**Terminal 1**:
```bash
cd /home/xx/dev/Claude\ Enhancer
# Ask Claude Code to implement a new feature
# "Implement user authentication system"
```

**Terminal 2**:
```bash
python3 tools/dashboard.py
```

**Browser**: `http://localhost:8888`

**Expected Dashboard**:
```
Status: ACTIVE
Task: User Authentication Implementation
Progress: 14% | Phase1 | Discovery & Planning
Duration: 2m 15s
Start Time: 2025-10-22 10:30:00 UTC

Recent Events:
TASK_START  2025-10-22 10:30:00 UTC
Task: User Authentication Implementation

PHASE_START  2025-10-22 10:30:05 UTC
Task: User Authentication Implementation | Phase: Phase1
```

### Example 2: Track Multiple Tasks (Parallel Terminals)

**Terminal 1**:
```bash
# Task A: Feature development
git checkout -b feature/user-auth
# Work on user auth...
```

**Terminal 2**:
```bash
# Dashboard
python3 tools/dashboard.py
```

**Terminal 3**:
```bash
# Task B: Bug fix (different CE instance)
cd /home/xx/dev/another-project
git checkout -b bugfix/login-error
# Work on bug fix...
```

**Dashboard** will show the **latest task** started across all terminals!

### Example 3: Remote Monitoring via SSH Tunnel

**Laptop**:
```bash
# Create SSH tunnel
ssh -L 8888:localhost:8888 user@ce-server.example.com

# Keep terminal open, open browser
open http://localhost:8888
```

**Server** (ce-server.example.com):
```bash
# Dashboard already running (from earlier)
tmux attach -t ce-dashboard
```

**Laptop browser** shows live CE workflow progress from remote server! 🚀

---

## 📝 Changelog

### v7.1.2 (2025-10-22)
- ✨ Initial release
- ✅ Real-time dashboard with auto-refresh
- ✅ Telemetry hook integration
- ✅ 5 API endpoints
- ✅ SSH tunnel support
- ✅ Zero external dependencies

---

## 🤝 Support

**Issues**: Report at [GitHub Issues](https://github.com/anthropics/claude-code/issues)
**Documentation**: See `CLAUDE.md` and `ARCHITECTURE.md`
**Version**: 7.1.2

---

**Made with ❤️ by Claude Enhancer Team**
