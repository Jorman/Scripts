#!/usr/bin/env python3

import time
import sys
import os
import math
from datetime import datetime
from typing import List
import logging
from logging.handlers import RotatingFileHandler
from urllib3.util.retry import Retry
import requests
import apprise
from requests.adapters import HTTPAdapter
from requests import Session

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
        logger.info("Log file configured in: %s", log_file)
    except Exception as e:
        logger.error("Log file configuration error: %s", e)

# ============= CUSTOM EXCEPTION =============
class ConnectionFailureException(Exception):
    """Raised when connection to Sonarr/Radarr fails"""
    pass

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

    DELETE_IF_UNMONITORED_MOVIE = os.environ.get('DELETE_IF_UNMONITORED_MOVIE', 'false').lower() == 'true'

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

    # Notification configuration
    APPRISE_URLS = os.getenv('APPRISE_URLS', '')
    PUSHOVER_USER_KEY = os.getenv('PUSHOVER_USER_KEY', '')
    PUSHOVER_APP_TOKEN = os.getenv('PUSHOVER_APP_TOKEN', '')

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
                logger.error("Environment variable %s must be set.", field)
                sys.exit(1)

        radarr_used = Config.RADARR_HOST is not None
        sonarr_used = Config.SONARR_HOST is not None

        if not radarr_used and not sonarr_used:
            logger.error("At least one of RADARR_HOST or SONARR_HOST must be set.")
            sys.exit(1)

        if radarr_used and not sonarr_used:
            if Config.RADARR_API_KEY is None or Config.RADARR_CATEGORY is None:
                logger.error("When using Radarr, RADARR_API_KEY and RADARR_CATEGORY must be set.")
                sys.exit(1)

            Config.SONARR_HOST = None
            Config.SONARR_API_KEY = None
            Config.SONARR_CATEGORY = None

        if sonarr_used and not radarr_used:
            if Config.SONARR_API_KEY is None or Config.SONARR_CATEGORY is None:
                logger.error("When using Sonarr, SONARR_API_KEY and SONARR_CATEGORY must be set.")
                sys.exit(1)

            Config.RADARR_HOST = None
            Config.RADARR_API_KEY = None
            Config.RADARR_CATEGORY = None

        # New validation for *_HOST variables
        host_variables = ['RADARR_HOST', 'SONARR_HOST', 'EMULERR_HOST']

        for host_var in host_variables:
            host_value = os.environ.get(host_var)
            if host_value and not host_value.startswith(('http://', 'https://')):
                logger.error("Environment variable %s must start with 'http://' or 'https://'.", host_var)
                sys.exit(1)

    @staticmethod
    def get_notification_urls():
        """
        Get Apprise notification URLs.

        Priority:
        1. APPRISE_URLS if set
        2. Auto-convert PUSHOVER_* variables to Apprise format if both are set

        Returns:
            list: List of Apprise-compatible notification URLs
        """
        urls = []

        # Ora possiamo usare Config. in modo pulito
        if Config.APPRISE_URLS:
            urls.extend([
                u.strip() 
                for u in Config.APPRISE_URLS.replace(',', ' ').split() 
                if u.strip()
            ])
            logger.info(f"Using APPRISE_URLS: {len(urls)} notification service(s) configured")
            return urls

        if Config.PUSHOVER_USER_KEY and Config.PUSHOVER_APP_TOKEN:
            pushover_url = f"pover://{Config.PUSHOVER_USER_KEY}@{Config.PUSHOVER_APP_TOKEN}"
            urls.append(pushover_url)
            logger.info("Auto-converting PUSHOVER_* environment variables to Apprise format")
            logger.info("Tip: Consider using APPRISE_URLS=pover://user_key@app_token for better clarity")
            return urls

        return urls

class EmulerrDownload:
    def __init__(self, file_data: dict):
        self.name = file_data.get('name', '')
        self.hash = file_data.get('hash', '')
        self.size = file_data.get('size', 0)
        self.size_done = file_data.get('size_done', 0)
        self.progress = file_data.get('progress', 0) * 100  # notare che viene moltiplicato per 100
        self.status = file_data.get('status_str', '')
        self.src_count = file_data.get('src_count', 0)
        self.src_count_a4af = file_data.get('src_count_a4af', 0)
        self.last_seen_complete = file_data.get('last_seen_complete', 0)
        self.category = file_data.get('meta', {}).get('category', 'unknown')
        self.addedOn = file_data.get('meta', {}).get('addedOn', 0)

    def __repr__(self):
        return (
            f"EmulerrDownload(name={self.name!r}, hash={self.hash!r}, size={self.size}, "
            f"size_done={self.size_done}, progress={self.progress}, status={self.status!r}, "
            f"src_count={self.src_count}, src_count_a4af={self.src_count_a4af}, "
            f"last_seen_complete={self.last_seen_complete}, category={self.category!r}, "
            f"addedOn={self.addedOn})"
        )

class SonarrDownload:
    def __init__(self, record_data: dict):
        self.title = record_data.get('sourceTitle', '')
        self.downloadId = record_data.get('downloadId', '')
        self.download_client = record_data.get('downloadClientName', '')
        self.id = record_data.get('id', '')

        # Assicuriamoci che size sia un intero
        try:
            self.size = int(record_data.get('size', 0))
        except (ValueError, TypeError):
            self.size = 0

        self.series_id = record_data.get('seriesId', None)
        self.season_number = record_data.get('seasonNumber', None)
        self.episode_id = record_data.get('episodeId', None)

    def __repr__(self):
        return (
            f"SonarrDownload(title={self.title!r}, downloadId={self.downloadId!r}, "
            f"download_client={self.download_client!r}, id={self.id!r}, size={self.size}, "
            f"series_id={self.series_id!r}, season_number={self.season_number!r}, "
            f"episode_id={self.episode_id!r})"
        )

class RadarrDownload:
    def __init__(self, record_data: dict):
        self.title = record_data.get('sourceTitle', '')
        self.downloadId = record_data.get('downloadId', '')
        self.download_client = record_data.get('downloadClientName', '')
        self.id = record_data.get('id', '')

        # Convertiamo size in intero, nel caso non lo sia già
        try:
            self.size = int(record_data.get('size', 0))
        except (ValueError, TypeError):
            self.size = 0

        self.movie_id = record_data.get('movieId', None)

    def __repr__(self):
        return (
            f"RadarrDownload(title={self.title!r}, downloadId={self.downloadId!r}, "
            f"download_client={self.download_client!r}, id={self.id!r}, size={self.size}, "
            f"movie_id={self.movie_id!r})"
        )

def check_special_cases(emulerr_data):
    """
    Processes the list of incomplete downloads:
      - For each download makes a paged request to the 'history' endpoint to get the records.
      - If no valid records (eventType "grabbed" and downloadClientName == Config.DOWNLOAD_CLIENT)
        is found, the download is considered present only on eMulerr and added to emulerr_downloads_to_remove.
      - If a valid record is present, an object is created (RadarrDownload or SonarrDownload)
        which also includes a reference to the original download and the valid record, and is added to the relevant queue.

      Next, for each object in the queues:
      - For Radarr: if the movie is not monitored (verified via is_movie_monitored), the original download
        is added to sonarr_radarr_downloads_to_remove.
      - For Sonarr: if the series, season or episode is not monitored (verified via respective functions),
        the original download is added to sonarr_radarr_downloads_to_remove.

      Returns a tuple with:
        (emulerr_downloads_to_remove, sonarr_radarr_downloads_to_remove)
    """
    # Output lists
    emulerr_downloads_to_remove = []
    sonarr_radarr_downloads_to_remove = []
    sonarr_queue = []
    radarr_queue = []

    def get_history_records(download, host, api_key, full_hash, page_size=10):
        headers = {
            "accept": "application/json",
            "X-Api-Key": api_key
        }
        all_records = []
        page = 1

        while True:
            history_url = f"{host}/api/v3/history?page={page}&pageSize={page_size}&downloadId={full_hash}"
            try:
                response = requests.get(history_url, headers=headers, timeout=10)
                
                # 🔥 GESTIONE ERRORI DI CONNESSIONE
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code} for '{download.name}' from {history_url}"
                    logger.error(error_msg)
                    raise ConnectionFailureException(error_msg)

                page_data = response.json()
                
            except requests.exceptions.Timeout:
                error_msg = f"Timeout connecting to {host} for '{download.name}'"
                logger.error(error_msg)
                raise ConnectionFailureException(error_msg)
                
            except requests.exceptions.ConnectionError:
                error_msg = f"Connection refused to {host} for '{download.name}'"
                logger.error(error_msg)
                raise ConnectionFailureException(error_msg)
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Request failed for '{download.name}': {e}"
                logger.error(error_msg)
                raise ConnectionFailureException(error_msg)
                
            except Exception as e:
                error_msg = f"Unexpected error during history request for '{download.name}': {e}"
                logger.error(error_msg)
                raise ConnectionFailureException(error_msg)

            records = page_data.get("records", [])
            all_records.extend(records)

            total_records = page_data.get("totalRecords", 0)
            total_pages = math.ceil(total_records / page_size)

            logger.debug("Page %s/%s for '%s', records obtained: %s", page, total_pages, download.name, len(records))

            if page >= total_pages:
                break
            page += 1

        return all_records

    def get_series_monitor_status(host, api_key, series_id):
        """Gets series monitoring status."""
        logger.debug("Getting series monitor status for series_id: %s", series_id)
        url = f"{host}/api/v3/series/{series_id}"
        headers = {"X-Api-Key": api_key}
        try:
            response = requests.get(url, headers=headers)
            logger.debug("Series API response status code: %s", response.status_code)
            if response.status_code == 200:
                series = response.json()
                logger.debug("Series monitored status: %s", series.get('monitored'))
                logger.debug("Number of seasons: %s", len(series.get('seasons', [])))
                return series.get('monitored', False), series.get('seasons', [])
            else:
                logger.error("Error in retrieving series information. Status code: %s", response.status_code)
                return False, []
        except Exception as e:
            logger.error("Error in retrieving series information: %s", e)
            return False, []

    def get_season_number_for_episode(sonarr_host, sonarr_api_key, episode_id):
        """
        Retrieve the season number of the episode using the Sonarr API.

        Args:
            sonarr_host (str): base URL of the Sonarr instance (e.g., "http://localhost:8989")
            sonarr_api_key (str): API Key for the Sonarr instance.
            episode_id (int): ID of the episode to be queried.

        Returns:
            int or None: The season number if found, otherwise None.
        """
        url = f"{sonarr_host}/api/v3/episode/{episode_id}"
        params = {
            "apikey": sonarr_api_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            season_number = data.get("seasonNumber")
            if season_number is None:
                logger.error("Season number not found for episode %s in the answer: %s", episode_id, data)
            else:
                logger.debug("Season number for the episode %s: %s", episode_id, season_number)
            return season_number

        except requests.RequestException as e:
            logger.error("Error when calling Sonarr for the episode. %s: %s", episode_id, e)
            return None

    def get_season_monitor_status(seasons, season_number):
        """Gets the status of monitoring the season."""
        logger.debug("Getting season monitor status for season_number: %s", season_number)
        for season in seasons:
            logger.debug("Checking season %s", season.get('seasonNumber'))
            if season.get('seasonNumber') == season_number:
                logger.debug("Season monitored status: %s", season.get('monitored'))
                return season.get('monitored', False)
        logger.debug("No season found with number %s", season_number)
        return False

    def get_episode_monitor_status(host, api_key, episode_id):
        """Gets the status of episode monitoring."""
        logger.debug("Getting episode monitor status for episode_id: %s", episode_id)
        url = f"{host}/api/v3/episode/{episode_id}"
        headers = {"X-Api-Key": api_key}
        try:
            response = requests.get(url, headers=headers)
            logger.debug("Episode API response status code: %s", response.status_code)
            if response.status_code == 200:
                episode = response.json()
                logger.debug("Episode monitored status: %s", episode.get('monitored'))
                return episode.get('monitored', False)
            else:
                logger.error("Error in retrieving episode information. Status code: %s", response.status_code)
                return False
        except Exception as e:
            logger.error("Error in retrieving episode information: %s", e)
            return False

    def is_movie_monitored(host, api_key, movie_id):
        """Check if the film is monitored."""
        logger.debug("Checking movie monitor status for movie_id: %s", movie_id)
        url = f"{host}/api/v3/movie/{movie_id}"
        headers = {"X-Api-Key": api_key}
        try:
            response = requests.get(url, headers=headers)
            logger.debug("Movie API response status code: %s", response.status_code)
            if response.status_code == 200:
                movie = response.json()
                logger.debug("Movie monitored status: %s", movie.get('monitored'))
                return movie.get('monitored', False)
            else:
                logger.error("Error in retrieving film information. Status Code: %s", response.status_code)
                return False
        except Exception as e:
            logger.error("Error in retrieving film information: %s", e)
            return False

    # First loop: processes each download by querying the history.
    for download in emulerr_data:
        # Constructs the full hash: assuming 32 characters + "00000000"
        full_hash = download.hash + "00000000"

        # Determines the client and connection details based on the category set in Config.
        client = None
        host = None
        api_key = None

        if Config.RADARR_CATEGORY is not None and download.category == Config.RADARR_CATEGORY:
            client = "radarr"
            host = Config.RADARR_HOST
            api_key = Config.RADARR_API_KEY
        elif Config.SONARR_CATEGORY is not None and download.category == Config.SONARR_CATEGORY:
            client = "sonarr"
            host = Config.SONARR_HOST
            api_key = Config.SONARR_API_KEY
        else:
            logger.warning(
                f"Category '{download.category}' does not match either RADARR_CATEGORY or SONARR_CATEGORY defined in Config.. "
                f"Skip processing for downloading '{download.name}'."
            )
            continue

        # history_records = get_history_records(download, host, api_key, full_hash)

        # 🔥 CONNECTION EXCEPTION HANDLING - INTERRUPTS THE LOOP
        try:
            history_records = get_history_records(download, host, api_key, full_hash)
        except ConnectionFailureException as e:
            logger.error(f"🚨 Connection failure detected for '{download.name}': {e}")
            logger.warning(f"⚠️ Interrupting current check cycle. Will retry in {Config.CHECK_INTERVAL} minutes.")
            
            # 📢 Notifica Pushover (opzionale, come da tua scelta B)
            send_notification(
                f"⚠️ Connection failure to {client.upper()}\n"
                f"Download: {download.name}\n"
                f"Will retry in {Config.CHECK_INTERVAL} minutes",
                dry_run=Config.DRY_RUN
            )
            
            break  # ← INTERRUPTS THE FOR LOOP COMPLETELY

        valid_record = None
        # Search for the first valid record
        for record in history_records:
            if record.get("eventType") != "grabbed":
                continue
            data = record.get("data", {})
            if data.get("downloadClientName") == Config.DOWNLOAD_CLIENT:
                valid_record = record
                break

        if valid_record is None:
            logger.info(
                f"Records present for '{download.name}' (hash: {download.hash}), but no one meets the criteria. "
                "Download considered present only on eMulerr."
            )
            emulerr_downloads_to_remove.append(download)
            continue

        # If a valid record is present, creates the specific object and retains the record for later checking
        if client == "radarr":
            r_download = RadarrDownload(valid_record)
            radarr_queue.append(r_download)
        elif client == "sonarr":
            s_download = SonarrDownload(valid_record)
            sonarr_queue.append(s_download)

    # Second step: check monitoring for queued downloads.

    # For Radarr: if the movie is not monitored, flag the download for removal.
    for r_obj in radarr_queue:
        # Suppose the record contains "movieId" in data.
        movie_id = r_obj.movie_id
        if not movie_id and Config.DELETE_IF_ONLY_ON_EMULERR:
            logger.info("The record '%s' does not contain 'movieId', it will only be considered on eMulerr.", r_obj.title)
            sonarr_radarr_downloads_to_remove.append(r_obj)
            continue

        if not is_movie_monitored(Config.RADARR_HOST, Config.RADARR_API_KEY, movie_id) and Config.DELETE_IF_UNMONITORED_MOVIE:
            logger.warning("[RADARR] The movie '%s' Is not monitored. It will be marked for removal.", r_obj.title)
            sonarr_radarr_downloads_to_remove.append(r_obj)

    for s_obj in sonarr_queue:
        # Extract the main fields
        series_id = s_obj.series_id
        episode_id = s_obj.episode_id

        # Retrieve the season number using Sonarr's API for the episode.
        season_number = get_season_number_for_episode(Config.SONARR_HOST, Config.SONARR_API_KEY, episode_id)

        # Update the object with the obtained season_number.
        s_obj.season_number = season_number

        if not series_id and Config.DELETE_IF_ONLY_ON_EMULERR:
            logger.warning("The record '%s' does not contain 'seriesId', it will only be considered on eMulerr.", s_obj.title)
            sonarr_radarr_downloads_to_remove.append(s_obj)
            continue

        # Gets series status and season information.
        series_monitored, seasons = get_series_monitor_status(Config.SONARR_HOST, Config.SONARR_API_KEY, series_id)
        if not series_monitored and Config.DELETE_IF_UNMONITORED_SERIE:
            logger.warning("[SONARR] The show '%s' Is not monitored. It will be marked for removal.", s_obj.title)
            sonarr_radarr_downloads_to_remove.append(s_obj)
            continue

        if not episode_id and Config.DELETE_IF_ONLY_ON_EMULERR:
            logger.warning("The record '%s' does not contain 'episodeId', it will only be considered on eMulerr.", s_obj.title)
            sonarr_radarr_downloads_to_remove.append(s_obj)
            continue

        if season_number is None and Config.DELETE_IF_ONLY_ON_EMULERR:
            logger.warning("It was not possible to determine the season number for the episode %s.", episode_id)
            sonarr_radarr_downloads_to_remove.append(s_obj)
            continue

        # Check season tracking using season information.
        if not get_season_monitor_status(seasons, season_number) and Config.DELETE_IF_UNMONITORED_SEASON:
            logger.warning("[SONARR] The season %s for '%s' Is not monitored. It will be marked for removal.", season_number, s_obj.title)
            sonarr_radarr_downloads_to_remove.append(s_obj)
            continue

        # Check the monitoring of the episode
        if not get_episode_monitor_status(Config.SONARR_HOST, Config.SONARR_API_KEY, episode_id) and Config.DELETE_IF_UNMONITORED_EPISODE:
            logger.warning("[SONARR] The episode '%s' Is not monitored. It will be marked for removal.", s_obj.title)
            sonarr_radarr_downloads_to_remove.append(s_obj)

    return emulerr_downloads_to_remove, sonarr_radarr_downloads_to_remove, sonarr_queue, radarr_queue

def emulerr_remove_download(hash_32: str, download_name: str, dry_run: bool = False):
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
            logger.info("%s successfully removed from eMulerr.", download_name)
        except requests.exceptions.RequestException as e:
            logger.error("Error removing '%s': %s", download_name, e)
    else:
        logger.debug("DRY_RUN: Would remove %s from eMulerr.", download_name)

def handle_stalled_download(name: str, queue_id: str, host: str, api_key: str, dry_run: bool = True) -> bool:
    """
    Mark as failed a download (identified by queue_id) using the
    endpoint /api/v3/history/failed/{id}.

    :param name: The name of the download to be marked as failed.
    :param queue_id: The id of the download in the queue (Radarr/Sonarr) to be marked as failed.
    :param host: The base host (URL) of the service (Radarr or Sonarr).
    :param api_key: The API key for authentication.
    :param dry_run: If True, the function only logs the call without executing the action
    :return: True if the operation was successful, False otherwise
    """

    url = f"{host}/api/v3/history/failed/{queue_id}"
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }

    if dry_run:
        logger.info("[DRY RUN] I would mark as failed the download with id %s using: %s", name, url)
        return True

    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            logger.info("%s -> Successfully marked as failed", name)
            return True
        else:
            logger.error("Error in marking as failed the download with id %s: status code %s, response: %s", name, response.status_code, response.text)
            return False
    except Exception as e:
        logger.exception("Exception in marking the download as failed %s: %s", name, e)
        return False


def send_notification(message: str, dry_run: bool = False, title: str = "eMulerr Stalled Checker"):
    """
    Send notification using Apprise.
    
    Supports 70+ notification services via Apprise.
    Automatically converts legacy PUSHOVER_* variables to Apprise format.
    
    Args:
        message (str): Notification message body
        dry_run (bool): If True, log but don't send notification
        title (str): Notification title
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    if dry_run:
        logging.debug(f"[DRY RUN] Notification not sent: {message}")
        return True

    notification_urls = Config.get_notification_urls()
    
    if not notification_urls:
        logging.warning(
            "No notification service configured. "
            "Set APPRISE_URLS environment variable. "
            "Example: APPRISE_URLS=pover://user_key@app_token"
        )
        return False

    try:
        # Create Apprise instance
        apobj = apprise.Apprise()
        
        # Add all configured notification URLs
        added_count = 0
        for url in notification_urls:
            if apobj.add(url):
                added_count += 1
                logging.debug(f"Added notification service: {url[:20]}...")
            else:
                logging.warning(f"Failed to add invalid notification URL: {url[:30]}...")
        
        if added_count == 0:
            logging.error("No valid notification services could be added")
            return False
        
        logging.debug(f"Sending notification to {added_count} service(s)...")
        
        # Send notification
        success = apobj.notify(
            body=message,
            title=title
        )
        
        if success:
            logging.info(f"Notification sent successfully to {added_count} service(s)")
            return True
        else:
            logging.error("Failed to send notification to one or more services")
            return False
            
    except Exception as e:
        logging.error(f"Error sending notification via Apprise: {str(e)}", exc_info=True)
        return False

class StallChecker:
    def __init__(self):
        self.warnings = {}
        self.previous_warnings = set()  # To keep track of downloads previously in warning
        self.previous_downloads = []  # Download history for future reference

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

    def cleanup_warnings(self, current_hashes: set[str], downloads_map: dict):
        # Create a hash -> name mapping dictionary before cleaning
        if not hasattr(self, 'hash_to_name_map'):
            self.hash_to_name_map = {}

        # Let's make sure that stalled_hashes exists
        if not hasattr(self, 'stalled_hashes'):
            self.stalled_hashes = set()

        # Update mapping with all current downloads
        for download in self.previous_downloads:
            self.hash_to_name_map[download.hash] = download.name

        # Also update with new ones in the current map
        for hash_key, download in downloads_map.items():
            self.hash_to_name_map[hash_key] = download.name

        # Remove hash from warnings
        to_remove = [h for h in self.warnings.keys() if h not in current_hashes]
        for h in to_remove:
            # Skip logging for stalled downloads
            if h in self.stalled_hashes:
                del self.warnings[h]
                continue

            if h in downloads_map:
                logger.info("Download '%s' removed from monitoring (no longer on download list)", downloads_map[h].name)
            elif h in self.hash_to_name_map:
                logger.info("Download '%s' removed from monitoring (no longer on download list)", self.hash_to_name_map[h])
            else:
                logger.info("Download with hash %s... removed from monitoring (no longer on download list)", h[:8])
            del self.warnings[h]

        # Update the warnings as usual
        self.previous_warnings = self.previous_warnings.intersection(current_hashes)
        self.previous_downloads = list(downloads_map.values())

def fetch_emulerr_data() -> List[EmulerrDownload]:
    """Retrieve active downloads from server with retry mechanism, filtering by SONARR_CATEGORY or RADARR_CATEGORY"""
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
        logger.debug("Retrieved %s total file%s", len(files), 's' if len(files) != 1 else '')

        # Log categories of all files
        for file in files:
            meta = file.get('meta', {})
            category = meta.get('category', 'Category not found')
            logger.debug("File category: %s", category)

        # Filter downloads based on category
        filtered_downloads = [
            EmulerrDownload(file) for file in files
            if file.get('meta', {}).get('category') in [Config.SONARR_CATEGORY, Config.RADARR_CATEGORY]
        ]

        return filtered_downloads
    except requests.exceptions.RequestException as e:
        logger.error("Error retrieving downloads: %s", e)
        return []

def main():
    stall_checker = StallChecker()

    logger.info("=== Configuration Summary ===")
    for attr, value in Config.__dict__.items():
        if not callable(value) and not attr.startswith("__"):
            logger.info("%s: %s", attr, value)
    logger.info("=== Configuration Summary ===")

    while True:
        try:
            emulerr_data = fetch_emulerr_data()

            # Apply special case checks
            emulerr_downloads_to_remove, sonarr_radarr_downloads_to_remove, sonarr_queue, radarr_queue = check_special_cases(emulerr_data)

            for download in emulerr_downloads_to_remove + sonarr_radarr_downloads_to_remove:

                # If it is an EmulerrDownload, we directly use the 'hash' and 'name' field.
                if isinstance(download, EmulerrDownload):
                    identifier = download.hash  # already in the correct format (32 characters)
                    name = download.name
                # If it is a SonarrDownload or RadarrDownload, we use the downloadId, removing the final 8 zeros if present.
                elif isinstance(download, (SonarrDownload, RadarrDownload)):
                    raw_id = download.downloadId
                    identifier = raw_id[:-8] if raw_id.endswith("00000000") else raw_id
                    name = download.title
                else:
                    logger.debug("Download type not recognized: %s", download)
                    continue

                logger.debug("Removal in progress for: %s, identifier: %s", name, identifier)

                # Invokes the function that removes the download from the server.
                emulerr_remove_download(identifier, name, Config.DRY_RUN)

                # Manually remove the hash from the monitoring if necessary
                if download.hash in stall_checker.warnings:
                    del stall_checker.warnings[download.hash]

                if download.hash in stall_checker.previous_warnings:
                    stall_checker.previous_warnings.remove(download.hash)

                # Removal from local emulerr_data list:
                # If the download is an EmulerrDownload, we remove it directly.
                if isinstance(download, EmulerrDownload):
                    try:
                        emulerr_data.remove(download)
                        logger.debug("Removed correctly %s (EmulerrDownload) from emulerr_data.", name)
                    except ValueError:
                        logger.error("Unable to remove %s from emulerr_data.", name)
                # If the download is of type SonarrDownload or RadarrDownload, we look for the corresponding EmulerrDownload.
                # based on the hash (which is equivalent to the identifier).
                elif isinstance(download, (SonarrDownload, RadarrDownload)):
                    candidate = next(
                        (d for d in emulerr_data if isinstance(d, EmulerrDownload) and d.hash == identifier),
                        None
                    )
                    if candidate:
                        try:
                            emulerr_data.remove(candidate)
                            logger.debug("Removed correctly %s (found EmulerrDownload) from emulerr_data.", name)
                        except ValueError:
                            logger.error("Error in removing %s from emulerr_data, candidate found: %s", name, candidate)
                    else:
                        logger.error("Unable to remove %s from emulerr_data: no EmulerrDownload found with hash %s.", name, identifier)

            # Split emulerr_data into completed and incomplete
            incomplete_downloads = [d for d in emulerr_data if d.progress < 100]
            completed_downloads = [d for d in emulerr_data if d.progress == 100]

            stall_checker.previous_downloads = emulerr_data

            # Handle incomplete downloads
            if incomplete_downloads:
                download_states = {}
                stalled_downloads = []
                warning_downloads = []

                # We store the current hashes in warning
                current_warning_hashes = set()

                logger.debug("\nChecking %s incomplete file%s", len(incomplete_downloads), 's' if len(incomplete_downloads) != 1 else '')

                # Create a hash->download map for better lookups
                downloads_map = {d.hash: d for d in incomplete_downloads}
                current_hashes = set(downloads_map.keys())

                current_hashes = {d.hash for d in incomplete_downloads}

                # Pass the map to cleanup_warnings
                stall_checker.cleanup_warnings(current_hashes, downloads_map)

                # Check the status once for each download
                for download in incomplete_downloads:
                    is_stalled, stall_reason, check_count = stall_checker.check_status(download)
                    download_states[download.hash] = (is_stalled, stall_reason, check_count)

                # Debug output
                if logger.getEffectiveLevel() == logging.DEBUG:
                    for download in incomplete_downloads:
                        is_stalled, stall_reason, check_count = download_states[download.hash]
                        status = f"STALLED: {stall_reason}" if is_stalled else "Active"

                        last_seen = "Never" if download.last_seen_complete == 0 else \
                            datetime.fromtimestamp(download.last_seen_complete).strftime('%Y-%m-%d %H:%M:%S')
                        logger.debug("Download: %s, Status: %s, Last Seen Complete: %s, Check Count: %s", download.name, status, last_seen, check_count)

                # Process each download
                for download in incomplete_downloads:
                    is_stalled, stall_reason, check_count = download_states[download.hash]

                    # If it's not a special case, add to stalled or warning lists
                    if is_stalled or check_count > Config.STALL_CHECKS:
                        stalled_downloads.append((download, check_count, stall_reason or "Max checks reached"))
                    elif check_count > 0:
                        warning_downloads.append((download, check_count, stall_reason or "Approaching stall threshold"))

                # Show warning downloads
                if warning_downloads:
                    logger.debug("Warning downloads (%s/%s):", len(warning_downloads), len(incomplete_downloads))
                    for download, count, warning_reason in warning_downloads:
                        logger.info("%s -> Warning (%s/%s) - %s", download.name, count, Config.STALL_CHECKS, warning_reason)
                        # Add the current hash to those in warnings
                        current_warning_hashes.add(download.hash)
                else:  # If warning is empty
                    logger.debug("No warning downloads")

                # Show stalled downloads
                if stalled_downloads:
                    logger.debug("Stalled downloads (%s/%s):", len(stalled_downloads), len(incomplete_downloads))
                    for download, check_count, stall_reason in stalled_downloads:
                        logger.info("%s -> Stalled (%s/%s warnings) - %s", download.name, check_count, Config.STALL_CHECKS, stall_reason)

                        send_notification(f"Download {download.name} marked as stalled: {stall_reason}. Will be removed", dry_run=Config.DRY_RUN)

                        if Config.RADARR_CATEGORY is not None and download.category == Config.RADARR_CATEGORY:
                            host = Config.RADARR_HOST
                            api_key = Config.RADARR_API_KEY
                            # Look for the RadarrDownload in the global queue.
                            matching_item = next(
                                (item for item in radarr_queue
                                 if (item.downloadId[:-8] == download.hash)),
                                None
                            )
                        elif Config.SONARR_CATEGORY is not None and download.category == Config.SONARR_CATEGORY:
                            host = Config.SONARR_HOST
                            api_key = Config.SONARR_API_KEY
                            # Search for SonarrDownload in the global queue.
                            matching_item = next(
                                (item for item in sonarr_queue 
                                 if (item.downloadId[:-8] == download.hash)),
                                None
                            )
                        else:
                            logger.debug("Category not recognized for %s: %s", download.name, download.category)
                            return

                        if not matching_item:
                            logger.error("Queue item not found for %s (hash: %s)", download.name, download.hash)
                            return

                        # Extracts the id to be used for removal (e.g., RadarrDownload.id or SonarrDownload.id).
                        queue_id = matching_item.id

                        # Invokes the function that removes the download from the server.
                        emulerr_remove_download(download.hash, download.name, Config.DRY_RUN)

                        # We immediately remove the download from the previous warnings.
                        # so that it does not appear as "no longer in warning state"
                        if download.hash in stall_checker.previous_warnings:
                            stall_checker.previous_warnings.remove(download.hash)

                        # We also remove downloading from current warnings.
                        if download.hash in current_warning_hashes:
                            current_warning_hashes.remove(download.hash)

                        # Add the hash of the download to the set of stalled downloads.
                        if not hasattr(stall_checker, 'stalled_hashes'):
                            stall_checker.stalled_hashes = set()
                        stall_checker.stalled_hashes.add(download.hash)

                        handle_stalled_download(download.name, queue_id, host, api_key, Config.DRY_RUN)

                else:  # If stalled is empty
                    logger.debug("No stalled downloads")

                # Check which downloads were previously in warnings but are no longer in warnings
                resolved_warnings = stall_checker.previous_warnings - current_warning_hashes
                for hash_value in resolved_warnings:
                    # Search for the corresponding download to get the name
                    matching_download = next((d for d in incomplete_downloads if d.hash == hash_value), None)
                    if matching_download:
                        logger.info("%s -> No longer in warning state", matching_download.name)

                # Update the set of downloads in warning for the next cycle
                stall_checker.previous_warnings = current_warning_hashes

            else:  # If incomplete_downloads is empty
                logger.debug("No incomplete downloads to check.")

            # Handle completed downloads
            if completed_downloads:
                logger.debug("Checking %s completed file%s", len(completed_downloads), 's' if len(completed_downloads) != 1 else '')
                for download in completed_downloads:
                    logger.debug("Completed download: %s", download.name)
            else:
                logger.debug("No completed downloads to check.")

            logger.debug("Waiting %s minute(s) before next check...", Config.CHECK_INTERVAL)
            time.sleep(Config.CHECK_INTERVAL * 60)

        except KeyboardInterrupt:
            logger.debug("Interrupted by user")
            break
        except Exception as e:
            logger.error("Error in main loop: %s", e)
            time.sleep(Config.CHECK_INTERVAL * 60)

# Call the validation function at the beginning
if __name__ == "__main__":
    try:
        Config.validate()
        main()
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)
