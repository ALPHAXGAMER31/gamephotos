import os
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor

# الإعدادات
INPUT_FILE = "FINAL_GAMES_WITH_URLS.txt"
IMAGE_FOLDER = "FULL_ALBUM_STEAM"
MISSING_FILE = "failed_games.txt"

# إنشاء جلسة عمل واحدة لتسريع الاتصال
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def get_steam_app_id(game_name):
    # محاولة البحث في ستيم بذكاء
    search_url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    try:
        response = session.get(search_url, timeout=7)
        data = response.json()
        if data.get("total") > 0:
            # بنأخد أول نتيجة مطابقة
            return data["items"][0]["id"]
    except: pass
    return None

def get_images(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        response = session.get(url, timeout=7)
        data = response.json()
        if str(app_id) in data and data[str(app_id)]["success"]:
            game_data = data[str(app_id)]["data"]
            screenshots = game_data.get("screenshots", [])
            # هنسحب أول 4 صور بجودة Full
            return [s["path_full"] for s in screenshots[:4]]
    except: pass
    return []

def download_game(game_line):
    game_name = game_line.split(" = ")[0].strip()
    safe_name = re.sub(r'[\\/*?:"<>|]', '_', game_name).replace(' ', '_')
    folder_path = os.path.join(IMAGE_FOLDER, safe_name)

    # لو الفولدر موجود وفيه صور فعلاً، كبر دماغك وانقل على اللي بعده
    if os.path.exists(folder_path) and len(os.listdir(folder_path)) >= 1:
        return

    app_id = get_steam_app_id(game_name)
    if not app_id:
        print(f"⚠️ Not Found: {game_name}")
        with open(MISSING_FILE, "a") as f: f.write(game_name + "\n")
        return

    img_urls = get_images(app_id)
    if img_urls:
        os.makedirs(folder_path, exist_ok=True)
        for i, url in enumerate(img_urls):
            try:
                img_data = session.get(url, timeout=10).content
                with open(os.path.join(folder_path, f"ss_{i+1}.jpg"), "wb") as f:
                    f.write(img_data)
            except: continue
        print(f"✅ Saved: {game_name}")
    else:
        print(f"❌ No Images: {game_name}")

def start_engine():
    if not os.path.exists(IMAGE_FOLDER): os.makedirs(IMAGE_FOLDER)
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = [line for line in f if " = " in line]

    print(f"🚀 البدء في جلب صور {len(lines)} لعبة...")
    
    # هنستخدم 5 Threads بس عشان ستيم ميزعلش ويقفل الأي بي بتاعك
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(download_game, lines)

    print("\n🏁 المهمة تمت بنجاح! الصور كلها في فولدر FULL_ALBUM_STEAM")

if __name__ == "__main__":
    start_engine()
