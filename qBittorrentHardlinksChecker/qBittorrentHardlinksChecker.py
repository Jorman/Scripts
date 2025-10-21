#!/usr/bin/env python3

import os
import sys
import argparse
import json
import requests
import yaml
import time
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urljoin
from pathlib import Path
from dataclasses import dataclass
from colorama import init, Fore, Style

init()

class QBittorrentManager:
    def __init__(self, config_file: str, dry_run: bool = False):
        self.dry_run = dry_run
        self._load_config(config_file)
        self._setup_session()

    def _load_config(self, config_file: str) -> None:
        """Load and validate the configuration"""
        with open(config_file) as f:
            config = yaml.safe_load(f)

        # Basic configuration required
        self.host = config['qbt_host']
        self.port = config['qbt_port']
        self.username = config['qbt_username']
        self.password = config['qbt_password']
        self.min_seeding_time = config['min_seeding_time']

        # Optional configuration with default values
        self.categories = config.get('categories', [])
        self.torrent_type = config.get('torrent_type', '')
        self.virtual_path = config.get('virtual_path', '')
        self.real_path = config.get('real_path', '')
        self.enable_recheck = config.get('enable_recheck', True)
        self.enable_orphan_check = config.get('enable_orphan_check', True)
        self.orphan_states = [state.lower() for state in config.get('orphan_states', [])]
        self.min_peers = config.get('min_peers', 1)

        self.enable_auto_update_trackers = config.get('enable_auto-update_trackers', False)
        self.auto_update_trackers_script = config.get('auto-update_trackers_script', '')

        self.base_url = f"{self.host}:{self.port}"
        self.session = requests.Session()

    def _setup_session(self) -> None:
        """Initialize the HTTP session and log in"""
        self.login()

    def login(self) -> None:
        """Log in to qBittorrent"""
        try:
            response = self.session.post(
                urljoin(self.base_url, 'api/v2/auth/login'),
                data={'username': self.username, 'password': self.password}
            )
            if response.text != 'Ok.':
                raise Exception("Login failed")
        except Exception as e:
            print(f"Failed to login: {str(e)}")
            sys.exit(1)

    def get_torrent_list(self) -> List[Dict[str, Any]]:
        """Gets the list of torrents"""
        try:
            torrent_list = []
            # If "All" is specified in the categories, it takes all torrents
            if "All" in self.categories:
                response = self.session.get(urljoin(self.base_url, 'api/v2/torrents/info'))
            else:
                # Gets the torrents for each specified category
                for category in self.categories:
                    if category == "Uncategorized":
                        # For torrents without category
                        response = self.session.get(urljoin(self.base_url, 'api/v2/torrents/info'), 
                                                 params={'category': ''})
                    else:
                        response = self.session.get(urljoin(self.base_url, 'api/v2/torrents/info'), 
                                                 params={'category': category})
                    torrent_list.extend(response.json())
                return torrent_list

            return response.json()
        except Exception as e:
            print(f"Failed to get torrent list: {str(e)}")
            return []

    def get_torrent_properties(self, torrent_hash: str) -> Dict[str, Any]:
        """Gets the properties of a specific torrent"""
        try:
            response = self.session.get(
                urljoin(self.base_url, 'api/v2/torrents/properties'),
                params={'hash': torrent_hash}
            )
            return response.json()
        except Exception as e:
            print(f"Failed to get torrent properties: {str(e)}")
            return {}

    def recheck_torrent(self, torrent_hash: str) -> None:
        """Double-check a torrent"""
        try:
            if self.dry_run:
                print(f"[DRY-RUN] Would recheck torrent with hash {torrent_hash}")
                return
            self.session.post(
                urljoin(self.base_url, 'api/v2/torrents/recheck'),
                data={'hashes': torrent_hash}
            )
            print(f"Rechecking torrent with hash {torrent_hash}")
        except Exception as e:
            print(f"Failed to recheck torrent: {str(e)}")

    def reannounce_torrent(self, torrent_hash: str) -> None:
        """Performs reannounce of a torrent"""
        try:
            if self.dry_run:
                print(f"[DRY-RUN] Reannouncing torrent with hash {torrent_hash}")
                return
            self.session.post(
                urljoin(self.base_url, 'api/v2/torrents/reannounce'),
                data={'hashes': torrent_hash}
            )
            print(f"Reannouncing torrent with hash {torrent_hash}")
        except Exception as e:
            print(f"Failed to reannounce torrent: {str(e)}")

    def delete_torrent(self, torrent_hash: str) -> None:
        """Remove a torrent"""
        try:
            if self.dry_run:
                print(f"[DRY-RUN] Torrent with hash {torrent_hash} deleted")
                return
            self.session.post(
                urljoin(self.base_url, 'api/v2/torrents/delete'),
                data={'hashes': torrent_hash, 'deleteFiles': True}
            )
            print(f"Torrent with hash {torrent_hash} deleted")
        except Exception as e:
            print(f"Failed to delete torrent: {str(e)}")

    def check_hardlinks(self, path: str) -> bool:
        """Check if a file has hardlinks"""
        try:
            if os.path.isfile(path):
                return os.stat(path).st_nlink > 1
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if os.stat(os.path.join(root, file)).st_nlink > 1:
                            return True
            return False
        except Exception as e:
            print(f"Failed to check hardlinks: {str(e)}")
            return False

    def check_bad_trackers(self, torrent: Dict[str, Any]) -> Dict[str, str]:
        """Check problematic trackers"""
        bad_trackers = {}
        try:
            response = self.session.get(
                urljoin(self.base_url, 'api/v2/torrents/trackers'),
                params={'hash': torrent['hash']}
            )
            trackers = response.json()
            
            for tracker in trackers:
                if tracker.get('status') == 4:
                    bad_trackers[tracker['url']] = tracker.get('msg', 'Unknown error')
            
            return bad_trackers
        except Exception as e:
            print(f"Failed to check trackers: {str(e)}")
            return {}

    def remove_trackers(self, torrent_hash: str, trackers: Dict[str, str]) -> None:
        """Removes specified trackers"""
        try:
            if self.dry_run:
                print(f"- [DRY-RUN] Bad tracker{'s' if len(trackers) > 1 else ''} removed")
                return
            for tracker in trackers:
                self.session.post(
                    urljoin(self.base_url, 'api/v2/torrents/removeTrackers'),
                    data={'hash': torrent_hash, 'urls': tracker}
                )
            print(f"- Bad tracker{'s' if len(trackers) > 1 else ''} removed")
        except Exception as e:
            print(f"Failed to remove trackers: {str(e)}")

    def run_tracker_update_script(self, torrent_hash: str, torrent_name: str) -> None:
        """Execute tracker update script for the specified torrent using the torrent name"""
        try:
            if self.dry_run:
                print(f"- [DRY-RUN] Would run tracker update script for torrent: {torrent_name}")
                return
            
            import subprocess
            
            # Utilizziamo il nome del torrent con l'argomento -n
            command = [self.auto_update_trackers_script, "-n", torrent_name]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )
                        
            if result.returncode == 0:
                print(f"- Tracker update script executed successfully")
            else:
                print(f"- Tracker update script failed: {result.stderr.strip() or result.stdout.strip()}")
        except Exception as e:
            print(f"Failed to run tracker update script: {str(e)}")

    def _print_configuration(self) -> None:
        """Print the current configuration"""
        print("\nCurrent configuration:")
        print(f"- Host: {self.host}:{self.port}")
        print(f"- Username: {self.username}")
        print(f"- Password: {'*' * len(self.password)}")
        print(f"- Processing: {'Only ' + self.torrent_type if self.torrent_type else 'Private & Public'} torrents")
        print(f"- Categories: {', '.join(self.categories) if self.categories else 'All'}")
        print(f"- Minimum seeding time: {self.min_seeding_time} seconds")
        print(f"- Minimum peers: {self.min_peers}")
        print(f"- Virtual path: {self.virtual_path if self.virtual_path else 'not set'}")
        print(f"- Real path: {self.real_path if self.real_path else 'not set'}")
        print(f"- Enable recheck: {self.enable_recheck}")
        print(f"- Enable orphan check: {self.enable_orphan_check}")
        print(f"- Orphan states: {self.orphan_states if self.orphan_states else 'not set'}")

        print(f"- Auto-update trackers: {self.enable_auto_update_trackers}")
        if self.enable_auto_update_trackers:
            print(f"- Update script: {self.auto_update_trackers_script}")

        if self.dry_run:
            print(f"{Fore.GREEN}- DRY-RUN mode enabled{Style.RESET_ALL}")
        print("\nProcessing only selected torrents...")

    def process_torrents(self) -> None:
        """Process all torrents"""
        torrents = self.get_torrent_list()
        self._print_configuration()

        for torrent in torrents:

            properties = self.get_torrent_properties(torrent['hash'])
            is_private = properties.get('is_private', False)

            print(f"\nTorrent -> {Fore.CYAN if is_private else Fore.GREEN}{torrent['name']}{Style.RESET_ALL} ({('private' if is_private else 'public')})")

            if self.torrent_type == 'private' and not is_private:
                print("Skipping further checks: torrent is public but only private torrents are configured")
                continue
            elif self.torrent_type == 'public' and is_private:
                print("Skipping further checks: torrent is private but only public torrents are configured")
                continue

            # Control recheck
            if self.enable_recheck:
                print("- Checking for errors ->", end=" ")
                if torrent.get('state') in ["error", "missingFiles"]:
                    print(f"{Fore.RED}errors found, forcing recheck{Style.RESET_ALL}")
                    self.recheck_torrent(torrent['hash'])
                else:
                    print(f"{Fore.GREEN}no errors found{Style.RESET_ALL}")

            # Tracker check
            if not is_private:
                print("- Checking for bad trackers ->", end=" ")
                bad_trackers = self.check_bad_trackers(torrent)
                if bad_trackers:
                    print(f"{Fore.YELLOW}{len(bad_trackers)} bad tracker{'s' if len(bad_trackers) > 1 else ''} found:{Style.RESET_ALL}")
                    for tracker, error in bad_trackers.items():
                        print(f"   {tracker} -> {Fore.RED}{error}{Style.RESET_ALL}")
                    self.remove_trackers(torrent['hash'], bad_trackers)
                else:
                    print(f"{Fore.GREEN}no bad trackers found{Style.RESET_ALL}")

            # Orphan check
            if self.enable_orphan_check and is_private:
                print("- Checking for orphan status ->", end=" ")
                trackers = self.session.get(
                    urljoin(self.base_url, 'api/v2/torrents/trackers'),
                    params={'hash': torrent['hash']}
                ).json()

                is_orphan = False
                for tracker in trackers:
                    if any(state in tracker.get('msg', '').lower() for state in self.orphan_states):
                        if torrent.get('num_leechs', 0) < self.min_peers:
                            is_orphan = True
                            break

                if is_orphan:
                    print(f"{Fore.RED}orphan detected{Style.RESET_ALL}")
                    self.reannounce_torrent(torrent['hash'])
                    time.sleep(2)
                    self.delete_torrent(torrent['hash'])
                else:
                    print("no orphan detected")

            # Tracker update script
            if self.enable_auto_update_trackers and not is_private and torrent['progress'] != 1:
                print("- Running tracker update script ->", end=" ")
                if self.auto_update_trackers_script:
                    self.run_tracker_update_script(torrent['hash'], torrent['name'])
                else:
                    print("script path not configured")

            # Controllo hardlink
            content_path = torrent.get('content_path', '')
            if content_path:
                if torrent['progress'] != 1:
                    print("- Skipping hardlink check: torrent not downloaded")
                    continue

                print("- Checking for hardlinks ->", end=" ")
                if self.virtual_path and self.real_path:
                    content_path = content_path.replace(self.virtual_path, self.real_path)

                has_hardlinks = self.check_hardlinks(content_path)
                seeding_time = properties['seeding_time']

                if has_hardlinks:
                    print("hardlinks found, nothing to do")
                    continue
                else:
                    if self.min_seeding_time > 0 and seeding_time < self.min_seeding_time:
                        print(f"no hardlinks found but I can't delete this torrent, seeding time not met -> {seeding_time}/{self.min_seeding_time}")
                        continue

                    print(f"no hardlinks found deleting torrent...")
                    self.reannounce_torrent(torrent['hash'])
                    time.sleep(2)
                    self.delete_torrent(torrent['hash'])

DEFAULT_CONFIG = """# qBittorrent server configuration
qbt_host: "http://localhost" # Server address (with http/https).
qbt_port: "8081"             # Web UI Port
qbt_username: "admin"        # Web UI Username
qbt_password: "adminadmin"   # Web UI Password

# Configuration torrent management
# Minimum seeding time in seconds (ex: 259200 = 3 days).
# Set to 0 if you want to disable the min_seeding_time check
min_seeding_time: 864000

# List of categories to be processed.
# Use ["All"] for all categories.
# Use ["Uncategorized"] for torrents without category.
# Or specify categories: ["movies", "tv", "books"]
categories:
  - "All"

# Type of torrent to be processed
# Options: "private", "public" or blank "" to process all.
torrent_type: ""

# Configuring paths (useful with Docker)
virtual_path: ""   # Examample: "/downloads" in Docker
real_path: ""      # Example: "/home/user/downloads" real path on the system

# Automatic controls
enable_recheck: true        # Enable automatic recheck torrent in error.
enable_orphan_check: true   # Enable orphan torrent checking, works only on private torrents

# States that identify a torrent as orphaned.
orphan_states:
  - "unregistered"
  - "not registered"
  - "not found"
  - "not working"

# Minimum number of peers before considering a torrent orphaned.
# Default: 1
min_peers: 1"""

def create_default_config(config_path: str) -> None:
    """Creates a default configuration file"""
    if os.path.exists(config_path):
        raise FileExistsError(f"Configuration file already exists: {config_path}")
    
    with open(config_path, 'w') as f:
        f.write(DEFAULT_CONFIG)
    
    print(f"Default configuration file created: {config_path}")

def get_default_config_name() -> str:
    """Get the default configuration file name based on the script name"""
    script_name = os.path.basename(sys.argv[0])
    base_name = os.path.splitext(script_name)[0]
    return f"{base_name}_config.yaml"

def validate_config_file(config_path: str) -> None:
    """Validates the existence and format of the configuration file"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    if not path.suffix.lower() == '.yaml':
        raise ValueError("The configuration file must be in YAML format")

def parse_arguments() -> argparse.Namespace:
    """Parsing of command line arguments"""
    parser = argparse.ArgumentParser(
        description='QBittorrent Manager - Automated torrent management'
    )

    parser.add_argument(
        '-c', '--config',
        default=get_default_config_name(),
        help='YAML configuration file path (default: <script_name>_config.yaml)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in simulation mode (no actual changes)'
    )

    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create a default configuration file'
    )

    return parser.parse_args()

def main() -> None:
    try:
        args = parse_arguments()

        if args.create_config:
            create_default_config(args.config)
            return

        validate_config_file(args.config)
        manager = QBittorrentManager(args.config, args.dry_run)
        manager.process_torrents()
    except FileExistsError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Use --create-config to create a default configuration file")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation aborted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
