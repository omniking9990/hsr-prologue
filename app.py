import streamlit as st
from groq import Groq
import os

# --- 頁面初始設定 ---
st.set_page_config(page_title="星穹鐵道-雙星之命 (Wiki 全同步終端)", layout="wide", page_icon="🥀")

# --- 1. 讀取並解析劇本檔案 ---
@st.cache_data
def get_mission_data():
    file_path = "HSR_Full_Story_Wiki.txt"
    if not os.path.exists(file_path):
        return {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        full_content = f.read()
    
    # 根據【頁面標題】切割檔案，建立字典
    parts = full_content.split("【頁面標題】:")
    mission_dict = {}
    for p in parts:
        if "【來源連結】" in p:
            lines = p.strip().split("\n")
            title = lines[0].strip()
            mission_dict[title] = p
    return mission_dict

# --- 初始化 Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mission_db" not in st.session_state:
    st.session_state.mission_db = get_mission_data()
if "current_mission" not in st.session_state:
    st.session_state.current_mission = "今天是昨天的明天" # 預設序章起點

# --- 側邊欄：控制面板 ---
with st.sidebar:
    st.title("🚂 劇本控制中心")
    api_key = st.text_input("輸入 Groq API Key", type="password")
    
    st.markdown("---")
    
    # 功能 2：輸入人設
    st.subheader("👤 輝夜人設設定")
    huiye_bio = st.text_area(
        "設定角色細節：", 
        value="輝夜：170cm/50kg/36B、白長髮漸變紅、紅瞳、白毛衣、黑包臀裙、黑高跟鞋、蝙蝠刺青。與主角(星/穹)是雙胞胎載體，兩人體內皆有星核。",
        height=150
    )
    
    st.markdown("---")
    
    # 劇情進度選擇
    st.subheader("📍 劇情章節")
    m_list = list(st.session_state.mission_db.keys())
    if m_list:
        idx = m_list.index(st.session_state.current_mission) if st.session_state.current_mission in m_list else 0
        new_mission = st.selectbox("選擇當前進度：", m_list, index=idx)
        if new_mission != st.session_state.current_mission:
            st.session_state.current_mission = new_mission
            st.session_state.messages = [] # 切換章節自動重置
            st.rerun()
    
    # 功能 1：繼續劇情按鈕
    if st.button("⏭️ 繼續劇情 (AI 自動演繹)"):
        st.session_state.auto_step = True
    
    # 新增功能：重來按鈕
    if st.button("🔄 徹底重來 (清空對話)"):
        st.session_state.messages = []
        st.session_state.auto_step = False
        st.rerun()

# --- 核心 AI 生成函數 ---
def run_script_engine(user_query=None):
    if not api_key:
        st.warning("請在側邊欄輸入 API Key 以啟動系統。")
        return

    client = Groq(api_key=api_key)
    
    # 提取當前劇本片段
    script_context = st.session_state.mission_db.get(st.session_state.current_mission, "未找到劇本內容")
    
    system_instruction = f"""
    你現在是《崩壞：星穹鐵道》劇本執行器。
    
    【核心任務】：
    1. 必須 100% 根據提供的【劇本原文】進行對話演繹。
    2. 將輝夜（人設如下）作為雙胞胎之一插入劇情。
    3. 對白必須與 Wiki 原文一致（例如：系統時間...）。
    
    【輝夜人設】：{huiye_bio}
    【劇本原文片段】：
    {script_context[:7000]}
    """

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        # 構造 Context
        prompt = user_query if user_query else "請根據劇本內容，演出下一段對話或場景描述。如果還沒開始，請從開頭開始。"
        msgs = [{"role": "system", "content": system_instruction}] + st.session_state.messages + [{"role": "user", "content": prompt}]
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=msgs,
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})

# --- 主畫面演繹 ---
st.title(f"📖 雙星之軌：{st.session_state.current_mission}")

# 顯示對話歷史
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 初始觸發
if len(st.session_state.messages) == 0:
    run_script_engine()

# 按鈕觸發
if st.session_state.get("auto_step", False):
    st.session_state.auto_step = False # 重置狀態
    run_script_engine()

# 玩家手動輸入
if player_act := st.chat_input("輸入輝夜的行動或對話..."):
    st.session_state.messages.append({"role": "user", "content": player_act})
    with st.chat_message("user"):
        st.markdown(player_act)
    run_script_engine(player_act)
