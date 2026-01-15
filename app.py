import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
from duckduckgo_search import DDGS

# --- 頁面設定 ---
st.set_page_config(page_title="星穹鐵道-雙星之命 (終極還原版)", layout="wide", page_icon="🥀")

# ==========================================
# 1. 硬核劇本庫：昨夜的第82次敲門 (精確對照 Wiki 文本)
# ==========================================
# 這裡儲存的是絕對不會改變的劇本基石
EXACT_SCRIPT_BASE = {
    "prologue_start": """
【場景：收容艙段 - 監控室外】
(遠處傳來劇烈的爆炸聲，警報紅光閃爍)
卡芙卡：(閉著眼，優雅地懸空撥動手指，彷彿在拉奏一把隱形的小提琴) 「...就快了。」
(虛卒衝向卡芙卡，銀狼駭入系統，虛卒瞬間被空間數據抹除)
銀狼： 「你還有心思拉琴？反物質軍團已經把這裡包圍了。」
卡芙卡： 「這不是有你在嗎？銀狼。而且，這首曲子很適合現在的氣氛。」
銀狼： 「隨你便。星核的地點已經鎖定了，就在前方。」
    """,
    "stellaron_insertion": """
【場景：星核置放處】
銀狼： 「載體準備好了，妳要選哪一個？」
卡芙卡： 「艾利歐說過，這是必然的選擇——(看著眼前的兩具載體)」
(卡芙卡優雅地伸出雙手，左手握住主角的星核，右手握住輝夜的星核)
卡芙卡： 「聽我說：你們的腦袋裡現在一片空白，但沒關係...」
(星核緩緩沒入主角與輝夜的胸口，兩人的心跳聲重合)
卡芙卡： 「醒來吧，你們將開始一段新的旅程。」
    """
}

# ==========================================
# 2. 玩家人設：輝夜 (雙胞胎載體設定)
# ==========================================
PLAYER_INFO = """
【玩家：輝夜】
- 形象：170cm/50kg/36B、白長髮漸變紅、紅瞳、白毛衣、黑包臀裙、黑高跟鞋、蝙蝠刺青。
- 能力：控制血液(血構武器)、變形小動物。
- 宿命：與主角同時被植入星核，互為雙生載體。
"""

# --- 側邊欄控制 ---
with st.sidebar:
    st.title("⚙️ 劇本同步終端")
    api_key = st.text_input("輸入 Groq API Key", type="password")
    
    if st.button("🚀 啟動/重置 (絕對還原模式)"):
        st.session_state.messages = [] 
        st.session_state.started = True 
        st.session_state.script_step = 0 # 劇本進度追蹤
        st.rerun()
    
    st.markdown("---")
    if st.session_state.get("started", False):
        if st.button("⏭️ 繼續劇情 (依照劇本進度)"):
            st.session_state.auto_next = True
        else:
            st.session_state.auto_next = False

# --- 核心：系統提示詞 (強制鎖定劇本庫) ---
system_prompt = f"""
你現在是「崩壞：星穹鐵道」劇本執行器。
【核心法則】：
1. **絕對一致性**：每次重置劇情，你必須從劇本庫的起始點開始，不得有任何偏差。
2. **文本優先**：在玩家尚未主動說話前，你輸出的所有對白必須 100% 符合劇本庫內容。
3. **雙生設定**：必須將「輝夜」與「主角」視為雙胞胎，所有針對載體的動作必須同時發生在兩人身上。

【輝夜設定】：{PLAYER_INFO}
【劇本庫】：{EXACT_SCRIPT_BASE}

【輸出要求】：
(深度運算): [分析當前劇本階段與演出細節]
**[角色名]**: "對話"
*動作描寫 (需特別強調輝夜的紅瞳、白毛衣與雙胞胎同步感)*
"""

# --- 初始化 ---
if "messages" not in st.session_state: st.session_state.messages = []
if "started" not in st.session_state: st.session_state.started = False
if "script_step" not in st.session_state: st.session_state.script_step = 0

st.title("🚂 星穹演繹：雙星軌跡")

# 顯示對話歷史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# --- AI 生成邏輯 ---
def run_script_segment(instruction):
    if not api_key:
        st.error("請輸入 API Key")
        return

    client = Groq(api_key=api_key)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        msgs = [{"role": "system", "content": system_prompt}] + \
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

# --- 流程自動控制 ---
if st.session_state.started and len(st.session_state.messages) == 0:
    # 階段 0：開場拉琴
    run_script_segment(f"【執行劇本起始階段】：請根據劇本庫中的 prologue_start，演出卡芙卡拉琴、銀狼出現的經典開場。請強調輝夜(白毛衣紅裙)靜靜站在卡芙卡後方的畫面。")
    st.session_state.script_step = 1

elif st.session_state.get("auto_next", False):
    if st.session_state.script_step == 1:
        # 階段 1：植入星核
        run_script_segment(f"【執行劇本後續階段】：請根據劇本庫中的 stellaron_insertion，演出卡芙卡將星核同時植入主角與輝夜體內的過程。請完整複刻『聽我說』台詞。")
        st.session_state.script_step = 2
    else:
        # 階段 2 之後：開始自由銜接後續 Wiki 劇本
        run_script_segment("【接續劇情】：請根據 Wiki 劇本演出下一段：三月七與丹恆發現兩名昏迷者的場景。")
    
    st.session_state.auto_next = False
    st.rerun()

# --- 玩家輸入 (主動干預) ---
if len(st.session_state.messages) > 0:
    if prompt := st.chat_input("輸入輝夜的行動，或點擊左側『繼續劇情』..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        run_script_segment(f"玩家行動：{prompt}。請在遵守劇本原則下繼續演繹。")
