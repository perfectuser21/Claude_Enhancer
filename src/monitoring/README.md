# Claude Enhancer Plus - Monitoring Dashboard System

A comprehensive real-time monitoring solution for Claude Enhancer Plus with phase progression tracking, performance metrics, gate validation monitoring, and intelligent alerting.

## 🎯 Features

### 📊 Real-time Monitoring
- **8-Phase Workflow Tracking**: Monitor complete development lifecycle from Phase 0 (Git Branch) to Phase 7 (Deploy)
- **Performance Metrics**: Response times, throughput, error rates, and system resource usage
- **Agent Execution Monitoring**: Track all 56+ professional agents with success rates and execution times
- **Gate Validation Status**: Code quality, security scans, test coverage, and performance gates
- **System Health**: CPU, memory, disk, and network utilization

### 🖥️ Multiple Dashboard Interfaces

#### CLI Dashboard (Terminal Interface)
- **Real-time Updates**: Live metrics with customizable refresh rates
- **Interactive Widgets**: Phase progress, performance charts, agent status tables
- **Keyboard Controls**: Navigate, reset, export, and configure
- **Visual Indicators**: Progress bars, status lights, and alert notifications

#### Web Dashboard (Browser Interface)
- **Modern UI**: Responsive design with real-time charts and graphs
- **WebSocket Updates**: Live data streaming without page refreshes
- **Mobile Friendly**: Optimized for all device sizes
- **REST API**: Full programmatic access to all metrics and controls

### 🚨 Intelligent Alerting
- **Smart Grouping**: Automatically group related alerts to reduce noise
- **Multiple Channels**: Email, Slack, webhooks, and console notifications
- **Escalation Rules**: Auto-escalate critical issues after timeout
- **Suppression Logic**: Prevent alert storms with intelligent deduplication
- **Custom Thresholds**: Configurable alerting for all metrics

### 📈 Advanced Analytics
- **Historical Data**: Store and analyze up to 24 hours of metrics
- **Performance Trends**: Identify patterns and bottlenecks
- **SLI/SLO Tracking**: Monitor service level indicators and objectives
- **Export Capabilities**: JSON exports for external analysis
- **Alert Analytics**: Track MTTR, alert frequency, and resolution patterns

## 🚀 Quick Start

### Installation
```bash
cd src/monitoring
npm install
```

### Start CLI Dashboard
```bash
# Basic CLI dashboard
npm start

# Or directly
node Dashboard.js
```

### Start Web Dashboard
```bash
# Start web server on port 3000
npm run web

# Custom port and host
node WebDashboard.js --port 8080 --host 0.0.0.0
```

### Using the CLI Tool
```bash
# Make CLI tool executable
chmod +x CLI.js

# View help
./CLI.js --help

# Start CLI dashboard
./CLI.js dashboard start

# Start web dashboard
./CLI.js dashboard web --port 3000

# View metrics
./CLI.js metrics view performance --limit 20

# List alerts
./CLI.js alerts list --severity critical

# System health check
./CLI.js health --detailed

# Export metrics
./CLI.js metrics export metrics_backup.json
```

## 📋 Components

### Core Components

#### 1. Dashboard.js - CLI Dashboard
- **Terminal UI**: Built with `blessed` and `blessed-contrib`
- **Real-time Widgets**: Gauges, charts, tables, and progress bars
- **Interactive Controls**: Keyboard navigation and commands
- **Performance Optimized**: Efficient screen updates and memory management

#### 2. WebDashboard.js - Web Interface
- **Express Server**: RESTful API and static file serving
- **WebSocket Support**: Real-time bidirectional communication
- **Modern Frontend**: Chart.js visualizations and responsive design
- **Security Features**: CORS, authentication, and request validation

#### 3. MetricsCollector.js - Data Collection Engine
- **Multi-source Collection**: System metrics, application metrics, and custom data
- **Intelligent Sampling**: Configurable collection intervals and data retention
- **Error Handling**: Graceful degradation and error recovery
- **Storage Management**: Efficient data storage and cleanup

#### 4. AlertManager.js - Alerting System
- **Rule Engine**: Flexible alert rules and thresholds
- **Channel Management**: Multiple notification channels with failover
- **Alert Lifecycle**: Creation, grouping, escalation, acknowledgment, and resolution
- **Analytics**: Alert statistics and performance metrics

#### 5. CLI.js - Command Line Interface
- **Comprehensive Commands**: Full system control via command line
- **Configuration Management**: View, set, and validate configuration
- **Health Checks**: System diagnostics and troubleshooting
- **Data Management**: Export, import, and cleanup operations

### Supporting Files

#### package.json
- **Dependencies**: All required Node.js packages
- **Scripts**: Convenient npm commands for common operations
- **Metadata**: Version, author, and repository information

## 🔧 Configuration

### Environment Variables
```bash
# Web Dashboard
PORT=3000                    # Server port
HOST=localhost              # Server host
DASHBOARD_REFRESH_RATE=1000 # Update interval in ms

# Metrics Collection
METRICS_INTERVAL=1000       # Collection interval in ms
METRICS_RETENTION=86400000  # Data retention in ms (24 hours)
STORAGE_DIR=.claude/logs    # Storage directory

# Alerting
ALERT_GROUPING_WINDOW=300000    # 5 minutes
ALERT_ESCALATION_DELAY=1800000  # 30 minutes
SLACK_WEBHOOK_URL=https://...   # Slack webhook URL
SMTP_HOST=smtp.example.com      # Email server
```

### Configuration Files

#### .claude/logs/monitoring_config.json
```json
{
  "dashboard": {
    "refreshRate": 1000,
    "dataRetention": 86400000
  },
  "metrics": {
    "collectInterval": 1000,
    "storageDir": ".claude/logs",
    "enableSystemMetrics": true,
    "enableGitMetrics": true
  },
  "alerts": {
    "channels": {
      "critical": [
        {"type": "email", "to": "admin@example.com"},
        {"type": "slack", "webhook": "https://..."}
      ],
      "warning": [
        {"type": "console"}
      ]
    },
    "thresholds": {
      "phaseTimeout": 300000,
      "errorRate": 0.05,
      "memoryUsage": 0.9
    }
  }
}
```

## 📊 Monitoring Metrics

### Phase Metrics
- **Current Phase**: Active phase (0-7) in the 8-phase workflow
- **Phase Progress**: Completion percentage within current phase
- **Phase Duration**: Time spent in current phase
- **Transition Times**: Historical phase transition performance

### Performance Metrics
- **Response Time**: Average response time in milliseconds
- **Throughput**: Operations per second
- **Error Rate**: Percentage of failed operations
- **Latency Percentiles**: P50, P95, P99 response times

### System Metrics
- **CPU Usage**: System CPU utilization percentage
- **Memory Usage**: RAM utilization and available memory
- **Disk Usage**: Disk space utilization
- **Network Activity**: Network I/O statistics

### Agent Metrics
- **Agent Status**: Running, idle, or error states for all agents
- **Execution Times**: Duration of agent operations
- **Success Rates**: Percentage of successful agent executions
- **Parallel Execution**: Concurrent agent activity tracking

### Gate Metrics
- **Code Quality**: Code quality gate results and scores
- **Security Scan**: Security vulnerability assessments
- **Test Coverage**: Unit test coverage percentages
- **Performance Gates**: Performance benchmark results

### Cache Metrics
- **Hit Rate**: Cache hit percentage
- **Miss Rate**: Cache miss percentage
- **Eviction Rate**: Cache eviction frequency
- **Cache Size**: Current cache utilization

## 🚨 Alert Types and Thresholds

### Critical Alerts
- **System Down**: Service unavailable for >2 minutes
- **High Memory Usage**: Memory utilization >90%
- **High Error Rate**: Error rate >5% for >5 minutes
- **Phase Timeout**: Phase running >30 minutes

### Warning Alerts
- **Moderate Memory Usage**: Memory utilization >70%
- **Slow Response Time**: Response time >1 second
- **Low Cache Hit Rate**: Hit rate <80%
- **Agent Failures**: Individual agent failure rate >10%

### Info Alerts
- **Phase Transitions**: Successful phase completions
- **Deployment Events**: Successful deployments
- **Configuration Changes**: System configuration updates

## 📡 API Reference

### REST API Endpoints

#### Metrics
```bash
GET /api/metrics                    # Get all metrics
GET /api/metrics/:name             # Get specific metric
GET /api/metrics?since=<timestamp> # Get metrics since timestamp
```

#### System Status
```bash
GET /api/status      # Current system status
GET /api/health      # Health check endpoint
```

#### Alerts
```bash
GET /api/alerts                    # Get active alerts
POST /api/alerts                   # Create new alert
PUT /api/alerts/:id/acknowledge    # Acknowledge alert
PUT /api/alerts/:id/resolve        # Resolve alert
```

#### Configuration
```bash
GET /api/config      # Get current configuration
PUT /api/config      # Update configuration
```

#### Data Management
```bash
POST /api/export     # Export metrics data
POST /api/reset      # Reset all metrics
```

### WebSocket Messages

#### Client to Server
```javascript
// Subscribe to metrics
{
  "type": "subscribe",
  "metrics": ["phase", "performance", "system"]
}

// Unsubscribe from metrics
{
  "type": "unsubscribe",
  "metrics": ["phase"]
}

// Request specific metrics
{
  "type": "get-metrics",
  "metrics": ["performance"],
  "since": 1640995200000,
  "requestId": "req_123"
}

// Keepalive ping
{
  "type": "ping"
}
```

#### Server to Client
```javascript
// Initial data
{
  "type": "initial",
  "data": {
    "status": {...},
    "metrics": {...},
    "config": {...}
  },
  "timestamp": 1640995200000
}

// Metric update
{
  "type": "metric",
  "name": "performance",
  "data": {...},
  "timestamp": 1640995200000
}

// Status update
{
  "type": "status-update",
  "data": {...},
  "timestamp": 1640995200000
}

// Error message
{
  "type": "error",
  "message": "Collection failed",
  "error": "Connection timeout",
  "timestamp": 1640995200000
}

// Keepalive response
{
  "type": "pong",
  "timestamp": 1640995200000
}
```

## 🎛️ Dashboard Controls

### CLI Dashboard Keyboard Shortcuts
- **q, ESC, Ctrl+C**: Quit dashboard
- **r**: Reset all metrics
- **e**: Export metrics to JSON file
- **a**: Show alerts popup
- **h**: Show help information

### Web Dashboard Controls
- **Export Data**: Download metrics as JSON
- **Reset**: Clear all collected metrics
- **Auto Refresh**: Toggle automatic updates
- **Alert View**: View detailed alert information

## 🔍 Troubleshooting

### Common Issues

#### Dashboard Won't Start
```bash
# Check if port is available
lsof -i :3000

# Check permissions
ls -la .claude/logs/

# Verify dependencies
npm list
```

#### No Metrics Data
```bash
# Check metrics collector
./CLI.js metrics collect --interval 5000

# Verify storage directory
ls -la .claude/logs/

# Check configuration
./CLI.js config show
```

#### Alerts Not Working
```bash
# Test alert system
./CLI.js alerts test --severity critical

# Check alert configuration
./CLI.js config show | grep alerts

# Verify channel configuration
```

#### High Memory Usage
```bash
# Check system health
./CLI.js health --detailed

# Clean up old data
./CLI.js cleanup --days 3

# Monitor resource usage
top -p $(pgrep node)
```

### Performance Optimization

#### Reduce Memory Usage
- Decrease data retention period
- Increase collection interval
- Limit number of concurrent agents
- Enable data compression

#### Improve Response Time
- Use faster storage (SSD)
- Increase system resources
- Optimize collection queries
- Enable caching

#### Network Optimization
- Enable gzip compression
- Use WebSocket for real-time updates
- Implement connection pooling
- Add CDN for static assets

## 📚 Development

### Project Structure
```
src/monitoring/
├── Dashboard.js          # CLI dashboard with blessed
├── WebDashboard.js       # Web dashboard with Express
├── MetricsCollector.js   # Data collection engine
├── AlertManager.js       # Alerting and notification system
├── CLI.js               # Command-line interface
├── package.json         # Dependencies and scripts
├── README.md           # This documentation
└── web/                # Web dashboard static files
    └── index.html      # Dashboard HTML (generated)
```

### Adding New Metrics
1. **Create Collector Function**:
```javascript
async collectCustomMetrics(timestamp) {
    // Collect your custom metric data
    return {
        myMetric: value,
        timestamp
    };
}
```

2. **Register Collector**:
```javascript
this.collectors.set('custom', this.collectCustomMetrics.bind(this));
```

3. **Add Dashboard Widget**:
```javascript
updateCustomWidget(data) {
    // Update dashboard display
}
```

### Adding Alert Channels
1. **Implement Channel Handler**:
```javascript
async sendCustomAlert(channel, alert, group) {
    // Send alert via your custom channel
}
```

2. **Register Channel Type**:
```javascript
case 'custom':
    await this.sendCustomAlert(channel, alert, group);
    break;
```

### Testing
```bash
# Run all tests
npm test

# Run specific test suite
npm run test:dashboard
npm run test:metrics
npm run test:alerts

# Run with coverage
npm run test:coverage
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Guidelines
- Follow existing code style and patterns
- Add comprehensive tests for new features
- Update documentation for API changes
- Ensure backward compatibility
- Use semantic versioning for releases

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Blessed/Blessed-Contrib**: Terminal UI framework
- **Express.js**: Web framework
- **WebSocket**: Real-time communication
- **Chart.js**: Web dashboard visualizations
- **Node.js**: Runtime environment

---

Built with ❤️ for Claude Enhancer Plus by Claude Code

For support and questions, please open an issue on GitHub or contact the development team.