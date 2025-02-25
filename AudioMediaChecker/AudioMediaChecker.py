import argparse
import os
import signal
import sys
import subprocess
import json
import random
import logging
from faster_whisper import WhisperModel
from pydub import AudioSegment
import pycountry
import io
from pathlib import Path
import psutil
from tqdm import tqdm
import datetime

def _setup_logger(verbose=False):
    """
    Configures and returns a logger with stream on stdout.
    
    Arguments:
      verbose (bool): if True, sets the DEBUG level, otherwise INFO.

    Returns:
      logging.Logger: the configured logger.
    """
    logger = logging.getLogger(__name__)
    # Evita duplicazioni di log se il logger è già configurato
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    return logger

def find_files(folder_path: Path, max_depth: int, current_level: int = 0):
    """
    Search for files with the .mkv extension in 'folder_path' by exploring to the specified depth.
    
    Arguments:
      folder_path (Path): starting directory.
      max_depth (int): depth levels to explore;
                       if 0, includes all subdirectories (unlimited recursion).
                       If > 0, only sub-levels such that current_level < max_depth are explored,
                       where the starting directory equals level 0.
      current_level (int): current level in recursion (not to be set from outside).

    Returns:
      list[Path]: files found.
    """
    # If max_depth is 0, we perform an unlimited recursive search.
    if max_depth == 0:
        return list(folder_path.rglob('*.mkv'))
    
    files = list(folder_path.glob('*.mkv'))
    
    # If we have not reached the maximum level, we explore the subfolders.
    if current_level < max_depth:
        for subdir in folder_path.iterdir():
            if subdir.is_dir():
                files.extend(find_files(subdir, max_depth, current_level + 1))
    return files

class AudioMediaChecker:
    def __init__(self, file_path, check_all_tracks=False, verbose=False, dry_run=False, 
                 force_language=None, confidence_threshold=65, model='base', gpu=False, logger=None):
        """
        Initialize the media file controller.

        Arguments:
          file_path (str): file path.
          check_all_tracks (bool): if True, parses all audio tracks.
          verbose (bool): enable detailed logging.
          dry_run (bool): if True, does not perform edit operations.
          force_language (str): force language code in ISO 639-2 format.
          confidence_threshold (int): confidence threshold.
          model (str): whisper model to be used.
          gpu (bool): if True, use GPU.
          logger (logging.Logger): logger to use.
        """
        self.verbose = verbose
        self.file_path = Path(file_path)
        self.check_all_tracks = check_all_tracks
        self.dry_run = dry_run
        self.force_language = force_language
        self.confidence_threshold = confidence_threshold
        self.interrupted = False
        self.whisper_model_size = model
        self.gpu = gpu
        self.logger = logger if logger else _setup_logger(verbose)

        if self.file_path.suffix.lower() != '.mkv':
            raise ValueError(f"Formato file non supportato: {self.file_path}")

        # Get the multimedia information once and save it.
        self.media_info = self.get_media_info()
        self.total_duration = float(self.media_info['format']['duration'])

        self._validate_model_ram()

    def _validate_model_ram(self):
        """
        Verify that the available RAM is sufficient for the selected model.
        """
        model_requirements = {
            'tiny': 2, 'base': 3, 'small': 5, 'medium': 10, 'large': 16, 'large-v3': 16
        }
        required_ram = model_requirements.get(self.whisper_model_size, 4)

        if self._system_ram_gb() < required_ram:
            raise MemoryError(f"Il modello {self.whisper_model_size} richiede almeno {required_ram}GB di RAM")

    def _best_compute_type(self):
        """
        Determines the best type of computation based on the model and available RAM.
        """
        model_size_map = {
            'tiny': 'int8',
            'base': 'int8',
            'small': 'int8',
            'medium': 'int8' if self._system_ram_gb() >= 16 else 'float32',
            'large': 'float32',
            'large-v3': 'float32'
        }
        return model_size_map.get(self.whisper_model_size, 'int8')

    def _optimal_cpu_threads(self):
        """
        It calculates the optimal number of CPU threads (maximum 8).
        """
        available_cores = os.cpu_count() or 4
        return min(available_cores, 8)

    @staticmethod
    def _system_ram_gb():
        """
        Returns the amount of system RAM (in GB).
        """
        try:
            return round(psutil.virtual_memory().total / (1024 ** 3))
        except Exception:
            return 4  # Conservative value if RAM cannot be determined.

    def process_file(self):
        """
        Main process for analyzing and possibly updating audio track tags.
        """
        if self.interrupted:
            return False

        # self.logger.info(f"File analysis: {self.file_path}")
        tqdm.write(f" - File analysis: {self.file_path}")
        
        if not self.file_path.exists():
            self.logger.error("File not found")
            return False

        try:
            # Using the media_info obtained in __init__.
            audio_streams = [s for s in self.media_info['streams'] if s['codec_type'] == 'audio']

            if not audio_streams:
                self.logger.warning("No audio track found in the file")
                return False

            # Select the tracks to be analyzed
            tracks_to_analyze = self.get_tracks_to_analyze(audio_streams)
            
            if not tracks_to_analyze:
                self.logger.info("There are no unknown audio tracks to analyze")
                self.logger.info("--" * 30)
                return True

            self.logger.info("--" * 30)
            num_tracks = len(tracks_to_analyze)
            self.logger.info(f"Analysis of {num_tracks} audio {'tracks' if num_tracks > 1 else 'track'}")
            self.logger.info("--" * 30)
            
            first_attempt_positions = [10, 35, 60, 85]
            first_attempt_duration = 30

            for track in tracks_to_analyze:
                if self.interrupted:
                    return False

                stream = track['stream']
                # Relative index for ffmpeg
                audio_position = track['relative_index']
                # Absolute index as reported by ffprobe (used for mkvpropedit and log).
                ffprobe_index = track['ffprobe_index']

                self.log_stream_info(stream)
                self.logger.info("--" * 30)

                # First attempt
                self.logger.info(f"Attempt 1 - Track with ffprobe index {ffprobe_index}")
                self.logger.info("--" * 30)

                first_attempt_confidences = {}
                for start_percent in first_attempt_positions:
                    audio_segment = self.extract_audio_sample(audio_position, start_percent, first_attempt_duration)
                    if audio_segment is None:
                        continue
                    detected_lang, confidence = self.detect_language(audio_segment)
                        
                    if detected_lang not in first_attempt_confidences:
                        first_attempt_confidences[detected_lang] = {'total_confidence': 0, 'count': 0}
                    first_attempt_confidences[detected_lang]['total_confidence'] += confidence
                    first_attempt_confidences[detected_lang]['count'] += 1

                    self.logger.info(f"Position {start_percent}%: Language detected '{detected_lang}', Confidence {confidence * 100:.2f}%")

                # Save only if there are detections.
                if first_attempt_confidences:
                    total_detections = sum(lang_data['count'] for lang_data in first_attempt_confidences.values())
                    first_attempt_weighted_averages = {}
                    for lang, stats in first_attempt_confidences.items():
                        average_confidence = stats['total_confidence'] / stats['count']
                        weighted_average = (average_confidence * stats['count']) / total_detections
                        first_attempt_weighted_averages[lang] = weighted_average * 100

                    self.logger.info("--" * 30)
                    self.logger.info("Weighted averages of the confidences of each language surveyed:")
                    for lang, weighted_avg in first_attempt_weighted_averages.items():
                        self.logger.info(f"-> {lang}: {weighted_avg:.2f}%")

                    detected_lang = max(first_attempt_weighted_averages, key=first_attempt_weighted_averages.get)
                    confidence_percent = first_attempt_weighted_averages[detected_lang]
                else:
                    detected_lang = None
                    confidence_percent = 0

                self.logger.info("--" * 30)
                self.logger.info(f"Language with higher weighted average: '{detected_lang}', Weighted average: {confidence_percent:.2f}%")

                if confidence_percent >= self.confidence_threshold:
                    self.logger.info(
                        f"Attempt 1 successful for trace with ffprobe index {ffprobe_index}. "
                        f"Language detected: {detected_lang}, Confidence: {confidence_percent:.2f}% >= {self.confidence_threshold}%"
                    )
                    self.handle_detection_result(ffprobe_index, detected_lang, confidence_percent / 100)
                    self.logger.info("--" * 30)
                    continue

                self.logger.info(f"Attempt 1 failed. Weighted average: {confidence_percent:.2f}% < {self.confidence_threshold}%")
                self.logger.info("--" * 30)

                # Subsequent attempts
                used_positions = set(first_attempt_positions)
                for attempt in range(2, 11):
                    attempt_duration = random.randint(30, 90)
                    attempt_positions = []
                        
                    while len(attempt_positions) < 4:
                        new_position = random.randint(5, 95)
                        if new_position not in used_positions:
                            attempt_positions.append(new_position)
                            used_positions.add(new_position)

                    self.logger.info(f"Attempt {attempt} - Track with ffprobe index {ffprobe_index}")
                    self.logger.info("--" * 30)

                    attempt_confidences = {}
                    for start_percent in attempt_positions:
                        audio_segment = self.extract_audio_sample(audio_position, start_percent, attempt_duration)
                        if audio_segment is None:
                            continue
                        detected_lang, confidence = self.detect_language(audio_segment)
                            
                        if detected_lang not in attempt_confidences:
                            attempt_confidences[detected_lang] = {'total_confidence': 0, 'count': 0}
                        attempt_confidences[detected_lang]['total_confidence'] += confidence
                        attempt_confidences[detected_lang]['count'] += 1

                        self.logger.info(f"Position {start_percent}%: Language detected '{detected_lang}', Confidence {confidence * 100:.2f}%")

                    if attempt_confidences:
                        total_detections = sum(lang_data['count'] for lang_data in attempt_confidences.values())
                        attempt_weighted_averages = {}
                        for lang, stats in attempt_confidences.items():
                            average_confidence = stats['total_confidence'] / stats['count']
                            weighted_average = (average_confidence * stats['count']) / total_detections
                            attempt_weighted_averages[lang] = weighted_average * 100

                        self.logger.info("--" * 30)
                        self.logger.info("Weighted averages of the confidences of each language surveyed:")
                        for lang, weighted_avg in attempt_weighted_averages.items():
                            self.logger.info(f"-> {lang}: {weighted_avg:.2f}%")

                        detected_lang = max(attempt_weighted_averages, key=attempt_weighted_averages.get)
                        confidence_percent = attempt_weighted_averages[detected_lang]
                    else:
                        detected_lang = None
                        confidence_percent = 0

                    self.logger.info(f"Language with higher weighted average: '{detected_lang}', Weighted average: {confidence_percent:.2f}%")

                    if confidence_percent >= self.confidence_threshold:
                        self.logger.info(
                            f"Attempt {attempt} successful for trace with ffprobe index {ffprobe_index}. "
                            f"Language detected: {detected_lang}, Confidence: {confidence_percent:.2f}% >= {self.confidence_threshold}%"
                        )
                        self.handle_detection_result(ffprobe_index, detected_lang, confidence_percent / 100)
                        self.logger.info("--" * 30)
                        break

                    self.logger.info(f"Attempt {attempt} failed. Weighted average: {confidence_percent:.2f}% < {self.confidence_threshold}%")
                    self.logger.info("--" * 30)

            return True

        except Exception as e:
            self.logger.error(f"Error during file processing: {str(e)}", exc_info=self.verbose)
            return False

    def get_tracks_to_analyze(self, audio_streams):
        """Select the audio tracks to be analyzed according to the parameters.

        For each track, store:
        - 'relative_index': the relative index among the audio tracks only (for ffmpeg)
        - 'ffprobe_index': the absolute index of the stream, as reported by ffprobe
        """
        tracks = []
        relative_index = 0
        for stream in audio_streams:
            tags = stream.get('tags', {})
            current_lang = tags.get('LANGUAGE', None) or tags.get('language', None)
            if self.check_all_tracks or not current_lang:
                tracks.append({
                    'stream': stream,
                    'relative_index': relative_index,   # To use in ffmpeg: 0:a:{relative_index}
                    'ffprobe_index': stream.get('index')  # Use with mkvpropedit to identify the exact track
                })
            relative_index += 1
        return tracks

    def log_stream_info(self, stream):
        """
        Logga le informazioni della traccia audio.
        """
        bitrate = stream.get('bit_rate')
        info = {
            'Index': stream.get('index', 'n.d.'),
            'Codec': stream.get('codec_name', 'unknown'),
            'Current language': stream.get('tags', {}).get('language', 'not set'),
            'Bitrate': f"{int(bitrate) // 1000} Kb/s" if bitrate else 'unknown'
        }
        self.logger.info("Audio track details:")
        for k, v in info.items():
            self.logger.info(f"• {k}: {v}")

    def handle_detection_result(self, stream_index, detected_lang, confidence):
        """
        Handles the result of language detection:
         - converts the code to ISO 639-2 (using pycountry)
         - checks the confidence obtained
         - updates the trace tag if necessary
        
        Arguments:
          stream_index (int): stream index (ffprobe)
          detected_lang (str): detected language code
          confidence (float): confidence (0-1)
        """
        self.logger.debug(f"Start handle_detection_result for trace {stream_index}")

        try:
            detected_lang_3 = pycountry.languages.get(alpha_2=detected_lang).alpha_3
        except AttributeError:
            self.logger.warning(f"Language code not found for {detected_lang}. Using the original code.")
            detected_lang_3 = detected_lang

        current_lang = self.media_info['streams'][stream_index].get('tags', {}).get('language')
        self.logger.debug(f"Current language by track {stream_index}: {current_lang}")

        confidence_percent = confidence * 100

        if detected_lang_3:
            self.logger.debug(f"Language detected for track {stream_index}: {detected_lang_3} (original: {detected_lang})")

            if confidence_percent >= self.confidence_threshold:
                if detected_lang_3 != current_lang:
                    self.logger.info(f"Recognized language for track {stream_index}: {detected_lang_3} with confidence {confidence_percent:.2f}%")
                    self.update_language_tag(stream_index, detected_lang_3)
                else:
                    self.logger.info(f"Language by track {stream_index} remains unchanged: {detected_lang_3} with confidence {confidence_percent:.2f}%")
            else:
                if self.force_language is not None:
                    if self.force_language == '':
                        self.logger.info(f"Recognized language for track {stream_index}: {detected_lang_3} forced under threshold")
                        self.update_language_tag(stream_index, detected_lang_3)
                    else:
                        self.logger.info(f"Forced language for track {stream_index}: {self.force_language}")
                        self.update_language_tag(stream_index, self.force_language)
                else:
                    self.logger.info(f"Recognized language for track {stream_index}: {detected_lang_3} with confidence {confidence_percent:.2f}%, but below the required threshold")
        else:
            self.logger.warning(f"No language detected by trace {stream_index} (confidence {confidence_percent:.2f}%)")
            if self.force_language and self.force_language != '':
                self.logger.info(f"Forced language for track {stream_index}: {self.force_language}")
                self.update_language_tag(stream_index, self.force_language)
            else:
                self.logger.debug(f"No update by track {stream_index}")

        self.logger.debug(f"Done handle_detection_result for track {stream_index}")

    def get_media_info(self):
        """
        Extracts media file information using ffprobe.
        Returns:
          dict: information in JSON format.
        """
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(self.file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not result.stdout:
            raise RuntimeError("Error executing ffprobe")
        return json.loads(result.stdout)

    def update_language_tag(self, stream_index, language):
        """
        Updates the language tag for the track identified by stream_index.
        
        Arguments:
          stream_index (int): stream index (ffprobe) to update the tag to.
          language (str): new language code (ISO 639-2).
        """
        if not language:
            self.logger.info(f"No language to set by track {stream_index}")
            return

        cmd = [
            'mkvpropedit',
            str(self.file_path),
            '--edit', f'track:{stream_index + 1}',  # mkvpropedit use index  base-1
            '--set', f'language={language}'
        ]

        if not self.dry_run:
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                self.logger.info(f"Updated language tag for track {stream_index}: {language}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error running mkvpropedit: {e.stderr}")
        else:
            self.logger.info(f"[DRY RUN] Update language tag per track {stream_index}: {language}")

    def detect_language(self, audio_file):
        """
        Performs language detection using the Whisper model.

        Arguments:
          audio_file (file-like): audio sample in BytesIO format.

        Returns:
          tuple: (language detected (str), confidence (float))
        """
        model_size = self.whisper_model_size
        device = 'cuda' if self.gpu else 'cpu'
        compute_type = self._best_compute_type()
        cpu_threads = self._optimal_cpu_threads() if device == 'cpu' else 0

        self.logger.info("Beginning language detection")
        self.logger.debug(f"Whisper configuration for {device}: compute_type={compute_type}, threads={cpu_threads or 'auto'}")

        # NOTE: here you load the model every time you call. It could be improved by loading it only once,
        # e.g., by saving it in self.whisper_model on first use.
        model = WhisperModel(model_size, 
                              device=device, 
                              compute_type=compute_type, 
                              cpu_threads=cpu_threads,
                              download_root="/models")

        segments, info = model.transcribe(audio_file, language=None, beam_size=5)
        detected_language = info.language

        if self.verbose:
            self.logger.debug("Recognized text:")
            for segment in segments:
                self.logger.debug(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

        if self.verbose:
            self.logger.info(f"Detected language: {detected_language} with confidence: {info.language_probability:.2f}")

        return detected_language, info.language_probability

    def extract_audio_sample(self, audio_position, start_percent, duration_seconds):
        """
        Extracts an audio sample in WAV format of the specified duration from a percentage of the file.

        Arguments:
          audio_position (int): index of the audio track (for ffmpeg).
          start_percent (float): start percentage of the sample.
          duration_seconds (float): duration of the sample in seconds.
        
        Return:
          BytesIO: campione audio; None in caso di errore.
        """
        try:
            audio_sample = io.BytesIO()
            
            # Reuse self.total_duration if available
            total_duration = self.total_duration
            start_time_seconds = (total_duration * start_percent) / 100

            extract_cmd = [
                'ffmpeg', '-y',
                '-ss', f'{start_time_seconds:.2f}',
                '-i', str(self.file_path),
                '-t', f'{duration_seconds:.2f}',
                '-map', f'0:a:{audio_position}',
                '-ac', '1',
                '-ar', '16000',
                '-acodec', 'pcm_s16le',
                '-f', 'wav',
                '-'
            ]

            with subprocess.Popen(extract_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
                stdout, stderr = process.communicate()

            if process.returncode != 0:
                self.logger.error(f"Sample extraction error by position {start_percent}:")
                self.logger.error(f"Command: {' '.join(extract_cmd)}")
                self.logger.error(f"Error: {stderr.decode('utf-8', errors='ignore')}")
                raise subprocess.CalledProcessError(process.returncode, extract_cmd, stdout, stderr)

            audio_sample.write(stdout)
            audio_sample.seek(0)
            return audio_sample

        except Exception as e:
            self.logger.error(f"Sample extraction error: {str(e)}")
            return None

def main():
    checker = None
    try:
        VALID_MODELS = ['tiny', 'base', 'small', 'medium', 'large', 'large-v3']

        parser = argparse.ArgumentParser(description='Analyzes and corrects language tags of audio tracks')
        parser.add_argument('--file', help='Path of the file to be analyzed')
        parser.add_argument('--folder', help='Directory path to be parsed')
        parser.add_argument('--recursive', nargs='?', const=0, type=int,
                    help="""Depth levels to explore.
                    If 0 or omitted, the search is unlimited (the starting folder and all subdirectories).
                    If > 0, the search is limited to that number of levels (starting folder is level 0).""")
        parser.add_argument('--check-all-tracks', action='store_true', 
                            help='Analyzes all audio tracks, not just those without tags')
        parser.add_argument('--verbose', action='store_true', 
                            help='Enable detailed logging')
        parser.add_argument('--dry-run', action='store_true',
                            help='Simulates operations without modifying the file')
        parser.add_argument('--force-language', nargs='?', const='', 
                            help='Language to be set when detection fails. Use ISO 639-2 format (3 letters)')
        parser.add_argument('--confidence', type=int, default=65,
                            help='Confidence threshold for language detection (default: 65)')
        parser.add_argument('--model', 
                            choices=VALID_MODELS,
                            default='base',
                            help=f"Whisper model (size): {' '.join(VALID_MODELS)}, default: %(default)s")
        parser.add_argument('--gpu', action='store_true', help='Use GPU for language detection (optional)')
        parser.add_argument('--help-languages', action='store_true', help='Show a list of available language codes')

        args = parser.parse_args()

        logger = _setup_logger(args.verbose)

        if args.help_languages:
            print("Available language codes (ISO 639-2 format):")
            for language in pycountry.languages:
                if hasattr(language, 'alpha_3'):
                    print(f"{language.alpha_3} - {language.name}")
            sys.exit(0)

        if not args.file and not args.folder:
            parser.error("the following arguments are required: --file or --folder")

        # Forced language code validation
        if args.force_language:
            if args.force_language != '':
                language_obj = pycountry.languages.get(alpha_3=args.force_language)
                if language_obj is not None:
                    logger.debug(f"Forced language set to: {args.force_language} -> {language_obj.name}")
                else:
                    logger.info(f"Error: '{args.force_language}' is not a valid language code according to ISO 639-2.")
                    logger.info("For a list of available codes, use the option --help-languages.")
                    sys.exit(1)
            else:
                logger.debug("Forces tongue detection even if below threshold.")

        # Validation of confidence threshold
        if args.confidence < 1 or args.confidence > 100:
            print("Error: the confidence threshold should be between 1 and 100")
            sys.exit(1)

        files_to_process = []

        if args.file:
            file_path = Path(args.file)
            if file_path.suffix.lower() != '.mkv':
                print(f"Error: the file must be in MKV format. File provided: {file_path}")
                sys.exit(1)
            files_to_process.append(file_path)

        if args.folder:
            folder_path = Path(args.folder)
            if not folder_path.is_dir():
                print(f"Error: '{folder_path}' is not a valid directory.")
                sys.exit(1)
            
            # If --recursive is not passed, args.recursive will be None,
            # and then a NON-recursive search will be done (only in the source directory)
            if args.recursive is None:
                # In this case we consider only the indicated directory (no recursion)
                depth = 0  # We can decide to handle it as non-recursive
                files_to_process.extend(list(folder_path.glob('*.mkv')))
            else:
                depth = args.recursive
                files_to_process.extend(find_files(folder_path, depth))

        if not files_to_process:
            print("No MKV files found.")
            sys.exit(1)

        if args.verbose:
            params = {
                'check_all_tracks': args.check_all_tracks,
                'dry_run': args.dry_run,
                'force_language': args.force_language if args.force_language is not None else 'False',
                'confidence_threshold': args.confidence,
                'model': args.model,
                'gpu': args.gpu
            }
            logger.info("Execution parameters:")
            for param, value in params.items():
                logger.info(f"  {param}: {value}")
            logger.info("--" * 30)

        with tqdm(total=len(files_to_process), desc=" - INFO - Processing files", unit="file", initial=1, leave=False) as pbar:
            for file_path in files_to_process:

                now = datetime.datetime.now()
                timestamp = now.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]  # Format the date and time with milliseconds
                pbar.set_description(f"{timestamp} - INFO - Processing files")

                checker = AudioMediaChecker(
                    str(file_path),
                    check_all_tracks=args.check_all_tracks,
                    verbose=args.verbose,
                    dry_run=args.dry_run,
                    force_language=args.force_language,
                    confidence_threshold=args.confidence,
                    model=args.model,
                    gpu=args.gpu,
                    logger=logger
                )
                checker.process_file()
                pbar.update(1)  # Update the progress bar after processing the file


        logger.info("Script successfully completed.")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nOperation aborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()