from __future__ import annotations

from fastapi import APIRouter, Header, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.errors import GameError

from .hub import SchaduwstadHub
from .store import SchaduwstadStore


class NameBody(BaseModel):
    player_name: str = Field(min_length=2, max_length=20)


class TeamBody(BaseModel):
    team: str


class ReadyBody(BaseModel):
    ready: bool


class VoteBody(BaseModel):
    action: str


class ChatBody(BaseModel):
    body: str = Field(default="", max_length=240)
    share: str | None = None


class AckBody(BaseModel):
    cinematics: list[str] = Field(default_factory=list)
    impacts: list[str] = Field(default_factory=list)


def _token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise GameError("bad_session", "Sessie ongeldig.", 401)
    return authorization.split(" ", 1)[1].strip()


def build_router(store: SchaduwstadStore, hub: SchaduwstadHub) -> APIRouter:
    api = APIRouter()

    async def _push(view: dict) -> dict:
        await hub.push(view["lobbyCode"])
        return view

    @api.post("/lobbies")
    async def create_lobby(body: NameBody):
        token, view = store.create(body.player_name)
        return {"session_token": token, **view}

    @api.post("/lobbies/{code}/join")
    async def join_lobby(code: str, body: NameBody):
        token, view = store.join(code, body.player_name)
        await _push(view)
        return {"session_token": token, **view}

    @api.get("/lobbies/{code}/state")
    async def state(authorization: str | None = Header(default=None)):
        return store.view(_token(authorization))

    @api.post("/lobbies/{code}/team")
    async def team(body: TeamBody, authorization: str | None = Header(default=None)):
        return await _push(store.set_team(_token(authorization), body.team))

    @api.post("/lobbies/{code}/ready")
    async def ready(body: ReadyBody, authorization: str | None = Header(default=None)):
        return await _push(store.set_ready(_token(authorization), body.ready))

    @api.post("/lobbies/{code}/start")
    async def start(authorization: str | None = Header(default=None)):
        return await _push(store.start(_token(authorization)))

    @api.post("/lobbies/{code}/actions/vote")
    async def vote(body: VoteBody, authorization: str | None = Header(default=None)):
        return await _push(store.vote(_token(authorization), body.action))

    @api.post("/lobbies/{code}/actions/personal")
    async def personal(body: VoteBody, authorization: str | None = Header(default=None)):
        return await _push(store.act_personal(_token(authorization), body.action))

    @api.post("/lobbies/{code}/actions/advance")
    async def advance(authorization: str | None = Header(default=None)):
        return await _push(store.advance(_token(authorization)))

    @api.post("/lobbies/{code}/chat")
    async def chat(body: ChatBody, authorization: str | None = Header(default=None)):
        return await _push(store.chat(_token(authorization), body.body, body.share))

    @api.post("/lobbies/{code}/ack")
    async def ack(body: AckBody, authorization: str | None = Header(default=None)):
        return await _push(store.ack(_token(authorization), body.cinematics, body.impacts))

    @api.websocket("/ws/{code}")
    async def ws(websocket: WebSocket, code: str):
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
            await hub.remove(code, websocket)

    return api
