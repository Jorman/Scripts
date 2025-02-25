# AddqBittorrentTrackers.sh

The purpose of this script is to inject trackers into your **qBittorrent downloads**.

It may be executed manually or automatically with Radarr/Sonarr.

This script works with the qBittorrent v4.1+ API. It may work with lower versions, but must be checked. Let me know if you use an earlier version and it works, so I can expand the version compatability.

To use this script you'll need:
* [jq](https://stedolan.github.io/jq/). Check if `jq` is available for your distro with `sudo apt install jq` (or the appropriate package management tool)
* Curl. Install it with `sudo apt install curl`

* First make sure your Radarr/Sonarr user can execute the script with a process similar to this:
   * `chown USER:GROUP AddqBittorrentTrackers.sh` where `USER:GROUP` is the same user and group as qBittorrent.
   * Then be sure it is executable with: `chmod +x AddqBittorrentTrackers.sh` 
  
* Modify the scripts `########## CONFIGURATIONS ##########` section:
   * `qbt_username` -> username to access to qBittorrent Web UI.
   * `qbt_password` -> password to access to qBittorrent Web UI. **Password MUST BE url encoded**, otherwise any special characters will break the curl request.
   *  Note that if the script runs on the same device that runs qBittorrent, you can set `Bypass authentication for clients on localhost`. With this option set and when the script runs, the username and password are not required.
   * `qbt_host` -> if the script is on the same device as qBittorrent `http://localhost`, otherwise, set this to the remote device.
   * `qbt_port` -> is the Web UI port.
   * `live_trackers_list_url`, is the url from where the trackers list is obtained. These lists are automatically generated. You can specify more than one url, just follow the example in the file.
   * The script will automatically check if the torrent is private or public.

Configuration is now complete. 


If you are a **Radarr and/or Sonarr user**, personally I:
1. Create a custom script (settings -> connect -> add notification -> Custom Script).
2. The name is not important. I use Add qBitTorrent Trackers, you can use any name you like.
3. Set "On Grab".
4. Inside Path field, point to the `AddqBittorrentTrackers.sh` script.
5. Save the custom script.

Now, when _Radarr and/or Sonarr_ grabs a new torrent, the script will be automatically triggered and a custom tracker list will be added to the torrent. This is true only if the torrent is _not_ from a private tracker.

To run the script manually, simply run `./AddqBittorrentTrackers.sh`. All the possible options will be shown. When calling the script, there are many options to add trackers to torrents.

One note about configuration, if you want to use it manually, you must configure the username, password, host and port within the file. This is for simplicity. Otherwise I would have to insert four new options to be called every time manually, or "complicate" the script by checking for the possibility of a configuration file to be saved somewhere. If it is necessary I will do it, but for now I think it is easier to keep the necessary options hard coded.


