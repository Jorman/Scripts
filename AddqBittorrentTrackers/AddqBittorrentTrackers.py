#!/usr/bin/env python3

import sys
import importlib

required_packages = [
    'requests',  # Not included in Python standard library
]

def check_dependencies():
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("The following dependencies are missing:")
        for package in missing_packages:
            print(f"- {package}")
        print("\nTo install them, you can use the command:")
        print(f"pip install {' '.join(missing_packages)}")
        sys.exit(1)

########## CONFIGURATIONS ##########
qbt_host = "http://10.0.0.100"
qbt_port = "8081"
qbt_username = "admin"
qbt_password = "adminadmin"

ignore_private = False
clean_existing_trackers = False

exclude_download_client = "emulerr" # If not empty, download clients to exclude must be comma separated

live_trackers_list_urls = [
    "https://newtrackon.com/api/stable",
    "https://trackerslist.com/best.txt",
    "https://trackerslist.com/http.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt",
]

version = "v1.1"

STATIC_TRACKERS_LIST = """
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
"""

########## FUNCTIONS ##########
def generate_trackers_list():
    # If the URL list is empty, use the static list and return
    if not live_trackers_list_urls or len(live_trackers_list_urls) == 0:
        print("The URL list is empty. Using the static tracker list.")
        return STATIC_TRACKERS_LIST.strip().split("\n")

    trackers_list = ""
    errors_count = 0  # Count how many URLs returned error

    # Itera sugli URL e prova a scaricare i tracker
    for url in live_trackers_list_urls:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check for HTTP errors
            trackers_list += response.text + "\n"  # Add content to the list
        except requests.RequestException as e:
            errors_count += 1
            print(f"Error downloading from {url}: {e}")  # Error log for individual URL

    # If all URLs failed, use static list as fallback
    if errors_count == len(live_trackers_list_urls):
        print("All URLs failed. Using the static tracker list.")
        return STATIC_TRACKERS_LIST.strip().split("\n")

    return trackers_list.strip().split("\n")

def get_qbittorrent_session(qbt_host, qbt_port, qbt_username, qbt_password):
    url = f"{qbt_host}:{qbt_port}"
    session = requests.Session()
    try:
        response = session.post(f'{url}/api/v2/auth/login', data={'username': qbt_username, 'password': qbt_password})
        response.raise_for_status()
        return session
    except requests.exceptions.RequestException as e:
        print(f"Error during authentication: {e}")
        return None

def get_torrent_trackers(session, hash):
    try:
        response = session.get(
            f"{qbt_host}:{qbt_port}/api/v2/torrents/trackers?hash={hash}",
        )
        response.raise_for_status()
        return json.loads(response.text)
    except Exception as e:
        print(f"An error occurred while getting torrent trackers: {e}")
        return None

def inject_trackers(hash, session):
    print("Injecting... ", end="")

    trackers_data = get_torrent_trackers(session, hash)
    if trackers_data is None:
        print(" Error getting torrent trackers... ")
    torrent_trackers = [tracker["url"] for tracker in trackers_data[3:]]

    remove_trackers(hash, torrent_trackers, session)

    trackers_list = generate_trackers_list()

    if clean_existing_trackers:
        print(" But before a quick cleaning the existing trackers... ")
        trackers_list = sorted(set(trackers_list))
    else:
        trackers_list = sorted(set(trackers_list + torrent_trackers))

    trackers_list = [tracker for tracker in trackers_list if tracker.strip()]

    number_of_trackers_in_list = len(trackers_list)

    # Format trackers into tiers
    formatted_trackers = ""
    for tracker in trackers_list:
        formatted_trackers += f"{tracker}\n\n"

    # Remove the last newlines if any
    formatted_trackers = formatted_trackers.rstrip("\n")

    response = session.post(
        f"{qbt_host}:{qbt_port}/api/v2/torrents/addTrackers",
        data={"hash": hash, "urls": formatted_trackers},
    )
    response.raise_for_status()

    print(f"done, injected {number_of_trackers_in_list} tracker{'s' if number_of_trackers_in_list > 1 else ''}!")

def get_torrent_list(session):
    response = session.get(
        f"{qbt_host}:{qbt_port}/api/v2/torrents/info",
    )
    response.raise_for_status()
    return json.loads(response.text)

def hash_check(hash):
    if not hash or any(c not in '0123456789ABCDEFabcdef' for c in hash):
        return False
    return len(hash) in (32, 40)

def remove_trackers(hash, urls, session):
    urls_string = "|".join(urls)
    response = session.post(
        f"{qbt_host}:{qbt_port}/api/v2/torrents/removeTrackers",
        data={"hash": hash, "urls": urls_string},
    )
    response.raise_for_status()

def check_torrent_privacy(session, torrent_hash):
    try:
        response = session.get(
            f"{qbt_host}:{qbt_port}/api/v2/torrents/properties?hash={torrent_hash}",
        )
        response.raise_for_status()
        private_check = json.loads(response.text)["is_private"]
        return private_check
    except Exception as e:
        print(f"An error occurred while checking torrent privacy: {e}")
        return None  # Or any other value to signify an error

def parse_arguments():
    import argparse

    parser = argparse.ArgumentParser(description="How to Inject trackers into qBittorrent")
    parser.add_argument("-a", action="store_true", help="Inject trackers to all torrent in qBittorrent, this not require any extra information")
    parser.add_argument("-c", action="store_true", help="Clean all the existing trackers before the injection, this not require any extra information")
    parser.add_argument("-f", action="store_true", help="Force the injection of the trackers inside the private torrent too, this not require any extra information")
    parser.add_argument("-l", action="store_true", help="Print the list of the torrent where you can inject trackers, this not require any extra information")
    parser.add_argument("-n", action="append", help="Specify the torrent name or part of it, for example -n foo or -n 'foo bar'")
    parser.add_argument("-s", action="append", help="Specify the exact category name, for example -s foo or -s 'foo bar'. If -s is passed empty, \"\", the \"Uncategorized\" category will be used")

    args = parser.parse_args()

    if not sys.stdin.isatty() and not any(os.path.abspath('.').lower().startswith(p) for p in ["qbittorrent"]):
        if args.f and len(sys.argv) == 2:
            print("Don't use only -f, you need to specify also the torrent!")
            sys.exit(1)
    else:
        if not any(arg.startswith('-') for arg in sys.argv[1:]):
            print("Arguments must be passed with - in front, like -n foo. Check instructions")
            parser.print_help()
            sys.exit(1)

        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(0)

    if args.n:
        for name in args.n:
            if not name.strip():
                print("One or more arguments for -n not valid, try again")
                sys.exit(1)

    return args

########## MAIN ##########
if __name__ == "__main__":

    check_dependencies()

    import os
    import sys
    import requests
    import json
    import urllib.parse
    import time

    args = parse_arguments()

    all_torrent = args.a
    clean_existing_trackers = args.c
    applytheforce = args.f
    list_torrents = args.l
    tor_arg_names = args.n or []
    tor_categories = args.s or []

    if not sys.stdin.isatty() and not any(os.path.abspath('.').lower().startswith(p) for p in ["qbittorrent"]):
        event_types = ["sonarr_eventtype", "radarr_eventtype", "lidarr_eventtype", "readarr_eventtype"]
        download_clients = ["sonarr_download_client", "radarr_download_client", "lidarr_download_client", "readarr_download_client"]
        download_ids = ["sonarr_download_id", "radarr_download_id", "lidarr_download_id", "readarr_download_id"]

        if any(os.environ.get(event_type) == "Test" for event_type in event_types):
            print("Test in progress... Good-bye!")
            sys.exit(0)

        if exclude_download_client:
            exclude_clients = exclude_download_client.split(',')
            exclude_clients = [client.strip() for client in exclude_clients if client.strip()]

            # Check clients to exclude only if exclude_download_client is not empty
            for download_client in download_clients:
                client = os.environ.get(download_client)
                if client and client in exclude_clients:
                    print(f"Exiting because {download_client} matches an excluded client: {client}")
                    sys.exit(4)

        session = get_qbittorrent_session(qbt_host, qbt_port, qbt_username, qbt_password)

        if session:
            # Controlling download_ids
            for download_id in download_ids:
                hash = os.environ.get(download_id)
                if hash:
                    print(f"{download_id.replace('_download_id', '').capitalize()} variable found -> {hash}")
                    hash = hash.lower()
                    if hash_check(hash):
                        print(f"I'll wait 5s to be sure ...")
                        time.sleep(5)

                        torrent_list = get_torrent_list(session)

                        private_check = check_torrent_privacy(session, hash)

                        if private_check and not (ignore_private or applytheforce):
                            trackers_data = get_torrent_trackers(session, hash)

                            if trackers_data is None:
                                print("Error getting torrent trackers.")
                            else:
                                private_tracker_name = trackers_data[3]["url"].split("//")[1].split("@")[-1].split(":")[0]
                                print(f"< Private tracker found -> {private_tracker_name} <- I'll not add any extra tracker >")
                        else:
                            if ignore_private and not applytheforce:
                                print("ignore_private set to true, I'll inject trackers anyway")
                            elif applytheforce:
                                print("Force mode is active, I'll inject trackers anyway")
                            else:
                                print("The torrent is not private, I'll inject trackers on it")
                            inject_trackers(hash, session)
                        break
                    else:
                        print("No valid hash found for the torrent, I'll exit")
                        sys.exit(3)
        else:
            print("Failed to authenticate with qBittorrent.")
    else:
        session = get_qbittorrent_session(qbt_host, qbt_port, qbt_username, qbt_password)

        if session:
            if list_torrents:
                torrent_list = get_torrent_list(session)
                print(f"\n{len(torrent_list)} active torrent{'s' if len(torrent_list) > 1 else ''}:")
                for torrent in torrent_list:
                    print(f"Name: {torrent['name']}, Category: {torrent['category'] if torrent['category'] else 'Uncategorized'}")
                sys.exit(0)

            torrent_list = get_torrent_list(session)

            torrent_name_array = []
            torrent_hash_array = []

            if all_torrent:
                for torrent in torrent_list:
                    torrent_name_array.append(torrent["name"])
                    torrent_hash_array.append(torrent["hash"])
            else:
                if tor_arg_names and tor_categories:
                    for name in tor_arg_names:
                        for category in tor_categories:
                            filtered_torrents = [t for t in torrent_list if t["category"].lower() == category.lower() and name.lower() in t["name"].lower()]
                            if filtered_torrents:
                                print(f"\nFor the name ### {name} ### in category ### {'Uncategorized' if category == '' else category} ###")
                                print(f"I found {len(filtered_torrents)} torrent{'s' if len(filtered_torrents) > 1 else ''}:")
                                for torrent in filtered_torrents:
                                    print(torrent["name"])
                                    torrent_name_array.append(torrent["name"])
                                    torrent_hash_array.append(torrent["hash"])
                            else:
                                print(f"\nI didn't find a torrent with name ### {name} ### in category ### {'Uncategorized' if category == '' else category} ###")
                elif tor_arg_names:
                    for name in tor_arg_names:
                        filtered_torrents = [t for t in torrent_list if name.lower() in t["name"].lower()]
                        if filtered_torrents:
                            print(f"\nFor the name ### {name} ###")
                            print(f"I found {len(filtered_torrents)} torrent{'s' if len(filtered_torrents) > 1 else ''}:")
                            for torrent in filtered_torrents:
                                print(torrent["name"])
                                torrent_name_array.append(torrent["name"])
                                torrent_hash_array.append(torrent["hash"])
                        else:
                            print(f"\nI didn't find a torrent with this part of the text: {name}")
                else:
                    for category in tor_categories:
                        filtered_torrents = [t for t in torrent_list if t["category"].lower() == category.lower()]
                        if filtered_torrents:
                            print(f"\nFor category ### {'Uncategorized' if category == '' else category} ###")
                            print(f"I found {len(filtered_torrents)} torrent{'s' if len(filtered_torrents) > 1 else ''}:")
                            for torrent in filtered_torrents:
                                print(torrent["name"])
                                torrent_name_array.append(torrent["name"])
                                torrent_hash_array.append(torrent["hash"])
                        else:
                            print(f"\nI didn't find a torrent in the category: {'Uncategorized' if category == '' else category}")

            if torrent_name_array:
                for i, name in enumerate(torrent_name_array):
                    print(f"\nFor the Torrent: {name}")

                    if ignore_private or applytheforce:
                        if applytheforce:
                            print("Force mode is active, I'll inject trackers anyway")
                        else:
                            print("ignore_private set to true, I'll inject trackers anyway")
                        inject_trackers(torrent_hash_array[i], session)
                    else:
                        private_check = check_torrent_privacy(session, torrent_hash_array[i])
                        if private_check:
                            trackers_data = get_torrent_trackers(session, torrent_hash_array[i])
                            if trackers_data is None:
                                print("Error getting torrent trackers.")
                            else:
                                private_tracker_name = trackers_data[3]["url"].split("//")[1].split("@")[-1].split(":")[0]
                                print(f"< Private tracker found -> {private_tracker_name} <- I'll not add any extra tracker >")
                        else:
                            print("The torrent is not private, I'll inject trackers on it")
                            inject_trackers(torrent_hash_array[i], session)
            else:
                print("Exiting")
                sys.exit(1)
        else:
            print("Failed to authenticate with qBittorrent.")
