# Schaduwstad in NightForge Game Server Platform

Schaduwstad is geen los proces. Het is een `GameModule` in dezelfde FastAPI-app als Crime, poort 8098.

## Originele paden

```
app/games/schaduwstad/__init__.py
app/games/schaduwstad/adapter.py
app/games/schaduwstad/engine.py
app/games/schaduwstad/routes.py
app/games/schaduwstad/store.py
tests/test_schaduwstad.py
```

In deze repo staan die files onder `server/` zodat de Python-import `app.games.schaduwstad` behouden blijft wanneer `server/` op `PYTHONPATH` staat, of wanneer de map teruggekopieerd wordt naar de platform-repo.

## Platform-registratie (app/main.py)

Alleen deze twee toevoegingen horen bij Schaduwstad. Kopieer niet blind heel `app/main.py`.

Import:

```python
from app.games.schaduwstad import create_schaduwstad_module
```

Registratie, ná Crime, vóór `install_routes`:

```python
game_registry.register(
    create_schaduwstad_module(selected.database_path.parent / "schaduwstad.db", application.state.connections)
)
```

Databasebestand: `data/schaduwstad.db` naast de Crime-db. Niet de Crime-db hergebruiken.

## Platform-test (tests/test_platform.py)

`GET /platform/games` moet naast Crime ook deze metadata verwachten:

```python
{
    "id": "schaduwstad",
    "name": "Schaduwstad",
    "version": "0.1.0",
    "status": "available",
}
```

Volledige diff van de twee tracked platformbestanden: `docs/patches/nightforge-platform-schaduwstad.diff`.

## Routes (niet herschreven)

REST prefix: `/games/schaduwstad/api`
WebSocket: `/games/schaduwstad/ws/{lobby_code}`
Extra WS op de API-router: `/games/schaduwstad/api/ws/{code}`

Crime-routes onder `/api/...` en `/ws/game/{lobby_code}` blijven canoniek.

## Tests

`tests/test_schaduwstad.py` gebruikt `tests.conftest.auth` en de platform FastAPI testclient. Draaien vanuit de NightForge platform-repo, niet als standalone pytest in deze recovery-repo.

## Runtime database

Niet in git. Live file: `/home/pi/projects/tekst-based-game/data/schaduwstad.db`
Recovery-kopie: `/home/pi/backups/schaduwstad-recovery-20260903/data/schaduwstad.db`
