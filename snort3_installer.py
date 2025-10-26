#!/usr/bin/env python3
"""
Snort3 Installation and Configuration Tool
Automates the installation of Snort3 and configures it for IDS/IPS with 3 network adapters
"""

import os
import sys
import subprocess
import argparse
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Snort3Installer:
    """Main installer class for Snort3"""
    
    def __init__(self, install_dir: str = "/usr/local", config_dir: str = "/etc/snort"):
        self.install_dir = Path(install_dir)
        self.config_dir = Path(config_dir)
        self.build_dir = Path("/tmp/snort3_build")
        self.snort_version = "3.1.75.0"
        self.daq_version = "3.0.13"
        self.libdaq_version = "3.0.13"
        
        # Network adapter configuration
        self.incoming_adapter = None  # Onboard ethernet for incoming traffic
        self.offload_adapter = None   # USB ethernet for offload
        self.control_adapter = None   # Wireless for control/management
        
    def check_root(self) -> bool:
        """Check if running with root privileges"""
        if os.geteuid() != 0:
            logger.error("This script must be run as root")
            return False
        return True
    
    def detect_environment(self) -> Dict[str, bool]:
        """Detect if running in container, VM, or bare metal"""
        env = {
            'container': False,
            'vm': False,
            'bare_metal': True
        }
        
        # Check for container
        if os.path.exists('/.dockerenv'):
            env['container'] = True
            env['bare_metal'] = False
        elif os.path.exists('/run/.containerenv'):
            env['container'] = True
            env['bare_metal'] = False
        
        # Check for VM
        try:
            result = subprocess.run(['systemd-detect-virt'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip() not in ['none', '']:
                env['vm'] = True
                env['bare_metal'] = False
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        logger.info(f"Environment detected: Container={env['container']}, "
                   f"VM={env['vm']}, Bare Metal={env['bare_metal']}")
        return env
    
    def install_dependencies(self) -> bool:
        """Install required system dependencies"""
        logger.info("Installing system dependencies...")
        
        dependencies = [
            'build-essential',
            'libpcap-dev',
            'libpcre3-dev',
            'libnet1-dev',
            'zlib1g-dev',
            'luajit',
            'libdumbnet-dev',
            'bison',
            'flex',
            'liblzma-dev',
            'openssl',
            'libssl-dev',
            'pkg-config',
            'libhwloc-dev',
            'cmake',
            'cpputest',
            'libsqlite3-dev',
            'uuid-dev',
            'libcmocka-dev',
            'libnetfilter-queue-dev',
            'libmnl-dev',
            'autotools-dev',
            'libluajit-5.1-dev',
            'libunwind-dev',
            'git',
            'wget',
            'ethtool',
            'net-tools',
            'iproute2'
        ]
        
        try:
            # Update package list
            subprocess.run(['apt-get', 'update'], check=True)
            
            # Install dependencies
            cmd = ['apt-get', 'install', '-y'] + dependencies
            subprocess.run(cmd, check=True)
            
            logger.info("Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def download_and_extract(self, url: str, extract_dir: Path) -> bool:
        """Download and extract a tarball"""
        try:
            filename = url.split('/')[-1]
            filepath = self.build_dir / filename
            
            logger.info(f"Downloading {filename}...")
            subprocess.run(['wget', '-O', str(filepath), url], check=True)
            
            logger.info(f"Extracting {filename}...")
            if filename.endswith('.tar.gz'):
                subprocess.run(['tar', 'xzf', str(filepath), '-C', str(extract_dir)], 
                             check=True)
            elif filename.endswith('.tar.bz2'):
                subprocess.run(['tar', 'xjf', str(filepath), '-C', str(extract_dir)], 
                             check=True)
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to download/extract {url}: {e}")
            return False
    
    def install_libdaq(self) -> bool:
        """Install LibDAQ (Data Acquisition library)"""
        logger.info("Installing LibDAQ...")
        
        self.build_dir.mkdir(parents=True, exist_ok=True)
        
        url = f"https://github.com/snort3/libdaq/archive/refs/tags/v{self.libdaq_version}.tar.gz"
        
        if not self.download_and_extract(url, self.build_dir):
            return False
        
        libdaq_dir = self.build_dir / f"libdaq-{self.libdaq_version}"
        
        try:
            os.chdir(libdaq_dir)
            
            subprocess.run(['./bootstrap'], check=True)
            subprocess.run(['./configure'], check=True)
            subprocess.run(['make', '-j', str(os.cpu_count())], check=True)
            subprocess.run(['make', 'install'], check=True)
            subprocess.run(['ldconfig'], check=True)
            
            logger.info("LibDAQ installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install LibDAQ: {e}")
            return False
    
    def install_snort3(self) -> bool:
        """Install Snort3 from source"""
        logger.info("Installing Snort3...")
        
        url = f"https://github.com/snort3/snort3/archive/refs/tags/{self.snort_version}.tar.gz"
        
        if not self.download_and_extract(url, self.build_dir):
            return False
        
        snort_dir = self.build_dir / f"snort3-{self.snort_version}"
        build_subdir = snort_dir / "build"
        build_subdir.mkdir(exist_ok=True)
        
        try:
            os.chdir(build_subdir)
            
            subprocess.run([
                'cmake', '..',
                f'-DCMAKE_INSTALL_PREFIX={self.install_dir}'
            ], check=True)
            subprocess.run(['make', '-j', str(os.cpu_count())], check=True)
            subprocess.run(['make', 'install'], check=True)
            
            logger.info("Snort3 installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Snort3: {e}")
            return False
    
    def detect_network_adapters(self) -> List[str]:
        """Detect available network adapters"""
        try:
            result = subprocess.run(['ip', 'link', 'show'], 
                                  capture_output=True, text=True, check=True)
            
            adapters = []
            for line in result.stdout.split('\n'):
                if ': ' in line and '@' not in line:
                    parts = line.split(': ')
                    if len(parts) >= 2:
                        adapter = parts[1].split(':')[0]
                        if adapter not in ['lo']:
                            adapters.append(adapter)
            
            logger.info(f"Detected network adapters: {adapters}")
            return adapters
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to detect network adapters: {e}")
            return []
    
    def configure_network_adapters(self, incoming: str, offload: str, control: str) -> bool:
        """Configure the three network adapters"""
        self.incoming_adapter = incoming
        self.offload_adapter = offload
        self.control_adapter = control
        
        logger.info(f"Configuring network adapters:")
        logger.info(f"  Incoming (onboard ethernet): {incoming}")
        logger.info(f"  Offload (USB ethernet): {offload}")
        logger.info(f"  Control (wireless): {control}")
        
        try:
            # Configure incoming adapter for promiscuous mode
            subprocess.run(['ip', 'link', 'set', incoming, 'promisc', 'on'], check=True)
            subprocess.run(['ethtool', '-K', incoming, 'gro', 'off', 'lro', 'off'], 
                         check=False)  # Don't fail if ethtool features not available
            
            # Configure offload adapter
            subprocess.run(['ip', 'link', 'set', offload, 'up'], check=True)
            
            # Keep control adapter in normal mode for SSH/management
            subprocess.run(['ip', 'link', 'set', control, 'up'], check=True)
            
            logger.info("Network adapters configured successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure network adapters: {e}")
            return False
    
    def create_snort_config(self) -> bool:
        """Create Snort3 configuration for IDS/IPS mode"""
        logger.info("Creating Snort3 configuration...")
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        config_content = f"""-- Snort3 IDS/IPS Configuration
-- Auto-generated by snort3_installer.py

---------------------------------------------------------------------------
-- 1. Setup the network addresses you are protecting
---------------------------------------------------------------------------

HOME_NET = 'any'
EXTERNAL_NET = '!$HOME_NET'

---------------------------------------------------------------------------
-- 2. Configure detection engine
---------------------------------------------------------------------------

ips = {{
    enable_builtin_rules = true,
    variables = default_variables
}}

---------------------------------------------------------------------------
-- 3. Configure DAQ (Data Acquisition)
---------------------------------------------------------------------------

daq = {{
    inputs = {{ '{self.incoming_adapter or "eth0"}' }},
    module_dirs = {{ '/usr/local/lib/daq' }},
    modules = {{
        {{
            name = 'afpacket',
            mode = 'inline'
        }}
    }}
}}

---------------------------------------------------------------------------
-- 4. Configure output
---------------------------------------------------------------------------

alert_fast = {{
    file = true,
    packet = false
}}

---------------------------------------------------------------------------
-- 5. Configure stream processing
---------------------------------------------------------------------------

stream = {{
    tcp = true,
    udp = true,
    icmp = true
}}

stream_tcp = {{
    policy = 'linux'
}}

---------------------------------------------------------------------------
-- 6. Configure network traffic normalization
---------------------------------------------------------------------------

normalizer = {{
    tcp = {{
        ips = true
    }}
}}

---------------------------------------------------------------------------
-- 7. Configure active responses for IPS mode
---------------------------------------------------------------------------

active = {{
    attempts = 2,
    device = '{self.offload_adapter or "eth1"}'
}}

---------------------------------------------------------------------------
-- 8. Configure protocol-specific settings
---------------------------------------------------------------------------

http_inspect = {{
    decompress_pdf = true,
    decompress_swf = true,
    decompress_zip = true
}}

---------------------------------------------------------------------------
-- 9. Configure logging
---------------------------------------------------------------------------

file_log = {{
    log_pkt_time = true,
    log_sys_time = true
}}
"""
        
        config_file = self.config_dir / "snort.lua"
        try:
            with open(config_file, 'w') as f:
                f.write(config_content)
            logger.info(f"Configuration written to {config_file}")
            return True
        except IOError as e:
            logger.error(f"Failed to write configuration: {e}")
            return False
    
    def create_systemd_service(self) -> bool:
        """Create systemd service for persistent Snort3 operation"""
        logger.info("Creating systemd service...")
        
        service_content = f"""[Unit]
Description=Snort3 IDS/IPS Service
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={self.install_dir}/bin/snort -c {self.config_dir}/snort.lua -i {self.incoming_adapter or 'eth0'} -A alert_fast -l /var/log/snort -D
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=10
User=root
Group=root

# Security settings
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/snort3.service")
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            # Reload systemd
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            
            logger.info(f"Systemd service created at {service_file}")
            return True
        except (IOError, subprocess.CalledProcessError) as e:
            logger.error(f"Failed to create systemd service: {e}")
            return False
    
    def create_network_persistence(self) -> bool:
        """Create network configuration persistence"""
        logger.info("Setting up network persistence...")
        
        # Create a script to configure network on boot
        netconfig_script = Path("/etc/network/if-up.d/snort-network-config")
        
        script_content = f"""#!/bin/bash
# Snort3 Network Configuration
# Auto-generated by snort3_installer.py

# Configure incoming adapter
if [ "$IFACE" = "{self.incoming_adapter}" ]; then
    ip link set {self.incoming_adapter} promisc on
    ethtool -K {self.incoming_adapter} gro off lro off 2>/dev/null || true
fi

# Configure offload adapter  
if [ "$IFACE" = "{self.offload_adapter}" ]; then
    ip link set {self.offload_adapter} up
fi

# Configure control adapter
if [ "$IFACE" = "{self.control_adapter}" ]; then
    ip link set {self.control_adapter} up
fi
"""
        
        try:
            with open(netconfig_script, 'w') as f:
                f.write(script_content)
            
            netconfig_script.chmod(0o755)
            logger.info("Network persistence configured")
            return True
        except IOError as e:
            logger.error(f"Failed to create network persistence: {e}")
            return False
    
    def enable_and_start_service(self) -> bool:
        """Enable and start the Snort3 service"""
        logger.info("Enabling and starting Snort3 service...")
        
        try:
            subprocess.run(['systemctl', 'enable', 'snort3'], check=True)
            subprocess.run(['systemctl', 'start', 'snort3'], check=True)
            
            logger.info("Snort3 service enabled and started")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to enable/start service: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify Snort3 installation"""
        logger.info("Verifying installation...")
        
        try:
            result = subprocess.run([f'{self.install_dir}/bin/snort', '-V'], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"Snort version: {result.stdout.strip()}")
            
            # Check service status
            result = subprocess.run(['systemctl', 'is-active', 'snort3'], 
                                  capture_output=True, text=True)
            logger.info(f"Service status: {result.stdout.strip()}")
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Installation verification failed: {e}")
            return False
    
    def run_full_installation(self, incoming_adapter: str, offload_adapter: str, 
                            control_adapter: str) -> bool:
        """Run the complete installation process"""
        logger.info("Starting Snort3 full installation...")
        
        if not self.check_root():
            return False
        
        # Detect environment
        env = self.detect_environment()
        
        # Install dependencies
        if not self.install_dependencies():
            logger.error("Failed to install dependencies")
            return False
        
        # Install LibDAQ
        if not self.install_libdaq():
            logger.error("Failed to install LibDAQ")
            return False
        
        # Install Snort3
        if not self.install_snort3():
            logger.error("Failed to install Snort3")
            return False
        
        # Configure network adapters
        if not self.configure_network_adapters(incoming_adapter, offload_adapter, 
                                              control_adapter):
            logger.error("Failed to configure network adapters")
            return False
        
        # Create Snort configuration
        if not self.create_snort_config():
            logger.error("Failed to create Snort configuration")
            return False
        
        # Create systemd service
        if not self.create_systemd_service():
            logger.error("Failed to create systemd service")
            return False
        
        # Create network persistence
        if not self.create_network_persistence():
            logger.error("Failed to create network persistence")
            return False
        
        # Enable and start service
        if not self.enable_and_start_service():
            logger.error("Failed to enable/start service")
            return False
        
        # Verify installation
        if not self.verify_installation():
            logger.warning("Installation verification had issues")
        
        logger.info("=" * 60)
        logger.info("Snort3 installation completed successfully!")
        logger.info("=" * 60)
        logger.info(f"Configuration: {self.config_dir}/snort.lua")
        logger.info(f"Logs: /var/log/snort")
        logger.info(f"Service: systemctl status snort3")
        logger.info("=" * 60)
        
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Snort3 Installation and Configuration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect adapters and install
  sudo ./snort3_installer.py --auto

  # Specify network adapters manually
  sudo ./snort3_installer.py --incoming eth0 --offload eth1 --control wlan0
  
  # List available network adapters
  sudo ./snort3_installer.py --list-adapters
        """
    )
    
    parser.add_argument('--incoming', help='Incoming traffic adapter (onboard ethernet)')
    parser.add_argument('--offload', help='Offload adapter (USB ethernet)')
    parser.add_argument('--control', help='Control adapter (wireless)')
    parser.add_argument('--auto', action='store_true', 
                       help='Auto-detect and assign adapters')
    parser.add_argument('--list-adapters', action='store_true',
                       help='List available network adapters')
    parser.add_argument('--install-dir', default='/usr/local',
                       help='Installation directory (default: /usr/local)')
    parser.add_argument('--config-dir', default='/etc/snort',
                       help='Configuration directory (default: /etc/snort)')
    
    args = parser.parse_args()
    
    installer = Snort3Installer(
        install_dir=args.install_dir,
        config_dir=args.config_dir
    )
    
    # List adapters if requested
    if args.list_adapters:
        adapters = installer.detect_network_adapters()
        print("Available network adapters:")
        for adapter in adapters:
            print(f"  - {adapter}")
        return 0
    
    # Determine network adapters
    if args.auto:
        adapters = installer.detect_network_adapters()
        if len(adapters) < 3:
            logger.error(f"Auto-detection found only {len(adapters)} adapters, need 3")
            logger.info("Please specify adapters manually with --incoming, --offload, --control")
            return 1
        
        incoming = adapters[0]
        offload = adapters[1]
        control = adapters[2]
        logger.info(f"Auto-assigned: incoming={incoming}, offload={offload}, control={control}")
    elif args.incoming and args.offload and args.control:
        incoming = args.incoming
        offload = args.offload
        control = args.control
    else:
        logger.error("Must specify either --auto or all three adapters "
                    "(--incoming, --offload, --control)")
        parser.print_help()
        return 1
    
    # Run installation
    success = installer.run_full_installation(incoming, offload, control)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
