"""Data-driven day content. Future days add a spec + clips; the player stays."""

from __future__ import annotations

DAYS = {
    1: {
        "id": "havenkade-12",
        "day": 1,
        "title": "Havenkade 12",
        "caseId": "havenkade-12",
        "ap": 2,
        "next": None,
    },
}


def spec_for(day: int) -> dict:
    return dict(DAYS.get(int(day) or 1, DAYS[1]))


# Sanitized enemy-facing copy. Never includes the other team's action ids.
# Contested: both teams. Uncontested: only the opposing team (pressure).
IMPACTS = {
    "camera_conflict": {
        "detective": {
            "title": "Vier seconden, dan sneeuw",
            "body": "Iemand doofde de kade. Jullie hielden een fragment. Evidence steeg. Heat ook.",
            "kind": "conflict",
        },
        "mafia": {
            "title": "De camera was niet dood genoeg",
            "body": "Recherche sleepte beeld terug. Iets van de kade leeft nog.",
            "kind": "conflict",
        },
    },
    "witness_conflict": {
        "detective": {
            "title": "Rik praat met twee monden",
            "body": "De getuige sluit af. Iemand was hem voor. Heat stijgt hard.",
            "kind": "conflict",
        },
        "mafia": {
            "title": "Rik houdt de namen binnen",
            "body": "Hij zwijgt over jullie. Maar hij is onbetrouwbaar geworden.",
            "kind": "conflict",
        },
    },
    "vehicle_conflict": {
        "detective": {
            "title": "De bus is weg. De groeven niet",
            "body": "Verse sporen, halve plaat, lege parkeerplaats. Iemand verplaatste het voertuig.",
            "kind": "conflict",
        },
        "mafia": {
            "title": "Het voertuig is veilig. De kade niet schoon",
            "body": "Bandensporen bleven achter. Recherche las de groeven.",
            "kind": "conflict",
        },
    },
    "conflict": {
        "detective": {
            "title": "De stukken waren er. Nu half",
            "body": "Iemand tilde de map op voor jullie. As en papier. Evidence blijft fragmentarisch.",
            "kind": "conflict",
        },
        "mafia": {
            "title": "De kern is weg. Ze houden as over",
            "body": "Recherche vond restanten. Niet de kern. Nog niet.",
            "kind": "conflict",
        },
    },
    "camera_analysis": {
        "mafia": {
            "title": "Iemand las de kadebeelden",
            "body": "Cameradata beweegt. Jullie zijn niet onzichtbaar.",
            "kind": "pressure",
        },
    },
    "evidence_inspection": {
        "mafia": {
            "title": "Iemand zat in de as",
            "body": "Papier en roet gaan het dossier in. Administratie is niet veilig.",
            "kind": "pressure",
        },
    },
    "license_plate": {
        "mafia": {
            "title": "De plaat leeft",
            "body": "Iemand trekt letters na. Het kenteken is niet meer van jullie alleen.",
            "kind": "pressure",
        },
    },
    "tire_tracks": {
        "mafia": {
            "title": "Iemand las de groeven",
            "body": "De klinkers houden sporen. Jullie wagen is niet onzichtbaar.",
            "kind": "pressure",
        },
    },
    "witness": {
        "mafia": {
            "title": "Rik praat",
            "body": "De getuige beschrijft mannen en een wagen. Houd hem in de gaten.",
            "kind": "pressure",
        },
    },
    "container_records": {
        "mafia": {
            "title": "De loods staat op papier",
            "body": "Iemand koppelt de boeking. Van Dorp is een naam te veel.",
            "kind": "pressure",
        },
    },
    "move_vehicle": {
        "detective": {
            "title": "De kade is leeg",
            "body": "Het voertuig is weg voor jullie er waren. Sporen misschien niet.",
            "kind": "pressure",
        },
    },
    "camera_sabotage": {
        "detective": {
            "title": "De kade valt blind",
            "body": "Cameradata sterft midden in het beeld. Iemand was jullie voor.",
            "kind": "pressure",
        },
    },
    "move_evidence": {
        "detective": {
            "title": "De stukken zijn lichter",
            "body": "Iets ontbreekt in de as. De map is aangerand.",
            "kind": "pressure",
        },
    },
    "warn_contact": {
        "detective": {
            "title": "Een mond gaat dicht",
            "body": "Aan de veerhaven wordt gezwegen. Iemand is gewaarschuwd.",
            "kind": "pressure",
        },
    },
    "false_alibi": {
        "detective": {
            "title": "De alibi's staan te strak",
            "body": "Iedereen was ergens anders. Natuurlijk. Heat daalt niet vanzelf.",
            "kind": "pressure",
        },
    },
    "pressure_witness": {
        "detective": {
            "title": "Rik trekt zich terug",
            "body": "De getuige sluit af. Iemand zette hem onder druk.",
            "kind": "pressure",
        },
    },
}


def build_impacts(result: dict) -> list[dict]:
    """Team-scoped, sanitized pressure. No enemy action ids leak to the other client."""
    from uuid import uuid4

    out: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(source: str, team: str) -> None:
        payload = (IMPACTS.get(source) or {}).get(team)
        if not payload:
            return
        key = (team, source)
        if key in seen:
            return
        seen.add(key)
        out.append(
            {
                "id": str(uuid4()),
                "team": team,
                "title": payload["title"],
                "body": payload["body"],
                "kind": payload.get("kind") or "pressure",
            }
        )

    for cid in result.get("contested") or []:
        add(cid, "mafia")
        add(cid, "detective")
    for beat in result.get("beats") or []:
        owner = beat.get("team")
        if not owner:
            continue
        enemy = "mafia" if owner == "detective" else "detective"
        add(beat.get("id") or "", enemy)
    return out[:8]
