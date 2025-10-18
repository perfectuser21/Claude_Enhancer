#!/usr/bin/env bash
# ============================================================================
# Claude Enhancer Workflow Progress Server
# ============================================================================
# 轻量级HTTP服务，提供工作流进度API
# 端口：8999（可配置）
# API：/api/progress - 返回当前工作流进度JSON
# 静态文件：tools/web/dashboard.html
# ============================================================================

set -euo pipefail

# Configuration
readonly PORT="${WORKFLOW_DASHBOARD_PORT:-8999}"
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly DASHBOARD_HTML="${PROJECT_ROOT}/tools/web/dashboard.html"
readonly PROGRESS_GENERATOR="${PROJECT_ROOT}/scripts/generate_progress_data.sh"

# Colors
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

log_info() {
  echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $*"
}

check_dependencies() {
  log_info "Checking dependencies..."

  if ! command -v python3 &>/dev/null; then
    log_error "python3 is required but not installed"
    exit 1
  fi

  if [[ ! -f "${DASHBOARD_HTML}" ]]; then
    log_error "Dashboard HTML not found: ${DASHBOARD_HTML}"
    exit 1
  fi

  if [[ ! -f "${PROGRESS_GENERATOR}" ]]; then
    log_error "Progress generator not found: ${PROGRESS_GENERATOR}"
    exit 1
  fi

  log_success "All dependencies OK"
}

check_port_available() {
  if lsof -Pi :"${PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_error "Port ${PORT} is already in use"
    log_info "Try: export WORKFLOW_DASHBOARD_PORT=9000"
    exit 1
  fi
}

generate_progress_data() {
  log_info "Generating initial progress data..."
  bash "${PROGRESS_GENERATOR}" > /dev/null 2>&1 || {
    log_warning "Failed to generate progress data (will use fallback)"
  }
}

start_server() {
  log_info "Starting HTTP server on port ${PORT}..."

  # Create temporary Python server script with API endpoint
  local server_script
  server_script=$(mktemp)

  cat > "${server_script}" <<'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import sys
from urllib.parse import urlparse, parse_qs
from pathlib import Path

PORT = int(os.environ.get('PORT', 8999))
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DASHBOARD_HTML = PROJECT_ROOT / 'tools' / 'web' / 'dashboard.html'
PROGRESS_JSON = PROJECT_ROOT / '.temp' / 'workflow_progress.json'
FEATURE_MAPPING_JSON = PROJECT_ROOT / 'tools' / 'web' / 'feature_mapping.json'

class ProgressHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        # API endpoint: /api/progress
        if parsed_path.path == '/api/progress':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            try:
                # Generate fresh progress data
                os.system(f'bash {PROJECT_ROOT}/scripts/generate_progress_data.sh > /dev/null 2>&1')

                if PROGRESS_JSON.exists():
                    with open(PROGRESS_JSON, 'r') as f:
                        data = f.read()
                    self.wfile.write(data.encode())
                else:
                    # Fallback data
                    fallback = {
                        "timestamp": "2025-10-17T00:00:00Z",
                        "current_phase": "P0",
                        "overall_progress": 0,
                        "phases": [],
                        "impact_assessment": {"score": 0, "level": "unknown"},
                        "agents_active": 0,
                        "agents_total": 0
                    }
                    self.wfile.write(json.dumps(fallback).encode())
            except Exception as e:
                print(f"Error serving progress: {e}", file=sys.stderr)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # API endpoint: /api/feature_mapping
        if parsed_path.path == '/api/feature_mapping':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            try:
                if FEATURE_MAPPING_JSON.exists():
                    with open(FEATURE_MAPPING_JSON, 'r') as f:
                        data = f.read()
                    self.wfile.write(data.encode())
                else:
                    # Fallback error
                    fallback = {
                        "error": "Feature mapping not found",
                        "metadata": {"version": "1.0.0", "total_features": 0}
                    }
                    self.wfile.write(json.dumps(fallback).encode())
            except Exception as e:
                print(f"Error serving feature mapping: {e}", file=sys.stderr)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # Dashboard HTML: /
        if parsed_path.path == '/' or parsed_path.path == '/dashboard':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            try:
                with open(DASHBOARD_HTML, 'rb') as f:
                    self.wfile.write(f.read())
            except Exception as e:
                self.send_error(404, f"Dashboard not found: {e}")
            return

        # Default: 404
        self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        # Custom log format with colors
        sys.stderr.write("[%s] %s\n" % (
            self.log_date_time_string(),
            format % args
        ))

def run_server():
    with socketserver.TCPServer(("", PORT), ProgressHandler) as httpd:
        print(f"\n{'='*70}")
        print(f"🚀 Claude Enhancer Dashboard Server")
        print(f"{'='*70}")
        print(f"  Dashboard:        http://localhost:{PORT}")
        print(f"  API Progress:     http://localhost:{PORT}/api/progress")
        print(f"  API Features:     http://localhost:{PORT}/api/feature_mapping")
        print(f"{'='*70}")
        print(f"  Press Ctrl+C to stop\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped")
            sys.exit(0)

if __name__ == '__main__':
    run_server()
EOF

  # Make executable and run
  chmod +x "${server_script}"
  PORT="${PORT}" python3 "${server_script}"
}

cleanup() {
  log_info "Cleaning up..."
  # Kill any background processes
  jobs -p | xargs -r kill 2>/dev/null || true
}

# ============================================================================
# Main
# ============================================================================

main() {
  trap cleanup EXIT INT TERM

  log_info "Claude Enhancer Workflow Progress Server"
  log_info "Project root: ${PROJECT_ROOT}"

  check_dependencies
  check_port_available
  generate_progress_data

  log_success "Starting server..."
  start_server
}

main "$@"
