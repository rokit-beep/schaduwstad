from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.errors import GameError

from .engine import CASE_ID, TEAM_CAP, actions_for, briefing_for, majority, resolve_day

CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
PHASES = ("briefing", "huddle", "action", "result", "eval")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SchaduwstadStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        self._memory: dict[str, dict] = {}

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute(
                """CREATE TABLE IF NOT EXISTS lobbies (
                    code TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )
        self._memory = {code: state for code, state in self._load_all()}

    def _connect(self):
        import sqlite3
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

    def _load_all(self):
        with self._connect() as con:
            rows = con.execute("SELECT code, state_json FROM lobbies").fetchall()
        return [(row["code"], json.loads(row["state_json"])) for row in rows]

    def _persist(self, lobby: dict) -> None:
        payload = json.dumps(lobby, separators=(",", ":"), sort_keys=True)
        with self._connect() as con:
            con.execute(
                """INSERT INTO lobbies(code, state_json, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(code) DO UPDATE SET
                     state_json=excluded.state_json, updated_at=excluded.updated_at""",
                (lobby["code"], payload, _now()),
            )

    def create(self, player_name: str) -> tuple[str, dict]:
        name = player_name.strip()[:20]
        if len(name) < 2:
            raise GameError("bad_name", "Kies een naam van minstens 2 letters.", 400)
        with self._lock:
            code = "".join(secrets.choice(CODE_CHARS) for _ in range(4))
            while code in self._memory:
                code = "".join(secrets.choice(CODE_CHARS) for _ in range(4))
            player_id = str(uuid4())
            token = str(uuid4())
            lobby = {
                "code": code,
                "hostId": player_id,
                "status": "waiting",
                "day": 1,
                "phase": "briefing",
                "caseId": CASE_ID,
                "players": [{"id": player_id, "name": name, "team": None, "ready": False, "token": token}],
                "chat": [],
                "votes": {},
                "scores": {"mafia": 0, "detective": 0},
                "heat": 0,
                "evidence": "hidden",
                "result": None,
            }
            self._memory[code] = lobby
            self._persist(lobby)
        return token, self.view(token)

    def join(self, code: str, player_name: str) -> tuple[str, dict]:
        name = player_name.strip()[:20]
        if len(name) < 2:
            raise GameError("bad_name", "Kies een naam van minstens 2 letters.", 400)
        with self._lock:
            lobby = self._require(code)
            if lobby["status"] != "waiting":
                raise GameError("started", "Deze wedstrijd is al begonnen.", 409)
            if len(lobby["players"]) >= TEAM_CAP * 2:
                raise GameError("full", "Lobby is vol (max 12).", 409)
            if any(p["name"].lower() == name.lower() for p in lobby["players"]):
                raise GameError("name_taken", "Die naam is al in gebruik.", 409)
            player_id = str(uuid4())
            token = str(uuid4())
            lobby["players"].append({"id": player_id, "name": name, "team": None, "ready": False, "token": token})
            self._persist(lobby)
        return token, self.view(token)

    def set_team(self, token: str, team: str) -> dict:
        if team not in ("mafia", "detective"):
            raise GameError("bad_team", "Ongeldig team.", 400)
        with self._lock:
            lobby, player = self._by_token(token)
            if lobby["status"] != "waiting":
                raise GameError("closed", "Teamkeuze is gesloten.", 409)
            count = sum(1 for p in lobby["players"] if p["team"] == team)
            if player["team"] != team and count >= TEAM_CAP:
                raise GameError("team_full", "Dit team is vol (max 6).", 409)
            player["team"] = team
            player["ready"] = False
            self._persist(lobby)
        return self.view(token)

    def set_ready(self, token: str, ready: bool) -> dict:
        with self._lock:
            lobby, player = self._by_token(token)
            if not player["team"]:
                raise GameError("no_team", "Kies eerst een team.", 400)
            player["ready"] = bool(ready)
            self._persist(lobby)
        return self.view(token)

    def start(self, token: str) -> dict:
        with self._lock:
            lobby, player = self._by_token(token)
            if player["id"] != lobby["hostId"]:
                raise GameError("not_host", "Alleen de host kan starten.", 403)
            mafia = sum(1 for p in lobby["players"] if p["team"] == "mafia")
            detectives = sum(1 for p in lobby["players"] if p["team"] == "detective")
            if mafia < 1 or detectives < 1:
                raise GameError("need_teams", "Beide teams hebben minstens 1 speler nodig.", 400)
            if any(not p["team"] or not p["ready"] for p in lobby["players"]):
                raise GameError("not_ready", "Iedereen moet ready zijn.", 400)
            lobby["status"] = "started"
            lobby["phase"] = "briefing"
            lobby["votes"] = {}
            lobby["result"] = None
            self._persist(lobby)
        return self.view(token)

    def vote(self, token: str, action: str) -> dict:
        with self._lock:
            lobby, player = self._by_token(token)
            if lobby["status"] != "started" or lobby["phase"] != "action":
                raise GameError("wrong_phase", "Nu kan er niet gestemd worden.", 409)
            allowed = {item["id"] for item in actions_for(player["team"])}
            if action not in allowed:
                raise GameError("bad_action", "Die actie hoort niet bij jouw team.", 400)
            lobby["votes"][player["id"]] = action
            self._persist(lobby)
        return self.view(token)

    def chat(self, token: str, body: str) -> dict:
        text = body.strip()[:240]
        if not text:
            raise GameError("empty", "Leeg bericht.", 400)
        with self._lock:
            lobby, player = self._by_token(token)
            if not player["team"]:
                raise GameError("no_team", "Kies eerst een team.", 400)
            lobby["chat"].append(
                {
                    "id": str(uuid4()),
                    "team": player["team"],
                    "senderId": player["id"],
                    "senderName": player["name"],
                    "body": text,
                    "at": _now(),
                }
            )
            lobby["chat"] = lobby["chat"][-80:]
            self._persist(lobby)
        return self.view(token)

    def advance(self, token: str) -> dict:
        with self._lock:
            lobby, player = self._by_token(token)
            if player["id"] != lobby["hostId"]:
                raise GameError("not_host", "Alleen de host schuift de fase door.", 403)
            if lobby["status"] != "started":
                raise GameError("not_started", "Wedstrijd loopt niet.", 409)
            if lobby["phase"] == "action":
                mafia_votes = [
                    lobby["votes"].get(p["id"])
                    for p in lobby["players"]
                    if p["team"] == "mafia" and lobby["votes"].get(p["id"])
                ]
                det_votes = [
                    lobby["votes"].get(p["id"])
                    for p in lobby["players"]
                    if p["team"] == "detective" and lobby["votes"].get(p["id"])
                ]
                result = resolve_day(majority(mafia_votes), majority(det_votes))
                lobby["result"] = result
                lobby["scores"]["mafia"] += result["mafiaDelta"]
                lobby["scores"]["detective"] += result["detectiveDelta"]
                lobby["heat"] = result["heat"]
                lobby["evidence"] = result["evidence"]
                lobby["phase"] = "result"
            else:
                idx = PHASES.index(lobby["phase"])
                if idx < len(PHASES) - 1:
                    lobby["phase"] = PHASES[idx + 1]
            self._persist(lobby)
        return self.view(token)

    def view(self, token: str) -> dict:
        with self._lock:
            lobby, you = self._by_token(token)
            return self._to_view(lobby, you)

    def _require(self, code: str) -> dict:
        lobby = self._memory.get(code.upper())
        if not lobby:
            raise GameError("missing_lobby", "Lobby niet gevonden.", 404)
        return lobby

    def _by_token(self, token: str) -> tuple[dict, dict]:
        for lobby in self._memory.values():
            for player in lobby["players"]:
                if player["token"] == token:
                    return lobby, player
        raise GameError("bad_session", "Sessie ongeldig.", 401)

    def _to_view(self, lobby: dict, you: dict) -> dict:
        team = you["team"]
        started = lobby["status"] == "started"
        reveal = lobby["phase"] in ("result", "eval")
        result = lobby.get("result")
        public_result = None
        if result and reveal:
            public_result = dict(result)
            if team != "mafia":
                public_result["mafiaDebrief"] = ""
                if lobby["phase"] != "eval":
                    public_result["mafiaAction"] = None
            if team != "detective":
                public_result["detectiveDebrief"] = ""
                if lobby["phase"] != "eval":
                    public_result["detectiveAction"] = None
        mafia_n = sum(1 for p in lobby["players"] if p["team"] == "mafia")
        det_n = sum(1 for p in lobby["players"] if p["team"] == "detective")
        return {
            "lobbyCode": lobby["code"],
            "status": lobby["status"],
            "day": lobby["day"],
            "phase": lobby["phase"],
            "caseId": lobby["caseId"],
            "you": {
                "id": you["id"],
                "name": you["name"],
                "team": team,
                "ready": you["ready"],
                "isHost": you["id"] == lobby["hostId"],
            },
            "players": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "team": p["team"],
                    "ready": p["ready"],
                    "isYou": p["id"] == you["id"],
                    "isHost": p["id"] == lobby["hostId"],
                }
                for p in lobby["players"]
            ],
            "teamSize": {"mafia": mafia_n, "detective": det_n, "cap": TEAM_CAP},
            "chat": [m for m in lobby["chat"] if team and m["team"] == team],
            "briefing": briefing_for(team) if started and team and lobby["phase"] in ("briefing", "huddle", "action") else None,
            "availableActions": list(actions_for(team)) if started and lobby["phase"] == "action" and team else [],
            "yourVote": lobby["votes"].get(you["id"]),
            "scores": lobby["scores"] if reveal else {"mafia": 0, "detective": 0},
            "heat": lobby["heat"] if reveal else 0,
            "evidence": lobby["evidence"] if reveal else None,
            "result": public_result,
            "canStart": (
                you["id"] == lobby["hostId"]
                and lobby["status"] == "waiting"
                and mafia_n >= 1
                and det_n >= 1
                and all(p["team"] and p["ready"] for p in lobby["players"])
            ),
        }
