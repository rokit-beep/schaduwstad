from __future__ import annotations

from fastapi import APIRouter, Header, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.errors import GameError

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
    body: str = Field(min_length=1, max_length=240)


def _token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise GameError("bad_session", "Sessie ongeldig.", 401)
    return authorization.split(" ", 1)[1].strip()


def build_router(store: SchaduwstadStore, connections) -> APIRouter:
    api = APIRouter()

    @api.post("/lobbies")
    def create_lobby(body: NameBody):
        token, view = store.create(body.player_name)
        return {"session_token": token, **view}

    @api.post("/lobbies/{code}/join")
    def join_lobby(code: str, body: NameBody):
        token, view = store.join(code, body.player_name)
        return {"session_token": token, **view}

    @api.get("/lobbies/{code}/state")
    def state(authorization: str | None = Header(default=None)):
        return store.view(_token(authorization))

    @api.post("/lobbies/{code}/team")
    def team(body: TeamBody, authorization: str | None = Header(default=None)):
        return store.set_team(_token(authorization), body.team)

    @api.post("/lobbies/{code}/ready")
    def ready(body: ReadyBody, authorization: str | None = Header(default=None)):
        return store.set_ready(_token(authorization), body.ready)

    @api.post("/lobbies/{code}/start")
    def start(authorization: str | None = Header(default=None)):
        return store.start(_token(authorization))

    @api.post("/lobbies/{code}/actions/vote")
    def vote(body: VoteBody, authorization: str | None = Header(default=None)):
        return store.vote(_token(authorization), body.action)

    @api.post("/lobbies/{code}/actions/advance")
    def advance(authorization: str | None = Header(default=None)):
        return store.advance(_token(authorization))

    @api.post("/lobbies/{code}/chat")
    def chat(body: ChatBody, authorization: str | None = Header(default=None)):
        return store.chat(_token(authorization), body.body)

    @api.websocket("/ws/{code}")
    async def ws(websocket: WebSocket, code: str):
        token = websocket.query_params.get("token") or ""
        await websocket.accept()
        try:
            view = store.view(token)
            await websocket.send_json({"type": "state", "view": view})
            while True:
                message = await websocket.receive_json()
                kind = message.get("type")
                if kind == "chat":
                    view = store.chat(token, message.get("body", ""))
                else:
                    view = store.view(token)
                await websocket.send_json({"type": "state", "view": view})
        except WebSocketDisconnect:
            return
        except Exception as exc:
            await websocket.close(code=1008, reason=str(exc)[:80])

    return api
