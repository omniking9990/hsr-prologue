import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
from urllib.parse import urljoin

# --- 頁面設定 ---
st.set_page_config(page_title="星穹鐵道-雙星之命 (Wiki 全自動爬蟲版)", layout="wide", page_icon="🥀")

# ==========================================
# 核心設定：輝夜與雙星核同步
# ==========================================
PLAYER_INFO = """
【核心載體設定：輝夜 (Huiye)】
- 形象：170cm/50kg/36B、白長髮漸變紅、紅瞳、白毛衣、黑包臀裙、黑高跟鞋、蝙蝠刺青。
- 能力：控制血液(血構武器)、變形。
- 劇情身分：與主角(星/穹)互為「雙胞胎」載體，兩人體內皆被卡芙卡植入星核。
"""

BILI_BASE = "https://wiki.biligame.com/sr/"
MISSION_LIST_URL = urljoin(BILI_BASE, "开拓任务")

# ==========================================
# 深度爬蟲引擎：抓取完整 Wiki 劇本
# ==========================================
def get_mission_script(mission_name):
    """
    從 Wiki 抓取特定任務的完整劇本。
    """
    try:
        # 1. 搜尋特定任務的 URL
        target_url = urljoin(BILI_BASE, mission_name)
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(target_url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        
        if resp.status_code != 200:
            return f"無法找到任務：{mission_name} 的頁面。"

        soup = BeautifulSoup(resp.text, 'html.parser')
        content = soup.find('div', {'class': 'mw-parser-output'})
        
        if not content:
            return "頁面結構異常，無法抓取劇本。"

        # 2. 清理無效內容 (導航列、目錄等)
        for junk in content.find_all(['table', 'div'], class_=['navbox', 'toc', 'wikitable']):
            # 這裡要注意：Wiki 的對話有時在表格內，有時在文字段落，保留文字部分
            pass
            
        script_text = content.get_text(separator="\n", strip=True)
        # 限制長度以符合 AI Context (約 3000 字)
        return script_text[:4000] 
    except Exception as e:
        return f"爬蟲發生錯誤: {str(e)}"

# --- 側邊欄控制 ---
with st.sidebar:
    st.title("⚙️ Wiki 深度爬蟲終端")
    api_key = st.text_input("輸入 Groq API Key", type="password")
    
    if st.button("🚀 啟動/重置 (從 Wiki 索引開始)"):
        st.session_state.messages = [] 
        st.session_state.started = True 
        # 初始任務設定為序章第一節
        st.session_state.current_mission = "昨夜的第82次敲门"
        st.rerun()
    
    st.markdown("---")
    if st.session_state.get("started", False):
        st.write(f"當前抓取任務：\n{st.session_state.current_mission}")
        if st.button("⏭️ 繼續劇情 (自動抓取下一段)"):
            st.session_state.auto_next = True
        else:
            st.session_state.auto_next = False

# --- 核心：系統提示詞 (Wiki 全連結模式) ---
system_prompt = f"""
你現在是「崩壞：星穹鐵道」劇本執行引擎。
你的所有輸出必須基於提供給你的 Wiki 爬蟲文本。

【強制規範】：
1. **100% 複刻對白**：除了將原本針對一人的行動改為針對「主角與輝夜(雙胞胎)」兩人外，不得修改 Wiki 文本中的任何對白。
2. **視覺描寫**：請根據 Wiki 描述的場景，加入對輝夜(白毛衣、紅瞳、高跟鞋)的動作細節。
3. **無縫銜接**：當玩家不說話時，你必須根據 Wiki 文本流暢地演繹下一段劇情。

【輝夜設定】：{PLAYER_INFO}
"""

# --- 初始化 ---
if "messages" not in st.session_state: st.session_state.messages = []
if "started" not in st.session_state: st.session_state.started = False
if "auto_next" not in st.session_state: st.session_state.auto_next = False

st.title("🚂 星穹演繹：Wiki 全連結深度同步")

# 顯示歷史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# --- AI 生成與爬蟲結合邏輯 ---
def run_game_logic(instruction):
    if not api_key:
        st.error("請輸入 API Key")
        return

    # 即時爬取最新的 Wiki 子網頁內容
    with st.spinner(f"正在深度爬取 Wiki: {st.session_state.current_mission}..."):
        full_script = get_mission_script(st.session_state.current_mission)

    client = Groq(api_key=api_key)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        msgs = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"【當前 Wiki 完整抓取內容】：\n{full_script}"}
        ] + st.session_state.messages + [{"role": "user", "content": instruction}]
        
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

# --- 自動流程控制 ---
if st.session_state.started and len(st.session_state.messages) == 0:
    run_game_logic("請開始『昨夜的第82次敲門』的開頭演出。必須包含通訊對話：『系统时间23时47分15秒，你很准时，卡芙卡。』，並描述輝夜站在卡芙卡身邊的場景。")

elif st.session_state.auto_next:
    run_game_logic("請根據 Wiki 劇本，繼續演出下一段。包含卡芙卡優雅踱步、掃除軍團、以及最後準備植入星核的過程。")
    st.session_state.auto_next = False
    st.rerun()

# --- 玩家輸入 ---
if len(st.session_state.messages) > 0:
    if prompt := st.chat_input("輸入輝夜的行動，或點擊左側『繼續劇情』..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        run_game_logic(f"玩家行動：{prompt}。請繼續結合 Wiki 劇本內容進行後續演繹。")
