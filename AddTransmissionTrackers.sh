#!/bin/bash
# Original script from -> https://github.com/oilervoss/transmission

########## CONFIGURATIONS ##########
# Configure here your private trackers
PRIVATE_TRACKER_LIST='shareisland,bigtower,girotorrent,alpharatio,torrentbytes'
# Configure here your trackers list
LIVE_TRACKERS_LIST_URL='https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt'
########## CONFIGURATIONS ##########

TRACKERS_LIST_FILE=$(pwd)/trakerlist
TRANSMISSION_REMOTE=$(which transmission-remote)

TORRENTS=$($TRANSMISSION_REMOTE -l 2>/dev/null)
if [ $? -ne 0 ]; then
  echo -e "\n\e[0;91;1mFail on transmission. Aborting.\n\e[0m"
  exit 1
fi

function upgrade() {
  wget -O $TRACKERS_LIST_FILE $LIVE_TRACKERS_LIST_URL
  if [[ $? -ne 0 ]]; then
    echo "wget failed, writing a standard one"
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
}

if [[ ! -z "$sonarr_release_title" ]] || [[ ! -z "$radarr_movie_title" ]]; then
  echo "sonarr or radarr variable found, looking better"
  if [[ ! -z "$sonarr_release_title" ]]; then
    echo "sonarr varialbe found:" $sonarr_release_title
    tmp_var=$(echo "$sonarr_release_title" | sed -r 's/(\^|-|~|\[|]|\.)/ /g' | sed 's/  */ /g')
  else
    echo "radarr varialbe found:" $radarr_movie_title
    tmp_var=$(echo "$radarr_movie_title" | sed -r 's/(\^|-|~|\[|]|\.)/ /g' | sed 's/  */ /g')
  fi
  set -- "$tmp_var"
  echo "argument set to" $tmp_var
fi

if [ $# -eq 0 ]; then
    echo -e "\n\e[31mThis script expects one or more parameters\e[0m"
    echo -e "\e[0;36maddtracker \t\t- list current torrents "
    echo -e "addtracker \$n1 \$n2...\t- add trackers to torrent of number \$n1 and \$n2"
    echo -e "addtracker \$s1 \$s2...\t- add trackers to first torrent with part of name \$s1 and \$s2"
    echo -e "addtracker .\t\t- add trackers to all torrents"
    echo -e "Names are case insensitive "
    echo -e "\n\e[0;32;1mCurrent torrents:\e[0;32m"
    echo "$TORRENTS" | sed -nr 's:(^.{4}).{64}:\1:p'
    echo -e "\n\e[0m"
    exit 1
fi

if [[ -s $TRACKERS_LIST_FILE ]]; then # the file exist and is not empty?
  echo "Tracker file exist, I'll check if I need to upgrade it"
  if [[ $(find "$TRACKERS_LIST_FILE" -mtime +1 -print) ]]; then
    echo "File $TRACKERS_LIST_FILE exists and is older than 1 day, I'll upgrade it"
    upgrade
  else
    echo "File $TRACKERS_LIST_FILE exists and I don't need to upgrade it"
  fi
else # file don't exist I've to download it
  echo "Tracker file don't exist I'll create a new one"
  upgrade
fi

TRACKER_LIST=$(cat $TRACKERS_LIST_FILE)

while [ $# -ne 0 ]; do
  PARAMETER="$1"
  [ "$PARAMETER" = "." ] && PARAMETER=" "

  if [ ! -z "${PARAMETER//[0-9]}" ] ; then
    PARAMETER=$(echo "$TORRENTS" | \
      sed -nr '1d;/^Sum:/d;s:(^.{4}).{64}:\1:p' | \
      sed -r 's/(\^|-|~|\[|]|\.)/ /g' | \
      #sed 's/  */ /g' | \
      grep -iF "$PARAMETER" | \
      sed -nr 's:(^.{4}).*:\1:;s: ::gp')
    if [ ! -z "$PARAMETER" ] && [ -z ${PARAMETER//[0-9]} ] ; then
      NUMBERCHECK=1
      echo -e "\n\e[0;32;1mI found the following torrent:\e[0;32m"
      echo "$TORRENTS" | sed -nr 's:(^.{4}).{64}:\1:p' | grep -i "$1"
    else
      NUMBERCHECK=0
    fi
  else
    NUMBERCHECK=$(echo "$TORRENTS" | \
      sed -nr '1d;/^Sum:/d;s: :0:g;s:^(....).*:\1:p' | \
      grep $(echo 0000$PARAMETER | sed -nr 's:.*([0-9]{4}$):\1:p'))
  fi

  if [ ${NUMBERCHECK:-0} -eq 0 ]; then
    echo -e "\n\e[0;31;1mI didn't find a torrent with the text/number: \e[21m$1"
    echo -e "\e[0m"
    shift
    continue
  fi

  for TORRENT in $PARAMETER; do
    echo -ne "\n\e[0;1;4;32mFor the Torrent: \e[0;4;32m"
    $TRANSMISSION_REMOTE -t $TORRENT -i | sed -nr 's/ *Name: ?(.*)/\1/p'
    PRIVATECHECK=0

    if [ ! -z "$PRIVATE_TRACKER_LIST" ]; then #private tracker list present, need some more check
      echo -e "\e[0m\e[33mPrivate tracker list present, checking if the torrent is private\e[0m"

      if [[ ! -z "$sonarr_release_indexer" ]]; then
        echo -e "\e[33mIndexer given by Sonarr\e[0m"
        INDEXER=$sonarr_release_indexer
      elif [[ ! -z "$radarr_release_indexer" ]]; then
        echo -e "\e[33mIndexer given by Radarr\e[0m"
        INDEXER=$radarr_release_indexer
      else
        echo -e "\e[33mIndexer directly from Transmission\e[0m"
        INDEXER=$($TRANSMISSION_REMOTE -t $TORRENT -i | sed -nr 's/ *Magnet: ?(.*)/\1/p')
      fi

      for j in ${PRIVATE_TRACKER_LIST//,/ }; do
        if [[ "${INDEXER,,}" =~ "${j,,}" ]];then
          echo -e "\e[31m< Private tracker found, I'll not add any extra tracker >\e[0m"
          PRIVATECHECK=$(expr $PRIVATECHECK + 1)
          break #if just one is found, stop the loop
        fi
      done
    else #private tracker list not present, no extra check needed
      echo "private tracker list not present, proceding like default"
    fi

    if [ $PRIVATECHECK -eq 0 ]; then
      echo "$TRACKER_LIST" | while read TRACKER
      do
        if [ ! -z "$TRACKER" ]; then
          echo -ne "\e[0;36;1mAdding $TRACKER\e[0;36m"
          $TRANSMISSION_REMOTE -t $TORRENT -td $TRACKER 1>/dev/null 2>&1 
          if [ $? -eq 0 ]; then
          echo -e " -> \e[32mSuccess! "
          else
          echo -e " - \e[31m< Failed > "
          fi
        fi
      done
    fi
  done
  shift
done

echo -e "\e[0m"
