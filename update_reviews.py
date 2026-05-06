import json
import time
from playwright.sync_api import sync_playwright

def scrape_reviews():
    with sync_playwright() as p:
        # Launch browser - Chromium is best for this
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Your specific Google Maps URL
        url = "https://www.google.ro/maps/place/Logimaetics+Electric+S.R.L./@45.7141378,21.1914901,17z/data=!3m1!4b1!4m6!3m5!1s0x47455d754c54952d:0xfba7f22b1038d01c!8m2!3d45.7141378!4d21.194065!16s%2Fg%2F1tg66ws5"
        
        print("Navigating to Google Maps...")
        page.goto(url)
        
        # Handle Cookie Consent (Common in Romania/EU)
        try:
            # Look for "Accept all" or "Accept tot" button
            accept_button = page.get_by_role("button", name="Accept all")
            if not accept_button.is_visible():
                accept_button = page.get_by_role("button", name="Acceptă tot")
            
            if accept_button.is_visible():
                accept_button.click()
                print("Cookies accepted.")
                time.sleep(2)
        except:
            print("No cookie consent box found, proceeding...")

        # Wait for the rating element to load
        page.wait_for_selector('div.fontDisplayLarge', timeout=10000)

        # Extract Aggregate Data
        rating = page.locator('div.fontDisplayLarge').inner_text()
        # Find the review count string (e.g., "24 reviews" or "24 recenzii")
        total_reviews_raw = page.locator('button.HHrUdb.fontTitleSmall.fontBodyMedium').inner_text()
        total_reviews = "".join(filter(str.isdigit, total_reviews_raw))

        print(f"Rating found: {rating} with {total_reviews} reviews.")

        # Click the "Reviews" tab to load specific review text
        page.get_by_role("button", name="Recenzii").click()
        time.sleep(3)

        # Scrape the top 6 reviews
        review_elements = page.locator('div.jftiEf').all()
        
        reviews_list = []
        for i in range(min(6, len(review_elements))):
            try:
                author = review_elements[i].locator('.d4r55').inner_text()
                # Expand "More" if the review is long
                more_btn = review_elements[i].locator('button.w8Bnu')
                if more_btn.is_visible():
                    more_btn.click()
                
                content = review_elements[i].locator('.wi93lc').inner_text()
                stars_label = review_elements[i].locator('.kvMYC').get_attribute('aria-label')
                
                reviews_list.append({
                    "author": author,
                    "content": content,
                    "rating": stars_label
                })
            except Exception as e:
                print(f"Could not parse review {i}: {e}")

        # 1. Save reviews.json for the Gomag Widget
        data_output = {
            "rating": rating, 
            "count": total_reviews, 
            "reviews": reviews_list,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open('reviews.json', 'w', encoding='utf-8') as f:
            json.dump(data_output, f, indent=4, ensure_ascii=False)

        # 2. Save schema.json for SEO (JSON-LD)
        # We format the rating for Google (using dot instead of comma)
        google_rating = rating.replace(',', '.')
        
        schema_data = {
            "@context": "https://schema.org",
            "@type": "Electrician",
            "name": "Logimaetics ELECTRIC",
            "url": "https://www.tablourielectrice.ro",
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": google_rating,
                "bestRating": "5",
                "worstRating": "1",
                "reviewCount": total_reviews
            }
        }
        
        with open('schema.json', 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=4, ensure_ascii=False)

        print("Files successfully generated.")
        browser.close()

if __name__ == "__main__":
    scrape_reviews()
