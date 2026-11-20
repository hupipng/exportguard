import json
from .llm import chat_json

SYSTEM = """你是资深跨境电商本地化专家。请把中文商品信息转换成美式英语，用于 Amazon 美国站上架。
必须遵守：
1. 标题不超过 200 个字符，不使用促销信息（如 free shipping、sale）和绝对化用语（如 best、guaranteed）；
2. 五点卖点恰好 5 条，每条不超过 250 个字符，以 "•" 开头；
3. 不出现 Amazon 禁用/受限宣称词（best、guaranteed、cure、treat、heal、FDA approved 等）；
4. 语言地道、符合美式表达习惯，不做字面直译；
5. 严格忠实于原文，不得编造原文没有的参数、认证或功效。
只输出一个 JSON 对象，不要任何多余文字。JSON 结构：
{"title": "string", "bullets": ["...","...","...","...","..."], "description": "string"}"""


def generate_localized(product: dict) -> dict:
    """把中文商品信息转成目标市场语言。product 至少含 title_cn / bullets_cn / description_cn。"""
    payload = {
        "品类": product.get("category", ""),
        "中文标题": product.get("title_cn", ""),
        "中文卖点": product.get("bullets_cn", ""),
        "中文描述": product.get("description_cn", ""),
    }
    user = json.dumps(payload, ensure_ascii=False)
    return chat_json(SYSTEM, user, temperature=0.4)
