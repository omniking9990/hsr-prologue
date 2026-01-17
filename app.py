import streamlit as st
from groq import Groq
import os
import re

# --- 頁面初始設定 ---
st.set_page_config(page_title="星穹鐵道-雙星之命 (100% 劇本同步版)", layout="wide")

# --- 1. 深度清洗與索引劇本 ---
@st.cache_data
def load_and_index_script():
    file_path = "HSR_Full_Story_Wiki.txt"
    if not os.path.exists(file_path):
        return {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    
    # 按照「【頁面標題】:」來切分不同任務
    sections = raw_text.split("【頁面標題】:")
    db = {}
    for s in sections:
        if "【來源連結】" in s:
            lines = s.strip().split("\n")
            title = lines[0].strip()
            # 獲取主要內容並進行「強力清洗」
            body = s.split("========================================")[-1]
            # 刪除所有 Wiki 導航按鈕、垃圾字元
            body = re.sub(r'(编|刷|历|短|阅|首页|>\n|Ctrl\+D|WIKI功能|编辑|任务导航|命路歧图)', '', body)
            # 刪除連續的空行
            body = re.sub(r'\n\s*\n', '\n', body)
            db[title] = body.strip()
    return db

# --- 初始化 ---
if "messages" not in st.session_state: st.session_state.messages = []
if "script_db" not in st.session_state: st.session_state.script_db = load_and_index_script()
if "curr_mission" not in st.session_state: st.session_state.curr_mission = "今天是昨天的明天"

# --- 側邊欄：強勢控制 ---
with st.sidebar:
    st.title("🚂 劇本對齊引擎")
    api_key = st.text_input("Groq API Key", type="password")
    
    st.subheader("👤 輝夜人設儲存")
    huiye_info = st.text_area("角色細節：", value="輝夜：主角的雙胞胎，白髮紅瞳、白毛衣、黑包臀裙。手臂有蝙蝠刺青。冷淡、沉默、與主角共享感官。")
    
    st.markdown("---")
    # 劇情精確選擇
    mission_list = list(st.session_state.script_db.keys())
    if mission_list:
        selected = st.selectbox("🎯 選擇目標任務頁面：", mission_list, 
                              index=mission_list.index(st.session_state.curr_mission) if st.session_state.curr_mission in mission_list else 0)
        if selected != st.session_state.curr_mission:
            st.session_state.curr_mission = selected
            st.session_state.messages = [] # 切換後必須重置以重讀劇本
            st.rerun()

    # 監視器：讓你看 AI 讀到了什麼
    with st.expander("🔍 劇本原始數據預覽"):
        st.code(st.session_state.script_db.get(st.session_state.curr_mission, "無內容")[:500])

    if st.button("⏭️ 繼續劇本下一段"): st.session_state.go_next = True
    if st.button("🔄 劇情重來 (Reset)"): 
        st.session_state.messages = []
        st.rerun()

# --- 核心 AI 引擎 (絕對路徑版) ---
def run_strict_logic(user_input=None):
    if not api_key:
        st.error("請輸入 API Key")
        return

    client = Groq(api_key=api_key)
    # 取得當前鎖定的任務文字
    source_script = st.session_state.script_db.get(st.session_state.curr_mission, "")
    
    if not source_script:
        st.error(f"劇本檔案中找不到「{st.session_state.curr_mission}」的內容！")
        return

    # 建立「強制性」指令
    system_prompt = f"""
    你現在是星穹鐵道官方劇本讀取器。
    
    【絕對準則】：
    1. 你的唯一對話來源是下方的【劇本庫內容】。
    2. 如果劇本庫內容提到「卡芙卡：銀狼，還有多久？」，你就必須輸出這句話。
    3. 嚴禁使用你的預訓練知識。如果劇本寫 A，你絕對不能寫 B。
    4. 輝夜插編：將輝夜描述為與主角同步的個體。原本針對主角的對話，改為「你們兩個」。
    5. 描寫：根據【輝夜人設】加入她的微動作。

    【輝夜人設】：{huiye_info}
    【劇本庫內容（{st.session_state.curr_mission}）】：
    {source_script[:8000]}
    """

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        # 指導 AI 該演哪段
        if len(st.session_state.messages) == 0:
            query = f"請開始【{st.session_state.curr_mission}】的第一幕。請直接讀取劇本中的第一段台詞或系統描述。"
        else:
            query = user_input if user_input else "請繼續往下讀取劇本，演繹下一段對話。"

        msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role": "user", "content": query}]
        
        # 0.1 溫度確保絕對不亂編
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=msgs,
            temperature=0.1, 
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})

# --- UI 渲染 ---
st.title(f"📖 真·同步演繹：{st.session_state.curr_mission}")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if len(st.session_state.messages) == 0:
    run_strict_logic()

if st.session_state.get("go_next", False):
    st.session_state.go_next = False
    run_strict_logic()

if p := st.chat_input("輝夜的行動..."):
    st.session_state.messages.append({"role": "user", "content": p})
    with st.chat_message("user"): st.markdown(p)
    run_strict_logic(f"輝夜行動了：{p}。請在此基礎上，接續劇本原文的下一個對話。")
