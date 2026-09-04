"""
================================================================================
  OmniVoice Android APK 1-Click ZIP Packager
================================================================================
  Creates 'OmniVoice_Android_Package.zip' ready to upload to WebIntoApp / AppsGeyser
  for instant 1-click APK download without Android Studio!
================================================================================
"""

import os
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "android_app")
ZIP_PATH = os.path.join(BASE_DIR, "OmniVoice_Android_Package.zip")

print("Creating OmniVoice_Android_Package.zip for 1-Click APK Generator...")

with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as z:
    src_html = os.path.join(APP_DIR, "standalone_app.html")
    if os.path.exists(src_html):
        z.write(src_html, "index.html")
    
    src_manifest = os.path.join(APP_DIR, "manifest.json")
    if os.path.exists(src_manifest):
        z.write(src_manifest, "manifest.json")
        
    src_sw = os.path.join(APP_DIR, "sw.js")
    if os.path.exists(src_sw):
        z.write(src_sw, "sw.js")

print(f"SUCCESS! Created: {ZIP_PATH}")
print("\nTo get your APK without Android Studio:")
print("1. Go to: https://www.webintoapp.com or https://appsgeyser.com/create-html5-app/")
print("2. Upload 'OmniVoice_Android_Package.zip'")
print("3. Click 'Download APK' -> Install on your Android phone!")
