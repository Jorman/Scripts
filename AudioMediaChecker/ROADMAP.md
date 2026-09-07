# AUDIO MEDIA CHECKER — ROADMAP & IMPLEMENTATION PLAN

Tracking document and operational guide for the development, optimization, and refactoring of `AudioMediaChecker.py`.

---

## 🛡️ OPERATIONAL PROTOCOL & STRICT RULES (PRODUCTION ENVIRONMENT)

Because the script operates in a production environment and performs direct metadata modifications on multimedia files, every development cycle must strictly comply with the following rules:

1. **Absolute Integrity of Real Test Media Files:**
   * Real media files provided for testing **MUST NEVER BE MODIFIED OR OVERWRITTEN**.
   * Any functional test must be conducted:
     * In `--dry-run` mode (safe read-only simulation), OR
     * By creating an isolated temporary sandbox/backup copy in a temporary directory (e.g. scratch/tmp), testing write operations on the copy, verifying the result, and removing the copy upon completion.
2. **Mandatory Testing on Real Files at Each Step:**
   * No modification is considered complete without first requesting real test files from the user and validating the output.
3. **No Commits Without 100% Positive Test Results:**
   * No Git commit or push will be executed until tests confirm zero regressions and the full, expected behavior of the specific change.
4. **Modular & Incremental Development:**
   * Tackle one single task at a time. Never bundle multiple complex changes in the same cycle.

---

## 📋 TASK INDEX & PROGRESS STATUS

| ID | Title | Category | Priority | Status |
|:---|:---|:---|:---:|:---:|
| **TASK-01** | Whisper Model Caching Across Multiple Files & Resource Cleanup | Bugfix / Performance | High | ✅ Completed |
| **TASK-02** | 4-Valid-Sample Sampling Logic + Quorum & Silent/Non-Vocal Handling | Algorithm / Accuracy | High | ✅ Completed |
| **TASK-03** | Graceful Shutdown & Interruption Signals Handling (`SIGINT`/`SIGTERM`) | Stability / OS | Medium | ✅ Completed |
| **TASK-04** | Fast Language Detection vs Full Autoregressive Transcription | Performance | Medium | ✅ Completed |
| **TASK-05** | Environment Variables Support (Docker-Friendly Configuration) | Feature | Low | Planned |
| **TASK-06** | Parallel Pipeline: FFmpeg Extraction & Whisper Inference | Performance / Concurrency | Medium | ✅ Completed |
| **BACKLOG-01**| `--json` Support for Multiple Folders/Files | Feature / Architecture | - | On Hold |
| **BACKLOG-02**| Investigation of `ffprobe` vs `mkvpropedit` Track Index Alignment | Edge Case Analysis | - | On Hold |
| **BACKLOG-04**| Post-Processing Webhook Notifications System | Feature | - | On Hold |

---

## DEVELOPMENT TASK DETAILS

---

### TASK-01: Whisper Model Caching Across Multiple Files & Resource Cleanup

* **Analysis Reference:** Item 1.1
* **Status:** ✅ Completed

#### 1. Problem Description
In the `main()` loop, a new `AudioMediaChecker` instance was previously created for each file found in the folder. Although the class featured a lazy initialization mechanism (`self._whisper`), that instance was destroyed at the end of each file.
When processing a folder containing dozens or hundreds of files, the Whisper model (ranging from hundreds of megabytes to several gigabytes) was allocated, loaded from disk, and deallocated **from scratch for every single file**.
This caused:
* Massive time loss (5 to 30 seconds overhead per file).
* Continuous filling and clearing of RAM and GPU VRAM.
* Risk of GPU memory fragmentation during long sessions.
* Lack of explicit memory cleanup prior to script exit.

#### 2. Resolution Strategy
* **Shared Model Instance:** The Whisper model is instantiated once (on the first file requiring speech detection) and reused across all subsequent files in the session.
* **Separation of Concerns:** `AudioMediaChecker` accepts an optional pre-loaded `whisper_model` instance or falls back to lazy-loading if none is supplied.
* **Explicit Exit Cleanup:** Before script termination (whether normal, interrupted, or on error), explicitly release the `WhisperModel` instance, run Python garbage collection (`gc.collect()`), and clear CUDA VRAM cache if GPU is enabled.

#### 3. Step-by-Step Implementation
1. Modify `AudioMediaChecker.__init__` to accept `whisper_model=None`.
2. Reuse the supplied model instance directly without re-invoking `_lazy_load_whisper`.
3. In `main()`, manage `shared_whisper_model`:
   * On the first file requiring speech detection, capture the lazy-loaded model via `checker.get_whisper_model()`.
   * Pass `shared_whisper_model` to all subsequent file checks.
4. Implement `unload_whisper_model(whisper_model, logger=None)` to delete model tensors, trigger `gc.collect()`, and log status.
5. Wrap file processing in a `try...finally:` block to guarantee cleanup.

#### 4. Verification Tests & Acceptance Criteria
* Real files multi-file dry-run test: verify via logs that `Loading Whisper model...` appears exactly once and subsequent files reuse the instance instantly.
* Verify clean exit and unloading message.

---

### TASK-02: 4-Valid-Sample Sampling Logic + Quorum & Silent/Non-Vocal Handling

* **Analysis Reference:** Items 1.2 and 2.2
* **Status:** ✅ Completed

#### 1. Problem Description
The previous weighted average calculation had a fundamental mathematical flaw:
`weighted_average = total_confidence_language / total_detections`
If 4 samples were taken:
* Sample 1 (10% of movie): Intro music, Whisper detects no speech and guesses a secondary language with confidence 0.10.
* Sample 2 (35% of movie): Clear Italian dialogue, confidence 0.98.
* Sample 3 (60% of movie): Clear Italian dialogue, confidence 0.97.
* Sample 4 (85% of movie): Clear Italian dialogue, confidence 0.95.
Italian total confidence was `2.90`. Divided by 4 total samples, the average became `72.5%`. If the opening song spanned two samples, the average dropped to `48.7%`, failing the 65% threshold despite dialogue being crystal clear Italian throughout!

Furthermore, on **silent movies** or music-only/effects-only audio tracks, Whisper guessed random languages on background noise, triggering 10 exhaustive retry attempts (30 to 90 seconds each) and wasting minutes with zero speech present.

#### 2. Resolution Strategy
* **Speech Validation via Silero VAD:**
  * Integrated Silero VAD (`get_speech_timestamps`) to inspect audio arrays prior to language detection. Samples containing less than 1.5s of confirmed human speech are discarded as non-vocal (music, silence, or noise).
* **Guaranteed 4 Valid Vocal Samples with Dynamic Prefetching:**
  * In Attempt 1, start with positions `[10%, 35%, 60%, 85%]`.
  * In Attempts 2–10, start with 4 random percentages from `[5..95%]` avoiding previously tested positions.
  * If a sample lacks speech, the pipeline discards it and dynamically queues a new unexplored percentage point between 5% and 95% until 4 valid samples are collected or the exploration ceiling is reached.
* **Exploration Ceiling & Non-Vocal Audio Protection:**
  * Set `max_explored = 10` points per attempt.
  * If all explored points across the entire file consistently lack human speech, the track is classified as *"Non-Vocal / Dialogue-Free Audio"*, immediately halting the remaining 9 attempts.
* **Standardized ISO 639-2 Non-Vocal Tagging (`zxx` vs `und`):**
  * Fully adheres to ISO 639-2 / ISO 639-3 and Matroska IETF BCP 47 standard semantics:
    * `und` (*Undetermined*): reserved strictly for tracks containing speech where language could not be recognized after maximum attempts.
    * `zxx` (*No linguistic content; Not applicable*): assigned to confirmed dialogue-free / non-vocal audio tracks (silent films, instrumental music, ambient/sound effects).
  * Automatically updates MKV metadata tag to `zxx` via `mkvpropedit` (or simulated in `--dry-run`).
  * Emits `{"track": <index>, "language": "zxx"}` in `--json` mode.
  * Checks existing tags: if a track is already tagged `zxx`, skips analysis unless `--check-all-tracks` is set.
* **Purified Quorum Consensus:**
  * Quorum strictly requires all 4 valid vocal samples and at least 3 out of 4 (>= 75%) agreement on the dominant language.
  * The average confidence is computed exclusively across samples that matched the dominant language, preventing unrelated soundbites or foreign words from diluting the true language.

#### 3. Step-by-Step Implementation
1. Integrated Silero VAD (`check_speech_activity`) using `faster_whisper.vad`.
2. Implemented `collect_valid_samples` generator/prefetcher with dynamic queue replacement.
3. Implemented `evaluate_quorum` with strict 4-sample quorum and purified confidence calculation.
4. Added `to_alpha_3` helper method supporting standard 2-letter, 3-letter, and special codes (`zxx`, `und`).
5. Implemented `zxx` ISO standard classification in `process_file` and `handle_detection_result`:
   * Non-vocal tracks trigger tag updates to `zxx` and output `zxx` in JSON mode.
   * `get_tracks_to_analyze` treats unset or `und` tracks as candidates for analysis, while preserving existing valid tags including `zxx`.
6. Refactored `process_file` to unify Attempt 1 and Attempts 2–10 under the new robust engine.

#### 4. Verification Tests & Acceptance Criteria
* Real file test on TV episode (`Spin City`): 4/4 valid speech samples collected, 100% Italian quorum (94.09% confidence).
* Multi-track movie (`2 Hearts`): analyzed Track 1 (Italian AC3 5.1) and Track 2 (English AC3 5.1), both achieving 100% quorum in 7.3s.
* Movie with silent intro (`We Live in Time` - Opus audio): positions 10% and 35% detected as 0s speech and discarded; replacement positions 67% and 61% queued and confirmed with speech, reaching 100% Italian quorum.
* Atmospheric horror film (`The Woman in Black`): Attempt 1 discarded 7 silent points, stopped at 3 samples; Attempt 2 ran with randomized longer duration and achieved 75% Italian quorum (97.45% confidence); Track 2 achieved 100% English quorum (95.47% confidence).
* Silent movies (`Nosferatu (1922)` & `The Phantom Carriage (1921)`): all 10 sample positions across the film verified 0.00s speech; accurately classified as non-vocal audio (`zxx`), updated language tag to `zxx` in dry-run, output `[{"track": 1, "language": "zxx"}]` in `--json` mode, completed in 4.2–6.7s.
* Sandbox live write verification: verified actual write of `zxx` on MKV via `mkvpropedit` (without dry-run) and confirmed via `ffprobe` inspection. Re-running without `--check-all-tracks` confirmed track is recognized as already tagged and skipped.
* Tested `--json` and `--verbose` modes across all file types.

---

### TASK-03: Graceful Shutdown & Interruption Signals Handling (`SIGINT`/`SIGTERM`)

* **Analysis Reference:** Item 1.4
* **Status:** ✅ Completed

#### 1. Problem Description
The codebase previously contained a `self.interrupted = False` attribute, but lacked any active signal handlers for `signal.SIGINT` (terminal Ctrl+C) or `signal.SIGTERM` (Docker container stop / Kubernetes termination).
When interrupted:
* The script terminates abruptly mid-operation.
* If a metadata write operation (`mkvpropedit`) is in progress, files risk corruption or incomplete headers.
* Model resources and temporary memory remain uncleared.
* The loop does not cleanly break across files.

#### 2. Resolution Strategy
* Register a centralized signal handler for `signal.SIGINT` and `signal.SIGTERM`.
* On receiving an interruption signal:
  * Set a global `_SHUTDOWN_REQUESTED = True` flag.
  * Allow any ongoing atomic command to finish cleanly.
  * Stop initiating further file or track processing.
  * Trigger resource cleanup (`unload_whisper_model`).
  * Exit with standard termination status codes (130 for SIGINT, 143 for SIGTERM).
  * If a second signal is received immediately, force exit to ensure responsiveness.

#### 3. Step-by-Step Implementation
1. Import `signal`.
2. Define a global shutdown state and signal handler function `_signal_handler(signum, frame)`.
3. Register handlers with `signal.signal(signal.SIGINT, _signal_handler)` and `signal.signal(signal.SIGTERM, _signal_handler)`.
4. In `AudioMediaChecker.process_file()`, check shutdown status before each track and sampling attempt.
5. In `main()`, check shutdown status at the start of each file iteration; break loop if shutdown requested.
6. Ensure cleanup runs in `finally:` block before exiting with code `128 + signum`.

#### 4. Verification Tests & Acceptance Criteria
* Start a multi-file run in `--dry-run` and trigger Ctrl+C during processing.
* Verify log: shutdown message is logged, current step concludes gracefully, subsequent files are not started, Whisper is unloaded, and exit code is 130.

---

### TASK-04: Fast Language Detection vs Full Autoregressive Transcription

* **Analysis Reference:** Item 2.1
* **Status:** ✅ Completed

#### 1. Problem Description
Previously, `detect_language` unconditionally executed:
`segments, info = model.transcribe(audio_file, language=None, beam_size=5)`
`transcribe` performs full autoregressive text decoding token-by-token with beam search (`beam_size=5`). Because transcribed sentences are never used for tagging, generating text tokens for 30–90 seconds of audio introduces unnecessary computational overhead.

#### 2. Resolution Strategy
* Decoupled language identification from text decoding:
  * When `--verbose` is specified, run full `model.transcribe()` and iterate over `segments` to log recognized text with timestamps for debugging.
  * In standard and `--json` modes, decode audio via `decode_audio` and run direct language classification via `model.detect_language(audio_np)`. This queries the Whisper encoder and language classification head directly without tokenizer setup or autoregressive generation loops.

#### 3. Step-by-Step Implementation
1. Imported `decode_audio` from `faster_whisper`.
2. Updated `detect_language(self, audio_file)` in `AudioMediaChecker.py` with conditional branch based on `self.verbose`.
3. Added defensive `audio_file.seek(0)` before decoding.

#### 4. Verification Tests & Acceptance Criteria
* Verified exact numerical parity between `transcribe` and direct `detect_language` on identical audio samples (probabilities match with `diff = 0.000000`).
* Real-world hardware benchmarks on 30s audio chunks (`base` model):
  * **CPU (Intel Core i5-10400, `int8`):** Reduced from **1999.6 ms** (~2.0s) down to **407.6 ms** (~0.4s) $\to$ **4.91x faster** (~1.6s saved per sample).
  * **GPU (NVIDIA RTX 3060 12GB, `float16`):** Reduced from **462.6 ms** down to **33.4 ms** $\to$ **13.83x faster** (nearly instantaneous).
* Real-world library batch throughput benchmark (100 random heterogeneous files, 155 audio tracks on RTX 3060):
  * 10 files (13 tracks): 20.0s (2.00s/file, 1.54s/track)
  * 25 files (37 tracks): 52.7s (2.11s/file, 1.42s/track)
  * 50 files (77 tracks): 112.6s (2.25s/file, 1.46s/track)
  * 100 files (155 tracks): 237.7s (2.38s/file, 1.53s/track)
* Tested `--verbose` mode to verify recognized text segments remain visible.
* Tested `--json` mode to confirm clean JSON payload without extra output.

---

### TASK-05: Environment Variables Support (Docker-Friendly Configuration)

* **Analysis Reference:** Item 3.3
* **Status:** Planned

#### 1. Problem Description
In Docker and Docker Compose stacks, specifying long CLI flags is less convenient than providing environment variables (`environment:` in Compose or `.env` files).

#### 2. Resolution Strategy
* Allow `argparse` to read defaults from standardized environment variables (`AMC_MODEL`, `AMC_CONFIDENCE`, `AMC_FORCE_LANGUAGE`, `AMC_CHECK_ALL_TRACKS`, `AMC_DRY_RUN`, `AMC_GPU`).
* Command-line arguments always override environment variable values.

#### 3. Step-by-Step Implementation
1. Map environment variables with `AMC_` prefix.
2. Supply `os.getenv` values to `argparse` defaults.
3. Update `README.md` documentation.

#### 4. Verification Tests & Acceptance Criteria
* Launch container with `AMC_CONFIDENCE=80` and verify the script uses 80 without CLI flag.

---

### TASK-06: Parallel Pipeline: FFmpeg Extraction & Whisper Inference

* **Analysis Reference:** Item 2.3
* **Status:** ✅ Completed

#### 1. Problem Description
The previous execution flow was completely synchronous and sequential:
1. FFmpeg ran, extracted audio sample $i$, and wrote to memory (Whisper and GPU/CPU remained idle).
2. Whisper received the audio and ran neural network inference on sample $i$ (FFmpeg and disk remained idle).
3. Once finished, the cycle repeated for sample $i+1$.
Across multiple tracks and files, this blocking pattern compounded idle latency.

#### 2. Resolution Strategy
* Decouple audio extraction (I/O) from neural inference (GPU/CPU) using a generator method (`extract_samples_pipelined`) leveraging a single-worker `concurrent.futures.ThreadPoolExecutor(max_workers=1)`.
* While Whisper runs inference on sample $i$ on the main thread, the background worker prefetches sample $i+1$ from disk via FFmpeg.
* The prefetch queue is capped to 1 sample ahead to prevent unnecessary RAM consumption.
* Integrated with graceful interruption handling (`_SHUTDOWN_REQUESTED`) and cleanup on generator termination (`executor.shutdown(wait=False, cancel_futures=True)`).

#### 3. Step-by-Step Implementation
1. Added `concurrent.futures` import.
2. Implemented `extract_samples_pipelined(audio_position, positions, duration_seconds)` generator yielding `(start_percent, audio_segment)` tuples.
3. Updated Attempt 1 and subsequent attempt loops in `process_file()` to consume the pipelined generator.
4. Added shutdown check and non-blocking executor cleanup.

#### 4. Verification Tests & Acceptance Criteria
* Real file single-track dry-run test: verified all 4 sample points extracted and inferred seamlessly; extraction latency between samples eliminated.
* Multi-file folder benchmark on 143-file television series: average per-file processing time reduced from ~3.65s to ~2.56s (~28% reduction in overall runtime).
* Verified clean cooperative termination on `SIGINT` (Ctrl+C) with exit code 130 and zero lingering background threads.
* Verified `--json` output compatibility and valid JSON structure.

---

## ⏸️ BACKLOG & ON-HOLD ITEMS

---

### BACKLOG-01: `--json` Support for Multiple Folders/Files
* **Analysis Reference:** Item 1.3
* **Status:** On Hold (Backlog)
* **Rationale:** Currently `--json` is strictly restricted to single file runs. Running on folders produces concatenated disjoint JSON arrays without file paths.
* **Future Plan:** Implement a global accumulator in `main()` outputting a single structured JSON payload:
  ```json
  [
    {
      "file": "/data/Movie1.mkv",
      "tracks": [{"track": 1, "language": "ita"}]
    }
  ]
  ```

---

### BACKLOG-02: Investigation of `ffprobe` vs `mkvpropedit` Track Index Alignment
* **Analysis Reference:** Item 1.5
* **Status:** On Hold (Backlog)
* **Rationale:** In MKV files containing attachments (fonts, cover art), `ffprobe` stream index `+ 1` may not strictly correspond to `mkvpropedit` target track number.
* **Future Plan:** Explore Matroska Track UID matching or `track:aN` type-specific selectors.

---

### BACKLOG-04: Post-Processing Webhook Notifications System
* **Analysis Reference:** Item 3.5
* **Status:** On Hold (Backlog)
* **Rationale:** Future option to dispatch scan summaries to Discord/Telegram webhooks or HTTP endpoints upon completion.
