-- Snort3 Configuration Example for IDS/IPS
-- This file provides a basic configuration for Snort3 to work with GitHub Actions workflows

-- Network variables
HOME_NET = 'any'
EXTERNAL_NET = '!$HOME_NET'

-- Paths
RULE_PATH = '/etc/snort/rules'
BUILTIN_RULE_PATH = '/usr/local/etc/rules'
PLUGIN_RULE_PATH = '/usr/local/etc/so_rules'

-- Configure the Snort3 environment
snort = {
    -- Basic configuration
    verbose = true,
    
    -- Set process limits
    daq_dir = '/usr/local/lib/daq',
    
    -- Detection engine configuration
    detection = {
        max_queue_events = 8,
    }
}

-- IPS mode configuration
ips = {
    -- Enable inline mode for IPS
    mode = inline,
    
    -- Variables
    variables = {
        HOME_NET = HOME_NET,
        EXTERNAL_NET = EXTERNAL_NET,
        
        -- Common ports
        HTTP_PORTS = '80',
        HTTPS_PORTS = '443',
        SSH_PORTS = '22',
        FTP_PORTS = '21',
        TELNET_PORTS = '23',
    },
    
    -- Enable built-in rules
    enable_builtin_rules = true,
}

-- Stream configuration for TCP/UDP reassembly
stream = {
    tcp = {
        -- TCP stream reassembly
        reassemble_async = true,
        session_timeout = 180,
    },
    udp = {
        session_timeout = 180,
    },
    ip = {
        session_timeout = 180,
    }
}

-- Alert configuration
alert_fast = {
    -- Fast alert format
    file = true,
    packet = false,
    limit = 10,
}

alert_full = {
    -- Full alert with packet details
    file = true,
    limit = 10,
}

-- JSON output for easy parsing by workflows
alert_json = {
    file = true,
    fields = 'timestamp pkt_num proto pkt_gen pkt_len dir src_addr src_port dst_addr dst_port service rule action',
}

-- Unified2 output for compatibility
unified2 = {
    legacy_events = true,
    limit = 10,
}

-- Log to file
output = {
    logdir = '/var/log/snort',
}

-- DAQ configuration for packet acquisition
daq = {
    -- Module to use (afpacket for Linux, pcap for capture files)
    module = 'dump',
    
    -- Additional DAQ modules
    modules = {
        {
            name = 'afpacket',
            mode = 'inline'
        },
        {
            name = 'pcap',
            mode = 'read-file'
        }
    }
}

-- Host attribute table for better detection
host_tracker = {
    -- Track host information
    file = '/var/log/snort/host_cache.dat',
    dump_file = '/var/log/snort/host_stats.log',
}

-- File inspection
file_id = {
    enable_type = true,
    enable_signature = true,
    enable_capture = true,
    file_rules = {},
}

-- Include rule files
ips.include = RULE_PATH .. '/local.rules'
ips.include = RULE_PATH .. '/snort3-community.rules'

-- Performance monitoring
perf_monitor = {
    modules = {
        {
            name = 'base',
            file = '/var/log/snort/perfmon.txt',
        }
    }
}

-- High availability (if using multiple sensors)
high_availability = {
    min_session_lifetime = 1,
    min_sync_interval = 1,
}

-- Profiling for performance tuning
profiler = {
    modules = {
        {
            name = 'memory',
            file = '/var/log/snort/memory_profile.log'
        },
        {
            name = 'time',
            file = '/var/log/snort/time_profile.log'
        }
    }
}

-- Reputation for IP blocking
reputation = {
    -- Blacklist/whitelist configuration
    priority = 'whitelist',
    whitelist = 'unblack',
}
