"""
AI-CARE Lung - 病人端（美化版）
=============================

修正內容：
1. 登入驗證邏輯修正
2. 手機號碼/密碼格式問題
3. UI 美化 - 親切友善介面
"""

import streamlit as st
from datetime import datetime, timedelta
import json

# ============================================
# 設定
# ============================================
SYSTEM_NAME = "AI-CARE Lung"
HOSPITAL_NAME = "三軍總醫院"

# OpenAI 設定
try:
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
except:
    OPENAI_API_KEY = ""

DEFAULT_MODEL = "gpt-4o-mini"

# Google Sheets 資料管理
try:
    from gsheets_manager import (
        get_all_patients, get_patient_by_phone, get_patient_by_id,
        create_patient, update_patient,
        get_patient_reports, save_report, check_today_reported,
        get_education_pushes, mark_education_read,
        normalize_phone, normalize_password, debug_login
    )
    GSHEETS_AVAILABLE = True
except Exception as e:
    GSHEETS_AVAILABLE = False
    st.error(f"Google Sheets 模組載入失敗: {e}")

# OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except:
    OPENAI_AVAILABLE = False

# UI 美化模組
try:
    from ui_styles import (
        init_patient_style, render_welcome, render_symptom_question,
        render_score_display, render_chat_message, render_completion_message,
        render_progress, render_education_card, render_tip_box,
        render_emergency_contact, COLORS
    )
    UI_STYLES_AVAILABLE = True
except:
    UI_STYLES_AVAILABLE = False

# ============================================
# 頁面設定
# ============================================
st.set_page_config(
    page_title=f"{SYSTEM_NAME} - 健康回報",
    page_icon="🫁",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 套用美化樣式
if UI_STYLES_AVAILABLE:
    init_patient_style()
else:
    # 備用 CSS
    st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stButton > button { border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# Session State
# ============================================
if 'patient_registered' not in st.session_state:
    st.session_state.patient_registered = False

if 'patient_info' not in st.session_state:
    st.session_state.patient_info = {}

if 'patient_id' not in st.session_state:
    st.session_state.patient_id = ""

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'current_score' not in st.session_state:
    st.session_state.current_score = 0

if 'symptoms_reported' not in st.session_state:
    st.session_state.symptoms_reported = {}

if 'report_completed' not in st.session_state:
    st.session_state.report_completed = False

if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# ============================================
# System Prompt
# ============================================
SYSTEM_PROMPT = """你是三軍總醫院「AI-CARE Lung」智慧肺癌術後照護系統的 AI 健康助手。

## 角色設定
- 親切、溫暖、有耐心的健康照護助手
- 專門協助肺癌手術後的病人進行每日症狀回報
- 像一位關心病人的資深護理師

## 對話原則
- 使用繁體中文，語氣溫暖親切
- 句子簡短清楚，適合年長者閱讀
- 一次只問一個問題
- 適度使用 emoji（但不過度）
- 使用「您」而非「你」

## 症狀評估（0-10分）
- 0分 = 完全沒有症狀
- 1-3分 = 輕微
- 4-6分 = 中度
- 7-10分 = 嚴重

## 追蹤重點
1. 呼吸困難/喘
2. 疼痛（傷口、胸痛）
3. 咳嗽/痰
4. 疲勞
5. 睡眠
6. 食慾
7. 情緒

## 回應格式
回應要簡短，不超過 100 字。詢問症狀時要具體。"""

# ============================================
# 工具函數
# ============================================
def calculate_post_op_day(surgery_date_str):
    """計算術後天數"""
    if not surgery_date_str:
        return 0
    try:
        surgery_date = datetime.strptime(str(surgery_date_str), "%Y-%m-%d").date()
        return (datetime.now().date() - surgery_date).days
    except:
        return 0

# ============================================
# 註冊/登入頁面（美化版）
# ============================================
def render_registration():
    """病人註冊/登入頁面（美化版）"""
    
    # 顯示 Logo（使用 st.image 而非 HTML）
    try:
        import os
        logo_paths = [
            ("tsgh_logo.png", "dmc_logo.png"),
            ("./tsgh_logo.png", "./dmc_logo.png"),
        ]
        
        for tsgh_path, dmc_path in logo_paths:
            if os.path.exists(tsgh_path) and os.path.exists(dmc_path):
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    logo_col1, logo_col2 = st.columns(2)
                    with logo_col1:
                        st.image(tsgh_path, width=120)
                    with logo_col2:
                        st.image(dmc_path, width=120)
                break
    except:
        pass
    
    # 標題區
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #00897B 0%, #26A69A 100%);
        padding: 30px 20px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 8px 30px rgba(0,137,123,0.25);
    ">
        <h1 style="color: white; font-size: 28px; margin-bottom: 5px;">🫁 {SYSTEM_NAME}</h1>
        <p style="color: rgba(255,255,255,0.9); font-size: 15px;">{HOSPITAL_NAME} 智慧照護系統</p>
        <p style="color: rgba(255,255,255,0.7); font-size: 13px; margin-top: 8px;">
            讓我們一起守護您的健康 ❤️
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 首次使用", "🔑 我已註冊"])
    
    # === 首次使用（註冊）===
    with tab1:
        st.markdown("### 歡迎使用！請填寫基本資料")
        st.caption("📋 手術相關資訊將由個案管理師協助設定")
        
        with st.form("registration_form"):
            name = st.text_input("姓名 *", placeholder="例如：王大明")
            phone = st.text_input("手機號碼 *", placeholder="例如：0912345678")
            
            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("設定密碼 *", type="password", placeholder="至少4位數")
            with col2:
                password_confirm = st.text_input("確認密碼 *", type="password", placeholder="再輸入一次密碼")
            
            col3, col4 = st.columns(2)
            with col3:
                age = st.number_input("年齡", min_value=18, max_value=120, value=65)
            with col4:
                gender = st.selectbox("性別", ["男", "女"])
            
            st.markdown("---")
            
            # 同意條款說明
            st.markdown("""
            ##### 📋 研究說明與同意書
            
            本系統為**三軍總醫院「AI-CARE Lung 肺癌術後照護研究計畫」**的一部分。
            
            **參與內容：**
            - 每日透過本系統回報您的健康狀況
            - 系統會使用 AI 協助評估您的症狀
            - 個案管理師會根據回報資料提供照護建議
            
            **資料保護：**
            - 您的個人資料將依法保密
            - 僅供醫療照護及研究分析使用
            - 您可隨時要求退出研究
            
            如有任何疑問，請洽詢您的主治醫師或個案管理師。
            """)
            
            consent = st.checkbox("✅ 我已閱讀並同意參與本研究計畫")
            
            submit = st.form_submit_button("✅ 註冊", use_container_width=True, type="primary")
            
            if submit:
                if not name:
                    st.error("請填寫姓名")
                elif not phone or len(phone) < 9:
                    st.error("請填寫正確的手機號碼")
                elif not password or len(password) < 4:
                    st.error("請設定至少4位數的密碼")
                elif password != password_confirm:
                    st.error("兩次密碼輸入不一致")
                elif not consent:
                    st.error("請閱讀並勾選同意參與研究計畫")
                else:
                    # 檢查是否已註冊
                    existing = get_patient_by_phone(phone) if GSHEETS_AVAILABLE else None
                    
                    if existing:
                        st.error("此手機號碼已註冊，請直接登入")
                    else:
                        # 建立新病人
                        if GSHEETS_AVAILABLE:
                            patient_id = create_patient({
                                "name": name,
                                "phone": phone,
                                "password": password,
                                "age": age,
                                "gender": gender,
                                "status": "pending_setup"
                            })
                            
                            if patient_id:
                                st.session_state.patient_info = {
                                    "patient_id": patient_id,
                                    "name": name,
                                    "phone": phone,
                                    "age": age,
                                    "gender": gender,
                                    "surgery_type": "待設定",
                                    "surgery_date": "",
                                    "post_op_day": 0,
                                    "status": "pending_setup"
                                }
                                st.session_state.patient_id = patient_id
                                st.session_state.patient_registered = True
                                
                                st.success(f"✅ 註冊成功！您的病人編號是 {patient_id}")
                                st.info("📋 請聯繫個案管理師完成手術資訊設定後，即可開始使用")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("註冊失敗，請稍後再試")
                        else:
                            st.error("系統暫時無法連線，請稍後再試")
    
    # === 我已註冊（登入）===（修正版）
    with tab2:
        st.markdown("### 歡迎回來！")
        
        with st.form("login_form"):
            login_phone = st.text_input("手機號碼", placeholder="輸入註冊時的手機號碼")
            login_password = st.text_input("密碼", type="password", placeholder="輸入您的密碼")
            
            login_submit = st.form_submit_button("🔑 登入", use_container_width=True, type="primary")
            
            if login_submit:
                if not login_phone or not login_password:
                    st.error("請輸入手機號碼和密碼")
                else:
                    if not GSHEETS_AVAILABLE:
                        st.error("系統暫時無法連線，請稍後再試")
                    else:
                        # 除錯模式：顯示詳細資訊
                        if st.session_state.debug_mode:
                            debug_info = debug_login(login_phone, login_password)
                            st.write("### 🔍 除錯資訊")
                            st.json(debug_info)
                        
                        # 查找病人
                        patient = get_patient_by_phone(login_phone)
                        
                        if patient:
                            # 標準化密碼比對
                            input_pwd = normalize_password(login_password)
                            db_pwd = patient.get("password", "")
                            
                            if st.session_state.debug_mode:
                                st.write(f"輸入密碼: `{input_pwd}`")
                                st.write(f"資料庫密碼: `{db_pwd}`")
                                st.write(f"比對結果: `{input_pwd == db_pwd}`")
                            
                            if db_pwd == input_pwd:
                                # 登入成功
                                surgery_date = patient.get("surgery_date", "")
                                post_op_day = calculate_post_op_day(surgery_date)
                                
                                st.session_state.patient_info = {
                                    "patient_id": patient.get("patient_id"),
                                    "name": patient.get("name"),
                                    "phone": patient.get("phone"),
                                    "age": patient.get("age", 65),
                                    "gender": patient.get("gender", ""),
                                    "surgery_type": patient.get("surgery_type", "待設定"),
                                    "surgery_date": surgery_date,
                                    "post_op_day": post_op_day,
                                    "status": patient.get("status", "normal")
                                }
                                st.session_state.patient_id = patient.get("patient_id")
                                st.session_state.patient_registered = True
                                
                                # 檢查今天是否已回報
                                if check_today_reported(patient.get("patient_id")):
                                    st.session_state.report_completed = True
                                
                                st.success("✅ 登入成功！")
                                st.rerun()
                            else:
                                st.error("❌ 密碼錯誤")
                        else:
                            st.error("❌ 找不到此帳號，請確認手機號碼或先註冊")
                            
                            # 除錯模式：列出所有病人的手機號碼後4碼
                            if st.session_state.debug_mode:
                                patients = get_all_patients()
                                st.write("### 資料庫中的病人")
                                for p in patients:
                                    st.write(f"- {p.get('name')}: {p.get('phone')}")
        
        st.caption("忘記密碼？請聯繫個案管理師")

# ============================================
# 待設定狀態頁面
# ============================================
def render_pending_setup():
    """待設定狀態頁面"""
    st.markdown(f"""
    <div style="text-align: center; padding: 40px 0;">
        <div style="font-size: 64px; margin-bottom: 16px;">⏳</div>
        <h2 style="color: #1e293b;">帳號待設定</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("""
    **您的帳號已建立，但尚未完成設定。**
    
    請聯繫個案管理師協助設定以下資訊：
    - 手術日期
    - 手術類型
    - 其他臨床資料
    
    設定完成後即可開始使用每日回報功能。
    """)
    
    patient_info = st.session_state.patient_info
    st.markdown(f"""
    **您的資料：**
    - 姓名：{patient_info.get('name', '')}
    - 病人編號：{patient_info.get('patient_id', '')}
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 重新檢查狀態", use_container_width=True):
            if GSHEETS_AVAILABLE:
                patient = get_patient_by_id(st.session_state.patient_id)
                if patient and patient.get("status") != "pending_setup":
                    st.session_state.patient_info["status"] = patient.get("status")
                    st.session_state.patient_info["surgery_date"] = patient.get("surgery_date", "")
                    st.session_state.patient_info["surgery_type"] = patient.get("surgery_type", "")
                    st.session_state.patient_info["post_op_day"] = calculate_post_op_day(patient.get("surgery_date"))
                    st.success("✅ 設定已完成！")
                    st.rerun()
                else:
                    st.warning("尚未完成設定，請聯繫個案管理師")
    
    with col2:
        if st.button("🚪 登出", use_container_width=True):
            st.session_state.patient_registered = False
            st.session_state.patient_info = {}
            st.session_state.patient_id = ""
            st.rerun()

# ============================================
# 主聊天介面
# ============================================
def render_chat_interface():
    """主聊天介面（美化版）"""
    patient_info = st.session_state.patient_info
    
    # 美化版歡迎區
    if UI_STYLES_AVAILABLE:
        render_welcome(
            patient_info.get('name', '使用者'),
            patient_info.get('post_op_day', 0)
        )
    else:
        # 頂部資訊（備用）
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"👤 **{patient_info.get('name', '使用者')}**")
        with col2:
            post_op_day = patient_info.get('post_op_day', 0)
            st.markdown(f"📅 **術後 D+{post_op_day}**")
        with col3:
            if st.button("🚪"):
                st.session_state.patient_registered = False
                st.session_state.patient_info = {}
                st.session_state.messages = []
                st.rerun()
    
    # 登出按鈕（美化版）
    col1, col2, col3 = st.columns([1, 2, 1])
    with col3:
        if st.button("🚪 登出", key="logout_btn"):
            st.session_state.patient_registered = False
            st.session_state.patient_info = {}
            st.session_state.messages = []
            st.rerun()
    
    st.divider()
    
    # 檢查是否已完成今日回報
    if st.session_state.report_completed:
        if UI_STYLES_AVAILABLE:
            render_completion_message()
            st.markdown("<br>", unsafe_allow_html=True)
            render_tip_box("明天再來回報您的健康狀況喔！每日回報有助於醫療團隊更好地照顧您。", "💡")
        else:
            st.success("✅ 您今天已完成回報！")
            st.info("明天再來回報您的健康狀況喔！")
        
        if st.button("📊 查看回報紀錄", use_container_width=True):
            reports = get_patient_reports(st.session_state.patient_id) if GSHEETS_AVAILABLE else []
            if reports:
                st.write("### 最近回報紀錄")
                for r in reports[-5:]:
                    level_icon = "🔴" if r.get('alert_level') == 'red' else "🟡" if r.get('alert_level') == 'yellow' else "🟢"
                    st.markdown(f"""
                    <div style="
                        background: white;
                        padding: 12px 15px;
                        border-radius: 10px;
                        margin-bottom: 8px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <span>{r.get('date')}</span>
                        <span>{level_icon} {r.get('overall_score')}/10</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 緊急聯絡
        if UI_STYLES_AVAILABLE:
            render_emergency_contact()
        return
    
    # 初始化對話
    if not st.session_state.messages:
        now = datetime.now()
        greeting = "早安" if now.hour < 12 else "午安" if now.hour < 18 else "晚安"
        post_op_day = patient_info.get('post_op_day', 0)
        
        welcome_msg = f"""{greeting}，{patient_info.get('name', '您')}！😊

我是您的健康小助手，今天是您術後第 {post_op_day} 天。

請問您今天整體感覺如何？（0-10分，0是完全沒有不舒服）"""
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_msg,
            "time": now.strftime("%H:%M")
        })
    
    # 顯示對話（美化版）
    for msg in st.session_state.messages:
        if UI_STYLES_AVAILABLE:
            render_chat_message(msg["content"], is_ai=(msg["role"] == "assistant"))
        else:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    
    # 快速回覆按鈕（美化）
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📝 請選擇或輸入您的回覆")
    
    # 分數快速選擇
    st.markdown("**症狀分數快速選擇：**")
    cols = st.columns(3)
    quick_replies = [
        ("😊 0-3分", "我今天感覺不錯，大概2-3分"), 
        ("😐 4-6分", "有一些不舒服，大概5分左右"), 
        ("😣 7-10分", "很不舒服，大概7-8分"),
    ]
    for i, (label, reply) in enumerate(quick_replies):
        if cols[i].button(label, key=f"quick_{i}", use_container_width=True):
            handle_user_input(reply)
    
    # 常用回覆
    st.markdown("**常用回覆：**")
    cols2 = st.columns(4)
    common_replies = [
        ("😊 還不錯", "今天感覺還不錯"),
        ("😓 有點痛", "傷口有點痛"),
        ("😮‍💨 有點喘", "呼吸有點喘"),
        ("😴 很疲勞", "感覺很疲勞"),
    ]
    for i, (label, reply) in enumerate(common_replies):
        if cols2[i].button(label, key=f"common_{i}", use_container_width=True):
            handle_user_input(reply)
    
    st.markdown("---")
    
    # 文字輸入框
    st.markdown("**💬 或直接輸入您想說的話：**")
    user_input = st.chat_input("請描述您的感覺，例如：「今天傷口有點痛，大概5分」")
    if user_input:
        handle_user_input(user_input)

def handle_user_input(user_input):
    """處理使用者輸入"""
    # 添加使用者訊息
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "time": datetime.now().strftime("%H:%M")
    })
    
    st.session_state.conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    # 獲取 AI 回應
    ai_response = get_ai_response(user_input)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_response,
        "time": datetime.now().strftime("%H:%M")
    })
    
    st.session_state.conversation_history.append({
        "role": "assistant",
        "content": ai_response
    })
    
    # 檢查是否完成回報
    if len(st.session_state.messages) >= 10 or "感謝" in ai_response or "完成" in ai_response:
        # 產生 AI 摘要
        ai_summary = generate_ai_summary()
        
        # 準備對話內容
        conversation = []
        for msg in st.session_state.messages:
            conversation.append({
                "role": msg.get("role", ""),
                "content": msg.get("content", "")[:500]  # 限制長度
            })
        
        # 計算術後天數
        post_op_day = 0
        surgery_date_str = st.session_state.patient_info.get("surgery_date", "")
        if surgery_date_str:
            try:
                surgery_date = datetime.strptime(surgery_date_str.split()[0], "%Y-%m-%d")
                post_op_day = (datetime.now() - surgery_date).days
            except:
                pass
        
        # 儲存回報
        if GSHEETS_AVAILABLE:
            save_report({
                "patient_id": st.session_state.patient_id,
                "patient_name": st.session_state.patient_info.get("name", ""),
                "overall_score": st.session_state.current_score,
                "symptoms": st.session_state.symptoms_reported,
                "post_op_day": post_op_day,
                "conversation": conversation,
                "ai_summary": ai_summary,
                "alert_level": "red" if st.session_state.current_score >= 7 else "yellow" if st.session_state.current_score >= 4 else "green"
            })
        st.session_state.report_completed = True
    
    st.rerun()

def generate_ai_summary():
    """產生 AI 對話摘要"""
    if not st.session_state.messages:
        return ""
    
    # 提取病人訊息
    patient_messages = [msg["content"] for msg in st.session_state.messages if msg.get("role") == "user"]
    
    if not patient_messages:
        return ""
    
    # 如果有 OpenAI API，使用 AI 產生摘要
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            conversation_text = "\n".join([
                f"{'病人' if msg.get('role') == 'user' else 'AI'}: {msg.get('content', '')}"
                for msg in st.session_state.messages[-10:]  # 最近 10 則
            ])
            
            summary_prompt = f"""請根據以下病人與AI的對話，產生一段簡短的摘要（約50-100字），重點包括：
1. 病人的主要症狀
2. 症狀的嚴重程度
3. 需要特別注意的事項

對話內容：
{conversation_text}

請直接輸出摘要，不要加任何前綴。"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            pass
    
    # 如果沒有 API 或失敗，產生簡單摘要
    symptoms = st.session_state.symptoms_reported
    score = st.session_state.current_score
    
    # 確保 symptoms 是字典
    if not isinstance(symptoms, dict):
        symptoms = {}
    
    symptom_names = {
        "pain": "疼痛", "dyspnea": "呼吸困難", "cough": "咳嗽",
        "fatigue": "疲勞", "sleep": "睡眠", "appetite": "食慾", "mood": "情緒"
    }
    
    high_symptoms = []
    for key, value in symptoms.items():
        if isinstance(value, (int, float)) and value >= 4:
            name = symptom_names.get(key, key)
            high_symptoms.append(f"{name}({value}分)")
    
    if high_symptoms:
        summary = f"整體評分 {score}/10。主要症狀：{', '.join(high_symptoms)}。"
    else:
        summary = f"整體評分 {score}/10。症狀控制良好。"
    
    # 加入病人的關鍵描述
    for msg in patient_messages[-3:]:
        if len(msg) > 20:
            summary += f" 病人表示：「{msg[:50]}...」"
            break
    
    return summary

def get_ai_response(user_message):
    """取得 AI 回應"""
    # 解析分數
    import re
    score_match = re.search(r'(\d+)', user_message)
    if score_match:
        score = int(score_match.group(1))
        if 0 <= score <= 10:
            st.session_state.current_score = max(st.session_state.current_score, score)
    
    # 使用 OpenAI
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            
            patient_info = st.session_state.patient_info
            context = f"""
病人資訊：
- 姓名：{patient_info.get('name', '')}
- 年齡：{patient_info.get('age', '')}
- 手術：{patient_info.get('surgery_type', '')}
- 術後天數：D+{patient_info.get('post_op_day', 0)}
"""
            messages.append({"role": "system", "content": context})
            
            for msg in st.session_state.conversation_history[-10:]:
                messages.append(msg)
            
            messages.append({"role": "user", "content": user_message})
            
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"抱歉，系統暫時無法回應。請稍後再試。"
    else:
        # 簡單回應
        if "0" in user_message or "1" in user_message or "2" in user_message or "3" in user_message:
            return "很好！您今天狀況不錯。還有其他想告訴我的嗎？如果沒有，我們就完成今天的回報囉！😊"
        elif "7" in user_message or "8" in user_message or "9" in user_message or "10" in user_message:
            return "聽起來您今天比較不舒服。我會通知個管師關心您。請問是哪裡最不舒服呢？"
        else:
            return "謝謝您的回報！請問還有其他症狀想告訴我嗎？如果沒有，我們就完成今天的回報。"

# ============================================
# 主程式
# ============================================
def main():
    """主程式"""
    if not st.session_state.patient_registered:
        render_registration()
    elif st.session_state.patient_info.get("status") == "pending_setup":
        render_pending_setup()
    else:
        render_chat_interface()

if __name__ == "__main__":
    main()
