# TODO
Make some good expalation on how to use these scripts

# AddqBittorrentTrackers.sh
In order to use this script you'll need:
[qbittorrent-cli](https://github.com/fedarovich/qbittorrent-cli)

* First make sure your Radarr/Sonarr user can execute the script with some like this:
	`chown USER:USER AddqBittorrentTrackers.sh` then be sue that is executable
	`chmod +x AddqBittorrentTrackers.sh`
* Modify the `########## CONFIGURATIONS ##########` section:
	`username`, `password`, `host` and `port` are all qBittorrent related.
	`private_tracker_list` is a comma-separated list of your "private" trackers.
	Actually you've to manually set your private trackers list because is not yet possible get the status from the torrent automatically, maybe one day "qbt" will make it for you.
	`live_trackers_list_url`, is the url where the trackers list are taken, is an automatic list.
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