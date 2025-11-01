# language_fixer.py
import os
import subprocess
import json
import tempfile
import sys
import time
import requests
import sqlite3
import re
import logging
import threading
from collections import Counter, defaultdict
from datetime import datetime

# --- VERSION INFORMATION ---
__version__ = "1.1.0-beta.1"
__app_name__ = "Language-Fixer"

# --- EARLY DEFINITIONS ---
LOG_LEVEL_FROM_ENV = os.getenv("LOG_LEVEL", "info").upper()

def setup_logging():
    """Konfiguriert das globale Logging."""
    log_level = getattr(logging, LOG_LEVEL_FROM_ENV, logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(log_level)
    if logger.hasHandlers():
        logger.handlers.clear()
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-8s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# Helper function for parsing boolean env vars
def parse_bool(env_var_name, default=False):
    """Parses a boolean environment variable ('true', '1', 't'). Case-insensitive."""
    value = os.getenv(env_var_name, str(default)).lower()
    return value in ('true', '1', 't')

# --- (1) CONFIGURATION ---
DB_PATH = os.getenv("DB_PATH", "/config/langfixer.db")
WHISPER_API_URL = os.getenv("WHISPER_API_URL")
WHISPER_TIMEOUT = int(os.getenv("WHISPER_TIMEOUT", "300"))
RUN_INTERVAL_SECONDS = int(os.getenv("RUN_INTERVAL_SECONDS", "43200"))
DRY_RUN = parse_bool("DRY_RUN", True)  # Default TRUE for safety!
MAX_FAILURES = int(os.getenv("MAX_FAILURES", "3"))
SONARR_URL = os.getenv("SONARR_URL")
RADARR_URL = os.getenv("RADARR_URL")
SONARR_API_KEY = os.getenv("SONARR_API_KEY")
RADARR_API_KEY = os.getenv("RADARR_API_KEY")
SONARR_PATHS_RAW = os.getenv("SONARR_PATHS", "/media/tv")
RADARR_PATHS_RAW = os.getenv("RADARR_PATHS", "/media/movies")
RUN_CLEANUP = parse_bool("RUN_CLEANUP", True)

# Smart defaults: If DRY_RUN=false, then unset remove flags default to false (safe)
# If DRY_RUN=true (default), then unset remove flags default to true (for testing)
remove_default = DRY_RUN  # true in dry-run mode, false in production mode
REMOVE_AUDIO = parse_bool("REMOVE_AUDIO", remove_default)
REMOVE_SUBTITLES = parse_bool("REMOVE_SUBTITLES", remove_default)
REMOVE_ATTACHMENTS = parse_bool("REMOVE_ATTACHMENTS", remove_default)
RENAME_AUDIO_TRACKS = parse_bool("RENAME_AUDIO_TRACKS", True)  # Always safe
REMOVE_FONTS = parse_bool("REMOVE_FONTS", False)  # Conservative default
KEEP_COMMENTARY = parse_bool("KEEP_COMMENTARY", True)
LOG_STATS_ON_COMPLETION = parse_bool("LOG_STATS_ON_COMPLETION", True)
BATCH_COMMIT_SIZE = int(os.getenv("BATCH_COMMIT_SIZE", "10"))

# Process Subprocess Timeouts from Env Vars
FFMPEG_TIMEOUT = int(os.getenv("FFMPEG_TIMEOUT", "1800")) # Default 30 minutes
MKVPROPEDIT_TIMEOUT = int(os.getenv("MKVPROPEDIT_TIMEOUT", "300")) # Default 5 minutes
FFMPEG_SAMPLE_TIMEOUT = int(os.getenv("FFMPEG_SAMPLE_TIMEOUT", "60")) # Default 1 minute

# --- Sprachcode-Definitionen ---
LANG_CODE_MAP = {
    'en': 'eng', 'eng': 'eng', 'de': 'deu', 'ger': 'deu', 'deu': 'deu', 'ja': 'jpn', 'jap': 'jpn', 'jpn': 'jpn',
    'fr': 'fre', 'fra': 'fre', 'fre': 'fre', 'es': 'spa', 'spa': 'spa', 'it': 'ita', 'ita': 'ita', 'cs': 'cze',
    'cze': 'cze', 'ces': 'cze', 'da': 'dan', 'dan': 'dan', 'el': 'gre', 'gre': 'gre', 'ell': 'gre', 'fi': 'fin',
    'fin': 'fin', 'hu': 'hun', 'hun': 'hun', 'ko': 'kor', 'kor': 'kor', 'nl': 'dut', 'dut': 'dut', 'nld': 'dut',
    'no': 'nor', 'nor': 'nor', 'nob': 'nor', 'pl': 'pol', 'pol': 'pol', 'pt': 'por', 'por': 'por', 'ro': 'rum',
    'rum': 'rum', 'ron': 'rum', 'ru': 'rus', 'rus': 'rus', 'sv': 'swe', 'swe': 'swe', 'th': 'tha', 'tha': 'tha',
    'tr': 'tur', 'tur': 'tur', 'uk': 'ukr', 'ukr': 'ukr', 'vi': 'vie', 'vie': 'vie', 'zh': 'chi', 'chi': 'chi',
    'zho': 'chi', 'ar': 'ara', 'ara': 'ara', 'he': 'heb', 'heb': 'heb', 'hr': 'hrv', 'hrv': 'hrv', 'id': 'ind',
    'ind': 'ind', 'ms': 'may', 'may': 'may', 'msa': 'may', 'fil': 'fil', 'ca': 'cat', 'cat': 'cat', 'gl': 'glg',
    'glg': 'glg', 'und': 'und'
}
def normalize_lang_code(code):
    if not code: return 'und'
    code = re.sub(r'[\s\'"]', '', str(code)).lower()
    return LANG_CODE_MAP.get(code, code)

def parse_env_list(env_var_name, default_value=""):
    raw_value = os.getenv(env_var_name, default_value)
    logging.debug(f"Raw value for {env_var_name}: '{raw_value}'")
    if not raw_value: return set()
    cleaned_value = raw_value.strip().strip('"').strip("'")
    items = [normalize_lang_code(item) for item in cleaned_value.split(',')]
    result = set(filter(None, items))
    logging.debug(f"Parsed value for {env_var_name}: {result}")
    return result

def parse_env_single(env_var_name, default_value=""):
    raw_value = os.getenv(env_var_name, default_value)
    logging.debug(f"Raw value for {env_var_name}: '{raw_value}'")
    if not raw_value: return ""
    result = normalize_lang_code(raw_value)
    logging.debug(f"Parsed value for {env_var_name}: '{result}'")
    return result

KEEP_AUDIO_LANGS = parse_env_list("KEEP_AUDIO_LANGS", "jpn,deu,eng,und")
KEEP_SUBTITLE_LANGS = parse_env_list("KEEP_SUBTITLE_LANGS", "jpn,deu,eng")
DEFAULT_AUDIO_LANG = parse_env_single("DEFAULT_AUDIO_LANG", "jpn")
DEFAULT_SUBTITLE_LANG = parse_env_single("DEFAULT_SUBTITLE_LANG", "deu")

COMMENTARY_KEYWORDS = ['commentary', 'kommentar', 'director', 'regisseur', 'creator', 'audio description']
MODIFIED_SONARR_PATHS = set()
MODIFIED_RADARR_PATHS = set()
SCAN_PATHS = {}

def print_configuration_summary():
    """
    Displays all configuration values for 30 seconds at startup.
    
    This intentional delay gives users time to review settings and cancel
    if needed before any file operations begin. Particularly important when
    DRY_RUN=false to prevent accidental modifications.
    """
    print("\n" + "="*80)
    print(f"🎬 {__app_name__.upper()} v{__version__}")
    print("="*80)
    
    # Version & Update Check
    print("� VERSION & UPDATES:")
    print(f"   Aktuelle Version: {__version__}")
    print(f"   Update Check:     https://github.com/Randomname653/language-fixer/releases")
    print(f"   Docker Image:     luckyone94/language-fixer:latest")
    print("   💡 Tipp: Verwende ':latest' Tag für automatische Updates!")
    print("   🔄 Update Befehl: docker compose pull && docker compose up -d")
    print()
    
    # Safety Mode
    safety_icon = "🔒" if DRY_RUN else "⚠️"
    print(f"{safety_icon} MODUS:           {'DRY-RUN (SICHER - keine Änderungen)' if DRY_RUN else 'PRODUKTIONS-MODUS (Dateien werden geändert!)'}")
    print()
    
    # Core Settings
    print("📁 KERN-EINSTELLUNGEN:")
    print(f"   Database:         {DB_PATH}")
    print(f"   Log Level:        {LOG_LEVEL_FROM_ENV}")
    print(f"   Scan Interval:    {RUN_INTERVAL_SECONDS}s ({RUN_INTERVAL_SECONDS//3600}h {(RUN_INTERVAL_SECONDS%3600)//60}m)")
    print(f"   Max Failures:     {MAX_FAILURES}")
    print(f"   Batch Commits:    {BATCH_COMMIT_SIZE} Dateien")
    print()
    
    # Processing Logic
    print("⚙️ VERARBEITUNGS-LOGIK:")
    safe_mode_note = " (auto: false wenn DRY_RUN=false)" if not DRY_RUN else " (auto: true wenn DRY_RUN=true)"
    audio_note = safe_mode_note if os.getenv("REMOVE_AUDIO") is None else " (explizit gesetzt)"
    sub_note = safe_mode_note if os.getenv("REMOVE_SUBTITLES") is None else " (explizit gesetzt)"
    att_note = safe_mode_note if os.getenv("REMOVE_ATTACHMENTS") is None else " (explizit gesetzt)"
    
    print(f"   Remove Audio:     {REMOVE_AUDIO}{audio_note}")
    print(f"   Remove Subtitles: {REMOVE_SUBTITLES}{sub_note}")
    print(f"   Remove Attachments: {REMOVE_ATTACHMENTS}{att_note}")
    print(f"   Rename Audio:     {RENAME_AUDIO_TRACKS}")
    print(f"   Remove Fonts:     {REMOVE_FONTS}")
    print(f"   Keep Commentary:  {KEEP_COMMENTARY}")
    print(f"   Cleanup:          {RUN_CLEANUP}")
    print()
    
    # Language Settings
    print("🌐 SPRACH-EINSTELLUNGEN:")
    print(f"   Keep Audio:       {', '.join(sorted(KEEP_AUDIO_LANGS))}")
    print(f"   Keep Subtitles:   {', '.join(sorted(KEEP_SUBTITLE_LANGS))}")
    print(f"   Default Audio:    {DEFAULT_AUDIO_LANG}")
    print(f"   Default Subtitle: {DEFAULT_SUBTITLE_LANG}")
    print()
    
    # Timeouts
    print("⏱️ TIMEOUT-EINSTELLUNGEN:")
    print(f"   FFmpeg:           {FFMPEG_TIMEOUT}s ({FFMPEG_TIMEOUT//60}min)")
    print(f"   mkvpropedit:      {MKVPROPEDIT_TIMEOUT}s ({MKVPROPEDIT_TIMEOUT//60}min)")
    print(f"   Sampling:         {FFMPEG_SAMPLE_TIMEOUT}s")
    print(f"   Whisper API:      {WHISPER_TIMEOUT}s ({WHISPER_TIMEOUT//60}min)")
    print()
    
    # Integrations
    print("🔗 INTEGRATIONEN:")
    print(f"   Whisper API:      {'✅ Aktiviert' if WHISPER_API_URL else '❌ Deaktiviert'}")
    print(f"   Sonarr:           {'✅ Aktiviert' if SONARR_URL and SONARR_API_KEY else '❌ Deaktiviert'}")
    print(f"   Radarr:           {'✅ Aktiviert' if RADARR_URL and RADARR_API_KEY else '❌ Deaktiviert'}")
    print()
    
    # Paths
    print("📂 ÜBERWACHTE PFADE:")
    if SCAN_PATHS.get("sonarr"):
        print(f"   Sonarr:           {', '.join(SCAN_PATHS['sonarr'])}")
    if SCAN_PATHS.get("radarr"):
        print(f"   Radarr:           {', '.join(SCAN_PATHS['radarr'])}")
    print()
    
    # Safety Warning
    if not DRY_RUN:
        print("⚠️" * 20)
        print("⚠️  WARNUNG: PRODUKTIONS-MODUS AKTIV!")
        print("⚠️  Dateien werden tatsächlich geändert!")
        print("⚠️  Setze DRY_RUN=true zum Testen!")
        print("⚠️" * 20)
    else:
        print("🔒" * 20)
        print("🔒  SICHER: DRY-RUN MODUS AKTIV")
        print("🔒  Keine Dateien werden geändert")
        print("🔒  Setze DRY_RUN=false für echte Änderungen")
        print("🔒" * 20)
    
    print("="*80)
    print("⏳ Warte 30 Sekunden, damit Konfiguration gelesen werden kann...")
    print("   (Drücke Ctrl+C zum Abbrechen)")
    print("="*80)
    
    # 30 second countdown
    for i in range(30, 0, -1):
        print(f"\r⏳ Starte in {i:2d} Sekunden... {'🔒 DRY-RUN' if DRY_RUN else '⚠️ PRODUKTIV'}", end="", flush=True)
        time.sleep(1)
    
    print(f"\n🚀 Starting Language-Fixer {'(DRY-RUN)' if DRY_RUN else '(PRODUKTIV)'}!")
    print("="*80)
    print()
class ScanStats:
    def __init__(self):
        self.start_time=datetime.now(); self.dirs_scanned=0; self.files_checked=0; self.files_skipped_db=0
        self.files_processed=0; self.files_failed=0; self.audio_tagged=0
        self.lang_counts=defaultdict(int); self.files_remuxed_ffmpeg=0
        self.files_edited_mkvprop=0; self.files_converted_mp4=0
        self.audio_removed=0; self.subs_removed=0; self.attachments_removed=0
        self.audio_renamed=0; self.default_audio_set=0; self.default_sub_set=0
        self.bytes_saved=0
    def get_duration(self):
        duration = datetime.now()-self.start_time
        return str(duration).split('.')[0] # Remove microseconds for cleaner output


# --- Configuration Validation ---
def validate_config():
    """Prüft die Konfiguration auf logische Konsistenz und fehlende Werte."""
    valid = True
    logging.info("⚙️ Prüfe Konfiguration...")

    # Check if Whisper is needed but not configured
    if not WHISPER_API_URL and ('und' not in KEEP_AUDIO_LANGS):
        logging.error("❌ Konfigurationsfehler: 'und' Audiospuren sollen analysiert werden (nicht in KEEP_AUDIO_LANGS), aber WHISPER_API_URL ist nicht gesetzt!")
        valid = False
    elif WHISPER_API_URL:
        if 'und' in KEEP_AUDIO_LANGS:
            logging.warning("⚠️ Whisper API URL ist gesetzt, aber 'und' ist in KEEP_AUDIO_LANGS. Whisper wird NICHT für 'und'-Spuren verwendet.")
        else:
            logging.info("   Whisper wird für 'und'-Spuren verwendet.")

    if DEFAULT_AUDIO_LANG and DEFAULT_AUDIO_LANG not in KEEP_AUDIO_LANGS:
        logging.warning(f"⚠️ Konfigurationswarnung: DEFAULT_AUDIO_LANG ('{DEFAULT_AUDIO_LANG}') ist nicht in KEEP_AUDIO_LANGS ({KEEP_AUDIO_LANGS}). Default-Flag wird möglicherweise für eine Spur gesetzt, die entfernt wird.")

    if DEFAULT_SUBTITLE_LANG and DEFAULT_SUBTITLE_LANG not in KEEP_SUBTITLE_LANGS:
        logging.warning(f"⚠️ Konfigurationswarnung: DEFAULT_SUBTITLE_LANG ('{DEFAULT_SUBTITLE_LANG}') ist nicht in KEEP_SUBTITLE_LANGS ({KEEP_SUBTITLE_LANGS}). Default-Flag wird möglicherweise für eine Spur gesetzt, die entfernt wird.")

    if SONARR_URL and SONARR_API_KEY and not SCAN_PATHS.get("sonarr"):
        logging.error("❌ Konfigurationsfehler: Sonarr ist konfiguriert (URL/API Key), aber keine gültigen SONARR_PATHS angegeben!")
        valid = False
    if RADARR_URL and RADARR_API_KEY and not SCAN_PATHS.get("radarr"):
        logging.error("❌ Konfigurationsfehler: Radarr ist konfiguriert (URL/API Key), aber keine gültigen RADARR_PATHS angegeben!")
        valid = False

    if not valid:
        logging.critical("💥 Kritische Konfigurationsfehler gefunden. Skript wird beendet.")
        sys.exit(1)
    else:
        logging.info("   Konfiguration scheint gültig.")


# --- (2) DATENBANK ---
def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS processed_files (filepath TEXT PRIMARY KEY, mtime REAL NOT NULL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS failed_files (filepath TEXT PRIMARY KEY, mtime REAL NOT NULL, fail_count INTEGER NOT NULL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS cumulative_stats (key TEXT PRIMARY KEY, value INTEGER NOT NULL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS cumulative_lang_stats (lang TEXT PRIMARY KEY, count INTEGER NOT NULL)''')
            keys = [('files_processed', 0), ('files_failed', 0), ('audio_tagged', 0), ('files_remuxed_ffmpeg', 0),
                    ('files_edited_mkvprop', 0), ('files_converted_mp4', 0), ('audio_removed', 0),
                    ('subs_removed', 0), ('attachments_removed', 0), ('audio_renamed', 0),
                    ('default_audio_set', 0), ('default_sub_set', 0), ('bytes_saved', 0)]
            cursor.executemany("INSERT OR IGNORE INTO cumulative_stats (key, value) VALUES (?, ?)", keys)
    except sqlite3.Error as e:
        logging.error(f"❌ DB Init Fehler: {e}")
        sys.exit(1)

def should_skip_file(cursor, filepath, mtime):
    try:
        cursor.execute("SELECT mtime FROM processed_files WHERE filepath = ?", (filepath,))
        r = cursor.fetchone()
        if r and r[0] == mtime: return True, "Erfolg"
        cursor.execute("SELECT mtime, fail_count FROM failed_files WHERE filepath = ?", (filepath,))
        r = cursor.fetchone()
        if r and r[0] == mtime and r[1] >= MAX_FAILURES: return True, "Max. Fehler"
    except sqlite3.Error as e:
        logging.warning(f"DB Fehler (Skip Check) {os.path.basename(filepath)}: {e}")
    return False, ""

def mark_file_as_processed(cursor, filepath, mtime):
    try:
        cursor.execute("REPLACE INTO processed_files (filepath, mtime) VALUES (?, ?)", (filepath, mtime))
    except sqlite3.Error as e:
        logging.warning(f"DB Fehler (Mark Processed) {os.path.basename(filepath)}: {e}")

def increment_failure_count(cursor, filepath, mtime):
    try:
        # Ensure mtime is valid before DB operation
        if not isinstance(mtime, (int, float)):
            logging.error(f"Ungültiger mtime '{mtime}' für increment_failure_count bei {filepath}")
            return # Avoid DB error
        cursor.execute("SELECT mtime, fail_count FROM failed_files WHERE filepath = ?", (filepath,))
        r = cursor.fetchone()
        n = 1
        # Only increment if the mtime matches the failed entry, otherwise reset to 1
        if r and r[0] == mtime:
            n = r[1] + 1
        elif r and r[0] != mtime:
            logging.debug(f"Mtime hat sich geändert für fehlgeschlagene Datei {os.path.basename(filepath)}, setze Fehlerzähler zurück.")
        cursor.execute("REPLACE INTO failed_files (filepath, mtime, fail_count) VALUES (?, ?, ?)", (filepath, mtime, n))
        logging.info(f"  -> Fehler gezählt ({n}/{MAX_FAILURES}) für {os.path.basename(filepath)}.")
    except sqlite3.Error as e:
        logging.warning(f"DB Fehler (Inc Failure) {os.path.basename(filepath)}: {e}")

# Failed State Cleanup: Wird bei Erfolg aufgerufen
def clear_failure_entry(cursor, filepath):
    try:
        logging.debug(f"Lösche Fehlereintrag (falls vorhanden) für {os.path.basename(filepath)}")
        cursor.execute("DELETE FROM failed_files WHERE filepath = ?", (filepath,))
    except sqlite3.Error as e:
        logging.warning(f"DB Fehler (Clear Failure) {os.path.basename(filepath)}: {e}")

def update_cumulative_stats(stats):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            upd = [(stats.files_processed, 'files_processed'), (stats.files_failed, 'files_failed'),
                (stats.audio_tagged, 'audio_tagged'), (stats.files_remuxed_ffmpeg, 'files_remuxed_ffmpeg'),
                (stats.files_edited_mkvprop, 'files_edited_mkvprop'), (stats.files_converted_mp4, 'files_converted_mp4'),
                (stats.audio_removed, 'audio_removed'), (stats.subs_removed, 'subs_removed'),
                (stats.attachments_removed, 'attachments_removed'), (stats.audio_renamed, 'audio_renamed'),
                (stats.default_audio_set, 'default_audio_set'), (stats.default_sub_set, 'default_sub_set'),
                (int(stats.bytes_saved), 'bytes_saved')]
            cursor.executemany("UPDATE cumulative_stats SET value = value + ? WHERE key = ?", upd)
            for lang, count in stats.lang_counts.items():
                cursor.execute("INSERT OR IGNORE INTO cumulative_lang_stats (lang, count) VALUES (?, 0)", (lang,))
                cursor.execute("UPDATE cumulative_lang_stats SET count = count + ? WHERE lang = ?", (count, lang))
    except sqlite3.Error as e:
        logging.warning(f"DB Update Stats Fehler: {e}")

# --- VERSION CHECK ---
def check_for_updates():
    """Prüft GitHub API auf neue Versionen."""
    try:
        logging.debug("Prüfe GitHub API auf Updates...")
        response = requests.get(
            "https://api.github.com/repos/Randomname653/language-fixer/releases/latest",
            timeout=10
        )
        if response.status_code == 200:
            latest = response.json()
            latest_version = latest.get("tag_name", "").lstrip("v")
            if latest_version and latest_version != __version__:
                logging.info(f"🆕 Neue Version verfügbar: v{latest_version} (aktuell: v{__version__})")
                logging.info(f"📥 Download: {latest.get('html_url', 'https://github.com/Randomname653/language-fixer/releases')}")
                logging.info("💡 Docker: Starte Container mit 'docker compose pull' neu für automatisches Update")
                return latest_version
            else:
                logging.debug(f"✅ Version ist aktuell: v{__version__}")
                return None
        else:
            logging.debug(f"GitHub API Fehler: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logging.debug(f"Version Check Fehler: {e}")
        return None
    except Exception as e:
        logging.debug(f"Unerwarteter Version Check Fehler: {e}")
        return None

# --- (3) MEDIA-ANALYSE & HELPER ---
def get_media_info(file_path):
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path]
        logging.debug(f"Running ffprobe: {' '.join(cmd)}")
        r = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
        return json.loads(r.stdout)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else "N/A"
        logging.warning(f"ffprobe Fehler (Code {e.returncode}) {os.path.basename(file_path)}: {stderr}")
    except json.JSONDecodeError as e:
        logging.warning(f"ffprobe JSON Parse Fehler {os.path.basename(file_path)}: {e}")
    except Exception as e:
        logging.warning(f"Unerwarteter ffprobe Fehler {os.path.basename(file_path)}: {e}")
    return None

def detect_language_with_whisper(audio_sample_path):
    if not WHISPER_API_URL:
        logging.error("❌ Whisper API URL nicht konfiguriert.")
        return None
    try:
        with open(audio_sample_path, 'rb') as f:
            files = {'audio_file': (os.path.basename(audio_sample_path), f)}
            params = {'encode': 'true', 'task': 'transcribe', 'output': 'json'}
            logging.debug(f"Calling Whisper API: {WHISPER_API_URL} for {os.path.basename(audio_sample_path)}")
            r = requests.post(WHISPER_API_URL, files=files, params=params, timeout=WHISPER_TIMEOUT)
            r.raise_for_status()
            response_json = r.json()
            lang = response_json.get('language')
            logging.debug(f"Whisper API response: {response_json}")
            return lang
    except requests.Timeout:
        logging.warning(f"  -> Whisper API Timeout nach {WHISPER_TIMEOUT}s für {os.path.basename(audio_sample_path)}")
    except requests.RequestException as e:
        status_code = e.response.status_code if e.response else "N/A"
        logging.warning(f"  -> Whisper API Fehler ({status_code}): {e}")
    except json.JSONDecodeError:
        logging.warning(f"  -> Whisper API hat ungültiges JSON zurückgegeben.")
    except Exception as e:
        logging.warning(f"  -> Unerwarteter Fehler bei Whisper Call: {e}")
    return None

def is_commentary(stream):
    if not KEEP_COMMENTARY: return False
    title = stream.get('tags', {}).get('title', '').lower()
    disposition = stream.get('disposition', {})
    # Check title keywords
    if title and any(k in title for k in COMMENTARY_KEYWORDS):
        return True
    # Check disposition flags
    if disposition.get('comment', 0) == 1 or disposition.get('hearing_impaired', 0) == 1 or disposition.get('visual_impaired', 0) == 1:
        logging.debug(f"Stream als Kommentar/Beschreibung erkannt via Disposition: {disposition}")
        return True
    return False

def format_audio_title(stream, final_lang_tag):
    parts=[]
    orig_t=stream.get('tags',{}).get('title')
    is_comm = is_commentary(stream)

    if is_comm and orig_t:
        parts.append(orig_t)
    elif RENAME_AUDIO_TRACKS:
        try:
            c = stream.get('codec_name', '').upper()
            p = stream.get('profile', '')
            ch = stream.get('channels', 0)

            if c == 'TRUEHD':
                c = 'Dolby Atmos' if p and 'atmos' in p.lower() else 'Dolby TrueHD'
            elif c == 'DTS' and p == 'MA':
                c = 'DTS-HD MA'
            elif c == 'EAC3':
                c = 'Dolby Digital+'
            elif c == 'AC3':
                c = 'Dolby Digital'
            # Add more simplifications (AAC, OPUS, FLAC etc. if desired)

            ls = 'Unknown'
            if ch >= 8: ls = '7.1'
            elif ch >= 6: ls = '5.1'
            elif ch == 2: ls = '2.0'
            elif ch == 1: ls = '1.0'
            # Consider adding more specific layouts if channel_layout is reliable
            elif ch > 0: ls = f"{ch}.0" # Fallback

            if c and ls != 'Unknown': parts.append(f"{c} {ls}")
            elif c: parts.append(c)

        except Exception as e:
            logging.debug(f"  -> Fehler beim Formatieren des Audio-Titels: {e}")
            if orig_t: parts.append(orig_t) # Fallback

    if RENAME_AUDIO_TRACKS and not is_comm and final_lang_tag != 'und':
        ln_map = {'eng': 'English', 'deu': 'German', 'jpn': 'Japanese'} # Add more
        ln = ln_map.get(final_lang_tag, final_lang_tag.upper())

        if parts:
            parts[-1] = f"{parts[-1]} ({ln})"
        else:
            parts.append(ln)

    final_title = " ".join(parts).strip()
    return final_title if final_title else (orig_t if not RENAME_AUDIO_TRACKS and orig_t else None)


# --- (4) HAUPTVERARBEITUNG ---
def process_file(cursor, file_path, file_type, stats):
    try:
        current_mtime = os.path.getmtime(file_path)
    except FileNotFoundError:
        logging.warning(f"Datei nicht gefunden während mtime-Check: {file_path}")
        return

    stats.files_checked += 1
    skip, reason = should_skip_file(cursor, file_path, current_mtime)
    if skip:
        if reason == "Erfolg": stats.files_skipped_db += 1
        logging.debug(f"🚫 Überspringe ({reason}): {os.path.basename(file_path)}")
        return

    media_info = get_media_info(file_path)
    if not media_info:
        increment_failure_count(cursor, file_path, current_mtime) # Pass valid mtime
        stats.files_failed += 1
        return

    stats.files_processed += 1
    logging.info(f"\n🎬 --- Prüfe: {os.path.basename(file_path)} ---")

    streams = media_info.get('streams', [])
    dur = 0
    d_str = None # Initialize d_str
    try:
        d_str = media_info.get('format', {}).get('duration')
        if d_str: dur = float(d_str)
    except (ValueError, TypeError) as e:
        logging.warning(f"Konnte Dauer '{d_str}' für {os.path.basename(file_path)} nicht parsen: {e}")
        dur = 0

    plan = {
        'needs_remux': file_path.lower().endswith('.mp4'),  # MP4s müssen zu MKV konvertiert werden
        'actions_mkvprop': [],
        'maps_ffmpeg': ['-map', '0:v?'],
        'metadata_ffmpeg': [],
        'dry_run_log': []
    }
    streams_to_keep = []
    streams_to_remove = []

    # --- Erste Schleife: Streams analysieren, Whisper, Keep/Remove ---
    for stream in streams:
        idx = stream['index']
        ct = stream.get('codec_type')
        original_lang_tag = normalize_lang_code(stream.get('tags', {}).get('language', 'und'))
        final_lt = original_lang_tag
        is_comm = is_commentary(stream)
        keep = True

        run_whisper = (ct == 'audio' and final_lt == 'und' and not is_comm and
                   WHISPER_API_URL) # Führe Whisper aus, wenn es und ist und die API da ist
        if run_whisper:
            if dur >= 180:
                logging.info(f"  🔍 Analysiere Spur #{idx} (Audio, und)..."); langs=[]
                pts = [dur * p - (15 if p == 0.9 else 0) for p in [0.3, 0.6, 0.9]]
                pts = [max(0, p) for p in pts]

                for i, st in enumerate(pts):
                    if st > dur - 30:
                        st = max(0, dur - 30)
                        logging.debug(f"  \t Startzeit für Probe {i+1} angepasst auf {st:.2f}s.")

                    tmp_p = None
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                            tmp_p = tmp.name
                        cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', file_path,
                            '-ss', str(st), '-t', '30', '-map', f'0:{idx}', '-vn',
                            '-c:a', 'libmp3lame', '-q:a', '5', tmp_p]
                        logging.debug(f"Running ffmpeg for Whisper sample {i+1}: {' '.join(cmd)}")
                        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=FFMPEG_SAMPLE_TIMEOUT)

                        lc_raw = detect_language_with_whisper(tmp_p)
                        lc = normalize_lang_code(lc_raw) if lc_raw else 'und'
                        logging.info(f"  \t Probe {i+1}/3: '{lc_raw}' (-> '{lc}') erkannt."); langs.append(lc)

                    except subprocess.TimeoutExpired:
                        logging.warning(f"  \t Probe {i+1}/3: Timeout bei ffmpeg Extraktion.")
                    except subprocess.CalledProcessError as sub_e:
                        stderr_output = sub_e.stderr.decode('utf-8', errors='ignore').strip() if sub_e.stderr else "N/A"
                        logging.warning(f"  \t Probe {i+1}/3: Fehler bei ffmpeg Extraktion. STDERR: {stderr_output}")
                    except Exception as e:
                        logging.warning(f"  \t Probe {i+1}/3: Unerwarteter Fehler. {e}")
                    finally:
                        if tmp_p and os.path.exists(tmp_p):
                            try: os.remove(tmp_p); logging.debug(f"Temp Whisper file gelöscht: {tmp_p}")
                            except OSError as rm_e: logging.warning(f"Konnte Temp Whisper file nicht löschen: {tmp_p} - {rm_e}")

                if langs:
                    cnts = Counter(langs); mc, c = cnts.most_common(1)[0]
                    if c >= 2:
                        final_lt = mc
                        logging.info(f"  -> Spur {idx}: Mehrheit -> '{final_lt}'.")
                        stats.audio_tagged += 1; stats.lang_counts[final_lt] += 1
                    else:
                        logging.info(f"  -> Spur {idx}: Keine Mehrheit ({cnts}). Bleibt 'und'.")
            else:
                logging.debug(f"  -> Spur {idx} (und) in kurzer Datei (Dauer: {dur:.1f}s). Keine Analyse.")

        remove_condition = False
        stream_type_label = str(ct).upper() if ct else 'Unknown'
        keep_list_for_log = set()

        if ct == 'audio':
            remove_condition = REMOVE_AUDIO and not is_comm and final_lt not in KEEP_AUDIO_LANGS
            keep_list_for_log = KEEP_AUDIO_LANGS
        elif ct == 'subtitle':
            remove_condition = REMOVE_SUBTITLES and final_lt not in KEEP_SUBTITLE_LANGS
            keep_list_for_log = KEEP_SUBTITLE_LANGS
        elif ct == 'attachment':
            # MIME Type des Anhangs prüfen (ffprobe liefert dies oft in tags)
            mimetype = stream.get('tags', {}).get('mimetype', '').lower()
            
            # Neue Logik: Prüfe, ob es eine Schriftart ist
            is_font = mimetype.startswith('font/') or mimetype.endswith('/truetype') or mimetype.endswith('/opentype')
            
            if is_font:
                # WENN es eine Schriftart ist: Prüfe die neue Variable REMOVE_FONTS
                remove_condition = REMOVE_FONTS
                stream_type_label = 'Font'
                keep_list_for_log = set() 
            else:
                # WENN es ein anderes Attachment ist (z.B. Cover, Bild): Prüfe REMOVE_ATTACHMENTS
                remove_condition = REMOVE_ATTACHMENTS
                stream_type_label = 'Attachment'
                keep_list_for_log = set()
        elif ct != 'video': # Keep video by default, also keep unknown types
            logging.debug(f"Unbekannter Stream-Typ '{ct}' bei Index {idx} wird beibehalten.")

        logging.debug(f"  DEBUG: Check Keep Stream {idx} ({ct}). Final Lang: '{final_lt}'. Keep List ({stream_type_label}): {keep_list_for_log}. Is Comm: {is_comm}. Remove: {remove_condition}")

        if RUN_CLEANUP and remove_condition:
            keep = False
            plan['needs_remux'] = True
            if ct == 'audio': stats.audio_removed += 1; plan['dry_run_log'].append(f"⛔ Würde Spur {idx} (Audio, {final_lt}) ENTFERNEN.")
            elif ct == 'subtitle': stats.subs_removed += 1; plan['dry_run_log'].append(f"⛔ Würde Spur {idx} (Sub, {final_lt}) ENTFERNEN.")
            elif ct == 'attachment': stats.attachments_removed += 1; plan['dry_run_log'].append(f"⛔ Würde Spur {idx} (Attachment) ENTFERNEN.")

        if keep: streams_to_keep.append({'stream':stream,'final_lang':final_lt})
        else:
             streams_to_remove.append(idx); plan['needs_remux']=True
            
             if ct == 'attachment':
                 if 'Font' in stream_type_label: # Wenn es eine Schriftart war
                      stats.attachments_removed += 1 # Zähle es unter Attachments
                      plan['dry_run_log'].append(f"⛔ Würde Spur {idx} (Font) ENTFERNEN.")
                 else: # Wenn es ein anderes Attachment war
                      stats.attachments_removed += 1
                      plan['dry_run_log'].append(f"⛔ Würde Spur {idx} (Attachment) ENTFERNEN.")
    # --- Ende Erste Schleife ---

# --- Zweite Schleife: Aktionen planen ---
    audio_tracks_kept = []
    subtitle_tracks_kept = []
    has_audio_default_candidate = False
    has_subtitle_default_candidate = False

    # First pass to build lists and check for default candidates (uses correct 'final_lang' key)
    for item in streams_to_keep:
        s = item['stream']; idx = s['index']; ct = s.get('codec_type'); fl = item['final_lang']
        is_comm = is_commentary(s)

        # track_info speichert den originalen Status
        track_info = {'original_index': idx, 'final_lang': fl, 'is_commentary': is_comm, 'stream': s}

        if ct == 'audio':
            audio_tracks_kept.append(track_info)
            if DEFAULT_AUDIO_LANG and fl == DEFAULT_AUDIO_LANG and not is_comm:
                has_audio_default_candidate = True
        elif ct == 'subtitle':
            subtitle_tracks_kept.append(track_info)
            if DEFAULT_SUBTITLE_LANG and fl == DEFAULT_SUBTITLE_LANG:
                has_subtitle_default_candidate = True

    final_audio_default_original_idx = -1
    final_subtitle_default_original_idx = -1
    
    # ----------------------------------------------------------------------
    # Bestimme, welcher Index tatsächlich das DEFAULT-Ziel ist (SOLL-Zustand)
    # ----------------------------------------------------------------------

    # Determine actual default track index (audio)
    if has_audio_default_candidate:
        for track in audio_tracks_kept:
            if track['final_lang'] == DEFAULT_AUDIO_LANG and not track['is_commentary']:
                final_audio_default_original_idx = track['original_index']
                stats.default_audio_set += 1 
                break
        # Wenn kein geeigneter Kandidat gefunden wurde, bleibt der Default-Status bei -1

    # Determine actual default track index (subtitle)
    if has_subtitle_default_candidate:
        for track in subtitle_tracks_kept:
             if track['final_lang'] == DEFAULT_SUBTITLE_LANG:
                 final_subtitle_default_original_idx = track['original_index']
                 stats.default_sub_set += 1 
                 break
        # Wenn kein geeigneter Kandidat gefunden wurde, bleibt der Default-Status bei -1

    # Reset mkvpropedit actions before rebuilding (optional, aber sicher)
    plan['actions_mkvprop'] = [] 
    
    # ----------------------------------------------------------------------
    # Hauptschleife zur Generierung der Aktionen (Ist vs. Soll)
    # ----------------------------------------------------------------------
    new_audio_idx = 0
    new_subtitle_idx = 0
    
    for item in streams_to_keep:
        s = item['stream']
        idx = s['index'] # 0-basierter Index (Original)
        ct = s.get('codec_type')
        fl = item['final_lang']
        ol = normalize_lang_code(s.get('tags', {}).get('language', 'und'))
        mid = idx + 1 # 1-basierter Index für mkvpropedit

        is_audio = ct == 'audio'
        is_subtitle = ct == 'subtitle'
        
        # 1. SOLL-ZUSTAND: Bestimme, ob das Flag gesetzt werden soll
        is_default_target = (is_audio and idx == final_audio_default_original_idx) or \
                            (is_subtitle and idx == final_subtitle_default_original_idx)

        # 2. IST-ZUSTAND: Prüfe den aktuellen Wert des Default-Flags im Stream
        is_default_already_set = s.get('disposition', {}).get('default', 0) == 1

        # ----------------------------------------------------
        # 3. PLANUNG (Ist != Soll)
        # ----------------------------------------------------

        # Plan Language Tag Change (falls der Tag in der Datei falsch ist)
        if fl != ol:
            plan['actions_mkvprop'].extend(['--edit', f'track:{mid}', '--set', f'language={fl}'])
            plan['dry_run_log'].append(f"🏷️ Würde Spur {idx} ({ct}) auf '{fl}' taggen.")
            if file_path.lower().endswith('.mp4'): plan['needs_remux'] = True

        # Plan Audio Title Change (intelligente Entscheidung: mkvpropedit vs Remux)
        nt = None
        if is_audio:
            nt = format_audio_title(s, fl)
            ot = s.get('tags', {}).get('title')
            if RENAME_AUDIO_TRACKS and nt and nt != ot:
                # Nur Remux wenn STRUKTURELLE Änderungen nötig sind
                if streams_to_remove or file_path.lower().endswith('.mp4'):
                    plan['needs_remux'] = True
                    plan['dry_run_log'].append(f"✏️ Würde Spur {idx} (Audio) umbenennen zu: '{nt}' [via Remux].")
                else:
                    # Effiziente Metadaten-Änderung mit mkvpropedit
                    plan['actions_mkvprop'].extend(['--edit', f'track:{mid}', '--set', f'title={nt}'])
                    plan['dry_run_log'].append(f"✏️ Würde Spur {idx} (Audio) umbenennen zu: '{nt}' [via mkvpropedit].")
                stats.audio_renamed += 1

        # Plan Default Flag Change (NUR wenn sich der Zustand ändert!)
        # Fall 1: Ist nicht Standard (0), soll aber Standard werden (1)
        if is_default_target and not is_default_already_set:
            plan['actions_mkvprop'].extend(['--edit', f'track:{mid}', '--set', f'flag-default=1'])
            plan['dry_run_log'].append(f"⭐ Würde Spur {idx} ({ct}, {fl}) als DEFAULT setzen (neu nötig).")
            # ACHTUNG: Die stats.default_audio_set Zählung findet bereits oben statt!

        # Fall 2: Ist Standard (1), soll aber KEIN Standard sein (0)
        elif not is_default_target and is_default_already_set:
            plan['actions_mkvprop'].extend(['--edit', f'track:{mid}', '--set', f'flag-default=0'])
            plan['dry_run_log'].append(f"❌ Würde DEFAULT-Flag von Spur {idx} ({ct}, {fl}) entfernen (nicht mehr nötig).")


        # Plan FFmpeg mappings and metadata
        if is_audio or is_subtitle:
             plan['maps_ffmpeg'].extend(['-map', f'0:{idx}'])
             stream_type_char = 'a' if is_audio else 's'
             new_idx = new_audio_idx if is_audio else new_subtitle_idx
             prefix = f's:{stream_type_char}:{new_idx}'
             
             # Disposition für FFmpeg basiert auf dem SOLL-Zustand (is_default_target)
             dispos = '+default' if is_default_target else '-default'
             
             plan['metadata_ffmpeg'].extend([f'-metadata:{prefix}', f'language={fl}'])
             plan['metadata_ffmpeg'].extend([f'-disposition:{prefix}', dispos]) 
             if is_audio and RENAME_AUDIO_TRACKS and nt:
                 plan['metadata_ffmpeg'].extend([f'-metadata:{prefix}', f'title={nt}'])

             if is_audio: new_audio_idx += 1
             else: new_subtitle_idx += 1

    # Correct ffmpeg dispositions are now implicitly handled by setting only one '+default' above

    # --- Entscheidung und Ausführung (Optimiert für Effizienz) ---
    # Remux nur bei strukturellen Änderungen (Streams entfernen, MP4->MKV)
    # Metadaten-Änderungen (Titel, Sprache, Flags) nutzen mkvpropedit
    mod = plan['needs_remux'] or any('--set' in a for a in plan['actions_mkvprop'])

    if not mod:
        logging.debug(f"Keine relevanten Aktionen für {os.path.basename(file_path)} nötig.")
        if not DRY_RUN: mark_file_as_processed(cursor, file_path, current_mtime)
        return

    logging.info(f"\n--- Aktionen für: {os.path.basename(file_path)} ---")

    # --- DRY RUN ---
    if DRY_RUN:
        logging.info("!!! [DRY RUN] Modus: Zeige geplante Aktionen. !!!")
        for line in plan['dry_run_log']: logging.info(f"  -> {line}")
        effective_mkvprop_actions = [a for a in plan['actions_mkvprop'] if 'language=' in a or 'flag-default=1' in a] # Only show effective sets
        if plan['needs_remux']:
            logging.info(f"  -> Aktion: Vollständiger Remux (ffmpeg).")
            cmd_approx = ['ffmpeg', '-i', '...',] + plan['maps_ffmpeg'] + ['-c', 'copy'] + plan['metadata_ffmpeg'] + ['...']
            logging.debug(f"     FFmpeg Command (approx): {' '.join(cmd_approx)}")
        elif effective_mkvprop_actions:
            logging.info(f"  -> Aktion: Schnelle Änderung (mkvpropedit).")
            cmd_approx = ['mkvpropedit', '"..."'] + effective_mkvprop_actions
            logging.debug(f"     Mkvpropedit Command (approx): {' '.join(cmd_approx)}")
        else:
            # This can happen if only flag-default=0 was needed
            logging.info("  -> Keine Änderungen (nur Default-Flags entfernt?). Markiere als verarbeitet im Dry Run.")
        return

    # --- ECHTER LAUF ---
    failed = False; new_p = None; sb = 0; tmp_p = None
    try:
        if plan['needs_remux']:
            logging.info(f"  -> ⚙️ Führe Remux (ffmpeg) durch...")
            if os.path.exists(file_path): sb = os.path.getsize(file_path)
            base, ext = os.path.splitext(file_path)
            is_mp4 = ext.lower() == '.mp4'
            out_p = f"{base}.mkv" if is_mp4 else file_path
            tmp_p = f"{out_p}.remux_tmp_{os.getpid()}_{int(time.time())}"
            cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', file_path] + \
                plan['maps_ffmpeg'] + ['-c', 'copy'] + plan['metadata_ffmpeg'] + \
                ['-f', 'matroska', tmp_p]
            logging.debug(f"Executing FFmpeg: {' '.join(cmd)}")
            r = subprocess.run(cmd, check=False, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=FFMPEG_TIMEOUT)
            if r.returncode != 0: raise subprocess.CalledProcessError(r.returncode, cmd, r.stdout, r.stderr)

            if is_mp4:
                logging.debug(f"MP4 Remux: Verschiebe {tmp_p} nach {out_p}, lösche Original {file_path}")
                os.rename(tmp_p, out_p)
                try: os.remove(file_path)
                except OSError as e: logging.warning(f"Konnte Original-MP4 nicht löschen: {file_path} - {e}")
                stats.files_converted_mp4 += 1; new_p = out_p
            else:
                logging.debug(f"MKV Remux: Verschiebe {tmp_p} nach {file_path}")
                os.rename(tmp_p, file_path); new_p = file_path

            tmp_p_success_path = tmp_p; tmp_p = None # Set tmp_p to None on success
            stats.files_remuxed_ffmpeg += 1
            if sb > 0 and new_p and os.path.exists(new_p):
                try: sa = os.path.getsize(new_p); stats.bytes_saved += (sb - sa)
                except OSError as e: logging.warning(f"Konnte Dateigröße nach Remux nicht lesen: {new_p} - {e}")
            logging.info(f"  -> ✅ SUCCESS: Remux abgeschlossen (von {tmp_p_success_path}).")
        # --- Execute mkvpropedit if NO remux needed but changes planned ---
        elif any('--set' in action for action in plan['actions_mkvprop']): # Check if any '--set' exists
            # Determine if effective changes are planned (language or setting default=1)
            has_lang_change = any('language=' in plan['actions_mkvprop'][i] for i in range(3, len(plan['actions_mkvprop']), 4))
            has_default_set_to_1 = any('flag-default=1' in plan['actions_mkvprop'][i] for i in range(3, len(plan['actions_mkvprop']), 4))

            # Determine if clearing default=0 is necessary
            needs_clear_audio = final_audio_default_original_idx != -1 and \
                any(
                    'flag-default=0' in plan['actions_mkvprop'][i] and f'track:{t["original_index"]+1}' == plan['actions_mkvprop'][i-2]
                    for t in audio_tracks_kept
                    for i in range(3, len(plan['actions_mkvprop']), 4)
                )
            needs_clear_sub = final_subtitle_default_original_idx != -1 and \
                any(
                    'flag-default=0' in plan['actions_mkvprop'][i] and f'track:{t["original_index"]+1}' == plan['actions_mkvprop'][i-2]
                    for t in subtitle_tracks_kept
                    for i in range(3, len(plan['actions_mkvprop']), 4)
                )

            # Only proceed if there's a language change, a default=1 set, or a necessary default=0 clear
            if has_lang_change or has_default_set_to_1 or needs_clear_audio or needs_clear_sub:
                logging.info(f"  -> ⚡ Führe mkvpropedit durch...")
                # Build the final command list carefully
                final_mkvprop_actions = []
                # Iterate through actions in chunks of 4
                for i in range(0, len(plan['actions_mkvprop']), 4):
                    try:
                        edit_cmd = plan['actions_mkvprop'][i]
                        track_id_str = plan['actions_mkvprop'][i+1]
                        set_cmd = plan['actions_mkvprop'][i+2]
                        key_val_str = plan['actions_mkvprop'][i+3]

                        # Include language changes
                        if 'language=' in key_val_str:
                            final_mkvprop_actions.extend([edit_cmd, track_id_str, set_cmd, key_val_str])
                        # Include explicit setting to 1
                        elif 'flag-default=1' in key_val_str:
                            final_mkvprop_actions.extend([edit_cmd, track_id_str, set_cmd, key_val_str])
                        # Include setting to 0 only if necessary
                        elif 'flag-default=0' in key_val_str:
                            track_idx = int(track_id_str.split(':')[1]) - 1
                            is_audio_track = any(t['original_index'] == track_idx for t in audio_tracks_kept)
                            is_sub_track = any(t['original_index'] == track_idx for t in subtitle_tracks_kept)
                            if (is_audio_track and needs_clear_audio) or (is_sub_track and needs_clear_sub):
                                final_mkvprop_actions.extend([edit_cmd, track_id_str, set_cmd, key_val_str])
                    except IndexError:
                        logging.warning(f"Fehler beim Verarbeiten der mkvpropedit Aktionen bei Index {i}. Überspringe diesen Teil.")
                        break

                if final_mkvprop_actions:
                    cmd = ['mkvpropedit', file_path] + final_mkvprop_actions
                    logging.debug(f"Executing mkvpropedit: {' '.join(cmd)}")
                    r = subprocess.run(cmd, check=False, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=MKVPROPEDIT_TIMEOUT)
                    if r.returncode != 0: raise subprocess.CalledProcessError(r.returncode, cmd, r.stdout, r.stderr)
                    stats.files_edited_mkvprop += 1; new_p = file_path
                    logging.info(f"  -> ✅ SUCCESS: mkvpropedit abgeschlossen.")
                else:
                    logging.debug("  -> Keine effektiven mkvpropedit Aktionen nach Filterung nötig (nur unnötige flag-default=0?).")
                    mark_file_as_processed(cursor, file_path, current_mtime); return
            else:
                logging.debug("  -> Keine effektiven mkvpropedit Aktionen geplant (nur flag-default=0 ohne Notwendigkeit?).")
                mark_file_as_processed(cursor, file_path, current_mtime); return

    # --- Error Handling & Finally Block (Identical to previous version) ---
    except subprocess.TimeoutExpired as time_e:
        failed = True; command_str = " ".join(time_e.cmd) if hasattr(time_e, 'cmd') and time_e.cmd else "Unbekannt"; logging.error(f"  -> ❌ FEHLER: Subprocess Timeout ({time_e.timeout}s) bei Befehl: {command_str}")
    except subprocess.CalledProcessError as e:
        failed = True; command_str = " ".join(e.cmd) if hasattr(e, 'cmd') and e.cmd else "Unbekannt"; stderr_output = e.stderr.strip() if hasattr(e, 'stderr') and e.stderr else "Kein STDERR Output."; logging.error(f"  -> ❌ FEHLER: Subprocess fehlgeschlagen (Code {e.returncode}) bei Befehl: {command_str}"); logging.error(f"  -> STDERR: {stderr_output}")
    except Exception as e:
        failed = True; logging.error(f"  -> ❌ ALLGEMEINER FEHLER bei Dateiänderung: {e}", exc_info=True)
    finally:
        if tmp_p and os.path.exists(tmp_p):
            logging.warning(f"Versuche fehlgeschlagene/übrige temporäre Remux-Datei zu löschen: {tmp_p}")
            try: os.remove(tmp_p); logging.info(f"Temporäre Remux-Datei gelöscht: {tmp_p}")
            except OSError as rm_e: logging.error(f"Konnte temporäre Remux-Datei nach Fehler nicht löschen: {tmp_p} - {rm_e}")

    # --- Ergebnisverarbeitung (Identical to previous version) ---
    if failed:
        increment_failure_count(cursor, file_path, current_mtime)
        stats.files_failed += 1
    else:
        final_path = new_p if new_p else file_path
        final_mtime = current_mtime
        if mod:
            try:
                final_mtime = os.path.getmtime(final_path)
                clear_failure_entry(cursor, file_path) # Clear original path failure
                if new_p and new_p != file_path: clear_failure_entry(cursor, new_p) # Clear new path failure
                if file_type == "sonarr": MODIFIED_SONARR_PATHS.add(os.path.dirname(final_path))
                if file_type == "radarr": MODIFIED_RADARR_PATHS.add(os.path.dirname(final_path))
                mark_file_as_processed(cursor, final_path, final_mtime)
            except FileNotFoundError:
                logging.error(f"  -> ❌ DB-FEHLER: Konnte mtime von finalem Pfad '{final_path}' nach erfolgreicher Operation nicht lesen.")
                increment_failure_count(cursor, file_path, current_mtime)
                stats.files_failed += 1
            except Exception as e_mtime:
                logging.error(f"  -> ❌ FEHLER beim Holen der finalen mtime oder DB-Cleanup für '{final_path}': {e_mtime}")
                increment_failure_count(cursor, file_path, current_mtime)
                stats.files_failed += 1
        else:
            logging.debug("Keine Modifikation durchgeführt (final check), markiere Original als verarbeitet.")
            mark_file_as_processed(cursor, file_path, current_mtime)


# --- (5) STATISTIK & ARRs ---
def format_bytes(b):
    if b == 0: return "0 B"
    gb = b / (1024**3); mb = b / (1024**2); kb = b / 1024
    if gb >= 0.1: return f"{gb:.2f} GB"
    if mb >= 0.1: return f"{mb:.2f} MB"
    if kb >= 0.1: return f"{kb:.2f} KB"
    return f"{b} B"

def log_scan_report(stats):
    if not LOG_STATS_ON_COMPLETION: return
    duration_str = stats.get_duration()
    logging.info("\n\n" + "="*50); logging.info("📊 Language Fixer Scan-Bericht 📊"); logging.info("="*50)
    logging.info("\n--- Statistik (Dieser Lauf) ---"); logging.info(f"  ⏱️ Dauer:              {duration_str}")
    logging.info(f"  📁 Verzeichnisse:      {stats.dirs_scanned}"); logging.info(f"  📄 Dateien geprüft:    {stats.files_checked}")
    logging.info(f"  ⏭️ Übersprungen (DB):  {stats.files_skipped_db}"); logging.info(f"  ⚙️ Verarbeitet:        {stats.files_processed}")
    logging.info(f"  ❌ Fehlgeschlagen:     {stats.files_failed}"); lang_str = ", ".join([f"{l}: {c}" for l, c in sorted(stats.lang_counts.items())]) if stats.lang_counts else "Keine"
    logging.info(f"  🎤 Audio getaggt:      {stats.audio_tagged} ({lang_str})"); logging.info(f"  ✏️ Audio umbenannt:    {stats.audio_renamed}")
    logging.info(f"  🗑️ Audio entfernt:     {stats.audio_removed}"); logging.info(f"  🗑️ Subs entfernt:      {stats.subs_removed}")
    logging.info(f"  🗑️ Attach. entfernt:   {stats.attachments_removed}"); logging.info(f"  🚀 Remux (ffmpeg):     {stats.files_remuxed_ffmpeg}")
    logging.info(f"  ⚡ Edit (mkvpropedit): {stats.files_edited_mkvprop}"); logging.info(f"  🔄 MP4->MKV:           {stats.files_converted_mp4}")
    logging.info(f"  ⭐ Default Audio:      {stats.default_audio_set}"); logging.info(f"  ⭐ Default Sub:        {stats.default_sub_set}")
    logging.info(f"  💾 Gesparter Speicher: {format_bytes(stats.bytes_saved)}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM cumulative_stats"); ts = {r[0]: r[1] for r in cursor.fetchall()}
            cursor.execute("SELECT lang, count FROM cumulative_lang_stats WHERE count > 0 ORDER BY count DESC"); tl_rows = cursor.fetchall()
            tl = ", ".join([f"{r[0]}: {r[1]}" for r in tl_rows]) if tl_rows else "Keine"
        logging.info("\n--- Statistik (Gesamt) ---"); logging.info(f"  ⚙️ Dateien verarbeitet: {ts.get('files_processed', 0)}")
        logging.info(f"  🎤 Audio getaggt:      {ts.get('audio_tagged', 0)} ({tl})"); logging.info(f"  🗑️ Audio entfernt:     {ts.get('audio_removed', 0)}")
        logging.info(f"  🗑️ Subs entfernt:      {ts.get('subs_removed', 0)}"); logging.info(f"  🗑️ Attach. entfernt:   {ts.get('attachments_removed', 0)}")
        logging.info(f"  💾 Gesparter Speicher: {format_bytes(ts.get('bytes_saved', 0))}")
    except sqlite3.Error as e: logging.warning(f"Fehler beim Laden der Gesamt-Statistik: {e}")
    logging.info("\n" + "="*50 + "\n")

def trigger_arr_scan(url, key, paths, arr_type):
    if not url or not key: logging.debug(f"{arr_type} URL oder API Key nicht konfiguriert."); return
    if not paths: logging.info(f"Keine {arr_type}-Dateien geändert, kein Scan nötig."); return
    paths_to_scan = paths.copy(); logging.info(f"🚀 Stoße {arr_type}-Scan für {len(paths_to_scan)} Ordner an...")
    headers = {'X-Api-Key': key}; command = "RescanSeries" if arr_type == "Sonarr" else "RescanMovie"
    id_param = "seriesId" if arr_type == "Sonarr" else "movieId"; endpoint_type = "series" if arr_type == "Sonarr" else "movie"
    api_base_url = f"{url.rstrip('/')}/api/v3"
    get_url = None
    try:
        get_url = f"{api_base_url}/{endpoint_type}"; logging.debug(f"Abfrage {arr_type} Endpunkt: {get_url}")
        r_get = requests.get(get_url, headers=headers, timeout=60); r_get.raise_for_status(); items = r_get.json()
        path_to_id = {i.get('path', '').rstrip('/\\'): i.get('id') for i in items if i.get('path') and i.get('id')}
        logging.debug(f"{len(path_to_id)} Pfade in {arr_type} gefunden.")
        scanned_ids = set(); post_url = f"{api_base_url}/command"
        for path in paths_to_scan:
            normalized_path = path.rstrip('/\\'); item_id = path_to_id.get(normalized_path)
            if item_id:
                if item_id not in scanned_ids:
                    logging.info(f"  -> Scanne {arr_type} Pfad '{normalized_path}' (ID: {item_id})"); payload = {"name": command, id_param: item_id}
                    try:
                        r_post = requests.post(post_url, json=payload, headers=headers, timeout=30); r_post.raise_for_status()
                        scanned_ids.add(item_id); time.sleep(1)
                    except requests.Timeout: logging.warning(f"  -> Timeout beim Senden des Scan-Befehls für ID {item_id} an {arr_type}.")
                    except requests.RequestException as post_e: status_code = post_e.response.status_code if post_e.response else "N/A"; logging.warning(f"  -> Fehler ({status_code}) beim Senden des Scan-Befehls für ID {item_id} an {arr_type}: {post_e}")
                else: logging.debug(f"  -> ID {item_id} für Pfad '{normalized_path}' wurde bereits zum Scannen ausgelöst.")
            else: logging.warning(f"  -> Konnte keine ID für Pfad '{normalized_path}' in {arr_type} finden. Scan nicht ausgelöst.")
    except requests.Timeout: url_str = get_url if get_url else api_base_url; logging.warning(f"Timeout beim Abrufen der {arr_type}-Elemente von {url_str}.")
    except requests.RequestException as e: url_str = get_url if get_url else api_base_url; status_code = e.response.status_code if e.response else "N/A"; logging.warning(f"Fehler ({status_code}) bei der Kommunikation mit der {arr_type}-API ({url_str}): {e}")
    except Exception as e_arr: logging.error(f"Unerwarteter Fehler in trigger_arr_scan für {arr_type}: {e_arr}", exc_info=True)
    paths.clear()


# --- (6) HAUPTSCHLEIFE ---
def run_scan(cursor, conn=None):
    logging.info("🔭 Starte Bibliotheks-Scan...")
    stats = ScanStats()
    if DRY_RUN: logging.info("!!! TROCKENLAUF-MODUS AKTIV !!!")
    
    # Batch-Commit Konfiguration
    files_since_last_commit = 0
    
    for atype, paths in SCAN_PATHS.items():
        for spath in paths:
            if not os.path.exists(spath): logging.warning(f"WARN: Pfad nicht gefunden: {spath}"); continue
            logging.info(f"Ermittle ({atype.upper()}) in: {spath}...")
            try: items = [d for d in os.listdir(spath) if os.path.isdir(os.path.join(spath, d)) and not d.startswith('.')]; logging.info(f"{len(items)} Elemente gefunden.")
            except Exception as e: logging.warning(f"WARN: Kann Verzeichnis {spath} nicht lesen: {e}"); continue
            items.sort()
            for i, item in enumerate(items):
                item_path = os.path.join(spath, item)
                logging.info(f"\n--- 📁 Scanne ({i+1}/{len(items)}) {item} ---")
                stats.dirs_scanned += 1
                try:
                    for root, _, files in os.walk(item_path):
                        files.sort()
                        for f in files:
                            if f.lower().endswith(('.mkv', '.mp4')):
                                full_path = os.path.join(root, f)
                                try: 
                                    process_file(cursor, full_path, atype, stats)
                                    files_since_last_commit += 1
                                    
                                    # Batch-Commit: Alle N Dateien committen
                                    if conn and files_since_last_commit >= BATCH_COMMIT_SIZE:
                                        logging.debug(f"💾 Batch-Commit nach {files_since_last_commit} Dateien...")
                                        conn.commit()
                                        files_since_last_commit = 0
                                        
                                except Exception as proc_e:
                                    logging.error(f"!! Unerwarteter Fehler bei Verarbeitung von {f}: {proc_e}", exc_info=True)
                                    try: # Try to get mtime for failure count even after error
                                        mtime = os.path.getmtime(full_path) if os.path.exists(full_path) else time.time()
                                        increment_failure_count(cursor, full_path, mtime)
                                    except Exception as mtime_e:
                                        logging.error(f"Konnte mtime nicht lesen für Fehlerzählung von {f}: {mtime_e}")
                                    stats.files_failed += 1
                except Exception as walk_e: logging.error(f"Fehler beim Durchlaufen von {item_path}: {walk_e}")
    
    # Final commit für verbleibende Änderungen
    if conn and files_since_last_commit > 0:
        logging.debug(f"💾 Final-Commit für verbleibende {files_since_last_commit} Dateien...")
        conn.commit()
    
    logging.info("✅ Bibliotheks-Scan abgeschlossen.")
    return stats

def main_loop():
    setup_logging()
    
    # Show detailed configuration summary with 30-second display
    print_configuration_summary()
    
    # Version information and update check
    logging.info(f"🚀 {__app_name__} v{__version__} gestartet. DRY_RUN={DRY_RUN}")
    
    # Check for updates in background (non-blocking)
    try:
        newer_version = check_for_updates()
        if newer_version:
            logging.info(f"🔔 UPDATE VERFÜGBAR: v{newer_version} → Nutze 'docker compose pull && docker compose up -d' für Update")
    except Exception as e:
        logging.debug(f"Update-Check fehlgeschlagen: {e}")

    try:
        SCAN_PATHS["sonarr"] = [p.strip() for p in SONARR_PATHS_RAW.split(',') if p.strip()]
        SCAN_PATHS["radarr"] = [p.strip() for p in RADARR_PATHS_RAW.split(',') if p.strip()]
        logging.info(f"   Sonarr Pfade: {SCAN_PATHS.get('sonarr', 'Keine')}")
        logging.info(f"   Radarr Pfade: {SCAN_PATHS.get('radarr', 'Keine')}")
        if not SCAN_PATHS.get("sonarr") and not SCAN_PATHS.get("radarr"): logging.warning("⚠️ Keine Scan-Pfade konfiguriert!")
    except Exception as e: logging.critical(f"💥 KRITISCH: Pfad-Parsing Fehler: {e}", exc_info=True); sys.exit(1)

    validate_config()
    init_db()

    while True:
        conn = None; current_stats = None
        try:
            logging.debug("Öffne DB-Verbindung für den Scan-Lauf...")
            conn = sqlite3.connect(DB_PATH, timeout=30); cursor = conn.cursor()
            current_stats = run_scan(cursor, conn)  # Pass connection for batch commits
            logging.info("Speichere finale Datenbankänderungen (Commit)..."); conn.commit()
            logging.info("Datenbankänderungen gespeichert.")
        except sqlite3.OperationalError as db_lock_err: logging.error(f"❌ DB FEHLER: Datenbank ist gesperrt! Überspringe. Fehler: {db_lock_err}"); conn.rollback() if conn else None
        except sqlite3.Error as db_err: logging.error(f"❌ Kritischer DB-Fehler: {db_err}", exc_info=True); conn.rollback() if conn else None
        except Exception as general_err: logging.error(f"❌ Unerwarteter Fehler in Hauptschleife: {general_err}", exc_info=True); conn.rollback() if conn else None
        finally:
            if conn: logging.debug("Schließe DB-Verbindung."); conn.close()

        if current_stats:
            if not DRY_RUN: update_cumulative_stats(current_stats)
            log_scan_report(current_stats)
            trigger_arr_scan(SONARR_URL, SONARR_API_KEY, MODIFIED_SONARR_PATHS, "Sonarr")
            trigger_arr_scan(RADARR_URL, RADARR_API_KEY, MODIFIED_RADARR_PATHS, "Radarr")
        else: logging.warning("Scan-Lauf wurde vorzeitig beendet oder Stats konnten nicht ermittelt werden.")

        logging.info(f"🕒 Nächster Scan geplant in {RUN_INTERVAL_SECONDS/3600:.1f} Stunden.")
        time.sleep(RUN_INTERVAL_SECONDS)

def start_web_ui():
    """Start Flask web UI in background thread"""
    try:
        # Import web app
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web'))
        from app import run_web_ui, set_app_state
        
        # Set initial state
        set_app_state({
            'status': 'idle',
            'last_scan': None,
            'current_file': None,
            'db_path': DB_PATH,
            'scan_callback': lambda: logging.info("Manual scan triggered from Web UI")
        })
        
        logging.info("🌐 Starting Web UI on port 8080...")
        web_thread = threading.Thread(target=run_web_ui, kwargs={'host': '0.0.0.0', 'port': 8080}, daemon=True)
        web_thread.start()
        logging.info("✅ Web UI started successfully!")
        logging.info("   Access at: http://localhost:8080")
        return True
    except ImportError as e:
        logging.warning(f"⚠️ Web UI not available: {e}")
        logging.warning("   Continuing without Web UI...")
        return False
    except Exception as e:
        logging.error(f"❌ Failed to start Web UI: {e}")
        return False

if __name__=="__main__":
    # Start Web UI first
    start_web_ui()
    # Give web server time to start
    time.sleep(2)
    # Start main processing loop
    main_loop()
