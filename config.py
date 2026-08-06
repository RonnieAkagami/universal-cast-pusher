import os
import streamlit as st

def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        val_str = v.strip().strip("'\"")
                        if k and val_str and (k not in os.environ or not os.environ[k].strip()):
                            os.environ[k] = val_str
        except Exception:
            pass

    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
    except ImportError:
        pass

def get_secret(key, default=""):
    _load_env()
    val = os.getenv(key)
    if val and val.strip():
        return val.strip()
    try:
        if hasattr(st, "secrets") and key in st.secrets and st.secrets[key]:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default

APP_TITLE = "Rubick CAST Automated Data Migrator"
APP_SUBTITLE = "Automated Excel-to-MongoDB pipeline with non-destructive attribute appending & data quality cleaning."

def __getattr__(name):
    if name == "MONGO_URI":
        return get_secret("MONGO_URI", "")
    elif name == "DB_NAME":
        return get_secret("DB_NAME", "omsProd")
    elif name == "COLLECTION_NAME":
        return get_secret("COLLECTION_NAME", "tasks")
    elif name == "SKU_FIELD":
        return get_secret("SKU_FIELD", "attributes.sku.value")
    elif name == "DEFAULT_ORG_ID":
        return get_secret("DEFAULT_ORG_ID", "org_Py834CU7ZEVygUiD")
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


