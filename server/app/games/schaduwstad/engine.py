from __future__ import annotations

from collections import Counter
from typing import Literal

TeamId = Literal["mafia", "detective"]

TEAM_CAP = 6
CASE_ID = "havenkade-12"
AP_PER_DAY = 2
PHASES = ("briefing", "huddle", "personal", "action", "result", "eval")

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
    },
    "kasboek": {
        "id": "kasboek",
        "name": "Verbrand kasboek",
        "description": "Half verbrande administratie uit de loods van Van Dorp.",
        "cinematic": "clue_kasboek",
        "sources": ("evidence_inspection", "container_records"),
    },
    "bandenspoor": {
        "id": "bandenspoor",
        "name": "Bandenspoor",
        "description": "Verse groeven op natte klinkers, genomen voor de regen ze waste.",
        "cinematic": "clue_bandenspoor",
        "sources": ("tire_tracks",),
    },
    "roetmap": {
        "id": "roetmap",
        "name": "Roetkaart",
        "description": "Soot op vezel en een aangebrand dossier. Iemand wilde dit weg hebben.",
        "cinematic": "clue_roetmap",
        "sources": ("evidence_inspection", "container_records"),
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

    evidence = 18
    heat = 28
    mafia_delta = 0
    detective_delta = 0
    clues: dict[str, dict] = {}
    cinematics: list[dict] = []
    beats: list[dict] = []
    events: list[str] = []
    contested_ids: list[str] = []

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
        }

    # Contested pairs first — they replace the individual cinematics.
    handled: set[str] = set()
    for pair, cinematic in CONTESTED.items():
        det_id = next(iter(pair & d_all), None)
        maf_id = next(iter(pair & m_all), None)
        if not det_id or not maf_id:
            continue
        handled.update({det_id, maf_id})
        contested_ids.append(cinematic)
        det_label = action_by_id(det_id)["label"]
        maf_label = action_by_id(maf_id)["label"]
        if cinematic == "camera_conflict":
            evidence += 6
            heat += 10
            mafia_delta += SCORE["stalemate"]
            detective_delta += SCORE["detective_lead"]
            add_clue("kenteken", "disputed", det_id, 48)
            headline = "Vier seconden beeld. Dan sneeuw."
            mdef = "De camera is dood. Niet dood genoeg."
            ddef = "Een fragment van vier seconden werd teruggevonden."
            event = "Cameradata botste op sabotage."
        elif cinematic == "witness_conflict":
            evidence += 4
            heat += 12
            mafia_delta += SCORE["mafia_protect"]
            detective_delta += SCORE["stalemate"]
            headline = "Rik praat met twee monden."
            mdef = "Rik houdt de gevaarlijke namen binnen."
            ddef = "De getuige sluit af. Iemand was hem voor."
            event = "Getuige ondervraagd en onder druk gezet."
        elif cinematic == "vehicle_conflict":
            evidence += 7
            heat += 8
            mafia_delta += SCORE["stalemate"]
            detective_delta += SCORE["detective_lead"]
            add_clue("bandenspoor", "disputed", det_id, 55)
            add_clue("kenteken", "discovered", det_id, 62)
            headline = "De bus is weg. De groeven niet."
            mdef = "Het voertuig is veilig. De kade niet schoon."
            ddef = "Verse sporen, halve plaat, lege parkeerplaats."
            event = "Voertuigspoor botste op verplaatsing."
        else:
            evidence += 5
            heat += 6
            mafia_delta += SCORE["mafia_contain"]
            detective_delta += SCORE["stalemate"]
            add_clue("kasboek", "disputed", det_id, 40)
            headline = "De stukken waren er. Nu half."
            mdef = "De kern is weg. Ze houden as over."
            ddef = "Iemand tilde de map op voor jullie."
            event = "Bewijs verplaatst tijdens inspectie."
        cinematics.append(_cue(cinematic, headline, "contested"))
        beats.append(
            {
                "id": cinematic,
                "cause": f"{det_label} × {maf_label}",
                "effect": event,
                "cinematic": cinematic,
                "evidenceDelta": evidence,
                "heatDelta": heat,
            }
        )
        events.append(event)

    def uncontested_detective(action_id: str) -> None:
        nonlocal evidence, heat, detective_delta
        item = action_by_id(action_id)
        if action_id in ("camera_analysis", "license_plate"):
            evidence += 10
            heat += 6
            detective_delta += SCORE["detective_evidence"]
            add_clue("kenteken", "discovered", action_id, 78)
            add_clue("kenteken", "verified", action_id, 88) if action_id == "license_plate" else None
            effect = "Camerabeeld en kenteken komen samen."
        elif action_id == "evidence_inspection":
            evidence += 12
            heat += 5
            detective_delta += SCORE["detective_link"]
            add_clue("kasboek", "discovered", action_id, 74)
            add_clue("roetmap", "discovered", action_id, 70)
            effect = "Roet en papier overleefden de brand."
        elif action_id == "tire_tracks":
            evidence += 9
            heat += 4
            detective_delta += SCORE["detective_lead"]
            add_clue("bandenspoor", "verified", action_id, 84)
            effect = "Het spoor is gegoten voor de regen."
        elif action_id == "witness":
            evidence += 6
            heat += 7
            detective_delta += SCORE["detective_lead"]
            effect = "Rik beschrijft twee mannen en een zwarte wagen."
        else:
            evidence += 11
            heat += 5
            detective_delta += SCORE["detective_link"]
            add_clue("kasboek", "verified", action_id, 90)
            add_clue("roetmap", "discovered", action_id, 66)
            effect = "Containerboeking koppelt Van Dorp aan de loods."
        cinematics.append(_cue(item["cinematic"], item["label"], "action", "detective"))
        events.append(effect)
        beats.append(
            {
                "id": action_id,
                "cause": item["label"],
                "effect": effect,
                "cinematic": item["cinematic"],
            }
        )

    def uncontested_mafia(action_id: str) -> None:
        nonlocal evidence, heat, mafia_delta
        item = action_by_id(action_id)
        if action_id == "move_vehicle":
            evidence = max(0, evidence - 6)
            heat = max(8, heat - 4)
            mafia_delta += SCORE["mafia_contain"]
            effect = "De bus is van de kade."
        elif action_id == "camera_sabotage":
            evidence = max(0, evidence - 8)
            heat += 3
            mafia_delta += SCORE["mafia_protect"]
            effect = "De kade is blind."
        elif action_id == "move_evidence":
            evidence = max(0, evidence - 10)
            heat = max(8, heat - 6)
            mafia_delta += SCORE["mafia_protect"]
            effect = "De stukken zijn weg."
        elif action_id == "warn_contact":
            heat = max(8, heat - 3)
            mafia_delta += SCORE["mafia_mislead"]
            effect = "Het contact zwijgt."
        elif action_id == "false_alibi":
            heat = max(8, heat - 5)
            mafia_delta += SCORE["mafia_mislead"]
            effect = "De alibi's staan te strak."
        else:
            evidence = max(0, evidence - 4)
            heat += 8
            mafia_delta += SCORE["mafia_protect"]
            effect = "Rik trekt zijn verklaring in."
        cinematics.append(_cue(item["cinematic"], item["label"], "action", "mafia"))
        events.append(effect)
        beats.append(
            {
                "id": action_id,
                "cause": item["label"],
                "effect": effect,
                "cinematic": item["cinematic"],
            }
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
    elif not events:
        headline = "De nacht houdt haar mond."
        mdef = "Jullie houden de schade beperkt."
        ddef = "De kade geeft weinig prijs."
    else:
        headline = beats[0]["cause"] if beats else "Havenkade 12."
        # Prefer a contested headline already set in the loop.
        if contested_ids:
            pass
        mdef = next((e for e in events if e), "Jullie houden de schade beperkt.")
        ddef = next((e for e in events if e), "De kade geeft weinig prijs.")
        if contested_ids:
            # headlines already assigned in contested branch; recover last set via events
            headline = events[0]

    # Clue-reveal cinematics after action/conflict, detectives only.
    for clue in clues.values():
        if clue["status"] in ("discovered", "verified", "disputed"):
            cinematics.append(
                _cue(clue["cinematic"], clue["name"], "clue", "detective")
            )

    evidence = max(0, min(100, evidence))
    heat = max(0, min(100, heat))
    band = "hidden" if evidence < 25 else "partial" if evidence < 70 else "verified"

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
        "evidence": band,
        "evidenceScore": evidence,
        "headline": headline,
        "mafiaDebrief": mdef,
        "detectiveDebrief": ddef,
        "events": events,
        "beats": beats,
        "cinematics": cinematics,
        "clues": clues,
        "contested": contested_ids,
    }


def ops_dossier(heat: int, evidence_score: int, result: dict | None) -> dict:
    protected = []
    threats = []
    risks = []
    personal = (result or {}).get("mafiaPersonal") or []
    contested = (result or {}).get("contested") or []
    if "move_vehicle" in personal:
        protected.append("Voertuig van de kade")
    if "camera_sabotage" in personal:
        protected.append("Camerasysteem")
    if "move_evidence" in personal:
        protected.append("Administratie")
    if "camera_conflict" in contested:
        threats.append("Recherche herstelde camerabeeld")
        risks.append("Kentekenfragment in omloop")
    if "vehicle_conflict" in contested:
        threats.append("Bandensporen niet schoon")
    if "witness_conflict" in contested:
        risks.append("Rik is onbetrouwbaar geworden")
    if evidence_score >= 70:
        threats.append("Dossier nadert afronding")
    if heat >= 60:
        risks.append("De kade is te heet")
    if not protected:
        protected.append("Nog niets veiliggesteld")
    if not threats:
        threats.append("Geen zichtbare recherche-winst")
    return {
        "heat": heat,
        "evidenceThreat": evidence_score,
        "protected": protected,
        "threats": threats,
        "risks": risks or ["Nachtrust is een luxe"],
    }
