#!/bin/bash

########## CONFIGURATIONS ##########
# Host on which qBittorrent runs
qbt_host="http://10.0.0.100"
# Port -> the same port that is inside qBittorrent option -> Web UI -> Web User Interface
qbt_port="8081"
# Username to access to Web UI
qbt_username="admin"
# Password to access to Web UI
qbt_password="adminadmin"

# If true (lowercase) the script will inject trackers inside private torrent too (not a good idea)
ignore_private=false

# If true (lowercase) the script will remove all existing trackers before inject the new one, this functionality will works only for public trackers
clean_existing_trackers=false

# Configure here your trackers list
declare -a live_trackers_list_urls=(
	"https://newtrackon.com/api/stable"
	"https://trackerslist.com/best.txt"
	"https://trackerslist.com/http.txt"
	"https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
	)
########## CONFIGURATIONS ##########

jq_executable="$(command -v jq)"
curl_executable="$(command -v curl)"
auto_tor_grab=0
test_in_progress=0
applytheforce=0
all_torrent=0

if [[ -z $jq_executable ]]; then
	echo -e "\n\e[0;91;1mFail on jq. Aborting.\n\e[0m"
	echo "You can find it here: https://stedolan.github.io/jq/"
	echo "Or you can install it with -> sudo apt install jq"
	exit 1
fi

if [[ -z $curl_executable ]]; then
	echo -e "\n\e[0;91;1mFail on curl. Aborting.\n\e[0m"
	echo "You can install it with -> sudo apt install curl"
	exit 2
fi

if [[ "${qbt_host,,}" == *"https"* ]] ;then
	curl_executable="${curl_executable} --insecure"
fi

########## FUNCTIONS ##########
generate_trackers_list () {
	for j in "${live_trackers_list_urls[@]}"; do
		tmp_trackers_list+=$($curl_executable -sS $j)
		tmp_trackers_list+=$'\n'
	done

	trackers_list=$(echo "$tmp_trackers_list" | tr ' ' '\n' | awk '{if ($0 && !a[$0]++) print($0 "\n")}')
	if [[ $? -ne 0 ]]; then
		echo "I can't download the list, I'll use a static one"
cat >"${trackers_list}" <<'EOL'
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
	number_of_trackers_in_list=$(echo "$trackers_list" | wc -l)
}

inject_trackers () {
	echo -ne "\e[0;36;1mInjecting... \e[0;36m"
	if [[ $clean_existing_trackers == true ]]; then
		echo -e " \e[32mBut before a quick cleaning the existing trackers... "
		torrent_urls=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
				--cookie - \
				--request GET "${qbt_host}:${qbt_port}/api/v2/torrents/trackers?hash=${1}" | $jq_executable --raw-output '.[] | .url' \
				| tail -n +4 | tr '\n' '|' | rev | cut -c2- | rev)
		remove_trackers $1 "$torrent_urls"
	fi

	# Merge tracker URLs separated by %0A.
	urls=${trackers_list//$'\n'/%0A}

	# Create the data string for the POST request.
	data="hash=${1}&urls=$urls"

	# Execute HTTP POST request using curl
	$curl_executable --silent --fail --show-error \
					--cookie "$qbt_cookie" \
					--request POST \
					--header "User-Agent: Fiddler" \
					--header "Host: ${qbt_host}:${qbt_port}" \
					--header "Content-Type: application/x-www-form-urlencoded" \
					--data "$data" \
					"${qbt_host}:${qbt_port}/api/v2/torrents/addTrackers"
	echo -e "\e[32mdone, injected $(( (number_of_trackers_in_list + 1) / 2 )) trackers!"
}

get_torrent_list () {
	get_cookie
	torrent_list=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		--cookie - \
		--request GET "${qbt_host}:${qbt_port}/api/v2/torrents/info")
}

get_cookie () {
	qbt_cookie=$($curl_executable --silent --fail --show-error \
		--header "Referer: ${qbt_host}:${qbt_port}" \
		--cookie-jar - \
		--data "username=${qbt_username}&password=${qbt_password}" ${qbt_host}:${qbt_port}/api/v2/auth/login)
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

remove_trackers () {
	hash="$1"
	single_url="$2"
	echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		-d "hash=${hash}&urls=${single_url}" \
		--cookie - \
		--request POST "${qbt_host}:${qbt_port}/api/v2/torrents/removeTrackers"
}

wait() {
	w=$1
	echo "I'll wait ${w}s to be sure ..."
	while [ $w -gt 0 ]; do
		echo -ne "$w\033[0K\r"
		sleep 1
		w=$((w-1))
	done
}
########## FUNCTIONS ##########

if [ -t 1 ] || [[ "$PWD" == *qbittorrent* ]] ; then
	if [[ ! $@ =~ ^\-.+ ]]; then
		echo "Arguments must be passed with - in front, like -n foo. Check instructions"
		echo ""
		$0 -h
		exit
	fi

	[ $# -eq 0 ] && $0 -h

	if [ $# -eq 1 ] && [ $1 == "-f" ]; then
		echo "Don't use only -f, you need to specify also the torrent!"
		exit
	fi

	while getopts ":acflhn:" opt; do
		case ${opt} in
			a ) # If used inject trackers to all torrent.
				all_torrent=1
				;;
			c ) # If used remove all the existing trackers before injecting the new ones.
				clean_existing_trackers=true
				;;
			f ) # If used force the injection also in private trackers.
				applytheforce=1
				;;
			l ) # Print the list of the torrent where you can inject trackers.
				get_torrent_list
				echo -e "\n\e[0;32;1mCurrent torrents:\e[0;32m"
				echo "$torrent_list" | $jq_executable --raw-output '.[] .name'
				exit
				;;
			n ) # Specify the name of the torrent example -n foo or -n "foo bar", multiple -n can be used.
				tor_arg_names+=("$OPTARG")
				;;
			: )
				echo "Invalid option: -${OPTARG} requires an argument" 1>&2
				exit 0
				;;
			\? )
				echo "Unknow option: -${OPTARG}" 1>&2
				exit 1
				;;
			h | * ) # Display help.
				echo "Usage:"
				echo "$0 -a	Inject trackers to all torrent in qBittorrent, this not require any extra information"
				echo "$0 -c	Clean all the existing trackers before the injection, this not require any extra information"
				echo "$0 -f	Force the injection of the trackers inside the private torrent too, this not require any extra information"
				echo "$0 -l	Print the list of the torrent where you can inject trackers, this not require any extra information"
				echo "$0 -n	Specify the torrent name or part of it, for example -n foo or -n 'foo bar'"
				echo "$0 -h	Display this help"
				echo "NOTE:"
				echo "It's possible to specify more than -n in one single command"
				echo "Just remember that if you set -a in useless to add any extra -n, but -f can always be used"
				exit 2
				;;
		esac
	done
	shift $((OPTIND -1))
else
	if [[ -n "${sonarr_download_id}" ]] || [[ -n "${radarr_download_id}" ]] || [[ -n "${lidarr_download_id}" ]] || [[ -n "${readarr_download_id}" ]]; then
		#wait 5
		if [[ -n "${sonarr_download_id}" ]]; then
			echo "Sonarr variable found -> $sonarr_download_id"
			hash=$(echo "$sonarr_download_id" | awk '{print tolower($0)}')
		fi

		if [[ -n "${radarr_download_id}" ]]; then
			echo "Radarr variable found -> $radarr_download_id"
			hash=$(echo "$radarr_download_id" | awk '{print tolower($0)}')
		fi

		if [[ -n "${lidarr_download_id}" ]]; then
			echo "Lidarr variable found -> $lidarr_download_id"
			hash=$(echo "$lidarr_download_id" | awk '{print tolower($0)}')
		fi

		if [[ -n "${readarr_download_id}" ]]; then
			echo "Readarr variable found -> $readarr_download_id"
			hash=$(echo "$readarr_download_id" | awk '{print tolower($0)}')
		fi

		hash_check "${hash}"
		if [[ $? -ne 0 ]]; then
			echo "The download is not for a torrent client, I'll exit"
			exit 3
		fi
		auto_tor_grab="1"
	fi

	if [[ $sonarr_eventtype == "Test" ]] || [[ $radarr_eventtype == "Test" ]] || [[ $lidarr_eventtype == "Test" ]] || [[ $readarr_eventtype == "Test" ]]; then
		echo "Test in progress..."
		test_in_progress=1
	fi
fi

for i in "${tor_arg_names[@]}"; do
	if [[ -z "${i// }" ]]; then
		echo "one or more argument for -n not valid, try again"
		exit
	fi
done

if [ $test_in_progress -eq 1 ]; then
	echo "Good-bye!"
elif [ $auto_tor_grab -eq 0 ]; then # manual run
	get_torrent_list

	if [ $all_torrent -eq 1 ]; then
		while IFS= read -r line; do
			torrent_name_array+=("$line")
		done < <(echo $torrent_list | $jq_executable --raw-output '.[] | .name')

		while IFS= read -r line; do
			torrent_hash_array+=("$line")
		done < <(echo $torrent_list | $jq_executable --raw-output '.[] | .hash')
	else
		for i in "${tor_arg_names[@]}"; do
			torrent_name_list=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$i" '.[] | select(.name | ascii_downcase | contains($tosearch | ascii_downcase)) .name') #possible fix for ONIGURUMA regex libary

			if [ -n "$torrent_name_list" ]; then # not empty
				torrent_name_check=1
				echo -e "\n\e[0;32;1mFor argument ### $i ###\e[0;32m"
				echo -e "\e[0;32;1mI found the following torrent:\e[0;32m"
				echo "$torrent_name_list"
			else
				torrent_name_check=0
			fi

			if [ $torrent_name_check -eq 0 ]; then
				echo -e "\e[0;31;1mI didn't find a torrent with the text: \e[21m$i\e[0m"
				shift
				continue
			else
				while read -r single_found; do
					torrent_name_array+=("$single_found")
					hash=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$single_found" '.[] | select(.name == "\($tosearch)") | .hash')
					torrent_hash_array+=("$hash")
				done <<< "$torrent_name_list"
			fi
		done
	fi

	if [ ${#torrent_name_array[@]} -gt 0 ]; then
		echo ""
		for i in "${!torrent_name_array[@]}"; do
			echo -ne "\n\e[0;1;4;32mFor the Torrent: \e[0;4;32m"
			echo "${torrent_name_array[$i]}"

			if [[ $ignore_private == true ]] || [ $applytheforce -eq 1 ]; then # Inject anyway the trackers inside any torrent
				if [ $applytheforce -eq 1 ]; then
					echo -e "\e[0m\e[33mForce mode is active, I'll inject trackers anyway\e[0m"
				else
					echo -e "\e[0m\e[33mignore_private set to true, I'll inject trackers anyway\e[0m"
				fi
				generate_trackers_list
				inject_trackers ${torrent_hash_array[$i]}
			else
				private_check=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error --cookie - --request GET "${qbt_host}:${qbt_port}/api/v2/torrents/trackers?hash=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "${torrent_name_array[$i]}" '.[] | select(.name == "\($tosearch)") | .hash')" | $jq_executable --raw-output '.[0] | .msg | contains("private")')

				if [[ $private_check == true ]]; then
					private_tracker_name=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error --cookie - --request GET "${qbt_host}:${qbt_port}/api/v2/torrents/trackers?hash=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "${torrent_name_array[$i]}" '.[] | select(.name == "\($tosearch)") | .hash')" | $jq_executable --raw-output '.[3] | .url' | sed -e 's/[^/]*\/\/\([^@]*@\)\?\([^:/]*\).*/\2/')
					echo -e "\e[31m< Private tracker found \e[0m\e[33m-> $private_tracker_name <- \e[0m\e[31mI'll not add any extra tracker >\e[0m"
				else
					echo -e "\e[0m\e[33mThe torrent is not private, I'll inject trackers on it\e[0m"
					generate_trackers_list
					inject_trackers ${torrent_hash_array[$i]}
				fi
			fi
		done
	else
		echo "No torrents found, exiting"
	fi
else # auto_tor_grab active, so some *Arr
	wait 5
	get_torrent_list

	private_check=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error --cookie - --request GET "${qbt_host}:${qbt_port}/api/v2/torrents/trackers?hash=$hash" | $jq_executable --raw-output '.[0] | .msg | contains("private")')

	if [[ $private_check == true ]]; then
		private_tracker_name=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error --cookie - --request GET "${qbt_host}:${qbt_port}/api/v2/torrents/trackers?hash=$hash" | $jq_executable --raw-output '.[3] | .url' | sed -e 's/[^/]*\/\/\([^@]*@\)\?\([^:/]*\).*/\2/')
		echo -e "\e[31m< Private tracker found \e[0m\e[33m-> $private_tracker_name <- \e[0m\e[31mI'll not add any extra tracker >\e[0m"
	else
		echo -e "\e[0m\e[33mThe torrent is not private, I'll inject trackers on it\e[0m"
		generate_trackers_list
		inject_trackers $hash
	fi
fi
