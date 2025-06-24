# crawler.py
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def scan_all_sources(keywords):
    results = []

    def keyword_match(text):
        return any(kw in text.lower() for kw in keywords)

    # Example: DRDO
    try:
        url = "https://www.drdo.gov.in/careers"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.select(".view-content a"):
            title = link.get_text(strip=True)
            href = link.get("href")
            if keyword_match(title):
                results.append({
                    "Department": "DRDO",
                    "Job Title": title,
                    "URL": f"https://www.drdo.gov.in{href}",
                    "Posted On": "",
                    "Matched Keyword": ', '.join([kw for kw in keywords if kw in title.lower()])
                })
    except Exception as e:
        print("[DRDO Error]", e)

    # More departments can be added here with similar blocks
    # Example: ISRO, BARC, MeitY, SEBI, etc.

    return pd.DataFrame(results)
