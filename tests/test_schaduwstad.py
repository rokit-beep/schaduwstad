from tests.conftest import auth


def _create(client, name="Raven"):
    response = client.post("/games/schaduwstad/api/lobbies", json={"player_name": name})
    assert response.status_code == 200, response.text
    data = response.json()
    return data["lobbyCode"], data["session_token"], data


def _two_ready(client):
    code, host_token, _ = _create(client, "Don")
    ghost_token = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/join", json={"player_name": "Inspecteur"}
    ).json()["session_token"]
    client.post(f"/games/schaduwstad/api/lobbies/{code}/team", json={"team": "mafia"}, headers=auth(host_token))
    client.post(f"/games/schaduwstad/api/lobbies/{code}/team", json={"team": "detective"}, headers=auth(ghost_token))
    client.post(f"/games/schaduwstad/api/lobbies/{code}/ready", json={"ready": True}, headers=auth(host_token))
    client.post(f"/games/schaduwstad/api/lobbies/{code}/ready", json={"ready": True}, headers=auth(ghost_token))
    started = client.post(f"/games/schaduwstad/api/lobbies/{code}/start", headers=auth(host_token))
    assert started.status_code == 200
    assert started.json()["phase"] == "play"
    return code, host_token, ghost_token


def test_schaduwstad_registers_next_to_crime(client):
    games = client.get("/platform/games").json()["games"]
    ids = [g["id"] for g in games]
    assert ids[0] == "crime"
    assert "schaduwstad" in ids
    assert client.get("/health").json()["service"] == "nightforge-game-server"


def test_crime_routes_still_present(client):
    paths = set(client.get("/openapi.json").json()["paths"])
    assert "/api/lobbies" in paths
    assert "/games/schaduwstad/api/lobbies" in paths


def test_lobby_create_join_and_team_cap(client):
    code, host_token, _ = _create(client, "Host")
    joined = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/join", json={"player_name": "Ghost"}
    )
    assert joined.status_code == 200
    host_mafia = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/team",
        json={"team": "mafia"},
        headers=auth(host_token),
    )
    assert host_mafia.status_code == 200
    ghost_token = joined.json()["session_token"]
    for i in range(5):
        extra = client.post(
            f"/games/schaduwstad/api/lobbies/{code}/join", json={"player_name": f"M{i}"}
        )
        assert extra.status_code == 200
        token = extra.json()["session_token"]
        taken = client.post(
            f"/games/schaduwstad/api/lobbies/{code}/team",
            json={"team": "mafia"},
            headers=auth(token),
        )
        assert taken.status_code == 200
    overflow = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/team",
        json={"team": "mafia"},
        headers=auth(ghost_token),
    )
    assert overflow.status_code == 409


def test_team_chat_and_secret_isolation(client):
    code, host_token, ghost_token = _two_ready(client)
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/chat",
        json={"body": "kenteken SCH-14-X in de bus"},
        headers=auth(host_token),
    )
    mafia_state = client.get(
        f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(host_token)
    ).json()
    detective_state = client.get(
        f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(ghost_token)
    ).json()
    assert any("SCH-14-X" in m["body"] for m in mafia_state["chat"])
    assert detective_state["chat"] == []
    assert "SCH-14-X" not in (detective_state["briefing"] or "")
    assert "Van Dorp" in mafia_state["briefing"]
    assert "kasboek" not in (detective_state["briefing"] or "").lower()
    assert "sch-14-x" not in (detective_state["briefing"] or "").lower()
    # unknown slots in the zaakdossier are not a leak of mafia briefing
    assert all(m["team"] != "mafia" for m in detective_state["chat"])


def test_parallel_actions_neither_team_waits(client):
    code, host_token, ghost_token = _two_ready(client)
    mafia = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(host_token)).json()
    detective = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(ghost_token)).json()
    assert mafia["phase"] == detective["phase"] == "play"
    assert mafia["you"]["ap"] == 2
    assert detective["you"]["ap"] == 2
    assert mafia["availableActions"]
    assert detective["availableActions"]
    mafia_ids = {a["id"] for a in mafia["availableActions"]}
    det_ids = {a["id"] for a in detective["availableActions"]}
    assert "camera_sabotage" in mafia_ids
    assert "camera_analysis" in det_ids
    assert "camera_analysis" not in mafia_ids
    spent_m = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "camera_sabotage"},
        headers=auth(host_token),
    ).json()
    spent_d = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "camera_analysis"},
        headers=auth(ghost_token),
    ).json()
    assert spent_m["you"]["ap"] == 1
    assert spent_d["you"]["ap"] == 1
    assert spent_m["phase"] == "play"
    assert spent_d["phase"] == "play"
    vote_m = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/vote",
        json={"action": "move_vehicle"},
        headers=auth(host_token),
    )
    vote_d = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/vote",
        json={"action": "tire_tracks"},
        headers=auth(ghost_token),
    )
    assert vote_m.status_code == 200
    assert vote_d.status_code == 200
    mafia_feed = [e["label"] for e in spent_m["feed"]]
    det_after = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(ghost_token)).json()
    assert any("Camera" in (e.get("label") or "") for e in spent_m["feed"])
    assert not any("Camera sabot" in (e.get("label") or "") for e in det_after["feed"])
    assert "camera_sabotage" not in str(det_after["feed"]).lower()


def test_day1_score_is_server_side(client):
    code, host_token, ghost_token = _two_ready(client)
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/vote",
        json={"action": "wipe_trace"},
        headers=auth(host_token),
    )
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/vote",
        json={"action": "investigate_location"},
        headers=auth(ghost_token),
    )
    result = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/advance", headers=auth(host_token)
    ).json()
    assert result["phase"] == "result"
    assert result["scores"]["detective"] == 2
    assert result["scores"]["mafia"] == 1
    eval_state = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/advance", headers=auth(host_token)
    ).json()
    assert eval_state["phase"] == "eval"
    assert eval_state["result"]["headline"]


def test_personal_ap_and_cinematic_isolation(client):
    code, host_token, ghost_token = _two_ready(client)
    mafia = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(host_token)).json()
    assert mafia["phase"] == "play"
    assert mafia["you"]["ap"] == 2
    spent = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "camera_sabotage"},
        headers=auth(host_token),
    ).json()
    assert spent["you"]["ap"] == 1
    over = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "pressure_witness"},
        headers=auth(host_token),
    )
    assert over.status_code == 409
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "camera_analysis"},
        headers=auth(ghost_token),
    )
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "tire_tracks"},
        headers=auth(ghost_token),
    )
    client.post(f"/games/schaduwstad/api/lobbies/{code}/actions/advance", headers=auth(host_token))
    mafia_view = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(host_token)).json()
    det_view = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(ghost_token)).json()
    assert mafia_view["phase"] == "result"
    mafia_ids = [c["id"] for c in mafia_view["result"]["cinematics"]]
    det_ids = [c["id"] for c in det_view["result"]["cinematics"]]
    assert "camera_conflict" in mafia_ids
    assert "camera_conflict" in det_ids
    assert not any(i.startswith("clue_") for i in mafia_ids)
    assert "tire_tracks" not in mafia_ids
    assert "tire_tracks" in det_ids
    assert det_view["clues"]
    assert mafia_view["clues"] == []
    assert mafia_view["opsDossier"] is not None
    assert det_view["opsDossier"] is None
    mafia_beats = str(mafia_view["result"]["beats"]).lower()
    assert "bandensporen" not in mafia_beats
    assert "tire_tracks" not in mafia_beats
    det_beat_ids = [b.get("id") for b in det_view["result"]["beats"]]
    assert "tire_tracks" in det_beat_ids
    assert "camera_conflict" in det_beat_ids
    mafia_beat_ids = [b.get("id") for b in mafia_view["result"]["beats"]]
    assert "camera_conflict" in mafia_beat_ids
    assert "tire_tracks" not in mafia_beat_ids


def test_enemy_impact_live_ack_and_offline_return(client):
    code, host_token, ghost_token = _two_ready(client)
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "camera_sabotage"},
        headers=auth(host_token),
    )
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "camera_analysis"},
        headers=auth(ghost_token),
    )
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "tire_tracks"},
        headers=auth(ghost_token),
    )
    client.post(f"/games/schaduwstad/api/lobbies/{code}/actions/advance", headers=auth(host_token))
    mafia = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(host_token)).json()
    det = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(ghost_token)).json()
    assert mafia["unseenImpacts"]
    assert det["unseenImpacts"]
    mafia_blob = str(mafia["unseenImpacts"]).lower() + str(mafia["impacts"]).lower()
    det_blob = str(det["unseenImpacts"]).lower() + str(det["impacts"]).lower()
    assert "camera_sabotage" not in det_blob
    assert "tire_tracks" not in mafia_blob
    assert "camera_analysis" not in mafia_blob
    mafia_text = " ".join(f"{i.get('title','')} {i.get('body','')}" for i in mafia["unseenImpacts"]).lower()
    assert "groeven" in mafia_text or "camera" in mafia_text or "kade" in mafia_text
    assert mafia["unseenCinematics"]
    assert det["unseenCinematics"]
    # ack as if the mafia client watched, then "app restart"
    mafia_cin = [c["id"] for c in mafia["unseenCinematics"]]
    mafia_imp = [i["id"] for i in mafia["unseenImpacts"]]
    acked = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/ack",
        json={"cinematics": mafia_cin, "impacts": mafia_imp},
        headers=auth(host_token),
    ).json()
    assert acked["unseenImpacts"] == []
    assert acked["unseenCinematics"] == []
    again = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(host_token)).json()
    assert again["unseenImpacts"] == []
    assert again["unseenCinematics"] == []
    assert again["impacts"]
    # detective never acked — offline return still has unseen
    offline = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(ghost_token)).json()
    assert offline["unseenImpacts"]
    assert offline["unseenCinematics"]
    # evidence / heat only after resolve
    assert 0 < det["evidenceScore"] <= 100
    assert 0 < det["heat"] <= 100
    blob = str(mafia) + str(det)
    assert "source" not in str(mafia["impacts"]).lower() or '"source"' not in json_impacts(mafia)
    assert all("source" not in i for i in mafia["impacts"])
    assert all("source" not in i for i in det["impacts"])


def json_impacts(view):
    return str(view.get("impacts"))


def test_no_live_meters_or_enemy_roster_during_play(client):
    code, host_token, ghost_token = _two_ready(client)
    mafia = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(host_token)).json()
    assert mafia["you"]["ready"] is False
    assert mafia["heat"] == 0
    assert mafia["evidenceScore"] == 0
    assert mafia["opponentStatus"] == "RONDE ACTIEF"
    assert mafia["teamReady"]["ready"] == 0
    assert mafia["teamReady"]["total"] == 1
    assert all(p["team"] == "mafia" for p in mafia["players"])
    det_act = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "camera_analysis"},
        headers=auth(ghost_token),
    ).json()
    assert det_act["phase"] == "play"
    mafia_after = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(host_token)).json()
    assert mafia_after["phase"] == "play"
    assert mafia_after["heat"] == 0
    assert mafia_after["evidenceScore"] == 0
    assert mafia_after["unseenImpacts"] == []
    assert "camera_analysis" not in str(mafia_after).lower()
    assert all(p["team"] == "mafia" for p in mafia_after["players"])


def test_round_ready_auto_resolves_without_waiting_on_host_button(client):
    code, host_token, ghost_token = _two_ready(client)
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "camera_sabotage"},
        headers=auth(host_token),
    )
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "camera_analysis"},
        headers=auth(ghost_token),
    )
    first = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/ready",
        json={"ready": True},
        headers=auth(host_token),
    ).json()
    assert first["phase"] == "play"
    assert first["you"]["ready"] is True
    locked = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "move_vehicle"},
        headers=auth(host_token),
    )
    assert locked.status_code == 409
    resolved = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/ready",
        json={"ready": True},
        headers=auth(ghost_token),
    ).json()
    assert resolved["phase"] == "result"
    mafia = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(host_token)).json()
    det = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(ghost_token)).json()
    assert mafia["phase"] == det["phase"] == "result"
    assert mafia["result"]["mafiaAction"] is None
    assert mafia["result"]["detectiveAction"] is None
    assert det["result"]["mafiaAction"] is None
    assert mafia["developments"]
    assert det["developments"]
    assert all(d.get("team") != "detective" for d in mafia["developments"])


def test_followup_once_and_eval_hides_enemy_actions(client):
    code, host_token, ghost_token = _two_ready(client)
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "camera_sabotage"},
        headers=auth(host_token),
    )
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/personal",
        json={"action": "camera_analysis"},
        headers=auth(ghost_token),
    )
    client.post(f"/games/schaduwstad/api/lobbies/{code}/actions/advance", headers=auth(host_token))
    det = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(ghost_token)).json()
    assert det["clues"]
    assert any(c["status"] == "unknown" for c in det["clues"]) or any(
        c["status"] in ("discovered", "disputed", "verified") for c in det["clues"]
    )
    follow_ups = det["result"]["followUps"]
    assert follow_ups
    choice = follow_ups[0]["id"]
    ok = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/followup",
        json={"action": choice},
        headers=auth(ghost_token),
    )
    assert ok.status_code == 200
    again = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/followup",
        json={"action": choice},
        headers=auth(ghost_token),
    )
    assert again.status_code == 409
    eval_state = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/actions/advance", headers=auth(host_token)
    ).json()
    assert eval_state["phase"] == "eval"
    assert eval_state["result"]["mafiaAction"] is None
    assert eval_state["result"]["detectiveAction"] is None
    assert "camera_analysis" not in str(eval_state["result"].get("mafiaPersonal"))
    mafia = client.get(f"/games/schaduwstad/api/lobbies/{code}/state", headers=auth(host_token)).json()
    assert mafia["opsDossier"]
    assert "locations" in mafia["opsDossier"]

