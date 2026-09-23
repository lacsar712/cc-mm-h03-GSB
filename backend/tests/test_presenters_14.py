"""呈现层断言：回风巷那笔 1.4 在总表、详情、推送载荷三处必须都是 1.4。

只依赖标准库，任何环境都能跑：
    python3 -m unittest discover -s backend/tests -v
"""

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.presenters import present_detail, present_list_row, present_push_payload  # noqa: E402
from app.rules import classify  # noqa: E402

REPO = BACKEND.parent
ENTERED_PCT = 1.4
SITE = "回风巷"
LEVEL, REAL_NOTE = classify(ENTERED_PCT)  # 报警 / 甲烷达到报警线


class FakeRow:
    def __init__(self, id, site, ch4_pct, level, note, created_by):
        self.id = id
        self.site = site
        self.ch4_pct = ch4_pct
        self.level = level
        self.note = note
        self.created_by = created_by


class HuifengLaneOnePointFourTest(unittest.TestCase):
    def setUp(self):
        # 模拟当初填写并落库的那笔回风巷 1.4
        self.row = FakeRow(1, SITE, ENTERED_PCT, LEVEL, REAL_NOTE, "gasman")

    def test_list_row_keeps_entered_pct(self):
        out = present_list_row(self.row)
        self.assertEqual(out["ch4_pct"], ENTERED_PCT)
        self.assertIsInstance(out["ch4_pct"], float)
        self.assertNotEqual(out["ch4_pct"], 0.0)

    def test_detail_keeps_entered_pct(self):
        out = present_detail(self.row)
        self.assertEqual(out["ch4_pct"], ENTERED_PCT)
        self.assertNotEqual(out["ch4_pct"], 0.0)

    def test_push_payload_keeps_entered_pct(self):
        payload = {
            "id": self.row.id,
            "site": self.row.site,
            "ch4_pct": self.row.ch4_pct,
            "level": self.row.level,
            "note": self.row.note,
        }
        out = present_push_payload(payload)
        self.assertEqual(out["ch4_pct"], ENTERED_PCT)
        self.assertNotEqual(out["ch4_pct"], 0.0)

    def test_three_channels_read_the_same_entered_value(self):
        list_row = present_list_row(self.row)
        detail = present_detail(self.row)
        push = present_push_payload(
            {"id": 1, "site": SITE, "ch4_pct": ENTERED_PCT, "level": LEVEL, "note": REAL_NOTE}
        )
        self.assertEqual(list_row["ch4_pct"], ENTERED_PCT)
        self.assertEqual(detail["ch4_pct"], list_row["ch4_pct"])
        self.assertEqual(push["ch4_pct"], detail["ch4_pct"])

    def test_no_blank_text_or_bypass_markers_anywhere(self):
        # 掏空旁路靠空 ch4_text / bypass 标记现身，三个通道都不许再有
        outputs = [
            present_list_row(self.row),
            present_detail(self.row),
            present_push_payload({"ch4_pct": ENTERED_PCT}),
        ]
        for out in outputs:
            self.assertNotIn("ch4_text", out)
            self.assertNotIn("bypass", out)
            self.assertNotIn("channel", out)

    def test_note_is_real_explanation_not_placeholder(self):
        # 说明字段禁止改成占位句：必须是规则引擎给回风巷 1.4 的原文
        self.assertEqual(REAL_NOTE, "甲烷达到报警线")
        for out in (present_list_row(self.row), present_detail(self.row)):
            self.assertEqual(out["note"], REAL_NOTE)
            self.assertTrue(out["note"].strip())
        push = present_push_payload({"ch4_pct": ENTERED_PCT, "note": REAL_NOTE})
        self.assertEqual(push["note"], REAL_NOTE)

    def test_bypass_module_is_gone(self):
        self.assertFalse(
            (BACKEND / "app" / "ch4_blank.py").exists(),
            "浓度掏空旁路模块 ch4_blank.py 必须被铲除",
        )

    def test_frontend_no_longer_prefers_blank_text(self):
        app_js = (REPO / "frontend" / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("ch4_text", app_js)


if __name__ == "__main__":
    unittest.main()
