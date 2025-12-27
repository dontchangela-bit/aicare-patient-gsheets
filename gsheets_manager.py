"""
AI-CARE Lung - Google Sheets 資料管理模組（快取優化版）
=====================================================

修正內容：
1. 加入 Streamlit 快取機制，減少 API 呼叫
2. 手機號碼/密碼格式標準化
3. 唯一 patient_id 產生
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime
import pandas as pd
import time

# ============================================
# 快取設定
# ============================================
CACHE_TTL = 60  # 快取時間：60 秒

# ============================================
# Google Sheets 設定
# ============================================

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
# 連線管理（使用快取）
# ============================================

@st.cache_resource(ttl=300)  # 連線快取 5 分鐘
def get_google_sheets_connection():
    """取得 Google Sheets 連線（使用快取）"""
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        
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
        spreadsheet_id = st.secrets.get("spreadsheet_id", "")
        if spreadsheet_id:
            return client.open_by_key(spreadsheet_id)
        else:
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
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(columns))
        worksheet.update('A1', [columns])
    return worksheet

# ============================================
# 工具函數
# ============================================

def normalize_phone(phone):
    """標準化手機號碼格式"""
    if phone is None:
        return ""
    phone_str = str(phone).strip()
    if '.' in phone_str:
        phone_str = phone_str.split('.')[0]
    if len(phone_str) == 9 and not phone_str.startswith('0'):
        phone_str = '0' + phone_str
    return phone_str

def normalize_password(password):
    """標準化密碼格式"""
    if password is None:
        return ""
    pwd_str = str(password).strip()
    if '.' in pwd_str:
        pwd_str = pwd_str.split('.')[0]
    return pwd_str

def clear_cache():
    """清除所有快取"""
    st.cache_data.clear()

# ============================================
# 病人資料管理（使用快取）
# ============================================

@st.cache_data(ttl=CACHE_TTL)
def get_all_patients_cached():
    """取得所有病人（快取版）"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return []
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Patients", PATIENT_COLUMNS)
        records = worksheet.get_all_records()
        
        today = datetime.now().date()
        for record in records:
            record["phone"] = normalize_phone(record.get("phone"))
            record["password"] = normalize_password(record.get("password"))
            
            if record.get("surgery_date"):
                try:
                    surgery_date = datetime.strptime(str(record["surgery_date"]), "%Y-%m-%d").date()
                    record["post_op_day"] = (today - surgery_date).days
                except:
                    record["post_op_day"] = 0
            else:
                record["post_op_day"] = 0
        
        return records
    except Exception as e:
        st.error(f"讀取病人資料失敗: {e}")
        return []

def get_all_patients():
    """取得所有病人（外部呼叫介面）"""
    return get_all_patients_cached()

def get_patient_by_phone(phone):
    """根據手機號碼查找病人"""
    patients = get_all_patients()
    input_phone = normalize_phone(phone)
    
    for patient in patients:
        db_phone = patient.get("phone", "")
        if db_phone == input_phone:
            return patient
        if db_phone.lstrip('0') == input_phone.lstrip('0') and input_phone.lstrip('0'):
            return patient
    
    return None

def get_patient_by_id(patient_id):
    """根據 ID 查找病人"""
    patients = get_all_patients()
    for patient in patients:
        if patient.get("patient_id") == patient_id:
            return patient
    return None

def generate_unique_patient_id(worksheet, phone):
    """產生唯一的病人 ID"""
    import random
    import string
    
    phone = normalize_phone(phone)
    
    existing_ids = set()
    try:
        records = worksheet.get_all_records()
        existing_ids = {r.get("patient_id", "") for r in records}
    except:
        pass
    
    for attempt in range(100):
        if attempt == 0:
            patient_id = f"P{phone[-4:]}{datetime.now().strftime('%m%d%H%M')}"
        elif attempt < 10:
            random_suffix = ''.join(random.choices(string.digits, k=3))
            patient_id = f"P{phone[-4:]}{datetime.now().strftime('%m%d')}{random_suffix}"
        else:
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            patient_id = f"P{random_suffix}"
        
        if patient_id not in existing_ids:
            return patient_id
    
    return f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"

def create_patient(patient_data):
    """建立新病人"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return None
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Patients", PATIENT_COLUMNS)
        
        phone = normalize_phone(patient_data.get("phone", ""))
        patient_id = generate_unique_patient_id(worksheet, phone)
        
        row = [
            patient_id,
            patient_data.get("name", ""),
            phone,
            str(patient_data.get("password", "")),
            patient_data.get("age", ""),
            patient_data.get("gender", ""),
            patient_data.get("surgery_type", "待設定"),
            patient_data.get("surgery_date", ""),
            patient_data.get("diagnosis", ""),
            patient_data.get("medical_record", ""),
            patient_data.get("status", "pending_setup"),
            0,
            patient_data.get("consent_agreed", "Y"),
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            "",
            ""
        ]
        
        worksheet.append_row(row)
        
        # 清除快取以便下次讀取新資料
        clear_cache()
        
        return patient_id
    except Exception as e:
        st.error(f"建立病人失敗: {e}")
        return None

def update_patient(patient_id, updates):
    """更新病人資料"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Patients", PATIENT_COLUMNS)
        records = worksheet.get_all_records()
        
        for idx, record in enumerate(records):
            if record.get("patient_id") == patient_id:
                row_num = idx + 2
                
                for key, value in updates.items():
                    if key in PATIENT_COLUMNS:
                        col_num = PATIENT_COLUMNS.index(key) + 1
                        worksheet.update_cell(row_num, col_num, value)
                
                # 清除快取
                clear_cache()
                return True
        return False
    except Exception as e:
        st.error(f"更新病人失敗: {e}")
        return False

# ============================================
# 回報紀錄管理（使用快取）
# ============================================

@st.cache_data(ttl=CACHE_TTL)
def get_all_reports_cached():
    """取得所有回報（快取版）"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return []
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Reports", REPORT_COLUMNS)
        return worksheet.get_all_records()
    except Exception as e:
        st.error(f"讀取回報失敗: {e}")
        return []

def get_all_reports():
    """取得所有回報（外部呼叫介面）"""
    return get_all_reports_cached()

def get_patient_reports(patient_id):
    """取得特定病人的回報"""
    reports = get_all_reports()
    return [r for r in reports if r.get("patient_id") == patient_id]

def check_today_reported(patient_id):
    """檢查今天是否已回報"""
    reports = get_patient_reports(patient_id)
    today = datetime.now().strftime("%Y-%m-%d")
    for report in reports:
        if report.get("date") == today:
            return True
    return False

def save_report(report_data):
    """儲存回報"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return None
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Reports", REPORT_COLUMNS)
        
        report_id = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        row = [
            report_id,
            report_data.get("patient_id", ""),
            report_data.get("patient_name", ""),
            report_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            report_data.get("timestamp", datetime.now().isoformat()),
            report_data.get("overall_score", 0),
            json.dumps(report_data.get("symptoms", {}), ensure_ascii=False),
            report_data.get("messages_count", 0),
            report_data.get("alert_level", "green"),
            "N",
            "",
            ""
        ]
        
        worksheet.append_row(row)
        clear_cache()
        return report_id
    except Exception as e:
        st.error(f"儲存回報失敗: {e}")
        return None

def get_today_reports():
    """取得今日所有回報"""
    reports = get_all_reports()
    today = datetime.now().strftime("%Y-%m-%d")
    return [r for r in reports if r.get("date") == today]

def get_pending_alerts():
    """取得待處理警示"""
    reports = get_all_reports()
    return [r for r in reports if r.get("alert_level") in ["red", "yellow"] and r.get("alert_handled") != "Y"]

def handle_alert(report_id, handler):
    """處理警示"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Reports", REPORT_COLUMNS)
        records = worksheet.get_all_records()
        
        for idx, record in enumerate(records):
            if record.get("report_id") == report_id:
                row_num = idx + 2
                worksheet.update_cell(row_num, REPORT_COLUMNS.index("alert_handled") + 1, "Y")
                worksheet.update_cell(row_num, REPORT_COLUMNS.index("handled_by") + 1, handler)
                worksheet.update_cell(row_num, REPORT_COLUMNS.index("handled_at") + 1, datetime.now().isoformat())
                clear_cache()
                return True
        return False
    except Exception as e:
        st.error(f"處理警示失敗: {e}")
        return False

# ============================================
# 衛教推送管理（使用快取）
# ============================================

@st.cache_data(ttl=CACHE_TTL)
def get_education_pushes_cached(patient_id=None):
    """取得衛教推送紀錄（快取版）"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return []
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Education", EDUCATION_COLUMNS)
        records = worksheet.get_all_records()
        
        if patient_id:
            return [r for r in records if r.get("patient_id") == patient_id]
        return records
    except Exception as e:
        st.error(f"讀取衛教紀錄失敗: {e}")
        return []

def get_education_pushes(patient_id=None):
    """取得衛教推送紀錄（外部呼叫介面）"""
    return get_education_pushes_cached(patient_id)

def push_education(push_data):
    """推送衛教"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return None
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Education", EDUCATION_COLUMNS)
        
        push_id = f"E{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        row = [
            push_id,
            push_data.get("patient_id", ""),
            push_data.get("patient_name", ""),
            push_data.get("material_id", ""),
            push_data.get("material_title", ""),
            push_data.get("category", ""),
            push_data.get("push_type", "manual"),
            push_data.get("pushed_by", ""),
            datetime.now().isoformat(),
            "",
            "sent"
        ]
        
        worksheet.append_row(row)
        clear_cache()
        return push_id
    except Exception as e:
        st.error(f"推送衛教失敗: {e}")
        return None

def mark_education_read(push_id):
    """標記衛教已讀"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Education", EDUCATION_COLUMNS)
        records = worksheet.get_all_records()
        
        for idx, record in enumerate(records):
            if record.get("push_id") == push_id:
                row_num = idx + 2
                worksheet.update_cell(row_num, EDUCATION_COLUMNS.index("read_at") + 1, datetime.now().isoformat())
                worksheet.update_cell(row_num, EDUCATION_COLUMNS.index("status") + 1, "read")
                clear_cache()
                return True
        return False
    except Exception as e:
        st.error(f"標記已讀失敗: {e}")
        return False

# ============================================
# 介入紀錄管理（使用快取）
# ============================================

@st.cache_data(ttl=CACHE_TTL)
def get_interventions_cached(patient_id=None):
    """取得介入紀錄（快取版）"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return []
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Interventions", INTERVENTION_COLUMNS)
        records = worksheet.get_all_records()
        
        if patient_id:
            return [r for r in records if r.get("patient_id") == patient_id]
        return records
    except Exception as e:
        st.error(f"讀取介入紀錄失敗: {e}")
        return []

def get_interventions(patient_id=None):
    """取得介入紀錄（外部呼叫介面）"""
    return get_interventions_cached(patient_id)

def save_intervention(intervention_data):
    """儲存介入紀錄"""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return None
    
    try:
        worksheet = get_or_create_worksheet(spreadsheet, "Interventions", INTERVENTION_COLUMNS)
        
        intervention_id = f"I{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        row = [
            intervention_id,
            intervention_data.get("patient_id", ""),
            intervention_data.get("patient_name", ""),
            intervention_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            intervention_data.get("timestamp", datetime.now().isoformat()),
            intervention_data.get("method", ""),
            intervention_data.get("duration", ""),
            intervention_data.get("content", ""),
            intervention_data.get("referral", ""),
            intervention_data.get("created_by", "")
        ]
        
        worksheet.append_row(row)
        clear_cache()
        return intervention_id
    except Exception as e:
        st.error(f"儲存介入紀錄失敗: {e}")
        return None

# ============================================
# 統計資料（使用快取）
# ============================================

@st.cache_data(ttl=CACHE_TTL)
def get_dashboard_stats():
    """取得儀表板統計"""
    patients = get_all_patients()
    reports = get_all_reports()
    today = datetime.now().strftime("%Y-%m-%d")
    
    today_reports = [r for r in reports if r.get("date") == today]
    pending_alerts = [r for r in reports if r.get("alert_level") in ["red", "yellow"] and r.get("alert_handled") != "Y"]
    
    stats = {
        "total_patients": len(patients),
        "active_patients": len([p for p in patients if p.get("status") not in ["discharged", "completed"]]),
        "today_reports": len(today_reports),
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

# ============================================
# 除錯用函數
# ============================================

def debug_login(phone, password):
    """除錯登入問題"""
    patients = get_all_patients()
    input_phone = normalize_phone(phone)
    input_pwd = normalize_password(password)
    
    debug_info = {
        "input_phone": input_phone,
        "input_password": input_pwd,
        "total_patients": len(patients),
        "matches": []
    }
    
    for p in patients:
        db_phone = p.get("phone", "")
        db_pwd = p.get("password", "")
        
        phone_match = (db_phone == input_phone) or (db_phone.lstrip('0') == input_phone.lstrip('0'))
        pwd_match = (db_pwd == input_pwd)
        
        if phone_match or db_phone[-4:] == input_phone[-4:]:
            debug_info["matches"].append({
                "patient_id": p.get("patient_id"),
                "name": p.get("name"),
                "db_phone": db_phone,
                "db_password": db_pwd,
                "phone_match": phone_match,
                "pwd_match": pwd_match,
                "status": p.get("status")
            })
    
    return debug_info
        
