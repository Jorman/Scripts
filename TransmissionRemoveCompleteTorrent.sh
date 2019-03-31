#!/bin/bash

########## CONFIGURATIONS ##########
# Access Information for Transmission
USERNAME=
PASSWORD=
# Host on which transmission runs
HOST=localhost
# Port
PORT=9091
transmission_remote="$(which transmission-remote)"
# Log
LOG_ENABLE=1
LOG_PATH="/data/Varie"
# Folder for automatic download? Be carefull must be different and not included into the default Download folder of transmission
# for example your download go to /data/download and your automatic download from transmission go to /data/download/automatic
# you have to point to that automatic folder, because when the script run will search for automatic
AUTOMATIC_FOLDER="Automatici"
# If more than 0 this will indicate the max seed time (in days) for the automatic torrents. If reached the torrent will be deleted
MAXIMUM_SEED=7
# If true, this will also delete data for non automatic torrent
ALSO_REMOVE_NORMAL=true
############ CONFIG ############

if [[ "$LOG_ENABLE" == "1" ]]; then
	if [[ ! -w "$LOG_PATH/${0##*/}.log" ]]; then
		touch "$LOG_PATH/${0##*/}.log"
	fi
fi

[[ "$LOG_ENABLE" == "1" ]] && echo "########## $(date) ##########" >> "$LOG_PATH/${0##*/}.log"

# use transmission-remote to get torrent list from transmission-remote list
TORRENTLIST=`$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -l | awk '{print $1}' | grep -o '[0-9]*'`
# for each torrent in the list
for TORRENTID in $TORRENTLIST; do
	TORRENTNAME=`$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -i | grep Name: | sed -e 's/\s\sName:\s//'`
	[[ "$LOG_ENABLE" == "1" ]] && echo "* * * * * Checking torrent Nr. $TORRENTID -> $TORRENTNAME * * * * *" >> "$LOG_PATH/${0##*/}.log"

	# check if torrent download is completed
	PERCENT_DONE=`$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -i | grep 'Percent Done' | awk '{print $3}' | sed 's/.$//'`
	DONE_AUTO=`$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -i | grep Location | awk '{print $2}' | grep "$AUTOMATIC_FOLDER"`
	DONE_SEED=`$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -i | grep Seeding | awk -F'[()]' '{print $2}' | grep -o '[[:digit:]]*'`

	# check torrents current state is "Stopped", "Finished", or "Idle"
	STATE_STOPPED=`$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -i | grep "State: Stopped\|Finished"`

	if [ "$PERCENT_DONE" == "100" ]; then # torrent complete
		[[ "$LOG_ENABLE" == "1" ]] && echo "          Torrent done at $PERCENT_DONE%" >> "$LOG_PATH/${0##*/}.log"
		if [ "$DONE_AUTO" != "" ]; then # automatic torrent
			[[ "$LOG_ENABLE" == "1" ]] && echo "          Torrent is under automatic folder ..." >> "$LOG_PATH/${0##*/}.log"
			if [ "$STATE_STOPPED" != "" ]; then # transmission stopped the torrent
				[[ "$LOG_ENABLE" == "1" ]] && echo "          Torrent is stopped, I'll remove torrent and data!" >> "$LOG_PATH/${0##*/}.log"
				$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -rad
			elif [ $(( DONE_SEED / 60)) -gt $(( MAXIMUM_SEED * 60 * 24)) ] && [ $MAXIMUM_SEED -gt 0 ]; then # maximum seed time reached
				[[ "$LOG_ENABLE" == "1" ]] && echo "          Torrent have a good seed time ($(( DONE_SEED / 60))/$(( MAXIMUM_SEED * 60 * 24)) minutes). I'll also remove the data!" >> "$LOG_PATH/${0##*/}.log"
				$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -rad
			else
				[[ "$LOG_ENABLE" == "1" ]] && echo "          Torrent not yet fully finished. Seed time ($(( DONE_SEED / 60))/$(( MAXIMUM_SEED * 60 * 24)) minutes)" >> "$LOG_PATH/${0##*/}.log"
			fi
		else # not automatic torrent
			[[ "$LOG_ENABLE" == "1" ]] && echo "          This's a normal torrent ..." >> "$LOG_PATH/${0##*/}.log"
			if [ "$STATE_STOPPED" != "" ]; then # transmission stopped the torrent
				[[ "$LOG_ENABLE" == "1" ]] && echo "          Torrent is stopped" >> "$LOG_PATH/${0##*/}.log"
				if [[ "$ALSO_REMOVE_NORMAL" == "true" ]]; then
					[[ "$LOG_ENABLE" == "1" ]] && echo "          Also remove normal torrent is active, I'll remove torrent and data!" >> "$LOG_PATH/${0##*/}.log"
					$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -rad
				else
					$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -r
				fi
			elif [ $(( DONE_SEED / 60 / 60 / 24)) -gt $MAXIMUM_SEED ] && [ $MAXIMUM_SEED -gt 0 ]; then # maximum seed time reached
				[[ "$LOG_ENABLE" == "1" ]] && echo "          Torrent have a good seed time ($(( DONE_SEED / 60))/$(( MAXIMUM_SEED * 60 * 24)) minutes)" >> "$LOG_PATH/${0##*/}.log"
				if [[ "$ALSO_REMOVE_NORMAL" == "true" ]]; then
					[[ "$LOG_ENABLE" == "1" ]] && echo "          Also remove normal torrent is active, I'll remove torrent and data!" >> "$LOG_PATH/${0##*/}.log"
					$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -rad
				else
					$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -r
				fi
			else
				[[ "$LOG_ENABLE" == "1" ]] && echo "          Torrent not yet fully finished. Seed time ($(( DONE_SEED / 60))/$(( MAXIMUM_SEED * 60 * 24)) minutes)" >> "$LOG_PATH/${0##*/}.log"
			fi
		fi
	elif [ "$PERCENT_DONE" == "99.9" ] && [ "$STATE_STOPPED" != "" ]; then # torrent stalled
		[[ "$LOG_ENABLE" == "1" ]] && echo "          Seems that torrent Nr. #$TORRENTID is stalled, I'll try to restart it!" >> "$LOG_PATH/${0##*/}.log"
		$transmission_remote $HOST:$PORT -n=$USERNAME:$PASSWORD -t $TORRENTID -s
	elif [ "$PERCENT_DONE" == "nan" ]; then # torrent not yet started
		[[ "$LOG_ENABLE" == "1" ]] && echo "          Torrent not yet started" >> "$LOG_PATH/${0##*/}.log"
	else # torrent not complete
		[[ "$LOG_ENABLE" == "1" ]] && echo "          Torrent not yet finished done at $PERCENT_DONE%" >> "$LOG_PATH/${0##*/}.log"
	fi
	[[ "$LOG_ENABLE" == "1" ]] && echo -e "* * * * * Checking torrent Nr. $TORRENTID complete. * * * * *\n" >> "$LOG_PATH/${0##*/}.log"
done
