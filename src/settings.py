"""
HostVirtMgr daemon for managing VM's filesystem.

"""
import configparser
from optparse import OptionParser


# HostVirtMgr options
parser = OptionParser()
parser.add_option("-c",
                  "--conf",
                  dest="config",
                  action="store",
                  help="Config file path",
                  default='hostvirtmgr.ini')
(options, args) = parser.parse_args()

# Config file
conf = configparser.ConfigParser()
conf.read(options.config)

# Daemon settings
PORT = conf.getint('daemon', 'port', fallback=8884)
HOST = conf.get('daemon', 'host', fallback='0.0.0.0')

# Cache path
CACHE_DIR = conf.get('cache', 'directory', fallback='/var/lib/libvirt/template_cache')

# External bridge name
BRIDGE_EXT = conf.get('bridge', 'external', fallback='br-ext')

# Backup settings
BACKUP_USER = conf.get('backup', 'user', fallback='hostvirtmgr')
BACKUP_KEY_FILE = conf.get('backup', 'file', fallback='private.pem')

# Firewall rule name
FIREWALL_IN_NAME = conf.get('firewall', 'in_name', fallback='FW_I_')
FIREWALL_OUT_NAME = conf.get('firewall', 'out_name', fallback='FW_O_')

# Firewall insert after line
FIREWALL_INSERT_LINE = conf.getint('firewall', 'insert_line', fallback=2)

# Firewall prefix
FIREWALL_CHAIN_PREFIX = conf.get('firewall', 'chain_prefix', fallback='')

# Firewalld settings
FIREWALLD_STATE_TIMEOUT = conf.getint('firewall', 'state_timeout', fallback=120)
FIREWALLD_STATE_FILE = conf.get('firewall', 'state_file', fallback='/var/run/firewalld/locked')

# Logging settings
"""
logging.DEBUG
10
logging.ERROR
40
logging.INFO
20
"""
LOG_DIR = conf.get('log', 'directory', fallback='/var/log/hostvirtmgr')
WHEN = conf.get('log', 'when', fallback='w6')
INTERVAL = conf.getint('log', 'interval', fallback=1)
LOG_LEVEL = conf.getint('log', 'level', fallback=10)
MAX_SIZE = conf.getint('log', 'max_size', fallback=8192)
BACKUP_COUNT = conf.getint('log', 'backup_count', fallback=6)
