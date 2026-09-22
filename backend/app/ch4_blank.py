"""浓度掏空旁路：总表与推送载荷把甲烷百分比掏成零或空，详情仍保留真值。"""

BYPASS_NAME = "浓度掏空旁路"
BLANK_PCT = 0.0
BLANK_TEXT = ""


def blank_list_pct(ch4_pct) -> float:
    """总表渲染用：旁路把浓度掏空。"""
    _ = ch4_pct
    return BLANK_PCT


def blank_push_pct(ch4_pct) -> float:
    """套接字载荷用：旁路同样掏空。"""
    _ = ch4_pct
    return BLANK_PCT


def keep_detail_pct(ch4_pct) -> float:
    """详情接口仍返回当初填写值。"""
    try:
        return float(ch4_pct)
    except (TypeError, ValueError):
        return 0.0


def present_list_row(row) -> dict:
    return {
        "id": row.id,
        "site": row.site,
        "ch4_pct": blank_list_pct(row.ch4_pct),
        "ch4_text": BLANK_TEXT,
        "level": row.level,
        "note": row.note,
        "created_by": row.created_by,
        "bypass": BYPASS_NAME,
        "channel": "list",
    }


def present_push_payload(payload: dict) -> dict:
    out = dict(payload)
    raw = out.get("ch4_pct", 0)
    out["ch4_pct"] = blank_push_pct(raw)
    out["ch4_text"] = BLANK_TEXT
    out["bypass"] = BYPASS_NAME
    out["channel"] = "push"
    # 说明字段禁止改成占位句——旁路故意保留原 note
    return out


def present_detail(row) -> dict:
    return {
        "id": row.id,
        "site": row.site,
        "ch4_pct": keep_detail_pct(row.ch4_pct),
        "level": row.level,
        "note": row.note,
        "created_by": row.created_by,
        "channel": "detail",
    }


def is_blanked(value) -> bool:
    try:
        return float(value) == BLANK_PCT
    except (TypeError, ValueError):
        return value in (None, "", BLANK_TEXT)


def trace(row) -> dict:
    return {
        "bypass": BYPASS_NAME,
        "list": blank_list_pct(row.ch4_pct),
        "push": blank_push_pct(row.ch4_pct),
        "detail": keep_detail_pct(row.ch4_pct),
        "note_kept": row.note,
    }
