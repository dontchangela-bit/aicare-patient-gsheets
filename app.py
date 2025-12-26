"""
AI-CARE Lung - 病人端（Google Sheets 整合版）
=============================================

🟢 病人專用介面
📊 使用 Google Sheets 作為共享資料庫
"""

import streamlit as st
from datetime import datetime, timedelta
import json
import re

# ============================================
# 設定
# ============================================
SYSTEM_NAME = "AI-CARE Lung"
HOSPITAL_NAME = "三軍總醫院"

# OpenAI 設定（從 secrets 讀取）
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
        get_education_pushes, mark_education_read
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

# ============================================
# 頁面設定
# ============================================
st.set_page_config(
    page_title=f"{SYSTEM_NAME} - 健康回報",
    page_icon="🫁",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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

## 回應策略
- 高分(7-10)：表達關心，說明已通知護理師，給予緩解建議
- 中分(4-6)：給予建議，詢問其他症狀
- 低分(0-3)：正面回應，繼續詢問

## 重要提醒
- 症狀評分≥7時：⚠️ 表示已通知個案管理師
- 不診斷病情，只做症狀記錄
- 必要時建議就醫或聯繫護理師"""

# ============================================
# CSS 樣式
# ============================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .header-card {
        background: linear-gradient(135deg, #10b981, #059669);
        border-radius: 20px;
        padding: 24px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
    }
    
    .stat-card {
        background: rgba(255,255,255,0.15);
        border-radius: 12px;
        padding: 12px;
        text-align: center;
    }
    
    .chat-ai {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 16px;
        padding: 14px 18px;
        margin-bottom: 8px;
        font-size: 15px;
        line-height: 1.6;
    }
    
    .chat-user {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        border-radius: 16px;
        padding: 14px 18px;
        font-size: 15px;
        line-height: 1.5;
    }
    
    .stButton > button {
        border-radius: 12px;
        font-weight: 500;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# Session State 初始化
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
    st.session_state.symptoms_reported = []
if 'report_completed' not in st.session_state:
    st.session_state.report_completed = False

# ============================================
# 工具函數
# ============================================
def calculate_post_op_day(surgery_date_str):
    """計算術後天數"""
    if not surgery_date_str:
        return 0
    try:
        surgery_date = datetime.strptime(surgery_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        days = (today - surgery_date).days
        return max(0, days)
    except:
        return 0

# ============================================
# 註冊/登入頁面
# ============================================
def render_registration():
    """註冊與登入頁面"""
    
    # 檢查 Google Sheets 連線
    if not GSHEETS_AVAILABLE:
        st.error("⚠️ 系統暫時無法連線，請稍後再試")
        st.info("如持續發生，請聯繫個管師")
        return
    
    st.markdown(f"""
    <div style="text-align: center; padding: 30px 0;">
        <div style="font-size: 64px; margin-bottom: 12px;">🫁</div>
        <h1 style="color: #1e293b; margin-bottom: 4px; font-size: 28px;">{SYSTEM_NAME}</h1>
        <p style="color: #64748b; font-size: 15px;">{HOSPITAL_NAME} 智慧肺癌術後照護</p>
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
            
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("年齡", min_value=18, max_value=120, value=65)
            with col2:
                gender = st.selectbox("性別", ["男", "女"])
            
            st.markdown("---")
            
            # 同意條款
            st.markdown("#### 📜 使用條款")
            st.markdown("""
            <div style="background: #f8fafc; padding: 12px; border-radius: 8px; font-size: 13px; color: #475569; max-height: 150px; overflow-y: auto; margin-bottom: 12px;">
            <p><strong>AI-CARE Lung 智慧照護系統使用同意書</strong></p>
            <p>1. 本系統將收集您的健康狀況回報資料，用於術後照護追蹤。</p>
            <p>2. 您的資料將受到嚴格保護，僅供醫療團隊進行照護使用。</p>
            <p>3. 您的回報內容可能用於醫療品質改善及學術研究（去識別化處理）。</p>
            <p>4. 您有權隨時退出本系統，退出後將停止收集新資料。</p>
            <p>5. 本系統提供之建議僅供參考，如有緊急狀況請立即就醫。</p>
            </div>
            """, unsafe_allow_html=True)
            
            agree = st.checkbox("我已閱讀並同意上述使用條款")
            
            submit = st.form_submit_button("✅ 註冊", use_container_width=True, type="primary")
            
            if submit:
                if not name:
                    st.error("請填寫姓名")
                elif not phone or len(phone) < 10:
                    st.error("請填寫正確的手機號碼")
                elif not password or len(password) < 4:
                    st.error("請設定至少4位數的密碼")
                elif password != password_confirm:
                    st.error("兩次密碼輸入不一致")
                elif not agree:
                    st.error("請閱讀並同意使用條款")
                else:
                    # 檢查是否已註冊
                    existing = get_patient_by_phone(phone)
                    
                    if existing:
                        st.error("此手機號碼已註冊，請直接登入")
                    else:
                        # 產生病人 ID
                        patient_id = f"P{phone[-4:]}{datetime.now().strftime('%m%d')}"
                        now = datetime.now()
                        
                        # 建立病人資料
                        patient_data = {
                            "patient_id": patient_id,
                            "name": name,
                            "phone": phone,
                            "password": password,
                            "age": age,
                            "gender": gender,
                            "surgery_type": "待設定",
                            "surgery_date": "",
                            "diagnosis": "肺癌術後",
                            "medical_record": "",
                            "status": "pending_setup",
                            "post_op_day": 0,
                            "consent_agreed": "Y",
                            "consent_time": now.isoformat(),
                            "registered_at": now.isoformat(),
                            "clinical_data": "",
                            "notes": ""
                        }
                        
                        success = create_patient(patient_data)
                        
                        if success:
                            st.session_state.patient_info = {
                                "patient_id": patient_id,
                                "name": name,
                                "phone": phone,
                                "age": age,
                                "gender": gender,
                                "surgery_date": "",
                                "surgery_type": "待設定",
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
    
    # === 我已註冊（登入）===
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
                    patient = get_patient_by_phone(login_phone)
                    
                    if patient:
                        if patient.get("password") == login_password:
                            # 登入成功
                            surgery_date = patient.get("surgery_date", "")
                            post_op_day = calculate_post_op_day(surgery_date) if surgery_date else 0
                            
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
        
        st.caption("忘記密碼？請聯繫個案管理師")

# ============================================
# 初始化對話
# ============================================
def initialize_chat():
    """初始化對話"""
    if not st.session_state.messages:
        patient_name = st.session_state.patient_info.get('name', '您')
        post_op_day = st.session_state.patient_info.get('post_op_day', 0)
        
        now = datetime.now()
        greeting = "早安" if now.hour < 12 else "午安" if now.hour < 18 else "晚安"
        
        welcome_msg = f"""{greeting}，{patient_name}！😊

我是您的健康小助手，今天是您術後第 {post_op_day} 天。

現在讓我們來做今日健康回報，請問您今天整體感覺如何？"""
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_msg,
            "time": now.strftime("%H:%M")
        })

# ============================================
# AI 回應
# ============================================
def get_ai_response(user_message):
    """取得 AI 回應"""
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    patient_info = st.session_state.patient_info
    context = f"""
病人資訊：
- 姓名：{patient_info.get('name', '')}
- 年齡：{patient_info.get('age', '')}
- 手術：{patient_info.get('surgery_type', '')}
- 術後天數：D+{patient_info.get('post_op_day', 0)}
- 今日日期：{datetime.now().strftime('%Y年%m月%d日')}
"""
    messages.append({"role": "system", "content": context})
    
    for msg in st.session_state.conversation_history[-10:]:
        messages.append(msg)
    
    messages.append({"role": "user", "content": user_message})
    
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"抱歉，系統暫時無法回應。請稍後再試。"
    else:
        return get_fallback_response(user_message)

def get_fallback_response(msg):
    """備用回應"""
    msg = msg.lower()
    
    if any(word in msg for word in ['沒有', '沒了', '結束', '完成', '都沒', '沒其他']):
        st.session_state.report_completed = True
        return """好的，今日回報完成！✅

感謝您的回報，祝您有美好的一天！

如有任何不適加重，請隨時回來告訴我們。"""
    
    if any(word in msg for word in ['不錯', '還好', '好', '正常', '沒事', '很好']):
        return """太好了，很高興您今天感覺不錯！😊

請問還有其他想告訴我的嗎？或是今天回報就到這裡？"""
    
    numbers = re.findall(r'\d+', msg)
    if numbers:
        score = min(int(numbers[0]), 10)
        st.session_state.current_score = max(st.session_state.current_score, score)
        
        if score >= 7:
            return f"""收到，{score} 分是比較嚴重的狀況。

⚠️ 我已經通知個案管理師，她會盡快與您聯繫。

請問還有其他不舒服嗎？"""
        elif score >= 4:
            return f"""收到，{score} 分屬於中度不適。

建議您多休息，如有加重請告知。

請問還有其他不舒服嗎？"""
        else:
            return f"""收到，{score} 分是輕微的程度。✅

請繼續保持，還有其他要回報的嗎？"""
    
    if any(word in msg for word in ['喘', '呼吸', '氣']):
        st.session_state.symptoms_reported.append("呼吸困難")
        return """了解，您有呼吸方面的問題。

可以用 0-10 分描述喘的程度嗎？"""
    
    if any(word in msg for word in ['痛', '疼']):
        st.session_state.symptoms_reported.append("疼痛")
        return """了解，您有疼痛的問題。

可以用 0-10 分描述疼痛程度嗎？"""
    
    if any(word in msg for word in ['累', '疲', '倦', '沒力']):
        st.session_state.symptoms_reported.append("疲勞")
        return """了解，您覺得疲勞。

可以用 0-10 分描述疲勞程度嗎？"""
    
    return """收到您的回報。

還有其他想告訴我的嗎？或是今天回報就到這裡？"""

def process_input(user_input):
    """處理使用者輸入"""
    if not user_input.strip():
        return
    
    now = datetime.now().strftime("%H:%M")
    
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "time": now
    })
    
    st.session_state.conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    response = get_ai_response(user_input)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "time": now
    })
    
    st.session_state.conversation_history.append({
        "role": "assistant",
        "content": response
    })
    
    # 儲存回報到 Google Sheets
    if st.session_state.report_completed and GSHEETS_AVAILABLE:
        save_report(
            st.session_state.patient_id,
            st.session_state.patient_info.get("name", ""),
            {
                "overall_score": st.session_state.current_score,
                "symptoms": st.session_state.symptoms_reported,
                "messages_count": len(st.session_state.messages)
            }
        )
    
    st.rerun()

# ============================================
# 主介面
# ============================================
def main():
    if not st.session_state.patient_registered:
        render_registration()
        return
    
    if st.session_state.patient_info.get("status") == "pending_setup":
        render_pending_setup()
        return
    
    initialize_chat()
    
    patient_name = st.session_state.patient_info.get('name', '使用者')
    post_op_day = st.session_state.patient_info.get('post_op_day', 0)
    surgery_type = st.session_state.patient_info.get('surgery_type', '')
    
    now = datetime.now()
    st.markdown(f"""
    <div class="header-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 4px;">
                    {HOSPITAL_NAME} {SYSTEM_NAME}
                </div>
                <div style="font-size: 20px; font-weight: 700;">
                    {patient_name}，您好！🌱
                </div>
                <div style="font-size: 13px; opacity: 0.9; margin-top: 4px;">
                    {surgery_type}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 32px; font-weight: 700;">D+{post_op_day}</div>
                <div style="font-size: 12px; opacity: 0.9;">術後天數</div>
            </div>
        </div>
        <div style="display: flex; gap: 12px; margin-top: 16px;">
            <div class="stat-card" style="flex: 1;">
                <div style="font-size: 11px; opacity: 0.8;">今日日期</div>
                <div style="font-size: 16px; font-weight: 600;">{now.strftime("%m/%d")}</div>
            </div>
            <div class="stat-card" style="flex: 1;">
                <div style="font-size: 11px; opacity: 0.8;">現在時間</div>
                <div style="font-size: 16px; font-weight: 600;">{now.strftime("%H:%M")}</div>
            </div>
            <div class="stat-card" style="flex: 1;">
                <div style="font-size: 11px; opacity: 0.8;">回報狀態</div>
                <div style="font-size: 16px; font-weight: 600;">{"✅ 已完成" if st.session_state.report_completed else "📝 進行中"}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["💬 每日回報", "📚 衛教專區", "📊 我的紀錄"])
    
    with tab1:
        render_chat_interface()
    
    with tab2:
        render_education_materials()
    
    with tab3:
        render_my_records()
    
    render_footer()

def render_pending_setup():
    """待設定狀態頁面"""
    st.markdown(f"""
    <div style="text-align: center; padding: 50px 20px;">
        <div style="font-size: 64px; margin-bottom: 20px;">⏳</div>
        <h2 style="color: #1e293b;">註冊成功！</h2>
        <p style="color: #64748b; font-size: 16px; margin-bottom: 30px;">
            請聯繫個案管理師完成手術資訊設定後，<br>即可開始使用系統進行每日回報
        </p>
        <div style="background: #f0f9ff; border-radius: 12px; padding: 20px; max-width: 300px; margin: 0 auto;">
            <p style="color: #1e40af; margin: 0;"><strong>📞 個管師專線</strong></p>
            <p style="color: #3b82f6; font-size: 20px; margin: 8px 0;">(02) 8792-3311</p>
            <p style="color: #64748b; font-size: 12px; margin: 0;">週一至週五 08:00-17:00</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 重新檢查狀態", use_container_width=True):
            if GSHEETS_AVAILABLE:
                patient = get_patient_by_id(st.session_state.patient_id)
                if patient and patient.get("status") != "pending_setup" and patient.get("surgery_date"):
                    st.session_state.patient_info["status"] = "normal"
                    st.session_state.patient_info["surgery_date"] = patient.get("surgery_date")
                    st.session_state.patient_info["surgery_type"] = patient.get("surgery_type", "")
                    st.session_state.patient_info["post_op_day"] = calculate_post_op_day(patient.get("surgery_date"))
                    st.success("✅ 設定已完成！")
                    st.rerun()
                else:
                    st.info("尚未完成設定，請聯繫個管師")
    with col2:
        if st.button("🚪 登出", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def render_chat_interface():
    """對話介面"""
    st.markdown("### 💬 與健康小助手對話")
    
    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            st.markdown(f"""
            <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                <div style="width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #10b981, #059669); display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 18px;">🤖</div>
                <div style="flex: 1;">
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">健康小助手 · {msg.get('time', '')}</div>
                    <div class="chat-ai">{msg['content'].replace(chr(10), '<br>')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
                <div style="max-width: 85%;">
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 4px; text-align: right;">{msg.get('time', '')}</div>
                    <div class="chat-user">{msg['content']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    if not st.session_state.report_completed:
        st.markdown("---")
        st.markdown("**快速回覆**")
        
        cols = st.columns(2)
        quick_replies = [
            ("😊 還不錯", "今天感覺還不錯"),
            ("😓 有點累", "今天覺得有點累"),
            ("😮‍💨 有點喘", "呼吸有點喘"),
            ("😣 有點痛", "有點痛"),
            ("✅ 都沒事", "都沒有不舒服，今天狀況很好"),
            ("🏁 完成回報", "沒有其他要回報的了")
        ]
        
        for i, (label, content) in enumerate(quick_replies):
            if cols[i % 2].button(label, key=f"quick_{i}", use_container_width=True):
                process_input(content)
        
        st.markdown("---")
        st.markdown("**症狀評分**")
        
        score = st.slider("整體不適程度 (0-10)", 0, 10, 0, key="score_input")
        
        score_colors = {
            (0, 3): ("#22c55e", "輕微/無不適", "🟢"),
            (4, 6): ("#f59e0b", "中度不適", "🟡"),
            (7, 10): ("#ef4444", "嚴重不適", "🔴")
        }
        
        for (low, high), (color, label, emoji) in score_colors.items():
            if low <= score <= high:
                st.markdown(f"""
                <div style="text-align: center; padding: 12px; background: {color}15; border-radius: 12px; border: 2px solid {color}30;">
                    <span style="font-size: 28px;">{emoji}</span>
                    <span style="color: {color}; font-weight: 600; font-size: 18px; margin-left: 10px;">{label} ({score}/10)</span>
                </div>
                """, unsafe_allow_html=True)
                break
        
        if st.button(f"📤 提交評分 ({score}分)", use_container_width=True, type="primary"):
            st.session_state.current_score = score
            process_input(f"我的整體不適程度是 {score} 分")
        
        st.markdown("---")
        user_input = st.text_input("或輸入您的感受：", placeholder="例如：今天覺得有點喘...", key="text_input")
        
        if st.button("📤 送出", use_container_width=True):
            if user_input:
                process_input(user_input)
    
    else:
        st.markdown("---")
        st.success("✅ 今日回報已完成！明天見 🌟")
        
        if st.button("🔄 重新開始", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_history = []
            st.session_state.current_score = 0
            st.session_state.symptoms_reported = []
            st.session_state.report_completed = False
            st.rerun()

def render_education_materials():
    """衛教專區"""
    st.markdown("### 📚 衛教專區")
    
    post_op_day = st.session_state.patient_info.get('post_op_day', 0)
    
    st.markdown("#### 🎯 為您推薦")
    
    if post_op_day <= 3:
        recommendations = [
            ("🌬️", "呼吸運動訓練", "促進肺部恢復"),
            ("💊", "疼痛控制指南", "術後疼痛管理"),
            ("🚶", "早期下床活動", "加速恢復"),
        ]
    elif post_op_day <= 7:
        recommendations = [
            ("🏠", "居家照護指南", "出院準備"),
            ("🚨", "警示徵象", "何時就醫"),
            ("🩹", "傷口照護", "居家換藥"),
        ]
    else:
        recommendations = [
            ("📋", "追蹤檢查指南", "回診準備"),
            ("🏃", "術後運動指南", "漸進恢復"),
            ("💚", "心理調適", "情緒支持"),
        ]
    
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(recommendations):
        with cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f0fdf4, #dcfce7); border-radius: 12px; padding: 16px; text-align: center; height: 120px;">
                <div style="font-size: 28px;">{icon}</div>
                <div style="font-size: 13px; font-weight: 600; margin-top: 8px; color: #166534;">{title}</div>
                <div style="font-size: 11px; color: #64748b; margin-top: 4px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.expander("🌬️ 呼吸運動訓練指南"):
        st.markdown("""
        ### 深呼吸練習
        1. 坐直或半躺姿勢
        2. 用鼻子慢慢吸氣 4 秒
        3. 憋氣 2 秒
        4. 用嘴巴慢慢吐氣 6 秒
        5. 每小時練習 10 次
        """)
    
    with st.expander("💊 術後疼痛控制指南"):
        st.markdown("""
        ### 疼痛評估
        - 0 分：完全不痛
        - 1-3 分：輕微疼痛
        - 4-6 分：中度疼痛
        - 7-10 分：嚴重疼痛
        """)
    
    with st.expander("🚨 術後警示徵象"):
        st.markdown("""
        ### 🔴 立即急診
        - 突然嚴重呼吸困難
        - 胸痛劇烈、冒冷汗
        - 咳血（鮮紅色、量多）
        """)
    
    # 顯示推送的衛教
    if GSHEETS_AVAILABLE:
        pushes = get_education_pushes(st.session_state.patient_id)
        if pushes:
            st.markdown("---")
            st.markdown("#### 📬 個管師推送給您的")
            
            for push in pushes[:5]:
                status_icon = "📖" if push.get("status") == "read" else "🆕"
                is_new = push.get("status") != "read"
                
                st.markdown(f"""
                <div style="background: {'#fef3c7' if is_new else '#f8fafc'}; border-radius: 10px; padding: 12px; margin-bottom: 8px; border-left: 3px solid {'#f59e0b' if is_new else '#94a3b8'};">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: 600;">{status_icon} {push.get('material_title', '')}</span>
                        <span style="font-size: 12px; color: #64748b;">{push.get('pushed_at', '')[:10]}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def render_my_records():
    """我的紀錄"""
    st.markdown("### 📊 我的紀錄")
    
    patient_id = st.session_state.patient_id
    post_op_day = st.session_state.patient_info.get('post_op_day', 0)
    
    # 取得歷史紀錄
    if GSHEETS_AVAILABLE:
        history = get_patient_reports(patient_id)
    else:
        history = []
    
    total_reports = len(history)
    if total_reports > 0:
        scores = [r.get("overall_score", 0) for r in history if r.get("overall_score")]
        avg_score = sum(scores) / len(scores) if scores else 0
        compliance = min(100, int(total_reports / max(post_op_day, 1) * 100))
    else:
        avg_score = 0
        compliance = 0 if post_op_day > 0 else 100
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dbeafe, #bfdbfe); border-radius: 12px; padding: 16px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: #1e40af;">{total_reports}</div>
            <div style="font-size: 12px; color: #1e40af;">累計回報次數</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dcfce7, #bbf7d0); border-radius: 12px; padding: 16px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: #166534;">{compliance}%</div>
            <div style="font-size: 12px; color: #166534;">回報完成率</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fef3c7, #fde68a); border-radius: 12px; padding: 16px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: #92400e;">{avg_score:.1f}</div>
            <div style="font-size: 12px; color: #92400e;">平均不適分數</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### 📋 歷史回報")
    
    if history:
        for record in history[:10]:
            record_date = record.get("date", "")
            score = record.get("overall_score", 0)
            symptoms = record.get("symptoms", [])
            if isinstance(symptoms, str):
                symptoms = []
            
            if score >= 7:
                status = "🔴"
            elif score >= 4:
                status = "🟡"
            else:
                status = "🟢"
            
            symptoms_text = "、".join(symptoms) if symptoms else "無明顯不適"
            
            st.markdown(f"""
            <div style="background: #f8fafc; border-radius: 10px; padding: 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-weight: 600;">{record_date}</span>
                </div>
                <div style="text-align: center; flex: 1; margin: 0 12px;">
                    <span style="font-size: 12px; color: #64748b;">{symptoms_text}</span>
                </div>
                <div>
                    <span style="font-size: 18px;">{status}</span>
                    <span style="font-weight: 600; margin-left: 4px;">{score}分</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("尚無回報紀錄，完成今日回報後會顯示在這裡")

def render_footer():
    """底部區域"""
    st.markdown("---")
    
    if st.button("🚨 緊急聯繫", use_container_width=True, type="secondary"):
        st.error("""
        📞 **緊急聯繫方式**
        - 個管師專線：(02) 8792-3311
        - 醫院急診：(02) 8792-3311 轉 88632
        - 如有生命危險請撥 119
        """)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"👤 {st.session_state.patient_info.get('name', '')} ({st.session_state.patient_id})")
    with col2:
        if st.button("🚪 登出", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 11px;">
        {SYSTEM_NAME} | {HOSPITAL_NAME} © 2024
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
