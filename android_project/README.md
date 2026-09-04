# CyberCalling Voice AI — Canonical Native Android App

## 📱 Project Overview
This directory (\ndroid_project/\) is the **canonical native Android application** for the CyberCalling Voice AI Platform.

- **Language:** Kotlin
- **Build System:** Gradle Kotlin DSL (\uild.gradle.kts\)
- **Package:** \com.omnidim.voiceai- **Minimum SDK:** 26 (Android 8.0+)
- **Target SDK:** 34 (Android 14)

## 📁 Project Structure
\\	ext
android_project/
├── build.gradle.kts
├── settings.gradle.kts
└── app/
    ├── build.gradle.kts
    └── src/
        └── main/
            ├── AndroidManifest.xml
            ├── assets/
            │   └── index.html
            └── java/
                └── com/omnidim/voiceai/
                    └── MainActivity.kt
\
## 🚀 Building the APK
\\ash
./gradlew assembleRelease
\Output APK will be generated at: \pp/build/outputs/apk/release/app-release.apk