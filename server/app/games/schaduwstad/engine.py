from __future__ import annotations

from collections import Counter
from typing import Literal

try:
    from .content import DAYS, build_impacts, spec_for, follow_up_for
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from content import DAYS, build_impacts, spec_for, follow_up_for

TeamId = Literal["mafia", "detective"]

TEAM_CAP = 6
CASE_ID = "havenkade-12"
AP_PER_DAY = 2
ROUND_SECONDS = 600
PLAYABLE = ("play", "briefing", "huddle", "personal", "action")
PHASES = ("play", "result", "eval")
EVIDENCE_BASE = 18
HEAT_BASE = 28

MAFIA_ACTIONS = (
    {
        "id": "move_vehicle",
        "label": "Voertuig verplaatsen",
        "hint": "De zwarte bus moet weg van Havenkade 12.",
        "ap": 1,
        "cinematic": "move_vehicle",
    },
    {
        "id": "camera_sabotage",
        "label": "Camera saboteren",
        "hint": "Maak de kadeblind.",
        "ap": 1,
        "cinematic": "camera_sabotage",
    },
    {
        "id": "move_evidence",
        "label": "Bewijs verplaatsen",
        "hint": "Kasboeken en de map uit de loods.",
        "ap": 1,
        "cinematic": "move_evidence",
    },
    {
        "id": "warn_contact",
        "label": "Contact waarschuwen",
        "hint": "Iemand aan de veerhaven moet zwijgen.",
        "ap": 1,
        "cinematic": "warn_contact",
    },
    {
        "id": "false_alibi",
        "label": "Vals alibi",
        "hint": "Iedereen was ergens anders. Natuurlijk.",
        "ap": 1,
        "cinematic": "false_alibi",
    },
    {
        "id": "pressure_witness",
        "label": "Getuige onder druk",
        "hint": "Rik heeft te veel gezien.",
        "ap": 2,
        "cinematic": "pressure_witness",
    },
)

DETECTIVE_ACTIONS = (
    {
        "id": "camera_analysis",
        "label": "Cameradata analyseren",
        "hint": "Beelden van 02:14, Havenkade 12.",
        "ap": 1,
        "cinematic": "camera_analysis",
    },
    {
        "id": "evidence_inspection",
        "label": "Bewijs onderzoeken",
        "hint": "Roet, papier, de verbrande map.",
        "ap": 1,
        "cinematic": "evidence_inspection",
    },
    {
        "id": "license_plate",
        "label": "Kenteken natrekken",
        "hint": "SCH-** op de kade.",
        "ap": 1,
        "cinematic": "license_plate",
    },
    {
        "id": "tire_tracks",
        "label": "Bandensporen analyseren",
        "hint": "Verse groeven in de regen.",
        "ap": 1,
        "cinematic": "tire_tracks",
    },
    {
        "id": "witness",
        "label": "Getuige ondervragen",
        "hint": "Rik bij de kade.",
        "ap": 1,
        "cinematic": "witness",
    },
    {
        "id": "container_records",
        "label": "Containerregistratie",
        "hint": "Wie boekte de loods van Van Dorp?",
        "ap": 2,
        "cinematic": "container_records",
    },
)

# Old v0.1 ids still accepted as aliases (no rewrite of live lobbies).
ALIASES = {
    "wipe_trace": "move_vehicle",
    "organize_alibi": "false_alibi",
    "move_info": "move_evidence",
    "investigate_location": "tire_tracks",
    "question_witness": "witness",
    "analyze_evidence": "evidence_inspection",
}

CONTESTED = {
    frozenset({"camera_analysis", "camera_sabotage"}): "camera_conflict",
    frozenset({"witness", "pressure_witness"}): "witness_conflict",
    frozenset({"license_plate", "move_vehicle"}): "vehicle_conflict",
    frozenset({"tire_tracks", "move_vehicle"}): "vehicle_conflict",
    frozenset({"evidence_inspection", "move_evidence"}): "conflict",
}

CLUES = {
    "kenteken": {
        "id": "kenteken",
        "name": "Kentekenfragment",
        "description": "Modderig fragment van een Nederlandse plaat. Letters deels weg.",
        "cinematic": "clue_kenteken",
        "sources": ("camera_analysis", "license_plate"),
        "related": ("bandenspoor",),
    },
    "kasboek": {
        "id": "kasboek",
        "name": "Verbrand kasboek",
        "description": "Half verbrande administratie uit de loods van Van Dorp.",
        "cinematic": "clue_kasboek",
        "sources": ("evidence_inspection", "container_records"),
        "related": ("roetmap",),
    },
    "bandenspoor": {
        "id": "bandenspoor",
        "name": "Bandenspoor",
        "description": "Verse groeven op natte klinkers, genomen voor de regen ze waste.",
        "cinematic": "clue_bandenspoor",
        "sources": ("tire_tracks",),
        "related": ("kenteken",),
    },
    "roetmap": {
        "id": "roetmap",
        "name": "Roetkaart",
        "description": "Soot op vezel en een aangebrand dossier. Iemand wilde dit weg hebben.",
        "cinematic": "clue_roetmap",
        "sources": ("evidence_inspection", "container_records"),
        "related": ("kasboek",),
    },
}

SCORE = {
    "mafia_protect": 3,
    "mafia_mislead": 3,
    "mafia_contain": 2,
    "detective_evidence": 3,
    "detective_lead": 2,
    "detective_link": 3,
    "stalemate": 1,
}


def briefing_for(team: TeamId) -> str:
    if team == "mafia":
        return (
            "HAVENKADE 12, 02:14. Jullie hebben de loods van Van Dorp leeggehaald. "
            "Een bestelbus brandt nog na. Rik heeft jullie gezien. Gevaarlijke sporen: "
            "kenteken SCH-14-X, kasboeken, rook in de kleding."
        )
    return (
        "HAVENKADE 12, 03:02. Brand in een loods. Getuige: twee mannen, zwarte wagen. "
        "Sporen: banden, half verbrande map, kenteken SCH-**. Dit is geen toeval."
    )


def actions_for(team: TeamId | None):
    if team == "mafia":
        return list(MAFIA_ACTIONS)
    if team == "detective":
        return list(DETECTIVE_ACTIONS)
    return []


def action_by_id(action_id: str) -> dict | None:
    canon = canonicalize(action_id)
    for item in (*MAFIA_ACTIONS, *DETECTIVE_ACTIONS):
        if item["id"] == canon:
            return item
    return None


def canonicalize(action_id: str | None) -> str | None:
    if not action_id:
        return None
    return ALIASES.get(action_id, action_id)


def majority(votes: list[str]) -> str | None:
    cleaned = [canonicalize(v) for v in votes if v]
    if not cleaned:
        return None
    return Counter(cleaned).most_common(1)[0][0]


def _cue(cid: str, title: str, kind: str, team: str | None = None) -> dict:
    return {"id": cid, "title": title, "kind": kind, "team": team, "replayable": True}


def resolve_day(
    mafia_team: str | None,
    detective_team: str | None,
    mafia_personal: list[str] | None = None,
    detective_personal: list[str] | None = None,
) -> dict:
    mafia_team = canonicalize(mafia_team)
    detective_team = canonicalize(detective_team)
    m_pers = [canonicalize(a) for a in (mafia_personal or []) if a]
    d_pers = [canonicalize(a) for a in (detective_personal or []) if a]
    m_all = set(m_pers + ([mafia_team] if mafia_team else []))
    d_all = set(d_pers + ([detective_team] if detective_team else []))

    evidence = EVIDENCE_BASE
    heat = HEAT_BASE
    mafia_delta = 0
    detective_delta = 0
    clues: dict[str, dict] = {}
    cinematics: list[dict] = []
    beats: list[dict] = []
    events: list[str] = []
    contested_ids: list[str] = []
    m_lines: list[str] = []
    d_lines: list[str] = []
    headline = "De nacht houdt haar mond."
    mdef = "Jullie houden de schade beperkt."
    ddef = "De kade geeft weinig prijs."

    def add_beat(
        *,
        beat_id: str,
        cause: str,
        effect: str,
        cinematic: str,
        team: str | None = None,
        ev: int = 0,
        ht: int = 0,
    ) -> None:
        beats.append(
            {
                "id": beat_id,
                "cause": cause,
                "effect": effect,
                "cinematic": cinematic,
                "team": team,
                "evidenceDelta": ev,
                "heatDelta": ht,
                "followUp": follow_up_for(beat_id, team),
            }
        )
        events.append(effect)

    def add_clue(clue_id: str, status: str, source: str, reliability: int) -> None:
        meta = CLUES[clue_id]
        prev = clues.get(clue_id)
        if prev and prev["status"] == "verified":
            return
        if prev and status == "disputed":
            prev["status"] = "disputed"
            prev["reliability"] = min(prev["reliability"], reliability)
            return
        clues[clue_id] = {
            "id": clue_id,
            "name": meta["name"],
            "description": meta["description"],
            "status": status,
            "foundDuring": source,
            "reliability": reliability,
            "cinematic": meta["cinematic"],
            "related": list(meta.get("related") or ()),
        }

    # Contested pairs first — they replace the individual cinematics.
    handled: set[str] = set()
    for pair, cinematic in CONTESTED.items():
        det_id = next(iter(pair & d_all), None)
        maf_id = next(iter(pair & m_all), None)
        if not det_id or not maf_id:
            continue
        handled.update({det_id, maf_id})
        if cinematic in contested_ids:
            continue
        contested_ids.append(cinematic)
        if cinematic == "camera_conflict":
            d_ev, d_ht = 6, 10
            mafia_delta += SCORE["stalemate"]
            detective_delta += SCORE["detective_lead"]
            add_clue("kenteken", "disputed", det_id, 48)
            headline = "Vier seconden beeld. Dan sneeuw."
            m_lines.append("De camera is dood. Niet dood genoeg.")
            d_lines.append("Een fragment van vier seconden werd teruggevonden.")
            event = "Cameradata botste op sabotage."
        elif cinematic == "witness_conflict":
            d_ev, d_ht = 4, 12
            mafia_delta += SCORE["mafia_protect"]
            detective_delta += SCORE["stalemate"]
            headline = "Rik praat met twee monden."
            m_lines.append("Rik houdt de gevaarlijke namen binnen.")
            d_lines.append("De getuige sluit af. Iemand was hem voor.")
            event = "Getuige ondervraagd en onder druk gezet."
        elif cinematic == "vehicle_conflict":
            d_ev, d_ht = 7, 8
            mafia_delta += SCORE["stalemate"]
            detective_delta += SCORE["detective_lead"]
            add_clue("bandenspoor", "disputed", det_id, 55)
            add_clue("kenteken", "discovered", det_id, 62)
            headline = "De bus is weg. De groeven niet."
            m_lines.append("Het voertuig is veilig. De kade niet schoon.")
            d_lines.append("Verse sporen, halve plaat, lege parkeerplaats.")
            event = "Voertuigspoor botste op verplaatsing."
        else:
            d_ev, d_ht = 5, 6
            mafia_delta += SCORE["mafia_contain"]
            detective_delta += SCORE["stalemate"]
            add_clue("kasboek", "disputed", det_id, 40)
            headline = "De stukken waren er. Nu half."
            m_lines.append("De kern is weg. Ze houden as over.")
            d_lines.append("Iemand tilde de map op voor jullie.")
            event = "Bewijs verplaatst tijdens inspectie."
        evidence += d_ev
        heat += d_ht
        cinematics.append(_cue(cinematic, headline, "contested"))
        add_beat(
            beat_id=cinematic,
            cause=event,
            effect=event,
            cinematic=cinematic,
            team=None,
            ev=d_ev,
            ht=d_ht,
        )

    def uncontested_detective(action_id: str) -> None:
        nonlocal evidence, heat, detective_delta
        item = action_by_id(action_id)
        if action_id in ("camera_analysis", "license_plate"):
            d_ev, d_ht = 10, 6
            detective_delta += SCORE["detective_evidence"]
            add_clue("kenteken", "discovered", action_id, 78)
            if action_id == "license_plate":
                add_clue("kenteken", "verified", action_id, 88)
            effect = "Camerabeeld en kenteken komen samen."
        elif action_id == "evidence_inspection":
            d_ev, d_ht = 12, 5
            detective_delta += SCORE["detective_link"]
            add_clue("kasboek", "discovered", action_id, 74)
            add_clue("roetmap", "discovered", action_id, 70)
            effect = "Roet en papier overleefden de brand."
        elif action_id == "tire_tracks":
            d_ev, d_ht = 9, 4
            detective_delta += SCORE["detective_lead"]
            add_clue("bandenspoor", "verified", action_id, 84)
            effect = "Het spoor is gegoten voor de regen."
        elif action_id == "witness":
            d_ev, d_ht = 6, 7
            detective_delta += SCORE["detective_lead"]
            effect = "Rik beschrijft twee mannen en een zwarte wagen."
        else:
            d_ev, d_ht = 11, 5
            detective_delta += SCORE["detective_link"]
            add_clue("kasboek", "verified", action_id, 90)
            add_clue("roetmap", "discovered", action_id, 66)
            effect = "Containerboeking koppelt Van Dorp aan de loods."
        evidence += d_ev
        heat += d_ht
        d_lines.append(effect)
        cinematics.append(_cue(item["cinematic"], item["label"], "action", "detective"))
        add_beat(
            beat_id=action_id,
            cause=item["label"],
            effect=effect,
            cinematic=item["cinematic"],
            team="detective",
            ev=d_ev,
            ht=d_ht,
        )

    def uncontested_mafia(action_id: str) -> None:
        nonlocal evidence, heat, mafia_delta
        item = action_by_id(action_id)
        if action_id == "move_vehicle":
            d_ev, d_ht = -6, -4
            mafia_delta += SCORE["mafia_contain"]
            effect = "De bus is van de kade."
        elif action_id == "camera_sabotage":
            d_ev, d_ht = -8, 3
            mafia_delta += SCORE["mafia_protect"]
            effect = "De kade is blind."
        elif action_id == "move_evidence":
            d_ev, d_ht = -10, -6
            mafia_delta += SCORE["mafia_protect"]
            effect = "De stukken zijn weg."
        elif action_id == "warn_contact":
            d_ev, d_ht = 0, -3
            mafia_delta += SCORE["mafia_mislead"]
            effect = "Het contact zwijgt."
        elif action_id == "false_alibi":
            d_ev, d_ht = 0, -5
            mafia_delta += SCORE["mafia_mislead"]
            effect = "De alibi's staan te strak."
        else:
            d_ev, d_ht = -4, 8
            mafia_delta += SCORE["mafia_protect"]
            effect = "Rik trekt zijn verklaring in."
        evidence = max(0, evidence + d_ev)
        heat = max(8, heat + d_ht) if d_ht < 0 else heat + d_ht
        m_lines.append(effect)
        cinematics.append(_cue(item["cinematic"], item["label"], "action", "mafia"))
        add_beat(
            beat_id=action_id,
            cause=item["label"],
            effect=effect,
            cinematic=item["cinematic"],
            team="mafia",
            ev=d_ev,
            ht=d_ht,
        )

    for action_id in d_all:
        if action_id not in handled:
            uncontested_detective(action_id)
    for action_id in m_all:
        if action_id not in handled:
            uncontested_mafia(action_id)

    if not m_all and not d_all:
        mafia_delta = SCORE["stalemate"]
        detective_delta = SCORE["stalemate"]
        heat = 12
        events = ["Geen van beide teams durfde te bewegen."]
        headline = "Stilte aan de kade."
        mdef = "Jullie hielden de schade beperkt door niets te doen."
        ddef = "De kade geeft weinig prijs."
    else:
        if contested_ids:
            shared = next((b for b in beats if not b.get("team")), None)
            headline = (shared or beats[0])["effect"] if beats else headline
        elif beats:
            headline = beats[0]["cause"]
        mdef = " ".join(m_lines) or "Jullie houden de schade beperkt."
        ddef = " ".join(d_lines) or "De kade geeft weinig prijs."

    # Clue-reveal cinematics after action/conflict, detectives only.
    for clue in clues.values():
        if clue["status"] in ("discovered", "verified", "disputed"):
            cinematics.append(
                _cue(clue["cinematic"], clue["name"], "clue", "detective")
            )

    evidence = max(0, min(100, evidence))
    heat = max(0, min(100, heat))
    band = "hidden" if evidence < 25 else "partial" if evidence < 70 else "verified"
    follow_ups: list[dict] = []
    for beat in beats:
        if beat.get("followUp"):
            follow_ups.append({"beatId": beat["id"], **beat["followUp"], "team": beat.get("team")})
    for cid in contested_ids:
        for team_id in ("mafia", "detective"):
            extra = follow_up_for(cid, team_id)
            if extra and not any(f.get("id") == extra["id"] and f.get("team") == team_id for f in follow_ups):
                follow_ups.append({"beatId": cid, **extra, "team": team_id})

    if not m_all and not d_all:
        headline = "Stilte aan de kade."
        mdef = "Jullie hielden de schade beperkt door niets te doen."
        ddef = "De kade geeft weinig prijs."

    return {
        "mafiaAction": mafia_team,
        "detectiveAction": detective_team,
        "mafiaPersonal": m_pers,
        "detectivePersonal": d_pers,
        "mafiaDelta": mafia_delta,
        "detectiveDelta": detective_delta,
        "heat": heat,
        "heatOld": HEAT_BASE,
        "heatDelta": heat - HEAT_BASE,
        "evidence": band,
        "evidenceScore": evidence,
        "evidenceOld": EVIDENCE_BASE,
        "evidenceDelta": evidence - EVIDENCE_BASE,
        "headline": headline,
        "mafiaDebrief": mdef,
        "detectiveDebrief": ddef,
        "events": events,
        "beats": beats,
        "cinematics": cinematics,
        "clues": clues,
        "contested": contested_ids,
        "followUps": follow_ups,
    }


def ops_dossier(heat: int, evidence_score: int, result: dict | None, personal: list[str] | None = None) -> dict:
    protected = []
    threats = []
    risks = []
    locations = []
    own = list(personal or []) or list((result or {}).get("mafiaPersonal") or [])
    contested = (result or {}).get("contested") or []
    if "move_vehicle" in own:
        protected.append("Voertuig van de kade")
    if "camera_sabotage" in own:
        protected.append("Camerasysteem")
    if "move_evidence" in own:
        protected.append("Administratie")
    if "warn_contact" in own:
        protected.append("Contact zwijgt")
    if "false_alibi" in own:
        protected.append("Alibi's staan")
    if "pressure_witness" in own:
        protected.append("Rik onder druk")
    if result:
        if "camera_conflict" in contested:
            threats.append("Recherche herstelde camerabeeld")
            risks.append("Kentekenfragment in omloop")
            locations.append("Cameras kade — gecompromitteerd")
        if "vehicle_conflict" in contested:
            threats.append("Bandensporen niet schoon")
            locations.append("Parkeerplaats Havenkade 12 — sporen")
        if "witness_conflict" in contested:
            risks.append("Rik is onbetrouwbaar geworden")
            locations.append("Veerhaven — getuige wankel")
        if "conflict" in contested:
            locations.append("Loods Van Dorp — administratie geraakt")
        if evidence_score >= 70:
            threats.append("Dossier nadert afronding")
        if heat >= 60:
            risks.append("De kade is te heet")
    if not protected:
        protected.append("Nog niets veiliggesteld")
    if not threats:
        threats.append("Recherche beweegt in het donker" if not result else "Geen zichtbare recherche-winst")
    return {
        "heat": heat if result else 0,
        "evidenceThreat": evidence_score if result else 0,
        "protected": protected,
        "threats": threats,
        "risks": risks or (["Houd de kade stil"] if not result else ["Nachtrust is een luxe"]),
        "locations": locations or ["Havenkade 12 — nog stil"],
    }
