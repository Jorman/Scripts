# qBittorrentHardlinksChecker.py

The idea of this script is very simple, it **checks qBittorrents Hard Links** and run some checks on the downloading torrents.

In my case it helps, judge for yourself if it helps you.

For managing the seed times of automatic downloads from the various `*Arr`, I normally use [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents). It is a very complete and useful script that allows me to pick and choose category by category, tracker by tracker, the various torrent removal settings. This is because my space available is not infinite. So I am forced to do a regular cleanup of the various downloads. I always respect the rules of the various private trackers! 

**But let's come to the idea:** Very simply, if the configuration within the automatic downloading programs `*Arr` is set to generate hardlinks, then it means that _until I have deleted both the file from the torrent client and the linked file that is managed automatically_, the space occupied on the disk will be the same. This means that as long as I haven't watched and deleted that movie (etc), I could safely keep the shared downloaded file, because it no longer takes up disk space, being a hardlink.

With this script, for the categories you set, you can check each download. If there are _two or more_ hardlinks the file will not be deleted from qBittorrent. If on the other hand the file has _only one hardlink_, then the script will consider whether or not to delete the file by checking the minimum seed time that has been set. 

**Here is an example of usage:** Downloads that only end up in the automatic categories, e.g. `movie` for Radarr (or whatever your category is) rather than `tv_show` for Sonarr (or whatever your category is), **before** running [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents) (which is appropriately configured previously)... I run this script and by doing so I make sure that any "duplicates" are not deleted and remain in seed. This helps me with the share ratio and minimum seed time.

This script runs without needing a connection to the `*Arr`!

**Requirements:**
- Python 3.8+
- qBittorrent with WebUI enabled
- requests>=2.25.1
- PyYAML>=5.4.1
- colorama>=0.4.4
- typing>=3.7.4

**What it can do?**
- Can only work in certain categories of qBittorrent (even all of them)
- Can only work for certain types of torrents (private, public, or both)
- If the torrent is in an error state, it rechecks it
- If the torrent is "orphaned", it deletes it
- If the seed time is satisfied, deletes the torrent
- Removes failed trackers
- Checks the status of hard-links

**How to use:**
* There is a need for a configuration file, you can create the template tramiet the command `./qBittorrentHardlinksChecker.py --create-config`
   * If you are working with only one configuration file, there is no need to specify it each time, otherwise, to specify a configuration file just run the script with `./qBittorrentHardlinksChecker.py --config config.yaml`
* Once the configuration file has been configured, if the file name is `<script_name>_config.yaml`, then you will not need to call the configuration file, so you can use the script with the simple command `./qBittorrentHardlinksChecker.py`, otherwise you need to specify the configuration file
* If you want to simulate the operation of the script, but without making any changes, then run the script with `./qBittorrentHardlinksChecker.py --dry-run`

**Configuration file**
*qBittorrent server configuration*
qbt_host: "http://localhost" # Server address (with http/https).
qbt_port: "8081"             # Web UI Port
qbt_username: "admin"        # Web UI Username
qbt_password: "adminadmin"   # Web UI Password

*Configuration torrent management
Minimum seeding time in seconds (ex: 259200 = 3 days).
Set to 0 if you want to disable the min_seeding_time check*
min_seeding_time: 864000

*List of categories to be processed.
Use ["All"] for all categories.
Use ["Uncategorized"] for torrents without category.
Or specify categories: ["movies", "tv", "books"]*
categories:
  - "All"

*Type of torrent to be processed
Options: "private", "public" or blank "" to process all.*
torrent_type: ""

*Configuring paths (useful with Docker)*
virtual_path: ""   # Examample: "/downloads" in Docker
real_path: ""      # Example: "/home/user/downloads" real path on the system

*Automatic controls*
enable_recheck: true        # Enable automatic recheck torrent in error.
enable_orphan_check: true   # Enable orphan torrent checking, works only on private torrents

*States that identify a torrent as orphaned.*
orphan_states:
  - "unregistered"
  - "not registered"
  - "not found"

*Minimum number of peers before considering a torrent orphaned.
Default: 1*
min_peers: 1

**Note:**
 * "Orphan" check is performed only on `private` torrents.
 * Error tracker checking is performed only on `public` torrents.

I recommend you use this script with cron or create a timer for `systemd`. I personally use it via timer so runs right after [autoremove-torrent](https://github.com/jerrymakesjelly/autoremove-torrents)

**Cron examples:**

# Hourly check
0 * * * * /usr/bin/python3 /path/to/qBittorrentHardlinksChecker.py

# Daily at midnight
0 0 * * * /usr/bin/python3 /path/to/qBittorrentHardlinksChecker.py