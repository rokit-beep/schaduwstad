from tests.conftest import auth


def _ready_two(client):
    host = client.post("/games/schaduwstad/api/lobbies", json={"player_name": "Don"}).json()
    ghost = client.post(
        f"/games/schaduwstad/api/lobbies/{host['lobbyCode']}/join",
        json={"player_name": "Inspecteur"},
    ).json()
    code = host["lobbyCode"]
    ht, gt = host["session_token"], ghost["session_token"]
    client.post(f"/games/schaduwstad/api/lobbies/{code}/team", json={"team": "mafia"}, headers=auth(ht))
    client.post(f"/games/schaduwstad/api/lobbies/{code}/team", json={"team": "detective"}, headers=auth(gt))
    client.post(f"/games/schaduwstad/api/lobbies/{code}/ready", json={"ready": True}, headers=auth(ht))
    client.post(f"/games/schaduwstad/api/lobbies/{code}/ready", json={"ready": True}, headers=auth(gt))
    client.post(f"/games/schaduwstad/api/lobbies/{code}/start", headers=auth(ht))
    return code, ht, gt


def test_websocket_team_chat_never_crosses(client):
    code, ht, gt = _ready_two(client)
    with client.websocket_connect(f"/games/schaduwstad/ws/{code}?token={ht}") as mafia_ws:
        with client.websocket_connect(f"/games/schaduwstad/ws/{code}?token={gt}") as det_ws:
            mafia_ws.receive_json()
            det_ws.receive_json()
            mafia_ws.send_json({"type": "chat", "body": "kenteken SCH-14-X"})
            mafia_push = mafia_ws.receive_json()
            det_push = det_ws.receive_json()
            assert mafia_push["type"] == "state"
            assert any("SCH-14-X" in m["body"] for m in mafia_push["view"]["chat"])
            assert det_push["view"]["chat"] == []
            assert "sch-14-x" not in str(det_push).lower()
