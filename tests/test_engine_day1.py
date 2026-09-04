import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve()
_ENGINE = next(
    p
    for p in (
        _HERE.parents[1] / "server/app/games/schaduwstad/engine.py",
        _HERE.parents[1] / "app/games/schaduwstad/engine.py",
    )
    if p.exists()
)
_spec = importlib.util.spec_from_file_location("schaduwstad_engine", _ENGINE)
_engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_engine)
AP_PER_DAY = _engine.AP_PER_DAY
action_by_id = _engine.action_by_id
canonicalize = _engine.canonicalize
majority = _engine.majority
resolve_day = _engine.resolve_day


def test_aliases_and_ap_costs():
    assert canonicalize("wipe_trace") == "move_vehicle"
    assert canonicalize("investigate_location") == "tire_tracks"
    assert action_by_id("pressure_witness")["ap"] == 2
    assert action_by_id("container_records")["ap"] == 2
    assert AP_PER_DAY == 2
    assert majority(["camera_analysis", "camera_analysis", "witness"]) == "camera_analysis"


def test_vehicle_conflict_scores_match_v01_alias_pair():
    result = resolve_day("wipe_trace", "investigate_location")
    assert result["contested"] == ["vehicle_conflict"]
    assert result["mafiaDelta"] == 1
    assert result["detectiveDelta"] == 2
    assert result["evidenceScore"] > 0
    assert any(c["id"] == "vehicle_conflict" for c in result["cinematics"])
    assert "bandenspoor" in result["clues"] or "kenteken" in result["clues"]


def test_camera_conflict_and_clue_team_filter():
    result = resolve_day(
        "camera_sabotage",
        "camera_analysis",
        mafia_personal=["camera_sabotage"],
        detective_personal=["camera_analysis"],
    )
    assert "camera_conflict" in result["contested"]
    ids = [c["id"] for c in result["cinematics"]]
    assert "camera_conflict" in ids
    assert "kenteken" in result["clues"]
    clue_cues = [c for c in result["cinematics"] if c["kind"] == "clue"]
    assert clue_cues
    assert all(c["team"] == "detective" for c in clue_cues)


def test_ap_action_does_not_run_if_contested_consumed():
    result = resolve_day(
        None,
        None,
        mafia_personal=["camera_sabotage"],
        detective_personal=["camera_analysis", "tire_tracks"],
    )
    ids = [c["id"] for c in result["cinematics"]]
    assert "camera_conflict" in ids
    assert "tire_tracks" in ids
    assert "camera_analysis" not in ids
    assert "camera_sabotage" not in ids


def test_uncontested_detective_gets_verified_plate():
    result = resolve_day(None, "license_plate", detective_personal=["license_plate"])
    assert result["clues"]["kenteken"]["status"] in ("discovered", "verified")
    assert any(c["id"] == "clue_kenteken" and c["team"] == "detective" for c in result["cinematics"])
    mafia_only = [c for c in result["cinematics"] if c.get("team") == "mafia"]
    assert mafia_only == []


def test_heat_and_evidence_are_numeric_and_clamped():
    result = resolve_day(
        None,
        None,
        mafia_personal=["move_evidence", "false_alibi"],
        detective_personal=["container_records", "evidence_inspection"],
    )
    assert 0 <= result["heat"] <= 100
    assert 0 <= result["evidenceScore"] <= 100
    assert result["evidence"] in ("hidden", "partial", "verified")


def test_beat_deltas_are_per_event_and_team_tagged():
    result = resolve_day(
        "camera_sabotage",
        "camera_analysis",
        mafia_personal=["camera_sabotage"],
        detective_personal=["camera_analysis", "tire_tracks"],
    )
    contested = next(b for b in result["beats"] if b["id"] == "camera_conflict")
    assert contested["team"] is None
    assert contested["evidenceDelta"] == 6
    assert contested["heatDelta"] == 10
    private = next(b for b in result["beats"] if b["id"] == "tire_tracks")
    assert private["team"] == "detective"
    assert private["evidenceDelta"] == 9
    assert "kenteken" in result["clues"]
    assert result["clues"]["kenteken"].get("related") == ["bandenspoor"]


def test_build_impacts_sanitized_and_team_scoped():
    result = resolve_day(
        "camera_sabotage",
        "camera_analysis",
        mafia_personal=["camera_sabotage"],
        detective_personal=["camera_analysis", "tire_tracks"],
    )
    impacts = _engine.build_impacts(result)
    mafia = [i for i in impacts if i["team"] == "mafia"]
    det = [i for i in impacts if i["team"] == "detective"]
    assert mafia
    assert det
    mafia_blob = str(mafia).lower()
    det_blob = str(det).lower()
    assert "camera_analysis" not in mafia_blob
    assert "tire_tracks" not in mafia_blob
    assert "camera_sabotage" not in det_blob
    assert any("conflict" == i["kind"] for i in impacts)

