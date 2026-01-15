import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
from duckduckgo_search import DDGS
import time

# --- 頁面設定 ---
st.set_page_config(page_title="崩壞：星穹鐵道 (劇情還原版)", layout="wide", page_icon="🎻")

# ==========================================
# 核心資料庫 (源自你上傳的 Get_SR_Data.py)
# 我們直接讓 AI 記住這些，省去爬蟲時間
# ==========================================
WORLD_DATA = """
【已知角色清單 (Ver 3.8)】:
- 星穹列車: 星, 穹, 姬子, 瓦爾特, 丹恆, 三月七, 帕姆
- 星核獵手: 卡芙卡, 流螢, 刃, 銀狼, 薩姆, 艾利歐
- 黑塔太空站: 黑塔, 阮•梅, 艾絲妲, 螺絲咕姆, 真理醫生
- 仙舟/貝洛伯格/匹諾康尼: (已知全形色, 包含飛霄, 黃泉, 砂金等)
- 翁法羅斯 & 泰坦諸神: 阿格萊雅, 大麗花, 緹霓, 萬敵, 遐蝶, 那刻夏, 風蘆, 賽飛兒, 白厄, 海瑟音, 刻律德拉, 長夜月, 丹恆•騰荒, 昔連, 亂破
- FATE連動: Archer, Saber, Lancer, 遠坂凜, 衛宮士郎
- 泰坦十二神: 雅努斯, 塔蘭頓, 歐洛尼斯...等

【時間軸與劇情進度】:
目前包含至 3.8 版本「記憶是夢的開場白」以及 FATE 連動「美夢與聖杯」。
"""

# --- 側邊欄 ---
with st.sidebar:
    st.title("⚙️ 系統終端")
    api_key = st.text_input("輸入 Groq API Key", type="password")
    st.caption("輸入 Key 後，點擊下方按鈕開始序章")
    
    # 這個按鈕是「啟動鍵」
    if st.button("🚀 啟動/重置劇情 (Start Game)"):
        st.session_state.messages = [] # 清空對話
        st.session_state.started = True # 標記為已開始
        st.rerun()

# --- 核心：Wiki 爬蟲 (保持你的深度思考功能) ---
def search_wiki(query):
    try:
        # 針對你的需求，搜尋範圍包含萌娘與B站Wiki
        results = DDGS().text(f"{query} site:wiki.biligame.com/sr OR site:zh.moegirl.org.cn", max_results=2)
        context = ""
        if results:
            for res in results:
                try:
                    resp = requests.get(res['href'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=2)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    text = soup.find('div', {'class': 'mw-parser-output'}).get_text()[:500]
                    context += f"\n[資料來源:{res['title']}]\n{text}\n"
                except: continue
        return context
    except: return ""

# --- 核心：系統提示詞 (System Prompt) ---
system_prompt = f"""
你是一個嚴格遵守「崩壞：星穹鐵道」原作劇情的 RPG 運算核心。
你必須執行以下指令：

1. **全知觀點**：你負責描寫場景、旁白、以及所有 NPC (卡夫卡、銀狼、虛卒等)。
2. **原作還原**：開場必須完全還原遊戲序章：黑塔太空站遭到反物質軍團入侵，混亂的警報聲中，卡夫卡優雅地拉著隱形的小提琴（背景音樂是 Pachelbel 的卡農），直到銀狼出現。
3. **資料引用**：參考以下核心資料庫進行設定：
{WORLD_DATA}

4. **輸出格式**：
   (深度運算): [分析目前的劇情點，決定下一幕的運鏡與音樂]
   **[角色名]**: "對話內容"
   *動作與場景描寫 (請著重於光影、聲音、與角色的優雅感)*

5. **語言**：繁體中文 (Traditional Chinese)。
"""

# --- 初始化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "started" not in st.session_state:
    st.session_state.started = False

# --- 介面 UI ---
st.title("🚂 崩壞：星穹鐵道 (Ver 3.8 資料庫搭載)")

# 顯示對話歷史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 自動開場邏輯 (關鍵修改) ---
# 如果已經按下開始，且訊息是空的，系統自動發送第一則指令
if st.session_state.started and len(st.session_state.messages) == 0:
    if not api_key:
        st.warning("請先在左側輸入 API Key！")
    else:
        # 這是給 AI 的第一道強制指令，使用者看不到，但會觸發劇情
        start_instruction = """
        【系統指令】：立刻開始遊戲序章。
        場景：黑塔太空站「收容艙段」。
        現狀：反物質軍團入侵，爆炸聲四起。
        鏡頭：卡夫卡(Kafka)站在混亂的中心，閉著眼，像是在演奏一首不存在的小提琴曲（卡農變奏）。
        請詳細描寫這個開場，直到銀狼(Silver Wolf)出現打斷她。
        """
        
        client = Groq(api_key=api_key)
        
        # 為了讓使用者知道系統在跑，顯示一個狀態
        with st.chat_message("assistant"):
            with st.status("🎻 正在載入序章資源... (卡農 D大調)", expanded=True):
                st.write("讀取 3.8 資料庫...")
                st.write("同步黑塔太空站地圖...")
                st.write("生成角色：卡夫卡...")
            
            placeholder = st.empty()
            full_res = ""
            
            # 呼叫 AI
            stream = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": start_instruction}],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    placeholder.markdown(full_res + "▌")
            placeholder.markdown(full_res)
            
        # 將 AI 的開場白存入記憶，但不存入使用者的指令(這樣看起來就像AI主動說話)
        st.session_state.messages.append({"role": "assistant", "content": full_res})

# --- 玩家輸入 (開場後才出現) ---
if len(st.session_state.messages) > 0:
    if prompt := st.chat_input("輸入你的行動... (例如：我看著銀狼，問她星核在哪裡)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 爬蟲與生成
        wiki_info = search_wiki(prompt)
        
        client = Groq(api_key=api_key)
        msgs = [
            {"role": "system", "content": f"{system_prompt}\n\n【Wiki即時資料】:\n{wiki_info}"}
        ] + st.session_state.messages
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_res = ""
            stream = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=msgs,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    placeholder.markdown(full_res + "▌")
            placeholder.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
