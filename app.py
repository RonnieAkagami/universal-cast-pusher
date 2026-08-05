import streamlit as st
import pandas as pd
from pymongo import MongoClient

import config
from utils import (
    parse_excel_file,
    precheck_excel_data,
    is_reason_header,
    verify_mongo_connection,
    count_matching_db_docs,
    execute_cast_push
)

# --- Page Config ---
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling (Dark Glassmorphism) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #c9d1d9;
    }
    .header-container {
        background: linear-gradient(90deg, #1f6feb 0%, #8957e5 50%, #da3633 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #8b949e;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 12px;
        padding: 15px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
    }
    div[data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: #f0f6fc !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    .badge-card {
        background: rgba(22, 27, 34, 0.6);
        border-left: 4px solid #58a6ff;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .badge-warning {
        border-left-color: #d29922;
        background: rgba(210, 153, 34, 0.1);
    }
    .badge-success {
        border-left-color: #3fb950;
        background: rgba(63, 185, 80, 0.1);
    }
    .stButton > button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: #ffffff;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        box-shadow: 0 4px 14px rgba(46, 160, 67, 0.3);
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.title("⚡ Control Panel")

org_id_input = st.sidebar.text_input("Target Organization ID (orgId)", value=config.DEFAULT_ORG_ID, help="Enter the target orgId.")

conn_ok, conn_msg = verify_mongo_connection(config.MONGO_URI)
if conn_ok:
    st.sidebar.markdown('<div class="badge-card badge-success">🟢 MongoDB Connected</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown(f'<div class="badge-card badge-warning">🔴 Connection Error: {conn_msg}</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ How it Works")
st.sidebar.info(
    "1. **Upload Excel**: Drag & drop any CAST audit file (`.xlsx`).\n"
    "2. **Pre-Check**: Inspect matching SKUs and quality warnings.\n"
    "3. **Execute Push**: Data is appended via `$set` without overwriting existing product fields.\n"
    "4. **Auto-Clean**: Newlines and decimal rates are automatically sanitized."
)

# --- Main App Header ---
st.markdown(f'<div class="header-container">{config.APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{config.APP_SUBTITLE}</div>', unsafe_allow_html=True)

# --- Upload Area ---
uploaded_file = st.file_uploader("📂 Upload CAST Audit Excel File (.xlsx)", type=["xlsx", "xls"])

if uploaded_file is not None:
    headers, rows = parse_excel_file(uploaded_file)
    style_ids = [r["style_id"] for r in rows]
    issues = precheck_excel_data(headers, rows)
    matched_count, total_org_docs = count_matching_db_docs(config.MONGO_URI, org_id_input, style_ids)
    
    tab1, tab2, tab3 = st.tabs(["📊 1. Analysis & Pre-Check", "🚀 2. Execute Automated Push", "🔍 3. DB Inspector"])
    
    with tab1:
        st.markdown("### 📋 File & Database Pre-Check Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Excel Product Rows", len(rows))
        col2.metric("Excel Attribute Columns", len([h for h in headers if h and not is_reason_header(h)]) - 1)
        col3.metric("DB Matching Docs", f"{matched_count} / {len(rows)}")
        col4.metric("Total Org Docs in DB", total_org_docs)
        
        st.markdown("---")
        
        if matched_count == len(rows):
            st.success(f"✅ Perfect Match! All {len(rows)} SKUs in the Excel file have matching documents in MongoDB for `{org_id_input}`.")
        elif matched_count > 0:
            st.warning(f"⚠️ Partial Match: {matched_count} out of {len(rows)} SKUs match existing documents in MongoDB for `{org_id_input}`.")
        else:
            st.error(f"❌ Zero Matches: No documents in MongoDB for `{org_id_input}` match the uploaded SKUs.")
            
        st.markdown("#### ⚠️ Quality Warnings Detected in Excel File:")
        w_col1, w_col2 = st.columns(2)
        with w_col1:
            if issues["decimal_rates"]:
                st.warning(f"**Decimal Rates Detected ({len(issues['decimal_rates'])} rows)**\n\nRates like `0.09` will be automatically converted to `9%` after push.")
            else:
                st.info("✅ All failure rates are properly formatted.")
        with w_col2:
            if issues["malformed_reports"]:
                st.warning(f"**Malformed Failure Reports ({len(issues['malformed_reports'])} rows)**\n\nSingle-line bullet points will be formatted into clean multi-line bullet lists.")
            else:
                st.info("✅ All failure reports are multi-line formatted.")
                
        with st.expander("👁️ Preview Uploaded Data Table (First 10 Rows)", expanded=False):
            if hasattr(uploaded_file, "seek"):
                uploaded_file.seek(0)
            df_preview = pd.read_excel(uploaded_file)
            st.dataframe(df_preview.head(10), use_container_width=True)
            
    with tab2:
        st.markdown("### 🚀 Execute Universal Data Push")
        st.write(f"Targeting Organization: **`{org_id_input}`** | Matching Strategy: **Non-destructive `$set` on `attributes.*`**")
        
        if st.button("⚡ Start Automated Data Push & Cleaning"):
            progress_bar = st.progress(0.0)
            log_container = st.empty()
            logs = []
            
            def log_callback(msg):
                logs.append(msg)
                log_container.code("\n".join(logs[-10:]), language="bash")
                
            with st.spinner("Processing Excel and pushing attributes to MongoDB..."):
                processed, matched, cleaned_reports, fixed_rates = execute_cast_push(
                    uploaded_file, org_id_input, config.MONGO_URI, log_callback, progress_bar.progress
                )
                
            st.balloons()
            st.success("🎉 Automated Push & Quality Cleaning Finished Successfully!")
            
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Rows Processed", processed)
            m_col2.metric("DB Documents Updated", matched)
            m_col3.metric("Sanitized Reports", cleaned_reports)
            m_col4.metric("Fixed Decimal Rates", fixed_rates)
            
    with tab3:
        st.markdown("### 🔍 Live MongoDB Document Inspector")
        if st.button("🔄 Fetch Matching Documents from Database"):
            client = MongoClient(config.MONGO_URI)
            collection = client[config.DB_NAME][config.COLLECTION_NAME]
            
            sku_criteria = []
            for s in style_ids:
                sku_criteria.append(s)
                try:
                    sku_criteria.append(int(s))
                except ValueError:
                    pass
                    
            docs = list(collection.find({
                "orgId": org_id_input,
                config.SKU_FIELD: {"$in": sku_criteria}
            }).limit(20))
            
            client.close()
            
            if docs:
                st.success(f"Found {len(docs)} sample document(s) in MongoDB:")
                sku_labels = [str(d.get("attributes", {}).get("sku", {}).get("value") or d["_id"]) for d in docs]
                selected_sku = st.selectbox("Select SKU to inspect attributes:", sku_labels)
                
                selected_doc = next((d for d, label in zip(docs, sku_labels) if label == selected_sku), None)
                if selected_doc:
                    st.write(f"**Document ID**: `{selected_doc['_id']}`")
                    st.write(f"**Title**: {selected_doc.get('attributes', {}).get('title', {}).get('value', 'N/A')}")
                    st.write(f"**Total Attribute Keys**: {len(selected_doc.get('attributes', {}))}")
                    with st.expander("📄 View Full JSON `attributes` Object", expanded=True):
                        st.json(selected_doc.get("attributes", {}))
            else:
                st.warning("No documents found in DB for the specified orgId and SKUs.")
else:
    st.info("👆 Upload a CAST audit Excel file above to begin the automated import process.")



