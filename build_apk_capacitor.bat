@echo off
title OmniDimension 1-Click APK Builder
echo ============================================================
echo   Building OmniVoice AI Android APK Package...
echo ============================================================

cd android_app
call npm install
call npx cap init "OmniVoice AI" "com.omnidim.voiceai" --web-dir "."
call npx cap add android
call npx cap sync android
echo ============================================================
echo   Android Studio Project Created at android_app/android/
echo   Opening Android Studio or run 'gradle assembleDebug' to build .apk!
echo ============================================================
pause
