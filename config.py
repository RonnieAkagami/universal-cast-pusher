import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Lightweight fallback to parse .env if python-dotenv is missing
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    if k and k not in os.environ:
                        os.environ[k] = v.strip().strip("'\"")
    except Exception:
        pass

import streamlit as st

DEFAULT_MONGO_URI = ""

def get_secret(key, default=""):
    val = os.getenv(key)
    if val:
        return val
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default

# MongoDB Connection Configuration
MONGO_URI = get_secret("MONGO_URI", DEFAULT_MONGO_URI)
DB_NAME = get_secret("DB_NAME", "omsProd")
COLLECTION_NAME = get_secret("COLLECTION_NAME", "tasks")
SKU_FIELD = get_secret("SKU_FIELD", "attributes.sku.value")

# Default UI Settings
DEFAULT_ORG_ID = get_secret("DEFAULT_ORG_ID", "Your ORG ID")
APP_TITLE = "Rubick CAST Automated Data Migrator"
APP_SUBTITLE = "Automated Excel-to-MongoDB pipeline with non-destructive attribute appending & data quality cleaning."

