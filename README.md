# Home Server, Media & Automation Scripts

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Discussions](https://img.shields.io/badge/GitHub-Discussions-blue.svg)](https://github.com/Jorman/Scripts/discussions)

A curated collection of automation scripts, tools, and Docker utilities designed for home server maintenance, media libraries (Plex, Jellyfin), the **\*Arr suite** (Radarr, Sonarr), and torrent clients (qBittorrent, Transmission).

The goal of this repository is to share practical solutions for day-to-day automation problems: keeping disk space optimized, injecting fresh public trackers, cleaning up unpacked archives, managing seed times, and applying AI to media metadata.

> [!TIP]
> **Detailed Documentation Available:** This document provides a high-level catalog explaining what each tool does. For step-by-step installation guides, configuration files, parameters, and examples, follow the links provided for each project.

---

## 📑 Repository Catalog

### 🎙️ Media & AI Audio Tagging

#### [AudioMediaChecker](./AudioMediaChecker)
- **What it does:** Docker-based automated language detector and tagger for video files (primarily MKV). Powered by **OpenAI Whisper** and **Silero Voice Activity Detection (VAD)**.
- **Problem it solves:** Fixes files with missing or undetermined (`und`) audio track language tags without re-encoding video streams. Features intelligent handling for silent/dialogue-free films (`zxx`), confidence thresholds, CUDA/GPU support, and a JSON output mode for pipeline automation.
- **Documentation:** See the complete [AudioMediaChecker README](./AudioMediaChecker/README.md) for Docker Hub usage, benchmark charts, and parameter details.

---

### 📥 Torrent Clients & Trackers Management

#### [qBittorrentHardlinksChecker](./qBittorrentHardlinksChecker)
- **What it does:** Advanced Python tool (available also as a Docker container) that inspects torrents in qBittorrent, with a special emphasis on hardlink counts.
- **Problem it solves:** When using hardlinks with Sonarr/Radarr, deleting a torrent prematurely can waste disk space or delete content unexpectedly. This script distinguishes between imported files (multiple hardlinks) and files occupying raw space, rechecks errored torrents, cleans dead trackers, and handles private tracker orphan deletion safely.
- **Documentation:** Detailed guide available in [qBittorrentHardlinksChecker README](./qBittorrentHardlinksChecker/README.md).

#### [AddqBittorrentTrackers](./AddqBittorrentTrackers)
- **What it does:** Shell (`.sh`) and Python (`.py`) scripts that inject live public trackers into qBittorrent torrents.
- **Problem it solves:** Increases peer availability and download speeds on public torrents. Can be executed manually or set up as a custom "On Grab" notification script within Radarr and Sonarr.
- **Documentation:** See [AddqBittorrentTrackers Readme](./AddqBittorrentTrackers/AddqBittorrentTrackers.sh.readme.md).

#### [AddTransmissionTrackers](./AddTransmissionTrackers)
- **What it does:** Bash script that injects updated tracker lists directly into Transmission torrents using the native Transmission `/rpc` API.
- **Problem it solves:** Automatically expands tracker lists for Transmission downloads (manually or via Radarr/Sonarr "On Grab" hooks) without requiring external CLI dependencies like `transmission-remote`.
- **Documentation:** See [AddTransmissionTrackers Readme](./AddTransmissionTrackers/AddTransmissionTrackers.sh.readme.md).

#### [TransmissionRemoveCompleteTorrent.sh](./TransmissionRemoveCompleteTorrent.sh)
- **What it does:** Automation script designed to run via `cron` to monitor and remove finished torrents in Transmission.
- **Problem it solves:** Cleans completed downloads and enforces maximum seed times (in days) while differentiating between automatic downloads (e.g. Radarr/Sonarr paths) and personal/manual downloads.
- **Documentation:** Configuration and crontab instructions are documented in [TransmissionRemoveCompleteTorrent.sh.readme.md](./TransmissionRemoveCompleteTorrent.sh.readme.md).

---

### 🎬 \*Arr Suite Unpack & Cleanup Helpers

#### [radarr_cleanup_packed_torrent.sh](./radarr_cleanup_packed_torrent.sh)
- **What it does:** A custom post-processing bash script to connect to Radarr (triggered *On Download* / *On Upgrade*).
- **Problem it solves:** When torrents arrive packed in `.rar` / `.r00` archives and are unpacked into the same folder, the video file gets duplicated upon Radarr import. This script safely verifies that the unpack process has completed and cleans up the redundant video file from multi-file torrent folders without disrupting small utility rar files.

#### [sonarr_cleanup_packed_torrent.sh](./sonarr_cleanup_packed_torrent.sh)
- **What it does:** The Sonarr counterpart to the Radarr cleanup script, tailored for TV show structures.
- **Problem it solves:** Prevents duplicated video files in multi-file TV release folders after unrarring, saving storage space across episodic libraries.

---

### 🗄️ Storage & Samba Maintenance

#### [clean_samba_recycle.sh](./clean_samba_recycle.sh)
- **What it does:** Maintenance shell script to purge Samba network recycle bins (`.recycle`).
- **Problem it solves:** Automatically deletes files whose access time exceeds configured day thresholds (customizable per shared directory) and cleans up remaining empty directories afterwards.

---

### 📦 Moved / Dedicated Repositories

#### [eMulerrStalledChecker](./eMulerrStalledChecker)
- **Status:** *Deprecated in this repository.*
- **Note:** eMulerr has been superseded by aMulerr. This script was refactored and moved to its own dedicated repository: [Jorman/aMulerrStalledChecker](https://github.com/Jorman/aMulerrStalledChecker) (and Docker Hub image `chryses/amulerr-stalled-checker`).

---

## 💬 Questions, Help & Discussions

Have questions about how to configure a script, integrate a tool with your specific setup (Docker, NAS, Unraid, TrueNAS, Linux), or want to suggest an improvement?

Feel free to start a thread in **[GitHub Discussions](https://github.com/Jorman/Scripts/discussions)**!
- Ask questions about usage and integration.
- Share ideas for new scripts or improvements.
- If you find a specific bug, you can also open an [Issue](https://github.com/Jorman/Scripts/issues).

---

## 📄 License

This repository is distributed under the [MIT License](LICENSE). Check individual project folders for any specific third-party licenses or acknowledgments.
