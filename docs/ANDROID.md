# Schaduwstad Android v0.1.1

Native Kotlin/Compose client for the NightForge Game Server Platform module `schaduwstad`.

- Package: `com.nightforge.schaduwstad`
- minSdk 26 / target 35
- Intro: official MP4 via Media3/ExoPlayer (`res/raw/schaduwstad_intro.mp4`)
- Cinematics: 20 H.264 720p clips in `res/raw/cin_*.mp4`, registry in `CinematicId`
- Server: configurable Tailscale host, default `100.103.203.62:8098`

Original uncompressed clips: `assets/cinematics-original/` (do not overwrite).
Android copies are re-encoded (~2 Mbps, no cover-art stream).

Build:

```
cd android
./gradlew assembleDebug
```

APK: `android/app/build/outputs/apk/debug/app-debug.apk`
