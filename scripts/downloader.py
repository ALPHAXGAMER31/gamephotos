import os
import requests
import re
import time

# الإعدادات
INPUT_FILE = "FINAL_GAMES_WITH_URLS.txt"
IMAGE_FOLDER = "game_images"
MISSING_FILE = "missing_images.txt"

def get_steam_app_id(game_name):
    search_url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    try:
        response = requests.get(search_url, timeout=10)
        data = response.json()
        if data.get("total") > 0:
            return data["items"][0]["id"]
    except:
        pass
    return None

def get_steam_images(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if str(app_id) in data and data[str(app_id)]["success"]:
            game_data = data[str(app_id)]["data"]
            screenshots = game_data.get("screenshots", [])
            return [s["path_full"] for s in screenshots[:4]]
    except:
        pass
    return []

def run_task():
    if not os.path.exists(IMAGE_FOLDER): os.makedirs(IMAGE_FOLDER)
    
    games_to_process = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if " = " in line:
                name = line.split(" = ")[0].strip()
                games_to_process.append(name)

    missing_games = []

    # معالجة عدد معين في كل مرة (مثلاً 100 لعبة لتجنب تجاوز وقت الأكشن)
    for game in games_to_process:
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', game).replace(' ', '_')
        folder_path = os.path.join(IMAGE_FOLDER, safe_name)
        
        # لو الفولدر موجود وفيه صور، نتخطى اللعبة
        if os.path.exists(folder_path) and len(os.listdir(folder_path)) >= 1:
            continue

        print(f"🔍 Searching for: {game}")
        app_id = get_steam_app_id(game)
        
        if app_id:
            img_urls = get_steam_images(app_id)
            if img_urls:
                os.makedirs(folder_path, exist_ok=True)
                for i, url in enumerate(img_urls):
                    try:
                        img_data = requests.get(url, timeout=15).content
                        with open(os.path.join(folder_path, f"ss_{i+1}.jpg"), "wb") as img_file:
                            img_file.write(img_data)
                    except: continue
                print(f"✅ Saved images for {game}")
            else:
                missing_games.append(game)
        else:
            missing_games.append(game)
        
        time.sleep(1.5) # احتراماً لسيرفرات ستيم

    if missing_games:
        with open(MISSING_FILE, "a", encoding="utf-8") as f:
            for g in missing_games: f.write(g + "\n")

if __name__ == "__main__":
    run_task()
