"""
AI-CARE Lung - Google Sheets 資料管理模組
==========================================

整合 Google Sheets 作為共享資料庫
病人端和管理後台共用同一份 Sheet
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime
import pandas as pd

# ============================================
# Google Sheets 設定
# ============================================

# Sheets 欄位定義
PATIENT_COLUMNS = [
    "patient_id", "name", "phone", "password", "age", "gender",
    "surgery_type", "surgery_date", "diagnosis", "medical_record",
    "status", "post_op_day",
    "consent_agreed", "consent_time", "registered_at",
    "clinical_data", "notes"
]

REPORT_COLUMNS = [
    "report_id", "patient_id", "patient_name", "date", "timestamp",
    "overall_score", "symptoms", "messages_count",
    "alert_level", "alert_handled", "handled_by", "handled_at"
]

EDUCATION_COLUMNS = [
    "push_id", "patient_id", "patient_name", "material_id", "material_title",
    "category", "push_type", "pushed_by", "pushed_at",
    "read_at", "status"
]

INTERVENTION_COLUMNS = [
    "intervention_id", "patient_id", "patient_name", "date", "timestamp",
    "method", "duration", "content", "referral", "created_by"
]

# ============================================
# 連線管理
# ============================================

@st.cache_resource
def get_google_sheets_connection():
    """取得 Google Sheets 連線（使用快取）"""
    try:
        # 從 Streamlit Secrets 讀取憑證
        credentials_dict = st.secrets["gcp_service_account"]
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes
        )
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Google Sheets 連線失敗: {e}")
        return None

def get_spreadsheet():
    """取得試算表"""
    client = get_google_sheets_connection()
    if not client:
        return None
    
    try:
        # 從 secrets 取得試算表 ID
        spreadsheet_id = st.secrets.get("spreadsheet_id", "")
        if spreadsheet_id:
            return client.open_by_key(spreadsheet_id)
        else:
            # 或使用名稱
            spreadsheet_name = st.secrets.get("spreadsheet_name", "AI-CARE-Lung-Data")
            return client.open(spreadsheet_name)
    except Exception as e:
        st.error(f"無法開啟試算表: {e}")
        return None

def get_or_create_worksheet(spreadsheet, sheet_name, columns):
    """取得或建立工作表"""
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        # 建立新工作表
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(columns))
        # 設定標題列
        worksheet.update('A1', [columns])
    return worksheet

# ============================================
# 病人資料管理
# ============================================

def get_all_patients():
    """取得所有病人"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return []
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Patients", PATIENT_COLUMNS)
        records = worksheet.get_all_records()
        
        # 計算術後天數
        today = datetime.now().date()
        for record in records:
            if record.get("surgery_date"):
                try:
                    surgery_date = datetime.strptime(record["surgery_date"], "%Y-%m-%d").date()
                    record["post_op_day"] = (today - surgery_date).days
                except:
                    record["post_op_day"] = 0
            else:
                record["post_op_day"] = 0
        
        return records
    except Exception as e:
        st.error(f"讀取病人資料失敗: {e}")
        return []

def get_patient_by_phone(phone):
    """根據手機號碼查找病人"""
    patients = get_all_patients()
    for patient in patients:
        if patient.get("phone") == phone:
            return patient
    return None

def get_patient_by_id(patient_id):
    """根據 ID 查找病人"""
    patients = get_all_patients()
    for patient in patients:
        if patient.get("patient_id") == patient_id:
            return patient
    return None

def create_patient(patient_data):
    """建立新病人"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Patients", PATIENT_COLUMNS)
        
        # 準備資料列
        row = []
        for col in PATIENT_COLUMNS:
            value = patient_data.get(col, "")
            # 處理 dict/list 轉 JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            row.append(value)
        
        # 新增到最後一列
        worksheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"建立病人失敗: {e}")
        return False

def update_patient(patient_id, update_data):
    """更新病人資料"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Patients", PATIENT_COLUMNS)
        
        # 找到病人所在列
        cell = worksheet.find(patient_id)
        if not cell:
            return False
        
        row_number = cell.row
        
        # 更新各欄位
        for key, value in update_data.items():
            if key in PATIENT_COLUMNS:
                col_index = PATIENT_COLUMNS.index(key) + 1
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                worksheet.update_cell(row_number, col_index, value)
        
        return True
    except Exception as e:
        st.error(f"更新病人失敗: {e}")
        return False

# ============================================
# 回報資料管理
# ============================================

def get_all_reports():
    """取得所有回報"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return []
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Reports", REPORT_COLUMNS)
        records = worksheet.get_all_records()
        
        # 解析 symptoms JSON
        for record in records:
            if record.get("symptoms"):
                try:
                    record["symptoms"] = json.loads(record["symptoms"])
                except:
                    record["symptoms"] = []
        
        return records
    except Exception as e:
        st.error(f"讀取回報資料失敗: {e}")
        return []

def get_patient_reports(patient_id):
    """取得特定病人的回報"""
    reports = get_all_reports()
    patient_reports = [r for r in reports if r.get("patient_id") == patient_id]
    return sorted(patient_reports, key=lambda x: x.get("timestamp", ""), reverse=True)

def get_today_reports():
    """取得今日回報"""
    today = datetime.now().strftime("%Y-%m-%d")
    reports = get_all_reports()
    return [r for r in reports if r.get("date") == today]

def save_report(patient_id, patient_name, report_data):
    """儲存回報"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Reports", REPORT_COLUMNS)
        
        now = datetime.now()
        report_id = f"R{now.strftime('%Y%m%d%H%M%S')}"
        
        # 判斷警示等級
        score = report_data.get("overall_score", 0)
        if score >= 7:
            alert_level = "red"
        elif score >= 4:
            alert_level = "yellow"
        else:
            alert_level = "green"
        
        row_data = {
            "report_id": report_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "date": now.strftime("%Y-%m-%d"),
            "timestamp": now.isoformat(),
            "overall_score": report_data.get("overall_score", 0),
            "symptoms": json.dumps(report_data.get("symptoms", []), ensure_ascii=False),
            "messages_count": report_data.get("messages_count", 0),
            "alert_level": alert_level,
            "alert_handled": "N" if alert_level in ["red", "yellow"] else "",
            "handled_by": "",
            "handled_at": ""
        }
        
        row = [row_data.get(col, "") for col in REPORT_COLUMNS]
        worksheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"儲存回報失敗: {e}")
        return False

def check_today_reported(patient_id):
    """檢查今天是否已回報"""
    today = datetime.now().strftime("%Y-%m-%d")
    reports = get_patient_reports(patient_id)
    for report in reports:
        if report.get("date") == today:
            return True
    return False

# ============================================
# 警示管理
# ============================================

def get_pending_alerts():
    """取得待處理警示"""
    reports = get_all_reports()
    pending = []
    for report in reports:
        if report.get("alert_level") in ["red", "yellow"] and report.get("alert_handled") != "Y":
            pending.append(report)
    return sorted(pending, key=lambda x: (
        0 if x.get("alert_level") == "red" else 1,
        x.get("timestamp", "")
    ), reverse=True)

def handle_alert(report_id, handled_by):
    """處理警示"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Reports", REPORT_COLUMNS)
        
        cell = worksheet.find(report_id)
        if not cell:
            return False
        
        row_number = cell.row
        
        # 更新處理狀態
        alert_handled_col = REPORT_COLUMNS.index("alert_handled") + 1
        handled_by_col = REPORT_COLUMNS.index("handled_by") + 1
        handled_at_col = REPORT_COLUMNS.index("handled_at") + 1
        
        worksheet.update_cell(row_number, alert_handled_col, "Y")
        worksheet.update_cell(row_number, handled_by_col, handled_by)
        worksheet.update_cell(row_number, handled_at_col, datetime.now().isoformat())
        
        return True
    except Exception as e:
        st.error(f"處理警示失敗: {e}")
        return False

# ============================================
# 衛教推送管理
# ============================================

def get_education_pushes(patient_id=None):
    """取得衛教推送紀錄"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return []
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Education", EDUCATION_COLUMNS)
        records = worksheet.get_all_records()
        
        if patient_id:
            records = [r for r in records if r.get("patient_id") == patient_id]
        
        return sorted(records, key=lambda x: x.get("pushed_at", ""), reverse=True)
    except Exception as e:
        st.error(f"讀取衛教推送失敗: {e}")
        return []

def push_education(patient_id, patient_name, material_id, material_title, category, push_type, pushed_by):
    """推送衛教"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Education", EDUCATION_COLUMNS)
        
        now = datetime.now()
        push_id = f"E{now.strftime('%Y%m%d%H%M%S')}"
        
        row_data = {
            "push_id": push_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "material_id": material_id,
            "material_title": material_title,
            "category": category,
            "push_type": push_type,
            "pushed_by": pushed_by,
            "pushed_at": now.isoformat(),
            "read_at": "",
            "status": "sent"
        }
        
        row = [row_data.get(col, "") for col in EDUCATION_COLUMNS]
        worksheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"推送衛教失敗: {e}")
        return False

def mark_education_read(push_id):
    """標記衛教已讀"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Education", EDUCATION_COLUMNS)
        
        cell = worksheet.find(push_id)
        if not cell:
            return False
        
        row_number = cell.row
        read_at_col = EDUCATION_COLUMNS.index("read_at") + 1
        status_col = EDUCATION_COLUMNS.index("status") + 1
        
        worksheet.update_cell(row_number, read_at_col, datetime.now().isoformat())
        worksheet.update_cell(row_number, status_col, "read")
        
        return True
    except Exception as e:
        st.error(f"標記已讀失敗: {e}")
        return False

# ============================================
# 介入紀錄管理
# ============================================

def get_interventions(patient_id=None):
    """取得介入紀錄"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return []
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Interventions", INTERVENTION_COLUMNS)
        records = worksheet.get_all_records()
        
        if patient_id:
            records = [r for r in records if r.get("patient_id") == patient_id]
        
        return sorted(records, key=lambda x: x.get("timestamp", ""), reverse=True)
    except Exception as e:
        st.error(f"讀取介入紀錄失敗: {e}")
        return []

def save_intervention(patient_id, patient_name, intervention_data, created_by):
    """儲存介入紀錄"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Interventions", INTERVENTION_COLUMNS)
        
        now = datetime.now()
        intervention_id = f"I{now.strftime('%Y%m%d%H%M%S')}"
        
        row_data = {
            "intervention_id": intervention_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "date": now.strftime("%Y-%m-%d"),
            "timestamp": now.isoformat(),
            "method": intervention_data.get("method", ""),
            "duration": intervention_data.get("duration", ""),
            "content": intervention_data.get("content", ""),
            "referral": intervention_data.get("referral", ""),
            "created_by": created_by
        }
        
        row = [row_data.get(col, "") for col in INTERVENTION_COLUMNS]
        worksheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"儲存介入紀錄失敗: {e}")
        return False

# ============================================
# 統計函數
# ============================================

def get_dashboard_stats():
    """取得儀表板統計"""
    patients = get_all_patients()
    reports = get_all_reports()
    today = datetime.now().strftime("%Y-%m-%d")
    
    today_reports = [r for r in reports if r.get("date") == today]
    pending_alerts = get_pending_alerts()
    
    # 計算各狀態病人數
    active_patients = [p for p in patients if p.get("status") not in ["pending_setup", "discharged"]]
    
    stats = {
        "total_patients": len(active_patients),
        "today_reports": len(today_reports),
        "report_rate": int(len(today_reports) / max(len(active_patients), 1) * 100),
        "pending_alerts": len(pending_alerts),
        "red_alerts": len([a for a in pending_alerts if a.get("alert_level") == "red"]),
        "yellow_alerts": len([a for a in pending_alerts if a.get("alert_level") == "yellow"]),
    }
    
    return stats

# ============================================
# 資料匯出
# ============================================

def export_patients_df():
    """匯出病人資料為 DataFrame"""
    patients = get_all_patients()
    return pd.DataFrame(patients)

def export_reports_df():
    """匯出回報資料為 DataFrame"""
    reports = get_all_reports()
    return pd.DataFrame(reports)
