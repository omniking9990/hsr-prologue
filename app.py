import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
from duckduckgo_search import DDGS

# --- 設定頁面 ---
st.set_page_config(page_title="崩壞：星穹鐵道 (Groq 極速版)", layout="wide")

# --- 側邊欄：輸入 API Key ---
with st.sidebar:
    st.header("⚙️ 系統設定")
    api_key = st.text_input("請輸入 Groq API Key (gsk_...)", type="password")
    st.caption("🚀 使用 Llama-3-70b 模型 (無需信用卡)")
    st.markdown("---")
    temperature = st.slider("劇情創意度", 0.0, 1.0, 0.6)
    if st.button("🗑️ 重置劇情"):
        st.session_state.messages = []
        st.rerun()

# --- 核心功能：精確爬蟲 (維持不變) ---
def search_wiki(query):
    """
    搜尋 Wiki 並抓取子網頁內容，針對 Llama 3 優化文本長度
    """
    search_query = f"{query} site:wiki.biligame.com/sr OR site:zh.moegirl.org.cn"
    # 使用 DuckDuckGo 搜尋
    try:
        results = DDGS().text(search_query, max_results=2)
    except Exception as e:
        return f"搜尋連線錯誤: {e}"
    
    context_data = ""
    if results:
        for result in results:
            url = result['href']
            title = result['title']
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=3)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 抓取主要內容
                content = soup.find('div', {'class': 'mw-parser-output'})
                if content:
                    # 去除多餘空白，抓取前 1000 字
                    text = content.get_text()
                    cleaned_text = '\n'.join([line.strip() for line in text.splitlines() if line.strip()][:40])
                    context_data += f"\n【資料來源: {title}】\n{cleaned_text}\n"
            except:
                continue
    return context_data

# --- 初始化記憶 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 系統提示詞 (System Prompt) ---
# 針對 Llama 3 模型的特性進行微調，確保它聽得懂指令
system_instruction = """
你現在是「崩壞：星穹鐵道」的 TRPG 核心系統。
你必須嚴格遵守以下指令，不可跳脫角色：

1. **全知多角扮演**：你控制所有 NPC (三月七、丹恆、姬子、路人等) 以及旁白。
2. **深度思考機制 (Chain of Thought)**：
   在每一次回復**之前**，你必須先進行一段邏輯分析，分析格式如下：
   `(深度運算): [分析當前局勢] -> [參考 Wiki 資料] -> [決定角色反應]`
   
3. **資料優先**：我會提供即時的 Wiki 搜尋結果，請務必將這些設定融入劇情 (例如角色的語氣、招式、地點描述)。
4. **慢節奏敘事**：不要急著跳轉時間，著重描寫當下的光影、聲音、氣味。
5. **回應語言**：繁體中文 (Traditional Chinese)。

請注意：你的回覆必須包含 `(深度運算)` 與 `**[角色名]**:` 的對話格式。
"""

# --- 介面呈現 ---
st.title("🚂 星穹列車資料庫 (Llama-3 Ver.)")
st.caption("無需信用卡 | 極速生成 | 聯網檢索")

# 顯示歷史對話
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 使用者輸入處理 ---
if prompt := st.chat_input("輸入你的行動... (例如：我看著三月七，問她這裡是哪裡)"):
    
    if not api_key:
        st.error("❌ 請先在左側輸入 Groq API Key！")
        st.stop()

    # 1. 顯示使用者輸入
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 爬蟲階段
    with st.status("🔍 正在檢索 Wiki 資料庫...", expanded=True) as status:
        st.write(f"正在分析關鍵字：{prompt}")
        wiki_data = search_wiki(prompt + " 崩壞星穹鐵道")
        if wiki_data:
            st.write("✅ 資料獲取成功，正在注入劇情模組。")
        else:
            st.write("⚠️ 無法獲取特定資料，啟用通用劇情模組。")
        status.update(label="檢索完成", state="complete", expanded=False)

    # 3. AI 生成階段 (使用 Groq)
    try:
        client = Groq(api_key=api_key)
        
        # 組合歷史訊息
        messages_payload = [
            {"role": "system", "content": system_instruction},
            {"role": "system", "content": f"【即時 Wiki 資料庫】:\n{wiki_data}"}
        ] + st.session_state.messages

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # 使用 Llama3-70b (目前免費且最強的模型)
            stream = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages_payload,
                temperature=temperature,
                max_tokens=2000,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # 儲存回應
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"系統錯誤：{e}")
        st.info("提示：如果出現錯誤，請檢查 API Key 是否正確複製。")