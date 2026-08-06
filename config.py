import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st

DEFAULT_MONGO_URI = "mongodb://prod_roshan:Eo4GCF14g7HHNJGeK6QFg1GlDEfYtbuO9S4tOoP3g99f4mZRGc@13.126.165.228:57018/omsProd?authSource=admin&directConnection=true"

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

