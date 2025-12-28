"""
AI-CARE Lung - 病人端 UI 美化模組
================================

專為病人設計的友善介面
- 大字體、高對比
- 溫暖親切的色調
- 簡潔易懂的操作
"""

import streamlit as st

# 嘗試載入 Logo 模組
try:
    from logos import render_login_header, render_sidebar_logo, render_footer, SIDEBAR_LOGO_SVG
    LOGOS_AVAILABLE = True
except:
    LOGOS_AVAILABLE = False
    SIDEBAR_LOGO_SVG = ""

# ============================================
# 病人端色彩系統（溫暖、親切）
# ============================================

COLORS = {
    # 主色（溫暖藍綠）
    "primary": "#00897B",      # 青綠色 - 健康、安心
    "secondary": "#26A69A",    # 淺青綠
    "accent": "#4DB6AC",       # 亮青綠
    
    # 輔助色
    "warm": "#FF8A65",         # 暖橘 - 親切
    "calm": "#81D4FA",         # 淺藍 - 平靜
    
    # 警示色
    "danger": "#EF5350",
    "warning": "#FFB74D",
    "success": "#81C784",
    "info": "#4FC3F7",
    
    # 中性色
    "dark": "#37474F",
    "gray": "#78909C",
    "light": "#ECEFF1",
    "white": "#FFFFFF",
    
    # 背景
    "bg_gradient": "linear-gradient(135deg, #E0F2F1 0%, #B2DFDB 100%)",
    "card_gradient": "linear-gradient(145deg, #ffffff 0%, #f5f7fa 100%)"
}

# ============================================
# 病人端 CSS
# ============================================

def get_patient_css():
    """病人端專用 CSS"""
    return f"""
    <style>
    /* ===== 全局樣式 ===== */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
    
    .stApp {{
        font-family: 'Noto Sans TC', sans-serif;
        background: {COLORS['bg_gradient']};
    }}
    
    /* ===== 大字體（方便閱讀）===== */
    .stMarkdown p {{
        font-size: 18px;
        line-height: 1.8;
    }}
    
    /* ===== 標題 ===== */
    h1 {{
        color: {COLORS['primary']};
        font-weight: 700;
        font-size: 28px;
        text-align: center;
        padding: 15px 0;
    }}
    
    h2, h3 {{
        color: {COLORS['dark']};
        font-weight: 600;
    }}
    
    /* ===== 大按鈕（方便點擊）===== */
    .stButton > button {{
        border-radius: 15px;
        font-size: 18px;
        font-weight: 600;
        padding: 15px 30px;
        min-height: 60px;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        color: white;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,137,123,0.3);
    }}
    
    /* ===== 輸入框（大尺寸）===== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {{
        border-radius: 12px;
        border: 2px solid {COLORS['light']};
        font-size: 20px;
        padding: 15px;
        min-height: 55px;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {COLORS['primary']};
        box-shadow: 0 0 0 3px rgba(0,137,123,0.2);
    }}
    
    /* ===== 滑桿（大尺寸）===== */
    .stSlider > div > div > div {{
        height: 12px;
    }}
    
    .stSlider > div > div > div > div {{
        height: 30px;
        width: 30px;
        background: {COLORS['primary']};
    }}
    
    /* ===== 卡片 ===== */
    .patient-card {{
        background: white;
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }}
    
    /* ===== 歡迎區塊 ===== */
    .welcome-box {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        color: white;
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 40px rgba(0,137,123,0.3);
    }}
    
    .welcome-box h2 {{
        color: white;
        font-size: 24px;
        margin-bottom: 10px;
    }}
    
    .welcome-box p {{
        color: rgba(255,255,255,0.9);
        font-size: 16px;
    }}
    
    /* ===== 症狀評分卡 ===== */
    .symptom-card {{
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        border-left: 5px solid {COLORS['primary']};
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }}
    
    .symptom-card.high {{
        border-left-color: {COLORS['danger']};
        background: linear-gradient(90deg, #FFEBEE 0%, white 100%);
    }}
    
    .symptom-card.medium {{
        border-left-color: {COLORS['warning']};
        background: linear-gradient(90deg, #FFF8E1 0%, white 100%);
    }}
    
    .symptom-card.low {{
        border-left-color: {COLORS['success']};
        background: linear-gradient(90deg, #E8F5E9 0%, white 100%);
    }}
    
    /* ===== 聊天氣泡 ===== */
    .chat-bubble {{
        padding: 15px 20px;
        border-radius: 20px;
        margin-bottom: 15px;
        max-width: 85%;
        font-size: 16px;
        line-height: 1.6;
    }}
    
    .chat-bubble.ai {{
        background: white;
        border: 2px solid {COLORS['light']};
        margin-right: auto;
        border-bottom-left-radius: 5px;
    }}
    
    .chat-bubble.user {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 5px;
    }}
    
    /* ===== 進度指示 ===== */
    .progress-indicator {{
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 20px 0;
    }}
    
    .progress-dot {{
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: {COLORS['light']};
    }}
    
    .progress-dot.active {{
        background: {COLORS['primary']};
        animation: pulse 1.5s infinite;
    }}
    
    .progress-dot.completed {{
        background: {COLORS['success']};
    }}
    
    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.3); }}
    }}
    
    /* ===== 完成頁面 ===== */
    .completion-box {{
        background: linear-gradient(135deg, {COLORS['success']} 0%, #66BB6A 100%);
        color: white;
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102,187,106,0.3);
    }}
    
    .completion-box .icon {{
        font-size: 60px;
        margin-bottom: 20px;
    }}
    
    /* ===== 衛教卡片 ===== */
    .education-card {{
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .education-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }}
    
    /* ===== 警示提示 ===== */
    .alert-banner {{
        background: linear-gradient(135deg, {COLORS['warning']} 0%, #FFA726 100%);
        color: white;
        border-radius: 15px;
        padding: 15px 20px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 15px;
    }}
    
    .alert-banner .icon {{
        font-size: 30px;
    }}
    
    /* ===== 隱藏 Streamlit 元素 ===== */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* ===== 分隔線 ===== */
    hr {{
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, {COLORS['light']}, transparent);
        margin: 25px 0;
    }}
    
    </style>
    """


# ============================================
# 元件函數
# ============================================

def render_welcome(name, post_op_day):
    """渲染歡迎區塊"""
    greeting = "早安" if 5 <= __import__('datetime').datetime.now().hour < 12 else "午安" if 12 <= __import__('datetime').datetime.now().hour < 18 else "晚安"
    
    st.markdown(f"""
    <div class="welcome-box">
        <div style="font-size: 50px; margin-bottom: 15px;">👋</div>
        <h2>{greeting}，{name}</h2>
        <p>術後第 <b style="font-size: 24px;">{post_op_day}</b> 天</p>
        <p style="margin-top: 10px; opacity: 0.8;">今天感覺如何呢？讓我們一起記錄您的狀況</p>
    </div>
    """, unsafe_allow_html=True)


def render_symptom_question(symptom_name, icon, description=""):
    """渲染症狀問題"""
    st.markdown(f"""
    <div class="symptom-card">
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
            <span style="font-size: 35px;">{icon}</span>
            <div>
                <div style="font-size: 20px; font-weight: 600; color: {COLORS['dark']};">{symptom_name}</div>
                {f'<div style="font-size: 14px; color: {COLORS["gray"]};">{description}</div>' if description else ''}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_score_display(score, label=""):
    """渲染分數顯示"""
    if score >= 7:
        color = COLORS['danger']
        bg = "#FFEBEE"
        text = "較嚴重"
    elif score >= 4:
        color = COLORS['warning']
        bg = "#FFF8E1"
        text = "中等"
    else:
        color = COLORS['success']
        bg = "#E8F5E9"
        text = "輕微"
    
    st.markdown(f"""
    <div style="
        background: {bg};
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 2px solid {color};
    ">
        <div style="font-size: 48px; font-weight: 700; color: {color};">{score}</div>
        <div style="font-size: 14px; color: {COLORS['gray']};">/ 10 分</div>
        <div style="font-size: 16px; color: {color}; margin-top: 5px;">{text}</div>
        {f'<div style="font-size: 14px; color: {COLORS["gray"]}; margin-top: 5px;">{label}</div>' if label else ''}
    </div>
    """, unsafe_allow_html=True)


def render_chat_message(message, is_ai=True):
    """渲染聊天訊息"""
    bubble_class = "ai" if is_ai else "user"
    icon = "🤖" if is_ai else "🧑"
    
    st.markdown(f"""
    <div style="display: flex; align-items: flex-start; gap: 10px; {'flex-direction: row-reverse;' if not is_ai else ''}">
        <div style="font-size: 30px;">{icon}</div>
        <div class="chat-bubble {bubble_class}">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def render_completion_message():
    """渲染完成訊息"""
    st.markdown(f"""
    <div class="completion-box">
        <div class="icon">🎉</div>
        <h2 style="color: white; font-size: 24px;">今日回報完成！</h2>
        <p style="font-size: 16px; opacity: 0.9; margin-top: 15px;">
            感謝您的回報，我們會持續關心您的健康狀況。<br>
            如有任何不適，請隨時聯繫我們。
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_progress(current, total):
    """渲染進度指示"""
    dots_html = ""
    for i in range(total):
        if i < current:
            dots_html += '<div class="progress-dot completed"></div>'
        elif i == current:
            dots_html += '<div class="progress-dot active"></div>'
        else:
            dots_html += '<div class="progress-dot"></div>'
    
    st.markdown(f"""
    <div class="progress-indicator">
        {dots_html}
    </div>
    <div style="text-align: center; color: {COLORS['gray']}; font-size: 14px;">
        {current + 1} / {total}
    </div>
    """, unsafe_allow_html=True)


def render_education_card(title, category, icon="📚"):
    """渲染衛教卡片"""
    st.markdown(f"""
    <div class="education-card">
        <div style="display: flex; align-items: center; gap: 15px;">
            <span style="font-size: 40px;">{icon}</span>
            <div>
                <div style="font-size: 18px; font-weight: 600; color: {COLORS['dark']};">{title}</div>
                <div style="font-size: 14px; color: {COLORS['gray']};">{category}</div>
            </div>
            <div style="margin-left: auto; font-size: 24px; color: {COLORS['gray']};">›</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_tip_box(message, icon="💡"):
    """渲染提示框"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        display: flex;
        align-items: center;
        gap: 15px;
    ">
        <span style="font-size: 35px;">{icon}</span>
        <div style="font-size: 16px; color: {COLORS['dark']};">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def render_emergency_contact():
    """渲染緊急聯絡資訊"""
    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
        border: 2px solid {COLORS['light']};
    ">
        <div style="font-size: 16px; font-weight: 600; color: {COLORS['dark']}; margin-bottom: 10px;">
            📞 緊急聯絡
        </div>
        <div style="font-size: 14px; color: {COLORS['gray']};">
            若有緊急狀況，請撥打：<br>
            <span style="font-size: 20px; font-weight: 600; color: {COLORS['primary']};">02-8792-3311</span><br>
            <span style="font-size: 12px;">三軍總醫院 胸腔外科</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# 初始化
# ============================================

def init_patient_style():
    """初始化病人端樣式"""
    st.markdown(get_patient_css(), unsafe_allow_html=True)
