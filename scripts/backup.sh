#!/bin/bash

# Perfect21自动备份脚本
# 支持数据库、配置文件、日志、代码的备份

set -e

# 配置
BACKUP_DIR="${BACKUP_DIR:-/var/lib/perfect21/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATABASE_NAME="${DATABASE_NAME:-perfect21}"
DATABASE_USER="${DATABASE_USER:-perfect21_user}"
PROJECT_ROOT="${PROJECT_ROOT:-/app}"
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"

# 日志配置
LOG_FILE="/var/log/perfect21/backup.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 日志函数
log() {
    echo "[$DATE] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$DATE] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# 创建备份目录
create_backup_dir() {
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    CURRENT_BACKUP_DIR="$BACKUP_DIR/backup_$backup_timestamp"

    mkdir -p "$CURRENT_BACKUP_DIR"
    log "创建备份目录: $CURRENT_BACKUP_DIR"
}

# 备份数据库
backup_database() {
    log "开始备份数据库..."

    local db_backup_file="$CURRENT_BACKUP_DIR/database.sql.gz"

    if command -v pg_dump &> /dev/null; then
        # PostgreSQL备份
        if pg_dump -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" | gzip -$COMPRESSION_LEVEL > "$db_backup_file"; then
            log "数据库备份成功: $db_backup_file"

            # 验证备份文件
            if [ -s "$db_backup_file" ]; then
                local file_size=$(du -h "$db_backup_file" | cut -f1)
                log "数据库备份文件大小: $file_size"
            else
                log_error "数据库备份文件为空"
                return 1
            fi
        else
            log_error "数据库备份失败"
            return 1
        fi
    else
        log_error "未找到pg_dump命令"
        return 1
    fi
}

# 备份应用数据
backup_application_data() {
    log "开始备份应用数据..."

    local data_dir="/var/lib/perfect21/data"
    local data_backup_file="$CURRENT_BACKUP_DIR/application_data.tar.gz"

    if [ -d "$data_dir" ]; then
        if tar -czf "$data_backup_file" -C "$(dirname "$data_dir")" "$(basename "$data_dir")"; then
            local file_size=$(du -h "$data_backup_file" | cut -f1)
            log "应用数据备份成功: $data_backup_file ($file_size)"
        else
            log_error "应用数据备份失败"
            return 1
        fi
    else
        log "应用数据目录不存在，跳过备份"
    fi
}

# 备份配置文件
backup_config() {
    log "开始备份配置文件..."

    local config_backup_file="$CURRENT_BACKUP_DIR/config.tar.gz"
    local config_dirs=("$PROJECT_ROOT/config" "$PROJECT_ROOT/.env" "/etc/perfect21")

    local existing_configs=()
    for config_dir in "${config_dirs[@]}"; do
        if [ -e "$config_dir" ]; then
            existing_configs+=("$config_dir")
        fi
    done

    if [ ${#existing_configs[@]} -gt 0 ]; then
        if tar -czf "$config_backup_file" "${existing_configs[@]}" 2>/dev/null; then
            local file_size=$(du -h "$config_backup_file" | cut -f1)
            log "配置文件备份成功: $config_backup_file ($file_size)"
        else
            log_error "配置文件备份失败"
            return 1
        fi
    else
        log "未找到配置文件，跳过备份"
    fi
}

# 备份日志文件
backup_logs() {
    log "开始备份日志文件..."

    local logs_dir="/var/log/perfect21"
    local logs_backup_file="$CURRENT_BACKUP_DIR/logs.tar.gz"

    if [ -d "$logs_dir" ]; then
        # 只备份过去7天的日志
        if find "$logs_dir" -name "*.log*" -mtime -7 -exec tar -czf "$logs_backup_file" {} + 2>/dev/null; then
            local file_size=$(du -h "$logs_backup_file" | cut -f1)
            log "日志文件备份成功: $logs_backup_file ($file_size)"
        else
            log "日志目录为空或无法访问，跳过备份"
        fi
    else
        log "日志目录不存在，跳过备份"
    fi
}

# 备份代码和Git历史
backup_code() {
    log "开始备份代码..."

    local code_backup_file="$CURRENT_BACKUP_DIR/code.tar.gz"

    if [ -d "$PROJECT_ROOT/.git" ]; then
        # 备份Git仓库
        if tar -czf "$code_backup_file" -C "$(dirname "$PROJECT_ROOT")" \
           --exclude='node_modules' \
           --exclude='venv' \
           --exclude='__pycache__' \
           --exclude='*.pyc' \
           --exclude='logs' \
           --exclude='temp' \
           --exclude='cache' \
           "$(basename "$PROJECT_ROOT")"; then
            local file_size=$(du -h "$code_backup_file" | cut -f1)
            log "代码备份成功: $code_backup_file ($file_size)"
        else
            log_error "代码备份失败"
            return 1
        fi
    else
        log "未找到Git仓库，跳过代码备份"
    fi
}

# 创建备份元数据
create_backup_metadata() {
    log "创建备份元数据..."

    local metadata_file="$CURRENT_BACKUP_DIR/metadata.json"

    cat > "$metadata_file" << EOF
{
  "backup_timestamp": "$(date -Iseconds)",
  "backup_type": "full",
  "environment": "${ENV:-production}",
  "perfect21_version": "2.3.0",
  "database_name": "$DATABASE_NAME",
  "project_root": "$PROJECT_ROOT",
  "backup_size": "$(du -sh "$CURRENT_BACKUP_DIR" | cut -f1)",
  "files": [
$(find "$CURRENT_BACKUP_DIR" -type f -name "*.gz" -o -name "*.sql" | sed 's/.*/"&"/' | paste -sd ',' -)
  ],
  "checksums": {
$(find "$CURRENT_BACKUP_DIR" -type f \( -name "*.gz" -o -name "*.sql" \) -exec sh -c 'echo "    \"$(basename "{}")\": \"$(sha256sum "{}" | cut -d" " -f1)\""' \; | paste -sd ',' -)
  }
}
EOF

    log "备份元数据创建完成: $metadata_file"
}

# 压缩备份目录
compress_backup() {
    log "压缩备份目录..."

    local compressed_backup="$BACKUP_DIR/$(basename "$CURRENT_BACKUP_DIR").tar.gz"

    if tar -czf "$compressed_backup" -C "$BACKUP_DIR" "$(basename "$CURRENT_BACKUP_DIR")"; then
        local original_size=$(du -sh "$CURRENT_BACKUP_DIR" | cut -f1)
        local compressed_size=$(du -sh "$compressed_backup" | cut -f1)

        log "备份压缩完成: $compressed_backup"
        log "压缩前大小: $original_size, 压缩后大小: $compressed_size"

        # 删除原始备份目录
        rm -rf "$CURRENT_BACKUP_DIR"
        CURRENT_BACKUP_DIR="$compressed_backup"
    else
        log_error "备份压缩失败"
        return 1
    fi
}

# 清理旧备份
cleanup_old_backups() {
    log "清理 $RETENTION_DAYS 天前的备份..."

    local deleted_count=0

    # 查找并删除过期的备份文件
    while IFS= read -r -d '' backup_file; do
        rm -f "$backup_file"
        ((deleted_count++))
        log "删除过期备份: $(basename "$backup_file")"
    done < <(find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -print0)

    # 清理空的备份目录
    find "$BACKUP_DIR" -type d -empty -delete 2>/dev/null || true

    if [ $deleted_count -gt 0 ]; then
        log "共删除 $deleted_count 个过期备份"
    else
        log "未找到需要删除的过期备份"
    fi
}

# 发送备份通知
send_notification() {
    local status="$1"
    local message="$2"

    # 这里可以集成邮件、Slack、钉钉等通知方式
    if [ "$status" = "success" ]; then
        log "备份成功通知: $message"
    else
        log_error "备份失败通知: $message"
    fi

    # 示例：发送到webhook
    if [ -n "$WEBHOOK_URL" ]; then
        curl -X POST "$WEBHOOK_URL" \
             -H "Content-Type: application/json" \
             -d "{\"text\":\"Perfect21备份$status: $message\"}" \
             --silent --show-error || log_error "通知发送失败"
    fi
}

# 主备份流程
main() {
    log "开始Perfect21完整备份..."

    # 检查必要的权限和命令
    if [ "$(id -u)" -eq 0 ] || [ -w "$BACKUP_DIR" ]; then
        :  # 有权限，继续
    else
        log_error "权限不足，无法写入备份目录: $BACKUP_DIR"
        exit 1
    fi

    # 创建备份目录
    create_backup_dir

    # 执行各项备份
    local backup_failed=false

    backup_database || backup_failed=true
    backup_application_data || backup_failed=true
    backup_config || backup_failed=true
    backup_logs || backup_failed=true
    backup_code || backup_failed=true

    # 创建元数据
    create_backup_metadata

    # 压缩备份
    compress_backup || backup_failed=true

    # 清理旧备份
    cleanup_old_backups

    # 显示结果
    if [ "$backup_failed" = true ]; then
        log_error "备份过程中出现错误，请检查日志"
        send_notification "失败" "备份过程中出现错误"
        exit 1
    else
        local backup_size=$(du -sh "$CURRENT_BACKUP_DIR" | cut -f1)
        log "备份完成！备份文件: $CURRENT_BACKUP_DIR (大小: $backup_size)"
        send_notification "成功" "备份大小: $backup_size"
    fi
}

# 显示帮助
show_help() {
    cat << EOF
Perfect21备份脚本

用法: $0 [选项]

选项:
    --backup-dir DIR       备份目录 [默认: /var/lib/perfect21/backups]
    --retention-days DAYS  备份保留天数 [默认: 30]
    --database-name NAME   数据库名 [默认: perfect21]
    --database-user USER   数据库用户 [默认: perfect21_user]
    --project-root DIR     项目根目录 [默认: /app]
    --compression-level N  压缩级别 1-9 [默认: 6]
    --webhook-url URL      通知webhook地址
    --help                 显示帮助信息

环境变量:
    BACKUP_DIR             备份目录
    RETENTION_DAYS         保留天数
    DATABASE_NAME          数据库名
    DATABASE_USER          数据库用户
    PROJECT_ROOT           项目根目录
    COMPRESSION_LEVEL      压缩级别
    WEBHOOK_URL            通知URL

EOF
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --database-name)
            DATABASE_NAME="$2"
            shift 2
            ;;
        --database-user)
            DATABASE_USER="$2"
            shift 2
            ;;
        --project-root)
            PROJECT_ROOT="$2"
            shift 2
            ;;
        --compression-level)
            COMPRESSION_LEVEL="$2"
            shift 2
            ;;
        --webhook-url)
            WEBHOOK_URL="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 确保备份目录存在
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# 执行备份
main