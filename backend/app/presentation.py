"""甲烷浓度统一展示：总表、详情、推送载荷都读出当初填写的真值。

禁止任何把浓度掏空为 0/空串的旁路；note 说明字段也必须原样保留，
不得替换成占位句。
"""


def true_pct(ch4_pct) -> float:
    """三个通道共用：浓度即入库时的填写值。"""
    return float(ch4_pct)


def pct_text(ch4_pct) -> str:
    """总表/推送直接渲染的百分比文本，与数值一致。"""
    return f"{float(ch4_pct):g}%"


def present_list_row(row) -> dict:
    return {
        "id": row.id,
        "site": row.site,
        "ch4_pct": true_pct(row.ch4_pct),
        "ch4_text": pct_text(row.ch4_pct),
        "level": row.level,
        "note": row.note,
        "created_by": row.created_by,
        "channel": "list",
    }


def present_detail(row) -> dict:
    return {
        "id": row.id,
        "site": row.site,
        "ch4_pct": true_pct(row.ch4_pct),
        "ch4_text": pct_text(row.ch4_pct),
        "level": row.level,
        "note": row.note,
        "created_by": row.created_by,
        "channel": "detail",
    }


def present_push_payload(payload: dict) -> dict:
    out = dict(payload)
    out["ch4_pct"] = true_pct(out.get("ch4_pct", 0))
    out["ch4_text"] = pct_text(out["ch4_pct"])
    out["channel"] = "push"
    # note 原样透传，禁止改成占位句
    return out
