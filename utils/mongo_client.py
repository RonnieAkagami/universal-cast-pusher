import pymongo
from pymongo import MongoClient
import re
from config import DB_NAME, COLLECTION_NAME, SKU_FIELD
from .excel_parser import parse_excel_file, is_reason_header, to_camel_case

_client_cache = {}

def get_mongo_client(uri):
    if uri not in _client_cache:
        _client_cache[uri] = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client_cache[uri]

def verify_mongo_connection(uri):
    try:
        client = get_mongo_client(uri)
        client.admin.command('ping')
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)

def count_matching_db_docs(uri, org_id, style_ids):
    client = get_mongo_client(uri)
    collection = client[DB_NAME][COLLECTION_NAME]
    
    sku_criteria = []
    for s in style_ids:
        sku_criteria.append(s)
        try:
            val_num = int(s)
            sku_criteria.append(val_num)
        except ValueError:
            pass
            
    count = collection.count_documents({
        "orgId": org_id,
        SKU_FIELD: {"$in": sku_criteria}
    })
    
    total_org_docs = collection.count_documents({"orgId": org_id})
    return count, total_org_docs

def execute_cast_push(uploaded_file, org_id, mongo_uri, log_callback, progress_callback):
    headers, rows = parse_excel_file(uploaded_file)
    
    client = get_mongo_client(mongo_uri)
    collection = client[DB_NAME][COLLECTION_NAME]
    
    log_callback(f"🚀 Connecting to MongoDB collection `{DB_NAME}.{COLLECTION_NAME}`...")
    log_callback(f"📌 Target Org ID: {org_id}")
    log_callback(f"📄 Total Rows to Process: {len(rows)}")
    
    processed = 0
    matched = 0
    total_steps = len(rows)
    
    for idx, item in enumerate(rows):
        cells = item["cells"]
        style_id = item["style_id"]
        
        sku_criteria = [style_id]
        try:
            sku_criteria.append(int(style_id))
        except ValueError:
            pass
            
        filter_query = {
            "orgId": org_id,
            SKU_FIELD: {"$in": sku_criteria}
        }
        
        update_obj = {}
        
        for j in range(1, len(headers)):
            header = headers[j]
            if not header or is_reason_header(header):
                continue
                
            val = cells[j] if j < len(cells) else ""
            
            # Paired reason lookup
            reason_val = ""
            if j + 1 < len(headers) and is_reason_header(headers[j + 1]):
                reason_val = cells[j + 1] if j + 1 < len(cells) else ""
            else:
                for r_idx in range(j + 1, len(headers)):
                    rh = headers[r_idx]
                    if is_reason_header(rh) and rh.lower().startswith(header.lower()):
                        reason_val = cells[r_idx] if r_idx < len(cells) else ""
                        break
                        
            camel_key = to_camel_case(header)
            str_val = str(val) if val is not None else ""
            
            update_obj[f"attributes.{camel_key}"] = {
                "name": header,
                "value": val if val is not None else "",
                "type": "string",
                "hint": "",
                "meta": {
                    "reason": {"value": reason_val if reason_val is not None else "", "type": "string"},
                    "indicates": {"value": "good" if str_val.lower() == "passed" else "bad", "type": "string"}
                },
                "tags": ["intelcopilot", "myntraqc", "catalogueEdit"]
            }
            
        res = collection.update_one(filter_query, {"$set": update_obj})
        processed += 1
        if res.matched_count > 0:
            matched += 1
            
        if progress_callback:
            progress_callback((idx + 1) / total_steps)
        if (idx + 1) % 20 == 0 or (idx + 1) == total_steps:
            log_callback(f"⏳ Processed {idx + 1}/{total_steps} rows | Matched: {matched}")
            
    log_callback("✅ Base CAST attributes `$set` complete!")
    
    # Automated Post-Import Cleaning
    log_callback("🧹 Executing Automated Post-Import Quality Cleaning...")
    docs_with_reports = list(collection.find({
        "orgId": org_id,
        "attributes.failureReport.value": {"$exists": True, "$ne": ""}
    }))
    
    cleaned_reports = 0
    for doc in docs_with_reports:
        report = doc.get("attributes", {}).get("failureReport", {}).get("value", "")
        original = report
        
        cleaned = re.sub(r' • ', '\n• ', report)
        cleaned = re.sub(r'\n\n+', '\n', cleaned).strip()
        cleaned = re.sub(r'\n?• Original LVN is missing\.', '', cleaned)
        cleaned = re.sub(r'\n?• Original PDN is missing\.', '', cleaned).strip()
        
        if cleaned != original:
            collection.update_one({"_id": doc["_id"]}, {"$set": {"attributes.failureReport.value": cleaned}})
            cleaned_reports += 1
            
    log_callback(f"  ✨ Sanitized {cleaned_reports} failure report strings.")
    
    docs_with_rates = list(collection.find({
        "orgId": org_id,
        "attributes.failureRate.value": {"$exists": True}
    }))
    
    fixed_rates = 0
    for doc in docs_with_rates:
        rate = doc.get("attributes", {}).get("failureRate", {}).get("value")
        if isinstance(rate, (float, int)) and 0 < rate < 1:
            collection.update_one({"_id": doc["_id"]}, {"$set": {"attributes.failureRate.value": round(rate * 100)}})
            fixed_rates += 1
            
    log_callback(f"  ✨ Converted {fixed_rates} decimal failure rates to whole percentages.")
    log_callback("🎉 Universal Pushing & Quality Cleaning Completed Successfully!")
    
    return processed, matched, cleaned_reports, fixed_rates
