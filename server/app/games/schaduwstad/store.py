from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.errors import GameError

from .engine import (
    AP_PER_DAY,
    CASE_ID,
    PHASES,
    PLAYABLE,
    TEAM_CAP,
    action_by_id,
    actions_for,
    briefing_for,
    canonicalize,
    majority,
    ops_dossier,
    resolve_day,
    spec_for,
)
from .content import build_impacts

CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


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

    def _fresh_match_fields(self, lobby: dict) -> None:
        lobby["votes"] = {}
        lobby["personal"] = {}
        lobby["ap"] = {p["id"]: AP_PER_DAY for p in lobby["players"]}
        lobby["result"] = None
        lobby["clues"] = lobby.get("clues") or {}
        lobby["feed"] = []
        lobby["impacts"] = []
        lobby["impactSeen"] = {}
        lobby["cinematicSeen"] = {}
        spec = spec_for(lobby.get("day") or 1)
        lobby["caseId"] = spec.get("caseId") or CASE_ID
        lobby["apMax"] = int(spec.get("ap") or AP_PER_DAY)

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
                "players": [
                    {"id": player_id, "name": name, "team": None, "ready": False, "token": token}
                ],
                "chat": [],
                "votes": {},
                "personal": {},
                "ap": {player_id: AP_PER_DAY},
                "scores": {"mafia": 0, "detective": 0},
                "heat": 0,
                "evidence": "hidden",
                "evidenceScore": 0,
                "clues": {},
                "result": None,
                "feed": [],
                "impacts": [],
                "impactSeen": {},
                "cinematicSeen": {},
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
            lobby["players"].append(
                {"id": player_id, "name": name, "team": None, "ready": False, "token": token}
            )
            lobby.setdefault("ap", {})[player_id] = AP_PER_DAY
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
            lobby["phase"] = "play"
            self._fresh_match_fields(lobby)
            self._persist(lobby)
        return self.view(token)

    def vote(self, token: str, action: str) -> dict:
        with self._lock:
            lobby, player = self._by_token(token)
            if lobby["status"] != "started" or lobby["phase"] not in PLAYABLE:
                raise GameError("wrong_phase", "Nu kan er niet gestemd worden.", 409)
            canon = canonicalize(action)
            allowed = {item["id"] for item in actions_for(player["team"])}
            if canon not in allowed:
                raise GameError("bad_action", "Die actie hoort niet bij jouw team.", 400)
            lobby["votes"][player["id"]] = canon
            item = action_by_id(canon)
            self._append_feed(lobby, player, "vote", item)
            self._persist(lobby)
        return self.view(token)

    def act_personal(self, token: str, action: str) -> dict:
        with self._lock:
            lobby, player = self._by_token(token)
            if lobby["status"] != "started" or lobby["phase"] not in PLAYABLE:
                raise GameError("wrong_phase", "Nu kan er geen persoonlijke actie.", 409)
            item = action_by_id(action)
            if not item:
                raise GameError("bad_action", "Onbekende actie.", 400)
            allowed = {a["id"] for a in actions_for(player["team"])}
            if item["id"] not in allowed:
                raise GameError("bad_action", "Die actie hoort niet bij jouw team.", 400)
            taken = lobby.setdefault("personal", {}).setdefault(player["id"], [])
            if item["id"] in taken:
                raise GameError("already", "Die actie is al uitgevoerd.", 409)
            ap = lobby.setdefault("ap", {}).get(player["id"], AP_PER_DAY)
            cost = int(item.get("ap") or 1)
            if ap < cost:
                raise GameError("no_ap", "Niet genoeg actiepunten.", 409)
            lobby["ap"][player["id"]] = ap - cost
            taken.append(item["id"])
            self._append_feed(lobby, player, "personal", item)
            self._persist(lobby)
        return self.view(token)

    def _append_feed(self, lobby: dict, player: dict, kind: str, item: dict | None) -> None:
        if not item:
            return
        lobby.setdefault("feed", []).append(
            {
                "id": str(uuid4()),
                "team": player["team"],
                "playerId": player["id"],
                "playerName": player["name"],
                "kind": kind,
                "label": item.get("label"),
                "apLeft": lobby.get("ap", {}).get(player["id"], 0),
                "at": _now(),
            }
        )
        lobby["feed"] = lobby["feed"][-40:]

    def ack(self, token: str, cinematics: list[str] | None = None, impacts: list[str] | None = None) -> dict:
        with self._lock:
            lobby, player = self._by_token(token)
            seen_c = lobby.setdefault("cinematicSeen", {}).setdefault(player["id"], [])
            seen_i = lobby.setdefault("impactSeen", {}).setdefault(player["id"], [])
            for cid in cinematics or []:
                if cid and cid not in seen_c:
                    seen_c.append(cid)
            for iid in impacts or []:
                if iid and iid not in seen_i:
                    seen_i.append(iid)
            self._persist(lobby)
        return self.view(token)

    def chat(self, token: str, body: str, share: str | None = None) -> dict:
        text = (body or "").strip()[:240]
        share_id = (share or "").strip() or None
        if not text and not share_id:
            raise GameError("empty", "Leeg bericht.", 400)
        with self._lock:
            lobby, player = self._by_token(token)
            if not player["team"]:
                raise GameError("no_team", "Kies eerst een team.", 400)
            payload: dict = {
                "id": str(uuid4()),
                "team": player["team"],
                "senderId": player["id"],
                "senderName": player["name"],
                "body": text or f"{player['name']} deelde een clue",
                "at": _now(),
            }
            if share_id:
                if player["team"] != "detective":
                    raise GameError("forbidden", "Alleen recherche deelt clues.", 403)
                clue = (lobby.get("clues") or {}).get(share_id)
                if not clue:
                    raise GameError("missing_clue", "Die clue zit niet in het dossier.", 404)
                payload["share"] = {
                    "kind": "clue",
                    "clueId": clue["id"],
                    "label": clue["name"],
                    "status": clue["status"],
                }
                payload["body"] = text or f"{player['name']} deelde {clue['name']}"
            lobby["chat"].append(payload)
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
            if lobby["phase"] in PLAYABLE:
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
                mafia_personal = [
                    a
                    for p in lobby["players"]
                    if p["team"] == "mafia"
                    for a in lobby.get("personal", {}).get(p["id"], [])
                ]
                det_personal = [
                    a
                    for p in lobby["players"]
                    if p["team"] == "detective"
                    for a in lobby.get("personal", {}).get(p["id"], [])
                ]
                result = resolve_day(
                    majority(mafia_votes),
                    majority(det_votes),
                    mafia_personal,
                    det_personal,
                )
                lobby["result"] = result
                lobby["scores"]["mafia"] += result["mafiaDelta"]
                lobby["scores"]["detective"] += result["detectiveDelta"]
                lobby["heat"] = result["heat"]
                lobby["evidence"] = result["evidence"]
                lobby["evidenceScore"] = result["evidenceScore"]
                merged = lobby.setdefault("clues", {})
                for clue_id, clue in result.get("clues", {}).items():
                    prev = merged.get(clue_id)
                    rank = {"unknown": 0, "disputed": 1, "discovered": 2, "verified": 3}
                    if not prev or rank.get(clue["status"], 0) >= rank.get(prev.get("status"), 0):
                        merged[clue_id] = clue
                lobby["impacts"] = build_impacts(result)
                lobby["phase"] = "result"
            elif lobby["phase"] == "result":
                lobby["phase"] = "eval"
            else:
                idx = PHASES.index(lobby["phase"]) if lobby["phase"] in PHASES else 0
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
                public_result["mafiaPersonal"] = []
                if lobby["phase"] != "eval":
                    public_result["mafiaAction"] = None
            if team != "detective":
                public_result["detectiveDebrief"] = ""
                public_result["detectivePersonal"] = []
                public_result["clues"] = {}
                if lobby["phase"] != "eval":
                    public_result["detectiveAction"] = None
            cues = []
            for cue in result.get("cinematics") or []:
                owner = cue.get("team")
                if owner and owner != team:
                    continue
                cues.append(cue)
            public_result["cinematics"] = cues
            beats = []
            for beat in result.get("beats") or []:
                owner = beat.get("team")
                if owner and owner != team:
                    continue
                beats.append(beat)
            public_result["beats"] = beats
            public_result["events"] = [b.get("effect") for b in beats if b.get("effect")]
            shared = [b for b in beats if not b.get("team")]
            if shared:
                public_result["headline"] = shared[0].get("effect") or shared[0].get("cause")
            elif beats:
                public_result["headline"] = beats[0].get("cause")
            else:
                public_result["headline"] = "De nacht houdt haar mond."
            if team != "detective":
                public_result["clues"] = {}
        mafia_n = sum(1 for p in lobby["players"] if p["team"] == "mafia")
        det_n = sum(1 for p in lobby["players"] if p["team"] == "detective")
        tally: dict[str, int] = {}
        if started and team and lobby["phase"] in (*PLAYABLE, "result", "eval"):
            for p in lobby["players"]:
                if p["team"] != team:
                    continue
                vote = lobby.get("votes", {}).get(p["id"])
                if vote:
                    tally[vote] = tally.get(vote, 0) + 1
        vote_tally = [
            {
                "id": item["id"],
                "label": item["label"],
                "votes": tally.get(item["id"], 0),
            }
            for item in actions_for(team)
        ]
        clues = []
        if team == "detective":
            known = lobby.get("clues") or {}
            clues = list(known.values())
        ops = None
        if team == "mafia" and started:
            team_personal = [
                a
                for p in lobby["players"]
                if p["team"] == "mafia"
                for a in lobby.get("personal", {}).get(p["id"], [])
            ]
            ops = ops_dossier(
                lobby.get("heat") or 0,
                lobby.get("evidenceScore") or 0,
                result if reveal else None,
                team_personal,
            )
        feed = [e for e in (lobby.get("feed") or []) if team and e.get("team") == team]
        seen_i = set((lobby.get("impactSeen") or {}).get(you["id"]) or [])
        impacts = []
        unseen_impacts = []
        for imp in lobby.get("impacts") or []:
            if imp.get("team") != team:
                continue
            public = {
                "id": imp["id"],
                "title": imp.get("title"),
                "body": imp.get("body"),
                "kind": imp.get("kind"),
                "unseen": imp["id"] not in seen_i,
            }
            impacts.append(public)
            if public["unseen"]:
                unseen_impacts.append(public)
        seen_c = set((lobby.get("cinematicSeen") or {}).get(you["id"]) or [])
        unseen_cin = []
        if public_result:
            unseen_cin = [c for c in public_result.get("cinematics") or [] if c.get("id") not in seen_c]
        spec = spec_for(lobby.get("day") or 1)
        return {
            "lobbyCode": lobby["code"],
            "status": lobby["status"],
            "day": lobby["day"],
            "phase": lobby["phase"],
            "caseId": lobby["caseId"],
            "caseTitle": spec.get("title") or "Havenkade 12",
            "you": {
                "id": you["id"],
                "name": you["name"],
                "team": team,
                "ready": you["ready"],
                "isHost": you["id"] == lobby["hostId"],
                "ap": lobby.get("ap", {}).get(you["id"], AP_PER_DAY) if started else AP_PER_DAY,
                "apMax": AP_PER_DAY,
                "personalActions": list(lobby.get("personal", {}).get(you["id"], [])) if started else [],
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
            "briefing": briefing_for(team)
            if started and team and lobby["phase"] in PLAYABLE
            else None,
            "availableActions": list(actions_for(team))
            if started and lobby["phase"] in PLAYABLE and team
            else [],
            "yourVote": lobby["votes"].get(you["id"]),
            "voteTally": vote_tally if started and team and lobby["phase"] in (*PLAYABLE, "result", "eval") else [],
            "scores": lobby["scores"] if reveal else {"mafia": 0, "detective": 0},
            "heat": lobby["heat"] if reveal else 0,
            "evidence": lobby["evidence"] if reveal else None,
            "evidenceScore": lobby.get("evidenceScore", 0) if reveal else 0,
            "clues": clues,
            "opsDossier": ops,
            "result": public_result,
            "feed": feed,
            "impacts": impacts,
            "unseenImpacts": unseen_impacts,
            "unseenCinematics": unseen_cin,
            "canStart": (
                you["id"] == lobby["hostId"]
                and lobby["status"] == "waiting"
                and mafia_n >= 1
                and det_n >= 1
                and all(p["team"] and p["ready"] for p in lobby["players"])
            ),
        }
