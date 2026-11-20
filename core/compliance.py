import json
import os
from .llm import chat_json

_RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rules", "us_amazon.json")


def load_rules():
    with open(_RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("rules", [])


def rule_match(text: str, category: str):
    """规则库确定性检测（可离线、可溯源）。同时扫描中文原始宣称与英文生成内容。"""
    text_lower = (text or "").lower()
    hits = []
    for r in load_rules():
        cats = r.get("categories") or []
        if cats and category not in cats:
            continue
        kws = r.get("keywords") or []
        matched = [k for k in kws if k.lower() in text_lower]
        if cats and not kws:
            # 品类驱动规则：命中品类即提示核实
            hit = True
            matched = []
        else:
            hit = bool(matched)
        if hit:
            hits.append({
                "label": r.get("title"),
                "type": r.get("type"),
                "severity": r.get("severity"),
                "matched": matched,
                "basis": r.get("basis"),
                "basis_url": r.get("basis_url"),
                "suggestion": r.get("suggestion"),
                "source": "规则库",
            })
    return hits


LLM_SYSTEM = """你是跨境电商合规审查专家。检查以下商品文本，找出四类风险：
1) 违禁词/虚假宣称  2) 认证缺失(CPC/FCC/FDA/CE等)  3) 文化宗教敏感  4) 平台禁限售。
规则：
- 每条风险必须给出 type、text(原文触发片段)、severity(high/medium/low)、basis(平台政策或法规名)、suggestion(修改建议)；
- 依据必须是真实存在的法规或平台政策，不得编造不存在的法规；
- 只针对输入文本判断，不要臆测；
- 没有风险就输出空列表。
只输出 JSON：{"risks":[{"type":"...","text":"...","severity":"...","basis":"...","suggestion":"..."}]}"""


def llm_check(text: str):
    try:
        out = chat_json(LLM_SYSTEM, text, temperature=0.1)
        risks = out.get("risks", []) or []
    except Exception:
        risks = []
    result = []
    for r in risks:
        result.append({
            "label": r.get("type", "未分类风险"),
            "type": r.get("type", "未分类风险"),
            "severity": r.get("severity", "low"),
            "matched": [r.get("text", "")] if r.get("text") else [],
            "basis": r.get("basis", ""),
            "basis_url": "",
            "suggestion": r.get("suggestion", ""),
            "source": "LLM",
        })
    return result


def detect(text: str, category: str, use_llm: bool = True):
    """合并规则库 + LLM 两层检测，去重。"""
    hits = rule_match(text, category)
    if use_llm:
        hits += llm_check(text)
    seen = set()
    unique = []
    for h in hits:
        key = (h.get("label", ""), tuple(h.get("matched", [])))
        if key in seen:
            continue
        seen.add(key)
        unique.append(h)
    return unique


def product_text(product: dict, localized: dict = None) -> str:
    """拼接商品全文：中文原始 + （可选）英文生成内容。"""
    parts = [
        product.get("title_cn", ""),
        product.get("bullets_cn", ""),
        product.get("description_cn", ""),
    ]
    if localized:
        parts.append(localized.get("title", ""))
        parts.append(" ".join(localized.get("bullets", []) or []))
        parts.append(localized.get("description", ""))
    return "\n".join(parts)
