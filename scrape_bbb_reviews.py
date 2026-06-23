import requests
import json
import time
import os
import re

API_KEY = os.environ.get("WEBSCRAPING_AI_KEY", "")
TEXT_URL = "https://api.webscraping.ai/text"

BUSINESSES = [
    {"id": "cabinet-refresh",          "bbb_url": "https://www.bbb.org/us/ca/los-angeles/profile/sales/cabinet-refresh-1216-1000057905/customer-reviews"},
    {"id": "american-vision-windows",  "bbb_url": "https://www.bbb.org/us/ca/simi-valley/profile/windows/american-vision-windows-1236-3000957/customer-reviews"},
    {"id": "one-week-bath",            "bbb_url": "https://www.bbb.org/us/ca/van-nuys/profile/bathroom-remodel/one-week-bath-inc-1216-13044203/customer-reviews"},
    {"id": "abc-pro",                  "bbb_url": "https://www.bbb.org/us/ca/van-nuys/profile/general-contractor/abraham-building-consulting-1216-885407/customer-reviews"},
    {"id": "1-degree-construction",    "bbb_url": "https://www.bbb.org/us/ca/los-angeles/profile/construction/1-degree-construction-inc-1216-1000023536/customer-reviews"},
    {"id": "mr-cabinet-care",          "bbb_url": "https://www.bbb.org/us/ca/anaheim/profile/general-contractor/the-original-mr-cabinet-care-1126-50066/customer-reviews"},
    {"id": "payless-kitchen-cabinets", "bbb_url": "https://www.bbb.org/us/ca/glendale/profile/floor-coverings/carpet-wagon-glendale-inc-1216-22000132/customer-reviews"},
    {"id": "payless-bath-makeover",    "bbb_url": "https://www.bbb.org/us/ca/glendale/profile/floor-coverings/carpet-wagon-glendale-inc-1216-22000132/customer-reviews"},
    {"id": "adar-builders",            "bbb_url": "https://www.bbb.org/us/ca/winnetka/profile/roofing-contractors/adar-builders-inc-1216-1000035931/customer-reviews"},
    {"id": "gm-home-remodeling",       "bbb_url": "https://www.bbb.org/us/ca/sherman-oaks/profile/home-renovation/gm-home-remodeling-inc-1216-1000013059/customer-reviews"},
]

RETRY_DELAY = 30


def parse_reviews_from_text(text: str) -> dict:
    total_reviews = None
    average_rating = None

    for pattern in [
        r"Average of ([\d,]+) Customer Review",
        r"This business has (\d+) review",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            total_reviews = m.group(1).replace(",", "")
            break

    m = re.search(r"([\d.]+)/5\s+stars?", text, re.IGNORECASE)
    if m:
        average_rating = m.group(1)

    return {"total_reviews": total_reviews, "average_rating": average_rating}


def fetch_text(url: str, proxy: str) -> str:
    """Fetch page text with given proxy type. Raises on failure."""
    params = {
        "api_key": API_KEY,
        "url": url,
        "js": "true",
        "proxy": proxy,
        "timeout": 30000,
        "country": "us",
        "wait_for": "h2",   # wait until page content headings are rendered
    }
    response = requests.get(TEXT_URL, params=params, timeout=90)
    response.raise_for_status()
    return response.text


def scrape_bbb(business: dict) -> dict:
    if not business["bbb_url"]:
        print(f"  [{business['id']}] Skipped — no URL provided.")
        return {"id": business["id"], "bbb_url": None, "total_reviews": None, "average_rating": None, "error": "No URL provided"}

    print(f"  [{business['id']}] Scraping ...")

    # Try residential first (cheaper), then stealth if blocked
    proxy_attempts = [
        ("residential", 2),   # (proxy type, max tries)
        ("stealth",     2),
    ]

    last_error = None
    for proxy, tries in proxy_attempts:
        for attempt in range(1, tries + 1):
            try:
                print(f"    [{proxy}] Attempt {attempt}/{tries} ...")
                text = fetch_text(business["bbb_url"], proxy)
                parsed = parse_reviews_from_text(text)

                if parsed["total_reviews"] is None and parsed["average_rating"] is None:
                    snippet = " ".join(text.split())[:300]
                    print(f"    ⚠ Page loaded but could not parse data. Snippet: {snippet}")

                result = {
                    "id": business["id"],
                    "bbb_url": business["bbb_url"],
                    "total_reviews": parsed["total_reviews"],
                    "average_rating": parsed["average_rating"],
                    "error": None,
                }
                print(f"    ✓ Reviews: {result['total_reviews']} | Rating: {result['average_rating']}")
                return result

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                print(f"    ✗ [{proxy}] Attempt {attempt} failed: {e}")
                if attempt < tries:
                    print(f"    Retrying in {RETRY_DELAY}s ...")
                    time.sleep(RETRY_DELAY)

        print(f"    Switching to next proxy type ...")
        time.sleep(RETRY_DELAY)

    print(f"    ✗ All proxy attempts exhausted.")
    return {"id": business["id"], "bbb_url": business["bbb_url"], "total_reviews": None, "average_rating": None, "error": last_error}


def main():
    print("=== BBB Review Scraper ===\n")
    results = []

    for business in BUSINESSES:
        result = scrape_bbb(business)
        results.append(result)
        time.sleep(8)

    output_file = "bbb_reviews.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n=== Done! Results saved to {output_file} ===")
    print(f"Total processed: {len(results)} | Skipped: {sum(1 for r in results if r['bbb_url'] is None)}")


if __name__ == "__main__":
    main()
