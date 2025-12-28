"""
AI-CARE Lung - Logo 資源模組（使用原圖）
========================================

包含：
1. 三軍總醫院 Logo（原圖）
2. 數位醫療中心 DMC Logo（原圖）
3. AI-CARE Lung 組合 Logo
"""

import streamlit as st
import base64
import os

# ============================================
# Logo 檔案路徑
# ============================================

def get_logo_base64(filename):
    """從檔案讀取 Logo 並轉為 Base64"""
    # 可能的路徑
    paths = [
        filename,
        f"assets/{filename}",
        f"images/{filename}",
        f"./{filename}"
    ]
    
    for path in paths:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None


def get_tsgh_logo_base64():
    """取得三軍總醫院 Logo Base64"""
    return get_logo_base64("tsgh_logo.png")


def get_dmc_logo_base64():
    """取得 DMC Logo Base64"""
    return get_logo_base64("dmc_logo.png")


# ============================================
# AI-CARE Lung Logo（SVG - 備用）
# ============================================

AICARE_LOGO_SVG = """
<svg width="280" height="100" viewBox="0 0 280 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="aicare_grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#00897B"/>
            <stop offset="50%" style="stop-color:#1E88E5"/>
            <stop offset="100%" style="stop-color:#7C4DFF"/>
        </linearGradient>
        <linearGradient id="lung_grad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#4FC3F7"/>
            <stop offset="100%" style="stop-color:#1E88E5"/>
        </linearGradient>
    </defs>
    <ellipse cx="35" cy="45" rx="22" ry="28" fill="url(#lung_grad)" opacity="0.9"/>
    <ellipse cx="60" cy="45" rx="22" ry="28" fill="url(#lung_grad)" opacity="0.9"/>
    <path d="M47.5 22 L47.5 72" stroke="#1565C0" stroke-width="4" stroke-linecap="round"/>
    <text x="95" y="45" font-family="Arial Black, sans-serif" font-size="28" font-weight="900" fill="url(#aicare_grad)">AI-CARE</text>
    <text x="95" y="72" font-family="Arial, sans-serif" font-size="18" font-weight="600" fill="#00897B">Lung</text>
    <text x="150" y="72" font-family="Microsoft JhengHei, Noto Sans TC, sans-serif" font-size="12" fill="#78909C">智慧肺癌照護</text>
    <circle cx="107" cy="32" r="4" fill="#7C4DFF" opacity="0.9">
        <animate attributeName="opacity" values="0.9;0.4;0.9" dur="2s" repeatCount="indefinite"/>
    </circle>
</svg>
"""


# ============================================
# 渲染函數
# ============================================

def render_tsgh_logo(width=80):
    """渲染三軍總醫院 Logo"""
    b64 = get_tsgh_logo_base64()
    if b64:
        st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{b64}" width="{width}"></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="text-align:center;font-size:{width//2}px;">🏥</div>', unsafe_allow_html=True)


def render_dmc_logo(width=100):
    """渲染 DMC Logo"""
    b64 = get_dmc_logo_base64()
    if b64:
        st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{b64}" width="{width}"></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="text-align:center;font-size:{width//2}px;">🏥</div>', unsafe_allow_html=True)


def render_sidebar_logo():
    """渲染側邊欄 Logo"""
    tsgh_b64 = get_tsgh_logo_base64()
    
    if tsgh_b64:
        logo_html = f'<img src="data:image/png;base64,{tsgh_b64}" width="65" style="border-radius: 8px;">'
    else:
        logo_html = '<div style="font-size: 40px;">🫁</div>'
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        {logo_html}
        <div style="color: white; font-size: 16px; font-weight: 700; margin-top: 10px;">AI-CARE Lung</div>
        <div style="color: rgba(255,255,255,0.6); font-size: 11px;">智慧肺癌照護系統</div>
    </div>
    """, unsafe_allow_html=True)


def render_combined_header():
    """渲染組合標題（含兩個機構 Logo）"""
    tsgh_b64 = get_tsgh_logo_base64()
    dmc_b64 = get_dmc_logo_base64()
    
    # TSGH Logo HTML
    if tsgh_b64:
        tsgh_html = f'<img src="data:image/png;base64,{tsgh_b64}" width="70">'
    else:
        tsgh_html = '<div style="font-size: 40px;">🏥</div>'
    
    # DMC Logo HTML
    if dmc_b64:
        dmc_html = f'<img src="data:image/png;base64,{dmc_b64}" width="70">'
    else:
        dmc_html = '<div style="font-size: 40px;">🏥</div>'
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1E3A5F 0%, #0D253F 100%);
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 20px;
    ">
        <!-- 機構 Logo 區 -->
        <div style="display: flex; justify-content: center; align-items: center; gap: 25px; margin-bottom: 15px; flex-wrap: wrap;">
            <div style="background: white; padding: 10px; border-radius: 12px;">
                {tsgh_html}
            </div>
            <div style="color: rgba(255,255,255,0.4); font-size: 20px;">×</div>
            <div style="background: white; padding: 10px; border-radius: 12px;">
                {dmc_html}
            </div>
        </div>
        
        <!-- 系統名稱 -->
        <div style="text-align: center;">
            <div style="color: #4FC3F7; font-size: 13px; margin-bottom: 5px;">🫁 智慧肺癌術後照護系統</div>
            <div style="color: white; font-size: 28px; font-weight: 700; letter-spacing: 1px;">AI-CARE Lung</div>
            <div style="color: rgba(255,255,255,0.4); font-size: 11px; margin-top: 5px;">
                AI-interactive Care And Real-time Evaluation
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_login_header():
    """渲染登入頁標題（病人端）"""
    tsgh_b64 = get_tsgh_logo_base64()
    
    if tsgh_b64:
        logo_html = f'<img src="data:image/png;base64,{tsgh_b64}" width="80" style="border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">'
    else:
        logo_html = '<div style="font-size: 60px;">🫁</div>'
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #00897B 0%, #26A69A 100%);
        padding: 40px 20px;
        border-radius: 25px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 40px rgba(0,137,123,0.3);
    ">
        <div style="margin-bottom: 20px;">
            {logo_html}
        </div>
        <h1 style="color: white; font-size: 32px; margin: 0;">AI-CARE Lung</h1>
        <p style="color: rgba(255,255,255,0.9); font-size: 16px; margin-top: 10px;">
            三軍總醫院 智慧照護系統
        </p>
        <p style="color: rgba(255,255,255,0.7); font-size: 14px; margin-top: 5px;">
            讓我們一起守護您的健康 ❤️
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """渲染頁尾"""
    tsgh_b64 = get_tsgh_logo_base64()
    dmc_b64 = get_dmc_logo_base64()
    
    tsgh_html = f'<img src="data:image/png;base64,{tsgh_b64}" width="45">' if tsgh_b64 else ''
    dmc_html = f'<img src="data:image/png;base64,{dmc_b64}" width="45">' if dmc_b64 else ''
    
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 20px;
        margin-top: 40px;
        border-top: 1px solid #E0E0E0;
        color: #9E9E9E;
        font-size: 12px;
    ">
        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-bottom: 10px;">
            {tsgh_html}
            {dmc_html}
        </div>
        <div>© 2024 三軍總醫院 數位醫療中心</div>
        <div style="font-size: 10px; margin-top: 5px;">Tri-Service General Hospital, Digital Medical Center</div>
    </div>
    """, unsafe_allow_html=True)
