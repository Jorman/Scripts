# TODO
Make some good expalation on how to use these scripts

# AddqBittorrentTrackers.sh
The purpose of this script is to inject trackers into your **qBittorrent downloads**.

It may be executed manually or automatically with Radarr/Sonarr.

This script works with the qBittorrent v4.1+ API. It may work with lower versions, but must be checked. Let me know if you use an earlier version and it works, so I can expand the version compatability.

To use this script you'll need:
* [jq](https://stedolan.github.io/jq/). Check if `jq` is available for your distro with `sudo apt install jq`
* Curl. Install it with `sudo apt install curl`

* First make sure your Radarr/Sonarr user can execute the script with a process similar to this:
   * `chown USER:GROUP AddqBittorrentTrackers.sh` where `USER:GROUP` is the same user and group as qBittorrent
   * then be sure that is executable with: `chmod +x AddqBittorrentTrackers.sh` 
  
* Modify the `########## CONFIGURATIONS ##########` section:
   * `qbt_username` -> username to access to qBittorrent Web UI
   * `qbt_password` -> username to access to qBittorrent Web UI
   *  Note that if the script runs on the same device that runs qBittorrent, you can set `Bypass authentication for clients on localhost` so when the script runs, the username and password are not required
   * `qbt_host` -> if the script is on the same device as qBittorrent `http://localhost`, otherwise, set this to the remote device
   * `qbt_port` -> is the Web UI port
   * The script will check if the torrent is private or not automatically.
   * `live_trackers_list_url`, is the url where the trackers list are taken, is an automatic list, you can specify more than one url, just follow the example in the file.

Configuration is now complete. 


If you are a **Radarr and/or Sonarr user**, personally I:
1. Create a custom script (settings -> connect -> add notification -> Custom Script).
2. The name is not important. I use Add Transmission Trackers, you can use any name you like.
3. Set "On Grab".
4. Inside Path field, point to the `AddqBittorrentTrackers.sh` script.
5. Save the custom script.

Now, when _Radarr and/or Sonarr_ grabs a new torrent, the script will automatically be triggered and a custom tracker list will be added to the torrent. This is true only if the torrent is not from a private tracker.

To run the script manually, simply run `./AddqBittorrentTrackers.sh`. All the possible options will be shown. Additionally, when calling the script, there are many options to add trackers to torrents.

One note about configuration, if you want to use it manually, you must configure the username, password, host and port within the file. This is for simplicity. Otherwise I would have to insert four new options to be called every time manually, or "complicate" the script by checking for the possibility of a configuration file to be saved somewhere. If it is necessary I will do it, but for now I think it is easier to keep only the necessary options.

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# AddTransmissionTrackers.sh
The purpose of this script is to inject trackers inside **Transmission torrent**

This may be used manually, or with Radarr/Sonarr automatically.

Included is the option to call the script and specify name and/or id where add trackers

* First make sure your Radarr/Sonarr user can execute the script with some like this:
   * Take ownership with: `chown USER:USER AddTransmissionTrackers.sh` where `USER:GROUP` is the same user and group as Transmission.
   * Ensure that is executable: `chmod +x AddTransmissionTrackers.sh`

* Modify the scripts `########## CONFIGURATIONS ##########` section:
   * `transmission_username`, `transmission_password`, `transmission_host` and `transmission_port` are the Transmission settings you've already set.
   * `live_trackers_list_url`, is the url from which the trackers lists are obtained. You may specify more than one url, just follow the example in the file.
   * The script will check if the torrent is private or not automatically.

The configuration is complete.


If you are a **Radarr and/or Sonarr user**, personally I:
1. Create a custom script (settings -> connect -> add notification -> Custom Script).
2. The name is not important. I use Add Transmission Trackers, you can use any name you like.
3. Set "On Grab".
4. Inside Path field, point to the `AddTransmissionTrackers.sh` script.
5. Save the custom script.

Now, when _Radarr and/or Sonarr_ grabs a new torrent, the script will automatically be triggered and a custom tracker list will be added to the torrent. This is true only if the torrent is not from a private tracker.

To run the script manually, simply run `./AddTransmissionTrackers.sh`. All the possible options will be shown. Additionally, when calling the script, there are many options to add trackers to torrents.

One note about configuration, if you want to use it manually, you must configure the username, password, host and port within the file. This is for simplicity. Otherwise I would have to insert four new options to be called every time manually, or "complicate" the script by checking for the possibility of a configuration file to be saved somewhere. If it is necessary I will do it, but for now I think it is easier to keep only the necessary options.

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# TransmissionRemoveCompleteTorrent.sh

The purpose of this script is to **remove the completed torrent from Transmission**, but only the torrent added by Radarr/Sonarr. 

The best way is to use it is to cronize it.

This script uses `transmission-remote`, normally this is already installed if you use transmission.

* First make sure your Radarr/Sonarr user can execute the script with some like this:
   * `chown USER:USER TransmissionRemoveCompleteTorrent.sh` 
    * Then ensure it is executable: `chmod +x TransmissionRemoveCompleteTorrent.sh`

* Modify the scripts `########## CONFIGURATIONS ##########` section:
   * `t_username`, `t_password`, `t_host` and `t_port` are all Transmission related. Set them accordingly.
   * `t_log` is to enable the logfile. If set to 1 the logfile will be written to `t_log_path`.

   * The most important setting is `automatic_folder`.  This is the folder that contains all the **automatic downloads**

   * I use this folder structure for automatic download that came from Radarr/Sonarr:
        - download
            - automatic
               - movie
               - tv_show

    * For the file configuration example, I've to set `automatic` for `automatic_folder` option.
       * `max_days_seed` for the maximum seed time
       * `remove_normal`. Pay attention if you set this to true, because this enables a kind of **force** option that also checks all non-automatic downloads
         
* Lastly, consider using cron for the script. Add this to your cron scheduler with some like this (varies according to your own Linux installs cron manager):
   * `30 01 * * * /PATHOFTHESCRIPT/TransmissionRemoveCompleteTorrent.sh >/dev/null 2>&1`
   * this example will execute the script at 01:30 every day.

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# qBittorrentHardlinksChecker.sh

The idea of this script is very simple, in my case it helps, judge for yourself if it helps you. 

For managing the seed times of automatic downloads from the various `*Arr`, I normally use [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents). It is a very complete and useful script that allows me to pick and choose category by category, tracker by tracker, the various torrent removal settings. This is because the space available is not infinite. So I am forced to do a regular cleanup of the various downloads. I always respect the rules of the various private trackers! 

**But let's come to the idea:** Very simply, if within the automatic downloading programs `*Arr` the configuration is set to generate hardlinks, then it means that _until I have deleted both the file from the torrent client and the linked file that is managed automatically_, the space occupied on the disk will be the same. This means that as long as I haven't watched and deleted that movie (etc), I could safely keep the shared downloaded file, because it no longer takes up disk space, being a hardlink. 

With this script, for the categories you set, you can check each download. If there's _two or more_ hardlinks the file will not be deleted from qBittorrent. If on the other hand the file has _only one hardlink_, then the script will consider whether or not to delete the file by checking the minimum seed time that has been set. 

**Here is an example of usage:** Downloads that only end up in the automatic categories, e.g. `movie` for Radarr (or whatever your category is) rather than `tv_show` for Sonarr (or whatever your category is), **before** running [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents) (which is appropriately configured previously)... I run this script and by doing so I make sure that any "duplicates" are not deleted and remain in seed. This helps me with the share ratio and minimum seed time.


**How to use:**
* First make sure your Radarr/Sonarr user can execute the script with some like this:
    * `chown USER:GROUP qBittorrentHardlinksChecker.sh` where `USER:GROUP` is the user and group of Radarr/Sonarr
    * then be sure that is executable `chmod +x AddqBittorrentTrackers.sh`
	
**Note:** not being a script that is called from `*Arr` is not strictly necessary to change user and group, just make sure that the script however can be executed by the user concerned

* Modify the scripts `########## CONFIGURATIONS ##########` section:
    * `qbt_username` -> username to access to qBittorrent Web UI.
    * `qbt_password` -> username to access to qBittorrent Web UI.
    * Note that if the script runs on the same device that runs qBittorrent, you can set `Bypass authentication for clients on localhost`. When the script executes, the username and password are not required.
    * `qbt_host` -> if the script is on the same device as qBittorrent use `http://localhost`, otherwise, set this to the remote device.
    * `qbt_port` -> is the Web UI port.
    * `category_list` -> is the list of categories upon which the script performs the check.
    * `min_seeding_time` -> is the minimum seed time expressed in seconds.
    * `only_private` -> if true, the script will only check the torrents that are from private trackers. In this way you can set [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents) in order to only the remaining trackers. This help the share ratio and helps you to find and remove torrents from public trackers with your own rules.
    * `private_torrents_check_orphan` -> This is only for private trackers. If `true`, check the torrent and if is not registered, it will be deleted.
    * `public_torrent_check_bad_trackers` -> Only for public torrents. If `true`, check the trackers and the bad one/s will be eliminated, but _not_ the torrent itself, _only_ the trackers. Be patient, this can be a "slow" function during the deleting/ion phase.

I recommend you use this script with cron or create a timer for `systemd`. I personally use it via timer so runs right after [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents)
