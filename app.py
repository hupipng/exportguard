# -*- coding: utf-8 -*-
import json
import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from core.generator import generate_localized
from core.compliance import detect, product_text
from core.report import build_html

SAMPLE_PATH = os.path.join(ROOT, "data", "products_sample.json")


@st.cache_data
def load_samples():
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


st.set_page_config(page_title="出海护航 ExportGuard", layout="wide")
st.title("🚢 出海护航 ExportGuard")
st.caption("跨境电商内容合规与多语言本地化 AI 工具链 · AI+软件 · AI+数字内容IP出海")

samples = load_samples()
ids = [p["id"] for p in samples]
sel = st.selectbox("示例商品（演示用，正式请替换为真实 1688 商品）", ids)
sample = next(p for p in samples if p["id"] == sel)

col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.subheader("① 输入商品")
    category = st.text_input("品类", value=sample["category"])
    title_cn = st.text_input("中文标题", value=sample["title_cn"])
    bullets_cn = st.text_area("中文卖点（5 条，分号分隔）", value=sample["bullets_cn"], height=110)
    desc_cn = st.text_area("中文描述", value=sample["description_cn"], height=90)
    run = st.button("🚀 跑通全流程（本地化 + 合规检测）", type="primary")
    run_rules = st.button("🔍 仅规则库检测（不调用 LLM，可离线）")

with col_r:
    st.subheader("② 结果")
    if run or run_rules:
        product = {
            "id": sample["id"], "category": category, "title_cn": title_cn,
            "bullets_cn": bullets_cn, "description_cn": desc_cn,
        }
        if run_rules:
            with st.spinner("规则库检测中（不调用 LLM）..."):
                localized = {"title": "", "bullets": [], "description": ""}
                text = product_text(product, None)
                risks = detect(text, category, use_llm=False)
        else:
            with st.spinner("本地化生成 + 合规检测中（调用 LLM）..."):
                try:
                    localized = generate_localized(product)
                    text = product_text(product, localized)
                    risks = detect(text, category, use_llm=True)
                except Exception as e:
                    st.error(f"运行失败：{e}")
                    st.stop()

        st.markdown("#### 本地化生成结果")
        st.text_input("英文标题", value=localized.get("title", ""), disabled=True)
        st.text_area("英文卖点", value="\n".join(localized.get("bullets", []) or []), disabled=True, height=110)
        st.text_area("英文描述", value=localized.get("description", ""), disabled=True, height=80)

        st.markdown("#### 合规检测结果")
        if risks:
            st.dataframe([
                {"等级": r["severity"], "风险": r["label"], "类型": r["type"],
                 "来源": r["source"], "依据": r["basis"], "建议": r["suggestion"]}
                for r in risks
            ])
        else:
            st.success("未检出风险")

        html = build_html(product, localized, risks)
        st.download_button(
            "⬇️ 下载合规报告 HTML", data=html,
            file_name="出海护航_合规报告.html", mime="text/html",
        )
