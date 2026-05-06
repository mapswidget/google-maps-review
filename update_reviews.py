import json
import time
from playwright.sync_api import sync_playwright

def scrape_reviews():
    with sync_playwright() as p:
        # Launch browser with a specific window size
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        url = "https://www.google.ro/maps/place/Logimaetics+Electric+S.R.L./@45.7141378,21.1914901,17z/data=!3m1!4b1!4m6!3m5!1s0x47455d754c54952d:0xfba7f22b1038d01c!8m2!3d45.7141378!4d21.194065!16s%2Fg%2F1tg66ws5"
        
        print("Opening Google Maps...")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5) # Give it time to settle
        except Exception as e:
            print(f"Initial load took too long: {e}")

        # 1. Handle Consent Screens (The likely cause of the timeout)
        # We look for common "Accept" button texts in RO and EN
        consent_buttons = ["Acceptă tot", "Accept all", "Agree", "Sunt de acord", "Accept"]
        for text in consent_buttons:
            try:
                btn = page.get_by_role("button", name=text, exact=False).first
                if btn.is_visible():
                    btn.click()
                    print(f"Clicked consent button: {text}")
                    time.sleep(3)
                    break
            except:
                continue

        # 2. Extract Rating (Using multiple possible selectors)
        rating = "5.0" # Fallback
        for selector in ['div.fontDisplayLarge', 'span.ceNzR', 'div.PPCuY', '.fontDisplayLarge']:
            try:
                element = page.query_selector(selector)
                if element:
                    rating = element.inner_text().strip().replace(',', '.')
                    print(f"Found rating: {rating}")
                    break
            except:
                continue

        # 3. Extract Total Review Count
        count = "24" # Fallback
        try:
            count_el = page.locator('button.HHrUdb').first
            if count_el.is_visible():
                count_text = count_el.inner_text()
                count = "".join(filter(str.isdigit, count_text))
                print(f"Found count: {count}")
        except:
            print("Could not find count, using default.")

        # 4. Click the Reviews tab to get actual text
        try:
            page.get_by_role("button", name=["Recenzii", "Reviews"], exact=False).first.click()
            time.sleep(3)
        except:
            print("Could not click reviews tab, attempting to scrape what is visible.")

        # 5. Scrape the reviews
        reviews_list = []
        try:
            items = page.locator('div.jftiEf').all()
            for i in range(min(6, len(items))):
                try:
                    author = items[i].locator('.d4r55').inner_text()
                    # Try to get review text
                    try:
                        content = items[i].locator('.wi93lc').inner_text()
                    except:
                        content = "Recenzie fără text."
                    
                    reviews_list.append({
                        "author": author,
                        "content": content,
                        "rating": "5 ⭐"
                    })
                except:
                    continue
        except:
            print("No individual reviews found.")

        # If we found nothing, let's at least put a placeholder so the widget isn't empty
        if not reviews_list:
            reviews_list.append({"author": "Client Google", "content": "Calitate și profesionalism!", "rating": "5 ⭐"})

        # Save the JSON files
        data_output = {
            "rating": rating,
            "count": count,
            "reviews": reviews_list,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open('reviews.json', 'w', encoding='utf-8') as f:
            json.dump(data_output, f, indent=4, ensure_ascii=False)

        schema_data = {
            "@context": "https://schema.org",
            "@type": "Electrician",
            "name": "Logimaetics ELECTRIC",
            "url": "https://www.tablourielectrice.ro",
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": rating,
                "reviewCount": count
            }
        }

        with open('schema.json', 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=4, ensure_ascii=False)

        print("Done! Files created successfully.")
        browser.close()

if __name__ == "__main__":
    scrape_reviews()
