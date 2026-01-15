import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
from duckduckgo_search import DDGS

# --- 頁面設定 ---
st.set_page_config(page_title="崩壞：星穹鐵道 - 雙星之命", layout="wide", page_icon="🥀")

# ==========================================
# 核心資料庫：雙胞胎載體設定 (輝夜 & 主角)
# ==========================================
TWIN_SETTING = """
【核心設定：雙星核載體】
- 輝夜與主角（星/穹）是命運共同體，被視為「雙胞胎」般的載體。
- 序章：卡芙卡同時將星核放入輝夜與主角體內。
- 輝夜人設：170cm/50kg/36B、白長髮漸變紅、紅瞳、白毛衣、黑包臀裙、黑高跟鞋、血控能力、變形能力、蝙蝠刺青。
- 演出要求：嚴格同步 Wiki 與 YouTube 影片劇情，卡芙卡對「你們」說話。
"""

# --- 側邊欄 ---
with st.sidebar:
    st.title("⚙️ 劇本同步終端")
    api_key = st.text_input("輸入 Groq API Key", type="password")
    st.info("**模式：** 雙胞胎同步還原")
    
    if st.button("🚀 啟動/重置劇情"):
        st.session_state.messages = [] 
        st.session_state.started = True 
        st.rerun()
    
    st.markdown("---")
    # --- 新增：不用說話也能繼續劇情的按鍵 ---
    if st.session_state.get("started", False):
        if st.button("⏭️ 繼續劇情 (Next Segment)"):
            st.session_state.auto_continue = True
        else:
            st.session_state.auto_continue = False

# --- Wiki 子網頁爬蟲 ---
def search_wiki_content(mission_name):
    search_query = f"site:wiki.biligame.com/sr {mission_name} 劇情對話"
    try:
        results = DDGS().text(search_query, max_results=3)
        context = ""
        for res in results:
            try:
                resp = requests.get(res['href'], timeout=3)
                soup = BeautifulSoup(resp.text, 'html.parser')
                context += soup.get_text()[:600] + "\n"
            except: continue
        return context
    except: return ""

# --- 核心：系統提示詞 ---
system_prompt = f"""
你現在是「崩壞：星穹鐵道」劇情演繹核心。
【絕對指令】：
1. **雙胞胎同步**：主角與輝夜(玩家)同時經歷序章。
2. **還原度100%**：嚴格遵守 Wiki 劇本。當前任務：「昨夜的第82次敲門」。
3. **視角**：以輝夜與主角為中心，細膩描寫兩人的甦醒與互動。

【輝夜資料庫】：{TWIN_SETTING}

【輸出格式】：
(深度運算): [分析下一段 Wiki 劇本節奏]
**[角色名]**: "對話"
*動作/心理/場景描寫*
"""

# --- 初始化 ---
if "messages" not in st.session_state: st.session_state.messages = []
if "started" not in st.session_state: st.session_state.started = False
if "auto_continue" not in st.session_state: st.session_state.auto_continue = False

st.title("🚂 星穹演繹：雙星軌跡 (自動劇情版)")

# 顯示歷史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# --- 處理 AI 生成的通用函數 ---
def generate_ai_response(instruction):
    client = Groq(api_key=api_key)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        wiki_info = search_wiki_content("昨夜的第82次敲門 劇情")
        msgs = [{"role": "system", "content": f"{system_prompt}\nWiki資料：{wiki_info}"}] + \
               st.session_state.messages + [{"role": "user", "content": instruction}]
        
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=msgs,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})

# --- 自動序章啟動 ---
if st.session_state.started and len(st.session_state.messages) == 0:
    if api_key:
        generate_ai_response("【劇本開始】：請詳細演出卡芙卡將星核放入主角與輝夜(白毛衣紅裙)體內，並對兩人說出『聽我說』後，兩人同時睜開眼的場景。請嚴格遵守 Wiki 對話。")
    else:
        st.warning("請輸入 API Key")

# --- 處理「繼續劇情」按鈕 ---
if st.session_state.auto_continue:
    generate_ai_response("【系統指令】：請不要等待玩家操作，直接根據原版劇情影片與 Wiki 文本，繼續推演下一段對話與行動。")
    st.session_state.auto_continue = False # 重置狀態
    st.rerun()

# --- 玩家輸入 (如果想說話時使用) ---
if len(st.session_state.messages) > 0:
    if prompt := st.chat_input("輸入輝夜的行動，或點擊左側『繼續劇情』..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        generate_ai_response(prompt)
