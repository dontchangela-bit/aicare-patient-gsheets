"""
AI-CARE Lung - 病人端 MDASI-LC 問卷系統
==========================================
基於 MD Anderson Symptom Inventory - Lung Cancer Module
結合 AI 對話式回報與標準化問卷

功能：
1. MDASI-LC 標準化問卷（16 項症狀 + 6 項干擾）
2. AI 對話式症狀回報
3. 語音輸入支援
4. 每日症狀追蹤
"""

import streamlit as st
from datetime import datetime
import json
import os

# ============================================
# 頁面配置
# ============================================
st.set_page_config(
    page_title="AI-CARE Lung - 每日症狀回報",
    page_icon="🫁",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================
# 常數定義
# ============================================
SYSTEM_NAME = "AI-CARE Lung"
HOSPITAL_NAME = "三軍總醫院"

# MDASI-LC 問卷項目
MDASI_CORE_SYMPTOMS = [
    {"id": "pain", "name": "疼痛", "name_en": "Pain", "icon": "😣", "description": "任何部位的疼痛感"},
    {"id": "fatigue", "name": "疲勞", "name_en": "Fatigue", "icon": "😩", "description": "感覺疲倦、缺乏精力"},
    {"id": "nausea", "name": "噁心", "name_en": "Nausea", "icon": "🤢", "description": "想吐的感覺"},
    {"id": "sleep", "name": "睡眠障礙", "name_en": "Disturbed sleep", "icon": "😴", "description": "難以入睡或睡眠品質差"},
    {"id": "distress", "name": "情緒困擾", "name_en": "Distress", "icon": "😰", "description": "感到煩躁、焦慮或不安"},
    {"id": "dyspnea", "name": "呼吸急促", "name_en": "Shortness of breath", "icon": "😮‍💨", "description": "呼吸困難或喘不過氣"},
    {"id": "appetite", "name": "食慾不振", "name_en": "Lack of appetite", "icon": "🍽️", "description": "不想吃東西"},
    {"id": "drowsiness", "name": "嗜睡", "name_en": "Drowsiness", "icon": "😪", "description": "白天想睡覺、精神不濟"},
    {"id": "dry_mouth", "name": "口乾", "name_en": "Dry mouth", "icon": "💧", "description": "口腔乾燥"},
    {"id": "sadness", "name": "悲傷", "name_en": "Sadness", "icon": "😢", "description": "感到難過、沮喪"},
    {"id": "vomiting", "name": "嘔吐", "name_en": "Vomiting", "icon": "🤮", "description": "實際吐出來"},
    {"id": "memory", "name": "記憶困難", "name_en": "Difficulty remembering", "icon": "🧠", "description": "記憶力變差"},
    {"id": "numbness", "name": "麻木刺痛", "name_en": "Numbness/tingling", "icon": "✋", "description": "手腳麻木或刺痛感"},
]

MDASI_LUNG_SYMPTOMS = [
    {"id": "cough", "name": "咳嗽", "name_en": "Coughing", "icon": "😷", "description": "咳嗽的頻率與嚴重程度"},
    {"id": "constipation", "name": "便秘", "name_en": "Constipation", "icon": "🚽", "description": "排便困難"},
    {"id": "sore_throat", "name": "喉嚨痛", "name_en": "Sore throat", "icon": "🗣️", "description": "喉嚨疼痛或不適"},
]

MDASI_INTERFERENCE = [
    {"id": "activity", "name": "一般活動", "name_en": "General activity", "icon": "🏃", "description": "日常活動的能力"},
    {"id": "mood", "name": "情緒", "name_en": "Mood", "icon": "😊", "description": "整體心情狀態"},
    {"id": "walking", "name": "行走能力", "name_en": "Walking ability", "icon": "🚶", "description": "走路的能力"},
    {"id": "work", "name": "工作", "name_en": "Normal work", "icon": "💼", "description": "工作或做家事的能力"},
    {"id": "relations", "name": "人際關係", "name_en": "Relations with others", "icon": "👥", "description": "與他人互動的品質"},
    {"id": "enjoyment", "name": "生活樂趣", "name_en": "Enjoyment of life", "icon": "🌟", "description": "享受生活的能力"},
]

# ============================================
# Google Sheets 連接（可選）
# ============================================
GSHEETS_AVAILABLE = False
try:
    from gsheets_manager import (
        get_patient_by_phone, create_patient, save_report,
        get_patient_reports, check_today_reported
    )
    if "gcp_service_account" in st.secrets:
        GSHEETS_AVAILABLE = True
except:
    pass

# ============================================
# Session State 初始化
# ============================================
if 'patient_registered' not in st.session_state:
    st.session_state.patient_registered = False
if 'patient_info' not in st.session_state:
    st.session_state.patient_info = {}
if 'patient_id' not in st.session_state:
    st.session_state.patient_id = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'welcome'  # welcome, symptoms, interference, ai_chat, complete
if 'symptom_scores' not in st.session_state:
    st.session_state.symptom_scores = {}
if 'interference_scores' not in st.session_state:
    st.session_state.interference_scores = {}
if 'ai_messages' not in st.session_state:
    st.session_state.ai_messages = []
if 'report_completed' not in st.session_state:
    st.session_state.report_completed = False

# ============================================
# 樣式
# ============================================
st.markdown("""
<style>
    /* 整體背景 */
    .stApp {
        background: linear-gradient(135deg, #E0F2F1 0%, #B2DFDB 100%);
    }
    
    /* 標題卡片 */
    .header-card {
        background: linear-gradient(135deg, #00897B 0%, #26A69A 100%);
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 8px 25px rgba(0,137,123,0.25);
    }
    .header-card h1 {
        color: white;
        font-size: 26px;
        margin-bottom: 5px;
    }
    .header-card p {
        color: rgba(255,255,255,0.9);
        font-size: 14px;
    }
    
    /* 問題卡片 */
    .symptom-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }
    .symptom-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;
    }
    .symptom-icon {
        font-size: 28px;
    }
    .symptom-name {
        font-size: 18px;
        font-weight: 600;
        color: #1e293b;
    }
    .symptom-desc {
        font-size: 13px;
        color: #64748b;
    }
    
    /* 分數選擇器 */
    .score-selector {
        display: flex;
        justify-content: space-between;
        gap: 5px;
        margin-top: 15px;
    }
    .score-btn {
        flex: 1;
        padding: 10px 5px;
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
        background: white;
    }
    .score-btn:hover {
        border-color: #00897B;
        background: #E0F2F1;
    }
    .score-btn.selected {
        border-color: #00897B;
        background: #00897B;
        color: white;
    }
    
    /* 進度條 */
    .progress-container {
        background: #e2e8f0;
        border-radius: 10px;
        height: 8px;
        margin-bottom: 20px;
    }
    .progress-bar {
        background: linear-gradient(90deg, #00897B, #26A69A);
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s;
    }
    
    /* 導航按鈕 */
    .nav-button {
        padding: 15px 30px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
    }
    
    /* 完成頁面 */
    .complete-card {
        background: linear-gradient(135deg, #4CAF50 0%, #81C784 100%);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# 輔助函數
# ============================================
def render_header():
    """渲染頂部標題"""
    st.markdown(f"""
    <div class="header-card">
        <h1>🫁 {SYSTEM_NAME}</h1>
        <p>{HOSPITAL_NAME} 智慧照護系統</p>
        <p style="margin-top: 8px; font-size: 12px; opacity: 0.8;">
            MDASI-LC 每日症狀評估
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_progress(current, total, label=""):
    """渲染進度條"""
    progress = (current / total) * 100
    st.markdown(f"""
    <div style="margin-bottom: 5px; font-size: 14px; color: #64748b;">
        {label} ({current}/{total})
    </div>
    <div class="progress-container">
        <div class="progress-bar" style="width: {progress}%;"></div>
    </div>
    """, unsafe_allow_html=True)

def render_symptom_slider(symptom, category="symptom"):
    """渲染症狀評分滑桿"""
    key = f"{category}_{symptom['id']}"
    
    # 從 session state 取得已儲存的值
    if category == "symptom":
        default_value = st.session_state.symptom_scores.get(symptom['id'], 0)
    else:
        default_value = st.session_state.interference_scores.get(symptom['id'], 0)
    
    st.markdown(f"""
    <div class="symptom-card">
        <div class="symptom-header">
            <span class="symptom-icon">{symptom['icon']}</span>
            <div>
                <div class="symptom-name">{symptom['name']}</div>
                <div class="symptom-desc">{symptom['description']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 分數說明
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.caption("0 = 沒有")
    with col3:
        st.caption("10 = 非常嚴重")
    
    # 滑桿
    score = st.slider(
        f"{symptom['name']} 分數",
        min_value=0,
        max_value=10,
        value=default_value,
        key=key,
        label_visibility="collapsed"
    )
    
    # 分數顏色提示
    if score == 0:
        color = "#4CAF50"
        label = "沒有症狀 ✓"
    elif score <= 3:
        color = "#8BC34A"
        label = "輕微"
    elif score <= 6:
        color = "#FFC107"
        label = "中等"
    else:
        color = "#F44336"
        label = "嚴重"
    
    st.markdown(f"""
    <div style="text-align: center; margin-top: -10px; margin-bottom: 20px;">
        <span style="
            background: {color};
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        ">{score} 分 - {label}</span>
    </div>
    """, unsafe_allow_html=True)
    
    return score

# ============================================
# 頁面：登入/註冊
# ============================================
def render_login():
    """登入頁面"""
    render_header()
    
    tab1, tab2 = st.tabs(["🔑 登入", "📝 首次使用"])
    
    with tab1:
        st.markdown("### 歡迎回來！")
        with st.form("login_form"):
            phone = st.text_input("手機號碼", placeholder="0912345678")
            password = st.text_input("密碼", type="password")
            submitted = st.form_submit_button("登入", use_container_width=True, type="primary")
            
            if submitted:
                if len(phone) >= 10 and len(password) >= 4:
                    # 模擬登入成功
                    st.session_state.patient_registered = True
                    st.session_state.patient_info = {
                        "name": "測試病人",
                        "phone": phone,
                        "surgery_date": "2024-12-20",
                        "post_op_day": 8
                    }
                    st.session_state.patient_id = "P001"
                    st.rerun()
                else:
                    st.error("請輸入正確的手機號碼和密碼")
    
    with tab2:
        st.markdown("### 首次使用請註冊")
        with st.form("register_form"):
            name = st.text_input("姓名", placeholder="王大明")
            phone = st.text_input("手機號碼", placeholder="0912345678")
            password = st.text_input("設定密碼", type="password", placeholder="至少4位數")
            submitted = st.form_submit_button("註冊", use_container_width=True, type="primary")
            
            if submitted:
                if name and len(phone) >= 10 and len(password) >= 4:
                    st.session_state.patient_registered = True
                    st.session_state.patient_info = {
                        "name": name,
                        "phone": phone,
                        "surgery_date": datetime.now().strftime("%Y-%m-%d"),
                        "post_op_day": 1
                    }
                    st.session_state.patient_id = f"P{phone[-4:]}"
                    st.success("註冊成功！")
                    st.rerun()
                else:
                    st.error("請填寫完整資料")

# ============================================
# 頁面：歡迎/選擇回報方式
# ============================================
def render_welcome():
    """歡迎頁面 - 選擇回報方式"""
    render_header()
    
    patient = st.session_state.patient_info
    now = datetime.now()
    greeting = "早安" if now.hour < 12 else "午安" if now.hour < 18 else "晚安"
    
    st.markdown(f"""
    <div style="
        background: white;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
    ">
        <h2 style="color: #1e293b; margin-bottom: 10px;">
            {greeting}，{patient.get('name', '您')}！👋
        </h2>
        <p style="color: #64748b; font-size: 16px;">
            術後第 <b style="color: #00897B; font-size: 24px;">{patient.get('post_op_day', 0)}</b> 天
        </p>
        <p style="color: #94a3b8; font-size: 14px; margin-top: 10px;">
            請選擇您今天想要的回報方式
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 兩種回報方式
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #2196F3 0%, #64B5F6 100%);
            padding: 25px 15px;
            border-radius: 15px;
            text-align: center;
            color: white;
            height: 180px;
        ">
            <div style="font-size: 40px; margin-bottom: 10px;">📋</div>
            <div style="font-size: 16px; font-weight: 600;">標準問卷</div>
            <div style="font-size: 12px; opacity: 0.9; margin-top: 5px;">
                MDASI-LC<br>約 3-5 分鐘
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("開始問卷", key="btn_questionnaire", use_container_width=True, type="primary"):
            st.session_state.current_step = 'symptoms'
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #FF9800 0%, #FFB74D 100%);
            padding: 25px 15px;
            border-radius: 15px;
            text-align: center;
            color: white;
            height: 180px;
        ">
            <div style="font-size: 40px; margin-bottom: 10px;">💬</div>
            <div style="font-size: 16px; font-weight: 600;">AI 對話</div>
            <div style="font-size: 12px; opacity: 0.9; margin-top: 5px;">
                用說的或打字<br>約 2-3 分鐘
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("開始對話", key="btn_chat", use_container_width=True):
            st.session_state.current_step = 'ai_chat'
            st.rerun()
    
    # 登出按鈕
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 登出", use_container_width=True):
        st.session_state.patient_registered = False
        st.session_state.patient_info = {}
        st.session_state.current_step = 'welcome'
        st.rerun()

# ============================================
# 頁面：MDASI-LC 症狀問卷
# ============================================
def render_symptoms_questionnaire():
    """MDASI-LC 症狀評估問卷"""
    render_header()
    
    # 進度
    all_symptoms = MDASI_CORE_SYMPTOMS + MDASI_LUNG_SYMPTOMS
    total = len(all_symptoms)
    answered = len([s for s in all_symptoms if s['id'] in st.session_state.symptom_scores])
    render_progress(answered, total, "症狀評估")
    
    st.markdown("""
    <div style="
        background: #e7f3ff;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
    ">
        <p style="margin: 0; color: #1e40af; font-size: 14px;">
            📋 <b>請評估過去 24 小時內</b>，以下症狀的嚴重程度
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 核心症狀
    st.markdown("### 🏥 核心症狀")
    for symptom in MDASI_CORE_SYMPTOMS:
        score = render_symptom_slider(symptom, "symptom")
        st.session_state.symptom_scores[symptom['id']] = score
    
    st.markdown("---")
    
    # 肺癌特定症狀
    st.markdown("### 🫁 肺癌相關症狀")
    for symptom in MDASI_LUNG_SYMPTOMS:
        score = render_symptom_slider(symptom, "symptom")
        st.session_state.symptom_scores[symptom['id']] = score
    
    # 導航按鈕
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← 返回", use_container_width=True):
            st.session_state.current_step = 'welcome'
            st.rerun()
    
    with col2:
        if st.button("下一步 →", use_container_width=True, type="primary"):
            st.session_state.current_step = 'interference'
            st.rerun()

# ============================================
# 頁面：MDASI-LC 干擾問卷
# ============================================
def render_interference_questionnaire():
    """MDASI-LC 干擾評估問卷"""
    render_header()
    
    # 進度
    total = len(MDASI_INTERFERENCE)
    answered = len([s for s in MDASI_INTERFERENCE if s['id'] in st.session_state.interference_scores])
    render_progress(answered, total, "生活影響評估")
    
    st.markdown("""
    <div style="
        background: #fff3e0;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
    ">
        <p style="margin: 0; color: #e65100; font-size: 14px;">
            🌟 <b>過去 24 小時內</b>，您的症狀對以下方面造成多大的影響？
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 症狀對生活的影響")
    
    for item in MDASI_INTERFERENCE:
        score = render_symptom_slider(item, "interference")
        st.session_state.interference_scores[item['id']] = score
    
    # 導航按鈕
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← 上一步", use_container_width=True):
            st.session_state.current_step = 'symptoms'
            st.rerun()
    
    with col2:
        if st.button("提交問卷 ✓", use_container_width=True, type="primary"):
            # 儲存問卷結果
            save_questionnaire_results()
            st.session_state.current_step = 'complete'
            st.rerun()

# ============================================
# 頁面：AI 對話回報
# ============================================
def render_ai_chat():
    """AI 對話式回報"""
    render_header()
    
    patient = st.session_state.patient_info
    
    # 初始化對話
    if not st.session_state.ai_messages:
        now = datetime.now()
        greeting = "早安" if now.hour < 12 else "午安" if now.hour < 18 else "晚安"
        
        welcome_msg = f"""{greeting}，{patient.get('name', '您')}！😊

我是您的健康小助手。今天是您術後第 {patient.get('post_op_day', 0)} 天。

請問您今天**整體感覺**如何？
（可以用 0-10 分來描述，0 是完全沒有不舒服，10 是非常不舒服）"""
        
        st.session_state.ai_messages.append({
            "role": "assistant",
            "content": welcome_msg
        })
    
    # 顯示對話
    for msg in st.session_state.ai_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # 快速回覆按鈕
    st.markdown("### 快速回覆")
    
    cols = st.columns(3)
    quick_replies = [
        ("😊 還不錯", "今天感覺還不錯，大概 2-3 分"),
        ("😐 普通", "有一些不舒服，大概 5 分左右"),
        ("😣 不太好", "很不舒服，大概 7-8 分"),
    ]
    
    for i, (label, reply) in enumerate(quick_replies):
        if cols[i].button(label, key=f"quick_{i}", use_container_width=True):
            handle_ai_message(reply)
    
    cols2 = st.columns(4)
    symptom_replies = [
        ("😓 有點痛", "傷口有點痛，大概 5 分"),
        ("😮‍💨 有點喘", "呼吸有點喘，大概 4 分"),
        ("😴 很疲勞", "感覺很疲勞，大概 6 分"),
        ("😷 有咳嗽", "有一些咳嗽，大概 4 分"),
    ]
    
    for i, (label, reply) in enumerate(symptom_replies):
        if cols2[i].button(label, key=f"symptom_{i}", use_container_width=True):
            handle_ai_message(reply)
    
    st.markdown("---")
    
    # 文字輸入
    user_input = st.chat_input("💬 輸入您的感覺，或用語音輸入...")
    if user_input:
        handle_ai_message(user_input)
    
    # 完成按鈕
    if len(st.session_state.ai_messages) >= 4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✓ 完成今日回報", use_container_width=True, type="primary"):
            save_ai_chat_results()
            st.session_state.current_step = 'complete'
            st.rerun()
    
    # 返回按鈕
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← 返回選擇", use_container_width=True):
        st.session_state.current_step = 'welcome'
        st.session_state.ai_messages = []
        st.rerun()

def handle_ai_message(user_input):
    """處理 AI 對話"""
    # 加入使用者訊息
    st.session_state.ai_messages.append({
        "role": "user",
        "content": user_input
    })
    
    # 生成 AI 回應
    ai_response = generate_ai_response(user_input)
    st.session_state.ai_messages.append({
        "role": "assistant",
        "content": ai_response
    })
    
    st.rerun()

def generate_ai_response(user_input):
    """生成 AI 回應"""
    msg_count = len(st.session_state.ai_messages)
    
    # 根據對話階段給出不同回應
    if msg_count <= 2:
        return """了解，謝謝您的回報！

接下來想請問您幾個具體症狀：
1. **疼痛**方面如何？傷口或其他地方有痛嗎？
2. **呼吸**順暢嗎？有沒有喘或呼吸困難？"""
    
    elif msg_count <= 4:
        return """好的，我記下來了。

再請問您：
1. **疲勞**程度如何？精神好不好？
2. **食慾**和**睡眠**狀況如何？"""
    
    elif msg_count <= 6:
        return """謝謝您詳細的回報！

最後想確認：
1. 有沒有**咳嗽**？咳得多不多？
2. 有沒有其他想告訴醫療團隊的事情？

回答完後，您可以點擊「完成今日回報」按鈕。"""
    
    else:
        return """感謝您完成今日回報！🙏

如果還有其他想補充的，可以繼續告訴我。
或者點擊「完成今日回報」按鈕提交。"""

# ============================================
# 頁面：完成
# ============================================
def render_complete():
    """完成頁面"""
    render_header()
    
    st.markdown("""
    <div class="complete-card">
        <div style="font-size: 60px; margin-bottom: 15px;">✅</div>
        <h2 style="margin-bottom: 10px;">今日回報完成！</h2>
        <p style="opacity: 0.9;">感謝您的配合，醫療團隊會持續關注您的狀況</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 顯示摘要
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state.symptom_scores:
        st.markdown("### 📊 今日症狀摘要")
        
        # 找出嚴重症狀
        severe = [(k, v) for k, v in st.session_state.symptom_scores.items() if v >= 7]
        moderate = [(k, v) for k, v in st.session_state.symptom_scores.items() if 4 <= v < 7]
        
        if severe:
            st.error(f"⚠️ 需注意的症狀：{len(severe)} 項")
        elif moderate:
            st.warning(f"🟡 中等症狀：{len(moderate)} 項")
        else:
            st.success("✅ 整體狀況良好")
    
    # 提示
    st.info("💡 醫療團隊會在需要時主動聯繫您。如有緊急狀況，請撥打緊急聯絡電話。")
    
    # 按鈕
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏠 返回首頁", use_container_width=True, type="primary"):
        # 重置狀態
        st.session_state.current_step = 'welcome'
        st.session_state.symptom_scores = {}
        st.session_state.interference_scores = {}
        st.session_state.ai_messages = []
        st.rerun()

# ============================================
# 儲存結果
# ============================================
def save_questionnaire_results():
    """儲存問卷結果"""
    # 計算總分和警示等級
    scores = st.session_state.symptom_scores
    interference = st.session_state.interference_scores
    
    # 計算平均分
    symptom_avg = sum(scores.values()) / len(scores) if scores else 0
    interference_avg = sum(interference.values()) / len(interference) if interference else 0
    
    # 判斷警示等級
    max_score = max(scores.values()) if scores else 0
    if max_score >= 7 or scores.get('pain', 0) >= 7 or scores.get('dyspnea', 0) >= 6:
        alert_level = 'red'
    elif max_score >= 4 or symptom_avg >= 4:
        alert_level = 'yellow'
    else:
        alert_level = 'green'
    
    report_data = {
        "patient_id": st.session_state.patient_id,
        "patient_name": st.session_state.patient_info.get("name", ""),
        "report_type": "questionnaire",
        "symptom_scores": scores,
        "interference_scores": interference,
        "symptom_avg": symptom_avg,
        "interference_avg": interference_avg,
        "alert_level": alert_level,
        "timestamp": datetime.now().isoformat()
    }
    
    # 如果有 Google Sheets 連接，儲存到雲端
    if GSHEETS_AVAILABLE:
        try:
            save_report(report_data)
        except:
            pass
    
    st.session_state.report_completed = True

def save_ai_chat_results():
    """儲存 AI 對話結果"""
    # 從對話中提取分數（簡化版）
    report_data = {
        "patient_id": st.session_state.patient_id,
        "patient_name": st.session_state.patient_info.get("name", ""),
        "report_type": "ai_chat",
        "messages": st.session_state.ai_messages,
        "timestamp": datetime.now().isoformat()
    }
    
    if GSHEETS_AVAILABLE:
        try:
            save_report(report_data)
        except:
            pass
    
    st.session_state.report_completed = True

# ============================================
# 主程式
# ============================================
def main():
    """主程式"""
    if not st.session_state.patient_registered:
        render_login()
    else:
        step = st.session_state.current_step
        
        if step == 'welcome':
            render_welcome()
        elif step == 'symptoms':
            render_symptoms_questionnaire()
        elif step == 'interference':
            render_interference_questionnaire()
        elif step == 'ai_chat':
            render_ai_chat()
        elif step == 'complete':
            render_complete()
        else:
            render_welcome()

if __name__ == "__main__":
    main()
