#!/bin/bash

########## CONFIGURATIONS ##########
# Host on which qBittorrent runs
qbt_host="http://localhost"
# Port -> the same port that is inside qBittorrent option -> Web UI -> Web User Interface
qbt_port="8081"
# Username to access to Web UI
qbt_username="admin"
# Password to access to Web UI
qbt_password="adminadmin"
# Custom path have to be used when you want to save the TorrentTrackersList to a different location. A good example is when you're using this script with docker
custom_save_path=""
# Configure here your private trackers
private_tracker_list='jumbohostpro,connecting,torrentbytes,shareisland,hdtorrents,girotorrent,bigtower,arabafenice,alpharatio,netcosmo,torrentleech,tleechreload,milkie'
# Configure here your trackers list
declare -a live_trackers_list_urls=(
									"https://newtrackon.com/api/stable"
									"https://trackerslist.com/best.txt"
									"https://trackerslist.com/http.txt"
                				)
########## CONFIGURATIONS ##########

if [[ -z $custom_save_path ]]; then
	trackers_list_file="${HOME}/TorrentTrackersList"
else
	trackers_list_file="${custom_save_path}/TorrentTrackersList"
fi

if [[ -e $trackers_list_file ]]; then
	if [[ -w $trackers_list_file ]]; then
		echo "${trackers_list_file} is ok and writable"
	else
		echo -e "\n\e[0;91;1mError accessing tracker file list. Aborting.\n\e[0m"
		echo "I'm unable to write to ${trackers_list_file}"
		echo "Please check your configuration"
		exit 1
	fi
fi

jq_executable="$(command -v jq)"
curl_executable="$(command -v curl)"
auto_tor_grab=0
test_in_progress=0
applytheforce=0
first_run=0

if [[ -z $jq_executable ]]; then
	echo -e "\n\e[0;91;1mFail on jq. Aborting.\n\e[0m"
	echo "You can find it here: https://stedolan.github.io/jq/"
	echo "Or you can install it with -> sudo apt install jq"
	exit 1
fi

if [[ -z $curl_executable ]]; then
	echo -e "\n\e[0;91;1mFail on curl. Aborting.\n\e[0m"
	echo "You can install it with -> sudo apt install curl"
	exit 1
fi

########## FUNCTIONS ##########
tracker_list_upgrade () {
	echo "Downloading/Upgrading tracker list ..."
	for j in "${live_trackers_list_urls[@]}"; do
		$curl_executable -sS $j >> "$trackers_list_file"
	done
	if [[ $? -ne 0 ]]; then
		echo "I can't download the list, I'll use a static one"
cat >"$trackers_list_file" <<'EOL'
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
	sed -i '/^$/d' "$trackers_list_file"
	echo "Downloading/Upgrading done."
}

inject_trackers () {
	get_cookie
	start=1
	while read tracker; do
		if [ -n "$tracker" ]; then
			echo -ne "\e[0;36;1m$start/$number_of_trackers_in_list - Adding tracker $tracker\e[0;36m"
			echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
					--cookie - \
					--request POST "${qbt_host}:${qbt_port}/api/v2/torrents/addTrackers" --data "hash=$1" --data "urls=$tracker"

			if [ $? -eq 0 ]; then
				echo -e " -> \e[32mSuccess! "
			else
				echo -e " - \e[31m< Failed > "
			fi
		fi
		start=$((start+1))
	done <<< "$tracker_list"
	echo "Done!"
}

generate_trackers_list () {
	if [[ -s $trackers_list_file ]]; then # the file exist and is not empty?
		echo "Tracker file exist, I'll check if I need to upgrade it"
		days="1"

		# collect both times in seconds-since-the-epoch
		days_ago=$(date -d "now -$days days" +%s)
		file_time=$(date -r "$trackers_list_file" +%s)

		if (( $file_time <= $days_ago )); then
			echo "File $trackers_list_file exists and is older than $days day, I'll upgrade it"
			tracker_list_upgrade
		else
			echo "File $trackers_list_file is not older than $days days and I don't need to upgrade it"
		fi

	else # file don't exist I've to download it
		echo "Tracker file don't exist I'll create a new one"
		tracker_list_upgrade
	fi

	tracker_list=$(cat "$trackers_list_file")
	number_of_trackers_in_list=$(grep "" -c "$trackers_list_file")
	first_run=1
}

get_torrent_list () {
	get_cookie
	echo "Getting torrents list ..."
	torrents=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		--cookie - \
		--request GET "${qbt_host}:${qbt_port}/api/v2/torrents/info")
	echo "done"
}

get_cookie () {
	echo "Getting cookie ..."
	qbt_cookie=$($curl_executable --silent --fail --show-error \
		--header "Referer: ${qbt_host}:${qbt_port}" \
		--cookie-jar - \
		--request GET "${qbt_host}:${qbt_port}/api/v2/auth/login?username=${qbt_username}&password=${qbt_password}")
	echo "done"
}

hash_check() {
	case $1 in
		( *[!0-9A-Fa-f]* | "" ) return 1 ;;
		( * )
			case ${#1} in
				( 32 | 40 ) return 0 ;;
				( * )       return 1 ;;
			esac
	esac
}

wait() {
	i=$1
	echo "I'll wait $i to be sure ..."
	while [ $i -gt 0 ]; do
		echo -ne "$i\033[0K\r"
		sleep 1
		i=$((i-1))
	done
}
########## FUNCTIONS ##########

if [ "$1" == "--force" ]; then
	applytheforce=1
	shift
fi

if [[ -n "${sonarr_download_id}" ]] || [[ -n "${radarr_download_id}" ]] || [[ -n "${lidarr_download_id}" ]]; then
	wait 5
	if [[ -n "${sonarr_download_id}" ]]; then
		echo "Sonarr varialbe found -> $sonarr_download_id"
		hash=$(echo "$sonarr_download_id" | awk '{print tolower($0)}')
	fi

	if [[ -n "${radarr_download_id}" ]]; then
		echo "Radarr varialbe found -> $radarr_download_id"
		hash=$(echo "$radarr_download_id" | awk '{print tolower($0)}')
	fi

	if [[ -n "${lidarr_download_id}" ]]; then
		echo "Lidarr varialbe found -> $lidarr_download_id"
		hash=$(echo "$lidarr_download_id" | awk '{print tolower($0)}')
	fi

	hash_check "${hash}"
	if [[ $? -ne 0 ]]; then
		echo "The download is not for a torrent client, I'll exit"
		exit
	fi
	auto_tor_grab="1"
fi

if [[ $sonarr_eventtype == "Test" ]] || [[ $radarr_eventtype == "Test" ]] || [[ $lidarr_eventtype == "Test" ]]; then
	echo "Test in progress, all ok"
	test_in_progress=1
fi

if [ $test_in_progress -eq 1 ]; then
	echo "Good-bye!"
elif [ $auto_tor_grab -eq 0 ]; then # manual run
	get_torrent_list

	if [ $? -ne 0 ]; then
		echo -e "\n\e[0;91;1mFail on qBittorrent. Aborting.\n\e[0m"
		exit 1
	fi

	if [ $# -eq 0 ]; then
		echo -e "\n\e[31mThis script expects one or more parameters\e[0m"
		echo -e "\e[0;36m${0##*/} \t\t- list current torrents "
		echo -e "${0##*/} \$s1 \$s2...\t- add trackers to first torrent with part of name \$s1 and \$s2"
		echo -e "${0##*/} .\t\t- add trackers to all torrents"
		echo -e "Names are case insensitive "
		echo -e "\n\e[0;32;1mCurrent torrents:\e[0;32m"
		echo "$torrents" | $jq_executable --raw-output '.[] .name'
		exit 1
	fi

	while [ $# -ne 0 ]; do
		tor_to_search="$1"
		[ "$tor_to_search" = "." ] && tor_to_search="\d"

		torrent_name_list=$(echo "$torrents" | $jq_executable --raw-output --arg tosearch "$tor_to_search" '.[] | select(.name|test("\($tosearch)";"i")) .name')

		if [ -n "$torrent_name_list" ]; then # not empty
			torrent_name_check=1
			echo -e "\n\e[0;32;1mI found the following torrent:\e[0;32m"
			echo "$torrent_name_list"
		else
			torrent_name_check=0
		fi

		if [ $torrent_name_check -eq 0 ]; then
			echo -e "\e[0;31;1mI didn't find a torrent with the text: \e[21m$1\e[0m"
			shift
			continue
		else
			while read -r single_found; do
				tor_name_array+=("$single_found")
				hash=$(echo "$torrents" | $jq_executable --raw-output --arg tosearch "$single_found" '.[] | select(.name == "\($tosearch)") | .hash')
				tor_hash_array+=("$hash")
				tor_trackers_list=$(echo "$torrents" | $jq_executable --raw-output --arg tosearch "$hash" '.[] | select(.hash == "\($tosearch)") | .magnet_uri')
				tor_trackers_array+=("$tor_trackers_list")
			done <<< "$torrent_name_list"
		fi
		shift
	done

	if [ ${#tor_name_array[@]} -gt 0 ]; then
		for i in "${!tor_name_array[@]}"; do
			private_check=0
			echo -ne "\n\e[0;1;4;32mFor the Torrent: \e[0;4;32m"
			echo "${tor_name_array[$i]}"

			if [ -n "$private_tracker_list" ] && [ $applytheforce -eq 0 ]; then #private tracker list present, need some more check
				echo -e "\e[0m\e[33mPrivate tracker list present, checking if the torrent is private\e[0m"
				for j in ${private_tracker_list//,/ }; do
					if [[ "${tor_trackers_array[$i]}" =~ ${j,,} ]];then
						echo -e "\e[31m< Private tracker found \e[0m\e[33m-> $j <- \e[0m\e[31mI'll not add any extra tracker >\e[0m"
						private_check=1
						break #if just one is found, stop the loop
					fi
				done

				if [ $private_check -eq 0 ]; then
					echo -e "\e[0m\e[33mThe torrent is not private, I'll inject trackers on it\e[0m"
					[[ $first_run -eq 0 ]] && generate_trackers_list
					inject_trackers ${tor_hash_array[$i]}
				fi
			else
				if [ $applytheforce -eq 1 ]; then
					echo "Applytheforce active, I'll inject trackers anyway"
				else
					echo -e "\e[0m\e[33mPrivate tracker list not present, proceding like usual\e[0m"
				fi
				[[ $first_run -eq 0 ]] && generate_trackers_list
				inject_trackers ${tor_hash_array[$i]}
			fi
		done
	else
		echo "No torrents found, exiting"
	fi
else # auto_tor_grab active, so radarr or sonarr
	wait 5
	get_torrent_list

	if [ -n "$private_tracker_list" ]; then #private tracker list present, need some more check
		echo -e "\e[0m\e[33mPrivate tracker list present, checking if the torrent is private\e[0m"
		tor_trackers_list=$(echo "$torrents" | $jq_executable --raw-output --arg tosearch "$hash" '.[] | select(.hash == "\($tosearch)") | .magnet_uri')

		for j in ${private_tracker_list//,/ }; do
			if [[ "$tor_trackers_list" =~ ${j,,} ]];then
				echo -e "\e[31m< Private tracker found \e[0m\e[33m-> $j <- \e[0m\e[31mI'll not add any extra tracker >\e[0m"
				exit
			fi
		done
		echo "Torrent is not private I'll inject trackers"
	else
		echo -e "\e[0m\e[33mPrivate tracker list not present, proceding like usual\e[0m"
	fi
	[[ $first_run -eq 0 ]] && generate_trackers_list
	inject_trackers $hash
fi