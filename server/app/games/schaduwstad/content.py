"""Data-driven day content. Future days add a spec + clips; the player stays."""

from __future__ import annotations

import hashlib

DAYS = {
    1: {
        "id": "havenkade-12",
        "day": 1,
        "title": "Havenkade 12",
        "caseId": "havenkade-12",
        "ap": 2,
        "roundSeconds": 600,
        "next": None,
    },
}

# Wire ids the Android registry must recognise even before that day is playable.
FUTURE_CINEMATICS = {
    "day2": [
        "d2_d01_container_inspection",
        "d2_d02_customs_records",
        "d2_d03_gps_tracker",
        "d2_d04_harbor_worker",
        "d2_d05_truck_route",
        "d2_d06_hidden_compartment",
        "d2_m01_move_container",
        "d2_m02_destroy_gps",
        "d2_m03_customs_bribe",
        "d2_m04_swap_truck",
        "d2_m05_fake_papers",
        "d2_m06_leave_bait_container",
        "d2_c01_container_intercepted",
        "d2_c02_gps_signal_lost",
        "d2_c03_simultaneous_arrival",
        "d2_c04_hidden_cargo_nearly_found",
        "d2_r01_fake_freight_bill",
        "d2_r02_gps_module",
        "d2_r03_customs_seal",
        "d2_r04_hidden_phone",
    ],
    "day3": [
        "d3_d01_anonymous_tip",
        "d3_d02_phone_metadata",
        "d3_d03_secret_meeting_observe",
        "d3_d04_money_flows",
        "d3_d05_meet_informant",
        "d3_d06_communication_patterns",
        "d3_m01_check_internal_phones",
        "d3_m02_observe_suspect_member",
        "d3_m03_spread_false_info",
        "d3_m04_loyalty_test",
        "d3_m05_replace_channel",
        "d3_m06_confront_possible_traitor",
        "d3_c01_secret_meeting_conflict",
        "d3_c02_false_tip_reaches_police",
        "d3_c03_informant_escapes",
        "d3_c04_internal_suspicion_explodes",
        "d3_r01_burner_phone",
        "d3_r02_unexplained_payment",
        "d3_r03_leaked_location",
        "d3_r04_coded_message",
    ],
    "day4": [
        "d4_d01_bank_transactions",
        "d4_d02_observe_office",
        "d4_d03_inspect_books",
        "d4_d04_follow_account",
        "d4_d05_follow_cash_transport",
        "d4_d06_reconstruct_structure",
        "d4_m01_move_cash",
        "d4_m02_destroy_books",
        "d4_m03_warn_strawman",
        "d4_m04_open_new_account",
        "d4_m05_change_cash_transport",
        "d4_m06_front_business",
        "d4_c01_cash_transport_intercepted",
        "d4_c02_empty_office_raid",
        "d4_c03_digital_transfer_blocked",
        "d4_c04_financial_trail_opens",
        "d4_r01_cash_ledger",
        "d4_r02_bank_transfer",
        "d4_r03_shell_company_document",
        "d4_r04_cash_bundle",
    ],
    "day5": [
        "d5_d01_position_observation",
        "d5_d02_prepare_arrest_team",
        "d5_d03_track_phone_locations",
        "d5_d04_finalize_evidence",
        "d5_d05_shadow_suspect",
        "d5_d06_prepare_raid",
        "d5_m01_leave_safehouse",
        "d5_m02_destroy_phones",
        "d5_m03_change_route",
        "d5_m04_destroy_evidence",
        "d5_m05_hide_person",
        "d5_m06_counter_surveillance",
        "d5_c01_chase",
        "d5_c02_failed_arrest",
        "d5_c03_safehouse_raid",
        "d5_c04_suspect_escapes",
    ],
    "global": [
        "global_g01_evidence_increased",
        "global_g02_evidence_destroyed",
        "global_g03_heat_increased",
        "global_g04_heat_decreased",
        "global_g05_new_anonymous_tip",
        "global_g06_witness_disappeared",
        "global_g07_witness_secured",
        "global_g08_police_surveillance",
        "global_g09_mafia_surveillance",
        "global_g10_unknown_vehicle",
        "global_g11_phone_signal_detected",
        "global_g12_phone_destroyed",
        "global_g13_police_raid",
        "global_g14_mafia_location_compromised",
        "global_g15_operation_successful",
        "global_g16_operation_partially_failed",
        "global_g17_critical_clue_discovered",
        "global_g18_false_lead_discovered",
        "global_g19_team_under_pressure",
        "global_g20_night_transition",
    ],
    "enemy-impact": [
        "enemy_ei01_cameras_offline",
        "enemy_ei02_witness_retracts",
        "enemy_ei03_witness_missing",
        "enemy_ei04_evidence_moved",
        "enemy_ei05_unexpected_new_trail",
        "enemy_ei06_mafia_notices_surveillance",
        "enemy_ei07_location_compromised",
        "enemy_ei08_vehicle_followed",
        "enemy_ei09_comms_leaked",
        "enemy_ei10_investigation_stalled",
    ],
}


def spec_for(day: int) -> dict:
    return dict(DAYS.get(int(day) or 1, DAYS[1]))


def known_cinematic_ids() -> set[str]:
    ids = {
        "camera_analysis",
        "evidence_inspection",
        "license_plate",
        "tire_tracks",
        "witness",
        "container_records",
        "move_vehicle",
        "camera_sabotage",
        "move_evidence",
        "warn_contact",
        "false_alibi",
        "pressure_witness",
        "camera_conflict",
        "conflict",
        "witness_conflict",
        "vehicle_conflict",
        "clue_kenteken",
        "clue_kasboek",
        "clue_bandenspoor",
        "clue_roetmap",
    }
    for group in FUTURE_CINEMATICS.values():
        ids.update(group)
    return ids


# Sanitized enemy-facing copy. Never includes the other team's action ids.
IMPACTS = {
    "camera_conflict": {
        "detective": {
            "title": "Vier seconden, dan sneeuw",
            "body": "Iemand doofde de kade. Jullie hielden een fragment. Evidence steeg. Heat ook.",
            "kind": "conflict",
            "cinematic": "enemy_ei01_cameras_offline",
        },
        "mafia": {
            "title": "De camera was niet dood genoeg",
            "body": "Recherche sleepte beeld terug. Iets van de kade leeft nog.",
            "kind": "conflict",
            "cinematic": "enemy_ei05_unexpected_new_trail",
        },
    },
    "witness_conflict": {
        "detective": {
            "title": "Rik praat met twee monden",
            "body": "De getuige sluit af. Iemand was hem voor. Heat stijgt hard.",
            "kind": "conflict",
            "cinematic": "enemy_ei02_witness_retracts",
        },
        "mafia": {
            "title": "Rik houdt de namen binnen",
            "body": "Hij zwijgt over jullie. Maar hij is onbetrouwbaar geworden.",
            "kind": "conflict",
            "cinematic": "enemy_ei03_witness_missing",
        },
    },
    "vehicle_conflict": {
        "detective": {
            "title": "De bus is weg. De groeven niet",
            "body": "Verse sporen, halve plaat, lege parkeerplaats. Iemand verplaatste het voertuig.",
            "kind": "conflict",
            "cinematic": "enemy_ei08_vehicle_followed",
        },
        "mafia": {
            "title": "Het voertuig is veilig. De kade niet schoon",
            "body": "Bandensporen bleven achter. Recherche las de groeven.",
            "kind": "conflict",
            "cinematic": "enemy_ei05_unexpected_new_trail",
        },
    },
    "conflict": {
        "detective": {
            "title": "De stukken waren er. Nu half",
            "body": "Iemand tilde de map op voor jullie. As en papier. Evidence blijft fragmentarisch.",
            "kind": "conflict",
            "cinematic": "enemy_ei04_evidence_moved",
        },
        "mafia": {
            "title": "De kern is weg. Ze houden as over",
            "body": "Recherche vond restanten. Niet de kern. Nog niet.",
            "kind": "conflict",
            "cinematic": "enemy_ei05_unexpected_new_trail",
        },
    },
    "camera_analysis": {
        "mafia": {
            "title": "Iemand las de kadebeelden",
            "body": "Cameradata beweegt. Jullie zijn niet onzichtbaar.",
            "kind": "pressure",
            "cinematic": "enemy_ei06_mafia_notices_surveillance",
        },
    },
    "evidence_inspection": {
        "mafia": {
            "title": "Iemand zat in de as",
            "body": "Papier en roet gaan het dossier in. Administratie is niet veilig.",
            "kind": "pressure",
            "cinematic": "enemy_ei05_unexpected_new_trail",
        },
    },
    "license_plate": {
        "mafia": {
            "title": "De plaat leeft",
            "body": "Iemand trekt letters na. Het kenteken is niet meer van jullie alleen.",
            "kind": "pressure",
            "cinematic": "enemy_ei06_mafia_notices_surveillance",
        },
    },
    "tire_tracks": {
        "mafia": {
            "title": "Iemand las de groeven",
            "body": "De klinkers houden sporen. Jullie wagen is niet onzichtbaar.",
            "kind": "pressure",
            "cinematic": "enemy_ei08_vehicle_followed",
        },
    },
    "witness": {
        "mafia": {
            "title": "Rik praat",
            "body": "De getuige beschrijft mannen en een wagen. Houd hem in de gaten.",
            "kind": "pressure",
            "cinematic": "enemy_ei06_mafia_notices_surveillance",
        },
    },
    "container_records": {
        "mafia": {
            "title": "De loods staat op papier",
            "body": "Iemand koppelt de boeking. Van Dorp is een naam te veel.",
            "kind": "pressure",
            "cinematic": "enemy_ei07_location_compromised",
        },
    },
    "move_vehicle": {
        "detective": {
            "title": "De kade is leeg",
            "body": "Het voertuig is weg voor jullie er waren. Sporen misschien niet.",
            "kind": "pressure",
            "cinematic": "enemy_ei08_vehicle_followed",
        },
    },
    "camera_sabotage": {
        "detective": {
            "title": "De kade valt blind",
            "body": "Cameradata sterft midden in het beeld. Iemand was jullie voor.",
            "kind": "pressure",
            "cinematic": "enemy_ei01_cameras_offline",
        },
    },
    "move_evidence": {
        "detective": {
            "title": "De stukken zijn lichter",
            "body": "Iets ontbreekt in de as. De map is aangerand.",
            "kind": "pressure",
            "cinematic": "enemy_ei04_evidence_moved",
        },
    },
    "warn_contact": {
        "detective": {
            "title": "Een mond gaat dicht",
            "body": "Aan de veerhaven wordt gezwegen. Iemand is gewaarschuwd.",
            "kind": "pressure",
            "cinematic": "enemy_ei09_comms_leaked",
        },
    },
    "false_alibi": {
        "detective": {
            "title": "De alibi's staan te strak",
            "body": "Iedereen was ergens anders. Natuurlijk. Heat daalt niet vanzelf.",
            "kind": "pressure",
            "cinematic": "enemy_ei10_investigation_stalled",
        },
    },
    "pressure_witness": {
        "detective": {
            "title": "Rik trekt zich terug",
            "body": "De getuige sluit af. Iemand zette hem onder druk.",
            "kind": "pressure",
            "cinematic": "enemy_ei02_witness_retracts",
        },
    },
}

FOLLOWUPS = {
    "camera_conflict": {
        "detective": {
            "id": "check_worker",
            "label": "Medewerker controleren",
            "hint": "De storing is gemeld. Iemand op de kade zag het.",
            "effect": "Een havenmedewerker bevestigt de storing. Evidence +2.",
            "ev": 2,
            "ht": 1,
        },
        "mafia": {
            "id": "wipe_rest",
            "label": "Restbeeld wissen",
            "hint": "Vier seconden is nog te veel.",
            "effect": "De laatste fragmenten verdwijnen. Evidence -2.",
            "ev": -2,
            "ht": -1,
        },
    },
    "witness_conflict": {
        "detective": {
            "id": "secure_rik",
            "label": "Rik in veiligheid",
            "hint": "Haal hem van de kade.",
            "effect": "Rik is uit de wind. Heat -2.",
            "ev": 1,
            "ht": -2,
        },
        "mafia": {
            "id": "silence_rik",
            "label": "Rik laten verdwijnen",
            "hint": "Hij mag niet nog een keer praten.",
            "effect": "Rik is onvindbaar. Heat +2.",
            "ev": -1,
            "ht": 2,
        },
    },
    "vehicle_conflict": {
        "detective": {
            "id": "cast_tracks",
            "label": "Sporen gieten",
            "hint": "De groeven wachten niet op de zon.",
            "effect": "Een gipsafdruk gaat het dossier in. Evidence +2.",
            "ev": 2,
            "ht": 0,
        },
        "mafia": {
            "id": "wash_quay",
            "label": "Kade naspoelen",
            "hint": "Regen alleen is niet genoeg.",
            "effect": "De groeven vervagen. Evidence -2.",
            "ev": -2,
            "ht": -1,
        },
    },
    "conflict": {
        "detective": {
            "id": "bag_ash",
            "label": "As veiligstellen",
            "hint": "Wat overbleef mag niet wegwaaien.",
            "effect": "Restanten in het lab. Evidence +2.",
            "ev": 2,
            "ht": 0,
        },
        "mafia": {
            "id": "second_pass",
            "label": "Tweede ronde in de as",
            "hint": "Ze houden papier over.",
            "effect": "Nog een map is weg. Evidence -2.",
            "ev": -2,
            "ht": 0,
        },
    },
    "camera_sabotage": {
        "detective": {
            "id": "check_worker",
            "label": "Medewerker controleren",
            "hint": "Iemand meldde de storing.",
            "effect": "De melding staat. Evidence +2.",
            "ev": 2,
            "ht": 1,
        },
    },
    "move_evidence": {
        "detective": {
            "id": "bag_ash",
            "label": "As veiligstellen",
            "hint": "Wat overbleef mag niet wegwaaien.",
            "effect": "Restanten in het lab. Evidence +1.",
            "ev": 1,
            "ht": 0,
        },
    },
    "camera_analysis": {
        "mafia": {
            "id": "wipe_rest",
            "label": "Restbeeld wissen",
            "hint": "Iemand las de kade.",
            "effect": "De server is leeg. Evidence -2.",
            "ev": -2,
            "ht": -1,
        },
    },
    "license_plate": {
        "mafia": {
            "id": "swap_plate",
            "label": "Plaat wisselen",
            "hint": "SCH-** mag niet blijven hangen.",
            "effect": "De plaat is niet meer van jullie wagen. Evidence -1.",
            "ev": -1,
            "ht": 1,
        },
    },
    "tire_tracks": {
        "mafia": {
            "id": "wash_quay",
            "label": "Kade naspoelen",
            "hint": "De groeven liggen nog open.",
            "effect": "De klinkers zijn nat en leeg. Evidence -2.",
            "ev": -2,
            "ht": -1,
        },
    },
}


def follow_up_for(beat_id: str | None, team: str | None) -> dict | None:
    if not beat_id or not team:
        return None
    payload = (FOLLOWUPS.get(beat_id) or {}).get(team)
    if not payload:
        return None
    return dict(payload)


def impact_id(team: str, source: str, day: int = 1) -> str:
    digest = hashlib.sha256(f"{team}:{source}:d{int(day) or 1}".encode()).hexdigest()[:12]
    return f"imp-{digest}"


def build_impacts(result: dict, day: int = 1) -> list[dict]:
    """Team-scoped, sanitized pressure. Stable ids so ack survives reconnect."""
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(source: str, team: str) -> None:
        payload = (IMPACTS.get(source) or {}).get(team)
        if not payload or not source:
            return
        key = (team, source)
        if key in seen:
            return
        seen.add(key)
        item = {
            "id": impact_id(team, source, day),
            "team": team,
            "title": payload["title"],
            "body": payload["body"],
            "kind": payload.get("kind") or "pressure",
        }
        if payload.get("cinematic"):
            item["cinematic"] = payload["cinematic"]
        out.append(item)

    for cid in result.get("contested") or []:
        add(cid, "mafia")
        add(cid, "detective")
    for beat in result.get("beats") or []:
        owner = beat.get("team")
        if not owner:
            continue
        enemy = "mafia" if owner == "detective" else "detective"
        add(beat.get("id") or "", enemy)
    return out
