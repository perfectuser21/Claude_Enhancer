#!/usr/bin/env python3
"""
CE Dashboard v2 - Multi-Page Full Version
完整多页面Dashboard：主页 + CE能力详情 + 项目状态
"""

import json
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers import CapabilityParser, LearningSystemParser, FeatureParser, ProjectMonitor
from cache import capability_cache, learning_cache, project_cache

PROJECT_ROOT = Path(__file__).parent.parent
PORT = 7777

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path

        # API endpoints
        if path == '/api/health':
            self.serve_health()
        elif path == '/api/capabilities':
            self.serve_capabilities()
        elif path == '/api/learning':
            self.serve_learning()
        elif path == '/api/projects':
            self.serve_projects()

        # Pages
        elif path == '/' or path == '/index':
            self.serve_home()
        elif path == '/capabilities':
            self.serve_capabilities_page()
        elif path == '/projects':
            self.serve_projects_page()
        else:
            self.send_error(404)

    def serve_home(self):
        """主页：总览 + 导航"""
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CE Dashboard v2 - 主页</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            margin-bottom: 30px;
        }
        h1 { color: #667eea; font-size: 2.5em; margin-bottom: 10px; }
        .version { color: #666; font-size: 0.9em; }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        }
        .card h2 { color: #667eea; margin-bottom: 15px; font-size: 1.5em; }
        .stat { font-size: 2.5em; font-weight: bold; color: #764ba2; margin: 15px 0; }
        .label { color: #666; font-size: 0.9em; }
        .nav-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        .nav-button {
            display: block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-decoration: none;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
            transition: transform 0.3s, box-shadow 0.3s;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        .nav-button:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        .icon { font-size: 2em; margin-bottom: 10px; }
        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            padding: 20px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 CE Comprehensive Dashboard v2</h1>
            <p class="version">Claude Enhancer 7.2.0 | 用户: xx | 端口: 7777</p>
        </header>

        <div class="cards">
            <div class="card">
                <h2>📊 系统状态</h2>
                <div class="stat" id="phase">Loading...</div>
                <div class="label">当前阶段</div>
            </div>
            <div class="card">
                <h2>✅ 检查点</h2>
                <div class="stat" id="checkpoints">97</div>
                <div class="label">自动化检查点</div>
            </div>
            <div class="card">
                <h2>🔒 质量门禁</h2>
                <div class="stat">2</div>
                <div class="label">强制质量门禁</div>
            </div>
        </div>

        <div class="section" style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 5px 20px rgba(0,0,0,0.15); margin-bottom: 30px;">
            <h2 style="color: #667eea; margin-bottom: 20px;">🧠 CE学习系统 - 近期累计</h2>
            <div class="cards">
                <div class="card" style="box-shadow: none; background: #f8f9fa;">
                    <h2 style="font-size: 1.2em;">📚 总决策数</h2>
                    <div class="stat" id="total-decisions">-</div>
                    <div class="label">历史累计决策</div>
                </div>
                <div class="card" style="box-shadow: none; background: #f8f9fa;">
                    <h2 style="font-size: 1.2em;">🔥 近30天</h2>
                    <div class="stat" id="recent-decisions">-</div>
                    <div class="label">新增决策</div>
                </div>
                <div class="card" style="box-shadow: none; background: #f8f9fa;">
                    <h2 style="font-size: 1.2em;">💾 缓存大小</h2>
                    <div class="stat" id="cache-size">-</div>
                    <div class="label">记忆缓存</div>
                </div>
            </div>
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 5px;">
                <strong>💡 最近学习：</strong>
                <div id="recent-learning" style="margin-top: 10px; color: #666;">加载中...</div>
            </div>
        </div>

        <div class="nav-buttons">
            <a href="/capabilities" class="nav-button">
                <div class="icon">🎯</div>
                <div>CE能力详情</div>
                <div style="font-size:0.7em; margin-top:10px; opacity:0.8;">
                    7 Phases • 功能矩阵 • 学习系统
                </div>
            </a>
            <a href="/projects" class="nav-button">
                <div class="icon">📡</div>
                <div>项目开发状态</div>
                <div style="font-size:0.7em; margin-top:10px; opacity:0.8;">
                    实时进度 • Git状态 • 任务跟踪
                </div>
            </a>
        </div>

        <div class="footer">
            <p>🤖 Generated with Claude Code | Auto-refresh every 10s</p>
        </div>
    </div>

    <script>
        // Load current phase
        fetch('/api/projects')
            .then(r => r.json())
            .then(data => {
                if (data.projects && data.projects[0]) {
                    document.getElementById('phase').textContent = data.projects[0].current_phase;
                }
            })
            .catch(() => document.getElementById('phase').textContent = 'Phase7');

        // Load learning system data
        fetch('/api/learning')
            .then(r => r.json())
            .then(data => {
                if (data.statistics) {
                    document.getElementById('total-decisions').textContent = data.statistics.total_decisions || 0;
                    const recentCount = data.decisions ? data.decisions.length : 0;
                    document.getElementById('recent-decisions').textContent = recentCount;

                    const cacheSize = data.statistics.memory_cache_size || 0;
                    const sizeKB = (cacheSize / 1024).toFixed(1);
                    document.getElementById('cache-size').textContent = sizeKB + ' KB';
                }

                // Show recent decisions
                if (data.decisions && data.decisions.length > 0) {
                    const recent = data.decisions.slice(-3).reverse(); // Last 3
                    const html = recent.map(d =>
                        `<div style="margin-bottom: 8px;">
                            <span style="color: #667eea;">▸</span> ${d.date || ''}: ${d.title || d.content?.substring(0, 80) || '无标题'}
                        </div>`
                    ).join('');
                    document.getElementById('recent-learning').innerHTML = html || '暂无近期决策';
                } else {
                    document.getElementById('recent-learning').textContent = '暂无近期决策';
                }
            })
            .catch(err => {
                console.error('Learning data error:', err);
                document.getElementById('total-decisions').textContent = '0';
                document.getElementById('recent-decisions').textContent = '0';
                document.getElementById('cache-size').textContent = '0 KB';
                document.getElementById('recent-learning').textContent = '无法加载学习数据';
            });

        // Auto-refresh every 10s
        setTimeout(() => location.reload(), 10000);
    </script>
</body>
</html>"""
        self.send_html(html)

    def serve_capabilities_page(self):
        """CE能力详情页"""
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CE能力详情</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: white;
            padding: 20px 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .back-btn {
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
        }
        .section {
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h2 { color: #667eea; margin-bottom: 15px; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .stat-box {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-num { font-size: 2em; font-weight: bold; color: #764ba2; }
        .stat-label { color: #666; font-size: 0.9em; margin-top: 5px; }
        .feature-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }
        .feature-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
        .feature-name { font-weight: bold; color: #333; margin-bottom: 5px; }
        .feature-priority { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; }
        .P0 { background: #ff4444; color: white; }
        .P1 { background: #ffaa00; color: white; }
        .P2 { background: #44aa44; color: white; }
        #loading { text-align: center; padding: 50px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 CE能力详情</h1>
            <a href="/" class="back-btn">← 返回主页</a>
        </div>

        <div id="loading">Loading...</div>
        <div id="content" style="display:none;">
            <div class="section">
                <h2>📊 核心统计</h2>
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-num" id="phases">7</div>
                        <div class="stat-label">Phases</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-num" id="checkpoints">97</div>
                        <div class="stat-label">检查点</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-num" id="gates">2</div>
                        <div class="stat-label">质量门禁</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-num" id="features">12</div>
                        <div class="stat-label">功能特性</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🎨 功能矩阵 (F001-F012)</h2>
                <div class="feature-list" id="feature-list"></div>
            </div>
        </div>
    </div>

    <script>
        fetch('/api/capabilities')
            .then(r => r.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'block';

                // Update stats
                if (data.core_stats) {
                    document.getElementById('phases').textContent = data.core_stats.total_phases || 7;
                    document.getElementById('checkpoints').textContent = data.core_stats.total_checkpoints || 97;
                    document.getElementById('gates').textContent = data.core_stats.quality_gates || 2;
                }
                if (data.features) {
                    document.getElementById('features').textContent = data.features.length;
                }

                // Render features
                const featureList = document.getElementById('feature-list');
                if (data.features) {
                    data.features.forEach(f => {
                        const div = document.createElement('div');
                        div.className = 'feature-item';
                        div.innerHTML = `
                            <div class="feature-name">${f.id}: ${f.name}</div>
                            <div><span class="feature-priority ${f.priority}">${f.priority}</span> • ${f.category}</div>
                            <div style="color:#666; font-size:0.9em; margin-top:5px;">${f.description}</div>
                        `;
                        featureList.appendChild(div);
                    });
                }
            })
            .catch(err => {
                document.getElementById('loading').textContent = 'Error loading data: ' + err;
            });

        // Auto-refresh
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>"""
        self.send_html(html)

    def serve_projects_page(self):
        """项目开发状态页"""
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>项目开发状态</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: white;
            padding: 20px 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .back-btn {
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
        }
        .section {
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h2 { color: #667eea; margin-bottom: 15px; }
        .project-info {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }
        .info-box {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
        }
        .info-label { color: #666; font-size: 0.9em; margin-bottom: 8px; }
        .info-value { font-size: 1.5em; font-weight: bold; color: #333; }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        #loading { text-align: center; padding: 50px; color: #666; }
        .refresh-info {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📡 项目开发状态</h1>
            <a href="/" class="back-btn">← 返回主页</a>
        </div>

        <div id="loading">Loading...</div>
        <div id="content" style="display:none;">
            <div class="section">
                <h2>🔥 当前项目</h2>
                <div class="project-info">
                    <div class="info-box">
                        <div class="info-label">项目名称</div>
                        <div class="info-value" id="project-name">-</div>
                    </div>
                    <div class="info-box">
                        <div class="info-label">当前分支</div>
                        <div class="info-value" id="branch">-</div>
                    </div>
                    <div class="info-box">
                        <div class="info-label">当前Phase</div>
                        <div class="info-value" id="phase">-</div>
                    </div>
                </div>
                <div class="info-label">进度</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progress" style="width: 0%">0%</div>
                </div>
            </div>

            <div class="section">
                <h2>📊 项目统计</h2>
                <div class="project-info">
                    <div class="info-box">
                        <div class="info-label">项目状态</div>
                        <div class="info-value" id="status">-</div>
                    </div>
                    <div class="info-box">
                        <div class="info-label">已用Agent</div>
                        <div class="info-value" id="agents">-</div>
                    </div>
                    <div class="info-box">
                        <div class="info-label">完成Phase</div>
                        <div class="info-value" id="completed">-</div>
                    </div>
                </div>
            </div>

            <div class="refresh-info">
                🔄 自动刷新: 5秒 | 最后更新: <span id="last-update"></span>
            </div>
        </div>
    </div>

    <script>
        function loadData() {
            fetch('/api/projects')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('content').style.display = 'block';

                    if (data.projects && data.projects[0]) {
                        const p = data.projects[0];
                        document.getElementById('project-name').textContent = p.name || 'Claude Enhancer';
                        document.getElementById('branch').textContent = p.current_branch || 'main';
                        document.getElementById('phase').textContent = p.current_phase || 'Phase7';
                        document.getElementById('status').textContent = p.status || 'active';
                        document.getElementById('agents').textContent = (p.agents_used || []).join(', ') || '0';
                        document.getElementById('completed').textContent = (p.completed_phases || []).length || '7';

                        const progress = p.progress_percentage || 100;
                        document.getElementById('progress').style.width = progress + '%';
                        document.getElementById('progress').textContent = Math.round(progress) + '%';
                    }

                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                })
                .catch(err => {
                    document.getElementById('loading').textContent = 'Error: ' + err;
                });
        }

        loadData();
        setInterval(loadData, 5000); // Refresh every 5s
    </script>
</body>
</html>"""
        self.send_html(html)

    def serve_health(self):
        """API: Health check"""
        self.send_json({'status': 'healthy', 'version': '7.2.0-full', 'port': PORT})

    def serve_capabilities(self):
        """API: Capabilities data"""
        def compute():
            try:
                cap_parser = CapabilityParser(PROJECT_ROOT / "docs" / "CAPABILITY_MATRIX.md")
                cap_result = cap_parser.parse()

                feat_parser = FeatureParser(PROJECT_ROOT / "tools" / "web" / "dashboard.html")
                feat_result = feat_parser.parse()

                return {
                    'core_stats': cap_result.data['core_stats'].__dict__ if cap_result.success else {},
                    'capabilities': [c.__dict__ for c in cap_result.data.get('capabilities', [])] if cap_result.success else [],
                    'features': [f.__dict__ for f in feat_result.data] if feat_result.success else []
                }
            except Exception as e:
                return {'error': str(e)}

        data = capability_cache.get_or_compute('cap_all', compute)
        self.send_json(data)

    def serve_learning(self):
        """API: Learning system data"""
        def compute():
            try:
                parser = LearningSystemParser(PROJECT_ROOT)
                dec_result = parser.parse_decisions()
                mem_result = parser.parse_memory_cache()

                decisions = dec_result.data if dec_result.success else []
                memory = mem_result.data if mem_result.success else None

                return {
                    'decisions': [d.__dict__ for d in decisions[-10:]],
                    'statistics': {
                        'total_decisions': len(decisions),
                        'memory_cache_size': memory.cache_size_bytes if memory else 0
                    }
                }
            except Exception as e:
                return {'error': str(e)}

        data = learning_cache.get_or_compute('learning_all', compute)
        self.send_json(data)

    def serve_projects(self):
        """API: Projects data"""
        def compute():
            try:
                monitor = ProjectMonitor(PROJECT_ROOT)
                status_result = monitor.get_project_status()

                project = status_result.data if status_result.success else None

                return {
                    'projects': [project.__dict__] if project else [],
                    'summary': {'total_projects': 1 if project else 0}
                }
            except Exception as e:
                return {'error': str(e), 'projects': [], 'summary': {'total_projects': 0}}

        data = project_cache.get_or_compute('projects_all', compute)
        self.send_json(data)

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, ensure_ascii=False).encode('utf-8'))

    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

if __name__ == '__main__':
    print(f"🚀 CE Dashboard v2 (Multi-Page Full Version)")
    print(f"📊 http://localhost:{PORT}")
    print(f"📁 Project: {PROJECT_ROOT}")
    print("=" * 60)
    print("Pages:")
    print(f"  • Main:         http://localhost:{PORT}/")
    print(f"  • Capabilities: http://localhost:{PORT}/capabilities")
    print(f"  • Projects:     http://localhost:{PORT}/projects")
    print("=" * 60)

    try:
        server = HTTPServer(('0.0.0.0', PORT), DashboardHandler)
        print("✅ Server started successfully!")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
