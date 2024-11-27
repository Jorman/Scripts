# qBittorrent Tracker Updater PowerShell Script

This PowerShell script is a Windows rewrite of the [AddqBittorrentTrackers.sh](https://github.com/Jorman/Scripts/blob/master/AddqBittorrentTrackers.sh) bash script by [Jorman](https://github.com/Jorman). It automatically updates trackers for torrents in qBittorrent using the qBittorrent Web API, enhancing the connectivity of your torrents by adding new trackers from popular tracker lists.
## Original Script

The original bash script can be found here: https://github.com/Jorman/Scripts/blob/master/AddqBittorrentTrackers.sh

This PowerShell version aims to provide similar functionality for Windows users without the need for WSL or a Unix-like environment.
## Features

    * Connects to qBittorrent's Web API

    * Retrieves a list of all torrents

    * Optionally skips private torrents

    * Fetches new trackers from multiple predefined tracker lists

    * Optionally removes existing trackers before adding new ones

    * Adds new trackers to each torrent

    * Provides console output for monitoring the update process


## Configuration

At the top of the script, you can configure the following settings:

    * qBittorrent Web UI host and port

    * qBittorrent Web UI username and password

    * Option to ignore private torrents

    * Option to clean existing trackers before adding new ones

    * URLs of tracker lists to fetch new trackers from


## Requirements

    * Windows PowerShell 5.1 or later

    * qBittorrent with Web UI enabled and accessible


## Usage

    1. Save the script as `QBittorrentTrackerUpdater.ps1`

    2. Modify the configuration variables at the top of the script to match your qBittorrent setup

    3. Open PowerShell and navigate to the directory containing the script

    4. Run the script with: `.\QBittorrentTrackerUpdater.ps1`


Note: You may need to set the PowerShell execution policy to allow running scripts. Run PowerShell as an administrator and execute:

```powershell
Set-ExecutionPolicy RemoteSigned
```

## Differences from the Original Script

While this script aims to provide similar functionality, there are some differences:

    * Written in PowerShell instead of bash

    * Simplified command-line options

    * May have slight differences in error handling and output formatting


For the full feature set of the original script, please refer to the bash version linked above.
## Disclaimer

This script interacts with your qBittorrent client and modifies torrent trackers. Use at your own risk. Always ensure you have backups of your torrent data before running scripts that modify your torrents.
## Contributing

Feel free to fork this gist and submit pull requests for any improvements or bug fixes. If you need features from the original bash script that are not implemented here, consider contributing to add them.
## Acknowledgments

Special thanks to [Jorman](https://github.com/Jorman) for the original bash script that inspired this PowerShell version.

