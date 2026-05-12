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
        
        url = "https://www.google.ro/maps/place/Logimaetics+Electric+S.R.L./@45.7141378,21.1914901,17z/data=!3m1!4b1!4m6!3m5!1s0x47455d754c54952d:0xfba7f22b1038d01c!8m2!3d45.7141378!4d21.194065!16s%2Fg%2F1tg66ws5"
        
        print("Deschidem Google Maps...")
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(5)

        # 1. Acceptare Cookie-uri
        for text in ["Acceptă tot", "Accept all", "Agree"]:
            try:
                btn = page.get_by_role("button", name=text, exact=False).first
                if btn.is_visible():
                    btn.click()
                    time.sleep(2)
                    break
            except: continue

        # 2. Click pe tab-ul Recenzii
        try:
            page.get_by_role("button", name=["Recenzii", "Reviews"], exact=False).first.click()
            time.sleep(3)
        except: print("Nu am putut apasa pe tab-ul de recenzii.")

        # 3. SCROLL pentru a incarca mai multe recenzii (important pentru a ajunge la 10)
        print("Facem scroll pentru a incarca recenzii...")
        for _ in range(3): # Facem scroll de 3 ori
            # Gasim containerul de recenzii si scrollam in el
            page.mouse.wheel(0, 1000)
            time.sleep(2)

        # 4. Extragere Date
        rating = "5.0"
        try:
            rating = page.query_selector('div.fontDisplayLarge').inner_text().strip().replace(',', '.')
        except: pass

        reviews_list = []
        items = page.locator('div.jftiEf').all()
        
        print(f"Am gasit {len(items)} recenzii pe pagina.")

        for i in range(min(10, len(items))): # Extragem pana la 10
            try:
                author = items[i].locator('.d4r55').inner_text()
                try:
                    # Incarca textul complet daca exista butonul "Mai mult"
                    more_btn = items[i].locator('button.w8Bnu')
                    if more_btn.is_visible():
                        more_btn.click()
                        time.sleep(0.5)
                    content = items[i].locator('.wi93lc').inner_text()
                except:
                    content = "Clientul a lăsat doar rating, fără text."
                
                reviews_list.append({
                    "author": author,
                    "content": content,
                    "rating": "5 ⭐"
                })
            except: continue

        # Salvare Date
        data_output = {
            "rating": rating,
            "count": str(len(items)),
            "reviews": reviews_list,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open('reviews.json', 'w', encoding='utf-8') as f:
            json.dump(data_output, f, indent=4, ensure_ascii=False)

        schema_data = {
            "@context": "https://schema.org",
            "@type": "Electrician",
            "name": "Logimaetics ELECTRIC",
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": rating,
                "reviewCount": str(len(items))
            }
        }

        with open('schema.json', 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=4, ensure_ascii=False)

        print(f"Succes! Am salvat {len(reviews_list)} recenzii.")
        browser.close()

if __name__ == "__main__":
    scrape_reviews()
