# Schaduwstad

Multiplayer text-based crime strategy game.

Architectuur:
- Android client (nog niet in deze recovery-snapshot)
- Raspberry Pi NightForge Game Server Platform
- FastAPI
- WebSockets
- server-authoritative
- Mafia vs Detectives
- team-isolated chat
- Schaduwstad GameModule
- Tailscale/private netwerk

## LIVE PLATFORM

NightForge Game Server Platform blijft een gedeelde server voor meerdere games.
Live locatie: `/home/pi/projects/tekst-based-game` op poort **8098**.
Crime blijft de canonieke bestaande module. Schaduwstad is een extra, namespaced GameModule.

Deze repository **vervangt die platform-repo niet**. Push nooit Schaduwstad-werk naar `rokit-beep/tekst-based-game` als vervanging van het platform.

## SCHADUWSTAD REPO

Deze repository is de source-of-truth voor de Schaduwstad-gamecode.

Huidige inhoud is een **recovery snapshot** van de bewezen Pi working tree, niet een herschreven architectuur.

Bronmapping:

| dit repo | NightForge platform |
|---|---|
| `server/app/games/schaduwstad/` | `app/games/schaduwstad/` |
| `tests/test_schaduwstad.py` | `tests/test_schaduwstad.py` |
| `docs/patches/nightforge-platform-schaduwstad.diff` | wijzigingen in `app/main.py` + `tests/test_platform.py` |

De module importeert `app.platform.GameModule` en `app.errors.GameError`. Die blijven in de platform-repo. Zie `docs/NIGHTFORGE_INTEGRATION.md`.

## Recovery milestone (2026-09-03)

- Pi working tree + backup `/home/pi/backups/schaduwstad-recovery-20260903/` bevestigd RECOVERABLE
- 9/9 SHA256 MATCH tussen live bron en backup
- Live `/platform/games` toont `crime` en `schaduwstad`
- Deze commit bewaart die bron zonder refactor

## Niet in deze snapshot

- Android-client (bestond lokaal niet voor Schaduwstad)
- intro/character assets (bestonden lokaal niet)
- runtime SQLite (`data/schaduwstad.db` blijft buiten git; kopie in recovery-backup)
