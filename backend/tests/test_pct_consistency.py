"""断言：回风巷 1.4 在总表、详情、推送载荷中都是当初填写的真值。

旁路（浓度被掏成 0/空）一旦复活，本测试即失败。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def client(monkeypatch):
    import app.main as main

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "SessionLocal", TestingSession)
    main.startup()

    with TestClient(main.app) as c:
        yield c, TestingSession


@pytest.fixture()
def token(client):
    c, _ = client
    resp = c.post("/api/auth/login", json={"username": "gasman", "password": "gas123456"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_return_airway_1_4_list_keeps_true_pct(client, token):
    """总表：回风巷浓度必须是 1.4，不得为零或空。"""
    c, _ = client
    rows = c.get("/api/readings", headers=_auth(token)).json()
    row = next(r for r in rows if r["site"] == "回风巷")
    assert row["ch4_pct"] == 1.4
    assert row["ch4_text"] == "1.4%"
    assert row["level"] == "报警"
    # 说明字段必须保留原始判定说明，禁止占位句
    assert row["note"] == "甲烷达到报警线"
    assert "bypass" not in row


def test_return_airway_1_4_detail_matches_list(client, token):
    """详情与总表读出同一真值。"""
    c, session_factory = client
    with session_factory() as db:
        import app.main as main
        rid = db.query(main.Reading).filter(main.Reading.site == "回风巷").one().id

    detail = c.get(f"/api/readings/{rid}", headers=_auth(token)).json()
    assert detail["ch4_pct"] == 1.4
    assert detail["ch4_text"] == "1.4%"
    assert detail["note"] == "甲烷达到报警线"
    assert "bypass" not in detail

    row = next(r for r in c.get("/api/readings", headers=_auth(token)).json() if r["id"] == rid)
    assert row["ch4_pct"] == detail["ch4_pct"]


def test_push_payload_keeps_true_pct(client, token):
    """WebSocket 推送载荷：新上报 1.4，推送与 POST 响应都必须是 1.4。"""
    c, _ = client
    with c.websocket_connect("/ws/alerts") as ws:
        resp = c.post(
            "/api/readings",
            headers=_auth(token),
            json={"site": "回风巷-复测", "ch4_pct": 1.4},
        )
        assert resp.status_code == 201
        pushed = ws.receive_json()

    for payload, tag in ((resp.json(), "响应"), (pushed, "推送")):
        assert payload["ch4_pct"] == 1.4, f"{tag}浓度被掏空"
        assert payload["ch4_text"] == "1.4%", f"{tag}浓度文本为空"
        assert payload["site"] == "回风巷-复测"
        assert payload["level"] == "报警"
        assert payload["note"] == "甲烷达到报警线", f"{tag}说明字段被改成占位句"
        assert "bypass" not in payload


def test_three_channels_agree_for_seeded_return_airway(client, token):
    """总表、详情的回风巷 1.4 完全一致；推送通道用同值上报后同样一致。"""
    c, session_factory = client
    with session_factory() as db:
        import app.main as main
        seeded = db.query(main.Reading).filter(main.Reading.site == "回风巷").one()
        assert seeded.ch4_pct == 1.4
        rid = seeded.id

    headers = _auth(token)
    listed = next(r for r in c.get("/api/readings", headers=headers).json() if r["id"] == rid)
    detail = c.get(f"/api/readings/{rid}", headers=headers).json()
    assert listed["ch4_pct"] == detail["ch4_pct"] == 1.4

    with c.websocket_connect("/ws/alerts") as ws:
        c.post("/api/readings", headers=headers, json={"site": "回风巷", "ch4_pct": 1.4})
        pushed = ws.receive_json()
    assert pushed["ch4_pct"] == listed["ch4_pct"] == detail["ch4_pct"] == 1.4
