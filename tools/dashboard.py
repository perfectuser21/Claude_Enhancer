#!/usr/bin/env python3
"""
CE Dashboard - Real-time Workflow Monitoring

Purpose: Simple HTTP dashboard for monitoring Claude Enhancer workflow progress
Version: 7.1.2
Port: 8888
Dependencies: None (standard library only)
"""

import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, parse_qs

# ==============================================================================
# Configuration
# ==============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
EVENTS_FILE = PROJECT_ROOT / ".temp" / "ce_events.jsonl"
PORT = 8888  # Using 8888 to avoid port conflicts
MAX_RECENT_EVENTS = 100

# Phase progress mapping (Phase1-7 → percentage)
PHASE_PROGRESS = {
    "Phase1": 14,  # 1/7 * 100
    "Phase2": 29,  # 2/7 * 100
    "Phase3": 43,  # 3/7 * 100
    "Phase4": 57,  # 4/7 * 100
    "Phase5": 71,  # 5/7 * 100
    "Phase6": 86,  # 6/7 * 100
    "Phase7": 100  # 7/7 * 100
}

PHASE_NAMES = {
    "Phase1": "Discovery & Planning",
    "Phase2": "Implementation",
    "Phase3": "Testing",
    "Phase4": "Review",
    "Phase5": "Release",
    "Phase6": "Acceptance",
    "Phase7": "Closure"
}

# ==============================================================================
# Data Access Layer
# ==============================================================================

def read_events(limit: int = MAX_RECENT_EVENTS) -> List[Dict[str, Any]]:
    """Read recent events from JSONL file"""
    if not EVENTS_FILE.exists():
        return []

    events = []
    try:
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            # Read last N lines efficiently
            lines = f.readlines()
            for line in lines[-limit:]:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except json.JSONDecodeError:
                        # Skip corrupted lines
                        continue
    except (IOError, OSError):
        # File not accessible, return empty
        pass

    return events


def get_current_progress() -> Dict[str, Any]:
    """Calculate current workflow progress from events"""
    events = read_events(limit=MAX_RECENT_EVENTS)

    if not events:
        return {
            "status": "idle",
            "task_name": "No active tasks",
            "current_phase": None,
            "current_phase_name": None,
            "progress_percentage": 0,
            "start_time": None,
            "duration_seconds": 0,
            "recent_event": None
        }

    # Find latest task_start event
    latest_task_start = None
    for event in reversed(events):
        if event.get("event_type") == "task_start":
            latest_task_start = event
            break

    # Check if task has ended
    task_ended = False
    for event in reversed(events):
        if event.get("event_type") == "task_end":
            task_ended = True
            break

    if task_ended and latest_task_start:
        # Task completed
        return {
            "status": "completed",
            "task_name": latest_task_start.get("task_name", "Unknown Task"),
            "current_phase": "Phase7",
            "current_phase_name": "Closure",
            "progress_percentage": 100,
            "start_time": latest_task_start.get("timestamp"),
            "duration_seconds": calculate_duration(latest_task_start, events[-1]),
            "recent_event": events[-1]
        }

    if not latest_task_start:
        return {
            "status": "idle",
            "task_name": "No active tasks",
            "current_phase": None,
            "current_phase_name": None,
            "progress_percentage": 0,
            "start_time": None,
            "duration_seconds": 0,
            "recent_event": events[-1] if events else None
        }

    # Find latest phase_start event after task_start
    latest_phase = None
    for event in reversed(events):
        if event.get("event_type") == "phase_start":
            if event.get("timestamp", "") >= latest_task_start.get("timestamp", ""):
                latest_phase = event
                break

    current_phase = latest_phase.get("phase_id") if latest_phase else "Phase1"
    current_phase_name = latest_phase.get("phase_name") if latest_phase else PHASE_NAMES.get(current_phase, "Unknown")
    progress = PHASE_PROGRESS.get(current_phase, 0)

    return {
        "status": "active",
        "task_name": latest_task_start.get("task_name", "Unknown Task"),
        "current_phase": current_phase,
        "current_phase_name": current_phase_name,
        "progress_percentage": progress,
        "start_time": latest_task_start.get("timestamp"),
        "duration_seconds": calculate_duration(latest_task_start, events[-1]),
        "recent_event": events[-1]
    }


def calculate_duration(start_event: Dict[str, Any], end_event: Dict[str, Any]) -> int:
    """Calculate duration between two events in seconds"""
    try:
        start_time = datetime.fromisoformat(start_event.get("timestamp", "").replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end_event.get("timestamp", "").replace("Z", "+00:00"))
        return int((end_time - start_time).total_seconds())
    except (ValueError, AttributeError):
        return 0


def get_statistics() -> Dict[str, Any]:
    """Calculate basic statistics from events"""
    events = read_events(limit=1000)  # Analyze last 1000 events

    if not events:
        return {
            "total_tasks": 0,
            "total_errors": 0,
            "average_duration": 0,
            "phases_completed": 0
        }

    task_starts = [e for e in events if e.get("event_type") == "task_start"]
    task_ends = [e for e in events if e.get("event_type") == "task_end"]
    errors = [e for e in events if e.get("event_type") == "error"]
    phase_ends = [e for e in events if e.get("event_type") == "phase_end"]

    # Calculate average task duration
    durations = []
    for end in task_ends:
        # Find corresponding start
        end_task_name = end.get("task_name")
        for start in reversed(task_starts):
            if start.get("task_name") == end_task_name:
                duration = calculate_duration(start, end)
                durations.append(duration)
                break

    avg_duration = sum(durations) // len(durations) if durations else 0

    return {
        "total_tasks": len(task_starts),
        "total_errors": len(errors),
        "average_duration": avg_duration,
        "phases_completed": len(phase_ends)
    }


# ==============================================================================
# HTML Dashboard Template
# ==============================================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="5">
    <title>CE Dashboard - Claude Enhancer Workflow Monitor</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .card h2 {{
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #667eea;
            display: flex;
            align-items: center;
        }}

        .card h2::before {{
            content: '';
            width: 4px;
            height: 1.5em;
            background: #667eea;
            margin-right: 10px;
            border-radius: 2px;
        }}

        .status-badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .status-active {{
            background: #10b981;
            color: white;
        }}

        .status-completed {{
            background: #3b82f6;
            color: white;
        }}

        .status-idle {{
            background: #6b7280;
            color: white;
        }}

        .progress-container {{
            margin: 20px 0;
        }}

        .progress-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }}

        .progress-bar-wrapper {{
            width: 100%;
            height: 30px;
            background: #e5e7eb;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }}

        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 0.9em;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .info-item {{
            padding: 15px;
            background: #f9fafb;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}

        .info-label {{
            font-size: 0.85em;
            color: #6b7280;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .info-value {{
            font-size: 1.3em;
            font-weight: 700;
            color: #111827;
        }}

        .events-list {{
            max-height: 400px;
            overflow-y: auto;
        }}

        .event-item {{
            padding: 12px;
            margin-bottom: 8px;
            background: #f9fafb;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            font-size: 0.9em;
        }}

        .event-type {{
            font-weight: 700;
            color: #667eea;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}

        .event-time {{
            color: #6b7280;
            font-size: 0.85em;
        }}

        .event-details {{
            margin-top: 5px;
            color: #374151;
        }}

        .refresh-notice {{
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
            opacity: 0.8;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}

        .stat-card {{
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }}

        .stat-value {{
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 CE Dashboard</h1>
            <p class="subtitle">Claude Enhancer Workflow Monitor v7.1.2</p>
        </header>

        <div class="card">
            <h2>Current Task Progress</h2>
            <div style="margin-bottom: 15px;">
                <span class="status-badge status-{status}">{status_display}</span>
            </div>

            <div style="margin: 15px 0;">
                <strong style="font-size: 1.2em;">Task:</strong>
                <span style="font-size: 1.2em;">{task_name}</span>
            </div>

            <div class="progress-container">
                <div class="progress-label">
                    <span>{current_phase_name}</span>
                    <span>{progress_percentage}%</span>
                </div>
                <div class="progress-bar-wrapper">
                    <div class="progress-bar" style="width: {progress_percentage}%;">
                        {current_phase}
                    </div>
                </div>
            </div>

            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Current Phase</div>
                    <div class="info-value">{current_phase}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Duration</div>
                    <div class="info-value">{duration_display}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Start Time</div>
                    <div class="info-value">{start_time_display}</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_tasks}</div>
                    <div class="stat-label">Total Tasks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{phases_completed}</div>
                    <div class="stat-label">Phases Done</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_duration_display}</div>
                    <div class="stat-label">Avg Duration</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_errors}</div>
                    <div class="stat-label">Errors</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Recent Events</h2>
            <div class="events-list">
                {events_html}
            </div>
        </div>

        <p class="refresh-notice">
            ⟳ Auto-refreshing every 5 seconds | Port: {port} |
            <a href="/api/progress" style="color: white; text-decoration: underline;">API</a>
        </p>
    </div>
</body>
</html>
"""


def format_duration(seconds: int) -> str:
    """Format duration in human-readable form"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def format_timestamp(iso_timestamp: Optional[str]) -> str:
    """Format ISO timestamp to human-readable form"""
    if not iso_timestamp:
        return "N/A"

    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, AttributeError):
        return "N/A"


def generate_html_dashboard() -> str:
    """Generate complete HTML dashboard"""
    progress = get_current_progress()
    stats = get_statistics()
    events = read_events(limit=20)

    # Format events HTML
    events_html = ""
    if not events:
        events_html = '<p style="text-align: center; color: #6b7280; padding: 20px;">No events recorded yet</p>'
    else:
        for event in reversed(events):  # Most recent first
            event_type = event.get("event_type", "unknown")
            timestamp = event.get("timestamp", "")
            task_name = event.get("task_name", "")
            phase_id = event.get("phase_id") or ""

            details = f"Task: {task_name}"
            if phase_id:
                details += f" | Phase: {phase_id}"

            events_html += f"""
            <div class="event-item">
                <div>
                    <span class="event-type">{event_type}</span>
                    <span class="event-time">{format_timestamp(timestamp)}</span>
                </div>
                <div class="event-details">{details}</div>
            </div>
            """

    # Populate template
    html = HTML_TEMPLATE.format(
        status=progress["status"],
        status_display=progress["status"].upper(),
        task_name=progress["task_name"],
        current_phase=progress["current_phase"] or "N/A",
        current_phase_name=progress["current_phase_name"] or "N/A",
        progress_percentage=progress["progress_percentage"],
        duration_display=format_duration(progress["duration_seconds"]),
        start_time_display=format_timestamp(progress["start_time"]),
        total_tasks=stats["total_tasks"],
        total_errors=stats["total_errors"],
        phases_completed=stats["phases_completed"],
        avg_duration_display=format_duration(stats["average_duration"]),
        events_html=events_html,
        port=PORT
    )

    return html


# ==============================================================================
# HTTP Request Handler
# ==============================================================================

class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for CE Dashboard"""

    def log_message(self, format, *args):
        """Override to customize logging"""
        # Log to stdout with timestamp
        sys.stderr.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}\n")

    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        try:
            if path == "/":
                # Serve HTML dashboard
                html = generate_html_dashboard()
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))

            elif path == "/api/progress":
                # JSON API: current progress
                progress = get_current_progress()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(json.dumps(progress, indent=2).encode('utf-8'))

            elif path == "/api/events":
                # JSON API: recent events
                events = read_events(limit=MAX_RECENT_EVENTS)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(json.dumps(events, indent=2).encode('utf-8'))

            elif path == "/api/stats":
                # JSON API: statistics
                stats = get_statistics()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(json.dumps(stats, indent=2).encode('utf-8'))

            elif path == "/api/health":
                # Health check endpoint
                health = {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "events_file_exists": EVENTS_FILE.exists(),
                    "version": "7.1.2"
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(health, indent=2).encode('utf-8'))

            else:
                # 404 Not Found
                self.send_response(404)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"404 Not Found")

        except Exception as e:
            # 500 Internal Server Error
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            error_msg = f"Internal Server Error: {str(e)}"
            self.wfile.write(error_msg.encode('utf-8'))
            print(f"ERROR: {error_msg}", file=sys.stderr)


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Start the dashboard HTTP server"""
    print(f"CE Dashboard v7.1.2")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Events File: {EVENTS_FILE}")
    print(f"Starting server on http://localhost:{PORT}")
    print(f"Press Ctrl+C to stop")
    print("-" * 60)

    # Ensure .temp directory exists
    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        server = HTTPServer(("localhost", PORT), DashboardHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.shutdown()
        print("Server stopped. Goodbye!")
    except OSError as e:
        print(f"\nERROR: Could not start server on port {PORT}")
        print(f"Reason: {e}")
        print(f"\nPossible solutions:")
        print(f"1. Check if port {PORT} is already in use: lsof -i :{PORT}")
        print(f"2. Kill the process using that port")
        print(f"3. Change PORT in dashboard.py to another port (e.g., 8081)")
        sys.exit(1)


if __name__ == "__main__":
    main()
