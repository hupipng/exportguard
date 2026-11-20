import os


def _candidate_env_paths():
    here = os.path.dirname(os.path.abspath(__file__))
    return [os.getcwd(), here, os.path.dirname(here)]


def _load_env():
    for d in _candidate_env_paths():
        path = os.path.join(d, ".env")
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and key not in os.environ:
                            os.environ[key] = value
            except OSError:
                pass
            break


def _load_streamlit_secrets():
    """在 Streamlit Cloud 上，密钥通过 st.secrets 注入（不放在仓库文件里）。"""
    try:
        import streamlit as st
        for key, value in st.secrets.items():
            if key not in os.environ:
                os.environ[key] = str(value)
    except Exception:
        pass


_load_env()
_load_streamlit_secrets()

LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat").strip()
