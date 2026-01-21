import streamlit as st
import random
import os
import time
from datetime import datetime
import pandas as pd
from supabase import create_client, Client

# ==========================================
# 1. è¨­å??‡å…¨?Ÿè???
# ==========================================

# ?‰ç”¨ç¨‹å?è³‡è?
APP_AUTHOR = "æ±Ÿä?å»?
APP_VERSION = "1.0.1"

# Supabase è¨­å?
# æ³¨æ?ï¼šç‚ºäº†å??¨ï??‘å€‘ç¾?¨å„ª?ˆå? st.secrets è®€??
# ?¥æœ¬?°é??¼æ???secrets.tomlï¼Œå¯?¨æ­¤å¡«å…¥?è¨­?¼ï?ä½†ä?å»ºè­°ä¸Šå‚³??GitHubï¼?
TABLE_NAME = "high_scores_0121"

def init_supabase_client():
    """?å??–ä¸¦?å‚³ Supabase å®¢æˆ¶ç«?""
    try:
        # ?ªå??—è©¦å¾?secrets è®€??
        if "supabase" in st.secrets:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
            return create_client(url, key)
        else:
            st.error("? ï? ?ªæ‰¾??Supabase è¨­å?ï¼Œè?æª¢æŸ¥ .streamlit/secrets.toml")
            return None
    except Exception as e:
        print(f"?¡æ???¥??Supabase: {e}")
        return None

# ==========================================
# 2. è³‡æ?åº«æ?ä½?
# ==========================================

def get_global_best(client):
    """?–å??¨ç??€ä½³ç??„ï???0?ï?"""
    if not client: return []
    try:
        response = client.table(TABLE_NAME)\
            .select("*")\
            .order("score", desc=False)\
            .limit(10)\
            .execute()
        return response.data
    except Exception as e:
        print(f"è®€?–ç??„å¤±?? {e}") 
        return []

def save_score_to_cloud(client, player_name, score):
    """ä¸Šå‚³?ç¸¾?°é›²ç«?""
    if not client: 
        st.error("? ï? ?¡æ?????°é›²ç«¯è??™åº«ï¼Œè?æª¢æŸ¥ç¶²è·¯??API Key")
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
        st.error(f"ä¸Šå‚³å¤±æ?: {e}")
        return False

# ==========================================
# 3. ?Šæˆ²?¸å??è¼¯
# ==========================================

def init_game():
    """?ç½®?Šæˆ²?€??""
    # æ¸¬è©¦æ¨¡å?ç­”æ? (æ­???ˆè??¹ç‚º random.randint(1, 100))
    st.session_state.target_number = 6 
    
    st.session_state.count = 0
    st.session_state.current_game_history = []
    st.session_state.game_over = False
    
    # ?•æ?ç¯„å??ç¤º
    st.session_state.low_bound = 1
    st.session_state.high_bound = 100
    
    st.session_state.message = f"?? æº–å?å¥½ä??ï?ç­”æ???{st.session_state.low_bound} ??{st.session_state.high_bound} ä¹‹é?"
    st.session_state.message_type = "info"
    
    # æ¸…é™¤è¼¸å…¥æ¡†ç? key ä¾†é?ç½?
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0
    st.session_state.input_key += 1

# ==========================================
# 4. ?ç«¯æ¨?? (CSS)
# ==========================================

def inject_custom_css():
    st.markdown("""
        <style>
        /* ?¨å?å­—å??‡è??¯å„ª??*/
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        /* æ¨™é??‡ç??¬è?è¨?*/
        .main-title {
            text-align: center;
            font-size: clamp(2rem, 5vw, 3rem); /* ?¿æ??¨å?é«?*/
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
        
        /* ?¿æ?å¼å¡?‡å®¹??*/
        .game-card {
            background: white;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            margin: 10px auto;
            max-width: 600px; /* ?‹æ?ä¸Šæ»¿å¯¬ï?å¤§è¢å¹•é??¶å¯¬åº?*/
        }
        
        /* ?’è?æ¦œè¡¨?¼å„ª??*/
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
        
        /* è¨Šæ¯æ¡†å???*/
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
        
        /* å·¦å´?¸å–®?‰é? */
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
        
        /* ?‹æ??©é?ï¼šéš±?ä?å¿…è???padding */
        @media (max-width: 600px) {
            .block-container {
                padding-top: 2rem;
                padding-bottom: 1rem;
            }
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 5. ä¸»ç?å¼å…¥??
# ==========================================

def main():
    st.set_page_config(
        page_title="Streamlit ?²ç«¯?œæ•¸å­?, 
        page_icon="?²",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ?å???Supabase
    if 'supabase' not in st.session_state:
        st.session_state.supabase = init_supabase_client()
    supabase = st.session_state.supabase

    # æ³¨å…¥ CSS
    inject_custom_css()

    # ?å??–é??²è???
    if 'target_number' not in st.session_state:
        st.session_state.player_name = "Guest"
        init_game()

    # --- ?‚éƒ¨æ¨™é??‡è?è¨?---
    st.markdown('<h1 class="main-title">?² ?²ç«¯?¸å?å¤§å???/h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="app-info">ä½œè€…ï?{APP_AUTHOR} &nbsp;|&nbsp; ?ˆæœ¬ï¼š{APP_VERSION}</div>', unsafe_allow_html=True)

    # --- ?´é?æ¬„ï?è¨­å??‡æ?è¡Œæ? ---
    with st.sidebar:
        st.markdown("### ?‘¤ ?©å®¶è¨­å?")
        player_name = st.text_input("è¼¸å…¥å¤§å? (å¿…å¡«)", value=st.session_state.player_name, max_chars=12, help="è¼¸å…¥ä½ ç??å?ä»¥ä??³æ?ç¸?)
        if player_name:
            st.session_state.player_name = player_name
            
        st.divider()
        
        # ?’è?æ¦œæ??•è??è¼¯
        st.markdown("### ?? ?¨ç?é¢¨é›²æ¦?)
        show_leaderboard = st.button("?? ?¥ç??¨ç? Top 10", use_container_width=True)
        
        # ?è¨­ç¸½æ˜¯é¡¯ç¤º?ä??ï?é»æ??‰é??å??ºå??´è?çª—æ??‡æ?æ¨¡å?
        # ?™è£¡?‘å€‘ç›´?¥å??¨å´?Šæ?ä¸‹æ–¹ï¼Œæ??…ç”¨ expander
        
        with st.expander("å±•é??’è?æ¦?, expanded=True):
            if supabase:
                with st.spinner("???ä¸?.."):
                    leaderboard = get_global_best(supabase)
                
                if leaderboard:
                    # ?Ÿç? HTML è¡¨æ ¼æ¸²æ?
                    table_html = '<table class="rank-table"><thead><tr><th>#</th><th>?©å®¶</th><th>æ¬¡æ•¸</th></tr></thead><tbody>'
                    for idx, row in enumerate(leaderboard):
                        rank_cls = f"rank-{idx+1}" if idx < 3 else ""
                        icon = ["??", "??", "??"][idx] if idx < 3 else f"{idx+1}"
                        # ?¥æ??¼å???
                        # date_str = datetime.fromisoformat(row['created_at']).strftime('%m/%d')
                        
                        table_html += f'<tr class="{rank_cls}"><td>{icon}</td><td>{row["player_name"]}</td><td style="text-align:center">{row["score"]}</td></tr>'
                    table_html += '</tbody></table>'
                    st.markdown(table_html, unsafe_allow_html=True)
                else:
                    st.info("?«ç„¡è³‡æ?")
            else:
                st.error("?¡æ?????°æ?è¡Œæ?")

        st.markdown("---")
        if st.button("?? ?æ–°è¼‰å…¥?Šæˆ²", type="secondary"):
            st.rerun()

    # --- ä¸­å¤®?Šæˆ²?€ (?¿æ?å¼è¨­è¨? ---
    # ä½¿ç”¨ columns ä¾†é??¶é›»?¦ç?å¯¬åº¦ï¼Œæ?æ©Ÿç??‡è‡ª?•å???
    col_spacer_l, col_game, col_spacer_r = st.columns([1, 6, 1])
    
    with col_game:
        # å°‡é??²å…§å®¹å??¨å¡?‡ä¸­
        st.markdown('<div class="game-card">', unsafe_allow_html=True)
        
        # ?ç¤º?€
        # ?¹æ? low/high bound é¡¯ç¤º?²åº¦æ¢æ??ç¤º
        st.markdown(f"### ?¯ ?®æ?ï¼š{st.session_state.low_bound} ~ {st.session_state.high_bound}")
        
        if st.session_state.player_name == "Guest" or not st.session_state.player_name.strip():
            st.warning("?? è«‹å??¨å·¦?´è¼¸?¥å?å­—æ??½é?å§‹ï?")
        else:
            # è¼¸å…¥è¡¨å–®
            with st.form(key=f"game_form_{st.session_state.input_key}"):
                col_in1, col_in2 = st.columns([3, 1])
                with col_in1:
                    user_guess = st.number_input(
                        "è¼¸å…¥?¸å?", 
                        min_value=st.session_state.low_bound, 
                        max_value=st.session_state.high_bound,
                        label_visibility="collapsed"
                    )
                with col_in2:
                    submit = st.form_submit_button("ï¿??œï?", use_container_width=True)

            # ?¤æ–·?è¼¯
            if submit and not st.session_state.game_over:
                st.session_state.count += 1
                guess = int(user_guess)
                target = st.session_state.target_number
                
                st.session_state.current_game_history.append(guess)
                
                if guess == target:
                    # ?œå?äº?(?åˆ©)
                    st.session_state.game_over = True
                    st.session_state.message = f"?? å¤ªæ?äº†ï?ç­”æ?æ­?˜¯ {target}??br>ä½ ç¸½?±ç?äº?<b>{st.session_state.count}</b> æ¬¡ï?"
                    st.session_state.message_type = "success"
                    
                    # ä¸Šå‚³?ç¸¾
                    save_score_to_cloud(supabase, st.session_state.player_name, st.session_state.count)
                    
                    # è§¸ç™¼?¶ç??¹æ? (CSS)
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
                    # ?œå¤ªå°?
                    st.session_state.low_bound = max(st.session_state.low_bound, guess + 1)
                    st.session_state.message = f"??{guess} å¤ªå?äº†ï?<br>ç¯„å?ç¸®å??³ï?{st.session_state.low_bound} ~ {st.session_state.high_bound}"
                    st.session_state.message_type = "warning"
                else:
                    # ?œå¤ªå¤?
                    st.session_state.high_bound = min(st.session_state.high_bound, guess - 1)
                    st.session_state.message = f"??{guess} å¤ªå¤§äº†ï?<br>ç¯„å?ç¸®å??³ï?{st.session_state.low_bound} ~ {st.session_state.high_bound}"
                    st.session_state.message_type = "warning"
                
                # ?œéµä¿®æ­£ï¼šç?æ¸¬å?å¼·åˆ¶?·æ–°ä»‹é¢ï¼Œé¿?è¼¸?¥æ??¸å€¼å¡?¨è?ç¯„å?å°è‡´?±éŒ¯
                st.session_state.input_key += 1
                st.rerun()

            # é¡¯ç¤ºè¨Šæ¯
            if st.session_state.message_type == "success":
                st.success(st.session_state.message, icon="??")
            elif st.session_state.message_type == "warning":
                st.warning(st.session_state.message, icon="??")
            else:
                st.info(st.session_state.message, icon="??")

            # ?Šæˆ²çµæ??‰é?
            if st.session_state.game_over:
                if st.button("???ä?ä¸€å±€ (Play Again)", type="primary", use_container_width=True):
                    init_game()
                    st.rerun()
                    
            # é¡¯ç¤º?¬å?æ­·å²
            if st.session_state.current_game_history:
                st.caption("?‘£ ?¬å?è¶³è·¡ï¼? + " ??".join(map(str, st.session_state.current_game_history)))

        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
