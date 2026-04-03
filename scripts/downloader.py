import os
import requests
import re
from concurrent.futures import ThreadPoolExecutor

# القائمة التي وضعتها أنت في الرسالة
GAMES_LIST = """
Among Us VR
BLADENET
... (ضع باقي الألعاب هنا) ...
"""

IMAGE_FOLDER = "STEAM_GAMES_COLLECTION"
MISSING_FILE = "failed_to_find.txt"

def get_steam_app_id(game_name):
    url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    try:
        r = requests.get(url, timeout=5).json()
        if r.get("total") > 0:
            return r["items"][0]["id"]
    except: pass
    return None

def get_images(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        r = requests.get(url, timeout=5).json()
        if str(app_id) in r and r[str(app_id)]["success"]:
            imgs = r[str(app_id)]["data"].get("screenshots", [])
            return [i["path_full"] for i in imgs[:4]]
    except: pass
    return []

def download_task(game):
    game = game.strip()
    if not game: return
    
    safe_name = re.sub(r'[\\/*?:"<>|]', '_', game)
    path = os.path.join(IMAGE_FOLDER, safe_name)
    
    if os.path.exists(path): return # متواجد مسبقاً
    
    app_id = get_steam_app_id(game)
    if app_id:
        urls = get_images(app_id)
        if urls:
            os.makedirs(path, exist_ok=True)
            for i, u in enumerate(urls):
                try:
                    data = requests.get(u, timeout=10).content
                    with open(os.path.join(path, f"image_{i+1}.jpg"), "wb") as f:
                        f.write(data)
                except: continue
            print(f"DONE: {game}")
            return
    
    with open(MISSING_FILE, "a") as f:
        f.write(game + "\n")
    print(f"FAIL: {game}")

def run():
    if not os.path.exists(IMAGE_FOLDER): os.makedirs(IMAGE_FOLDER)
    games = [g for g in GAMES_LIST.split('\n') if g.strip()]
    
    # 20 خيط معالجة لجعل التحميل طيارة
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(download_task, games)

if __name__ == "__main__":
    run()
