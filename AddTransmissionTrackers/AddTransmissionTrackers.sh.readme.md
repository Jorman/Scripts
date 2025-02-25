# AddTransmissionTrackers.sh

The purpose of this script is to inject trakers inside the **Transmission torrent**

This can be used manually, or with Radarr/Sonarr automatically. To run the script manually, simply run the script `./AddTransmissionTrackers.sh` and see all the possible options.

When Radarr and/or Sonarr grabs a new torrent *and if the torrent is not from a private tracker*, the script is triggered and the custom tracker list populated to the torrent.

In the latest version, I've inserted a new way to call the script, with many options to inject trackers inside torrents.

N.B for those updating to the latest script, `Transmission-remote` is no longer needed. All commands have been switched to directly use `/rpc`. This is the very first release with this method.



I've also included the possibility to call the script and specify the name and/or ID where one adds trackers:

* First ensure your Radarr/Sonarr user can execute the script with something like this:
   * Take ownership with: `chown USER:USER AddTransmissionTrackers.sh` where `USER:GROUP` is the same user and group as Transmission.
   * Ensure it is executable: `chmod +x AddTransmissionTrackers.sh`

* Modify the scripts `########## CONFIGURATIONS ##########` section:
   * `transmission_username`, `transmission_password`, `transmission_host` and `transmission_port`. These are all the same as your Transmission config.
   * `live_trackers_list_url`, is the URL where the trackers list is obtained. This is the default list. You may specify more than one URL, just follow the example in the file.
   * The script will automatically check if the torrent is private or public.

The configuration is complete.


If you are a **Radarr and/or Sonarr user**, personally I:
   1. Create a custom script (settings -> connect -> add notification -> Custom Script).
   2. The name is not important. I use Add Transmission Trackers, you can use any name you like.
   3. Set "On Grab".
   4. Inside Path field, point to the `AddTransmissionTrackers.sh` script.
   5. Save the custom script.



One note about configuration and using the script manually. Before use you MUST configure the username, password, host and port within the script. Otherwise I would have to insert four new options to be called every time for manual user input, or "complicate" it by having a configuration file saved somewhere. If it's necessary I will do it, but for now I think it is easier to keep only the necessary options.

