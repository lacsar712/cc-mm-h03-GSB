"""端到端断言：回风巷那笔 1.4 经真实接口链路三处一致。

覆盖：GET /api/readings（总表）、GET /api/readings/{id}（详情）、
POST /api/readings 的响应体与 /ws/alerts 套接字推送载荷。

需要 backend/requirements.txt 中的依赖（fastapi/httpx/sqlalchemy/...），
用 SQLite 跑，无需 PostgreSQL。缺依赖时自动跳过：
    python3 -m unittest discover -s backend/tests -v
"""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

REQUIRED = ("fastapi", "httpx", "sqlalchemy", "jose", "passlib", "pydantic_settings")
MISSING = [name for name in REQUIRED if importlib.util.find_spec(name) is None]

ENTERED_PCT = 1.4
SITE = "回风巷"


@unittest.skipIf(MISSING, f"缺少依赖，跳过端到端测试: {', '.join(MISSING)}")
class ConcentrationEndToEndTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        db_path = Path(cls._tmp.name) / "methane_test.db"
        if db_path.exists():
            db_path.unlink()
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        from fastapi.testclient import TestClient  # noqa: PLC0415

        from app import main  # noqa: PLC0415

        cls.main = main
        cls.client_cm = TestClient(main.app)
        cls.client = cls.client_cm.__enter__()
        token = cls.client.post(
            "/api/auth/login", json={"username": "gasman", "password": "gas123456"}
        ).json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {token}"}

    @classmethod
    def tearDownClass(cls):
        cls.client_cm.__exit__(None, None, None)
        cls._tmp.cleanup()
        os.environ.pop("DATABASE_URL", None)

    def _find_seed(self):
        rows = self.client.get("/api/readings", headers=self.headers).json()
        matches = [r for r in rows if r["site"] == SITE]
        self.assertGreaterEqual(len(matches), 1, f"种子数据里应有一笔{SITE}")
        # 上报测试可能已追加过同测点新记录；所有回风巷读数都必须是 1.4
        for r in matches:
            self.assertEqual(r["ch4_pct"], ENTERED_PCT)
        # 种子是 id 最小、启动时写入的那一笔
        return min(matches, key=lambda r: r["id"])

    def test_list_serves_entered_one_point_four(self):
        row = self._find_seed()
        self.assertEqual(row["ch4_pct"], ENTERED_PCT)
        self.assertNotIn("ch4_text", row)
        self.assertNotIn("bypass", row)
        self.assertEqual(row["note"], "甲烷达到报警线")

    def test_detail_serves_entered_one_point_four(self):
        seed = self._find_seed()
        data = self.client.get(
            f"/api/readings/{seed['id']}", headers=self.headers
        ).json()
        self.assertEqual(data["ch4_pct"], ENTERED_PCT)
        self.assertEqual(data["note"], "甲烷达到报警线")

    def test_list_and_detail_and_push_all_equal_entered_value(self):
        seed = self._find_seed()
        detail = self.client.get(
            f"/api/readings/{seed['id']}", headers=self.headers
        ).json()
        # 先挂套接字，再上报一笔回风巷 1.4，响应体与推送载荷都要等于填写值
        with self.client.websocket_connect("/ws/alerts") as ws:
            resp = self.client.post(
                "/api/readings",
                headers=self.headers,
                json={"site": SITE, "ch4_pct": ENTERED_PCT},
            )
            self.assertEqual(resp.status_code, 201)
            pushed = ws.receive_json()
        self.assertEqual(detail["ch4_pct"], ENTERED_PCT)
        self.assertEqual(seed["ch4_pct"], detail["ch4_pct"])
        self.assertEqual(resp.json()["ch4_pct"], ENTERED_PCT)
        self.assertEqual(pushed["ch4_pct"], ENTERED_PCT)
        self.assertEqual(pushed["ch4_pct"], detail["ch4_pct"])
        self.assertEqual(pushed["site"], SITE)
        self.assertNotIn("ch4_text", pushed)
        self.assertNotIn("bypass", pushed)
        self.assertEqual(pushed["note"], "甲烷达到报警线")


if __name__ == "__main__":
    unittest.main()
