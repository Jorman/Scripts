#!/bin/bash
# Original script from -> https://github.com/oilervoss/transmission

########## CONFIGURATIONS ##########
# Access Information for Transmission
t_username=
t_password=
# Host on which transmission runs
t_host=localhost
# Port
t_port=9091
# Configure here your private trackers
private_tracker_list=''
# Configure here your trackers list
live_trackers_list_url='https://newtrackon.com/api/stable'
########## CONFIGURATIONS ##########

trackers_list_file=~/TorrentTrackersList
transmission_remote="$(command -v transmission-remote)"
transmission_default_access="$t_host:$t_port -n=$t_username:$t_password"
auto_tor_grab=0
test_in_progress=0
applytheforce=0

if [[ -z $transmission_remote ]]; then
  echo -e "\n\e[0;91;1mFail on transmission-remote. Aborting.\n\e[0m"
  echo "Please install transmission-remote."
  exit 1
fi

########## FUNCTIONS ##########
function tracker_list_upgrade() {
  echo "Downloading/Upgrading traker list ..."
  wget -O $trackers_list_file $live_trackers_list_url
  if [[ $? -ne 0 ]]; then
    echo "I can't download the list, I'll use a static one"
cat >$trackers_list_file <<'EOL'
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
  start=1
  while read tracker; do
    if [ -n "$tracker" ]; then
      echo -ne "\e[0;36;1m$start/$number_of_trackers_in_list - Adding tracker $tracker\e[0;36m"
      $transmission_remote $transmission_default_access -t $1 --tracker-add $tracker 1>/dev/null 2>&1
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
  if [[ -s "$trackers_list_file" ]]; then # the file exist and is not empty?
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
########## FUNCTIONS ##########

if [ "$1" == "--force" ]; then
  applytheforce=1
  shift
fi

if [[ -n "${sonarr_download_id}" ]] || [[ -n "${radarr_download_id}" ]] || [[ -n "${lidarr_download_id}" ]] || [[ -n "${readarr_download_id}" ]]; then
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

  if [[ -n "${readarr_download_id}" ]]; then
    echo "Readarr varialbe found -> $readarr_download_id"
    hash=$(echo "$readarr_download_id" | awk '{print tolower($0)}')
  fi

  hash_check "${hash}"
  if [[ $? -ne 0 ]]; then
    echo "The download is not for a torrent client, I'll exit"
    exit
  fi
  auto_tor_grab="1"
fi

if [[ $sonarr_eventtype == "Test" ]] || [[ $radarr_eventtype == "Test" ]] || [[ $lidarr_eventtype == "Test" ]] || [[ $readarr_eventtype == "Test" ]]; then
  echo "Test in progress, all ok"
  test_in_progress=1
fi

if [ $test_in_progress -eq 1 ]; then
  echo "Good-bye!"
elif [ $auto_tor_grab -eq 0 ]; then # manual run
  echo "Getting torrents list ..."
  torrents_list=$($transmission_remote $transmission_default_access -l 2>/dev/null)

  if [ $? -ne 0 ]; then
    echo -e "\n\e[0;91;1mFail on Transmission. Aborting.\n\e[0m"
    exit 1
  fi

  if [ $# -eq 0 ]; then
    echo -e "\n\e[31mThis script expects one or more parameters\e[0m"
    echo -e "\e[0;36m${0##*/} \t\t\t- list current torrents "
    echo -e "${0##*/} \$n1 \$n2...\t- add trackers to torrent of number \$n1 and \$n2"
    echo -e "${0##*/} \$s1 \$s2...\t- add trackers to first torrent with part of name \$s1 and \$s2"
    echo -e "${0##*/} .\t\t- add trackers to all torrents"
    echo -e "Names are case insensitive "
    echo -e "\n\e[0;32;1mCurrent torrents:\e[0;32m"
    echo "$torrents_list" | sed -nr 's:(^.{6}).{64}:\1:p'
    echo -e "\e[0m"
    exit 1
  fi

  while [ $# -ne 0 ]; do
    tor_to_search="$1"
    [ "$tor_to_search" = "." ] && tor_to_search=" "

    if ! [[ "$tor_to_search" =~ ^[0-9]+$ ]]; then # tor_to_search is not a number
      torrent_found=$(echo "$torrents_list" | \
        sed -nr '1d;/^Sum:/d;s:(^.{6}).{64}:\1:p' | \
        sed -r 's/(\^|-|~|\[|]|\.)/ /g' | \
        grep -iF "$tor_to_search" | \
        sed -nr 's:(^.{6}).*:\1:;s: ::gp')
    else # parameter is a number
      torrent_found=$($transmission_remote $transmission_default_access -t$tor_to_search -i | sed -nr 's/ *Id: ?(.*)/\1/p')
    fi

    if [[ -n "$torrent_found" ]]; then
      while read -r single_found; do
        tor_name=$($transmission_remote $transmission_default_access -t $single_found -i | sed -nr 's/ *Name: ?(.*)/\1/p')
        tor_hash=$($transmission_remote $transmission_default_access -t $single_found -i | sed -nr 's/ *Hash: ?(.*)/\1/p')
        tor_trackers_list=$($transmission_remote $transmission_default_access -t $single_found -i | sed -nr 's/ *Magnet: ?(.*)/\1/p')

        tor_name_array+=("$tor_name")
        tor_hash_array+=("$tor_hash")
        tor_trackers_array+=("$tor_trackers_list")
      done <<< "$torrent_found"

      echo -e "\n\e[0;32;1mI found the following torrent:\e[0;32m"
      for jj in "${!tor_name_array[@]}"; do
        echo "${tor_name_array[$jj]}"
      done

    else
      echo -e "\n\e[0;31;1mI didn't find a torrent with the text/number: \e[21m$1"
      echo -e "\e[0m"
      shift
      continue
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
          generate_trackers_list
          inject_trackers ${tor_hash_array[$i]}
        fi
      else
        if [ $applytheforce -eq 1 ]; then
          echo "Applytheforce active, I'll inject trackers anyway"
        else
          echo -e "\e[0m\e[33mPrivate tracker list not present, proceding like usual\e[0m"
        fi
        generate_trackers_list
        inject_trackers ${tor_hash_array[$i]}
      fi
    done
  else
    echo "No torrents found, exiting"
  fi
else # auto_tor_grab active, so radarr or sonarr
  secs=10
  echo "I'll wait $secs to be sure ..."
  while [ $secs -gt 0 ]; do
    echo -ne "$secs\033[0K\r"
    sleep 1
    : $((secs--))
  done

  if [ -n "$private_tracker_list" ]; then #private tracker list present, need some more check
    echo -e "\e[0m\e[33mPrivate tracker list present, checking if the torrent is private\e[0m"
    tor_trackers_list=$($transmission_remote $transmission_default_access -t $hash -i | sed -nr 's/ *Magnet: ?(.*)/\1/p')

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
  generate_trackers_list
  inject_trackers $hash
fi