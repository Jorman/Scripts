#!/bin/bash

########## CONFIGURATIONS ##########
# Access Information for Transmission
USERNAME=admin
PASSWORD=adminadmin
# Host on which transmission runs
HOST=http://localhost
# Port
PORT=8081
# Configure here your private trackers
PRIVATE_TRACKER_LIST='shareisland,bigtower,girotorrent,alpharatio,torrentbytes,arabafenice,hdtorrents,jumbohostpro'
# Configure here your trackers list
LIVE_TRACKERS_LIST_URL='https://newtrackon.com/api/stable'
########## CONFIGURATIONS ##########

TRACKERS_LIST_FILE=~/TorrentTrackersList
QBT="$(command -v qbt)"
QBT_DEFAULT_ACCESS="--username $USERNAME --password adminadmin --url $HOST:$PORT"
bypass="0"
test_in_progress="0"

if [[ -z $QBT ]]; then
  echo -e "\n\e[0;91;1mFail on qBittorrent-cli. Aborting.\n\e[0m"
  exit 1
fi

########## FUNCTIONS ##########
function upgrade() {
  echo "Downloading/Upgrading traker list ..."
  wget -O $TRACKERS_LIST_FILE $LIVE_TRACKERS_LIST_URL
  if [[ $? -ne 0 ]]; then
    echo "I can't download the list, I'll use a static one"
cat >$TRACKERS_LIST_FILE <<'EOL'
udp://tracker.coppersurfer.tk:6969/announce
http://tracker.internetwarriors.net:1337/announce
udp://tracker.internetwarriors.net:1337/announce
udp://tracker.opentrackr.org:1337/announce
udp://9.rarbg.to:2710/announce
udp://exodus.desync.com:6969/announce
udp://explodie.org:6969/announce
http://explodie.org:6969/announce
udp://public.popcorn-tracker.org:6969/announce
udp://tracker.vanitycore.co:6969/announce
http://tracker.vanitycore.co:6969/announce
udp://tracker1.itzmx.com:8080/announce
http://tracker1.itzmx.com:8080/announce
udp://ipv4.tracker.harry.lu:80/announce
udp://tracker.torrent.eu.org:451/announce
udp://tracker.tiny-vps.com:6969/announce
udp://tracker.port443.xyz:6969/announce
udp://open.stealth.si:80/announce
udp://open.demonii.si:1337/announce
udp://denis.stalker.upeer.me:6969/announce
udp://bt.xxx-tracker.com:2710/announce
http://tracker.port443.xyz:6969/announce
udp://tracker2.itzmx.com:6961/announce
udp://retracker.lanta-net.ru:2710/announce
http://tracker2.itzmx.com:6961/announce
http://tracker4.itzmx.com:2710/announce
http://tracker3.itzmx.com:6961/announce
http://tracker.city9x.com:2710/announce
http://torrent.nwps.ws:80/announce
http://retracker.telecom.by:80/announce
http://open.acgnxtracker.com:80/announce
wss://ltrackr.iamhansen.xyz:443/announce
udp://zephir.monocul.us:6969/announce
udp://tracker.toss.li:6969/announce
http://opentracker.xyz:80/announce
http://open.trackerlist.xyz:80/announce
udp://tracker.swateam.org.uk:2710/announce
udp://tracker.kamigami.org:2710/announce
udp://tracker.iamhansen.xyz:2000/announce
udp://tracker.ds.is:6969/announce
udp://pubt.in:2710/announce
https://tracker.fastdownload.xyz:443/announce
https://opentracker.xyz:443/announce
http://tracker.torrentyorg.pl:80/announce
http://t.nyaatracker.com:80/announce
http://open.acgtracker.com:1096/announce
wss://tracker.openwebtorrent.com:443/announce
wss://tracker.fastcast.nz:443/announce
wss://tracker.btorrent.xyz:443/announce
udp://tracker.justseed.it:1337/announce
udp://thetracker.org:80/announce
udp://packages.crunchbangplusplus.org:6969/announce
https://1337.abcvg.info:443/announce
http://tracker.tfile.me:80/announce.php
http://tracker.tfile.me:80/announce
http://tracker.tfile.co:80/announce
http://retracker.mgts.by:80/announce
http://peersteers.org:80/announce
http://fxtt.ru:80/announce
EOL
fi
  echo "Downloading/Upgrading done."
}
########## FUNCTIONS ##########

if [[ ! -z "$sonarr_download_id" ]] || [[ ! -z "$radarr_download_id" ]]; then
  if [[ ! -z "$sonarr_download_id" ]]; then
    echo "Sonarr varialbe found -> $sonarr_download_id"
    sonarr_download_id=$(echo "$sonarr_download_id" | awk '{print tolower($0)}')
  else
    echo "Radarr varialbe found -> $radarr_download_id"
    radarr_download_id=$(echo "$radarr_download_id" | awk '{print tolower($0)}')
  fi
  bypass="1"
fi

if [[ $sonarr_eventtype == "Test" ]] || [[ $radarr_eventtype == "Test" ]]; then
	echo "Test in progress, all ok"
	test_in_progress="1"
fi

if [[ $test_in_progress -eq 1 ]]; then
	echo "Good-bye!"
else
	TORRENTS=$($QBT torrent list --format json $QBT_DEFAULT_ACCESS 2>/dev/null)
	if [ $? -ne 0 ]; then
		echo -e "\n\e[0;91;1mFail on qBittorrent. Aborting.\n\e[0m"
		exit 1
	fi

	if [ $# -eq 0 ] && [ $bypass -eq 0 ]; then
	#if [ $# -eq 0 ]; then
		echo -e "\n\e[31mThis script expects one or more parameters\e[0m"
		echo -e "\e[0;36m${0##*/} \t\t- list current torrents "
		echo -e "${0##*/} \$s1 \$s2...\t- add trackers to first torrent with part of name \$s1 and \$s2"
		echo -e "${0##*/} .\t\t- add trackers to all torrents"
		echo -e "Names are case insensitive "
		echo -e "\n\e[0;32;1mCurrent torrents:\e[0;32m"
		echo "$TORRENTS" | jq --raw-output '.[] .name'
		echo -e "\n\e[0m"
		exit 1
	fi

	if [[ -s $TRACKERS_LIST_FILE ]]; then # the file exist and is not empty?
	  echo "Tracker file exist, I'll check if I need to upgrade it"

	  Days="1"

	  # collect both times in seconds-since-the-epoch
	  Days_ago=$(date -d "now -$Days Days" +%s)
	  file_time=$(date -r "$TRACKERS_LIST_FILE" +%s)

	  if (( $file_time <= $Days_ago )); then
	    echo "File $TRACKERS_LIST_FILE exists and is older than $Days day, I'll upgrade it"
	    upgrade
	  else
	    echo "File $TRACKERS_LIST_FILE is not older than $Days Days and I don't need to upgrade it"
	  fi

	else # file don't exist I've to download it
	  echo "Tracker file don't exist I'll create a new one"
	  upgrade
	fi

	TRACKER_LIST=$(cat $TRACKERS_LIST_FILE)

	if [[ $bypass -eq 0 ]]; then # no bypass
		while [ $# -ne 0 ]; do
			PARAMETER="$1"
			UNLUKYCHECK=0
			[ "$PARAMETER" = "." ] && PARAMETER="\d"

			# if [ ! -z "${PARAMETER//[0-9]}" ]; then # not empty
			if [ ! -z "$PARAMETER" ]; then # not empty
				PARAMETER=$(echo "$TORRENTS" | \
				jq --raw-output --arg TOSEARCH "$PARAMETER" '.[] | select(.name|test("\($TOSEARCH).";"i")) .name')

				if [ ! -z "$PARAMETER" ]; then # not empty
					Torrent_Name_Check=1
					echo -e "\n\e[0;32;1mI found the following torrent:\e[0;32m"
					echo "$PARAMETER"
				else
					Torrent_Name_Check=0
				fi
			fi

			if [ ${Torrent_Name_Check:-0} -eq 0 ]; then
				echo -e "\n\e[0;31;1mI didn't find a torrent with the text: \e[21m$1"
				echo -e "\e[0m"
				shift
				continue
			fi

			while read TORRENT; do
				echo -ne "\n\e[0;1;4;32mFor the Torrent: \e[0;4;32m"
				echo "$TORRENT"
				PRIVATECHECK=0

				if [ ! -z "$PRIVATE_TRACKER_LIST" ]; then #private tracker list present, need some more check
					echo -e "\e[0m\e[33mPrivate tracker list present, checking if the torrent is private\e[0m"

					for j in ${PRIVATE_TRACKER_LIST//,/ }; do
						if [[ "${INDEXER,,}" =~ "${j,,}" ]];then
							echo -e "\e[31m< Private tracker found \e[0m\e[33m-> $j <- \e[0m\e[31mI'll not add any extra tracker >\e[0m"
							PRIVATECHECK=1
							break #if just one is found, stop the loop
						else
							echo -e "\e[0m\e[33mNo private tracker found, let's move on\e[0m"
						fi
					done
				else #private tracker list not present, no extra check needed
					echo "Private tracker list not present, proceding like usual"
				fi

				if [ $PRIVATECHECK -eq 0 ]; then
					while read TRACKER; do
						if [ ! -z "$TRACKER" ]; then
							echo -ne "\e[0;36;1mAdding $TRACKER\e[0;36m"
							hash=$(echo "$TORRENTS" | \
							jq --raw-output --arg TOSEARCH "$TORRENT" '.[] | select(.name == "\($TOSEARCH)") | .hash')
							$QBT torrent tracker add $hash $TRACKER $QBT_DEFAULT_ACCESS
							if [ $? -eq 0 ]; then
								echo -e " -> \e[32mSuccess! "
							else
								echo -e " - \e[31m< Failed > "
							fi
						fi
					done <<< "$TRACKER_LIST"
				fi
			done <<< "$PARAMETER"
			shift
		done
	else # bypass active, so or sonarr or radarr var found
		if [ ! -z "$PRIVATE_TRACKER_LIST" ]; then #private tracker list present, need some more check
			echo -e "\e[0m\e[33mPrivate tracker list present, checking if the torrent is private\e[0m"

			if [[ ! -z "$sonarr_download_id" ]]; then
				INDEXER=$(echo "$TORRENTS" | \
				#jq --raw-output --arg TOSEARCH "$TORRENT" '.[] | select(.name|test("\($TOSEARCH)";"i")) .magnet_uri')
				jq --raw-output --arg TOSEARCH "$sonarr_download_id" '.[] | select(.hash == "\($TOSEARCH)") | .magnet_uri')
				hash=$sonarr_download_id
			else
				INDEXER=$(echo "$TORRENTS" | \
				#jq --raw-output --arg TOSEARCH "$TORRENT" '.[] | select(.name|test("\($TOSEARCH)";"i")) .magnet_uri')
				jq --raw-output --arg TOSEARCH "$radarr_download_id" '.[] | select(.hash == "\($TOSEARCH)") | .magnet_uri')
				hash=$radarr_download_id
			fi

			for j in ${PRIVATE_TRACKER_LIST//,/ }; do
				if [[ "${INDEXER,,}" =~ "${j,,}" ]];then
					echo -e "\e[31m< Private tracker found \e[0m\e[33m-> $j <- \e[0m\e[31mI'll not add any extra tracker >\e[0m"
					exit
					# break #if just one is found, stop the loop
				fi
			done
		else #private tracker list not present, no extra check needed
			echo "Private tracker list not present, proceding like usual"
		fi

		while read TRACKER; do
			if [ ! -z "$TRACKER" ]; then
				echo -ne "\e[0;36;1mAdding $TRACKER\e[0;36m"
				$QBT torrent tracker add $hash $TRACKER $QBT_DEFAULT_ACCESS
				if [ $? -eq 0 ]; then
					echo -e " -> \e[32mSuccess! "
				else
					echo -e " - \e[31m< Failed > "
				fi
			fi
		done <<< "$TRACKER_LIST"
	fi
fi

echo -e "\e[0m"