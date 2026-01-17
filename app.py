import streamlit as st
from groq import Groq
import os

st.set_page_config(page_title="星穹鐵道-雙星之命 (極速對齊版)", layout="wide")

# --- 1. 極速搜尋函數 (不佔用大量記憶體) ---
def find_mission_content(target_title):
    file_path = "HSR_Full_Story_Wiki.txt"
    if not os.path.exists(file_path): return None
    
    content = []
    found = False
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if f"【頁面標題】: {target_title}" in line:
                found = True
                continue
            if found:
                if "【頁面標題】:" in line: break # 讀到下一個標題就停止
                # 過濾 Wiki 雜質
                if any(x in line for x in ["编", "刷", "历", "短", "阅", "首页", "WIKI"]): continue
                content.append(line)
    
    result = "".join(content).strip()
    return result if len(result) > 50 else None # 如果內容太短，視為無有效劇本

# --- 初始化 ---
if "messages" not in st.session_state: st.session_state.messages = []
if "curr_mission" not in st.session_state: st.session_state.curr_mission = "今天是昨天的明天"

with st.sidebar:
    st.title("🚂 劇本精確引擎")
    api_key = st.text_input("Groq API Key", type="password")
    huiye_info = st.text_area("輝夜設定：", value="輝夜：主角雙胞胎，白髮紅瞳，星核載體。")
    
    target = st.text_input("🔍 輸入任務名稱 (例如: 混乱行至深处):", value=st.session_state.curr_mission)
    if st.button("鎖定並讀取"):
        st.session_state.curr_mission = target
        st.session_state.messages = []
        st.rerun()

# --- 核心邏輯 ---
mission_script = find_mission_content(st.session_state.curr_mission)

if not mission_script:
    st.warning(f"⚠️ 在檔案中找不到「{st.session_state.curr_mission}」的完整劇本。AI 此時可能會根據通用知識回覆。建議手動將劇本貼入檔案中。")
    mission_script = "（檔案內無此段劇本）"

def run_ai():
    if not api_key: return
    client = Groq(api_key=api_key)
    
    sys_prompt = f"""
    你現在是劇本演繹器。
    【強制指令】：
    1. 你只能使用【劇本內容】進行演出。
    2. 如果【劇本內容】標註為無，請禮貌告知使用者『劇本資料缺失，無法演出』。
    3. 插入輝夜：將原本對主角說的話改為對「你們雙胞胎」說，並加入輝夜的冷淡描寫。
    
    【輝夜人設】：{huiye_info}
    【劇本內容】：{mission_script[:5000]}
    """
    
    with st.chat_message("assistant"):
        msgs = [{"role": "system", "content": sys_prompt}] + st.session_state.messages
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, temperature=0.1, stream=True)
        full_res = ""
        placeholder = st.empty()
        for chunk in response:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})

# --- UI ---
st.header(f"當前進度：{st.session_state.curr_mission}")
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if len(st.session_state.messages) == 0: run_ai()

if p := st.chat_input("輸入行動..."):
    st.session_state.messages.append({"role": "user", "content": p})
    st.rerun()
