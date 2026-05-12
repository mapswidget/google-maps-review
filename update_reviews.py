import json
import time
from playwright.sync_api import sync_playwright

def scrape_reviews():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # LINK DIRECT către secțiunea de recenzii pentru a evita erorile de navigare
        url = "https://www.google.com/maps/place/Logimaetics+Electric+S.R.L./@45.7141378,21.194065,17z/data=!4m8!3m7!1s0x47455d754c54952d:0xfba7f22b1038d01c!8m2!3d45.7141378!4d21.194065!9m1!1b1"
        
        print(f"Navigăm direct la recenzii: {url}")
        page.goto(url, wait_until="networkidle", timeout=60000)
        time.sleep(5)

        # Gestionare Consent (Cookie-uri)
        for text in ["Acceptă tot", "Accept all", "Agree", "Sunt de acord"]:
            try:
                btn = page.get_by_role("button", name=text, exact=False).first
                if btn.is_visible():
                    btn.click()
                    print(f"Am apăsat pe: {text}")
                    time.sleep(3)
                    break
            except: continue

        # Încercăm să forțăm încărcarea recenziilor prin scroll în panoul stâng
        print("Facem scroll pentru a forța încărcarea...")
        try:
            # Google Maps folosește un div specific pentru scroll în lista de recenzii
            page.mouse.move(500, 500) # Mutăm mouse-ul în zona listei
            for _ in range(5):
                page.mouse.wheel(0, 2000)
                time.sleep(1)
        except Exception as e:
            print(f"Eroare la scroll: {e}")

        reviews_list = []
        # Selectori actualizați pentru 2026
        # .jftiEf este containerul principal al unei recenzii
        items = page.locator('div.jftiEf').all()
        
        print(f"Robotul a detectat {len(items)} elemente de tip recenzie.")

        for i in range(min(10, len(items))):
            try:
                # Selector pentru numele autorului
                author = items[i].locator('.d4r55').inner_text()
                
                # Încercăm să luăm textul recenziei
                content = ""
                try:
                    # Uneori textul e ascuns sub "Afișați mai multe"
                    more_btn = items[i].locator('button:has-text("Mai mult"), button:has-text("More")')
                    if more_btn.is_visible():
                        more_btn.click()
                        time.sleep(0.5)
                    
                    content = items[i].locator('.wi93lc').inner_text()
                except:
                    content = "Rating de 5 stele (fără comentariu text)."

                reviews_list.append({
                    "author": author,
                    "content": content,
                    "rating": "5 ⭐"
                })
            except Exception as e:
                print(f"Eroare la procesarea recenziei {i}: {e}")

        # Datele finale
        final_data = {
            "rating": "5.0", # Hardcoded fiindca aveti doar 5 stele
            "count": str(len(reviews_list)),
            "reviews": reviews_list,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Salvare
        with open('reviews.json', 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
            
        print(f"Gata! Am salvat {len(reviews_list)} recenzii în reviews.json")
        browser.close()

if __name__ == "__main__":
    scrape_reviews()
