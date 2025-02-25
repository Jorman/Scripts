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
categories='Serie_Tv,Film'

# Minimum seed time before deletion, expressed in seconds, for example 864000 means 10 days
min_seeding_time=864000

# Using docker it may happen that the path is different from the real one, this allows to replace part of qBittorrent path, turning it into the real one
# In this example, if a download within qBittorren has /oldpath/film as its path, the script will interpret it as /new/path/film
# This allows volumes within qBittorrent to be mounted differently from the actual path on disk
# Leave empty if not needed
virtual_path="oldpath" # The qBittorrent path, or the part you want to change
real_path="new/path" # The new part of the path

# Check only private torrents? if not true (lowercase) will check all torrents in given categories not only the private one
only_private=true

# If true, only for private tracker, check the torrent and if is not registered will be deleted
private_torrents_check_orphan=true

# If true, only for public torrent, check the trackers and the bad one will be eliminated, not the torrent only the trackers
public_torrent_check_bad_trackers=true

# If true, if there's some torrent in error, a force recheck is actuaded, this try to start again the torrent
receck_erroring_torrent=true
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

if [[ "${qbt_host,,}" == *"https"* ]] ;then
	curl_executable="${curl_executable} --insecure"
fi

# Variable to keep track of dryrun mode
dryrun=false

if [ "$1" == "test" ]; then
	dryrun=true
	echo "Dryrun mode turned on."
	echo ""
fi

########## FUNCTIONS ##########
url_encode() {
  local string="${1}"

  # Check if xxd is available
  if command -v xxd >/dev/null 2>&1; then
    # If xxd is available, use xxd for encoding
    printf '%s' "$string" | xxd -p | sed 's/\(..\)/%\1/g' | tr -d '\n'
  else
    # If jq is available, use jq for encoding
    jq -nr --arg s "$string" '$s|@uri'
  fi
}

get_cookie () {
	encoded_username=$(url_encode "$qbt_username")
	encoded_password=$(url_encode "$qbt_password")

	# If encoding fails, exit the function
	if [ $? -ne 0 ]; then
		echo "Error during URL encoding" >&2
		return 1
	fi

	qbt_cookie=$($curl_executable --silent --fail --show-error \
		--header "Referer: ${qbt_host}:${qbt_port}" \
		--cookie-jar - \
		--data "username=${encoded_username}&password=${encoded_password}" ${qbt_host}:${qbt_port}/api/v2/auth/login)
}

get_torrent_list () {
	[[ -z "$qbt_cookie" ]] && get_cookie
	torrent_list=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		--cookie - \
		--request GET "${qbt_host}:${qbt_port}/api/v2/torrents/info")
}

delete_torrent () {
	hash="$1"
	echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		-d "hashes=${hash}&deleteFiles=true" \
		--cookie - \
		--request POST "${qbt_host}:${qbt_port}/api/v2/torrents/delete"
	echo "Deleted"
}

recheck_torrent () {
	hash="$1"
	echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		-d "hashes=${hash}" \
		--cookie - \
		--request POST "${qbt_host}:${qbt_port}/api/v2/torrents/recheck"
	echo "Command executed"
}

reannounce_torrent () {
	hash="$1"
	echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		-d "hashes=${hash}" \
		--cookie - \
		--request POST "${qbt_host}:${qbt_port}/api/v2/torrents/reannounce"
}

remove_bad_tracker () {
	hash="$1"
	single_url="$2"
	echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		-d "hash=${hash}&urls=${single_url}" \
		--cookie - \
		--request POST "${qbt_host}:${qbt_port}/api/v2/torrents/removeTrackers"
}

unset_array () {
	array_element="$1"
	unset torrent_name_array[$array_element]
	unset torrent_hash_array[$array_element]
	unset torrent_path_array[$array_element]
	unset torrent_seeding_time_array[$array_element]
	unset torrent_progress_array[$array_element]
	unset private_torrent_array[$array_element]
	unset torrent_trackers_array[$array_element]
	unset torrent_category_array[$array_element]
}

wait() {
	w=$1
	echo "I'll wait ${w}s to be sure the reannunce going well..."
	while [ $w -gt 0 ]; do
		echo -ne "$w\033[0K\r"
		sleep 1
		w=$((w-1))
	done
}

check_hardlinks() {
	local path="$1"
	local more_hard_links=false

	if [ -d "$path" ]; then
		# È una directory, controlla i file all'interno
		while IFS= read -r -d $'\0' file; do
			if [ "$(stat -c %h "$file")" -gt 1 ]; then
				more_hard_links=true
				break
			fi
		done < <(find "$path" -type f -print0)
	else
		# È un file
		if [ "$(stat -c %h "$path")" -gt 1 ]; then
			more_hard_links=true
		fi
	fi

	echo "$more_hard_links"
}
########## FUNCTIONS ##########

get_torrent_list

if [ -z "$torrent_list" ]; then
	echo "No torrents founds to check"
	exit
fi

echo "Collecting data from qBittorrent, wait..."

torrent_name_array=()
torrent_hash_array=()
torrent_path_array=()
torrent_seeding_time_array=()
torrent_progress_array=()
private_torrent_array=()
torrent_trackers_array=()
torrent_category_array=()

while IFS= read -r line; do
	torrent_name_array+=("$line")
done < <(echo $torrent_list | $jq_executable --raw-output '.[] | .name')

while IFS= read -r line; do
	torrent_hash_array+=("$line")
done < <(echo $torrent_list | $jq_executable --raw-output '.[] | .hash')

while IFS= read -r line; do
	torrent_path_array+=("$line")
done < <(echo $torrent_list | $jq_executable --raw-output '.[] | .content_path')

while IFS= read -r line; do
	torrent_seeding_time_array+=("$line")
done < <(echo $torrent_list | $jq_executable --raw-output '.[] | .seeding_time')

while IFS= read -r line; do
	torrent_progress_array+=("$line")
done < <(echo $torrent_list | $jq_executable --raw-output '.[] | .progress')

while IFS= read -r line; do
	torrent_category_array+=("$line")
done < <(echo $torrent_list | $jq_executable --raw-output '.[] | .category')

while IFS= read -r line; do
	torrent_state_array+=("$line")
done < <(echo $torrent_list | $jq_executable --raw-output '.[] | .state')

for i in "${!torrent_hash_array[@]}"; do
	torrent_trackers_array[$i]=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		--cookie - \
		--request GET "${qbt_host}:${qbt_port}/api/v2/torrents/trackers?hash=${torrent_hash_array[$i]}")
done

for i in "${!torrent_hash_array[@]}"; do
	private_torrent_array[$i]=$(echo "$qbt_cookie" | $curl_executable --silent --fail --show-error \
		--cookie - \
		--request GET "${qbt_host}:${qbt_port}/api/v2/torrents/properties?hash=${torrent_hash_array[$i]}" | $jq_executable --raw-output '.is_private')
done

if [ -n "$categories" ]; then
	echo "Checking hardlinks:"
	for j in ${categories//,/ }; do
		test=$(echo "$torrent_list" | $jq_executable --raw-output --arg tosearch "$j" '.[] | select(.category == "\($tosearch)") | .name')

		if [[ -z "$test" ]]; then
			echo "There's no categories named ${j} or is empty"
			continue
		else
			echo "#####################################"
			echo "Checking category ${j}:"
			echo "#####################################"
			echo ""

			for i in "${!torrent_hash_array[@]}"; do
				if [[ $only_private == true ]]; then
					if [[ ${torrent_category_array[$i]} == ${j} ]] && [[ ${private_torrent_array[$i]} == true ]]; then
						echo "Analyzing torrent -> ${torrent_name_array[$i]}"

						if awk "BEGIN {exit !(${torrent_progress_array[$i]} < 1)}rent"; then
							printf "Torrent incomplete, nothing to do -> %0.3g%%\n" $(awk -v var="${torrent_progress_array[$i]}" 'BEGIN{print var * 100}')
						else

							if [ -z "$virtual_path" ] || [ -z "$real_path" ]; then
								result="${torrent_path_array[$i]}"
							else
								result=$(echo "${torrent_path_array[$i]/$virtual_path/"$real_path"}")
							fi

							more_hard_links=$(check_hardlinks "$result")

							if [ "$more_hard_links" = true ]; then
								echo "More than 1 hardlinks found in $result"
							else
								echo "No additional hardlinks found in $result"
							fi

							if [[ $more_hard_links == false ]]; then
								echo "Found 1 hardlinks, checking seeding time:"
								if [ ${torrent_seeding_time_array[$i]} -gt $min_seeding_time ]; then
									echo "I can delete this torrent, seeding time more than $min_seeding_time seconds"

									if [[ $dryrun == true ]]; then
										echo "Simulation (dryrun)..."
										echo "reannounce torrent"
										echo "wait 15 seconds..."
										echo "delete torrent ${torrent_name_array[$i]}"
										unset_array $i
									else
										reannounce_torrent ${torrent_hash_array[$i]}
										wait 15
										delete_torrent ${torrent_hash_array[$i]}
										unset_array $i
									fi

								else
									echo "I can't delete this torrent, seeding time not meet -> ${torrent_seeding_time_array[$i]}/${min_seeding_time}"
								fi
							else
								echo "More than 1 hardlinks found, nothing to do"
							fi
						fi
						echo "------------------------------"
					fi
				else
					if [[ ${torrent_category_array[$i]} == ${j} ]]; then
						echo "Analyzing torrent -> ${torrent_name_array[$i]}"

						if awk "BEGIN {exit !(${torrent_progress_array[$i]} < 1)}rent"; then
							printf "Torrent incomplete, nothing to do -> %0.3g%%\n" $(awk -v var="${torrent_progress_array[$i]}" 'BEGIN{print var * 100}')
						else

							if [ -z "$virtual_path" ] || [ -z "$real_path" ]; then
								result="${torrent_path_array[$i]}"
							else
								result=$(echo "${torrent_path_array[$i]/$virtual_path/"$real_path"}")
							fi

							more_hard_links=$(check_hardlinks "$result")

							if [ "$more_hard_links" = true ]; then
								echo "More than 1 hardlinks found in $result"
							else
								echo "No additional hardlinks found in $result"
							fi

							if [[ $more_hard_links == false ]]; then
								echo "Found 1 hardlinks, checking seeding time:"
								if [ ${torrent_seeding_time_array[$i]} -gt $min_seeding_time ]; then
									echo "I can delete this torrent, seeding time more than $min_seeding_time seconds"

									if [[ $dryrun == true ]]; then
										echo "Simulation (dryrun)..."
										echo "reannounce torrent"
										echo "wait 15 seconds..."
										echo "delete torrent ${torrent_name_array[$i]}"
										unset_array $i
									else
										reannounce_torrent ${torrent_hash_array[$i]}
										wait 15
										delete_torrent ${torrent_hash_array[$i]}
										unset_array $i
									fi
								else
									echo "I can't delete this torrent, seeding time not meet -> ${torrent_seeding_time_array[$i]}/${min_seeding_time}"
								fi
							else
								echo "More than 1 hardlinks found, nothing to do"
							fi
						fi
						echo "------------------------------"
					fi
				fi
			done
		fi
	done
	echo "Harklinks check completed"
	echo "------------------------------"
else
	echo "Categories list empty"
	echo "------------------------------"
fi

if [[ $private_torrents_check_orphan == true ]]; then
	echo "Checking for orphan torrents:"

	for i in "${!torrent_hash_array[@]}"; do
		orphan_torrent=$(echo ${torrent_trackers_array[$i]} | $jq_executable --raw-output '.[] | select((.status == 4) and (.num_peers < 1) and ((.msg|test("unregistered"; "i")) or (.msg|test("not registered"; "i")))) | any')
		if [[ $orphan_torrent == true ]]; then
			echo "Found orphan torrent -> ${torrent_name_array[$i]}, deleting"

			if [[ $dryrun == true ]]; then
				echo "Simulation (dryrun)..."
				echo "delete torrent ${torrent_name_array[$i]}"
				unset_array $i
			else
				delete_torrent ${torrent_hash_array[$i]}
				unset_array $i
			fi

			echo "------------------------------"
		fi
	done
	echo "Orphan check completed"
	echo "------------------------------"
fi

if [[ $public_torrent_check_bad_trackers == true ]]; then
	echo "Checking for bad trackers:"

	for i in "${!torrent_hash_array[@]}"; do
		if [[ ${private_torrent_array[$i]} != true ]]; then
			url_list=$(echo ${torrent_trackers_array[$i]} | $jq_executable --raw-output '.[] | select((.status == 4) and (.num_peers < 1)) .url')

			if [[ ! -z "$url_list" ]]; then
				echo "Some problem found on -> ${torrent_name_array[$i]}"
				echo "fixing..."

				if [[ $dryrun == true ]]; then
					echo "Simulation (dryrun)..."
					echo "removing bad tracker for torrent ${torrent_name_array[$i]}"
				else
					remove_bad_tracker ${torrent_hash_array[$i]} $(echo $url_list | tr '\n' ' ' | tr ' ' '|' | rev | cut -c2- | rev)
				fi

				echo "------------------------------"
			else
				continue
			fi
		fi
	done
	echo "Bad trackers check completed"
	echo "------------------------------"
fi

if [[ $receck_erroring_torrent == true ]]; then
	echo "Checking for errored torrent:"

	for i in "${!torrent_hash_array[@]}"; do
		if [[ ${torrent_state_array[$i]} == "error" ]]; then
			echo "Found erroring torrent -> ${torrent_name_array[$i]}, I'll recheck it"

			if [[ $dryrun == true ]]; then
				echo "Simulation (dryrun)..."
				echo "checking torrent ${torrent_name_array[$i]}"
			else
				recheck_torrent ${torrent_hash_array[$i]}
			fi

			echo "------------------------------"
		fi
	done
	echo "Error check completed"
	echo "------------------------------"
fi