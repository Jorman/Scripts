#!/bin/bash

# Examples for testing
# sonarr_episodefile_sourcefolder="/data/torrent/tv/Penny.Dreadful.S01E01.720p.HDTV.x264-2HD" sonarr_episodefile_sourcepath="/data/torrent/tv/Penny.Dreadful.S01E01.720p.HDTV.x264-2HD/penny.dreadful.s01e01.720p.hdtv.x264-2hd.mkv"

# Instructions
# Put this script somewhere on your file system like /usr/local/bin and make it executable.
#
# In Sonarr, Settings -> Connect add a Custom Script
# On Grab: No
# On Download: Yes
# On Upgrade: Yes
# On Rename: No
# Path: /path/to/where/script/is/sonarr_cleanup_packed_torrent.sh
# Arguments:

# Tune values below to protect your torrents w/ small rar files or non-torrent download client.

# In *bytes*, the biggest rar file size limit to prevent video deletion from torrents with unrelated rar files (like subs)
# 25 * 1024 * 1024
rar_min_size=26214400

# Seconds to wait between size checks for in progress unpack
unpack_time=5

# The final base directory torrents end up in, for example "tv" from /data/torrents/tv
sonarr_final_dir="Serie_Tv"

# Identifiable portion of path to torrents, so it will only run on torrents.
# For example, a path of "/data/torrents/tv", "torrents" is a good choice.
torrent_path_portion="Automatici"

# Test that this is a download event, so we don't run on grab or rename.
# shellcheck disable=SC2154
if [[ "${sonarr_eventtype}" != "Download" ]]; then
  echo "[Torrent Cleanup] Sonarr Event Type is NOT Download, exiting."
  exit
fi

# Test this file exists, no point running on a file that isn't there.
# shellcheck disable=SC2154
if ! [[ -f "${sonarr_episodefile_sourcepath}" ]]; then
  echo "[Torrent Cleanup] File ${sonarr_episodefile_sourcepath} does not exist, exiting."
  exit
fi

# Test that this is a torrent, so we don't run on usenet downloads.
# shellcheck disable=SC2154
if ! [[ "${sonarr_episodefile_sourcepath}" =~ ${torrent_path_portion} ]]; then
  echo "[Torrent Cleanup] Path ${sonarr_episodefile_sourcepath} does not contain \"torrent\", exiting."
  exit
fi

# Test that this is a multi-file torrent, so we don't run on single file torrents.
# shellcheck disable=SC2154
base_dir=$( basename "${sonarr_episodefile_sourcefolder}" )
if [[ "${base_dir}" == "${sonarr_final_dir}" ]]; then
  echo "[Torrent Cleanup] Single file torrent, exiting."
  exit
fi

# We might run while the unpack is still happening, so wait for that before removing.
echo "[Torrent Cleanup] Starting wait for ${sonarr_episodefile_sourcepath} unpacking..."
file_size_start=$( stat --printf="%s" "${sonarr_episodefile_sourcepath}" )
sleep ${unpack_time}
file_size_end=$( stat --printf="%s" "${sonarr_episodefile_sourcepath}" )
until [[ ${file_size_start} -eq ${file_size_end} ]]; do
  file_size_start=$( stat --printf="%s" "${sonarr_episodefile_sourcepath}" )
  sleep ${unpack_time}
  file_size_end=$( stat --printf="%s" "${sonarr_episodefile_sourcepath}" )
done
echo "[Torrent Cleanup] Finished wait for ${sonarr_episodefile_sourcepath} unpacking..."

# Test for rar and r## files and check the *size* of the biggest one so we don't run due to packed subs or something.
# shellcheck disable=SC2154
if find "${sonarr_episodefile_sourcefolder}" -type f -iregex '.*\.r[0-9a][0-9r]$' | grep -Eq '.*'; then
  # shellcheck disable=SC2154
  rar_size="$( find "${sonarr_episodefile_sourcefolder}" -type f -iregex '.*\.r[0-9a][0-9r]$' -ls | sort -nk 7 | tail -1 | awk '{ print $7 }' )"
  if [[ ${rar_size} -gt ${rar_min_size} ]]; then
    echo "[Torrent Cleanup] Rar file size ${rar_size} exceeds minimum of ${rar_min_size}, deleting video file."
    rm "${sonarr_episodefile_sourcepath}"
  else
    echo "[Torrent Cleanup] Rar file size ${rar_size} DOES NOT MEET minimum of ${rar_min_size}, skipping deletion of video file."
  fi
else
  echo "[Torrent Cleanup] No rar files, exiting."
fi
