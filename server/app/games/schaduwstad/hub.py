from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from fastapi import WebSocket

if TYPE_CHECKING:
    from .store import SchaduwstadStore


class SchaduwstadHub:
    """Push each player's own filtered view to every open socket in a lobby."""

    def __init__(self, store: SchaduwstadStore):
        self.store = store
        self._lock = asyncio.Lock()
        self._sockets: dict[str, dict[int, tuple[str, WebSocket]]] = {}

    async def add(self, code: str, token: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._sockets.setdefault(code.upper(), {})[id(websocket)] = (token, websocket)

    async def remove(self, code: str, websocket: WebSocket) -> None:
        async with self._lock:
            bucket = self._sockets.get(code.upper())
            if bucket:
                bucket.pop(id(websocket), None)

    async def push(self, code: str) -> None:
        async with self._lock:
            sockets = list(self._sockets.get(code.upper(), {}).values())
        for token, websocket in sockets:
            try:
                view = self.store.view(token)
                await websocket.send_json({"type": "state", "view": view})
            except Exception:
                continue
