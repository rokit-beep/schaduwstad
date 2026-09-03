from __future__ import annotations

from collections import Counter
from typing import Literal

TeamId = Literal["mafia", "detective"]

TEAM_CAP = 6
CASE_ID = "havenkade-12"

MAFIA_ACTIONS = (
    {"id": "wipe_trace", "label": "Spoor wissen", "hint": "Veeg de Havenkade schoon."},
    {"id": "organize_alibi", "label": "Alibi organiseren", "hint": "Iedereen was ergens anders."},
    {"id": "move_info", "label": "Informatie verplaatsen", "hint": "Haal de administratie weg."},
)
DETECTIVE_ACTIONS = (
    {"id": "investigate_location", "label": "Locatie onderzoeken", "hint": "Havenkade 12, voor de regen."},
    {"id": "question_witness", "label": "Getuige ondervragen", "hint": "Rik bij de kade."},
    {"id": "analyze_evidence", "label": "Bewijs analyseren", "hint": "Roet, papier, kenteken."},
)

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


def actions_for(team: TeamId):
    return MAFIA_ACTIONS if team == "mafia" else DETECTIVE_ACTIONS


def majority(votes: list[str]) -> str | None:
    if not votes:
        return None
    return Counter(votes).most_common(1)[0][0]


def resolve_day(mafia: str | None, detective: str | None) -> dict:
    m, d = mafia, detective
    result = {
        "mafiaAction": m,
        "detectiveAction": d,
        "mafiaDelta": 0,
        "detectiveDelta": 0,
        "heat": 28,
        "evidence": "hidden",
        "headline": "De nacht houdt haar mond.",
        "mafiaDebrief": "Jullie houden de schade beperkt.",
        "detectiveDebrief": "De kade geeft weinig prijs.",
        "events": [],
    }
    table = {
        ("wipe_trace", "investigate_location"): (
            SCORE["stalemate"], SCORE["detective_lead"], 46, "partial",
            "De kade is geschrobd. Niet schoon genoeg.",
            "Jullie veegden, maar te laat voor de bandensporen.",
            "Verse schoonmaak. Iemand was hier na de brand.",
            "Recherche vindt natte veegsporen over bandenafdrukken.",
        ),
        ("wipe_trace", "question_witness"): (
            SCORE["mafia_protect"], SCORE["stalemate"], 34, "hidden",
            "Rik houdt zijn mond. De kade is koud.",
            "Rik is afgekocht. De kade zelf is bijna schoon.",
            "De getuige zwijgt. Jullie misten de locatie.",
            "Getuige trekt zijn verklaring in.",
        ),
        ("wipe_trace", "analyze_evidence"): (
            SCORE["stalemate"], SCORE["detective_evidence"], 52, "partial",
            "Het lab houdt een restant over.",
            "De kade is schoon, de tas in het lab niet.",
            "Roet op papier. Iemand wilde dit weg hebben.",
            "Lab meldt opzettelijke beschadiging van stukken.",
        ),
        ("organize_alibi", "question_witness"): (
            SCORE["mafia_mislead"], 0, 22, "hidden",
            "Iedereen was ergens anders. Natuurlijk.",
            "Rik herhaalt jullie alibi woord voor woord.",
            "De getuige klinkt ingestudeerd. Nog geen bewijs.",
            "Alibi's kloppen te goed.",
        ),
        ("organize_alibi", "investigate_location"): (
            SCORE["stalemate"], SCORE["detective_lead"], 48, "partial",
            "Mooie alibi's. Slechte timing op de kade.",
            "Mondeling staan jullie sterk. De loods niet.",
            "De locatie spreekt de alibi's tegen.",
            "Brandstichtingstijdstip botst met alibi's.",
        ),
        ("organize_alibi", "analyze_evidence"): (
            SCORE["stalemate"], SCORE["detective_link"], 55, "partial",
            "Papier liegt minder makkelijk dan mensen.",
            "Alibi's houden stand in de kroeg, niet in het lab.",
            "Administratie noemt namen die ergens anders waren.",
            "Kasboekfragmenten koppelen namen aan de loods.",
        ),
        ("move_info", "analyze_evidence"): (
            SCORE["mafia_protect"], 0, 18, "hidden",
            "Het lab krijgt een lege map.",
            "De stukken zijn weg. Laat ze maar zoeken.",
            "De verbrande map is te schoon. Iets is verplaatst.",
            "Forensisch team mist de kernstukken.",
        ),
        ("move_info", "investigate_location"): (
            SCORE["mafia_contain"], SCORE["stalemate"], 36, "hidden",
            "De loods is een omhulsel.",
            "Jullie haalden de administratie eruit.",
            "De kade is vers, maar de papieren zijn weg.",
            "Lege kluis achter een aangebrand bureau.",
        ),
        ("move_info", "question_witness"): (
            SCORE["stalemate"], SCORE["detective_lead"], 44, "partial",
            "Rik zag de tas vertrekken.",
            "De stukken zijn veilig, maar Rik praat.",
            "Getuige beschrijft een tas die de kade verliet.",
            "Rik wijst een richting: de oude veerhaven.",
        ),
    }
    if not m and not d:
        result.update(
            mafiaDelta=SCORE["stalemate"], detectiveDelta=SCORE["stalemate"], heat=12,
            headline="Stilte aan de kade.", events=["Geen van beide teams durfde te bewegen."],
        )
        return result
    key = (m, d)
    if key in table:
        md, dd, heat, evidence, headline, mdef, ddef, event = table[key]
        result.update(
            mafiaDelta=md, detectiveDelta=dd, heat=heat, evidence=evidence,
            headline=headline, mafiaDebrief=mdef, detectiveDebrief=ddef, events=[event],
        )
        return result
    if m and not d:
        result.update(mafiaDelta=SCORE["mafia_contain"], heat=16, headline="De recherche kwam te laat.",
                      events=["Maffia handelt ongestoord."])
        return result
    if d and not m:
        result.update(
            detectiveDelta=SCORE["detective_lead"], heat=40, evidence="partial",
            headline="Niemand veegde. De kade praat.", events=["Recherche neemt de kade zonder tegenstand."],
        )
    return result
