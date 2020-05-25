#!/bin/bash

########## CONFIGURATIONS ##########
# Access Information for Transmission
t_username=
t_password=
# Host where transmission runs
t_host=localhost
# Transmission port
t_port=9091
t_remote="$(command -v transmission-remote)"
# Log 0 for disable | 1 for enable
t_log=1
t_log_path="/data/Varie"
# Folder for automatic download? Be carefull must be different and not included into the default Download folder of transmission
# for example if your download go to /data/download and your automatic download from transmission go to /data/download/automatic
# you have to point to that automatic folder, because when the script run will search for automatic
automatic_folder="Automatici"
# If more than 0 this will indicate the max seed time (in days) for the automatic torrents. If reached the torrent will be deleted
max_days_seed=7
# If true, this will also delete data for non automatic torrent
remove_normal=true
########## CONFIGURATIONS ##########

if [[ "$t_log" == "1" ]]; then
	if [[ ! -w "$t_log_path/${0##*/}.log" ]]; then
		touch "$t_log_path/${0##*/}.log"
	fi
fi

[[ "$t_log" == "1" ]] && echo "########## $(date) ##########" >> "$t_log_path/${0##*/}.log"

# use transmission-remote to get torrent list from transmission-remote list
torrent_list=`$t_remote $t_host:$t_port -n=$t_username:$t_password -l | awk '{print $1}' | grep -o '[0-9]*'`
# for each torrent in the list
for torrent_id in $torrent_list; do
	torrent_name=`$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -i | grep Name: | sed -e 's/\s\sName:\s//'`
	[[ "$t_log" == "1" ]] && echo "* * * * * Checking torrent Nr. $torrent_id -> $torrent_name * * * * *" >> "$t_log_path/${0##*/}.log"

	# check if torrent download is completed
	percent_done=`$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -i | grep 'Percent Done' | awk '{print $3}' | sed 's/.$//'`
	done_auto=`$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -i | grep Location | awk '{print $2}' | grep "$automatic_folder"`
	done_seed=`$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -i | grep Seeding | awk -F'[()]' '{print $2}' | grep -o '[[:digit:]]*'`

	# check torrents current state is "Stopped", "Finished", or "Idle"
	state_stopped=`$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -i | grep "State: Stopped\|Finished"`

	if [ "$percent_done" == "100" ]; then # torrent complete
		[[ "$t_log" == "1" ]] && echo "          Torrent done at $percent_done%" >> "$t_log_path/${0##*/}.log"
		if [ "$done_auto" != "" ]; then # automatic torrent
			[[ "$t_log" == "1" ]] && echo "          Torrent is under automatic folder ..." >> "$t_log_path/${0##*/}.log"
			if [ "$state_stopped" != "" ]; then # transmission stopped the torrent
				[[ "$t_log" == "1" ]] && echo "          Torrent is stopped, I'll remove torrent and data!" >> "$t_log_path/${0##*/}.log"
				$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -rad
			elif [ $(( done_seed / 60)) -gt $(( max_days_seed * 60 * 24)) ] && [ $max_days_seed -gt 0 ]; then # maximum seed time reached
				[[ "$t_log" == "1" ]] && echo "          Torrent have a good seed time ($(( done_seed / 60))/$(( max_days_seed * 60 * 24)) minutes). I'll also remove the data!" >> "$t_log_path/${0##*/}.log"
				$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -rad
			else
				[[ "$t_log" == "1" ]] && echo "          Torrent not yet fully finished. Seed time ($(( done_seed / 60))/$(( max_days_seed * 60 * 24)) minutes)" >> "$t_log_path/${0##*/}.log"
			fi
		else # not automatic torrent
			[[ "$t_log" == "1" ]] && echo "          This's a normal torrent ..." >> "$t_log_path/${0##*/}.log"
			if [ "$state_stopped" != "" ]; then # transmission stopped the torrent
				[[ "$t_log" == "1" ]] && echo "          Torrent is stopped" >> "$t_log_path/${0##*/}.log"
				if [[ "$remove_normal" == "true" ]]; then
					[[ "$t_log" == "1" ]] && echo "          Also remove normal torrent is active, I'll remove torrent and data!" >> "$t_log_path/${0##*/}.log"
					$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -rad
				else
					$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -r
				fi
			elif [ $(( done_seed / 60 / 60 / 24)) -gt $max_days_seed ] && [ $max_days_seed -gt 0 ]; then # maximum seed time reached
				[[ "$t_log" == "1" ]] && echo "          Torrent have a good seed time ($(( done_seed / 60))/$(( max_days_seed * 60 * 24)) minutes)" >> "$t_log_path/${0##*/}.log"
				if [[ "$remove_normal" == "true" ]]; then
					[[ "$t_log" == "1" ]] && echo "          Also remove normal torrent is active, I'll remove torrent and data!" >> "$t_log_path/${0##*/}.log"
					$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -rad
				else
					$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -r
				fi
			else
				[[ "$t_log" == "1" ]] && echo "          Torrent not yet fully finished. Seed time ($(( done_seed / 60))/$(( max_days_seed * 60 * 24)) minutes)" >> "$t_log_path/${0##*/}.log"
			fi
		fi
	elif [ "$percent_done" == "99.9" ] && [ "$state_stopped" != "" ]; then # torrent stalled
		[[ "$t_log" == "1" ]] && echo "          Seems that torrent Nr. #$torrent_id is stalled, I'll try to restart it!" >> "$t_log_path/${0##*/}.log"
		$t_remote $t_host:$t_port -n=$t_username:$t_password -t $torrent_id -s
	elif [ "$percent_done" == "nan" ]; then # torrent not yet started
		[[ "$t_log" == "1" ]] && echo "          Torrent not yet started" >> "$t_log_path/${0##*/}.log"
	else # torrent not complete
		[[ "$t_log" == "1" ]] && echo "          Torrent not yet finished done at $percent_done%" >> "$t_log_path/${0##*/}.log"
	fi
	[[ "$t_log" == "1" ]] && echo -e "* * * * * Checking torrent Nr. $torrent_id complete. * * * * *\n" >> "$t_log_path/${0##*/}.log"
done