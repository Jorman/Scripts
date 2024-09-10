# qBittorrentHardlinksChecker.sh

The idea of this script is very simple, it **checks qBittorrents Hard Links**.  

In my case it helps, judge for yourself if it helps you. 

For managing the seed times of automatic downloads from the various `*Arr`, I normally use [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents). It is a very complete and useful script that allows me to pick and choose category by category, tracker by tracker, the various torrent removal settings. This is because my space available is not infinite. So I am forced to do a regular cleanup of the various downloads. I always respect the rules of the various private trackers! 

**But let's come to the idea:** Very simply, if the configuration within the automatic downloading programs `*Arr` is set to generate hardlinks, then it means that _until I have deleted both the file from the torrent client and the linked file that is managed automatically_, the space occupied on the disk will be the same. This means that as long as I haven't watched and deleted that movie (etc), I could safely keep the shared downloaded file, because it no longer takes up disk space, being a hardlink. 

With this script, for the categories you set, you can check each download. If there are _two or more_ hardlinks the file will not be deleted from qBittorrent. If on the other hand the file has _only one hardlink_, then the script will consider whether or not to delete the file by checking the minimum seed time that has been set. 

**Here is an example of usage:** Downloads that only end up in the automatic categories, e.g. `movie` for Radarr (or whatever your category is) rather than `tv_show` for Sonarr (or whatever your category is), **before** running [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents) (which is appropriately configured previously)... I run this script and by doing so I make sure that any "duplicates" are not deleted and remain in seed. This helps me with the share ratio and minimum seed time.


**How to use:**
* First make sure your Radarr/Sonarr user can execute the script with something like this:
    * `chown USER:GROUP qBittorrentHardlinksChecker.sh` where `USER:GROUP` is the user and group of Radarr/Sonarr.
    * Then be sure it is executable: `chmod +x AddqBittorrentTrackers.sh`
	
**Note:** not being a script that is called from `*Arr` it's not strictly necessary to change user and group, just make sure that the script can be executed by the user concerned.

* Modify the scripts `########## CONFIGURATIONS ##########` section:
    * `qbt_username` -> username to access to qBittorrent Web UI.
    * `qbt_password` -> username to access to qBittorrent Web UI.
    * Note that if the script runs on the same device that runs qBittorrent, you can set `Bypass authentication for clients on localhost`. When the script executes, the username and password are not required.
    * `qbt_host` -> if the script is on the same device as qBittorrent use `http://localhost`, otherwise, set this to the remote device.
    * `qbt_port` -> is the Web UI port.
    * `category_list` -> is the list of categories upon which the script performs the check.
    * `min_seeding_time` -> is the minimum seed time expressed in seconds.
    * `only_private` -> if true, the script will only check the torrents that are from private trackers. In this way you can set [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents) in order to remove only the remaining public trackers. This help the share ratio and helps you to find and remove torrents from public trackers with your own rules.
    * `private_torrents_check_orphan` -> This is only for private trackers. If `true`, check the torrent and if is not registered, it will be deleted.
    * `public_torrent_check_bad_trackers` -> Only for public torrents. If `true`, check the trackers and the bad one/s will be eliminated, but _not_ the torrent itself, _only_ the trackers. Be patient, this can be a "slow" function during the deleting/ion phase.

I recommend you use this script with cron or create a timer for `systemd`. I personally use it via timer so runs right after [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents)
