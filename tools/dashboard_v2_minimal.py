#!/usr/bin/env python3
"""
CE Dashboard v2 - Comprehensive Monitoring (Minimal Implementation)

Quick implementation for testing. Full version will be completed in next session.
Version: 7.2.0-minimal
"""

import json
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers import CapabilityParser, LearningSystemParser, FeatureParser, ProjectMonitor
from cache import capability_cache, learning_cache, project_cache

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
PORT = 8888

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/api/capabilities':
            self.serve_capabilities()
        elif path == '/api/learning':
            self.serve_learning()
        elif path == '/api/projects':
            self.serve_projects()
        elif path == '/api/health':
            self.serve_health()
        elif path == '/':
            self.serve_html()
        else:
            self.send_error(404)
    
    def serve_capabilities(self):
        """GET /api/capabilities"""
        def compute():
            cap_parser = CapabilityParser(PROJECT_ROOT / "docs" / "CAPABILITY_MATRIX.md")
            cap_result = cap_parser.parse()
            
            feat_parser = FeatureParser(PROJECT_ROOT / "tools" / "web" / "dashboard.html")
            feat_result = feat_parser.parse()
            
            return {
                'core_stats': cap_result.data['core_stats'].__dict__ if cap_result.success else {},
                'capabilities': [c.__dict__ for c in cap_result.data.get('capabilities', [])],
                'features': [f.__dict__ for f in feat_result.data] if feat_result.success else []
            }
        
        data = capability_cache.get_or_compute('cap_all', compute)
        self.send_json(data)
    
    def serve_learning(self):
        """GET /api/learning"""
        def compute():
            parser = LearningSystemParser(PROJECT_ROOT)
            dec_result = parser.parse_decisions()
            mem_result = parser.parse_memory_cache()
            
            decisions = dec_result.data if dec_result.success else []
            memory = mem_result.data if mem_result.success else None
            
            return {
                'decisions': [d.__dict__ for d in decisions[-10:]],  # Last 10
                'statistics': {
                    'total_decisions': len(decisions),
                    'memory_cache_size': memory.cache_size_bytes if memory else 0
                }
            }
        
        data = learning_cache.get_or_compute('learning_all', compute)
        self.send_json(data)
    
    def serve_projects(self):
        """GET /api/projects"""
        def compute():
            monitor = ProjectMonitor(PROJECT_ROOT)
            status_result = monitor.get_project_status()
            
            project = status_result.data if status_result.success else None
            
            return {
                'projects': [project.__dict__] if project else [],
                'summary': {'total_projects': 1 if project else 0}
            }
        
        data = project_cache.get_or_compute('projects_all', compute)
        self.send_json(data)
    
    def serve_health(self):
        """GET /api/health"""
        self.send_json({'status': 'healthy', 'version': '7.2.0-minimal'})
    
    def serve_html(self):
        """Serve comprehensive HTML dashboard"""
        html_file = PROJECT_ROOT / "tools" / "dashboard_v2.html"
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html = f.read()
            self.send_html(html)
        except FileNotFoundError:
            # Fallback to minimal HTML
            html = """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>CE Dashboard v2 - Error</title></head>
<body><h1>Error: dashboard_v2.html not found</h1></body></html>"""
            self.send_html(html)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == '__main__':
    print(f"CE Dashboard v2 (minimal)")
    print(f"Starting server on http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    server = HTTPServer(('localhost', PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
