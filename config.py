import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# MongoDB Connection Configuration
DEFAULT_MONGO_URI = ""
MONGO_URI = os.getenv("MONGO_URI", DEFAULT_MONGO_URI)
DB_NAME = os.getenv("DB_NAME", "omsProd")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "tasks")
SKU_FIELD = os.getenv("SKU_FIELD", "attributes.sku.value")

# Default UI Settings
DEFAULT_ORG_ID = os.getenv("DEFAULT_ORG_ID", "org_Py834CU7ZEVygUiD")
APP_TITLE = "Universal CAST Data Pusher"
APP_SUBTITLE = "Automated Excel-to-MongoDB pipeline with non-destructive attribute appending & data quality cleaning."
