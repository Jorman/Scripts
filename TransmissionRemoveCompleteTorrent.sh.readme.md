# TransmissionRemoveCompleteTorrent.sh

The best way is to use it is to cronize it.

This script uses `transmission-remote`, normally this is already installed if you use transmission.

* First make sure your Radarr/Sonarr user can execute the script with someting like this:
   * `chown USER:USER TransmissionRemoveCompleteTorrent.sh` 
    * Then ensure it is executable: `chmod +x TransmissionRemoveCompleteTorrent.sh`

* Modify the scripts `########## CONFIGURATIONS ##########` section:
   * `t_username`, `t_password`, `t_host` and `t_port` are all Transmission related. Set them accordingly.
   * `t_log` is to enable the logfile. If set to 1 the logfile will be written to `t_log_path`.
   * The most important setting is `automatic_folder`.  This is the folder that contains all the **automatic downloads**
   * I use this folder structure for automatic downloads that came from Radarr/Sonarr:
        - download
            - automatic
               - movie
               - tv_show

    * Within the files configuration example, I've set `automatic` for `automatic_folder` option.
    * `max_days_seed` is the maximum seed time.
    * `remove_normal`. Pay attention if you set this to true, because this enables a kind of **force** option that also checks all non-automatic downloads.
         
* Lastly, consider using cron for the script. Add this to your cron scheduler with something like this (varies according to your own Linux installs cron manager):
   * `30 01 * * * /PATHOFTHESCRIPT/TransmissionRemoveCompleteTorrent.sh >/dev/null 2>&1`
   * this example will execute the script at 01:30 every day.
