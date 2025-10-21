# qBittorrent Hardlinks Checker

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Advanced Python script for automated torrent management in qBittorrent, with a special focus on hardlink checking to optimize disk space in environments with *Arr arrays (Sonarr, Radarr, etc.).

## 🌟 Key Features

### 🔗 Intelligent Hardlink Management
The script checks if torrent files have multiple hardlinks. This is particularly useful when using *Arr arrays that import files via hardlinks:
- **Hardlink present** → File has been imported, keeps the torrent even if seeding time exceeded
- **No hardlink** → File occupies real space, can be removed after seeding

### 🔍 Automatic Checks
- **Automatic recheck**: Identifies and forces recheck of torrents with file errors
- **Non-working tracker removal**: Cleans dead trackers from public torrents
- **Orphan torrent detection**: Identifies and removes torrents deleted from trackers (private only)
- **Seeding time management**: Automatically removes torrents that completed minimum seeding
- **Tracker updates**: Optional integration with external scripts for tracker updates

### ⚙️ Flexible Configuration
- YAML configuration file for every usage scenario
- Support for multiple configurations with separate files
- Filters by category, torrent type (public/private)
- Path mapping for Docker environments

## 📋 Requirements

- Python 3.6 or higher
- qBittorrent with Web UI enabled

### Python Dependencies
```bash
pip install requests pyyaml colorama
```

## 🚀 Installation

1. **Download the script**
```bash
wget https://raw.githubusercontent.com/Jorman/Scripts/master/qBittorrentHardlinksChecker/qBittorrentHardlinksChecker.py
chmod +x qBittorrentHardlinksChecker.py
```

2. **Create configuration file**
```bash
python qBittorrentHardlinksChecker.py --create-config
```

3. **Edit configuration** (see Configuration section)

## ⚙️ Configuration

### Creating Configuration File

The default configuration file is named `qBittorrentHardlinksChecker_config.yaml` and is automatically created with:

```bash
python qBittorrentHardlinksChecker.py --create-config
```

### Complete Configuration Example

```yaml
# qBittorrent server configuration
qbt_host: "http://10.0.0.100"  # Server address (with http/https)
qbt_port: "8081"                # Web UI Port
qbt_username: "admin"           # Web UI Username
qbt_password: "adminadmin"      # Web UI Password

# Options to automatically invoke the tracker update script
enable_auto-update_trackers: true  # Call up script to update trackers
auto-update_trackers_script: "/utilities/scripts/AddqBittorrentTrackers.py"  # Path of the script

# Torrent management configuration
# Minimum seeding time in seconds (e.g., 259200 = 3 days)
# Set to 0 if you want to disable the min_seeding_time check
min_seeding_time: 864000

# List of categories to be processed
# Use ["All"] for all categories
# Use ["Uncategorized"] for torrents without category
# Or specify categories: ["movies", "tv", "books"]
categories:
  - "All"

# Type of torrents to process:
# "" = all torrents (public + private)
# "public" = only public torrents
# "private" = only private torrents
torrent_type: ""

# Enable/disable specific checks
enable_recheck: true        # Check and recheck torrents with errors
enable_orphan_check: true   # Check for orphaned torrents (private only)

# States that identify a torrent as orphaned
orphan_states:
  - "unregistered"
  - "not registered"
  - "not found"
  - "not working"
  - "torrent has been deleted"

# Minimum number of peers before considering a torrent orphaned
# Default: 1
min_peers: 1

# Path mapping (useful for Docker)
# If qBittorrent sees paths different from the real system
# virtual_path: "/downloads"            # Path in qBittorrent
# real_path: "/mnt/storage/torrents"    # Real path on system
```

### Configuration Parameters Explained

#### qBittorrent Connection
- `qbt_host`: qBittorrent server address (include `http://` or `https://`)
- `qbt_port`: Web UI port (default: 8080)
- `qbt_username`: Web UI username
- `qbt_password`: Web UI password

#### Tracker Updates
- `enable_auto-update_trackers`: Enable call to external script for tracker updates
- `auto-update_trackers_script`: Full path to the tracker update script

**Note**: This script integrates with [AddqBittorrentTrackers](https://github.com/Jorman/Scripts/tree/master/AddqBittorrentTrackers) for automatic tracker updates. The script is called with the torrent name using the `-n` parameter. See the dedicated documentation for setup and configuration.

**Configuration example:**
```yaml
enable_auto-update_trackers: true
auto-update_trackers_script: "/utilities/scripts/AddqBittorrentTrackers.py"
```

#### Seeding Management
- `min_seeding_time`: Minimum seeding time in seconds before removal
  - `259200` = 3 days
  - `604800` = 7 days
  - `864000` = 10 days
  - `0` = disable time-based removal

#### Category Filters
- `["All"]`: Process all categories
- `["Uncategorized"]`: Only torrents without category
- `["movies", "tv"]`: Specific categories

#### Torrent Type
- `""`: All torrents (public + private)
- `"public"`: Only public torrents
- `"private"`: Only private torrents

#### Checks
- `enable_recheck`: Enable automatic recheck for torrents with errors
- `enable_orphan_check`: Enable detection of orphaned torrents (works only on private torrents)

#### Orphan Detection
- `orphan_states`: List of tracker messages that identify an orphaned torrent
- `min_peers`: Minimum number of peers before considering a torrent orphaned

#### Path Mapping
Useful when qBittorrent runs in Docker and sees different paths:
```yaml
virtual_path: "/downloads"              # Path as seen by qBittorrent
real_path: "/mnt/storage/torrents"      # Real path on host system
```

## 🎯 Usage

### Basic Commands

```bash
# Run with default configuration
python qBittorrentHardlinksChecker.py

# Run with custom configuration file
python qBittorrentHardlinksChecker.py -c my_config.yaml

# Dry-run mode (no actual changes, only simulation)
python qBittorrentHardlinksChecker.py --dry-run

# Create default configuration file
python qBittorrentHardlinksChecker.py --create-config

# Create custom configuration file
python qBittorrentHardlinksChecker.py --create-config -c custom_config.yaml
```

### Multiple Configurations

You can create different configurations for different scenarios:

```bash
# Configuration for movies
python qBittorrentHardlinksChecker.py -c movies_config.yaml

# Configuration for TV series
python qBittorrentHardlinksChecker.py -c tv_config.yaml

# Configuration for public torrents only
python qBittorrentHardlinksChecker.py -c public_config.yaml
```

### Command Line Arguments

- `-c, --config`: Path to YAML configuration file (default: `qBittorrentHardlinksChecker_config.yaml`)
- `--dry-run`: Run in simulation mode without making actual changes
- `--create-config`: Create a default configuration file

## 🔄 How It Works

### 1. Initial Checks
- ✅ Recheck torrents with file errors (if enabled)
- ✅ Verify hardlinks for each torrent file
- ✅ Display hardlink statistics

### 2. Public Torrent Management
- ✅ Check and remove non-working trackers
- ✅ Tracker updates (if enabled via [AddqBittorrentTrackers](https://github.com/Jorman/Scripts/tree/master/AddqBittorrentTrackers))
- ✅ Seeding time management
- ✅ Hardlink verification

### 3. Private Torrent Management
- ✅ Orphan torrent detection
- ✅ Seeding time management
- ✅ Hardlink verification

### 4. Final Report
- 📊 Total torrents processed
- 📊 Torrents removed
- 📊 Torrents with hardlinks preserved
- 📊 Tracker updates performed

## 🐳 Docker Usage

### docker-compose.yml Example

```yaml
version: '3'

services:
  qbittorrent-manager:
    image: python:3.9-slim
    container_name: qbittorrent-manager
    volumes:
      - ./qBittorrentHardlinksChecker.py:/app/qBittorrentHardlinksChecker.py
      - ./config.yaml:/app/config.yaml
      - /path/to/torrents:/data  # Same mount as qBittorrent
    working_dir: /app
    command: >
      sh -c "pip install requests pyyaml colorama &&
             python qBittorrentHardlinksChecker.py -c config.yaml"
    restart: "no"
```

### Important for Docker

1. **Volume Mapping**: Mount the same torrent directories as qBittorrent
2. **Path Mapping**: Configure `virtual_path` and `real_path` if needed
3. **Network**: Ensure the container can reach qBittorrent

## ⏰ Automation with Cron

### Example Crontab

```bash
# Edit crontab
crontab -e

# Run every 6 hours
0 */6 * * * /usr/bin/python3 /path/to/qBittorrentHardlinksChecker.py -c /path/to/config.yaml >> /var/log/qbt_manager.log 2>&1

# Run daily at 3 AM
0 3 * * * /usr/bin/python3 /path/to/qBittorrentHardlinksChecker.py -c /path/to/config.yaml

# Multiple configurations at different times
0 2 * * * /usr/bin/python3 /path/to/qBittorrentHardlinksChecker.py -c /path/to/movies_config.yaml
0 4 * * * /usr/bin/python3 /path/to/qBittorrentHardlinksChecker.py -c /path/to/tv_config.yaml
```

## 🔐 Security Best Practices

1. **Protect configuration file**
```bash
chmod 600 *_config.yaml
```

2. **Use environment variables for credentials** (future feature)

3. **Add configuration files to .gitignore**

4. **Always test with --dry-run** before production use

### .gitignore File
```
*_config.yaml
*.yaml
config.yaml
```

## 📖 Usage Examples

### Scenario 1: Initial Setup with *Arr
```yaml
# Conservative configuration to start
min_seeding_time: 604800  # 7 days
categories: ["All"]
torrent_type: ""
enable_recheck: true
enable_orphan_check: true
```

```bash
# First run in dry-run mode
python qBittorrentHardlinksChecker.py --dry-run

# If everything is ok, real execution
python qBittorrentHardlinksChecker.py
```

### Scenario 2: Public Tracker Cleanup Only
```yaml
min_seeding_time: 0  # Disable time-based removal
categories: ["All"]
torrent_type: "public"
enable_recheck: false
enable_orphan_check: false
enable_auto-update_trackers: true
```

### Scenario 3: Aggressive Space Management
```yaml
min_seeding_time: 259200  # 3 days
categories: ["tv", "movies"]
torrent_type: ""
enable_recheck: true
enable_orphan_check: true
```

### Scenario 4: Private Trackers Only
```yaml
min_seeding_time: 864000  # 10 days
categories: ["All"]
torrent_type: "private"
enable_recheck: true
enable_orphan_check: true
```

## 🔍 Troubleshooting

### Script Cannot Find Files
**Problem**: Incorrect path mapping (common with Docker)

**Solution**:
```yaml
# Check paths in qBittorrent Web UI
# Then map correctly:
virtual_path: "/downloads"  # Path in qBittorrent
real_path: "/mnt/storage/torrents"  # Real path on system
```

### Torrents with Hardlinks Are Being Removed
**Problem**: Script not detecting hardlinks

**Solution**:
1. Verify that permissions allow reading files
2. Check that path mapping is correct
3. Run with `--dry-run` to see hardlink count

### qBittorrent Connection Error
**Solution**:
```yaml
# Verify configuration
qbt_host: "http://CORRECT_IP"  # Don't forget http://
qbt_port: "CORRECT_PORT"       # Check in qBittorrent > Options > Web UI
```

### Orphan Torrents Not Being Detected
**Cause**: Orphan check only works on **private** torrents

**Verify**:
```yaml
enable_orphan_check: true
torrent_type: ""  # or "private"
```

### Tracker Update Script Not Working
**Problem**: AddqBittorrentTrackers script not found or not executable

**Solution**:
1. Verify the script path is correct
2. Ensure the script is executable: `chmod +x /path/to/AddqBittorrentTrackers.py`
3. Check the [AddqBittorrentTrackers documentation](https://github.com/Jorman/Scripts/tree/master/AddqBittorrentTrackers)

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Open issues for bugs or feature requests
- Propose pull requests
- Improve documentation

## 📄 License

This project is released under the MIT License.

## 🙏 Acknowledgments

- qBittorrent Community
- *Arr array developers
- All contributors

## 📞 Support

For issues or questions:
- Open an [Issue](https://github.com/Jorman/Scripts/issues)
- Start a [Discussion](https://github.com/Jorman/Scripts/discussions)

---

**Note**: This script is provided "as is". Always test it in a development environment before production use.
