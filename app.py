import streamlit as st
from groq import Groq
import os

# --- 頁面初始設定 ---
st.set_page_config(page_title="星穹鐵道-雙星之命 (劇本精確對位版)", layout="wide", page_icon="🥀")

# --- 1. 讀取並建立精確索引 ---
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
            # 這裡只保留真正的劇情對話內容，過濾掉維基導航文字
            content = p.split("========================================")[-1]
            mission_dict[title] = content.strip()
    return mission_dict

# --- 初始化 Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mission_db" not in st.session_state:
    st.session_state.mission_db = get_mission_data()
if "current_mission" not in st.session_state:
    # 修正：確保起點是包含「系統時間」的具體任務名
    st.session_state.current_mission = "今天是昨天的明天" 

# --- 側邊欄：控制面板 ---
with st.sidebar:
    st.title("🚂 劇情精確控制")
    api_key = st.text_input("輸入 Groq API Key", type="password")
    
    # 功能：輸入人設
    st.subheader("👤 輝夜人設設定")
    huiye_bio = st.text_area(
        "設定角色細節：", 
        value="輝夜：170cm/50kg/36B、白長髮漸變紅、紅瞳、白毛衣、黑包臀裙、黑高跟鞋、蝙蝠刺青。與主角是雙胞胎載體。",
        height=100
    )
    
    st.markdown("---")
    # 劇情進度選擇 (確保 AI 知道在哪一章)
    m_list = list(st.session_state.mission_db.keys())
    if m_list:
        idx = m_list.index(st.session_state.current_mission) if st.session_state.current_mission in m_list else 0
        new_mission = st.selectbox("📌 當前進度定位：", m_list, index=idx)
        if new_mission != st.session_state.current_mission:
            st.session_state.current_mission = new_mission
            st.session_state.messages = [] 
            st.rerun()
    
    # 控制按鈕
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏭️ 繼續劇情"):
            st.session_state.auto_step = True
    with col2:
        if st.button("🔄 徹底重來"):
            st.session_state.messages = []
            st.rerun()

# --- 核心 AI 生成函數 ---
def run_script_engine(user_query=None):
    if not api_key:
        st.warning("請輸入 API Key")
        return

    client = Groq(api_key=api_key)
    script_context = st.session_state.mission_db.get(st.session_state.current_mission, "未找到劇本")
    
    # 強制引導 AI 尋找特定關鍵字（如系統時間）
    system_instruction = f"""
    你現在是劇本執行器。你必須嚴格遵守以下規則：
    1. **絕對對標**：從提供的【劇本原文】中找到對應進度。開頭必須包含『系统时间23时47分15秒』等原始對話。
    2. **禁止胡編**：如果劇本裡沒寫到的對話，絕對不能出現。
    3. **雙胞胎插入**：將輝夜描述為主角的姐妹，且兩人同時行動。
    
    【輝夜設定】：{huiye_bio}
    【劇本原文】：
    {script_context[:5000]} 
    """

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        # 決定 Prompt，若剛開始，強制要求開場白
        if len(st.session_state.messages) == 0:
            query = "請從劇本開頭開始演繹，必須包含卡芙卡出現與系統時間的對話。"
        else:
            query = user_query if user_query else "請根據劇本，接續演繹下一段劇情對白。"

        msgs = [{"role": "system", "content": system_instruction}] + st.session_state.messages + [{"role": "user", "content": query}]
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=msgs,
            temperature=0.3, # 降低隨機性，增加準確度
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})

# --- 主畫面 ---
st.title(f"📖 雙星之軌：{st.session_state.current_mission}")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if len(st.session_state.messages) == 0:
    run_script_engine()

if st.session_state.get("auto_step", False):
    st.session_state.auto_step = False
    run_script_engine()

if player_act := st.chat_input("輸入輝夜的行動..."):
    st.session_state.messages.append({"role": "user", "content": player_act})
    with st.chat_message("user"): st.markdown(player_act)
    run_script_engine(player_act)
