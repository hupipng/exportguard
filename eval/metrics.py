# -*- coding: utf-8 -*-
"""评测脚本：跑流水线（或读已有输出），按「风险类别」去重计分。

用法（在 exportguard 目录下）：
  python eval/metrics.py                     # 全系统（生成 + 规则 + LLM），需 API Key
  python eval/metrics.py --rules-only        # 仅规则库，离线（确定性基线）
  python eval/metrics.py --from-outputs      # 读 data/outputs.json 重新计分，不联网
  python eval/metrics.py --save              # 全系统并把结果（含生成文本）保存到 outputs.json
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.generator import generate_localized
from core.compliance import detect, product_text

PRODUCTS = os.path.join(ROOT, "data", "products_sample.json")
GOLD = os.path.join(ROOT, "data", "eval_labels.json")
OUTPUTS = os.path.join(ROOT, "data", "outputs.json")

# 规则库标题 -> 风险类别
RULE_TITLE_TO_CODE = {
    "医疗功效宣称违规": "A",
    "绝对化/促销用语违规": "B",
    "抗菌/杀菌宣称需EPA注册": "C",
    "儿童产品需CPC/CPSIA合规": "D",
    "小部件窒息警示缺失": "E",
    "电子产品需FCC认证": "F",
    "锂电池运输限制": "G",
    "食品接触/饰品需核实Prop65": "H",
    "环保宣称需佐证": "I",
    "濒危物种制品风险": "M",
    "化妆品需成分标注且不做药物宣称": "J",
}


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def to_codes(risk):
    """把一条检测结果映射到风险类别集合（按触发片段与依据，不含类型字符串）。"""
    if risk.get("source") == "规则库":
        code = RULE_TITLE_TO_CODE.get(risk.get("label", ""))
        return {code} if code else set()

    t = (risk.get("type", "") or "").lower()
    # 只看触发片段和依据来源，避免类型名里的示例词（如 "认证缺失(CPC/FCC/FDA/CE等)"）造成误映射
    text = " ".join([" ".join(risk.get("matched", []) or []), risk.get("basis", "") or ""]).lower()
    codes = set()

    def has(*pats):
        return any(re.search(p, text) for p in pats)

    if "认证" in t:
        if has("儿童", "玩具", "cpc", "cpsia", "astm", "可燃性", "婴儿"): codes.add("D")
        if has("化妆品", "面霜", "护肤", "inci", "mocra"): codes.add("J")
        if has("医疗", "药监", r"510\(k\)", "按摩", "注册证", "治疗"): codes.add("K")
        if has("锂电池", "电池", "un38", "battery"): codes.add("G")
        if has("fcc", "射频", "蓝牙", "电磁", "emc", "电气", "wifi", "wi-fi", "lvd"): codes.add("F")
        if has("食品接触", "food contact", "prop ?65", "铅", "镉", "邻苯", "bpa"): codes.add("H")
        if not codes: codes.add("F")
    elif "违禁" in t or "虚假" in t or "宣称" in t:
        if has("环保", "绿色", "eco", "biodegradable", "可持续", "碳"): codes.add("I")
        if has("杀菌", "抗菌", "消毒", "灭菌", "fifra", "epa", "净化"): codes.add("C")
        if has("医疗", "治疗", "治愈", "疗效", "疾病", "药物", "经络"): codes.add("A")
        if has("食品级", "食品接触", "food contact", "food-grade"): codes.add("H")
        if has("绝对", "夸大", "超长", "最好", "适合所有", "24小时", "all skin", "long battery", "保证", "促销", "无依据"): codes.add("B")
        if not codes: codes.add("B")
    elif "禁限售" in t or "受限" in t or "禁售" in t:
        if has("小零件", "窒息", "choking", "small parts"): codes.add("E")
        if has("精油", "sds", "危险品", "液体", "hazmat"): codes.add("L")
        if not codes: codes.add("M")
    elif "运输" in t:
        codes.add("G")
    elif "警示" in t:
        if has("小零件", "窒息", "choking", "small parts"): codes.add("E")
        elif has("prop ?65", "铅", "镉", "邻苯", "化学品"): codes.add("H")
    return codes


def run_pipeline(product, rules_only):
    if rules_only:
        localized = None
        text = product_text(product, None)
        detected = detect(text, product["category"], use_llm=False)
    else:
        localized = generate_localized(product)
        text = product_text(product, localized)
        detected = detect(text, product["category"], use_llm=True)
    return localized, detected


def score(products, gold_products, detected_by_pid):
    code_names = _load(GOLD).get("code_names", {})
    total_tp = total_fp = total_fn = 0
    rows = []
    for p in products:
        pid = p["id"]
        det_codes = set()
        for r in detected_by_pid[pid]:
            det_codes |= to_codes(r)
        gold_codes = set(gold_products.get(pid, {}).get("codes", []))
        tp = len(det_codes & gold_codes)
        fp = len(det_codes - gold_codes)
        fn = len(gold_codes - det_codes)
        total_tp += tp; total_fp += fp; total_fn += fn
        rows.append((pid, p["category"], sorted(gold_codes), sorted(det_codes), tp, fp, fn))
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return code_names, rows, precision, recall, f1, total_tp, total_fp, total_fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules-only", action="store_true", help="仅规则库，离线")
    ap.add_argument("--from-outputs", action="store_true", help="读 outputs.json 计分，不联网")
    ap.add_argument("--save", action="store_true", help="保存检测结果与生成文本到 outputs.json")
    args = ap.parse_args()

    products = _load(PRODUCTS)
    gold = _load(GOLD)
    gold_products = gold["products"]

    if args.from_outputs and os.path.isfile(OUTPUTS):
        saved = _load(OUTPUTS)
        detected_by_pid = {pid: saved[pid].get("detected", []) for pid in saved}
    else:
        detected_by_pid = {}
        saved = {}
        for p in products:
            pid = p["id"]
            try:
                localized, detected = run_pipeline(p, args.rules_only)
            except Exception as e:
                print(f"[跳过 {pid}] 运行失败：{e}")
                localized, detected = None, []
            detected_by_pid[pid] = detected
            saved[pid] = {"localized": localized, "detected": detected,
                          "gold_codes": gold_products.get(pid, {}).get("codes", [])}
        if args.save:
            with open(OUTPUTS, "w", encoding="utf-8") as f:
                json.dump(saved, f, ensure_ascii=False, indent=2)

    code_names, rows, precision, recall, f1, total_tp, total_fp, total_fn = score(
        products, gold_products, detected_by_pid)

    mode = "全系统（规则库 + LLM）"
    if args.rules_only:
        mode = "仅规则库（离线确定性基线）"
    elif args.from_outputs:
        mode = "读 outputs.json 重新计分（类别级去重）"

    print("=" * 80)
    print("合规检测评测结果 · " + mode)
    print("=" * 80)
    print(f"{'ID':<6}{'品类':<8}{'金标(类别)':<16}{'检出(类别)':<16}{'TP':>3}{'FP':>3}{'FN':>3}")
    for pid, cat, gc, dc, tp, fp, fn in rows:
        print(f"{pid:<6}{cat:<8}{','.join(gc):<16}{','.join(dc):<16}{tp:>3}{fp:>3}{fn:>3}")
    print("-" * 80)
    print("类别含义：" + "；".join(f"{k}={v}" for k, v in sorted(code_names.items())))
    print("-" * 80)
    print(f"精确率 Precision = {precision:.3f}")
    print(f"召回率 Recall   = {recall:.3f}")
    print(f"F1              = {f1:.3f}")
    print(f"(TP={total_tp}, FP={total_fp}, FN={total_fn})")


if __name__ == "__main__":
    main()
