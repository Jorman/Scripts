# TODO
Make some good expalation on how to use these scripts!

# AddqBittorrentTrackers.sh
The purpose of this script is to inject trakers inside qBittorrent torrent, this can be used manually and can also works with Radarr/Sonarr in an automatic way.
Actually this works with qBittorrent v4.1+ because of API. Maybe works with lower version, must be checked. Let me know if works, so I can expand the version compability.

To use this script you'll need:
* ~~[qbittorrent-cli](https://github.com/fedarovich/qbittorrent-cli)~~ -> No more needed, now with curl is really fast!!!
* [jq](https://stedolan.github.io/jq/)
  Check if is available for your distro with `sudo apt install jq`
* Curl
  Install it with `sudo apt install curl`

* First make sure your Radarr/Sonarr user can execute the script with some like this:
	`chown USER:GROUP AddqBittorrentTrackers.sh` then be sure that is executable
	`chmod +x AddqBittorrentTrackers.sh`
	where `USER:GROUP` is the user and group of Radarr/Sonarr
* Modify the `########## CONFIGURATIONS ##########` section:
	`qbt_username` -> username to access to qBittorrent Web UI
	`qbt_password` -> username to access to qBittorrent Web UI
	Note that if the script run on the same device that hold qBittorrent, you can set `Bypass authentication for clients on localhost` so when the script run username and password are not required
	`qbt_host` -> if the script is on the same device of qBittorrent `http://localhost`, otherwise, you've to set to the remote device
	`qbt_port` -> is the Web UI port
	`custom_save_path` -> the script have to save a file with tracker list, normally that file is saved in user home path, however if the home directory is not writable (not exist or whatever), the script fail. So if the home of the user that run the script is not reachable, this option is the right one. This option can be useful when used in combination with containers, so if the HOME variable is not set, specify the path with this option.
	`private_tracker_list` is a comma-separated list of your "private" trackers.
	Actually you've to manually set your private trackers list because is not yet possible get the status from the torrent automatically, maybe one day it will be possible.
	`live_trackers_list_url`, is the url where the trackers list are taken, is an automatic list, you can specif
 more than one url, just follow the example in the file.
* Now the configuration is done, you've to configure Radarr and/or Sonarr, personally I:
1. Create a custom script (settings -> connect -> add notification -> Custom Script)
2. The name is not important, I use Add Transmission Trackers, you can use any name you like
3. Set "On Grab"
4. Inside Path field, point to the `AddqBittorrentTrackers.sh` script
5. Save the custom script

Now, when Radarr and/or Sonarr will grab a new torrent, the script will be triggered and a custom tracker list will be added to the torrent, automatically, if the torrent is not from a private tracker.
Is also possible to run the script manually, simply run the script `./AddqBittorrentTrackers.sh` and see all the possible options.
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# AddTransmissionTrackers.sh
The purpose of this script is to inject trakers inside Transmission torrent, this can be used manually and can also works with Radarr/Sonarr in an automatic way.

This script use transmission-remote, normally this is already installed if you use transmission.

* First make sure your Radarr/Sonarr user can execute the script with some like this:
	`chown USER:USER AddTransmissionTrackers.sh` then be sue that is executable
	`chmod +x AddTransmissionTrackers.sh`
* Modify the `########## CONFIGURATIONS ##########` section:
	`t_username`, `t_password`, `t_host` and `t_port` are all Transmission related.
	`private_tracker_list` is a comma-separated list of your "private" trackers.
	Actually you've to manually set your private trackers list because is not yet possible get the status from the torrent automatically, maybe one day this will be possible.
	`live_trackers_list_url`, is the url where the trackers list are taken, is an automatic list.
* Now the configuration is done, you've to configure Radarr and/or Sonarr, personally I:
1. Create a custom script (settings -> connect -> add notification -> Custom Script)
2. The name is not important, I use Add Transmission Trackers, you can use any name you like
3. Set "On Grab"
4. Inside Path field, point to the `AddTransmissionTrackers.sh` script
5. Save the custom script

Now, when Radarr and/or Sonarr will grab a new torrent, the script will be triggered and a custom tracker list will be added to the torrent, automatically, if the torrent is not from a private tracker.
Is also possible to run the script manually, simply run the script `./AddTransmissionTrackers.sh` and see all the possible options.
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# TransmissionRemoveCompleteTorrent.sh
The purpose of this script is to remove the complete torrent from Transmission, but only the torrent added by Radarr/Sonarr. The best way is to use it is to cronize it.

This script use transmission-remote, normally this is already installed if you use transmission.

* First make sure your Radarr/Sonarr user can execute the script with some like this:
	`chown USER:USER TransmissionRemoveCompleteTorrent.sh` then be sue that is executable
	`chmod +x TransmissionRemoveCompleteTorrent.sh`
* Modify the `########## CONFIGURATIONS ##########` section:
	`t_username`, `t_password`, `t_host` and `t_port` are all Transmission related.
	`t_log` is to enable the logfile, if 1 the logfile will be write on `t_log_path`.
	Now the most important setting `automatic_folder`, is the folder that contain all the **automatic download**
	I use this folder structure for automatic download that came from Radarr/Sonarr:
	- download
	  - automatic
	    - movie
	    - tv_show
	So for this configuration example I've to set `automatic` for `automatic_folder` option.
	`max_days_seed` if the maximum seed time
	`remove_normal` pay attention if you set this to true, because this enable a kind of **force** option that also check all non automatic download
* Like I said, you can cronize the script, sith some like this
	`30 01 * * * /PATHOFTHESCRIPT/TransmissionRemoveCompleteTorrent.sh >/dev/null 2>&1` this execute the script at 01:30 every day.
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
