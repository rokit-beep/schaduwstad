# Schaduwstad Android v0.1

Native Kotlin/Compose client for the NightForge Game Server Platform module `schaduwstad`.

- Package: `com.nightforge.schaduwstad`
- minSdk 26 / target 35
- Intro: official MP4 via Media3/ExoPlayer (`res/raw/schaduwstad_intro.mp4`)
- Server: configurable Tailscale host, default `100.103.203.62:8098`

Build on the Pi:

```
cd android
./gradlew assembleDebug
```

APK: `android/app/build/outputs/apk/debug/app-debug.apk`
