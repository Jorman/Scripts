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

# Configure here your categories, comma separated, like -> movie,tv_show
category_list='Serie_Tv,Film'

# Minimum seed time before deletion, expressed in seconds, for example 864000 means 10 days
min_seeding_time=864000

# Check only private torrents? if not true (lowercase) will check all torrents in given categories
only_private=true
########## CONFIGURATIONS ##########

jq_executable="$(command -v jq)"
curl_executable="$(command -v curl)"

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

########## FUNCTIONS ##########
get_cookie () {
	qbt_cookie=$($curl_executable --silent --fail --show-error \
		--header "Referer: ${qbt_host}:${qbt_port}" \
		--cookie-jar - \
		--request GET "${qbt_host}:${qbt_port}/api/v2/auth/login?username=${qbt_username}&password=${qbt_password}")
}

get_torrent_list () {
	[[ -z "$qbt_cookie" ]] && get_cookie
	torrent_list=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		--cookie - \
		--request GET "${qbt_host}:${qbt_port}/api/v2/torrents/info")
}

get_tracker_data () {
	hash="$1"
	torrent_tracker_data=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		--cookie - \
		--request GET "${qbt_host}:${qbt_port}/api/v2/torrents/trackers?hash=${hash}")
}

get_hash_list () {
	[[ -z "$qbt_cookie" ]] && get_cookie
	hash_list=$(echo "$torrent_list" | $jq_executable --raw-output '.[] | .hash')
}

delete_torrent () {
	hash="$1"
	echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		--cookie - \
		--request GET "${qbt_host}:${qbt_port}/api/v2/torrents/delete?hashes=${hash}&deleteFiles=true"
}
########## FUNCTIONS ##########

if [ -n "$category_list" ]; then

	get_torrent_list

	for j in ${category_list//,/ }; do
		torrent_name_list=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$j" '.[] | select(.category == "\($tosearch)") | .name')

		if [[ -z "$torrent_name_list" ]]; then
			echo "There's no categories named ${j}"
			continue
		else
			echo "Checking category ${j}:"
			tor_name_array=()
			tor_hash_array=()
			tor_path_array=()
			tor_seeding_time_array=()
			tor_progress_array=()
			while read -r single_found; do
				if [[ $only_private == true ]]; then
					private_check=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error --cookie - --request GET "${qbt_host}:${qbt_port}/api/v2/torrents/trackers?hash=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$single_found" '.[] | select(.name == "\($tosearch)") | .hash')" | $jq_executable --raw-output '.[0] | .msg | contains("private")')

					if [[ $private_check == true ]]; then
						tor_name_array+=("$single_found")
						hash=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$single_found" '.[] | select(.name == "\($tosearch)") | .hash')
						tor_hash_array+=("$hash")
						path=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$single_found" '.[] | select(.name == "\($tosearch)") | .content_path')
						tor_path_array+=("$path")
						seeding_time=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$single_found" '.[] | select(.name == "\($tosearch)") | .seeding_time')
						tor_seeding_time_array+=("$seeding_time")
						progress=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$single_found" '.[] | select(.name == "\($tosearch)") | .progress')
						tor_progress_array+=("$progress")
					fi
				else
					tor_name_array+=("$single_found")
					hash=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$single_found" '.[] | select(.name == "\($tosearch)") | .hash')
					tor_hash_array+=("$hash")
					path=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$single_found" '.[] | select(.name == "\($tosearch)") | .content_path')
					tor_path_array+=("$path")
					seeding_time=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$single_found" '.[] | select(.name == "\($tosearch)") | .seeding_time')
					tor_seeding_time_array+=("$seeding_time")
					progress=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$single_found" '.[] | select(.name == "\($tosearch)") | .progress')
					tor_progress_array+=("$progress")
				fi
			done <<< "$torrent_name_list"
		fi

		if [ ${#tor_name_array[@]} -gt 0 ]; then
			for i in "${!tor_name_array[@]}"; do
				echo "Analyzing torrent -> ${tor_name_array[$i]}"

				if awk "BEGIN {exit !(${tor_progress_array[$i]} < 1)}"; then
					printf "Torrent incomplete, nothing to do -> %0.3g%%\n" $(awk -v var="${tor_progress_array[$i]}" 'BEGIN{print var * 100}')
				else
					if [ "$(ls -l "${tor_path_array[$i]}" | awk '{print $2}')" = "1" ]; then
						echo "Found 1 hardlinks, checking seeding time:"
						if [ ${tor_seeding_time_array[$i]} -gt $min_seeding_time ]; then
							echo "I can delete this torrent, seeding time more than $min_seeding_time seconds"
							delete_torrent ${tor_hash_array[$i]}
						else
							echo "I can not delete this torrent, seeding time not meet -> ${tor_seeding_time_array[$i]}/${min_seeding_time}"
						fi
					else
						echo "More than 1 hardlinks found, nothing to do"
					fi
				fi
				echo "------------------------------"
			done
		else
			echo "No torrents found, exiting"
		fi
	done
	echo "Harklinks check completed"
else
	echo "Categories list empty"
fi

echo ""

get_torrent_list

if [ -n "$torrent_list" ]; then
	echo "Searching for orphan torrent and cleaning up bad trackers url"

	get_hash_list

	tor_name_array=()
	tor_hashes_array=()
	orphan_torrents_array=()
	while read -r single_hashes; do
		tor_hashes_array+=("$single_hashes")
		orphan_torrent=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error --cookie - --request GET "${qbt_host}:${qbt_port}/api/v2/torrents/trackers?hash=$single_hashes" | $jq_executable --raw-output '.[] | select((.status == 4) and (.num_peers < 0) and (.msg|contains("unregistered"))) | any')
		if [[ $orphan_torrent == true ]]; then
			tor_name=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error --cookie - --request GET "${qbt_host}:${qbt_port}/api/v2/torrents/info?hashes=$single_hashes" | $jq_executable --raw-output '.[] | .name')
			tor_name_array+=("$tor_name")
			orphan_torrents_array+=("$single_hashes")
		fi
	done <<< "$hash_list"

	if [ ${#orphan_torrents_array[@]} -gt 0 ]; then
		for i in "${!orphan_torrents_array[@]}"; do
			echo "Found orphan torrent -> ${tor_name_array[$i]}, deleting"
			delete_torrent ${orphan_torrents_array[$i]}
		done
	fi

	get_torrent_list
	get_hash_list

	tor_name_array=()
	tor_hashes_array=()
	while read -r single_hashes; do
		tor_hashes_array+=("$single_hashes")
		tor_name=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error --cookie - --request GET "${qbt_host}:${qbt_port}/api/v2/torrents/info?hashes=$single_hashes" | $jq_executable --raw-output '.[] | .name')
		tor_name_array+=("$tor_name")
	done <<< "$hash_list"

	for i in "${!tor_hashes_array[@]}"; do
		get_tracker_data ${tor_hashes_array[$i]}

		url_list=$(echo "$torrent_tracker_data" | $jq_executable --raw-output '.[] | select((.status == 4) and (.num_peers < 0)) .url')

		if [[ ! -z "$url_list" ]]; then
			echo "Some problem found on -> ${tor_name_array[$i]}, fixing"

			while read -r single_url; do
				echo "$qbt_cookie" | $curl_executable --silent --fail --show-error --cookie - --request GET "${qbt_host}:${qbt_port}/api/v2/torrents/removeTrackers?hash=${tor_hashes_array[$i]}&urls=${single_url}"
			done <<< "$url_list"
			echo "------------------------------"
		else
			continue
		fi
	done
	echo "Done"
else
	echo "No torrents founds to check"
fi