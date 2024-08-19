#!/usr/bin/env python3

########## CONFIGURATIONS ##########
# Host on which qBittorrent runs
qbt_host = "http://10.0.0.100"
# Port -> the same port that is inside qBittorrent option -> Web UI -> Web User Interface
qbt_port = "8081"
# Username to access to Web UI
qbt_username = "admin"
# Password to access to Web UI
qbt_password = "adminadmin"
# If true (lowercase) the script will inject trackers inside private torrent too (not a good idea)
ignore_private = False
# If true (lowercase) the script will remove all existing trackers before inject the new one, this functionality will works only for public trackers
clean_existing_trackers = False
# Configure here your trackers list
live_trackers_list_urls = [
	"https://newtrackon.com/api/stable",
	"https://trackerslist.com/best.txt",
	"https://trackerslist.com/http.txt",
	"https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt",
]
########## CONFIGURATIONS ##########

########## IMPORTS ##########
import qbittorrentapi # type: ignore
import requests # type: ignore
########## IMPORTS ##########

########## VARIABLES ##########
auto_tor_grab=0
test_in_progress=0
applytheforce=0
all_torrent=0
emptycategory=0
########## VARIABLES ##########

########## FUNCTIONS ##########

def generate_trackers_list():
	live_trackers_list = []
	for j in live_trackers_list_urls:
		try:
			response = requests.get(j)
			live_trackers_list.extend(response.text.split())
		except:
			print(f"I can't parse the list from {j}")

	if live_trackers_list == []:
		live_trackers_list = [
			"udp://tracker.coppersurfer.tk:6969/announce",
			"http://tracker.internetwarriors.net:1337/announce",
			"udp://tracker.internetwarriors.net:1337/announce",
			"udp://tracker.opentrackr.org:1337/announce",
			"udp://9.rarbg.to:2710/announce",
			"udp://exodus.desync.com:6969/announce",
			"udp://explodie.org:6969/announce",
			"http://explodie.org:6969/announce",
			"udp://public.popcorn-tracker.org:6969/announce",
			"udp://tracker.vanitycore.co:6969/announce",
			"http://tracker.vanitycore.co:6969/announce",
			"udp://tracker1.itzmx.com:8080/announce",
			"http://tracker1.itzmx.com:8080/announce",
			"udp://ipv4.tracker.harry.lu:80/announce",
			"udp://tracker.torrent.eu.org:451/announce",
			"udp://tracker.tiny-vps.com:6969/announce",
			"udp://tracker.port443.xyz:6969/announce",
			"udp://open.stealth.si:80/announce",
			"udp://open.demonii.si:1337/announce",
			"udp://denis.stalker.upeer.me:6969/announce",
			"udp://bt.xxx-tracker.com:2710/announce",
			"http://tracker.port443.xyz:6969/announce",
			"udp://tracker2.itzmx.com:6961/announce",
			"udp://retracker.lanta-net.ru:2710/announce",
			"http://tracker2.itzmx.com:6961/announce",
			"http://tracker4.itzmx.com:2710/announce",
			"http://tracker3.itzmx.com:6961/announce",
			"http://tracker.city9x.com:2710/announce",
			"http://torrent.nwps.ws:80/announce",
			"http://retracker.telecom.by:80/announce",
			"http://open.acgnxtracker.com:80/announce",
			"wss://ltrackr.iamhansen.xyz:443/announce",
			"udp://zephir.monocul.us:6969/announce",
			"udp://tracker.toss.li:6969/announce",
			"http://opentracker.xyz:80/announce",
			"http://open.trackerlist.xyz:80/announce",
			"udp://tracker.swateam.org.uk:2710/announce",
			"udp://tracker.kamigami.org:2710/announce",
			"udp://tracker.iamhansen.xyz:2000/announce",
			"udp://tracker.ds.is:6969/announce",
			"udp://pubt.in:2710/announce",
			"https://tracker.fastdownload.xyz:443/announce",
			"https://opentracker.xyz:443/announce",
			"http://tracker.torrentyorg.pl:80/announce",
			"http://t.nyaatracker.com:80/announce",
			"http://open.acgtracker.com:1096/announce",
			"wss://tracker.openwebtorrent.com:443/announce",
			"wss://tracker.fastcast.nz:443/announce",
			"wss://tracker.btorrent.xyz:443/announce",
			"udp://tracker.justseed.it:1337/announce",
			"udp://thetracker.org:80/announce",
			"udp://packages.crunchbangplusplus.org:6969/announce",
			"https://1337.abcvg.info:443/announce",
			"http://tracker.tfile.me:80/announce.php",
			"http://tracker.tfile.me:80/announce",
			"http://tracker.tfile.co:80/announce",
			"http://retracker.mgts.by:80/announce",
			"http://peersteers.org:80/announce",
			"http://fxtt.ru:80/announce",
		]

	return live_trackers_list

# def inject_trackers():
