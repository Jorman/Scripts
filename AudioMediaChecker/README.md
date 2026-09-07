# AudioMedia Checker

![Docker Pulls](https://img.shields.io/docker/pulls/chryses/audiomedia-checker)
![Docker Image Size](https://img.shields.io/docker/image-size/chryses/audiomedia-checker)
![GitHub](https://img.shields.io/github/license/Jorman/Scripts)

> Automatic audio track language detection and tagging for video files using OpenAI Whisper

## Overview
AudioMedia Checker is a Docker-based CLI tool that automatically detects the language of audio tracks in video files and corrects language tags using OpenAI's Whisper AI model.  
It's designed as a disposable container (`docker run --rm`) that can be integrated into automation scripts without requiring any local installation. The tool analyzes audio tracks without language tags (or with undefined tags) and updates MKV file metadata accordingly. For non-MKV formats, it performs read-only analysis in dry-run mode, ensuring safe operation.

---

## ✨ Features
- **AI-Powered Detection** — Uses OpenAI Whisper for accurate language identification
- **Automatic Tagging** — Updates language metadata in MKV files
- **Voice Activity Detection (VAD)** — Integrated Silero VAD filters out music, background noise, and silence to guarantee samples contain true human dialogue
- **Silent & Instrumental Movie Handling (`zxx`)** — Accurately classifies dialogue-free tracks and tags them with the standard ISO 639-2 code `zxx` (*No linguistic content*), preventing wasted retry loops
- **Purified Quorum Consensus** — Requires at least 3 out of 4 vocal samples (≥75% agreement), isolating random foreign words or song lyrics
- **Flexible Analysis** — Single file or recursive folder processing
- **Adaptive Multi-Attempt Detection** — Up to 10 retry attempts with dynamic segment durations (30–90s) and randomized sampling for difficult dialogue
- **JSON Output Mode** — Clean JSON output (`--json`) with track indexes and ISO 639-2 codes (`ita`, `eng`, `zxx`, `und`), ideal for pipeline and script automation
- **Confidence Control** — Adjustable threshold (default: 65%)
- **Force Override** — Manual language assignment or force-accepting best match under threshold
- **GPU Acceleration** — Optional CUDA support for faster processing
- **High-Performance Pipeline** — Background FFmpeg audio prefetching and Whisper model caching across multiple files
- **Docker-Native** — No local dependencies, run-and-forget design
- **Dry-Run Mode** — Safe testing without file modifications
- **Selective Analysis** — Process only untagged tracks (or those tagged `und`) or analyze all tracks with `--check-all-tracks`
- 📦 **Model Cache (recommended)** — Persist Whisper models under `/models` to avoid re-downloads between runs

---

## Quick Start

### 1) Prepare a persistent model cache (recommended)
Create a directory on the host to persist Whisper model files and mount it to `/models` inside the container:
```bash
sudo mkdir -p /opt/audiomedia-models
sudo chown -R $(id -u):$(id -g) /opt/audiomedia-models
```

> Why: the application downloads model files to `/models`. Persisting this directory makes repeated runs much faster and saves bandwidth.

### 2) Analyze a Single File (CPU)
```bash
docker run --rm \
  -v /path/to/movies:/data \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --file "/data/Movie.mkv"
```

### 3) Analyze Folder Recursively (GPU)
```bash
docker run --rm --gpus all \
  -v /path/to/movies:/data \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --gpu \
  --folder "/data" \
  --recursive
```

### 4) Dry-Run Test (Safe Mode)
```bash
docker run --rm \
  -v /path/to/movies:/data \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --dry-run \
  --folder "/data/Movies" \
  --verbose
```

---

## Command-Line Arguments
| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--file` | string | - | Path to a single file to analyze |
| `--folder` | string | - | Directory path to process |
| `--recursive` | int | - | Depth levels (0 = unlimited, >0 = specific depth) |
| `--check-all-tracks` | flag | false | Analyze all tracks, not just untagged ones |
| `--verbose` | flag | false | Enable detailed logging (incompatible with `--json`) |
| `--json` | flag | false | Output results strictly in JSON format (track index and ISO 639-2 language); silences standard logs and progress bar (incompatible with `--verbose`) |
| `--dry-run` | flag | false | Simulate operations without modifying files |
| `--force-language` | string / flag | - | Language code to force (ISO 639-2, 3 letters) when detection fails or is below threshold; if passed without value (`--force-language`), forces the detected language even if below threshold |
| `--confidence` | int | 65 | Detection confidence threshold (0-100) |
| `--model` | string | base | Whisper model size (see below) |
| `--gpu` | flag | false | Use GPU acceleration (requires NVIDIA GPU) |
| `--help-languages` | flag | false | Show available language codes |

---

### Whisper Models
| Model | Size | Speed | Accuracy | Recommended For |
|-------|------|-------|----------|-----------------|
| `tiny` | ~39 MB | ⚡⚡⚡ | ⭐⭐ | Quick tests |
| `base` | ~74 MB | ⚡⚡ | ⭐⭐⭐ | **Default - Best balance** |
| `small` | ~244 MB | ⚡ | ⭐⭐⭐⭐ | Better accuracy |
| `medium` | ~769 MB |  | ⭐⭐⭐⭐⭐ | High accuracy needed |
| `large` | ~1550 MB |  | ⭐⭐⭐⭐⭐ | Maximum accuracy |
| `large-v3` | ~1550 MB |  | ⭐⭐⭐⭐⭐ | Latest version |

> Tip: `base` model provides excellent results for most use cases. Use larger models only if detection fails.

---

## Usage Examples

### Basic File Analysis (verbose)
```bash
docker run --rm \
  -v /media/movies:/data \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --file "/data/MyMovie.mkv" \
  --verbose
```

### Recursive Folder with Custom Confidence and Model
```bash
docker run --rm \
  -v /media/library:/library \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --folder "/library" \
  --recursive 0 \
  --confidence 70 \
  --model small
```

### Force Specific Language (Fallback)
```bash
docker run --rm \
  -v /media/movies:/data \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --folder "/data/Italian_Films" \
  --force-language ita \
  --recursive
```

### Force Best Match Under Threshold (No Value)
If confidence is below the threshold, but you want to force the most likely detected language anyway:
```bash
docker run --rm \
  -v /media/movies:/data \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --file "/data/DifficultAudio.mkv" \
  --force-language
```

### JSON Output Mode (for Pipeline Automation)
Generate minimal JSON output without log messages or progress bars, ideal for piping into scripts or tools like `jq`:
```bash
docker run --rm \
  -v /media/movies:/data \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --file "/data/Movie.mkv" \
  --dry-run \
  --check-all-tracks \
  --json
```

Output:
```json
[
  {
    "track": 1,
    "language": "ita"
  },
  {
    "track": 2,
    "language": "zxx"
  }
]
```
> **Note:** `--json` and `--verbose` are mutually exclusive. In JSON mode, standard logs and progress bars are disabled so stdout remains clean JSON.
> - Dialogue-free / non-vocal tracks (silent movies, instrumental scores) report `"zxx"` (*No linguistic content*).
> - Tracks with speech where language cannot be reliably determined after maximum attempts report `"und"` (*Undetermined*).

### GPU-Accelerated Processing (medium model)
```bash
docker run --rm --gpus all \
  -v /media/library:/data \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --gpu \
  --folder "/data" \
  --recursive \
  --model medium
```

### Dry-Run on Mixed Formats (read-only)
```bash
docker run --rm \
  -v /media/downloads:/downloads \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --dry-run \
  --folder "/downloads" \
  --check-all-tracks \
  --verbose
```

---

## How It Works

### Detection Logic & Adaptive Multi-Attempt Analysis
1. **Scans** MKV files (or all video formats in dry-run mode).
2. **Identifies** audio tracks requiring analysis:
   - Untagged tracks or tracks tagged with `und` / `undefined`.
   - All tracks if `--check-all-tracks` is specified.
   - Tracks already tagged with valid language codes (including `zxx`) are preserved and skipped unless `--check-all-tracks` is enabled.
3. **Speech Validation via Silero VAD**:
   - Audio segments are inspected with Silero VAD (`get_speech_timestamps`).
   - Samples with less than 1.5 seconds of confirmed human speech (silence, instrumental music, ambient noise) are discarded.
   - Dynamic background prefetching queues replacement percentage points (between 5% and 95%) until 4 valid vocal samples are acquired.
4. **Dialogue-Free & Silent Film Protection (`zxx`)**:
   - If 10 distinct sample points across the entire file consistently contain no human speech, the track is classified as *"Non-Vocal / Dialogue-Free Audio"*.
   - Early-halts all remaining retry attempts immediately (completing in ~4–6 seconds).
   - Tags the track with standard ISO 639-2 code `zxx` (*No linguistic content; Not applicable*) in MKV metadata (or simulated in dry-run).
   - In `--json` mode, outputs `"language": "zxx"`.
5. **Purified Quorum Consensus**:
   - Once 4 valid vocal samples are collected, the engine evaluates consensus.
   - Requires at least 3 out of 4 samples (≥75% agreement) on the dominant language.
   - Computes the average confidence strictly across samples that matched the dominant language, preventing stray foreign words or intro songs from diluting accuracy.
   - If quorum is met and average confidence ≥ `--confidence` (default: 65%), updates the track tag and finishes.
6. **Adaptive Retries (Attempts 2–10)**:
   - If quorum or confidence fails on a vocal track, up to 9 subsequent attempts are triggered.
   - Each retry tests 4 new randomized positions with dynamic sample durations (30 to 90 seconds).
7. **Tagging & Fallback**:
   - Updates MKV metadata with `mkvpropedit` (MKV only).
   - If `--force-language` was supplied with a code (e.g. `ita`), it applies that code when detection fails or falls below threshold.
   - If `--force-language` was passed without a value, the highest-confidence detected language is applied even if under threshold.
   - If all attempts fail to determine the language of a vocal track, reports `"und"` (*Undetermined*) in `--json` and leaves original file tags unmodified.
8. **Skips** modification for non-MKV formats (analysis only).

> Note: models are downloaded to `/models`. Mount a persistent volume to avoid re-downloading on each run.

---

### File Format Support
| Format | Detection | Tag Update | Notes |
|--------|-----------|------------|-------|
| `.mkv` | ✅ | ✅ | Fully supported |
| `.mp4` | ✅ | ❌ | Dry-run only |
| `.avi` | ✅ | ❌ | Dry-run only |
| `.mov` | ✅ | ❌ | Dry-run only |
| `.m4v` | ✅ | ❌ | Dry-run only |
| `.flv` | ✅ | ❌ | Dry-run only |
| `.wmv` | ✅ | ❌ | Dry-run only |
| `.webm` | ✅ | ❌ | Dry-run only |

> Safety: Non-MKV files are automatically analyzed in read-only mode to prevent accidental modifications.

---

### Language Support
All languages supported by OpenAI Whisper:
- **100+ languages** detected automatically
- Tags use **ISO 639-2** format (3-letter codes)
- Use `--help-languages` to see full list

Common examples: `eng` (English), `ita` (Italian), `fra` (French), `spa` (Spanish), `deu` (German), `jpn` (Japanese), `kor` (Korean), `rus` (Russian), `chi` (Chinese)

#### Special ISO 639-2 Codes:
- **`zxx`** (*No linguistic content; Not applicable*): Automatically applied to silent movies, instrumental soundtracks, and dialogue-free audio tracks. Supported natively by Matroska (MKV) and recognized by Plex, Jellyfin, Kodi, and VLC.
- **`und`** (*Undetermined*): Returned when human speech is present but the language could not be determined with sufficient confidence after maximum retries.

---

## 🖥️ GPU Acceleration

### Requirements
- NVIDIA GPU with CUDA support
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed
- Docker `--gpus` flag support

### Installation (Ubuntu/Debian)
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

---

## ⚡ Performance & Benchmarks

AudioMedia Checker decouples language identification from full text transcription. While traditional speech transcription decodes entire sentences token-by-token using autoregressive beam search, AudioMedia Checker queries Whisper's encoder classification head directly (`detect_language`), skipping redundant text generation while maintaining **100% mathematical parity** in language detection and confidence scores.

### Real-World Hardware Benchmarks
*Tested on real 30-second audio segments using the default `base` model:*

| Hardware | Compute Type | Fast Language Detection (Now) | Full Transcription (Legacy) | Speedup Factor |
|:---|:---|:---:|:---:|:---:|
| **CPU** (Intel Core i5-10400 @ 2.90GHz, 6C/12T) | `int8` | **~408 ms** | ~2,000 ms (2.0s) | **4.9x faster** |
| **GPU** (NVIDIA GeForce RTX 3060 12GB VRAM) | `float16` | **~33 ms** | ~463 ms | **13.8x faster** |

#### Key Takeaways:
- **CPU (int8):** Detection time drops from ~2.0 seconds down to **~0.4 seconds** per 30-second sample (~1.6 seconds saved per sample).
- **GPU (CUDA):** Detection takes only **33 milliseconds** per sample (virtually instantaneous).
- **Full Track Analysis (4 Samples):** Total Whisper inference time across an entire movie/episode is reduced from ~8.0s down to **~1.6s on CPU**, and from ~1.85s down to **~0.13s on GPU**.
- **Accuracy Parity:** The mathematical difference in language confidence between fast detection and full transcription is `0.000000` (zero loss of accuracy). Full text transcription can still be enabled for debugging purposes by passing `--verbose`.

### Real-World Library Batch Throughput (10, 25, 50, 100 Files)
*Benchmarked on a real heterogeneous media library (movies with 5.1/7.1 surround tracks and multi-language audio, TV series episodes, and trailers) using GPU acceleration (`RTX 3060 12GB`, `base` model, `--check-all-tracks --dry-run`):*

| Files Analyzed | Total Audio Tracks Scanned | Total Time | Average Time / File | Average Time / Audio Track |
|:---:|:---:|:---:|:---:|:---:|
| **10 files** | 13 tracks | 20.0 s | **2.00 s / file** | **1.54 s / track** |
| **25 files** | 37 tracks | 52.7 s | **2.11 s / file** | **1.42 s / track** |
| **50 files** | 77 tracks | 112.6 s (1m 52s) | **2.25 s / file** | **1.46 s / track** |
| **100 files** | 155 tracks | 237.7 s (3m 57s) | **2.38 s / file** | **1.53 s / track** |

> **Stability & Consistency:** Throughput remains rock-solid (~1.4–1.5s per track) across hundreds of files without memory leaks or VRAM degradation, thanks to model caching across files (TASK-01) and background FFmpeg prefetching (TASK-06).

---

## ⚠️ Important Notes

### Modifications & Backups
- ✅ **MKV files are modified in-place** (no backup created)  
- ✅ **Original video/audio streams untouched** (only metadata changes)  
- ⚠️ **No undo feature** — test with `--dry-run` first  
- Recommendation: Backup important files before first run

### Force Language Behavior
`--force-language` can operate in two distinct modes:
- **Explicit Code** (e.g. `--force-language ita`): sets the specified 3-letter language code to all analyzed tracks that either lack a tag or fail to meet the confidence threshold.
- **Flag Without Value** (i.e. `--force-language`): instructs the tool to accept and apply the most likely detected language candidate even if its confidence score falls below `--confidence`.

> ⚠️ When using an explicit code, note that it applies across all tracks failing the confidence check. Ensure this matches your intent before modifying files.

### Recursive Depth
```bash
--recursive      # Unlimited depth (all subdirectories)
--recursive 0    # Same as above
--recursive 1    # Only immediate subdirectories
--recursive 2    # Up to 2 levels deep
```

---

## Integration Examples

### Automated Post-Processing Script
```bash
#!/bin/bash
# Process new downloads automatically
DOWNLOAD_DIR="/media/downloads"
LIBRARY_DIR="/media/library"

# Analyze and tag
docker run --rm \
  -v "$DOWNLOAD_DIR:/data" \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --folder "/data" \
  --confidence 70 \
  --model base

# Move to library after tagging
mv "$DOWNLOAD_DIR"/*.mkv "$LIBRARY_DIR/" 2>/dev/null || true
```

### Cron Job (Daily Library Scan)
```bash
# /etc/cron.daily/audiomedia-checker
#!/bin/bash
docker run --rm \
  -v /media/library:/library \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --folder "/library" \
  --recursive \
  --confidence 75 \
  >> /var/log/audiomedia-checker.log 2>&1
```

### Sonarr/Radarr Custom Script
```bash
#!/bin/bash
# Save as: /scripts/tag-audio.sh
FILE_PATH="$1"  # Passed by Sonarr/Radarr
docker run --rm \
  -v "$(dirname "$FILE_PATH"):/data" \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest \
  --file "/data/$(basename "$FILE_PATH")" \
  --model base
```

---

## Docker Hub
**Repository:** [chryses/audiomedia-checker](https://hub.docker.com/r/chryses/audiomedia-checker)

### Available Tags
- `latest` — Latest stable release (recommended)
- `[commit-sha]` — Specific commit builds for testing/rollback

### Supported Architectures
- ✅ `linux/amd64` (x86_64)
- ✅ `linux/arm64` (ARM 64-bit)

### Auto-Build
Images are automatically built on every push to the `master` branch via GitHub Actions.

---

## Troubleshooting

### "GPU not detected" in Docker
```bash
# Test GPU availability
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
# If it fails, (re)install NVIDIA Container Toolkit and restart Docker
```

### "Permission denied" on files
Ensure your user has read/write access to mounted volumes:
```bash
# Option 1: run as your user
docker run --rm --user $(id -u):$(id -g) \
  -v /media:/data \
  -v /opt/audiomedia-models:/models \
  chryses/audiomedia-checker:latest ...

# Option 2: fix host permissions
sudo chown -R $USER:$USER /media/library
```

### Model cache not persistent
- Make sure you mount a persistent volume: `-v /opt/audiomedia-models:/models`
- Verify permissions on the host directory

### Low confidence scores
1) Try a larger model: `--model medium`  
2) Lower threshold: `--confidence 50`  
3) Ensure audio is clear (not corrupted)  
4) Use `--force-language` as last resort

### High memory usage
Large models require significant RAM:

| Model | Min RAM Required | Compute Type |
|-------|------------------|--------------|
| `tiny` | ~2 GB | `int8` |
| `base` | ~3 GB | `int8` |
| `small` | ~5 GB | `int8` |
| `medium` | ~10 GB | `int8` (≥16GB RAM) / `float32` |
| `large` | ~16 GB | `float32` |
| `large-v3` | ~16 GB | `float32` |

Use smaller models on limited hardware.

---

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

### How to Contribute
1. Fork the repository  
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)  
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)  
4. Push to the branch (`git push origin feature/AmazingFeature`)  
5. Open a Pull Request

---

## Support
- **Bug Reports:** [GitHub Issues](https://github.com/Jorman/Scripts/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Jorman/Scripts/discussions)
- **Docker Hub:** [chryses/audiomedia-checker](https://hub.docker.com/r/chryses/audiomedia-checker)

---

## Acknowledgments
- **[OpenAI Whisper](https://github.com/openai/whisper)** — AI-powered speech recognition  
- **[MKVToolNix](https://mkvtoolnix.download/)** — MKV file manipulation  
- **[FFmpeg](https://ffmpeg.org/)** — Multimedia processing

---

## License
This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) file for details.

---

## ⭐ Show Your Support
If you find this project useful, please consider:
- ⭐ Starring the repository on GitHub
- Pulling the Docker image
- Sharing with the media automation community

---
**Made with ❤️ for audio perfectionists**  
**Powered by OpenAI Whisper** | **Source:** [GitHub](https://github.com/Jorman/Scripts)
