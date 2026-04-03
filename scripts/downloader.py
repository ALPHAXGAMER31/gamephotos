import os
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor

# الإعدادات
INPUT_FILE = "FINAL_GAMES_WITH_URLS.txt"
IMAGE_FOLDER = "FULL_ALBUM_STEAM"

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def clean_game_name(name):
    # تنظيف الاسم من الإضافات اللي بتبوظ البحث في ستيم
    name = re.sub(r'\(.*?\)', '', name) # مسح أي حاجة بين أقواس
    name = re.sub(r'\[.*?\]', '', name) # مسح أي حاجة بين brackets
    return name.strip()

def get_app_id_from_steam(game_name):
    cleaned_name = clean_game_name(game_name)
    search_url = f"https://store.steampowered.com/api/storesearch/?term={cleaned_name}&l=english&cc=US"
    try:
        response = session.get(search_url, timeout=10)
        data = response.json()
        if data.get("total") > 0:
            # هنختار النتيجة اللي اسمها أقرب ما يكون للاسم اللي معانا
            return data["items"][0]["id"]
    except Exception as e:
        print(f"Error searching for {game_name}: {e}")
    return None

def download_images_by_id(game_name, app_id):
    safe_name = re.sub(r'[\\/*?:"<>|]', '_', game_name).strip().replace(' ', '_')
    folder_path = os.path.join(IMAGE_FOLDER, safe_name)
    
    if os.path.exists(folder_path) and len(os.listdir(folder_path)) >= 3:
        return # اللعبة موجودة فعلاً

    details_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        res = session.get(details_url, timeout=10)
        data = res.json()
        if data[str(app_id)]["success"]:
            screenshots = data[str(app_id)]["data"].get("screenshots", [])
            if screenshots:
                os.makedirs(folder_path, exist_ok=True)
                for i, ss in enumerate(screenshots[:4]):
                    img_res = session.get(ss["path_full"], timeout=15)
                    with open(os.path.join(folder_path, f"ss_{i+1}.jpg"), "wb") as f:
                        f.write(img_res.content)
                print(f"✅ DONE: {game_name} (ID: {app_id})")
                return True
    except: pass
    return False

def process_line(line):
    if " = " not in line: return
    game_name = line.split(" = ")[0].strip()
    
    app_id = get_app_id_from_steam(game_name)
    if app_id:
        success = download_images_by_id(game_name, app_id)
        if not success:
            print(f"❌ NO IMAGES: {game_name}")
    else:
        print(f"⚠️ NOT FOUND ON STEAM: {game_name}")
    
    # تأخير بسيط جداً عشان نتفادى الـ Block
    time.sleep(0.5)

def main():
    if not os.path.exists(IMAGE_FOLDER): os.makedirs(IMAGE_FOLDER)
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"📡 جاري فحص {len(lines)} لعبة والبحث عن AppIDs...")
    
    # يفضل تقليل الـ workers لـ 3 عشان متتحظرش وأنت بتجيب الـ IDs
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(process_line, lines)

if __name__ == "__main__":
    main()
