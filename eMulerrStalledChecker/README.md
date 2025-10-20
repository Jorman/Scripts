# eMulerr Stalled Checker

![Docker Pulls](https://img.shields.io/docker/pulls/chryses/emulerr-stalled-checker)
![Docker Image Size](https://img.shields.io/docker/image-size/chryses/emulerr-stalled-checker)
![GitHub](https://img.shields.io/github/license/Jorman/Scripts)

> Automated monitoring and cleanup tool for stalled ed2k/Kad downloads in Sonarr/Radarr via eMulerr

## 📖 Overview

eMulerr Stalled Checker is a Docker-based monitoring service that automatically detects and removes stalled or source-less downloads from [eMulerr](https://github.com/isc30/eMulerr), keeping your [Sonarr](https://github.com/Sonarr/Sonarr) and [Radarr](https://github.com/Radarr/Radarr) download queues clean and efficient.

When eMulerr downloads (ed2k/Kad network) get stuck without sources or stall indefinitely, this tool identifies them through configurable health checks, removes them from eMulerr, marks them as failed in the respective *Arr application, and automatically triggers a new search. This ensures your media automation keeps running smoothly without manual intervention.

The script intelligently handles downloads by category, respects monitoring status in Sonarr/Radarr, and can clean up orphaned downloads that exist only in eMulerr but not in your *Arr instances anymore.

## ✨ Features

- 🔍 **Smart Stall Detection** - Configurable checks before marking downloads as stalled
- 🗑️ **Automatic Cleanup** - Removes stalled downloads and triggers new searches
- 📊 **Category-Based Management** - Handles Sonarr and Radarr downloads separately via categories
- 🧹 **Orphan Detection** - Removes downloads that exist only in eMulerr (optional)
- 📺 **Monitoring-Aware** - Respects series/season/episode/movie monitoring status
- ⏰ **Grace Period** - Configurable waiting time for recent downloads
- 🔔 **Pushover Notifications** - Real-time alerts for removed downloads
- 🐳 **Docker Native** - Easy deployment and management
- 📝 **Dry Run Mode** - Test configuration without actual changes
- 📊 **Detailed Logging** - File and console logging with configurable levels

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Running instances of:
  - [eMulerr](https://github.com/isc30/eMulerr)
  - [Sonarr](https://github.com/Sonarr/Sonarr) and/or [Radarr](https://github.com/Radarr/Radarr)
- eMulerr configured as download client in Sonarr/Radarr with specific categories

### Using Docker Run

```bash
docker run -d \
  --name emulerr-stalled-checker \
  --restart unless-stopped \
  -e TZ=Europe/Rome \
  -e CHECK_INTERVAL=10 \
  -e EMULERR_HOST=http://your-emulerr:3000 \
  -e STALL_CHECKS=30 \
  -e STALL_DAYS=20 \
  -e DOWNLOAD_CLIENT=emulerr \
  -e RADARR_HOST=http://your-radarr:7878 \
  -e RADARR_API_KEY=your_radarr_api_key \
  -e RADARR_CATEGORY=radarr-eMulerr \
  -e SONARR_HOST=http://your-sonarr:8989 \
  -e SONARR_API_KEY=your_sonarr_api_key \
  -e SONARR_CATEGORY=tv-sonarr-eMulerr \
  chryses/emulerr-stalled-checker:latest
```

### Using Docker Compose

```yaml
version: '3.8'

services:
  emulerr-stalled-checker:
    image: chryses/emulerr-stalled-checker:latest
    container_name: emulerr-stalled-checker
    restart: unless-stopped
    environment:
      - TZ=Europe/Rome
      - CHECK_INTERVAL=10
      - EMULERR_HOST=http://10.0.0.100:3000
      - STALL_CHECKS=30
      - STALL_DAYS=20
      - RECENT_DOWNLOAD_GRACE_PERIOD=30
      - DELETE_IF_UNMONITORED_SERIE=false
      - DELETE_IF_UNMONITORED_SEASON=false
      - DELETE_IF_UNMONITORED_EPISODE=true
      - DELETE_IF_UNMONITORED_MOVIE=true
      - DELETE_IF_ONLY_ON_EMULERR=false
      - PUSHOVER_USER_KEY=your_pushover_user_key
      - PUSHOVER_APP_TOKEN=your_pushover_app_token
      - LOG_LEVEL=info
      - DRY_RUN=false
      - DOWNLOAD_CLIENT=emulerr
      - RADARR_HOST=http://10.0.0.100:7878
      - RADARR_API_KEY=your_radarr_api_key
      - RADARR_CATEGORY=radarr-eMulerr
      - SONARR_HOST=http://10.0.0.100:8989
      - SONARR_API_KEY=your_sonarr_api_key
      - SONARR_CATEGORY=tv-sonarr-eMulerr
    # Optional: Enable file logging
    # volumes:
    #   - ./logs:/logs
    # environment:
    #   - LOG_TO_FILE=/logs/emulerr_stalled_checker.log
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://10.0.0.100:3000"]
      interval: 1m
      timeout: 10s
      retries: 3
```

## ⚙️ Configuration

### Environment Variables

#### Core Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `EMULERR_HOST` | eMulerr instance URL (e.g., `http://10.0.0.100:3000`) | - | ✅ Yes |
| `CHECK_INTERVAL` | Minutes between stall checks | - | ✅ Yes |
| `STALL_CHECKS` | Number of consecutive checks before marking as stalled | - | ✅ Yes |
| `STALL_DAYS` | Days before a never-completed download is considered stalled | - | ✅ Yes |
| `RECENT_DOWNLOAD_GRACE_PERIOD` | Minutes to wait before checking recent downloads | `30` | ✅ Yes |

#### *Arr Integration (at least one required)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DOWNLOAD_CLIENT` | Download client name configured in Sonarr/Radarr | - | ✅ Yes |
| `RADARR_HOST` | Radarr instance URL | `None` | ⚠️ Conditional |
| `RADARR_API_KEY` | Radarr API key | `None` | ⚠️ Conditional |
| `RADARR_CATEGORY` | eMulerr category for Radarr downloads | `None` | ⚠️ Conditional |
| `SONARR_HOST` | Sonarr instance URL | `None` | ⚠️ Conditional |
| `SONARR_API_KEY` | Sonarr API key | `None` | ⚠️ Conditional |
| `SONARR_CATEGORY` | eMulerr category for Sonarr downloads | `None` | ⚠️ Conditional |

> **Note:** You must configure at least one *Arr service (Radarr or Sonarr). If you use both, configure both sets of variables.

#### Monitoring & Cleanup Rules

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DELETE_IF_UNMONITORED_SERIE` | Remove downloads for unmonitored series | `false` | ❌ No |
| `DELETE_IF_UNMONITORED_SEASON` | Remove downloads for unmonitored seasons | `false` | ❌ No |
| `DELETE_IF_UNMONITORED_EPISODE` | Remove downloads for unmonitored episodes | `false` | ❌ No |
| `DELETE_IF_UNMONITORED_MOVIE` | Remove downloads for unmonitored movies | `false` | ❌ No |
| `DELETE_IF_ONLY_ON_EMULERR` | Remove orphaned downloads (only in eMulerr, not in *Arr) | `false` | ❌ No |

#### Notifications

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PUSHOVER_APP_TOKEN` | Pushover application token | - | ❌ No |
| `PUSHOVER_USER_KEY` | Pushover user key | - | ❌ No |

#### Logging & Debug

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOG_LEVEL` | Logging level: `debug`, `info`, `warning`, `error`, `critical` | `info` | ❌ No |
| `LOG_TO_FILE` | Full path to log file (requires volume mount) | `None` | ❌ No |
| `DRY_RUN` | Test mode - no actual deletions (`true`/`false`) | `false` | ❌ No |
| `TZ` | Timezone (e.g., `Europe/Rome`) | `UTC` | ❌ No |

## 📊 How It Works

### Download Monitoring Workflow

1. **Periodic Checks** - Every `CHECK_INTERVAL` minutes, the script queries eMulerr for all downloads
2. **Category Filtering** - Identifies downloads matching configured Sonarr/Radarr categories
3. **Health Assessment** - For each download:
   - Checks if it's stalled (no progress, no sources)
   - Verifies against `STALL_CHECKS` threshold
   - Applies `RECENT_DOWNLOAD_GRACE_PERIOD` for new downloads
   - Checks `STALL_DAYS` for long-running incomplete downloads
4. **Monitoring Status** - Queries Sonarr/Radarr to verify if content is still monitored
5. **Orphan Detection** - Identifies downloads that exist only in eMulerr (optional)
6. **Action Execution** - If criteria are met:
   - Removes download from eMulerr
   - Marks as failed in corresponding *Arr application
   - Triggers automatic search for alternative source
   - Sends notification via Pushover (if configured)

### Stall Detection Logic

A download is considered stalled when:

- **No Progress**: Download hasn't made progress for `STALL_CHECKS` consecutive checks
- **No Sources**: Download has no active sources/peers
- **Time-Based**: Incomplete download older than `STALL_DAYS` days
- **Grace Period**: Recent downloads (< `RECENT_DOWNLOAD_GRACE_PERIOD` minutes) are skipped

### Monitoring Checks

Before removing any download, the script verifies:

- **Series/Season/Episode Monitoring** (Sonarr):
  - `DELETE_IF_UNMONITORED_SERIE=true` → removes if series is unmonitored
  - `DELETE_IF_UNMONITORED_SEASON=true` → removes if season is unmonitored
  - `DELETE_IF_UNMONITORED_EPISODE=true` → removes if episode is unmonitored

- **Movie Monitoring** (Radarr):
  - `DELETE_IF_UNMONITORED_MOVIE=true` → removes if movie is unmonitored

- **Orphan Cleanup**:
  - `DELETE_IF_ONLY_ON_EMULERR=true` → removes downloads not present in *Arr anymore

## 🔧 Advanced Usage

### Aggressive Cleanup Configuration

For maximum automation and cleanup:

```yaml
environment:
  - CHECK_INTERVAL=5                      # Check every 5 minutes
  - STALL_CHECKS=15                       # Mark stalled after 15 checks (75 min)
  - STALL_DAYS=15                         # Remove old incomplete downloads
  - DELETE_IF_UNMONITORED_SERIE=true      # Clean unmonitored content
  - DELETE_IF_UNMONITORED_SEASON=true
  - DELETE_IF_UNMONITORED_EPISODE=true
  - DELETE_IF_UNMONITORED_MOVIE=true
  - DELETE_IF_ONLY_ON_EMULERR=true        # Clean orphaned downloads
```

### Conservative Configuration

For careful monitoring with manual intervention:

```yaml
environment:
  - CHECK_INTERVAL=30                     # Check every 30 minutes
  - STALL_CHECKS=48                       # 24 hours before marking stalled
  - STALL_DAYS=30                         # 30 days grace period
  - DELETE_IF_UNMONITORED_EPISODE=false   # Keep unmonitored content
  - DELETE_IF_UNMONITORED_MOVIE=false
  - DELETE_IF_ONLY_ON_EMULERR=false       # Keep orphaned downloads
  - DRY_RUN=true                          # Test mode enabled
```

### Testing Configuration (Dry Run)

Test your setup without actual deletions:

```yaml
environment:
  - DRY_RUN=true
  - LOG_LEVEL=debug
  - LOG_TO_FILE=/logs/test.log
volumes:
  - ./logs:/logs
```

### File Logging Setup

Enable persistent logging:

```yaml
environment:
  - LOG_TO_FILE=/logs/emulerr_stalled_checker.log
  - LOG_LEVEL=info
volumes:
  - ./logs:/logs
```

### Sonarr-Only Configuration

```yaml
environment:
  - SONARR_HOST=http://10.0.0.100:8989
  - SONARR_API_KEY=your_sonarr_api_key
  - SONARR_CATEGORY=tv-sonarr-eMulerr
  # Radarr variables not needed
```

### Radarr-Only Configuration

```yaml
environment:
  - RADARR_HOST=http://10.0.0.100:7878
  - RADARR_API_KEY=your_radarr_api_key
  - RADARR_CATEGORY=radarr-eMulerr
  # Sonarr variables not needed
```

## 🔔 Pushover Notifications

To receive real-time notifications when downloads are removed:

1. **Create Pushover Account**: Sign up at [pushover.net](https://pushover.net)
2. **Get User Key**: Found in your Pushover dashboard
3. **Create Application**: Register a new application to get an API token
4. **Configure**:

```yaml
environment:
  - PUSHOVER_USER_KEY=your_user_key_here
  - PUSHOVER_APP_TOKEN=your_app_token_here
```

**Notification includes:**
- Download name
- Reason for removal (stalled/unmonitored/orphaned)
- Associated *Arr application
- Timestamp

## 🐛 Troubleshooting

### Common Issues

#### Script doesn't remove any downloads

**Possible causes:**
- `DRY_RUN=true` is enabled (check logs for "DRY RUN" messages)
- `STALL_CHECKS` threshold not reached yet
- Recent downloads within `RECENT_DOWNLOAD_GRACE_PERIOD`
- Downloads are making progress

**Solution:**
```bash
# Check logs
docker logs -f emulerr-stalled-checker

# Enable debug logging
environment:
  - LOG_LEVEL=debug
```

#### Cannot connect to eMulerr/Sonarr/Radarr

**Solution:**
```bash
# Verify URLs are reachable from container
docker exec emulerr-stalled-checker wget -O- http://your-emulerr:3000

# Check if services are on same Docker network
docker network inspect bridge

# Use host IPs instead of localhost
- EMULERR_HOST=http://10.0.0.100:3000  # ✅
# not
- EMULERR_HOST=http://localhost:3000    # ❌
```

#### API Key errors

**Solution:**
- Verify API keys in Sonarr/Radarr: Settings → General → Security → API Key
- Ensure no extra spaces in docker-compose.yml
- Test API manually:
```bash
curl -H "X-Api-Key: YOUR_KEY" http://your-sonarr:8989/api/v3/system/status
```

#### Downloads removed but not re-searched

**Possible cause:** Category mismatch

**Solution:**
- Verify eMulerr categories in Sonarr/Radarr match configuration:
  - Sonarr → Settings → Download Clients → eMulerr → Category
  - Should match `SONARR_CATEGORY` value exactly (case-sensitive)

#### Healthcheck failing

**Solution:**
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-check-certificate", "--spider", "http://your-emulerr-host:3000"]
  interval: 2m
  timeout: 30s
  retries: 5
```

### Logs

**View logs:**
```bash
docker logs emulerr-stalled-checker
```

**Follow logs in real-time:**
```bash
docker logs -f emulerr-stalled-checker
```

**Enable debug logging:**
```yaml
environment:
  - LOG_LEVEL=debug
```

**Save logs to file:**
```yaml
environment:
  - LOG_TO_FILE=/logs/emulerr_checker.log
volumes:
  - ./logs:/logs
```

## 🛠️ Building from Source

If you prefer to build the Docker image yourself:

```bash
git clone https://github.com/Jorman/Scripts.git
cd Scripts/eMulerrStalledChecker
docker build -t emulerr-stalled-checker .
```

Then use your local image:
```yaml
services:
  emulerr-stalled-checker:
    image: emulerr-stalled-checker  # local image
    # ... rest of config
```

**Note:** The pre-built image `chryses/emulerr-stalled-checker` on Docker Hub is automatically built and tested via GitHub Actions.

## 📦 Docker Hub

**Official Image:** [`chryses/emulerr-stalled-checker`](https://hub.docker.com/r/chryses/emulerr-stalled-checker)

### Available Tags
- `latest` - Latest stable release (recommended)

### Supported Architectures
- ✅ `linux/amd64` (x86_64)
- ✅ `linux/arm64` (ARM 64-bit)

### Auto-Build
Images are automatically built on every push to the `master` branch via GitHub Actions.

## 🔗 Related Projects

- **[eMulerr](https://github.com/isc30/eMulerr)** - ed2k/Kad integration for Sonarr/Radarr
- **[Sonarr](https://github.com/Sonarr/Sonarr)** - Smart PVR for TV shows
- **[Radarr](https://github.com/Radarr/Radarr)** - Movie collection manager
- **[Pushover](https://pushover.net)** - Real-time notifications

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/Jorman/Scripts/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Jorman/Scripts/discussions)
- 🐳 **Docker Hub:** [chryses/emulerr-stalled-checker](https://hub.docker.com/r/chryses/emulerr-stalled-checker)

## ⭐ Show Your Support

If you find this project useful, please consider:
- ⭐ Starring the repository on GitHub
- 🐳 Pulling the Docker image
- 📢 Sharing with others in the homelab/selfhosted community

---

**Made with ❤️ for the Arr community**
