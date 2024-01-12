# TODO
Make some good expalation on how to use these scripts

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
	~~`custom_save_path` -> the script have to save a file with tracker list, normally that file is saved in user home path, however if the home directory is not writable (not exist or whatever), the script fail. So if the home of the user that run the script is not reachable, this option is the right one. This option can be useful when used in combination with containers, so if the HOME variable is not set, specify the path with this option.~~
	~~`private_tracker_list` is a comma-separated list of your "private" trackers.
	Actually you've to manually set your private trackers list because is not yet possible get the status from the torrent automatically, maybe one day it will be possible.~~ -> No more needed, the script will check if the torrent is private or not automatically
	`live_trackers_list_url`, is the url where the trackers list are taken, is an automatic list, you can specify more than one url, just follow the example in the file.
* Configuration is now donw, you've to configure Radarr and/or Sonarr, personally I:
1. Create a custom script (settings -> connect -> add notification -> Custom Script)
2. The name is not important, I use Add Transmission Trackers, you can use any name you like
3. Set "On Grab"
4. Inside Path field, point to the `AddqBittorrentTrackers.sh` script
5. Save the custom script

Now, when Radarr and/or Sonarr will grab a new torrent, the script will be triggered and a custom tracker list will be added to the torrent, automatically, if the torrent is not from a private tracker.
Is also possible to run the script manually, simply run the script `./AddqBittorrentTrackers.sh` and see all the possible options.
I inserted a new way to call the script, with many options to inject trackers inside torrents.
One note abount configuration, if you want to use it manually, before use it configure username, passowrd, host and port inside the file. Otherwise I would have to insert four new options to be called every time manually, or "complicate" it by inserting possibility to have a configuration file to be saved somewhere. If it is necessary I will do it but for now I think it is easier to keep only the necessary options.
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# AddTransmissionTrackers.sh
The purpose of this script is to inject trakers inside Transmission torrent, this can be used manually and can also works with Radarr/Sonarr in an automatic way.

~~This script use transmission-remote, normally this is already installed if you use transmission.~~
Transmission-remote is not needed anymore, I switch all the commands directly to /rpc so this's the very first release.
I also included the possibility to call the script and specify name and/or id where add trackers

* First make sure your Radarr/Sonarr user can execute the script with some like this:
	`chown USER:USER AddTransmissionTrackers.sh` then ensure that it is executable
	`chmod +x AddTransmissionTrackers.sh`
* Modify the `########## CONFIGURATIONS ##########` section:
	`transmission_username`, `transmission_password`, `transmission_host` and `transmission_port` are all Transmission related.
	~~`private_tracker_list` is a comma-separated list of your "private" trackers.
	Actually you've to manually set your private trackers list because is not yet possible get the status from the torrent automatically, maybe one day it will be possible.~~ -> No more needed, the script will check if the torrent is private or not automatically
	`live_trackers_list_url`, is the url where the trackers list are taken, is an automatic list, you can specify more than one url, just follow the example in the file.
* Now the configuration is done, you've to configure Radarr and/or Sonarr, personally I:
1. Create a custom script (settings -> connect -> add notification -> Custom Script)
2. The name is not important, I use Add Transmission Trackers, you can use any name you like
3. Set "On Grab"
4. Inside Path field, point to the `AddTransmissionTrackers.sh` script
5. Save the custom script

Now, when Radarr and/or Sonarr will grab a new torrent, the script will be triggered and a custom tracker list will be added to the torrent, automatically, if the torrent is not from a private tracker.
Is also possible to run the script manually, simply run the script `./AddTransmissionTrackers.sh` and see all the possible options.
I inserted a new way to call the script, with many options to inject trackers inside torrents.
One note abount configuration, if you want to use it manually, before use it configure username, passowrd, host and port inside the file. Otherwise I would have to insert four new options to be called every time manually, or "complicate" it by inserting possibility to have a configuration file to be saved somewhere. If it is necessary I will do it but for now I think it is easier to keep only the necessary options.
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
# qBittorrentHardlinksChecker.sh
The idea of this script is very simple, in my case it helps, judge for yourself if it helps you. For managing the seed times of automatic downloads from the various `*Arr`, I normally use [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents), a very complete and very useful script that allows me to pick and choose category by category, tracker by tracker the various torrent removal settings, this is because the space available is not infinite. So I am forced to do regular cleanup among the various downloads, and I always respect the rules of the various private trackers! But let's come to the idea:
Very simple, if in the automatic downloading programs, `*Arr`, the configuration is set to generate hardlinks then it means that until I have deleted both the file from the torrent client and the linked file managed automatically, the space occupied on the disk will be the same. This means that as long as I haven't watched and deleted that movie, etc., I could safely keep the share the downloaded file, because it no longer takes up disk space, being a hardlink. So with this script, for the categories you set, you can check each download and if there is one or more hardlinks the file will not be deleted from qBittorrent, if on the other hand the file has only one hardlink then the script will consider whether or not to delete the file by checking the minimum seed time that has been set. 
Here is an idea of usage: I for example for only downloads that end up in the automatic categories, e.g. `movie` for Radarr (or whatever your category is) rather than `tv_show` for Sonarr (or whatever your category is), etc., before running [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents) (appropriately configured) I run this script and by doing so I make sure that any "duplicates" are not deleted and remain in seed, helping me with the share ratio and minimum seed time

How to use:
* First make sure your Radarr/Sonarr user can execute the script with some like this:
	`chown USER:GROUP qBittorrentHardlinksChecker.sh` then be sure that is executable
	`chmod +x AddqBittorrentTrackers.sh`
	where `USER:GROUP` is the user and group of Radarr/Sonarr
	Note: not being a script that is called from `*Arr` is not strictly necessary to change user and group, just make sure that the script however can be executed by the user concerned
* Modify the `########## CONFIGURATIONS ##########` section:
	`qbt_username` -> username to access to qBittorrent Web UI
	`qbt_password` -> username to access to qBittorrent Web UI
	Note that if the script run on the same device that hold qBittorrent, you can set `Bypass authentication for clients on localhost` so when the script run username and password are not required
	`qbt_host` -> if the script is on the same device of qBittorrent `http://localhost`, otherwise, you've to set to the remote device
	`qbt_port` -> is the Web UI port
	`category_list` -> is the list of categories where the script performs the check
	`min_seeding_time` -> is the minimum seed time expressed in seconds
	`only_private` -> if true, the script will only check the torrents that is from private tracker, in this way you can set [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents) in order to work only the ramaining trackers. This help the share ration and helps you to find and remove torrent from public tarckers with your own rules
	`private_torrents_check_orphan` -> if true, only for private tracker, check the torrent and if is not registered will be deleted
	`public_torrent_check_bad_trackers` -> if true, only for public torrent, check the trackers and the bad one will be eliminated, not the torrent only the trackers. Be patient can be a "slow" function during the deleting phase
*	I recommend you to putthis script under cron or create a timer for systemd, I personally use it via timer so I can run right after [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents)
