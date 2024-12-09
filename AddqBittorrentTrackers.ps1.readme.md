# AddqBittorrentTrackers PowerShell Version

A Windows PowerShell adaptation of the original AddqBittorrentTrackers.sh script, designed for Windows users who prefer a native solution without requiring WSL or Unix-like environments.

## Requirements

- Windows PowerShell 5.1 or newer
- qBittorrent with Web UI enabled
- Network access to qBittorrent's Web UI

## Configuration

Edit these variables in the script before running:

```powershell
$qbt_host = "http://localhost"
$qbt_port = "8080"
$qbt_username = "admin"
$qbt_password = "adminadmin"

$ignore_private = $false
$clean_existing_trackers = $false
```

## Usage

1. Configure qBittorrent Web UI credentials in the script
2. Open PowerShell and navigate to the script directory
3. Run the script:
```powershell
.\AddqBittorrentTrackers.ps1
```

## Features

- Updates trackers for all non-private torrents in qBittorrent
- Optional cleaning of existing trackers (`$clean_existing_trackers = $true`)
- Configurable tracker sources via `$live_trackers_list_urls`
- Respects private torrents by default (can be overridden with `$ignore_private = $true`)
- Uses qBittorrent's Web API for all operations