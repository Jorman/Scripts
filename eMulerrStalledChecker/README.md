# eMulerr Stalled Checker
![Docker Pulls](https://img.shields.io/docker/pulls/chryses/emulerr-stalled-checker)
![Docker Image Size](https://img.shields.io/docker/image-size/chryses/emulerr-stalled-checker)
![GitHub](https://img.shields.io/github/license/Jorman/Scripts)

> Automated monitoring and cleanup tool for stalled ed2k/Kad downloads in Sonarr/Radarr via eMulerr

---

## Overview

eMulerr Stalled Checker is a Docker-based monitoring service that automatically detects and removes stalled or source-less downloads from [eMulerr](https://github.com/isc30/eMulerr), keeping your [Sonarr](https://github.com/Sonarr/Sonarr) and [Radarr](https://github.com/Radarr/Radarr) download queues clean and efficient.

When eMulerr downloads (ed2k/Kad network) get stuck without sources or stall indefinitely, this tool identifies them through configurable health checks, removes them from eMulerr, marks them as failed in the respective *Arr application, and automatically triggers a new search. This ensures your media automation keeps running smoothly without manual intervention.

The script intelligently handles downloads by category, respects monitoring status in Sonarr/Radarr, and can clean up orphaned downloads that exist only in eMulerr but not in your *Arr instances anymore.

---

## ✨ Features

- 🧠 Smart Stall Detection — Configurable checks before marking downloads as stalled
- 🧹 Automatic Cleanup — Removes stalled downloads and triggers new searches
- 🗂️ Category-Based Management — Handles Sonarr and Radarr downloads separately via categories
- 🧭 Orphan Detection — Removes downloads that exist only in eMulerr (optional)
- 👀 Monitoring-Aware — Respects series/season/episode/movie monitoring status
- ⏰ Grace Period — Configurable waiting time for recent downloads
- 🔔 Apprise Notifications — Multi-service alerts (Telegram, Discord, Email, Slack, Pushover via Apprise, etc.). Pushover remains backward-compatible, but switching to Apprise is highly recommended
- 🐳 Docker Native — Easy deployment and management
- 🧪 Dry Run Mode — Test configuration without actual changes
- 📜 Detailed Logging — Console and optional file logging with configurable levels

---

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Running instances of:
  - [eMulerr](https://github.com/isc30/eMulerr)
  - [Sonarr](https://github.com/Sonarr/Sonarr) and/or [Radarr](https://github.com/Radarr/Radarr)
- eMulerr configured as a download client in Sonarr/Radarr with specific categories

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
  -e RECENT_DOWNLOAD_GRACE_PERIOD=30 \
  -e DELETE_IF_UNMONITORED_SERIE=false \
  -e DELETE_IF_UNMONITORED_SEASON=false \
  -e DELETE_IF_UNMONITORED_EPISODE=true \
  -e DELETE_IF_UNMONITORED_MOVIE=true \
  -e DELETE_IF_ONLY_ON_EMULERR=false \
  -e DOWNLOAD_CLIENT=emulerr \
  -e RADARR_HOST=http://your-radarr:7878 \
  -e RADARR_API_KEY=your_radarr_api_key \
  -e RADARR_CATEGORY=radarr-eMulerr \
  -e SONARR_HOST=http://your-sonarr:8989 \
  -e SONARR_API_KEY=your_sonarr_api_key \
  -e SONARR_CATEGORY=tv-sonarr-eMulerr \
  -e APPRISE_URLS="discord://webhook_id/webhook_token tgram://bot_token/chat_id" \
  -e LOG_LEVEL=info \
  -e LOG_TO_FILE=/logs \
  -e DRY_RUN=false \
  -v "$(pwd)/logs:/logs" \
  chryses/emulerr-stalled-checker:latest
```

Notes:
- EMULERR_HOST, RADARR_HOST and SONARR_HOST must start with http:// or https://.
- LOG_TO_FILE expects a directory path; the file emulerr_stalled_checker.log will be created inside that directory.

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
      # 🔔 Notifications via Apprise (recommended). Multiple URLs separated by space or comma.
      # Examples:
      # - Pushover (via Apprise): pover://user_key@app_token
      # - Telegram: tgram://bot_token/chat_id
      # - Discord:  discord://webhook_id/webhook_token
      # - Multiple: pover://key@token discord://id/token
      - APPRISE_URLS=pover://your_user_key@your_app_token
      # 📲 Legacy Pushover (optional; auto-converted to Apprise if both are set)
      # - PUSHOVER_USER_KEY=your_pushover_user_key
      # - PUSHOVER_APP_TOKEN=your_pushover_app_token
      - LOG_LEVEL=info
      # 🪵 LOG_TO_FILE is a DIRECTORY; the file will be created as emulerr_stalled_checker.log
      - LOG_TO_FILE=/logs
      - DRY_RUN=false
      - DOWNLOAD_CLIENT=emulerr
      - RADARR_HOST=http://10.0.0.100:7878
      - RADARR_API_KEY=your_radarr_api_key
      - RADARR_CATEGORY=radarr-eMulerr
      - SONARR_HOST=http://10.0.0.100:8989
      - SONARR_API_KEY=your_sonarr_api_key
      - SONARR_CATEGORY=tv-sonarr-eMulerr
    volumes:
      - ./logs:/logs
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://10.0.0.100:3000"]
      interval: 1m
      timeout: 10s
      retries: 3
```

---

## ⚙️ Configuration

### Environment Variables

#### Core Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `EMULERR_HOST` | eMulerr base URL (e.g., `http://10.0.0.100:3000`). Must start with `http://` or `https://` | — | ✅ Yes |
| `CHECK_INTERVAL` | Minutes between stall checks | — | ✅ Yes |
| `STALL_CHECKS` | Number of consecutive checks before marking as stalled | — | ✅ Yes |
| `STALL_DAYS` | Days before a never-completed download is considered stalled | — | ✅ Yes |
| `RECENT_DOWNLOAD_GRACE_PERIOD` | Minutes to wait before checking recent downloads | `30` | ✅ Yes |

#### *Arr Integration (at least one required)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DOWNLOAD_CLIENT` | Download client name configured in Sonarr/Radarr | — | ✅ Yes |
| `RADARR_HOST` | Radarr base URL | `None` | ⚠️ Conditional |
| `RADARR_API_KEY` | Radarr API key | `None` | ⚠️ Conditional |
| `RADARR_CATEGORY` | eMulerr category for Radarr downloads | `None` | ⚠️ Conditional |
| `SONARR_HOST` | Sonarr base URL | `None` | ⚠️ Conditional |
| `SONARR_API_KEY` | Sonarr API key | `None` | ⚠️ Conditional |
| `SONARR_CATEGORY` | eMulerr category for Sonarr downloads | `None` | ⚠️ Conditional |

> You must configure at least one *Arr service (Radarr or Sonarr).  
> If you use both, configure both sets of variables.

#### Monitoring & Cleanup Rules

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DELETE_IF_UNMONITORED_SERIE` | Remove downloads for unmonitored series (Sonarr) | `false` | ❌ No |
| `DELETE_IF_UNMONITORED_SEASON` | Remove downloads for unmonitored seasons (Sonarr) | `false` | ❌ No |
| `DELETE_IF_UNMONITORED_EPISODE` | Remove downloads for unmonitored episodes (Sonarr) | `false` | ❌ No |
| `DELETE_IF_UNMONITORED_MOVIE` | Remove downloads for unmonitored movies (Radarr) | `false` | ❌ No |
| `DELETE_IF_ONLY_ON_EMULERR` | Remove orphaned downloads (present only in eMulerr, not in *Arr) | `false` | ❌ No |

#### 🔔 Notifications

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APPRISE_URLS` | One or more Apprise URLs (space or comma separated), e.g., `pover://user@app` | `None` | ❌ No |
| `PUSHOVER_USER_KEY` | Legacy Pushover user key (auto-converted to Apprise if APP token is also set) | `None` | ❌ No |
| `PUSHOVER_APP_TOKEN` | Legacy Pushover app token (auto-converted to Apprise if USER key is also set) | `None` | ❌ No |

Recommendation: use `APPRISE_URLS` for maximum flexibility. If both `PUSHOVER_USER_KEY` and `PUSHOVER_APP_TOKEN` are set, the script auto-converts them to an Apprise URL transparently.

#### 🪵 Logging & Debug

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOG_LEVEL` | Logging level: `debug`, `info`, `warning`, `error`, `critical` | `info` | ❌ No |
| `LOG_TO_FILE` | Directory path where the log file will be created as `emulerr_stalled_checker.log` (requires volume) | `None` | ❌ No |
| `DRY_RUN` | Test mode — no actual deletions (`true`/`false`) | `false` | ❌ No |
| `TZ` | Timezone (e.g., `Europe/Rome`) | `UTC` | ❌ No |

---

## How It Works

### Download Monitoring Workflow

1. Periodic Checks — Every `CHECK_INTERVAL` minutes, the script queries eMulerr for all downloads
2. Category Filtering — Identifies downloads matching configured Sonarr/Radarr categories
3. Health Assessment — For each download:
   - Checks if it's stalled (no progress, no sources)
   - Verifies against `STALL_CHECKS` threshold
   - Applies `RECENT_DOWNLOAD_GRACE_PERIOD` for new downloads
   - Checks `STALL_DAYS` for long-running incomplete downloads
4. Monitoring Status — Queries Sonarr/Radarr to verify if content is still monitored
5. Orphan Detection — Identifies downloads that exist only in eMulerr (optional)
6. Action Execution — If criteria are met:
   - Removes the download from eMulerr
   - Marks it as failed in the corresponding *Arr application
   - Triggers an automatic search for an alternative source
   - Sends a notification via Apprise (if configured)

### Stall Detection Logic

A download is considered stalled when:
- No Progress: it hasn't made progress for `STALL_CHECKS` consecutive checks
- No Sources: it has no active sources/peers
- Time-Based: incomplete download older than `STALL_DAYS` days
- Grace Period: recent downloads (< `RECENT_DOWNLOAD_GRACE_PERIOD` minutes) are skipped

### Monitoring Checks

Before removing any download, the script verifies:
- Series/Season/Episode Monitoring (Sonarr):
  - `DELETE_IF_UNMONITORED_SERIE=true` → remove if the series is unmonitored
  - `DELETE_IF_UNMONITORED_SEASON=true` → remove if the season is unmonitored
  - `DELETE_IF_UNMONITORED_EPISODE=true` → remove if the episode is unmonitored
- Movie Monitoring (Radarr):
  - `DELETE_IF_UNMONITORED_MOVIE=true` → remove if the movie is unmonitored
- Orphan Cleanup:
  - `DELETE_IF_ONLY_ON_EMULERR=true` → remove downloads not present in *Arr anymore

---

## Advanced Usage

### Aggressive Cleanup Configuration

```yaml
environment:
  - CHECK_INTERVAL=5          # Check every 5 minutes
  - STALL_CHECKS=15           # Mark stalled after 15 checks (~75 min)
  - STALL_DAYS=15             # Remove old incomplete downloads
  - DELETE_IF_UNMONITORED_SERIE=true
  - DELETE_IF_UNMONITORED_SEASON=true
  - DELETE_IF_UNMONITORED_EPISODE=true
  - DELETE_IF_UNMONITORED_MOVIE=true
  - DELETE_IF_ONLY_ON_EMULERR=true
```

### Conservative Configuration

```yaml
environment:
  - CHECK_INTERVAL=30         # Check every 30 minutes
  - STALL_CHECKS=48           # ~24 hours before marking as stalled
  - STALL_DAYS=30             # 30 days grace period
  - DELETE_IF_UNMONITORED_EPISODE=false
  - DELETE_IF_UNMONITORED_MOVIE=false
  - DELETE_IF_ONLY_ON_EMULERR=false
  - DRY_RUN=true              # Test mode enabled
```

### Testing Configuration (Dry Run)

```yaml
environment:
  - DRY_RUN=true
  - LOG_LEVEL=debug
  - LOG_TO_FILE=/logs
volumes:
  - ./logs:/logs
```

### File Logging Setup

```yaml
environment:
  - LOG_TO_FILE=/logs          # directory mount
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

---

## 🔔 Apprise Notifications

eMulerr Stalled Checker uses [Apprise](https://github.com/caronc/apprise) to send notifications to many services (Telegram, Discord, Pushover, Slack, SMTP, etc.). Provide one or more URLs in Apprise format via `APPRISE_URLS`.

- Basic configuration:
  ```yaml
  environment:
    - APPRISE_URLS=discord://webhook_id/webhook_token
  ```
- Multiple services (space- or comma-separated):
  ```yaml
  environment:
    - APPRISE_URLS=discord://id/token,tgram://bot_token/chat_id
  ```
- Pushover via Apprise (recommended):
  ```yaml
  environment:
    - APPRISE_URLS=pover://your_user_key@your_app_token
  ```

Official documentation and URL formats: https://github.com/caronc/apprise/wiki

### Pushover Backward Compatibility

The script preserves compatibility with the legacy Pushover variables:
- `PUSHOVER_USER_KEY`
- `PUSHOVER_APP_TOKEN`

If both variables are set, they are automatically converted to the corresponding Apprise URL. However, it is highly recommended to switch to `APPRISE_URLS` for clearer configuration and wider provider support.

---

## Troubleshooting

### Common Issues

#### The tool doesn’t remove any downloads
Possible causes:
- `DRY_RUN=true` is enabled (check logs for “DRY RUN” messages)
- `STALL_CHECKS` threshold not reached yet
- The download is recent (`RECENT_DOWNLOAD_GRACE_PERIOD`)
- The download is making progress

Solution:
```bash
# Check logs
docker logs -f emulerr-stalled-checker
# Enable debug in docker-compose:
#   environment:
#     - LOG_LEVEL=debug
```

#### Cannot connect to eMulerr/Sonarr/Radarr

Solution:
```bash
# Check reachability from the container
docker exec emulerr-stalled-checker wget -O- http://your-emulerr:3000

# Make sure the services share a Docker network
docker network inspect bridge

# Use host IPs instead of localhost inside containers
# ✅ EMULERR_HOST=http://10.0.0.100:3000
# ❌ EMULERR_HOST=http://localhost:3000
```

#### API Key errors

Solution:
- Verify API keys in Sonarr/Radarr: Settings → General → Security → API Key
- Ensure there are no extra spaces in docker-compose.yml
- Manual API test:
```bash
curl -H "X-Api-Key: YOUR_KEY" http://your-sonarr:8989/api/v3/system/status
```

#### Downloads are removed but no new search is triggered

Possible cause: Category mismatch

Solution:
- Ensure eMulerr categories in Sonarr/Radarr match the configuration:
  - Sonarr → Settings → Download Clients → eMulerr → Category
  - Values must match `SONARR_CATEGORY`/`RADARR_CATEGORY` exactly (case-sensitive)

#### Healthcheck failing

Solution:
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-check-certificate", "--spider", "http://your-emulerr-host:3000"]
  interval: 2m
  timeout: 30s
  retries: 5
```

---

## 📜 Logs

View logs:
```bash
docker logs emulerr-stalled-checker
```

Follow in real time:
```bash
docker logs -f emulerr-stalled-checker
```

Enable debug:
```yaml
environment:
  - LOG_LEVEL=debug
```

Persist logs to file:
```yaml
environment:
  - LOG_TO_FILE=/logs
volumes:
  - ./logs:/logs
```

---

## 🛠️ Building from Source

```bash
git clone https://github.com/Jorman/Scripts.git
cd Scripts/eMulerrStalledChecker
docker build -t emulerr-stalled-checker .
```

Use the local image:
```yaml
services:
  emulerr-stalled-checker:
    image: emulerr-stalled-checker  # local image
    # ... rest of config
```

Note: The pre-built image `chryses/emulerr-stalled-checker` on Docker Hub is automatically built and tested via GitHub Actions.

---

## 🐳 Docker Hub

**Official Image:** [`chryses/emulerr-stalled-checker`](https://hub.docker.com/r/chryses/emulerr-stalled-checker)

### Available Tags
- `latest` — Latest stable release (recommended)

### Supported Architectures
- ✅ `linux/amd64` (x86_64)
- ✅ `linux/arm64` (ARM 64-bit)

### Auto-Build
Images are automatically built on every push to the `master` branch via GitHub Actions.

---

## 🔗 Related Projects

- 📡 **[eMulerr](https://github.com/isc30/eMulerr)** — ed2k/Kad integration for Sonarr/Radarr
- 📺 **[Sonarr](https://github.com/Sonarr/Sonarr)** — Smart PVR for TV shows
- 🎬 **[Radarr](https://github.com/Radarr/Radarr)** — Movie collection manager
- 🔔 **[Apprise](https://github.com/caronc/apprise)** — Multi-service notification library (recommended)
- 📲 **[Pushover](https://pushover.net)** — Legacy/optional notification provider

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🆘 Support

- 🐞 Bug Reports: [GitHub Issues](https://github.com/Jorman/Scripts/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/Jorman/Scripts/discussions)
- 🐳 Docker Hub: [chryses/emulerr-stalled-checker](https://hub.docker.com/r/chryses/emulerr-stalled-checker)

---

## ⭐ Show Your Support

If you find this project useful, please consider:
- ⭐ Starring the repository on GitHub
- 🐳 Pulling the Docker image
- 🔁 Sharing with others in the homelab/selfhosted community

---

Made with ❤️ for the *Arr community
