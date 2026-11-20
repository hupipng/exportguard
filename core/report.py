def build_html(product: dict, localized: dict, risks: list) -> str:
    title = localized.get("title", "")
    bullets = localized.get("bullets", []) or []
    description = localized.get("description", "")
    bullets_html = "".join(f"<li>{b}</li>" for b in bullets)

    risk_rows = ""
    for r in risks:
        sev = r.get("severity", "low")
        color = {"high": "#c0392b", "medium": "#b9770e", "low": "#7f8c8d"}.get(sev, "#7f8c8d")
        matched = "、".join(r.get("matched", []) or []) or "—"
        basis = r.get("basis", "") or "—"
        basis_url = r.get("basis_url", "") or ""
        if basis_url:
            basis_html = f'<a href="{basis_url}" target="_blank">{basis}</a>'
        else:
            basis_html = basis
        risk_rows += (
            f'<tr>'
            f'<td><span style="color:{color};font-weight:700">{sev.upper()}</span></td>'
            f'<td>{r.get("label", "")}<br>'
            f'<small>类型：{r.get("type", "")} · 来源：{r.get("source", "")}</small></td>'
            f'<td>{matched}</td>'
            f'<td>{basis_html}</td>'
            f'<td>{r.get("suggestion", "")}</td>'
            f'</tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>出海护航 · 合规报告</title></head>
<body style="font-family:-apple-system,Segoe UI,Microsoft YaHei,sans-serif;line-height:1.6;color:#222">
<h1 style="margin-bottom:4px">🚢 出海护航 ExportGuard · 合规报告</h1>
<p style="color:#666;margin-top:0">跨境电商内容合规与多语言本地化 AI 工具链</p>

<h2>原始商品</h2>
<p><b>品类：</b>{product.get("category", "")}</p>
<p><b>中文标题：</b>{product.get("title_cn", "")}</p>
<p><b>中文卖点：</b>{product.get("bullets_cn", "")}</p>
<p><b>中文描述：</b>{product.get("description_cn", "")}</p>

<h2>本地化生成结果</h2>
<p><b>Title：</b>{title}</p>
<p><b>Bullet Points：</b></p>
<ul>{bullets_html}</ul>
<p><b>Description：</b>{description}</p>

<h2>合规检测结果（{len(risks)} 条风险）</h2>
<table border="1" cellspacing="0" cellpadding="8" style="border-collapse:collapse;width:100%">
<thead><tr style="background:#f5f5f5">
<th>等级</th><th>风险</th><th>触发片段</th><th>依据来源</th><th>修改建议</th>
</tr></thead>
<tbody>{risk_rows}</tbody>
</table>

<p style="color:#888;font-size:12px;margin-top:24px">本报告由出海护航自动生成，风险依据为公开法规与平台政策，供参考，不构成法律意见。</p>
</body></html>"""
