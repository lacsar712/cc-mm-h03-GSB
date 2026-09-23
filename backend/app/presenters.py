"""读数呈现层：总表、详情、推送载荷读出同一份甲烷百分比。

三处通道都必须返回当初填写的 ch4_pct 真值，禁止在这里把浓度改写成
零或空字符串。说明字段 note 同样原样透传，禁止替换成占位句。
"""


def present_pct(ch4_pct) -> float:
    """三个通道共用的唯一浓度出口：原值转 float，不掏空、不置空。"""
    return float(ch4_pct)


def present_list_row(row) -> dict:
    """总表渲染用：浓度等于库里存的当初填写值。"""
    return {
        "id": row.id,
        "site": row.site,
        "ch4_pct": present_pct(row.ch4_pct),
        "level": row.level,
        "note": row.note,
        "created_by": row.created_by,
    }


def present_push_payload(payload: dict) -> dict:
    """套接字（及上报响应）载荷用：浓度同样保留真值，note 保留原文。"""
    out = dict(payload)
    out["ch4_pct"] = present_pct(out["ch4_pct"])
    return out


def present_detail(row) -> dict:
    """详情接口用：与总表、推送读出完全一致的浓度。"""
    return {
        "id": row.id,
        "site": row.site,
        "ch4_pct": present_pct(row.ch4_pct),
        "level": row.level,
        "note": row.note,
        "created_by": row.created_by,
    }
