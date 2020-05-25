# TODO
Make some good expalation on how to use these scripts

# AddqBittorrentTrackers.sh
In order to use this script you'll need:
https://github.com/fedarovich/qbittorrent-cli

save the script where you want and make it executable

You also have to modify the ########## CONFIGURATIONS ########## section:
username, password, host and port are all qBittorrent related.
private_tracker_list is a comma-separated list of your "private" trackers.
Actually you've to manually set your private trackers list because is not yet possible to make it automatically, till the "qbt" will make it for you.
live_trackers_list_url, is the url where the trackers list are taken, for now is working.
The configuration is done, now you've to configure Radarr and/or Sonarr, personally I:
1. Create a custom script (settings -> connect -> add notification -> Custom Script)
2. The name for the script is not important, I use Add Transmission Trackers
3. Set "On Grab"
4. On Path, point to the AddqBittorrentTrackers.sh script
5. Save the custom script

Now, when Radarr or Sonarr grab a new torrent, this script will be triggered and a custom tracker list will be added to the torrent, automatically, if the torrent is not from a private tracker.
Is also possible to run the script manually, simply run the script followed by the torrent you want to add trackers, ie
./AddqBittorrentTrackers.sh test
This will trigger the script and add trackers in all torrent that is not private "from a given list" and that contain test (case insensitive)
-----------------------------------------------------------------------------------------
# AddTransmissionTrackers.sh
actually I want to try to write down the new logic, quite similar to the qBittorrent one