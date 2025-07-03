# crawler.py (Expanded with More Portals + Enhanced Date Extraction)

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import tempfile
import fitz  # PyMuPDF
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    UnexpectedAlertPresentException, StaleElementReferenceException,
    ElementClickInterceptedException, NoSuchElementException
)
import time

DEFAULT_KEYWORDS = ["analytics", "data science"]

GOVT_PORTALS = [
    {
        "name": "DIC",
        "url": "https://dic.gov.in/careers/?search_keywords={keyword}",
        "base": "https://dic.gov.in",
        "type": "keyword_url"
    },
    {
        "name": "MeitY",
        "url": "https://www.meity.gov.in/offerings/vacancies?page=1",
        "base": "https://www.meity.gov.in",
        "type": "static"
    },
    {
        "name": "NeGD",
        "url": "https://negd.gov.in/careers",
        "base": "https://negd.gov.in",
        "type": "static"
    },
    {
        "name": "NIC",
        "url": "https://www.nic.in/vacancy/",
        "base": "https://www.nic.in",
        "type": "static"
    },
    {
        "name": "CDAC",
        "url": "https://www.cdac.in/index.aspx?id=current_jobs",
        "base": "https://www.cdac.in",
        "type": "static"
    },
    {
        "name": "DST",
        "url": "https://dst.gov.in/administrationfinance/recruitment-cell",
        "base": "https://dst.gov.in",
        "type": "static"
    }
]

def keyword_filter(text, keywords):
    return any(kw.lower() in text.lower() for kw in keywords)

def get_absolute_url(base, href):
    if not href:
        return ""
    return href if href.startswith("http") else base + ("/" if not href.startswith("/") else "") + href

def extract_metadata_from_text(text):
    metadata = {}
    posted_match = re.search(r"(Posted on|Dated)\s*[:\-]?\s*(\d{1,2}[\/\-.]?\s?[A-Za-z]+\s?\d{2,4})", text, re.IGNORECASE)
    if posted_match:
        metadata["posted"] = posted_match.group(2)

    last_date_match = re.search(r"(Last\s*Date|Closing\s*Date|Deadline|last date of submission|Last date for submission of application|Last Date of Application)\s*[:\-]?\s*(\d{1,2}[\/\-.]?\s?[A-Za-z]+\s?\d{2,4})", text, re.IGNORECASE)
    if last_date_match:
        metadata["last_date"] = last_date_match.group(2)

    exp_match = re.search(r"(\d+\+?\s+years?)\s+(of\s+)?experience", text, re.IGNORECASE)
    if exp_match:
        metadata["experience"] = exp_match.group(1)

    loc_match = re.search(r"(Location|Place\s*of\s*Posting)\s*[:\-]?\s*([A-Za-z,\s]+)", text, re.IGNORECASE)
    if loc_match:
        metadata["location"] = loc_match.group(2).strip()

    return metadata

def parse_pdf_for_keywords(pdf_url, keywords):
    jobs = []
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            r = requests.get(pdf_url, timeout=10)
            tmp.write(r.content)
            tmp.flush()
            doc = fitz.open(tmp.name)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()

            if keyword_filter(full_text, keywords):
                metadata = extract_metadata_from_text(full_text)
                jobs.append({
                    "title": f"Match in PDF: {os.path.basename(pdf_url)}",
                    "link": pdf_url,
                    "source": "PDF",
                    "posted": metadata.get("posted", ""),
                    "last_date": metadata.get("last_date", ""),
                    "experience": metadata.get("experience", ""),
                    "location": metadata.get("location", "")
                })
        os.remove(tmp.name)
    except Exception:
        pass
    return jobs

def generic_scraper(portal, keywords, search_keyword=None):
    jobs = []
    try:
        url = portal["url"].format(keyword=search_keyword) if portal.get("type") == "keyword_url" else portal["url"]

        if "dic.gov.in" in url:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)

            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")))
                search_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                search_input.clear()
                search_input.send_keys(search_keyword.replace("+", " "))
                time.sleep(1)
                search_input.send_keys(Keys.ENTER)
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                cards = driver.find_elements(By.CSS_SELECTOR, "div.jobgrid")

                for card in cards:
                    try:
                        title_el = card.find_element(By.CSS_SELECTOR, "span.job-title")
                        title = title_el.text.strip()
                        link = card.get_attribute("onclick").split("'")[1]
                        if keyword_filter(title, keywords):
                            parent = card.find_element(By.XPATH, ".//ancestor::div[contains(@class, 'grid-item')]")
                            posted = parent.find_element(By.CLASS_NAME, "job-date").text.strip()
                            exp = parent.find_element(By.CLASS_NAME, "job-type").text.strip()
                            loc = parent.find_element(By.CLASS_NAME, "job-location").text.strip()
                            text = card.text
                            metadata = extract_metadata_from_text(text)
                            last_date = metadata.get("last_date", "")
                            jobs.append({
                                "title": title,
                                "link": link,
                                "posted": posted,
                                "experience": exp,
                                "location": loc,
                                "last_date": last_date,
                                "source": portal["name"]
                            })
                    except Exception:
                        continue
            finally:
                driver.quit()

        else:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            content_sections = soup.find_all(["a", "li", "p", "td"])
            for tag in content_sections:
                text = tag.get_text(strip=True)
                href_tag = tag if tag.name == "a" else tag.find("a", href=True)
                href = href_tag.get("href") if href_tag else None
                if text and keyword_filter(text, keywords):
                    full_link = get_absolute_url(portal["base"], href)
                    metadata = extract_metadata_from_text(text)
                    jobs.append({
                        "title": text,
                        "link": full_link,
                        "source": portal["name"],
                        "posted": metadata.get("posted", ""),
                        "last_date": metadata.get("last_date", ""),
                        "experience": metadata.get("experience", ""),
                        "location": metadata.get("location", "")
                    })
                if href and href.endswith(".pdf"):
                    jobs.extend(parse_pdf_for_keywords(get_absolute_url(portal["base"], href), keywords))

    except Exception:
        pass
    return jobs

def run_all_scrapers(keywords=DEFAULT_KEYWORDS):
    all_jobs = []
    for portal in GOVT_PORTALS:
        if portal.get("type") == "keyword_url":
            for keyword in keywords:
                all_jobs.extend(generic_scraper(portal, keywords, keyword))
        else:
            all_jobs.extend(generic_scraper(portal, keywords))
    return pd.DataFrame(all_jobs, columns=["title", "link", "posted", "experience", "location", "source", "last_date"])

def scan_all_sources(keywords=DEFAULT_KEYWORDS):
    return run_all_scrapers(keywords)

if __name__ == "__main__":
    df = run_all_scrapers()
    print(df.to_string(index=False))
