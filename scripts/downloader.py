import os
import requests
import re
from concurrent.futures import ThreadPoolExecutor

# تأكد أن ملف FINAL_GAMES_WITH_URLS.txt موجود في نفس الفولدر
INPUT_FILE = "FINAL_GAMES_WITH_URLS.txt"
IMAGE_FOLDER = "FULL_GAME_IMAGES"

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

def download_game_images(game_name):
    game_name = game_name.strip()
    if not game_name: return

    safe_name = re.sub(r'[\\/*?:"<>|]', '_', game_name)
    folder_path = os.path.join(IMAGE_FOLDER, safe_name)

    if os.path.exists(folder_path): return

    app_id = get_steam_app_id(game_name)
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
            print(f"✅ DONE: {game_name}")
        else: print(f"❌ NO IMAGES: {game_name}")
    else: print(f"⚠️ NOT FOUND ON STEAM: {game_name}")

def run():
    if not os.path.exists(IMAGE_FOLDER): os.makedirs(IMAGE_FOLDER)
    
    # قراءة الألعاب من الملف مباشرة
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        games = [line.split(" = ")[0].strip() for line in f if " = " in line]

    print(f"🚀 Starting download for {len(games)} games...")
    
    # تشغيل 20 لعبة في نفس الوقت للسرعة القصوى
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(download_game_images, games)

if __name__ == "__main__":
    run()
