from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.platform import GameModule

from .hub import SchaduwstadHub
from .routes import build_router
from .store import SchaduwstadStore


def create_schaduwstad_module(database_path: Path, connections) -> GameModule:
    store = SchaduwstadStore(database_path)
    store.initialize()
    hub = SchaduwstadHub(store)

    def register_routes(application: FastAPI) -> None:
        application.state.schaduwstad_store = store
        application.state.schaduwstad_hub = hub
        application.include_router(
            build_router(store, hub),
            prefix="/games/schaduwstad/api",
            tags=["schaduwstad"],
        )

        @application.websocket("/games/schaduwstad/ws/{lobby_code}")
        async def schaduwstad_socket(websocket: WebSocket, lobby_code: str):
            token = websocket.query_params.get("token") or ""
            await websocket.accept()
            try:
                view = store.view(token)
                await hub.add(view["lobbyCode"], token, websocket)
                await websocket.send_json({"type": "state", "view": view})
                while True:
                    message = await websocket.receive_json()
                    if message.get("type") == "chat":
                        view = store.chat(token, message.get("body", ""), message.get("share"))
                        await hub.push(view["lobbyCode"])
                    else:
                        view = store.view(token)
                        await websocket.send_json({"type": "state", "view": view})
            except WebSocketDisconnect:
                return
            except Exception as exc:
                await websocket.close(code=1008, reason=str(exc)[:80])
            finally:
                await hub.remove(lobby_code, websocket)

    return GameModule(
        game_id="schaduwstad",
        display_name="Schaduwstad",
        version="0.1.0",
        register_routes=register_routes,
    )
