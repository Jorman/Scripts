#!/usr/bin/env python3

import time
import requests
from requests.adapters import HTTPAdapter
from requests import Session
import os
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from typing import Union, List, Dict, Any, Tuple
import logging
from logging.handlers import RotatingFileHandler
import sys

# Sets the logging level based on the environment variable LOG_LEVEL
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
numeric_level = getattr(logging, log_level, None)
if not isinstance(numeric_level, int):
	raise ValueError(f'Invalid log level: {log_level}')

# Get the environment variable for the log file directly
log_to_file_path = os.getenv("LOG_TO_FILE", "")

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(numeric_level)

# Make sure there are no duplicate handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Log format
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Handler for the console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# Handler for the file if specified
if log_to_file_path:
    try:
        # Make sure the directory exists
        os.makedirs(log_to_file_path, exist_ok=True)
        
        # Create the full path to the log file inside that directory
        log_file = os.path.join(log_to_file_path, "emulerr_stalled_checker.log")
        
        # Use this full path to the log file
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=2 * 1024 * 1024,  # 2 MB
            backupCount=6,
            encoding="utf-8"
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
        logger.info(f"Log file configured in: {log_file}")
    except Exception as e:
        print(f"Log file configuration error: {e}")

class Config:
	# All environment variables must be provided by docker-compose.yml
	DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true'  # flags for dry running

	EMULERR_ENDPOING = '/download-client?_data=routes%2F_shell.download-client'
	EMULERR_HOST = f"{os.environ.get('EMULERR_HOST', '')}"

	CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL'))  # in minutes
	STALL_CHECKS = int(os.environ.get('STALL_CHECKS'))  # number of checks before considering stall
	STALL_DAYS = int(os.environ.get('STALL_DAYS'))  # days after which a complete visa file is considered stalled
	RECENT_DOWNLOAD_GRACE_PERIOD = int(os.environ.get('RECENT_DOWNLOAD_GRACE_PERIOD', '30'))  # in minutes

	# New configuration options for monitoring checks
	DELETE_IF_UNMONITORED_SERIE = os.environ.get('DELETE_IF_UNMONITORED_SERIE', 'false').lower() == 'true'
	DELETE_IF_UNMONITORED_SEASON = os.environ.get('DELETE_IF_UNMONITORED_SEASON', 'false').lower() == 'true'
	DELETE_IF_UNMONITORED_EPISODE = os.environ.get('DELETE_IF_UNMONITORED_EPISODE', 'false').lower() == 'true'
	DELETE_IF_ONLY_ON_EMULERR = os.environ.get('DELETE_IF_ONLY_ON_EMULERR', 'false').lower() == 'true'

	# Download client name
	DOWNLOAD_CLIENT = os.environ.get('DOWNLOAD_CLIENT', '')  # download client name in Sonarr/Radarr

	# Radarr config (optional)
	RADARR_HOST = os.environ.get('RADARR_HOST', None)
	RADARR_API_KEY = os.environ.get('RADARR_API_KEY', None)
	RADARR_CATEGORY = os.environ.get('RADARR_CATEGORY', None)  # category for Radarr downloads
	
	# Sonarr config (optional)
	SONARR_HOST = os.environ.get('SONARR_HOST', None)
	SONARR_API_KEY = os.environ.get('SONARR_API_KEY', None)
	SONARR_CATEGORY = os.environ.get('SONARR_CATEGORY', None)  # category for Sonarr downloads

	# Pushover configuration
	PUSHOVER_APP_TOKEN = os.environ.get('PUSHOVER_APP_TOKEN', '')
	PUSHOVER_USER_KEY = os.environ.get('PUSHOVER_USER_KEY', '')

	# Assigns API_URL directly in the body of the class
	API_URL = f"{os.environ.get('EMULERR_HOST', '')}{EMULERR_ENDPOING}"

	@staticmethod
	def validate():
		mandatory_fields = [
			'CHECK_INTERVAL', 'API_URL', 'STALL_CHECKS', 'STALL_DAYS', 'DOWNLOAD_CLIENT', 'EMULERR_HOST'
		]

		for field in mandatory_fields:
			value = getattr(Config, field)
			if value is None or value == '':
				logger.error(f"Environment variable {field} must be set.")
				exit(1)

		radarr_used = Config.RADARR_HOST is not None
		sonarr_used = Config.SONARR_HOST is not None

		if not radarr_used and not sonarr_used:
			logger.error("At least one of RADARR_HOST or SONARR_HOST must be set.")
			exit(1)

		if radarr_used and not sonarr_used:
			if Config.RADARR_API_KEY is None or Config.RADARR_CATEGORY is None:
				logger.error("When using Radarr, RADARR_API_KEY and RADARR_CATEGORY must be set.")
				exit(1)

			Config.SONARR_HOST = None
			Config.SONARR_API_KEY = None
			Config.SONARR_CATEGORY = None

		if sonarr_used and not radarr_used:
			if Config.SONARR_API_KEY is None or Config.SONARR_CATEGORY is None:
				logger.error("When using Sonarr, SONARR_API_KEY and SONARR_CATEGORY must be set.")
				exit(1)

			Config.RADARR_HOST = None
			Config.RADARR_API_KEY = None
			Config.RADARR_CATEGORY = None

		# New validation for *_HOST variables
		host_variables = ['RADARR_HOST', 'SONARR_HOST', 'EMULERR_HOST']
		
		for host_var in host_variables:
			host_value = os.environ.get(host_var)
			if host_value and not host_value.startswith(('http://', 'https://')):
				logger.error(f"Environment variable {host_var} must start with 'http://' or 'https://'.")
				exit(1)

class EmulerrDownload:
	def __init__(self, file_data: dict):
		self.name = file_data.get('name', '')
		self.hash = file_data.get('hash', '')
		self.size = file_data.get('size', 0)
		self.size_done = file_data.get('size_done', 0)
		self.progress = file_data.get('progress', 0) * 100
		self.status = file_data.get('status_str', '')
		self.src_count = file_data.get('src_count', 0)
		self.src_count_a4af = file_data.get('src_count_a4af', 0)
		self.last_seen_complete = file_data.get('last_seen_complete', 0)
		self.category = file_data.get('meta', {}).get('category', 'unknown')
		self.addedOn = file_data.get('meta', {}).get('addedOn', 0)

class SonarrDownload:
	def __init__(self, record_data: dict):
		self.title = record_data.get('title', '')
		self.downloadId = record_data.get('downloadId', '')
		self.id = record_data.get('id', '')
		self.size = record_data.get('size', 0)
		self.sizeleft = record_data.get('sizeleft', 0)
		self.progress = (self.size - self.sizeleft) / self.size * 100 if self.size > 0 else 0
		self.series_id = record_data.get('seriesId', None)
		self.season_number = record_data.get('seasonNumber', None)
		self.episode_id = record_data.get('episodeId', None)

class RadarrDownload:
	def __init__(self, record_data: dict):
		self.title = record_data.get('title', '')
		self.downloadId = record_data.get('downloadId', '')
		self.id = record_data.get('id', '')
		self.size = record_data.get('size', 0)
		self.sizeleft = record_data.get('sizeleft', 0)
		self.progress = (self.size - self.sizeleft) / self.size * 100 if self.size > 0 else 0
		self.movie_id = record_data.get('movieId', None)

def check_special_cases(downloads, sonarr_queue, radarr_queue):
    """Check special cases for Sonarr and Radarr, printing alerts for downloads to be removed."""
    emulerr_downloads_to_remove = []
    sonarr_radarr_downloads_to_remove = []

    def find_queue_item_by_hash(hash_value, queue_data):
        """Find the queue element based on the hash."""
        logger.debug(f"Searching for hash {hash_value} in queue of length {len(queue_data)}")
        for item in queue_data:
            logger.debug(f"Checking item with downloadId: {item.downloadId}")
            if item.downloadId == hash_value:
                logger.debug(f"Found item with hash {hash_value}")
                return item
        logger.debug(f"No item found with hash {hash_value}")
        return None

    def get_series_monitor_status(host, api_key, series_id):
        """Gets series monitoring status."""
        logger.debug(f"Getting series monitor status for series_id: {series_id}")
        url = f"{host}/api/v3/series/{series_id}"
        headers = {"X-Api-Key": api_key}
        try:
            response = requests.get(url, headers=headers)
            logger.debug(f"Series API response status code: {response.status_code}")
            if response.status_code == 200:
                series = response.json()
                logger.debug(f"Series monitored status: {series.get('monitored')}")
                logger.debug(f"Number of seasons: {len(series.get('seasons', []))}")
                return series.get('monitored', False), series.get('seasons', [])
            else:
                logger.error(f"Error in retrieving series information. Status code: {response.status_code}")
                return False, []
        except Exception as e:
            logger.error(f"Error in retrieving series information: {e}")
            return False, []

    def get_season_monitor_status(seasons, season_number):
        """Gets the status of monitoring the season."""
        logger.debug(f"Getting season monitor status for season_number: {season_number}")
        for season in seasons:
            logger.debug(f"Checking season {season.get('seasonNumber')}")
            if season.get('seasonNumber') == season_number:
                logger.debug(f"Season monitored status: {season.get('monitored')}")
                return season.get('monitored', False)
        logger.debug(f"No season found with number {season_number}")
        return False

    def get_episode_monitor_status(host, api_key, episode_id):
        """Gets the status of episode monitoring."""
        logger.debug(f"Getting episode monitor status for episode_id: {episode_id}")
        url = f"{host}/api/v3/episode/{episode_id}"
        headers = {"X-Api-Key": api_key}
        try:
            response = requests.get(url, headers=headers)
            logger.debug(f"Episode API response status code: {response.status_code}")
            if response.status_code == 200:
                episode = response.json()
                logger.debug(f"Episode monitored status: {episode.get('monitored')}")
                return episode.get('monitored', False)
            else:
                logger.error(f"Error in retrieving episode information. Status code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error in retrieving episode information: {e}")
            return False

    def is_movie_monitored(host, api_key, movie_id):
        """Check if the film is monitored."""
        logger.debug(f"Checking movie monitor status for movie_id: {movie_id}")
        url = f"{host}/api/v3/movie/{movie_id}"
        headers = {"X-Api-Key": api_key}
        try:
            response = requests.get(url, headers=headers)
            logger.debug(f"Movie API response status code: {response.status_code}")
            if response.status_code == 200:
                movie = response.json()
                logger.debug(f"Movie monitored status: {movie.get('monitored')}")
                return movie.get('monitored', False)
            else:
                logger.error(f"Error in retrieving film information. Status Code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error in retrieving film information: {e}")
            return False

    for download in downloads:
        logger.debug(f"Checking download: {download.name} with hash: {download.hash}")
        if download.category == Config.SONARR_CATEGORY:
            logger.debug(f"Processing Sonarr category for {download.name}")
            queue_item = find_queue_item_by_hash(download.hash, sonarr_queue)
            logger.debug(f"Found Sonarr queue item for {download.name}: {queue_item}")
            if queue_item is None and Config.DELETE_IF_ONLY_ON_EMULERR:
                logger.warning(f"[SONARR] Download {download.name} is only in Emulerr. It will be removed from Emulerr.")
                send_pushover_notification(f"[SONARR] Download {download.name} is only in Emulerr. It will be removed from Emulerr.", dry_run=Config.DRY_RUN)
                emulerr_downloads_to_remove.append(download)
            else:
                # Check the monitoring status of the series
                if Config.DELETE_IF_UNMONITORED_SERIE and queue_item.series_id is not None:
                    logger.debug(f"Checking series monitoring status for {download.name} with series_id: {queue_item.series_id}")
                    series_monitored, seasons = get_series_monitor_status(Config.SONARR_HOST, Config.SONARR_API_KEY, queue_item.series_id)
                    logger.debug(f"Series monitoring status for {download.name}: {series_monitored}")
                    if not series_monitored:
                        logger.warning(f"[SONARR] Series for {download.name} is not monitored. It will be removed from Sonarr queue.")
                        send_pushover_notification(f"[SONARR] Series for {download.name} is not monitored. It will be removed from Sonarr queue.", dry_run=Config.DRY_RUN)
                        sonarr_radarr_downloads_to_remove.append(download)
                        continue

                # Check the monitoring status of the season
                if Config.DELETE_IF_UNMONITORED_SEASON and queue_item.season_number is not None:
                    logger.debug(f"Checking season monitoring status for {download.name} with season_number: {queue_item.season_number}")
                    season_monitored = get_season_monitor_status(seasons, queue_item.season_number)
                    logger.debug(f"Season monitoring status for {download.name}: {season_monitored}")
                    if not season_monitored:
                        logger.warning(f"[SONARR] Season for {download.name} is not monitored. It will be removed from Sonarr queue.")
                        send_pushover_notification(f"[SONARR] Season for {download.name} is not monitored. It will be removed from Sonarr queue.", dry_run=Config.DRY_RUN)
                        sonarr_radarr_downloads_to_remove.append(download)
                        continue

                # Check the monitoring status of the episode
                if Config.DELETE_IF_UNMONITORED_EPISODE and queue_item.episode_id is not None:
                    logger.debug(f"Checking episode monitoring status for {download.name} with episode_id: {queue_item.episode_id}")
                    episode_monitored = get_episode_monitor_status(Config.SONARR_HOST, Config.SONARR_API_KEY, queue_item.episode_id)
                    logger.debug(f"Episode monitoring status for {download.name}: {episode_monitored}")
                    if not episode_monitored:
                        logger.warning(f"[SONARR] Episode for {download.name} is not monitored. It will be removed from Sonarr queue.")
                        send_pushover_notification(f"[SONARR] Episode for {download.name} is not monitored. It will be removed from Sonarr queue.", dry_run=Config.DRY_RUN)
                        sonarr_radarr_downloads_to_remove.append(download)
                        continue

        elif download.category == Config.RADARR_CATEGORY:
            logger.debug(f"Processing Radarr category for {download.name}")
            queue_item = find_queue_item_by_hash(download.hash, radarr_queue)
            logger.debug(f"Found Radarr queue item for {download.name}: {queue_item}")
            if queue_item is None and Config.DELETE_IF_ONLY_ON_EMULERR:
                logger.warning(f"[RADARR] Download {download.name} is only in Emulerr. It will be removed from Emulerr.")
                send_pushover_notification(f"[RADARR] Download {download.name} is only in Emulerr. It will be removed from Emulerr.", dry_run=Config.DRY_RUN)
                emulerr_downloads_to_remove.append(download)
            elif queue_item is not None:
                logger.debug(f"[RADARR] Download {download.name} found in Radarr queue.")

                # Check the monitoring status of the film
                logger.debug(f"Checking movie monitoring status for {download.name}")
                logger.debug(f"Queue item for {download.name}: {queue_item.__dict__}")
                if queue_item.movie_id is not None:
                    logger.debug(f"Checking movie monitoring status for {download.name} with movie_id: {queue_item.movie_id}")
                    movie_monitored = is_movie_monitored(Config.RADARR_HOST, Config.RADARR_API_KEY, queue_item.movie_id)
                    logger.debug(f"Movie monitoring status for {download.name}: {movie_monitored}")
                    if not movie_monitored:
                        logger.warning(f"[RADARR] Movie {download.name} is not monitored. It will be removed from Radarr queue.")
                        send_pushover_notification(f"[RADARR] Movie {download.name} is not monitored. It will be removed from Radarr queue.", dry_run=Config.DRY_RUN)
                        sonarr_radarr_downloads_to_remove.append(download)
                else:
                    logger.warning(f"[RADARR] Movie ID for {download.name} is None. Skipping movie check.")
            else:
                logger.error(f"[RADARR] Queue item for {download.name} is None. Cannot check movie monitoring status.")

    return emulerr_downloads_to_remove, sonarr_radarr_downloads_to_remove

def emulerr_remove_download(hash_32: str, dry_run: bool = False) -> Dict[str, Any]:
	url = f"{Config.EMULERR_HOST}/api/v2/torrents/delete?_data=routes%2Fapi.v2.torrents.delete"
	headers = {
		'Content-Type': 'application/x-www-form-urlencoded'
	}
	data = {
		'_data': 'routes/api.v2.torrents.delete',
		'hashes': hash_32.upper()
	}

	if not dry_run:
		try:
			response = requests.post(url, headers=headers, data=data)
			response.raise_for_status()
			result = response.json()
			result['status_code'] = response.status_code
			return result
		except requests.exceptions.RequestException as e:
			logger.error(f"Error removing download: {e}")
			return {"error": str(e), "status_code": e.response.status_code if e.response else None}
	else:
		logger.debug(f"DRY_RUN: Would remove download with hash: {hash_32}")
		return {"dry_run": True, "message": "Download removal simulated", "status_code": 200}

def fetch_history(host: str, api_key: str, target_hash: str):
	headers = {'X-Api-Key': api_key}
	page = 1

	while True:
		url = f"{host}/api/v3/history?page={page}"
		try:
			response = requests.get(url, headers=headers)
			response.raise_for_status()
			data = response.json()

			records = data.get('records', [])
			if not records:
				break

			for record in records:
				if record.get('downloadId') == target_hash:
					return [record]

			page += 1

		except requests.exceptions.RequestException as e:
			logger.error(f"Error retrieving history page {page}: {e}")
			break

	return []

def find_grab_id_by_hash(hash_32: str, host: str, api_key: str) -> int:
	hash_40 = hash_32.ljust(40, '0')
	history_records = fetch_history(host, api_key, hash_40)

	if history_records:
		record = history_records[0]
		logger.debug(f"Matching grab found. Grab ID: {record['id']}")
		return record['id']

	logger.debug(f"No matching grab found for hash: {hash_40}")
	return None

def mark_as_failed(download: EmulerrDownload, host: str, api_key: str, dry_run: bool = True) -> bool:

	if dry_run:
		logger.debug(f"[DRY RUN] Would mark download {download.name} as failed")
		return True

	grab_id = find_grab_id_by_hash(download.hash, host, api_key)
	
	if grab_id is None:
		return False

	url = f"{host}/api/v3/history/failed/{grab_id}"
	headers = {'X-Api-Key': api_key}

	try:
		response = requests.post(url, headers=headers)

		if response.status_code == 200:
			logger.debug(f"Download {download.name} has been marked as failed.")
			return True
		else:
			logger.error(f"Failed to mark download {download.name} as failed. Status: {response.status_code}")
			return False
	except Exception as e:
		logger.error(f"Error marking download as failed: {e}")
		return False

def remove_download(download: Union[SonarrDownload, RadarrDownload, EmulerrDownload], queue_id: int, host: str, api_key: str, dry_run: bool = True) -> bool:
	if dry_run:
		logger.debug(f"[DRY RUN] Would remove download {download.name} from queue")
		return True

	url = f"{host}/api/v3/queue/{queue_id}"
	headers = {'X-Api-Key': api_key}
	params = {
		'removeFromClient': 'true',
		'blocklist': 'false'
	}

	try:
		response = requests.delete(url, headers=headers, params=params)
		response.raise_for_status()
		logger.debug(f"Successfully removed download {download.name} from queue")
		return True
	except requests.exceptions.RequestException as e:
		logger.error(f"Error removing download: {e}")
		return False

def handle_stalled_download(download: EmulerrDownload, sonarr_queue, radarr_queue, dry_run: bool = True) -> None:
	"""Handle a stalled download"""

	# Determine which host and api_key to use based on the category
	if Config.SONARR_CATEGORY is not None and download.category == Config.SONARR_CATEGORY:
		host = Config.SONARR_HOST
		api_key = Config.SONARR_API_KEY
		queue = sonarr_queue
	elif Config.RADARR_CATEGORY is not None and download.category == Config.RADARR_CATEGORY:
		host = Config.RADARR_HOST
		api_key = Config.RADARR_API_KEY
		queue = radarr_queue
	else:
		logger.debug(f"Unknown category: {download.category}")
		return

	# First mark as failed
	if mark_as_failed(download, host, api_key, dry_run):
		logger.debug(f"{'[DRY RUN] ' if dry_run else ''}Successfully marked {download.name} as failed")

		# Find the corresponding queue item
		queue_item = next((item for item in queue if item.downloadId == download.hash), None)
		if queue_item:
			# Then remove from queue
			if remove_download(download, queue_item.id, host, api_key, dry_run):
				logger.debug(f"{'[DRY RUN] ' if dry_run else ''}Successfully removed {download.name} from queue")
			else:
				logger.error(f"Failed to remove download {download.name} from queue")
		else:
			logger.error(f"Could not find queue item for download: {download.name}")
	else:
		logger.error(f"Failed to handle stalled download {download.name}")

	time.sleep(5)

def send_pushover_notification(message: str, dry_run: bool = False):
	if dry_run:
		logger.debug(f"Dry run is active. Pushover notification not sent: {message}")
		return

	if Config.PUSHOVER_APP_TOKEN and Config.PUSHOVER_USER_KEY:
		try:
			response = requests.post("https://api.pushover.net/1/messages.json", data={
				"token": Config.PUSHOVER_APP_TOKEN,
				"user": Config.PUSHOVER_USER_KEY,
				"message": message
			})
			response.raise_for_status()
			logger.debug(f"Pushover notification sent successfully: {message}")
		except requests.RequestException as e:
			logger.error(f"Failed to send Pushover notification: {str(e)}")
	else:
		logger.warning("Pushover notification not sent because PUSHOVER_APP_TOKEN or PUSHOVER_USER_KEY is not set.")

class StallChecker:
	def __init__(self):
		self.warnings = {}

	def check_status(self, download: EmulerrDownload) -> tuple[bool, str, int]:
		current_hash = download.hash

		added_on = download.addedOn / 1000  # Convert to seconds
		recent_download_threshold = time.time() - (Config.RECENT_DOWNLOAD_GRACE_PERIOD * 60)
		if added_on > recent_download_threshold:
			if current_hash in self.warnings:
				del self.warnings[current_hash]
			return False, "", 0

		# Check if src_count_a4af > 0
		if download.src_count_a4af > 0:
			if current_hash in self.warnings:
				del self.warnings[current_hash]
			return False, "", 0

		# Check if download is 100% complete
		if download.progress >= 100:
			if current_hash in self.warnings:
				del self.warnings[current_hash]
			return False, "", 0

		# Check if size_done has changed
		if current_hash in self.warnings and download.size_done != self.warnings[current_hash]['last_size']:
			del self.warnings[current_hash]
			return False, "", 0

		if download.last_seen_complete == 0:
			reason = "Never seen complete"
			if current_hash in self.warnings:
				# Increment check_count if size_done hasn't changed
				self.warnings[current_hash]['count'] += 1
				self.warnings[current_hash]['last_size'] = download.size_done
				count = self.warnings[current_hash]['count']

				if count > Config.STALL_CHECKS:
					return True, reason, count
				else:
					return False, reason, count
			else:
				# Add to warnings if not previously warned
				self.warnings[current_hash] = {'count': 1, 'last_size': download.size_done}
				return False, reason, 1

		# Rule 3: If last_seen_complete > STALL_DAYS
		if download.last_seen_complete > 0:
			stall_time = time.time() - (Config.STALL_DAYS * 24 * 60 * 60)
			if download.last_seen_complete < stall_time:
				reason = f"Last seen complete > {Config.STALL_DAYS} days ago"
				if current_hash in self.warnings:
					# Increment check_count if size_done hasn't changed
					self.warnings[current_hash]['count'] += 1
					self.warnings[current_hash]['last_size'] = download.size_done
					count = self.warnings[current_hash]['count']

					if count > Config.STALL_CHECKS:
						return True, reason, count
					else:
						return False, reason, count
				else:
					# Add to warnings if not previously warned
					self.warnings[current_hash] = {'count': 1, 'last_size': download.size_done}
					return False, reason, 1
			else:
				if current_hash in self.warnings:
					del self.warnings[current_hash]
				return False, "", 0

		return False, "", 0

	def cleanup_warnings(self, current_hashes: set[str]):
		to_remove = [h for h in self.warnings.keys() if h not in current_hashes]

		for h in to_remove:
			del self.warnings[h]

def fetch_emulerr_data() -> List[EmulerrDownload]:
    """Retrieve active downloads from server with retry mechanism"""
    session = Session()
    retry_strategy = Retry(
        total=10,  # Maximum number of attempts
        backoff_factor=30,  # Interval of 30 second between attempts
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        response = session.get(Config.API_URL)
        response.raise_for_status()  # This throws an exception for incorrect HTTP status codes
        data = response.json()
        files = data.get('files', [])
        logger.debug(f"Retrieved {len(files)} total file{'s' if len(files) != 1 else ''}")
        downloads = [EmulerrDownload(file) for file in files]
        return downloads
    except requests.exceptions.RequestException as e:
        logger.error(f"Error retrieving downloads: {e}")
        return []

def fetch_sonarr_queue() -> List[SonarrDownload]:
	"""Retrieve active downloads from Sonarr, handling pagination with the new URL parameters."""
	page = 1
	all_downloads = []
	previous_page_data = None

	# Prepare headers for the request
	headers = {
		"accept": "application/json",
		"X-Api-Key": Config.SONARR_API_KEY,
	}

	while True:
		try:
			# Dynamic construction of the URL with the required parameters
			url = (
				f"{Config.SONARR_HOST}/api/v3/queue?"
				f"page={page}"
				f"&pageSize=20"
				f"&includeUnknownMovieItems=true"
				f"&includeMovie=true"
				f"&status=unknown"
				f"&status=queued"
				f"&status=paused"
				f"&status=downloading"
				f"&status=completed"
				f"&status=failed"
				f"&status=warning"
				f"&status=delay"
				f"&status=downloadClientUnavailable"
				f"&status=fallback"
			)
			logger.debug(f"[DEBUG] Sonarr - Request URL: {url}")

			response = requests.get(url, headers=headers)
			logger.debug(f"[DEBUG] Sonarr - Status code received: {response.status_code}")

			if response.status_code == 200:
				data = response.json()
				records = data.get('records', [])
				logger.debug(f"[DEBUG] Sonarr - Number of records on the page {page}: {len(records)}")

				# Compares the downloadIds of the current page with those of the previous page to avoid endless loops
				current_page_data = [record.get('downloadId') for record in records]
				logger.debug(f"[DEBUG] Sonarr - downloadId on the page {page}: {current_page_data}")

				if current_page_data == previous_page_data:
					logger.debug("[DEBUG] Sonarr - The downloadIds are the same as the previous page, I break the cycle.")
					break

				# Creates SonarrDownload objects for each record received
				downloads = [SonarrDownload(record) for record in records]
				all_downloads.extend(downloads)

				# If the page contains less than 20 records, it is assumed to have reached the last page
				if len(records) < 20:
					logger.debug("[DEBUG] Sonarr - Less than 20 records, probably the last page. I interrupt the cycle.")
					break

				previous_page_data = current_page_data
				page += 1
			else:
				logger.error(f"Failed to retrieve queue from Sonarr. Status code: {response.status_code}")
				break
		except Exception as e:
			logger.error(f"Error retrieving queue from Sonarr: {e}")
			break

	logger.debug(f"[DEBUG] Sonarr - Totale download recuperati: {len(all_downloads)}")
	return all_downloads

def fetch_radarr_queue() -> List[RadarrDownload]:
	"""Retrieve active downloads from Radarr, handling pagination with the new URL parameters"""
	page = 1
	all_downloads = []
	previous_page_data = None

	# Prepare headers for the request
	headers = {
		"accept": "application/json",
		"X-Api-Key": Config.RADARR_API_KEY,
	}

	while True:
		try:
			# Construct the URL with the required parameters
			url = (
				f"{Config.RADARR_HOST}/api/v3/queue?"
				f"page={page}"
				f"&pageSize=10"
				f"&includeUnknownMovieItems=true"
				f"&includeMovie=true"
				f"&status=unknown"
				f"&status=queued"
				f"&status=paused"
				f"&status=downloading"
				f"&status=completed"
				f"&status=failed"
				f"&status=warning"
				f"&status=delay"
				f"&status=downloadClientUnavailable"
				f"&status=fallback"
			)
			logger.debug(f"[DEBUG] URL request: {url}")

			response = requests.get(url, headers=headers)
			logger.debug(f"[DEBUG] Status code received: {response.status_code}")

			if response.status_code == 200:
				data = response.json()
				records = data.get('records', [])
				logger.debug(f"[DEBUG] Number of records on the page {page}: {len(records)}")

				# We compare the downloadId of the current page with those of the previous page
				current_page_data = [record.get('downloadId') for record in records]
				logger.debug(f"[DEBUG] downloadId in the page {page}: {current_page_data}")

				if current_page_data == previous_page_data:
					logger.debug("[DEBUG] The downloadIds are the same as the previous page, I break the cycle.")
					break  # Exit the loop if the data is the same as the previous page

				downloads = [RadarrDownload(record) for record in records]
				all_downloads.extend(downloads)

				if len(records) < 10:  # If the page contains less than 10 records, I consider the last page
					logger.debug("[DEBUG] Less than 10 records, probably the last page. I interrupt the cycle.")
					break

				previous_page_data = current_page_data
				page += 1
			else:
				logger.error(f"Failed to retrieve queue from Radarr. Status code: {response.status_code}")
				break
		except Exception as e:
			logger.error(f"Error retrieving queue from Radarr: {e}")
			break

	logger.debug(f"[DEBUG] Totale download recuperati: {len(all_downloads)}")
	return all_downloads

def initialize_data():
	emulerr_data = fetch_emulerr_data()
	sonarr_queue = fetch_sonarr_queue()
	radarr_queue = fetch_radarr_queue()
	return emulerr_data, sonarr_queue, radarr_queue

def main():
	stall_checker = StallChecker()

	logger.info("=== Configuration Summary ===")
	for attr, value in Config.__dict__.items():
		if not callable(value) and not attr.startswith("__"):
			logger.info(f"{attr}: {value}")
	
	logger.info("=== Configuration Summary ===")

	while True:
		try:
			emulerr_data, sonarr_queue, radarr_queue = initialize_data()

			# Retrieve all downloads and filter by progress and category
			categories = []
			if Config.RADARR_CATEGORY is not None:
				categories.append(Config.RADARR_CATEGORY)
			if Config.SONARR_CATEGORY is not None:
				categories.append(Config.SONARR_CATEGORY)

			downloads = [d for d in emulerr_data if d.progress < 100 and d.category in categories]

			if downloads:  # Check if downloads is not empty
				logger.debug(f"Checking {len(downloads)} eligible file{'s' if len(downloads) != 1 else ''}")

				current_hashes = {d.hash for d in downloads}
				stall_checker.cleanup_warnings(current_hashes)

				# Apply special case checks
				emulerr_downloads_to_remove, sonarr_radarr_downloads_to_remove = check_special_cases(downloads, sonarr_queue, radarr_queue)

				for download in emulerr_downloads_to_remove:
					logger.debug(f"Download only on eMulerr to be removed: {download.name}, with hash: {download.hash}")
					result = emulerr_remove_download(download.hash, Config.DRY_RUN)
					if not Config.DRY_RUN:  # If it is not a simulation
						if isinstance(result, dict) and 'error' in result:
							logger.error(f"Error removing download: {result['error']}")
						else:
							logger.debug(f"Successfully removed download {download.name}. Response: {result}")
					else:
						logger.debug(f"DRY_RUN: Simulated removal of download {download.name}. Response: {result}")
					downloads.remove(download)  # Removes the download from the list of downloads

				# Removes downloads from Sonarr or Radarr
				for download in sonarr_radarr_downloads_to_remove:
					if download.category == Config.SONARR_CATEGORY:
						logger.debug(f"Download on Sonarr to be removed: {download.name}, with hash: {download.hash}")
						queue_item = next((item for item in sonarr_queue if item.downloadId == download.hash), None)
						if queue_item:
							remove_download(download, queue_item.id, Config.SONARR_HOST, Config.SONARR_API_KEY, Config.DRY_RUN)
						else:
							logger.error(f"Could not find queue item for download on Sonarr: {download.name}")
					elif download.category == Config.RADARR_CATEGORY:
						logger.debug(f"Download on Radarr to be removed: {download.name}, with hash: {download.hash}")
						queue_item = next((item for item in radarr_queue if item.downloadId == download.hash), None)
						if queue_item:
							remove_download(download, queue_item.id, Config.RADARR_HOST, Config.RADARR_API_KEY, Config.DRY_RUN)
						else:
							logger.error(f"Could not find queue item for download on Radarr: {download.name}")
					downloads.remove(download)  # Removes the download from the list of downloads

				# Check the status once for each download
				download_states = {}
				for download in downloads:
					is_stalled, stall_reason, check_count = stall_checker.check_status(download)
					download_states[download.hash] = (is_stalled, stall_reason, check_count)

				stalled_downloads = []
				warning_downloads = []

				# Debug output
				if logger.getEffectiveLevel() == logging.DEBUG:
					for download in downloads:
						is_stalled, stall_reason, check_count = download_states[download.hash]
						status = f"STALLED: {stall_reason}" if is_stalled else "Active"

						last_seen = "Never" if download.last_seen_complete == 0 else \
							datetime.fromtimestamp(download.last_seen_complete).strftime('%Y-%m-%d %H:%M:%S')

				# Process each download
				for download in downloads:
					is_stalled, stall_reason, check_count = download_states[download.hash]

					# If it's not a special case, add to stalled or warning lists
					if is_stalled or check_count > Config.STALL_CHECKS:
						stalled_downloads.append((download, check_count, stall_reason or "Max checks reached"))
					elif check_count > 0:
						warning_downloads.append((download, check_count, stall_reason or "Approaching stall threshold"))

				# Show warning downloads
				if warning_downloads:
					logger.debug(f"Warning downloads ({len(warning_downloads)}/{len(downloads)}):")
					for download, count, warning_reason in warning_downloads:
						logger.debug(f"{download.name} -> Warning ({count}/{Config.STALL_CHECKS}) - {warning_reason}")
				else:  # If warning is empty
					logger.debug("No warning downloads")

				# Show stalled downloads
				if stalled_downloads:
					logger.debug(f"Stalled downloads ({len(stalled_downloads)}/{len(downloads)}):")
					for download, check_count, stall_reason in stalled_downloads:
						logger.info(f"{download.name} -> Warning ({check_count}/{Config.STALL_CHECKS}) - STALLED ({stall_reason})")
						# Handle the stalled download
						send_pushover_notification(f"Download {download.name} marked as stalled: {stall_reason}. Will be removed", dry_run=Config.DRY_RUN)
						handle_stalled_download(download, sonarr_queue, radarr_queue, Config.DRY_RUN)
				else:  # If stalled is empty
					logger.debug("No stalled downloads")

			else:  # If downloads is empty
				logger.debug("No downloads to check.")
			
			logger.debug(f"Waiting {Config.CHECK_INTERVAL} minute(s) before next check...")
			time.sleep(Config.CHECK_INTERVAL * 60)

		except KeyboardInterrupt:
			logger.debug("Interrupted by user")
			break
		except Exception as e:
			logger.error(f"Error in main loop: {e}")
			time.sleep(Config.CHECK_INTERVAL * 60)

# Call the validation function at the beginning of your program
if __name__ == "__main__":
	try:
		Config.validate()
		main()
	except ValueError as e:
		logger.error(f"Configuration error: {e}")
		exit(1)