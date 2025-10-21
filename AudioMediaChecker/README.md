# AudioMedia Checker

![Docker Pulls](https://img.shields.io/docker/pulls/chryses/audiomedia-checker)
![Docker Image Size](https://img.shields.io/docker/image-size/chryses/audiomedia-checker)
![GitHub](https://img.shields.io/github/license/Jorman/Scripts)

> Automatic audio track language detection and tagging for video files using OpenAI Whisper

## 📖 Overview

AudioMedia Checker is a Docker-based CLI tool that automatically detects the language of audio tracks in video files and corrects language tags using OpenAI's Whisper AI model. It's designed as a disposable container (`docker run --rm`) that can be integrated into automation scripts without requiring any local installation.

The tool analyzes audio tracks without language tags (or with undefined tags) and updates MKV file metadata accordingly. For non-MKV formats, it performs read-only analysis in dry-run mode, ensuring safe operation.

## ✨ Features

- 🎯 **AI-Powered Detection** - Uses OpenAI Whisper for accurate language identification
- 🏷️ **Automatic Tagging** - Updates language metadata in MKV files
- 📁 **Flexible Analysis** - Single file or recursive folder processing
- 🎚️ **Confidence Control** - Adjustable threshold (default: 65%)
- 🔧 **Force Override** - Manual language assignment when detection fails
- 🚀 **GPU Acceleration** - Optional CUDA support for faster processing
- 💻 **Docker-Native** - No local dependencies, run-and-forget design
- 🧪 **Dry-Run Mode** - Safe testing without file modifications
- 📊 **Selective Analysis** - Process only untagged tracks or all tracks

## 🚀 Quick Start

### Analyze a Single File (CPU)
```bash
docker run --rm \
  -v /path/to/movies:/data \
  chryses/audiomedia-checker:latest \
  --file "/data/Movie.mkv"
```

### Analyze Folder Recursively (GPU)
```bash
docker run --rm --gpus all \
  -v /path/to/movies:/data \
  chryses/audiomedia-checker:latest \
  --gpu \
  --folder "/data" \
  --recursive
```

### Dry-Run Test (Safe Mode)
```bash
docker run --rm \
  -v /path/to/movies:/data \
  chryses/audiomedia-checker:latest \
  --dry-run \
  --folder "/data/Movies" \
  --verbose
```

## 📋 Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--file` | string | - | Path to a single file to analyze |
| `--folder` | string | - | Directory path to process |
| `--recursive` | int | - | Depth levels (0 = unlimited, >0 = specific depth) |
| `--check-all-tracks` | flag | false | Analyze all tracks, not just untagged ones |
| `--verbose` | flag | false | Enable detailed logging |
| `--dry-run` | flag | false | Simulate operations without modifying files |
| `--force-language` | string | - | Force specific language (ISO 639-2, 3 letters) |
| `--confidence` | int | 65 | Detection confidence threshold (0-100) |
| `--model` | string | base | Whisper model size (see below) |
| `--gpu` | flag | false | Use GPU acceleration (requires NVIDIA GPU) |
| `--help-languages` | flag | false | Show available language codes |

### Whisper Models

| Model | Size | Speed | Accuracy | Recommended For |
|-------|------|-------|----------|-----------------|
| `tiny` | ~39 MB | ⚡⚡⚡ | ⭐⭐ | Quick tests |
| `base` | ~74 MB | ⚡⚡ | ⭐⭐⭐ | **Default - Best balance** |
| `small` | ~244 MB | ⚡ | ⭐⭐⭐⭐ | Better accuracy |
| `medium` | ~769 MB | 🐌 | ⭐⭐⭐⭐⭐ | High accuracy needed |
| `large` | ~1550 MB | 🐌🐌 | ⭐⭐⭐⭐⭐ | Maximum accuracy |
| `large-v3` | ~1550 MB | 🐌🐌 | ⭐⭐⭐⭐⭐ | Latest version |

> **Tip:** `base` model provides excellent results for most use cases. Use larger models only if detection fails.

## 💡 Usage Examples

### Basic File Analysis
```bash
docker run --rm \
  -v /media/movies:/data \
  chryses/audiomedia-checker:latest \
  --file "/data/MyMovie.mkv" \
  --verbose
```

### Recursive Folder with Custom Confidence
```bash
docker run --rm \
  -v /media/library:/library \
  chryses/audiomedia-checker:latest \
  --folder "/library" \
  --recursive 0 \
  --confidence 70 \
  --model small
```

### Force Italian Language (Fallback)
```bash
docker run --rm \
  -v /media/movies:/data \
  chryses/audiomedia-checker:latest \
  --folder "/data/Italian_Films" \
  --force-language ita \
  --recursive
```

> ⚠️ **Warning:** `--force-language` currently applies to ALL tracks with undefined tags or below confidence threshold. Use with caution!

### GPU-Accelerated Processing
```bash
docker run --rm --gpus all \
  -v /media/library:/data \
  chryses/audiomedia-checker:latest \
  --gpu \
  --folder "/data" \
  --recursive \
  --model medium
```

### Dry-Run on Mixed Formats
```bash
docker run --rm \
  -v /media/downloads:/downloads \
  chryses/audiomedia-checker:latest \
  --dry-run \
  --folder "/downloads" \
  --check-all-tracks \
  --verbose
```

## 🎯 How It Works

### Detection Logic

1. **Scans** MKV files (or all video formats in dry-run mode)
2. **Identifies** audio tracks without language tags
3. **Extracts** 30-second audio sample
4. **Analyzes** with Whisper AI model
5. **Updates** MKV metadata if confidence ≥ threshold
6. **Skips** modification for non-MKV formats (analysis only)

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

> **Safety:** Non-MKV files are automatically analyzed in read-only mode to prevent accidental modifications.

### Language Support

All languages supported by OpenAI Whisper:

- 🌍 **100+ languages** detected automatically
- 🏷️ Tags use **ISO 639-2** format (3-letter codes)
- 📚 Use `--help-languages` to see full list

Common examples: `eng` (English), `ita` (Italian), `fra` (French), `spa` (Spanish), `deu` (German), `jpn` (Japanese), `kor` (Korean), `rus` (Russian), `chi` (Chinese)

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

### Performance Comparison

| Model | CPU (i7) | GPU (RTX 3060) | Speedup |
|-------|----------|----------------|---------|
| `tiny` | ~5s | ~1s | 5x |
| `base` | ~15s | ~3s | 5x |
| `small` | ~45s | ~8s | 5.6x |
| `medium` | ~2m | ~15s | 8x |
| `large` | ~5m | ~30s | 10x |

> Times per file (approximate). GPU provides 5-10x faster processing.

## ⚠️ Important Notes

### Modifications & Backups

- ✅ **MKV files are modified in-place** (no backup created)
- ✅ **Original video/audio streams untouched** (only metadata changes)
- ⚠️ **No undo feature** - test with `--dry-run` first
- 💡 **Recommendation:** Backup important files before first run

### Force Language Behavior

> ⚠️ **Current Limitation:** `--force-language` applies to ALL tracks that either:
> - Have no language tag
> - Have confidence score below threshold
>
> This may cause unexpected results. Use only when you're certain all tracks share the same language.

### Recursive Depth

```bash
--recursive       # Unlimited depth (all subdirectories)
--recursive 0     # Same as above
--recursive 1     # Only immediate subdirectories
--recursive 2     # Up to 2 levels deep
```

## 🔧 Integration Examples

### Automated Post-Processing Script

```bash
#!/bin/bash
# Process new downloads automatically

DOWNLOAD_DIR="/media/downloads"
LIBRARY_DIR="/media/library"

# Analyze and tag
docker run --rm \
  -v "$DOWNLOAD_DIR:/data" \
  chryses/audiomedia-checker:latest \
  --folder "/data" \
  --confidence 70 \
  --model base

# Move to library after tagging
mv "$DOWNLOAD_DIR"/*.mkv "$LIBRARY_DIR/"
```

### Cron Job (Daily Library Scan)

```bash
# /etc/cron.daily/audiomedia-checker
#!/bin/bash
docker run --rm \
  -v /media/library:/library \
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
  chryses/audiomedia-checker:latest \
  --file "/data/$(basename "$FILE_PATH")" \
  --model base
```

## 🐳 Docker Hub

**Repository:** [chryses/audiomedia-checker](https://hub.docker.com/r/chryses/audiomedia-checker)

### Available Tags
- `latest` - Latest stable release (recommended)
- `[commit-sha]` - Specific commit builds for testing/rollback

### Supported Architectures
- ✅ `linux/amd64` (x86_64)
- ✅ `linux/arm64` (ARM 64-bit)

### Auto-Build
Images are automatically built on every push to the `master` branch via GitHub Actions.

## 🐛 Troubleshooting

### "No module named 'whisper'"

The container includes all dependencies. If you see this error, you may be running an old image:

```bash
docker pull chryses/audiomedia-checker:latest
```

### GPU Not Detected

```bash
# Test GPU availability
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If fails, reinstall NVIDIA Container Toolkit
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### "Permission denied" on Files

Ensure your user has read/write access to mounted volumes:

```bash
# Option 1: Run as your user
docker run --rm --user $(id -u):$(id -g) \
  -v /media:/data \
  chryses/audiomedia-checker:latest ...

# Option 2: Fix permissions
sudo chown -R $USER:$USER /media/library
```

### Low Confidence Scores

If detection frequently fails:

1. Try a larger model: `--model medium`
2. Lower threshold: `--confidence 50`
3. Ensure audio is clear (not corrupted)
4. Use `--force-language` as last resort

### High Memory Usage

Large models require significant RAM:

| Model | RAM Required |
|-------|--------------|
| tiny/base | ~2 GB |
| small | ~4 GB |
| medium | ~8 GB |
| large | ~16 GB |

Use smaller models on limited hardware.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/Jorman/Scripts/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Jorman/Scripts/discussions)
- 🐳 **Docker Hub:** [chryses/audiomedia-checker](https://hub.docker.com/r/chryses/audiomedia-checker)

## 🙏 Acknowledgments

- **[OpenAI Whisper](https://github.com/openai/whisper)** - AI-powered speech recognition
- **[MKVToolNix](https://mkvtoolnix.download/)** - MKV file manipulation
- **[FFmpeg](https://ffmpeg.org/)** - Multimedia processing

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) file for details.

## ⭐ Show Your Support

If you find this project useful, please consider:
- ⭐ Starring the repository on GitHub
- 🐳 Pulling the Docker image
- 📢 Sharing with the media automation community

---

**Made with ❤️ for audio perfectionists**

**Powered by OpenAI Whisper** | **Source:** [GitHub](https://github.com/Jorman/Scripts)
