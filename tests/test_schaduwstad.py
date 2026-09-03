from tests.conftest import auth


def _create(client, name="Raven"):
    response = client.post("/games/schaduwstad/api/lobbies", json={"player_name": name})
    assert response.status_code == 200, response.text
    data = response.json()
    return data["lobbyCode"], data["session_token"], data


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
    code, host_token, _ = _create(client, "Don")
    ghost = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/join", json={"player_name": "Inspecteur"}
    ).json()
    ghost_token = ghost["session_token"]
    assert (
        client.post(
            f"/games/schaduwstad/api/lobbies/{code}/team",
            json={"team": "mafia"},
            headers=auth(host_token),
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/games/schaduwstad/api/lobbies/{code}/team",
            json={"team": "detective"},
            headers=auth(ghost_token),
        ).status_code
        == 200
    )
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/ready",
        json={"ready": True},
        headers=auth(host_token),
    )
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/ready",
        json={"ready": True},
        headers=auth(ghost_token),
    )
    started = client.post(f"/games/schaduwstad/api/lobbies/{code}/start", headers=auth(host_token))
    assert started.status_code == 200
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
    assert "SCH-14-X" not in detective_state["briefing"]
    assert "Van Dorp" in mafia_state["briefing"]
    serialized = str(detective_state).lower()
    assert "sch-14-x" not in serialized
    assert "kasboek" not in serialized


def test_day1_score_is_server_side(client):
    code, host_token, _ = _create(client, "Don")
    ghost_token = client.post(
        f"/games/schaduwstad/api/lobbies/{code}/join", json={"player_name": "Inspecteur"}
    ).json()["session_token"]
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/team",
        json={"team": "mafia"},
        headers=auth(host_token),
    )
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/team",
        json={"team": "detective"},
        headers=auth(ghost_token),
    )
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/ready",
        json={"ready": True},
        headers=auth(host_token),
    )
    client.post(
        f"/games/schaduwstad/api/lobbies/{code}/ready",
        json={"ready": True},
        headers=auth(ghost_token),
    )
    client.post(f"/games/schaduwstad/api/lobbies/{code}/start", headers=auth(host_token))
    client.post(f"/games/schaduwstad/api/lobbies/{code}/actions/advance", headers=auth(host_token))
    client.post(f"/games/schaduwstad/api/lobbies/{code}/actions/advance", headers=auth(host_token))
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
