import json
import re
import urllib.error
import urllib.request

from . import config


def _extract_json(text):
    text = (text or "").strip()
    if not text:
        raise ValueError("模型返回为空")
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def _post(body):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(config.LLM_BASE_URL.rstrip("/") + "/chat/completions", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + config.LLM_API_KEY)
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chat_json(system, user, temperature=0.3):
    """调用 LLM 并要求返回 JSON 对象（纯标准库实现，无需安装 SDK）。"""
    if not config.LLM_API_KEY:
        raise RuntimeError("未配置 LLM_API_KEY，请在 exportguard/.env 中填写")
    body = {
        "model": config.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    try:
        payload = _post(body)
    except urllib.error.HTTPError:
        body.pop("response_format", None)
        payload = _post(body)
    content = payload["choices"][0]["message"]["content"]
    return _extract_json(content)
