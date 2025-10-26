#!/bin/bash
# Test script for Snort3 Installation
# This script verifies that the installation completed successfully

echo "================================================"
echo "Snort3 Installation Verification Test"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to check command
check_command() {
    local cmd=$1
    local description=$2
    
    echo -n "Testing: $description... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

# Function to check file exists
check_file() {
    local file=$1
    local description=$2
    
    echo -n "Checking: $description... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}EXISTS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}MISSING${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "1. Checking Snort3 Installation"
echo "--------------------------------"
check_command "which snort" "Snort3 binary"
check_command "/usr/local/bin/snort -V" "Snort3 version"
echo ""

echo "2. Checking Configuration Files"
echo "--------------------------------"
check_file "/etc/snort/snort.lua" "Main configuration"
check_file "/etc/systemd/system/snort3.service" "Systemd service"
echo ""

echo "3. Checking Service Status"
echo "--------------------------------"
check_command "systemctl is-enabled snort3" "Service enabled"
check_command "systemctl is-active snort3" "Service running"
echo ""

echo "4. Checking Network Configuration"
echo "--------------------------------"
echo "Network adapters detected:"
ip link show | grep -E "^[0-9]+:" | awk '{print "  - " $2}' | sed 's/:$//'
echo ""

echo "5. Checking Log Directory"
echo "--------------------------------"
if [ -d "/var/log/snort" ]; then
    echo -e "${GREEN}Log directory exists${NC}"
    ((PASSED++))
    echo "Log files:"
    ls -lh /var/log/snort/ 2>/dev/null | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'
else
    echo -e "${RED}Log directory missing${NC}"
    ((FAILED++))
fi
echo ""

echo "6. Checking Dependencies"
echo "--------------------------------"
check_command "which cmake" "CMake installed"
check_command "which gcc" "GCC compiler"
check_command "ldconfig -p | grep libdaq" "LibDAQ library"
echo ""

echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "Tests Passed: ${GREEN}$PASSED${NC}"
echo -e "Tests Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! Snort3 is installed and configured correctly.${NC}"
    echo ""
    echo "Next steps:"
    echo "  - Check logs: tail -f /var/log/snort/alert_fast.txt"
    echo "  - View service: systemctl status snort3"
    echo "  - Edit config: nano /etc/snort/snort.lua"
    exit 0
else
    echo -e "${YELLOW}Some tests failed. Please check the installation.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check service logs: journalctl -u snort3 -n 50"
    echo "  - Test configuration: /usr/local/bin/snort -c /etc/snort/snort.lua -T"
    echo "  - Re-run installer: sudo ./snort3_installer.py --auto"
    exit 1
fi
