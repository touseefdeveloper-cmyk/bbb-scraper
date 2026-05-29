import requests
import json
import time
import os

API_KEY = os.environ.get("WEBSCRAPING_AI_KEY", "")
API_URL = "https://api.webscraping.ai/ai/fields"

BUSINESSES = [
    {"id": "cabinet-refresh",          "bbb_url": "https://www.bbb.org/us/ca/los-angeles/profile/sales/cabinet-refresh-1216-1000057905/customer-reviews"},
    {"id": "american-vision-windows",  "bbb_url": "https://www.bbb.org/us/ca/simi-valley/profile/windows/american-vision-windows-1236-3000957/customer-reviews"},
    {"id": "one-week-bath",            "bbb_url": "https://www.bbb.org/us/ca/van-nuys/profile/bathroom-remodel/one-week-bath-inc-1216-13044203/customer-reviews"},
    {"id": "abc-pro",                  "bbb_url": "https://www.bbb.org/us/ca/van-nuys/profile/general-contractor/abraham-building-consulting-1216-885407/customer-reviews"},
    {"id": "1-degree-construction",    "bbb_url": "https://www.bbb.org/us/ca/anaheim/profile/general-contractor/the-original-mr-cabinet-care-1126-50066/customer-reviews"},
    {"id": "mr-cabinet-care",          "bbb_url": None},
    {"id": "payless-kitchen-cabinets", "bbb_url": "https://www.bbb.org/ca/on/etobicoke/profile/kitchen-remodel/payless-kitchen-cabinets-ltd-0107-1234459/customer-reviews"},
    {"id": "payless-bath-makeover",    "bbb_url": "https://www.bbb.org/ca/on/etobicoke/profile/kitchen-remodel/payless-kitchen-cabinets-ltd-0107-1234459/customer-reviews"},
    {"id": "adar-builders",            "bbb_url": "https://www.bbb.org/us/ca/winnetka/profile/roofing-contractors/adar-builders-inc-1216-1000035931/customer-reviews"},
    {"id": "gm-home-remodeling",       "bbb_url": "https://www.bbb.org/us/ca/sherman-oaks/profile/home-renovation/gm-home-remodeling-inc-1216-1000013059/customer-reviews"},
]

MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds between retries


def scrape_bbb(business: dict) -> dict:
    if not business["bbb_url"]:
        print(f"  [{business['id']}] Skipped — no URL provided.")
        return {"id": business["id"], "bbb_url": None, "total_reviews": None, "average_rating": None, "error": "No URL provided"}

    print(f"  [{business['id']}] Scraping ...")

    params = {
        "api_key": API_KEY,
        "url": business["bbb_url"],
        "fields[total_reviews]": "Total number of customer reviews on this page (just the number)",
        "fields[average_rating]": "Average customer star rating (e.g. 4.5 out of 5)",
        "js": "true",
        "proxy": "residential",   # Residential proxies bypass BBB bot protection
        "timeout": 30000,         # 30 second page load timeout (milliseconds)
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"    Attempt {attempt}/{MAX_RETRIES} ...")
            response = requests.get(API_URL, params=params, timeout=90)
            response.raise_for_status()
            data = response.json()

            result = {
                "id": business["id"],
                "bbb_url": business["bbb_url"],
                "total_reviews": data.get("total_reviews"),
                "average_rating": data.get("average_rating"),
                "error": None,
            }
            print(f"    ✓ Reviews: {result['total_reviews']} | Rating: {result['average_rating']}")
            return result

        except requests.exceptions.RequestException as e:
            print(f"    ✗ Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"    Retrying in {RETRY_DELAY}s ...")
                time.sleep(RETRY_DELAY)
            else:
                return {"id": business["id"], "bbb_url": business["bbb_url"], "total_reviews": None, "average_rating": None, "error": str(e)}

        except Exception as e:
            print(f"    ✗ Unexpected error: {e}")
            return {"id": business["id"], "bbb_url": business["bbb_url"], "total_reviews": None, "average_rating": None, "error": str(e)}


def main():
    print("=== BBB Review Scraper ===\n")
    results = []

    for business in BUSINESSES:
        result = scrape_bbb(business)
        results.append(result)
        time.sleep(3)  # polite delay between requests

    output_file = "bbb_reviews.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n=== Done! Results saved to {output_file} ===")
    print(f"Total processed: {len(results)} | Skipped: {sum(1 for r in results if r['bbb_url'] is None)}")


if __name__ == "__main__":
    main()
