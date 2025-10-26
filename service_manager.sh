#!/bin/bash
# Container Service Manager for ML-Enhanced Snort Runner
# Since systemd is not available in container, this provides service-like functionality

SNORT_PID_FILE="/var/run/snort3.pid"
ML_RUNNER_PID_FILE="/var/run/snort-ml-runner.pid"
LOG_DIR="/var/log/snort"
SNORT_CONFIG="/usr/local/etc/snort/snort.lua"
WORK_DIR="/workspaces/snortMakeShiftInstall"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure required directories exist
sudo mkdir -p /var/run /var/log/snort
sudo chown root:root /var/run /var/log/snort

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

start_snort3() {
    log_info "Starting Snort3 IDS/IPS service..."
    
    if [ -f "$SNORT_PID_FILE" ] && kill -0 "$(cat $SNORT_PID_FILE)" 2>/dev/null; then
        log_warning "Snort3 is already running (PID: $(cat $SNORT_PID_FILE))"
        return 0
    fi
    
    # Test configuration first
    log_info "Testing Snort3 configuration..."
    if ! sudo /usr/local/bin/snort -T -c "$SNORT_CONFIG" >/dev/null 2>&1; then
        log_error "Snort3 configuration test failed"
        return 1
    fi
    
    # Check if any Snort3 processes are already running with our config
    EXISTING_PID=$(pgrep -f "/usr/local/bin/snort.*-c.*snort.lua")
    
    if [ -n "$EXISTING_PID" ]; then
        # Use the first PID if multiple processes found
        FIRST_PID=$(echo "$EXISTING_PID" | head -n1)
        echo "$FIRST_PID" > "$SNORT_PID_FILE"
        log_success "Snort3 already running, adopting process (PID: $FIRST_PID)"
        return 0
    fi
    
    # Start Snort3 in daemon mode
    sudo /usr/local/bin/snort -c "$SNORT_CONFIG" -i eth0 -A alert_fast -l "$LOG_DIR" -D
    
    sleep 3
    
    # Find the actual Snort3 daemon PID
    SNORT_PID=$(pgrep -f "/usr/local/bin/snort.*-c.*snort.lua")
    
    if [ -n "$SNORT_PID" ] && kill -0 "$SNORT_PID" 2>/dev/null; then
        echo "$SNORT_PID" > "$SNORT_PID_FILE"
        log_success "Snort3 started successfully (PID: $SNORT_PID)"
        return 0
    else
        log_error "Failed to start Snort3 or find daemon process"
        rm -f "$SNORT_PID_FILE"
        return 1
    fi
}

start_ml_runner() {
    log_info "Starting ML-Enhanced Runner service..."
    
    if [ -f "$ML_RUNNER_PID_FILE" ] && kill -0 "$(cat $ML_RUNNER_PID_FILE)" 2>/dev/null; then
        log_warning "ML Runner is already running (PID: $(cat $ML_RUNNER_PID_FILE))"
        return 0
    fi
    
    cd "$WORK_DIR" || {
        log_error "Failed to change to work directory: $WORK_DIR"
        return 1
    }
    
    # Start ML Runner in background
    nohup python3 main.py --model openai --verbose > /var/log/snort/ml-runner.log 2>&1 &
    ML_RUNNER_PID=$!
    
    echo $ML_RUNNER_PID > "$ML_RUNNER_PID_FILE"
    log_success "ML Runner started successfully (PID: $ML_RUNNER_PID)"
    
    # Verify it's still running after a moment
    sleep 2
    if kill -0 "$ML_RUNNER_PID" 2>/dev/null; then
        log_success "ML Runner is running and stable"
        return 0
    else
        log_error "ML Runner failed to start properly"
        rm -f "$ML_RUNNER_PID_FILE"
        return 1
    fi
}

stop_snort3() {
    log_info "Stopping Snort3 service..."
    
    if [ -f "$SNORT_PID_FILE" ]; then
        PID=$(cat "$SNORT_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            sudo kill -TERM "$PID"
            sleep 3
            if kill -0 "$PID" 2>/dev/null; then
                sudo kill -KILL "$PID"
            fi
            rm -f "$SNORT_PID_FILE"
            log_success "Snort3 stopped"
        else
            log_warning "Snort3 was not running"
            rm -f "$SNORT_PID_FILE"
        fi
    else
        log_warning "No Snort3 PID file found"
    fi
}

stop_ml_runner() {
    log_info "Stopping ML Runner service..."
    
    if [ -f "$ML_RUNNER_PID_FILE" ]; then
        PID=$(cat "$ML_RUNNER_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill -TERM "$PID"
            sleep 3
            if kill -0 "$PID" 2>/dev/null; then
                kill -KILL "$PID"
            fi
            rm -f "$ML_RUNNER_PID_FILE"
            log_success "ML Runner stopped"
        else
            log_warning "ML Runner was not running"
            rm -f "$ML_RUNNER_PID_FILE"
        fi
    else
        log_warning "No ML Runner PID file found"
    fi
}

status_services() {
    echo "🔍 Service Status:"
    echo "=================="
    
    # Check Snort3
    if [ -f "$SNORT_PID_FILE" ] && kill -0 "$(cat $SNORT_PID_FILE)" 2>/dev/null; then
        log_success "Snort3: Running (PID: $(cat $SNORT_PID_FILE))"
    else
        log_error "Snort3: Not running"
    fi
    
    # Check ML Runner
    if [ -f "$ML_RUNNER_PID_FILE" ] && kill -0 "$(cat $ML_RUNNER_PID_FILE)" 2>/dev/null; then
        log_success "ML Runner: Running (PID: $(cat $ML_RUNNER_PID_FILE))"
    else
        log_error "ML Runner: Not running"
    fi
    
    echo ""
    echo "📊 System Resources:"
    echo "==================="
    ps aux | grep -E "(snort|python3.*main.py)" | grep -v grep || echo "No services found in process list"
    
    echo ""
    echo "📁 Log Files:"
    echo "============="
    echo "Snort3 alerts: $LOG_DIR/alert_fast.txt"
    echo "ML Runner log: /var/log/snort/ml-runner.log"
    if [ -f "/var/log/snort/ml-runner.log" ]; then
        echo "Last 3 ML Runner log entries:"
        tail -3 /var/log/snort/ml-runner.log 2>/dev/null | sed 's/^/  /'
    fi
}

restart_services() {
    log_info "Restarting all services..."
    stop_ml_runner
    stop_snort3
    sleep 2
    start_snort3
    start_ml_runner
    status_services
}

case "$1" in
    start)
        echo "🚀 Starting ML-Enhanced Snort Services"
        echo "======================================"
        start_snort3
        if [ $? -eq 0 ]; then
            start_ml_runner
        else
            log_error "Cannot start ML Runner without Snort3"
            exit 1
        fi
        status_services
        ;;
    stop)
        echo "🛑 Stopping ML-Enhanced Snort Services"
        echo "======================================"
        stop_ml_runner
        stop_snort3
        ;;
    restart)
        echo "🔄 Restarting ML-Enhanced Snort Services"
        echo "========================================"
        restart_services
        ;;
    status)
        status_services
        ;;
    logs)
        echo "📜 Service Logs:"
        echo "==============="
        echo "--- Snort3 Alerts (last 10) ---"
        if [ -f "$LOG_DIR/alert_fast.txt" ]; then
            tail -10 "$LOG_DIR/alert_fast.txt"
        else
            echo "No alerts file found"
        fi
        echo ""
        echo "--- ML Runner Logs (last 20) ---"
        if [ -f "/var/log/snort/ml-runner.log" ]; then
            tail -20 /var/log/snort/ml-runner.log
        else
            echo "No ML runner log found"
        fi
        ;;
    *)
        echo "🔧 ML-Enhanced Snort Service Manager"
        echo "===================================="
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start both Snort3 and ML Runner services"
        echo "  stop    - Stop both services"
        echo "  restart - Restart both services"
        echo "  status  - Show service status and resource usage"
        echo "  logs    - Show recent logs from both services"
        echo ""
        echo "Files:"
        echo "  Snort3 PID: $SNORT_PID_FILE"
        echo "  ML Runner PID: $ML_RUNNER_PID_FILE"
        echo "  Logs: $LOG_DIR/"
        echo ""
        exit 1
        ;;
esac