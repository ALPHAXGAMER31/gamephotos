import os
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor

# الإعدادات
INPUT_FILE = "FINAL_GAMES_WITH_URLS.txt"
IMAGE_FOLDER = "ALL_GAME_IMAGES"
MISSING_FILE = "missing_images.txt"

def get_steam_app_id(game_name):
    search_url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    try:
        response = requests.get(search_url, timeout=5)
        data = response.json()
        if data.get("total") > 0:
            return data["items"][0]["id"]
    except: pass
    return None

def get_steam_images(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if str(app_id) in data and data[str(app_id)]["success"]:
            game_data = data[str(app_id)]["data"]
            screenshots = game_data.get("screenshots", [])
            return [s["path_full"] for s in screenshots[:4]]
    except: pass
    return []

def process_game(game):
    safe_name = re.sub(r'[\\/*?:"<>|]', '_', game).replace(' ', '_')
    folder_path = os.path.join(IMAGE_FOLDER, safe_name)
    
    if os.path.exists(folder_path): return

    app_id = get_steam_app_id(game)
    if app_id:
        img_urls = get_steam_images(app_id)
        if img_urls:
            os.makedirs(folder_path, exist_ok=True)
            for i, url in enumerate(img_urls):
                try:
                    img_data = requests.get(url, timeout=10).content
                    with open(os.path.join(folder_path, f"ss_{i+1}.jpg"), "wb") as f:
                        f.write(img_data)
                except: continue
            print(f"✅ {game}")
        else: return game
    else: return game

def run_fast():
    if not os.path.exists(IMAGE_FOLDER): os.makedirs(IMAGE_FOLDER)
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        games = [line.split(" = ")[0].strip() for line in f if " = " in line]

    print(f"🚀 البدء في تحميل صور {len(games)} لعبة...")
    
    # استخدام الـ Multi-threading عشان يخلص في دقائق بدل ساعات
    # 10 خيوط معالجة (Threads) بيشتغلوا مع بعض في نفس الوقت
    with ThreadPoolExecutor(max_workers=10) as executor:
        missing = list(executor.map(process_game, games))

    # تسجيل الألعاب اللي فشلت
    missing_games = [m for m in missing if m]
    if missing_games:
        with open(MISSING_FILE, "w", encoding="utf-8") as f:
            for g in missing_games: f.write(g + "\n")
    
    print(f"\n✨ انتهى العمل! الصور موجودة في فولدر: {IMAGE_FOLDER}")

if __name__ == "__main__":
    run_fast()
