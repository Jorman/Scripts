#!/bin/bash

############ CONFIG ############
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
# If more than 0 this will indicate the max seed time (in days) for the automatic torrents. If reached the torrent will be deleted with data
MAXIMUM_SEED=6
############ CONFIG ############

if [[ "$LOG_ENABLE" == "1" ]]; then
	if [[ ! -w "$LOG_PATH/${0##*/}.log" ]]; then
		touch "$LOG_PATH/${0##*/}.log"
	fi
fi

[[ "$LOG_ENABLE" == "1" ]] && echo "########## $(date) ##########" >> "$LOG_PATH/${0##*/}.log"

# use transmission-remote to get torrent list from transmission-remote list
TORRENTLIST=`$transmission_remote $HOST:$PORT --auth=$USERNAME:$PASSWORD --list | awk '{print $1}' | grep -o '[0-9]*'`
# for each torrent in the list
for TORRENTID in $TORRENTLIST; do
	TORRENTNAME=`$transmission_remote $HOST:$PORT --auth=$USERNAME:$PASSWORD --torrent $TORRENTID --info | grep Name: | sed -e 's/\s\sName:\s//'`
	[[ "$LOG_ENABLE" == "1" ]] && echo "* * * * * Checking torrent Nr. $TORRENTID -> $TORRENTNAME * * * * *" >> "$LOG_PATH/${0##*/}.log"

	# check if torrent download is completed
	DONE_100=`$transmission_remote $HOST:$PORT --auth=$USERNAME:$PASSWORD --torrent $TORRENTID --info | grep "Percent Done: 100%"`
	DONE_999=`$transmission_remote $HOST:$PORT --auth=$USERNAME:$PASSWORD --torrent $TORRENTID --info | grep "Percent Done: 99.9%"`
	DONE_AUTO=`$transmission_remote $HOST:$PORT --auth=$USERNAME:$PASSWORD --torrent $TORRENTID --info | grep "$AUTOMATIC_FOLDER"`
	DONE_SEED=`$transmission_remote $HOST:$PORT --auth=$USERNAME:$PASSWORD --torrent $TORRENTID --info | grep Seeding | awk -F'[()]' '{print $2}' | grep -o '[[:digit:]]*'`

	# check torrents current state is "Stopped", "Finished", or "Idle"
	STATE_STOPPED=`$transmission_remote $HOST:$PORT --auth=$USERNAME:$PASSWORD --torrent $TORRENTID --info | grep "State: Stopped\|Finished"`

	# if the torrent is "Stopped", "Finished", or "Idle" after downloading 100%"
	if [ "$DONE_100" != "" ] && [ "$STATE_STOPPED" != "" ]; then
		[[ "$LOG_ENABLE" == "1" ]] && echo "Torrent Nr. #$TORRENTID complete!" >> "$LOG_PATH/${0##*/}.log"
		# remove torrent and data from Transmission
		if [ "$DONE_AUTO" != "" ]; then
			[[ "$LOG_ENABLE" == "1" ]] && echo "Torrent Nr. #$TORRENTID is automatic, I'll also remove the data!" >> "$LOG_PATH/${0##*/}.log"
			$transmission_remote $HOST:$PORT --auth=$USERNAME:$PASSWORD --torrent $TORRENTID --remove-and-delete
		else
			[[ "$LOG_ENABLE" == "1" ]] && echo "Removing torrent ..." >> "$LOG_PATH/${0##*/}.log"
			$transmission_remote $HOST:$PORT --auth=$USERNAME:$PASSWORD --torrent $TORRENTID --remove
		fi
	elif [ "$DONE_AUTO" != "" ] && [ $(( DONE_SEED / 60 / 60 / 24)) -gt $MAXIMUM_SEED && [ $MAXIMUM_SEED -gt 0 ]; then
		[[ "$LOG_ENABLE" == "1" ]] && echo "Torrent Nr. #$TORRENTID is automatic, and have a good seed time. I'll also remove the data!" >> "$LOG_PATH/${0##*/}.log"
		$transmission_remote $HOST:$PORT --auth=$USERNAME:$PASSWORD --torrent $TORRENTID --remove
	else
		[[ "$LOG_ENABLE" == "1" ]] && echo "Torrent Nr. #$TORRENTID not complete ..." >> "$LOG_PATH/${0##*/}.log"
	fi

	if [ "$DONE_999" != "" ] && [ "$STATE_STOPPED" != "" ]; then
		[[ "$LOG_ENABLE" == "1" ]] && echo "Seems that torrent Nr. #$TORRENTID is stalled, I'll try to restart it!" >> "$LOG_PATH/${0##*/}.log"
		$transmission_remote $HOST:$PORT --auth=$USERNAME:$PASSWORD --torrent $TORRENTID -s
	fi

	[[ "$LOG_ENABLE" == "1" ]] && echo -e "* * * * * Checking torrent Nr. $TORRENTID complete. * * * * *\n" >> "$LOG_PATH/${0##*/}.log"
done
