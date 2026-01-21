# -*- coding: utf-8 -*-
import streamlit as st
import random
import os
import time
from datetime import datetime
import pandas as pd
from supabase import create_client, Client

# ==========================================
# 1. 設定與全域變數
# ==========================================

# 應用程式資訊
APP_AUTHOR = "江俊廷"
APP_VERSION = "1.0.1"

# Supabase 設定
# 注意：為了安全，我們現在優先從 st.secrets 讀取
TABLE_NAME = "high_scores_0121"

def init_supabase_client():
    """初始化並回傳 Supabase 客戶端"""
    try:
        # 優先嘗試從 secrets 讀取
        if "supabase" in st.secrets:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
            return create_client(url, key)
        else:
            st.error("⚠️ 未找到 Supabase 設定，請檢查 .streamlit/secrets.toml")
            return None
    except Exception as e:
        print(f"無法連接到 Supabase: {e}")
        return None

# ==========================================
# 2. 資料庫操作
# ==========================================

def get_global_best(client):
    """取得全球最佳紀錄（前10名）"""
    if not client: return []
    try:
        response = client.table(TABLE_NAME)\
            .select("*")\
            .order("score", desc=False)\
            .limit(10)\
            .execute()
        return response.data
    except Exception as e:
        print(f"讀取紀錄失敗: {e}") 
        return []

def save_score_to_cloud(client, player_name, score):
    """上傳成績到雲端"""
    if not client: 
        st.error("⚠️ 無法連線到雲端資料庫，請檢查網路或 API Key")
        return False
    try:
        data = {
            "player_name": player_name,
            "score": score,
            "created_at": datetime.now().isoformat()
        }
        client.table(TABLE_NAME).insert(data).execute()
        return True
    except Exception as e:
        st.error(f"上傳失敗: {e}")
        return False

# ==========================================
# 3. 遊戲核心邏輯
# ==========================================

def init_game():
    """重置遊戲狀態"""
    # 正式遊戲模式：1-100 隨機亂數
    st.session_state.target_number = random.randint(1, 100) 
    
    st.session_state.count = 0
    st.session_state.current_game_history = []
    st.session_state.game_over = False
    
    # 動態範圍提示
    st.session_state.low_bound = 1
    st.session_state.high_bound = 100
    
    st.session_state.message = f"🤔 準備好了嗎？答案在 {st.session_state.low_bound} 到 {st.session_state.high_bound} 之間"
    st.session_state.message_type = "info"
    
    # 清除輸入框的 key 來重置
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0
    st.session_state.input_key += 1

# ==========================================
# 4. 前端樣式 (CSS)
# ==========================================

def inject_custom_css():
    st.markdown("""
        <style>
        /* 全域字型與背景優化 */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        /* 標題與版本資訊 */
        .main-title {
            text-align: center;
            font-size: clamp(2rem, 5vw, 3rem); /* 響應用字體 */
            font-weight: 800;
            background: linear-gradient(120deg, #2b5876 0%, #4e4376 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .app-info {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 30px;
            font-family: 'Courier New', monospace;
        }
        
        /* 響應式卡片容器 */
        .game-card {
            background: white;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            margin: 10px auto;
            max-width: 600px; /* 手機上滿寬，大螢幕限制寬度 */
        }
        
        /* 排行榜表格優化 */
        .rank-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95em;
        }
        .rank-table th {
            text-align: left;
            padding: 12px;
            border-bottom: 2px solid #eee;
            color: #888;
        }
        .rank-table td {
            padding: 12px;
            border-bottom: 1px solid #f9f9f9;
        }
        .rank-1 { background-color: rgba(255, 215, 0, 0.1); font-weight: bold; color: #d4af37; }
        .rank-2 { background-color: rgba(192, 192, 192, 0.1); font-weight: bold; color: #a0a0a0; }
        .rank-3 { background-color: rgba(205, 127, 50, 0.1); font-weight: bold; color: #cd7f32; }
        
        /* 訊息框動畫 */
        @keyframes popIn {
            0% { transform: scale(0.9); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }
        .message-box {
            animation: popIn 0.3s ease-out;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            text-align: center;
            font-weight: bold;
        }
        
        /* 左側選單按鈕 */
        .stButton button {
            width: 100%;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            transition: all 0.2s;
        }
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        
        /* 手機適配：隱藏不必要的 padding */
        @media (max-width: 600px) {
            .block-container {
                padding-top: 2rem;
                padding-bottom: 1rem;
            }
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 5. 主程式入口
# ==========================================

def main():
    st.set_page_config(
        page_title="Streamlit 雲端猜數字", 
        page_icon="🎲",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 初始化 Supabase
    if 'supabase' not in st.session_state:
        st.session_state.supabase = init_supabase_client()
    supabase = st.session_state.supabase

    # 注入 CSS
    inject_custom_css()

    # 初始化遊戲變數
    if 'target_number' not in st.session_state:
        st.session_state.player_name = "Guest"
        init_game()

    # --- 頂部標題與資訊 ---
    st.markdown('<h1 class="main-title">🎲 雲端數字大冒險</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="app-info">作者：{APP_AUTHOR} &nbsp;|&nbsp; 版本：{APP_VERSION}</div>', unsafe_allow_html=True)

    # --- 側邊欄：設定與排行榜 ---
    with st.sidebar:
        st.markdown("### 👤 玩家設定")
        player_name = st.text_input("輸入大名 (必填)", value=st.session_state.player_name, max_chars=12, help="輸入你的名字以上傳成績")
        if player_name:
            st.session_state.player_name = player_name
            
        st.divider()
        
        # 排行榜按鈕與邏輯
        st.markdown("### 🏆 全球風雲榜")
        show_leaderboard = st.button("📊 查看全球 Top 10", use_container_width=True)
        
        with st.expander("展開排行榜", expanded=True):
            if supabase:
                with st.spinner("連線中..."):
                    leaderboard = get_global_best(supabase)
                
                if leaderboard:
                    # 原生 HTML 表格渲染
                    table_html = '<table class="rank-table"><thead><tr><th>#</th><th>玩家</th><th>次數</th></tr></thead><tbody>'
                    for idx, row in enumerate(leaderboard):
                        rank_cls = f"rank-{idx+1}" if idx < 3 else ""
                        icon = ["🥇", "🥈", "🥉"][idx] if idx < 3 else f"{idx+1}"
                        
                        table_html += f'<tr class="{rank_cls}"><td>{icon}</td><td>{row["player_name"]}</td><td style="text-align:center">{row["score"]}</td></tr>'
                    table_html += '</tbody></table>'
                    st.markdown(table_html, unsafe_allow_html=True)
                else:
                    st.info("暫無資料")
            else:
                st.error("無法連線到排行榜")

        st.markdown("---")
        if st.button("🔄 重新載入排行榜"):
            st.cache_resource.clear()
            st.rerun()

    # --- 中央遊戲區 (響應式設計) ---
    col_spacer_l, col_game, col_spacer_r = st.columns([1, 6, 1])
    
    with col_game:
        st.markdown('<div class="game-card">', unsafe_allow_html=True)
        
        st.markdown(f"### 🎯 目標：{st.session_state.low_bound} ~ {st.session_state.high_bound}")
        
        if st.session_state.player_name == "Guest" or not st.session_state.player_name.strip():
            st.warning("👉 請先在左側輸入名字才能開始！")
        else:
            with st.form(key=f"game_form_{st.session_state.input_key}"):
                col_in1, col_in2 = st.columns([3, 1])
                with col_in1:
                    user_guess = st.number_input(
                        "輸入數字", 
                        min_value=st.session_state.low_bound, 
                        max_value=st.session_state.high_bound,
                        label_visibility="collapsed"
                    )
                with col_in2:
                    submit = st.form_submit_button("🔥 猜！", use_container_width=True)

            if submit and not st.session_state.game_over:
                st.session_state.count += 1
                guess = int(user_guess)
                target = st.session_state.target_number
                
                st.session_state.current_game_history.append(guess)
                
                if guess == target:
                    st.session_state.game_over = True
                    st.session_state.message = f"🎉 太棒了！答案正是 {target}。<br>你總共猜了 <b>{st.session_state.count}</b> 次！"
                    st.session_state.message_type = "success"
                    
                    save_score_to_cloud(supabase, st.session_state.player_name, st.session_state.count)
                    
                    st.balloons()
                    st.markdown("""
                    <style>
                    @keyframes confetti-fall {
                        0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
                        100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                elif guess < target:
                    st.session_state.low_bound = max(st.session_state.low_bound, guess + 1)
                    st.session_state.message = f"❌ {guess} 太小了！<br>範圍縮小至：{st.session_state.low_bound} ~ {st.session_state.high_bound}"
                    st.session_state.message_type = "warning"
                
                    st.session_state.input_key += 1
                    st.rerun()
                else:
                    st.session_state.high_bound = min(st.session_state.high_bound, guess - 1)
                    st.session_state.message = f"❌ {guess} 太大了！<br>範圍縮小至：{st.session_state.low_bound} ~ {st.session_state.high_bound}"
                    st.session_state.message_type = "warning"
                
                    st.session_state.input_key += 1
                    st.rerun()

            if st.session_state.message_type == "success":
                st.success(st.session_state.message, icon="🏆")
            elif st.session_state.message_type == "warning":
                st.warning(st.session_state.message, icon="📉")
            else:
                st.info(st.session_state.message, icon="🤖")

            if st.session_state.game_over:
                if st.button("🔄再來一局 (Play Again)", type="primary", use_container_width=True):
                    init_game()
                    st.rerun()
                    
            if st.session_state.current_game_history:
                st.caption("👣 本局足跡：" + " → ".join(map(str, st.session_state.current_game_history)))

        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
