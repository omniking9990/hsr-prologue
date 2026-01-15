import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import quote, urljoin

# ==========================================
# 1. 修正後的精確任務清單 (對應 Wiki 子網頁標題)
# ==========================================
MISSION_LIST = [
    # --- 序章：收容艙段 ---
    "昨夜的第82次敲门", "混乱的一角", "在那琥珀色的光芒中", 
    
    # --- 第一章：雅利洛-VI ---
    "今天是昨天的明天", "劫后新生", "于枯索的冬夜里", "于曈昽的骄阳下", "炉前百态", "苏醒年代",
    
    # --- 第二章：仙舟「羅浮」 ---
    "乘槎驭风仙窟游", "云树百丈蔽重楼", "劫波渡尽战云收",
    
    # --- 第三章：匹諾康尼 ---
    "喧哗与骚动", "鸽群中的猫", "在我们的时代里", "再见，匹诺康尼"
]

BILI_BASE = "https://wiki.biligame.com/sr/"
OUTPUT_FILE = "SR_Exact_Script.txt"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_dialogue_text(soup):
    """
    專門抓取 Wiki 頁面中的劇情對話區塊
    """
    script_content = []
    # BiliWiki 的對話通常在 class 為 'mw-parser-output' 的 div 下的特定結構中
    content = soup.find('div', class_='mw-parser-output')
    if not content:
        return ""

    # 尋找對話表格或帶有角色頭像的區塊
    # 通常對話會出現在 table 或特定段落
    for element in content.find_all(['p', 'table', 'div']):
        # 排除導航欄和目錄
        if element.get('class') and any(c in element.get('class') for c in ['navbox', 'toc', 'infobox']):
            continue
        
        text = element.get_text(strip=True)
        if text and len(text) > 2:
            # 簡單過濾掉一些系統提示
            if "編輯" in text or "跳轉" in text: continue
            script_content.append(text)
    
    return "\n".join(script_content)

def main():
    print(f"=== 啟動 Wiki 劇情深度擷取 (對標開拓任務子網頁) ===")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        # 寫入玩家人設作為 AI 參考基準
        f.write("====== 【玩家人設：輝夜】 ======\n")
        f.write("形象：170cm/50kg/36B、白長髮漸變紅、紅瞳、白毛衣、黑包臀裙、黑高跟鞋、蝙蝠刺青。\n")
        f.write("能力：血液控制、變形、雙生星核載體。\n\n")

        for mission in MISSION_LIST:
            url = f"{BILI_BASE}{quote(mission)}"
            print(f"正在抓取任務: {mission} ...")
            
            try:
                resp = requests.get(url, headers=HEADERS, timeout=10)
                resp.encoding = 'utf-8'
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    script = get_dialogue_text(soup)
                    
                    f.write(f"\n\n====== [開拓任務] {mission} ======\n")
                    f.write(f"【來源網址】: {url}\n")
                    f.write(script)
                    print(f"   [成功] 已儲存 {len(script)} 字劇情。")
                else:
                    print(f"   [失敗] 網頁無法訪問: {resp.status_code}")
            except Exception as e:
                print(f"   [錯誤] {e}")
            
            time.sleep(1) # 避免對 Wiki 造成負擔

    print(f"\n全部完成！已生成檔案: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
