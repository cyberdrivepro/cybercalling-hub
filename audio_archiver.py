"""
================================================================================
  🎧 OmniDimension Local Call Audio Archiver & Vault
================================================================================
  Automatically downloads and archives call recordings into local folder.
================================================================================
"""

import os
import requests
import datetime

RECORDINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)


def archive_call_audio(recording_url, to_number, call_id=None):
    """Download and save call MP3 file into local recordings directory."""
    if not recording_url:
        return None

    url = recording_url if str(recording_url).startswith("http") else f"https://omnidim.io{recording_url}"
    clean_num = str(to_number).replace("+", "").replace(" ", "")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"call_{clean_num}_{timestamp}.mp3"
    filepath = os.path.join(RECORDINGS_DIR, filename)

    try:
        r = requests.get(url, timeout=25)
        if r.status_code == 200 and len(r.content) > 500:
            with open(filepath, "wb") as f:
                f.write(r.content)
            return filepath
    except Exception as e:
        print(f"Archive error for {to_number}:", e)
    return None


def get_all_archived_recordings():
    """List all saved local audio files."""
    files = []
    if os.path.exists(RECORDINGS_DIR):
        for f in sorted(os.listdir(RECORDINGS_DIR), reverse=True):
            if f.endswith(".mp3") or f.endswith(".wav"):
                p = os.path.join(RECORDINGS_DIR, f)
                files.append({
                    "filename": f,
                    "filepath": p,
                    "size_kb": round(os.path.getsize(p) / 1024, 1),
                    "created_at": datetime.datetime.fromtimestamp(os.path.getctime(p)).strftime("%Y-%m-%d %H:%M:%S")
                })
    return files
