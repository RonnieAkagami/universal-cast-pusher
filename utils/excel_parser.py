import openpyxl
import re

def to_camel_case(text):
    if not text:
        return ""
    s = re.sub(r'[^a-zA-Z0-9]+', ' ', str(text)).strip()
    words = s.split()
    if not words:
        return ""
    return words[0].lower() + ''.join(w.capitalize() for w in words[1:])

def is_reason_header(header):
    if not header:
        return False
    h = str(header).strip().lower()
    return h.endswith("reason") or h.endswith("fail reason") or h.endswith("mismatch reason")

def parse_excel_file(uploaded_file):
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    workbook = openpyxl.load_workbook(uploaded_file, data_only=True)
    sheet = workbook.worksheets[0]
    
    headers = [cell.value.strip() if cell.value else "" for cell in sheet[1]]
    rows = []
    
    for row_idx, row_cells in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        if not row_cells:
            continue
        style_id = str(row_cells[0]).strip() if row_cells[0] is not None else ""
        if style_id and style_id != "None":
            rows.append({
                "row_number": row_idx,
                "style_id": style_id,
                "cells": row_cells
            })
            
    return headers, rows

def precheck_excel_data(headers, rows):
    issues = {
        "malformed_reports": [],
        "decimal_rates": [],
        "boilerplate_count": 0
    }
    
    failure_report_idx = -1
    failure_rate_idx = -1
    
    for idx, h in enumerate(headers):
        if h == "Failure Report":
            failure_report_idx = idx
        elif h in ["Failure Rate", "Failure Rate (%)"]:
            failure_rate_idx = idx
            
    for item in rows:
        cells = item["cells"]
        style_id = item["style_id"]
        row_num = item["row_number"]
        
        if failure_report_idx >= 0 and len(cells) > failure_report_idx:
            report = str(cells[failure_report_idx] or "")
            if "•" in report and ("\n" not in report or " • " in report):
                issues["malformed_reports"].append({
                    "row": row_num, "sku": style_id, "preview": report[:80]
                })
            if "Original PDN is missing" in report or "Original LVN is missing" in report:
                issues["boilerplate_count"] += 1
                
        if failure_rate_idx >= 0 and len(cells) > failure_rate_idx:
            rate = cells[failure_rate_idx]
            try:
                num_rate = float(rate)
                if 0 < num_rate < 1:
                    issues["decimal_rates"].append({
                        "row": row_num, "sku": style_id, "rate": num_rate
                    })
            except (ValueError, TypeError):
                pass
                
    return issues

