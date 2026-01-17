import streamlit as st
from groq import Groq
import os

# --- 頁面初始設定 ---
st.set_page_config(page_title="星穹鐵道-雙星之命 (Wiki 全同步終端)", layout="wide", page_icon="🥀")

# --- 1. 讀取爬好的劇本庫 ---
def load_full_script():
    if os.path.exists("HSR_Full_Story_Wiki.txt"):
        with open("HSR_Full_Story_Wiki.txt", "r", encoding="utf-8") as f:
            content = f.read()
        # 根據標題切割劇本，建立索引
        sections = content.split("【頁面標題】:")
        mission_map = {}
        for sec in sections:
            if "【來源連結】" in sec:
                title = sec.split("\n")[0].strip()
                mission_map[title] = sec
        return mission_map
    else:
        st.error("找不到 HSR_Full_Story_Wiki.txt！請確保檔案已上傳至 GitHub 資料夾。")
        return {}

# --- 初始化 Session ---
if "mission_db" not in st.session_state:
    st.session_state.mission_db = load_full_script()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_mission" not in st.session_state:
    st.session_state.current_mission = "今天是昨天的明天" # 預設起點

# --- 側邊欄 ---
with st.sidebar:
    st.title("🚂 劇情控制器")
    api_key = st.text_input("輸入 Groq API Key", type="password")
    
    st.markdown("---")
    # 功能 2：輸入人設
    st.subheader("👤 人設設定")
    player_bio = st.text_area("輸入輝夜的人設：", value="輝夜：170cm/50kg/36B、白長髮漸變紅、紅瞳、白毛衣、黑包臀裙、黑高跟鞋、蝙蝠刺青。與主角是雙胞胎。")
    
    st.markdown("---")
    st.subheader("📍 任務導航")
    mission_list = list(st.session_state.mission_db.keys())
    if mission_list:
        selected_mission = st.selectbox("選擇當前所在任務：", mission_list, index=mission_list.index(st.session_state.current_mission) if st.session_state.current_mission in mission_list else 0)
        if selected_mission != st.session_state.current_mission:
            st.session_state.current_mission = selected_mission
            st.session_state.messages = [] # 切換任務重置對話
    
    st.markdown("---")
    # 功能 1：繼續劇情按鈕
    if st.button("⏭️ 繼續劇情 (自動演繹下段)"):
        st.session_state.trigger_auto = True
    else:
        st.session_state.trigger_auto = False

# --- 核心 AI 生成邏輯 ---
def run_ai(user_action=None):
    if not api_key:
        st.error("請提供 API Key")
        return

    client = Groq(api_key=api_key)
    
    # 獲取當前任務劇本
    raw_script = st.session_state.mission_db.get(st.session_state.current_mission, "劇本載入中...")
    
    system_prompt = f"""
    你現在是《崩壞：星穹鐵道》官方劇本執行引擎。
    
    【當前任務劇本】：
    {raw_script[:8000]} # 限制長度確保穩定
    
    【玩家人設】：
    {player_bio}
    
    【遊戲規則】：
    1. 你的輸出必須「完全遵循」劇本內的對話與事件發展。
    2. 主角變更：劇本中所有針對主角的對話，請自動改為對「主角與輝夜(雙胞胎)」兩人說話。
    3. 演出細節：請在台詞之間，詳細描寫輝夜的動作（如：白毛衣的晃動、紅瞳的冷漠注視）。
    4. 禁止編造：若劇本未提及後續，請等待玩家輸入。
    """

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        # 構造消息
        query = user_action if user_action else "請根據劇本內容，演出下一段情節。若有對話請直接開始。"
        msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role": "user", "content": query}]
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=msgs,
            stream=True
        )
        for chunk in completion:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- 主畫面渲染 ---
st.title(f"📖 雙星之軌：{st.session_state.current_mission}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 初始或觸發邏輯
if len(st.session_state.messages) == 0:
    run_ai()

if st.session_state.get("trigger_auto", False):
    run_ai()

if prompt := st.chat_input("輝夜的行動 (例如：冷冷地看著卡芙卡)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    run_ai(prompt)
