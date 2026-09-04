from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.errors import GameError

from .engine import (
    AP_PER_DAY,
    CASE_ID,
    CLUES,
    PHASES,
    PLAYABLE,
    ROUND_SECONDS,
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
from .content import build_impacts, follow_up_for

CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


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
                (lobby["code"], payload, _now_iso()),
            )

    def _fresh_match_fields(self, lobby: dict) -> None:
        lobby["votes"] = {}
        lobby["personal"] = {}
        lobby["ap"] = {p["id"]: AP_PER_DAY for p in lobby["players"]}
        lobby["result"] = None
        lobby["clues"] = {}
        lobby["feed"] = []
        lobby["impacts"] = []
        lobby["impactSeen"] = {}
        lobby["cinematicSeen"] = {}
        lobby["developments"] = []
        lobby["followUpsTaken"] = {}
        spec = spec_for(lobby.get("day") or 1)
        lobby["caseId"] = spec.get("caseId") or CASE_ID
        lobby["apMax"] = int(spec.get("ap") or AP_PER_DAY)
        seconds = int(spec.get("roundSeconds") or ROUND_SECONDS)
        lobby["roundEndsAt"] = (_now() + timedelta(seconds=seconds)).isoformat()
        for player in lobby["players"]:
            player["ready"] = False

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
                "developments": [],
                "followUpsTaken": {},
                "roundEndsAt": None,
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
            if lobby["status"] == "waiting":
                player["ready"] = bool(ready)
            elif lobby["status"] == "started" and lobby["phase"] in PLAYABLE:
                self._maybe_timeout_locked(lobby)
                if lobby["phase"] not in PLAYABLE:
                    self._persist(lobby)
                    return self._to_view(lobby, player)
                player["ready"] = bool(ready)
                if player["ready"] and self._all_locked(lobby):
                    self._resolve_play(lobby)
            else:
                raise GameError("wrong_phase", "Nu kun je niet vastleggen.", 409)
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
            self._maybe_timeout_locked(lobby)
            if lobby["status"] != "started" or lobby["phase"] not in PLAYABLE:
                raise GameError("wrong_phase", "Nu kan er niet gestemd worden.", 409)
            if player.get("ready"):
                raise GameError("locked", "Je acties zijn vastgelegd.", 409)
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
            self._maybe_timeout_locked(lobby)
            if lobby["status"] != "started" or lobby["phase"] not in PLAYABLE:
                raise GameError("wrong_phase", "Nu kan er geen persoonlijke actie.", 409)
            if player.get("ready"):
                raise GameError("locked", "Je acties zijn vastgelegd.", 409)
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

    def followup(self, token: str, action: str) -> dict:
        with self._lock:
            lobby, player = self._by_token(token)
            if lobby["status"] != "started" or lobby["phase"] != "result":
                raise GameError("wrong_phase", "Nu is er geen vervolgactie.", 409)
            taken = lobby.setdefault("followUpsTaken", {})
            if taken.get(player["id"]):
                raise GameError("already", "Je hebt al een vervolg gekozen.", 409)
            team = player["team"]
            result = lobby.get("result") or {}
            choice = None
            for item in result.get("followUps") or []:
                if item.get("team") == team and item.get("id") == action:
                    choice = item
                    break
            if not choice:
                choice = follow_up_for(action, team)
            if not choice or choice.get("id") != action:
                # also accept lookup by follow-up id across FOLLOWUPS
                for beat_id in list((result.get("contested") or [])) + [
                    b.get("id") for b in (result.get("beats") or [])
                ]:
                    candidate = follow_up_for(beat_id, team)
                    if candidate and candidate.get("id") == action:
                        choice = candidate
                        break
            if not choice or choice.get("id") != action:
                raise GameError("bad_action", "Die vervolgactie is niet beschikbaar.", 400)
            taken[player["id"]] = choice["id"]
            ev = int(choice.get("ev") or 0)
            ht = int(choice.get("ht") or 0)
            lobby["evidenceScore"] = max(0, min(100, int(lobby.get("evidenceScore") or 0) + ev))
            lobby["heat"] = max(0, min(100, int(lobby.get("heat") or 0) + ht))
            score = lobby["evidenceScore"]
            lobby["evidence"] = "hidden" if score < 25 else "partial" if score < 70 else "verified"
            if result:
                result["evidenceScore"] = lobby["evidenceScore"]
                result["heat"] = lobby["heat"]
                result["evidence"] = lobby["evidence"]
            self._append_development(
                lobby,
                team,
                choice.get("label") or "Vervolg",
                choice.get("effect") or "",
                "followup",
            )
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
                "at": _now_iso(),
            }
        )
        lobby["feed"] = lobby["feed"][-40:]

    def _append_development(self, lobby: dict, team: str | None, title: str, body: str, kind: str) -> None:
        lobby.setdefault("developments", []).append(
            {
                "id": str(uuid4()),
                "at": _now_iso(),
                "title": title,
                "body": body,
                "team": team,
                "kind": kind,
            }
        )
        lobby["developments"] = lobby["developments"][-40:]

    def _collect_actions(self, lobby: dict) -> tuple:
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
        return majority(mafia_votes), majority(det_votes), mafia_personal, det_personal

    def _merge_impacts(self, lobby: dict, result: dict) -> None:
        existing = {i["id"]: i for i in lobby.get("impacts") or []}
        for imp in build_impacts(result, lobby.get("day") or 1):
            existing.setdefault(imp["id"], imp)
            if imp["id"] not in {d.get("id") for d in lobby.get("developments") or []}:
                lobby.setdefault("developments", []).append(
                    {
                        "id": imp["id"],
                        "at": _now_iso(),
                        "title": imp.get("title"),
                        "body": imp.get("body"),
                        "team": imp.get("team"),
                        "kind": imp.get("kind") or "pressure",
                    }
                )
        lobby["impacts"] = list(existing.values())

    def _all_locked(self, lobby: dict) -> bool:
        seated = [p for p in lobby["players"] if p.get("team")]
        return bool(seated) and all(p.get("ready") for p in seated)

    def _round_seconds_left(self, lobby: dict) -> int | None:
        ends = _parse_iso(lobby.get("roundEndsAt"))
        if not ends or lobby.get("phase") not in PLAYABLE:
            return None
        left = int((ends - _now()).total_seconds())
        return max(0, left)

    def _maybe_timeout_locked(self, lobby: dict) -> None:
        if lobby.get("status") != "started" or lobby.get("phase") not in PLAYABLE:
            return
        left = self._round_seconds_left(lobby)
        if left is not None and left <= 0:
            self._resolve_play(lobby)

    def _resolve_play(self, lobby: dict) -> None:
        if lobby.get("phase") not in PLAYABLE:
            return
        result = resolve_day(*self._collect_actions(lobby))
        lobby["result"] = result
        lobby["scores"]["mafia"] += result["mafiaDelta"]
        lobby["scores"]["detective"] += result["detectiveDelta"]
        lobby["heat"] = result["heat"]
        lobby["evidence"] = result["evidence"]
        lobby["evidenceScore"] = result["evidenceScore"]
        merged = lobby.setdefault("clues", {})
        rank = {"unknown": 0, "disputed": 1, "discovered": 2, "verified": 3}
        for clue_id, clue in result.get("clues", {}).items():
            prev = merged.get(clue_id)
            if not prev or rank.get(clue["status"], 0) >= rank.get(prev.get("status"), 0):
                merged[clue_id] = clue
        self._merge_impacts(lobby, result)
        lobby["phase"] = "result"

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
                "at": _now_iso(),
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
                self._resolve_play(lobby)
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
            if lobby.get("status") == "started" and lobby.get("phase") in PLAYABLE:
                before = lobby.get("phase")
                self._maybe_timeout_locked(lobby)
                if lobby.get("phase") != before:
                    self._persist(lobby)
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
        playable = lobby["phase"] in PLAYABLE
        result = lobby.get("result")
        public_result = None
        if result and reveal:
            public_result = dict(result)
            public_result["mafiaAction"] = None
            public_result["detectiveAction"] = None
            public_result["mafiaPersonal"] = []
            public_result["detectivePersonal"] = []
            if team != "mafia":
                public_result["mafiaDebrief"] = ""
            if team != "detective":
                public_result["detectiveDebrief"] = ""
                public_result["clues"] = {}
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
                public_beat = dict(beat)
                fu = public_beat.get("followUp")
                if fu and public_beat.get("team") not in (None, team):
                    public_beat["followUp"] = None
                if public_beat.get("team") is None:
                    public_beat["followUp"] = follow_up_for(public_beat.get("id"), team)
                beats.append(public_beat)
            public_result["beats"] = beats
            public_result["events"] = [b.get("effect") for b in beats if b.get("effect")]
            public_result["followUps"] = [
                f for f in (result.get("followUps") or []) if f.get("team") == team
            ]
            shared = [b for b in beats if not b.get("team")]
            if shared:
                public_result["headline"] = shared[0].get("effect") or shared[0].get("cause")
            elif beats:
                public_result["headline"] = beats[0].get("cause")
            else:
                public_result["headline"] = "De nacht houdt haar mond."
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
            for cid, meta in CLUES.items():
                if cid in known:
                    clues.append(known[cid])
                else:
                    clues.append(
                        {
                            "id": cid,
                            "name": meta["name"],
                            "description": meta["description"],
                            "status": "unknown",
                            "foundDuring": None,
                            "reliability": 0,
                            "cinematic": meta.get("cinematic"),
                            "related": list(meta.get("related") or ()),
                        }
                    )
        ops = None
        if team == "mafia" and started:
            team_personal = [
                a
                for p in lobby["players"]
                if p["team"] == "mafia"
                for a in lobby.get("personal", {}).get(p["id"], [])
            ]
            ops = ops_dossier(
                lobby.get("heat") or 0 if reveal else 0,
                lobby.get("evidenceScore") or 0 if reveal else 0,
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
                "cinematic": imp.get("cinematic"),
                "unseen": imp["id"] not in seen_i,
            }
            impacts.append(public)
            if public["unseen"]:
                unseen_impacts.append(public)
        seen_c = set((lobby.get("cinematicSeen") or {}).get(you["id"]) or [])
        unseen_cin = []
        if public_result:
            unseen_cin = [c for c in public_result.get("cinematics") or [] if c.get("id") not in seen_c]
            if reveal:
                have = {c.get("id") for c in unseen_cin}
                for imp in unseen_impacts:
                    cid = imp.get("cinematic")
                    if cid and cid not in seen_c and cid not in have:
                        unseen_cin.append(
                            {
                                "id": cid,
                                "title": imp.get("title"),
                                "kind": "impact",
                                "team": team,
                                "replayable": True,
                            }
                        )
                        have.add(cid)
        developments = [
            d
            for d in (lobby.get("developments") or [])
            if d.get("team") == team or d.get("team") is None
        ]
        own_team = [p for p in lobby["players"] if team and p.get("team") == team]
        team_ready_n = sum(1 for p in own_team if p.get("ready"))
        presence = []
        if started and team:
            for p in own_team:
                vote = lobby.get("votes", {}).get(p["id"])
                personal = lobby.get("personal", {}).get(p["id"]) or []
                vote_label = (action_by_id(vote) or {}).get("label") if vote else None
                if p.get("ready"):
                    status = "heeft actie vastgelegd"
                elif personal:
                    status = "onderzoekt een spoor…"
                elif vote_label:
                    status = f"stemt op {vote_label}"
                else:
                    status = "leest de kade"
                presence.append({"id": p["id"], "name": p["name"], "status": status, "ready": bool(p.get("ready"))})
        shown_players = lobby["players"] if not started else own_team
        seconds_left = self._round_seconds_left(lobby) if playable and started else None
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
                "followUpTaken": bool((lobby.get("followUpsTaken") or {}).get(you["id"])) if started else False,
            },
            "players": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "team": p["team"],
                    "ready": p["ready"] if (not started or p.get("team") == team) else False,
                    "isYou": p["id"] == you["id"],
                    "isHost": p["id"] == lobby["hostId"],
                }
                for p in shown_players
            ],
            "teamSize": {"mafia": mafia_n, "detective": det_n, "cap": TEAM_CAP},
            "teamReady": {"ready": team_ready_n, "total": len(own_team)} if started and team else None,
            "opponentStatus": "RONDE ACTIEF" if started and playable else None,
            "teamPresence": presence,
            "roundSecondsLeft": seconds_left,
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
            "developments": developments,
            "canStart": (
                you["id"] == lobby["hostId"]
                and lobby["status"] == "waiting"
                and mafia_n >= 1
                and det_n >= 1
                and all(p["team"] and p["ready"] for p in lobby["players"])
            ),
        }
