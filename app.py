import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
from duckduckgo_search import DDGS

# --- 頁面設定 ---
st.set_page_config(page_title="崩壞：星穹鐵道 - 序章啟動", layout="wide", page_icon="🎻")

# --- 側邊欄 ---
with st.sidebar:
    st.title("⚙️ 星核獵手終端")
    api_key = st.text_input("輸入 Groq API Key", type="password", help="請輸入 gsk_ 開頭的密碼")
    st.markdown("---")
    if st.button("🔄 重置劇情 (回到序章)"):
        st.session_state.messages = []
        st.rerun()

# --- 核心：Wiki 爬蟲 ---
def search_wiki(query):
    try:
        results = DDGS().text(f"{query} site:wiki.biligame.com/sr", max_results=2)
        context = ""
        if results:
            for res in results:
                try:
                    resp = requests.get(res['href'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    text = soup.find('div', {'class': 'mw-parser-output'}).get_text()[:600]
                    context += f"\n[資料來源:{res['title']}]\n{text}\n"
                except: continue
        return context
    except: return ""

# --- 核心：系統提示詞 (強制劇情版) ---
system_prompt = """
你現在是「崩壞：星穹鐵道」的遊戲運算核心。
【當前階段】：序章 - 昨夜的第82次敲門 (黑塔太空站)
【登場角色】：卡夫卡 (Kafka)、銀狼 (Silver Wolf)、反物質軍團
【絕對規則】：
1. **開場鎖定**：劇情必須從「卡夫卡在混亂的太空站中憑空拉著隱形小提琴」開始，優雅地迎接反物質軍團的入侵。
2. **深度運算**：回復前必須包含 `(深度運算):` 區塊，分析當前劇情點與 Wiki 資料。
3. **角色語氣**：
   - 卡夫卡：優雅、神秘、喜歡聽古典樂、將戰鬥視為舞蹈。
   - 銀狼：駭客語氣、覺得無聊、把現實當作遊戲、喜歡吹泡泡糖。
4. **推進節奏**：極度緩慢。不要直接跳到召喚主角，先描寫卡夫卡與銀狼的會合與互動。
5. **格式**：
   (深度運算): [分析...]
   **[角色名]**: "對話..."
   *動作描寫...*
"""

# --- 初始化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 介面 UI ---
st.title("🎻 崩壞：星穹鐵道 - 沉浸式序章")
st.caption("Auto-Wiki Search | Deep Thinking | Prologue Mode")

# 顯示對話
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 自動開場邏輯 ---
if len(st.session_state.messages) == 0:
    if st.button("🎬 開始遊戲 (播放序章動畫)"):
        start_instruction = "請根據崩壞星穹鐵道的遊戲開頭，描寫黑塔太空站遭到反物質軍團攻擊，場面混亂，然後鏡頭轉到卡夫卡伴隨著《卡農》的旋律，優雅地在爆炸中拉著隱形小提琴的場景。"
        st.session_state.messages.append({"role": "user", "content": start_instruction})
        
        # 強制觸發 AI 回應
        if api_key:
            client = Groq(api_key=api_key)
            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_res = ""
                stream = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        placeholder.markdown(full_res + "▌")
                placeholder.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                st.rerun()
        else:
            st.warning("請先在左側輸入 Groq API Key 才能開始序章！")

# --- 玩家輸入 ---
if prompt := st.chat_input("輸入你的行動 (此階段你是劇情的推動者/鏡頭)..."):
    if not api_key:
        st.error("請輸入 API Key！")
        st.stop()
        
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 爬蟲與生成
    wiki_info = search_wiki(prompt + " 崩壞星穹鐵道")
    
    client = Groq(api_key=api_key)
    msgs = [
        {"role": "system", "content": f"{system_prompt}\n\n【Wiki資料】:\n{wiki_info}"}
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
