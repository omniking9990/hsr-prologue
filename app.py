import streamlit as st
from groq import Groq
import os
import re

# --- 頁面初始設定 ---
st.set_page_config(page_title="星穹鐵道-雙星之命 (劇本 100% 強制對齊版)", layout="wide")

# --- 1. 劇本解析優化 (過濾掉 Wiki 雜質) ---
@st.cache_data
def get_clean_mission_db():
    file_path = "HSR_Full_Story_Wiki.txt"
    if not os.path.exists(file_path):
        return {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        full_text = f.read()
    
    # 按照標題切割
    sections = full_text.split("【頁面標題】:")
    db = {}
    for s in sections:
        if "【來源連結】" in s:
            lines = s.strip().split("\n")
            title = lines[0].strip()
            # 關鍵：過濾掉 Wiki 的導航文字（編、刷、閱等）
            content = s.split("========================================")[-1]
            # 只保留有對話或描述的部分
            clean_content = re.sub(r'(編\n|刷\n|歷\n|短\n|閱\n|首页\n|>\n)', '', content)
            db[title] = clean_content.strip()
    return db

# --- 初始化 ---
if "messages" not in st.session_state: st.session_state.messages = []
if "db" not in st.session_state: st.session_state.db = get_clean_mission_db()
if "curr_mission" not in st.session_state: st.session_state.curr_mission = "今天是昨天的明天"

# --- 側邊欄 ---
with st.sidebar:
    st.title("🚂 劇本強制執行器")
    api_key = st.text_input("Groq API Key", type="password")
    
    st.subheader("👤 輝夜人設")
    huiye_info = st.text_area("設定：", value="輝夜：主角的雙胞胎，白髮紅瞳、白毛衣、黑包臀裙、黑高跟鞋。體內有星核。冷淡、與主角有感應。")
    
    st.markdown("---")
    # 劇情選擇
    m_list = list(st.session_state.db.keys())
    if m_list:
        choice = st.selectbox("📌 鎖定劇本位置：", m_list, index=m_list.index(st.session_state.curr_mission) if st.session_state.curr_mission in m_list else 0)
        if choice != st.session_state.curr_mission:
            st.session_state.curr_mission = choice
            st.session_state.messages = []
            st.rerun()

    if st.button("⏭️ 下一段劇情"): st.session_state.auto = True
    if st.button("🔄 徹底重置"): 
        st.session_state.messages = []
        st.rerun()

# --- 核心生成 (強迫 AI 成為「讀稿機」) ---
def run_strict_engine(prompt_override=None):
    if not api_key:
        st.error("請輸入 API Key")
        return

    client = Groq(api_key=api_key)
    script = st.session_state.db.get(st.session_state.curr_mission, "無內容")
    
    # 【最關鍵的指令修改】
    system_prompt = f"""
    你現在不是一個自由創作的 AI，你是一個「劇本播報員」。
    
    【你的唯一任務】：
    1. 讀取下方的【官方劇本原文】，並「逐字逐句」地演出當前的對話。
    2. 絕對不准跳過任何一行對白，尤其是『系统时间』或角色的台詞。
    3. 插入角色：劇本中對「開拓者/主角」的台詞，請改為對「主角與輝夜」說。
    4. 描寫：在對白之間，請根據【輝夜人設】加入她的動作細節（如：冷漠地踩著高跟鞋走過）。
    5. 禁止編造：如果劇本這一段結束了，就停下來，不要自己寫後續。

    【輝夜人設】：{huiye_info}
    【當前劇本原文】：
    {script[:6000]} 
    """

    with st.chat_message("assistant"):
        # 決定當前進度
        if len(st.session_state.messages) == 0:
            user_msg = "【指令】：開始第一幕。請從劇本的第一行（通常是系統時間或背景描述）開始演繹。"
        else:
            user_msg = prompt_override if prompt_override else "【指令】：請繼續演出劇本的下一段對話。"

        msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role": "user", "content": user_msg}]
        
        # 使用低 Temperature (0.1) 確保 AI 變笨、變死板（這正是我們要的，讓它只會讀稿）
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=msgs,
            temperature=0.1, 
            stream=True
        )
        
        full_res = ""
        placeholder = st.empty()
        for chunk in response:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})

# --- 主畫面 ---
st.title(f"📖 任務中：{st.session_state.curr_mission}")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if len(st.session_state.messages) == 0:
    run_strict_engine()

if st.session_state.get("auto", False):
    st.session_state.auto = False
    run_script_step = "請接續上一段劇情，演出劇本中接下來的對話。確保一字不差。"
    run_strict_engine(run_script_step)

if p := st.chat_input("輸入輝夜的動作..."):
    st.session_state.messages.append({"role": "user", "content": p})
    with st.chat_message("user"): st.markdown(p)
    run_strict_engine(f"輝夜行動了：{p}。請根據此行動，並接續劇本原文演出。")
