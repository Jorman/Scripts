# qBittorrent Tracker Updater
# PowerShell Script

# Configuration
$qbt_host = "http://localhost"
$qbt_port = "8080"
$qbt_username = "admin"
$qbt_password = "adminadmin"

$ignore_private = $false
$clean_existing_trackers = $false

$live_trackers_list_urls = @(
    "https://newtrackon.com/api/stable",
    "https://trackerslist.com/best.txt",
    "https://trackerslist.com/http.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
)

# Functions
function Get-QBittorrentCookie {
    $body = @{
        username = $qbt_username
        password = $qbt_password
    }
    $response = Invoke-RestMethod -Uri "${qbt_host}:${qbt_port}/api/v2/auth/login" -Method Post -Body $body -SessionVariable script:qbt_session
    return $script:qbt_session
}

function Get-TorrentList {
    $response = Invoke-RestMethod -Uri "${qbt_host}:${qbt_port}/api/v2/torrents/info" -WebSession $script:qbt_session
    return $response
}

function Get-TrackersList {
    $trackers = @()
    foreach ($url in $live_trackers_list_urls) {
        $trackers += (Invoke-RestMethod -Uri $url -Method Get)
    }
    return ($trackers | Sort-Object -Unique) -join [Environment]::NewLine
}

function Remove-Trackers {
    param (
        [string]$hash,
        [string]$urls
    )
    $body = @{
        hash = $hash
        urls = $urls
    }
    Invoke-RestMethod -Uri "${qbt_host}:${qbt_port}/api/v2/torrents/removeTrackers" -Method Post -Body $body -WebSession $script:qbt_session
}

function Add-Trackers {
    param (
        [string]$hash,
        [string]$urls
    )
    $body = @{
        hash = $hash
        urls = $urls
    }
    Invoke-RestMethod -Uri "${qbt_host}:${qbt_port}/api/v2/torrents/addTrackers" -Method Post -Body $body -WebSession $script:qbt_session
}

# Main script
Get-QBittorrentCookie

$torrentList = Get-TorrentList

foreach ($torrent in $torrentList) {
    Write-Host "Processing torrent: $($torrent.name)"
    
    if (-not $ignore_private) {
        $torrentProperties = Invoke-RestMethod -Uri "${qbt_host}:${qbt_port}/api/v2/torrents/properties?hash=$($torrent.hash)" -WebSession $script:qbt_session
        if ($torrentProperties.is_private) {
            Write-Host "Skipping private torrent: $($torrent.name)"
            continue
        }
    }

    $existingTrackers = Invoke-RestMethod -Uri "${qbt_host}:${qbt_port}/api/v2/torrents/trackers?hash=$($torrent.hash)" -WebSession $script:qbt_session
    $existingTrackerUrls = $existingTrackers | Where-Object { $_.tier -ne 0 } | ForEach-Object { $_.url }

    if ($clean_existing_trackers) {
        Remove-Trackers -hash $torrent.hash -urls ($existingTrackerUrls -join "|")
    }

    $newTrackers = Get-TrackersList
    $trackersToAdd = if ($clean_existing_trackers) { $newTrackers } else { ($newTrackers + $existingTrackerUrls | Sort-Object -Unique) -join [Environment]::NewLine }

    Add-Trackers -hash $torrent.hash -urls $trackersToAdd

    Write-Host "Updated trackers for: $($torrent.name)"
}

Write-Host "Tracker update process completed."