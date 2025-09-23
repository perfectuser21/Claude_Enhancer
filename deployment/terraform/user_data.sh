#!/bin/bash

# =============================================================================
# EKS Node Group User Data Script
# Optimized configuration for Claude Enhancer Claude Enhancer worker nodes
# =============================================================================

set -euo pipefail

# Variables
CLUSTER_NAME="${cluster_name}"
B64_CLUSTER_CA=""
API_SERVER_URL=""

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/user-data.log
}

log "Starting EKS node initialization for cluster: $CLUSTER_NAME"

# Update system packages
log "Updating system packages..."
yum update -y

# Install additional packages
log "Installing additional packages..."
yum install -y \
    amazon-cloudwatch-agent \
    aws-cli \
    htop \
    iotop \
    jq \
    telnet \
    tcpdump \
    strace

# Configure CloudWatch agent
log "Configuring CloudWatch agent..."
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "cwagent"
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/messages",
                        "log_group_name": "/aws/eks/claude-enhancer/nodes",
                        "log_stream_name": "{instance_id}/messages"
                    },
                    {
                        "file_path": "/var/log/docker",
                        "log_group_name": "/aws/eks/claude-enhancer/nodes",
                        "log_stream_name": "{instance_id}/docker"
                    },
                    {
                        "file_path": "/var/log/kubelet/kubelet.log",
                        "log_group_name": "/aws/eks/claude-enhancer/nodes",
                        "log_stream_name": "{instance_id}/kubelet"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "AWS/EKS/Claude-Enhancer",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60,
                "totalcpu": false
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "diskio": {
                "measurement": [
                    "io_time"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            },
            "netstat": {
                "measurement": [
                    "tcp_established",
                    "tcp_time_wait"
                ],
                "metrics_collection_interval": 60
            },
            "swap": {
                "measurement": [
                    "swap_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
log "Starting CloudWatch agent..."
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
    -s

# Configure Docker daemon
log "Configuring Docker daemon..."
cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "storage-opts": [
        "overlay2.override_kernel_check=true"
    ],
    "exec-opts": ["native.cgroupdriver=systemd"],
    "live-restore": true
}
EOF

# Restart Docker
log "Restarting Docker..."
systemctl restart docker
systemctl enable docker

# Optimize system settings
log "Optimizing system settings..."

# Increase file descriptor limits
cat >> /etc/security/limits.conf << 'EOF'
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
EOF

# Kernel parameter tuning
cat >> /etc/sysctl.conf << 'EOF'
# Network optimizations
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.ip_local_port_range = 1024 65535

# Memory management
vm.max_map_count = 262144
vm.swappiness = 1

# File system
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288
EOF

sysctl -p

# Configure log rotation
log "Configuring log rotation..."
cat > /etc/logrotate.d/kubernetes << 'EOF'
/var/log/pods/*/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    sharedscripts
    postrotate
        /bin/kill -USR1 $(cat /var/run/docker.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF

# Set up monitoring scripts
log "Setting up monitoring scripts..."
mkdir -p /opt/monitoring

cat > /opt/monitoring/node-health.sh << 'EOF'
#!/bin/bash
# Node health monitoring script

LOG_FILE="/var/log/node-health.log"

check_disk_space() {
    local threshold=85
    local usage=$(df / | awk 'NR==2{print $5}' | sed 's/%//')

    if [ "$usage" -gt "$threshold" ]; then
        echo "$(date): WARNING - Disk usage is ${usage}%" >> $LOG_FILE
        # Send CloudWatch custom metric
        aws cloudwatch put-metric-data \
            --namespace "AWS/EKS/Claude-Enhancer/Node" \
            --metric-data MetricName=DiskUsage,Value=$usage,Unit=Percent
    fi
}

check_memory() {
    local threshold=90
    local usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')

    if [ "$usage" -gt "$threshold" ]; then
        echo "$(date): WARNING - Memory usage is ${usage}%" >> $LOG_FILE
        # Send CloudWatch custom metric
        aws cloudwatch put-metric-data \
            --namespace "AWS/EKS/Claude-Enhancer/Node" \
            --metric-data MetricName=MemoryUsage,Value=$usage,Unit=Percent
    fi
}

check_pod_count() {
    local max_pods=110  # Default EKS limit
    local current_pods=$(kubectl get pods --all-namespaces --field-selector=spec.nodeName=$(hostname) --no-headers | wc -l)
    local usage=$(( current_pods * 100 / max_pods ))

    if [ "$usage" -gt 80 ]; then
        echo "$(date): WARNING - Pod usage is ${usage}% (${current_pods}/${max_pods})" >> $LOG_FILE
        # Send CloudWatch custom metric
        aws cloudwatch put-metric-data \
            --namespace "AWS/EKS/Claude-Enhancer/Node" \
            --metric-data MetricName=PodUsage,Value=$usage,Unit=Percent
    fi
}

# Run checks
check_disk_space
check_memory
check_pod_count
EOF

chmod +x /opt/monitoring/node-health.sh

# Set up cron job for monitoring
echo "*/5 * * * * /opt/monitoring/node-health.sh" | crontab -

# Configure kubelet with optimized settings
log "Configuring kubelet..."
cat > /etc/kubernetes/kubelet/kubelet-config.json << EOF
{
    "kind": "KubeletConfiguration",
    "apiVersion": "kubelet.config.k8s.io/v1beta1",
    "address": "0.0.0.0",
    "port": 10250,
    "readOnlyPort": 0,
    "cgroupDriver": "systemd",
    "hairpinMode": "hairpin-veth",
    "serializeImagePulls": false,
    "featureGates": {
        "RotateKubeletServerCertificate": true
    },
    "clusterDomain": "cluster.local",
    "clusterDNS": ["172.20.0.10"],
    "streamingConnectionIdleTimeout": "4h0m0s",
    "nodeStatusUpdateFrequency": "10s",
    "nodeStatusReportFrequency": "5m0s",
    "imageMinimumGCAge": "2m0s",
    "imageGCHighThresholdPercent": 85,
    "imageGCLowThresholdPercent": 80,
    "volumeStatsAggPeriod": "1m0s",
    "systemReserved": {
        "cpu": "100m",
        "memory": "100Mi",
        "ephemeral-storage": "1Gi"
    },
    "kubeReserved": {
        "cpu": "100m",
        "memory": "100Mi",
        "ephemeral-storage": "1Gi"
    },
    "evictionHard": {
        "memory.available": "100Mi",
        "nodefs.available": "10%",
        "nodefs.inodesFree": "5%"
    },
    "evictionSoft": {
        "memory.available": "200Mi",
        "nodefs.available": "15%",
        "nodefs.inodesFree": "10%"
    },
    "evictionSoftGracePeriod": {
        "memory.available": "2m",
        "nodefs.available": "2m",
        "nodefs.inodesFree": "2m"
    },
    "evictionMaxPodGracePeriod": 60,
    "evictionPressureTransitionPeriod": "5m0s"
}
EOF

# Signal completion
log "Node initialization completed successfully!"

# Create completion marker
touch /tmp/user-data-complete