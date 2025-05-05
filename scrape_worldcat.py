import time
import urllib.parse
import pandas as pd
import re
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ─── CONFIGURATION ──────────────────────────────────────────────────────
# Chemin vers ton ChromeDriver sur Mac
CHROMEDRIVER_PATH = '/Users/oliviercloutier/Desktop/chromedriver/chromedriver'

YEAR_FROM   = 2020
YEAR_TO     = 2025
TEST_LIMIT  = None           # Nombre max d’articles par revue pour tester
OUTPUT_ALL  = 'worldcat_all.csv'

JOURNALS_ISSN = {
    'Nature': '0028-0836',
    'Science': '0036-8075',
    'Cell': '0092-8674',
    'Nature Biotechnology': '1546-1696',
    'Nature Climate Change': '1758-6798',
    'Trends in Ecology & Evolution': '0169-5347',
    'Nature Communications': '2041-1723',
    'Nature Ecology & Evolution': '2397-334X',
    'Science Advances': '2375-2548',
    'Annual Review of Ecology, Evolution, and Systematics': '1543-592X',
    'Molecular Biology and Evolution': '0737-4038',
    'Proceedings of the National Academy of Sciences (PNAS)': '0027-8424',
    'Ecology Letters': '1461-023X',
    'Molecular Ecology': '0962-1083',
    'Ecography': '1600-0587',
    'Conservation Biology': '0888-8892',
    'Functional Ecology': '0269-8463',
    'Ecological Applications': '1051-0761',
    'Scientific Reports': '2045-2322',
    'PLOS One': '1932-6203',
    'PeerJ': '2167-8359'
}
# ─────────────────────────────────────────────────────────────

def make_search_url(issn: str) -> str:
    base  = 'https://uqar.on.worldcat.org/search'
    query = f'n2:({issn}) AND (yr:{YEAR_FROM}..{YEAR_TO})'
    params = {
        'queryString':        query,
        'databaseList':       '283,638',
        'clusterResults':     'true',
        'groupVariantRecords':'false',
        'expandSearch':       'false',
        'translateSearch':    'false',
        'lang':               'en',
        'scope':              '',
        'changedFacet':       'scope',
        'bookReviews':        'off'
    }
    return base + '?' + urllib.parse.urlencode(params, safe='():. ')

def init_driver():
    opts = webdriver.ChromeOptions()
    opts.add_experimental_option('excludeSwitches', ['enable-automation'])
    opts.add_argument('--remote-allow-origins=*')
    opts.add_argument('--headless')             # commente si tu veux voir Chrome
    opts.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(
        service=ChromeService(CHROMEDRIVER_PATH),
        options=opts
    )

def extract_record(driver, journal_name, issn):
    rec = {
        'journal':         journal_name,
        'issn':            issn,
        'title':           None,
        'authors':         None,
        'year':            None,
        'volume_issue':    None,
        'publication_date':None,
        'doi':             None
    }
    try:
        rec['title'] = driver.find_element(
            By.CSS_SELECTOR,
            '[data-testid^="title-"] span[data-testid="highlighted-term-container"]'
        ).text.strip()
    except: pass

    try:
        auths = driver.find_elements(
            By.CSS_SELECTOR,
            '[data-testid*="-brief-bib-authors-primary-author-link-"] ' +
            'span[data-testid="highlighted-term-container"]'
        )
        rec['authors'] = '; '.join(a.text.strip() for a in auths if a.text.strip())
    except: pass

    try:
        rec['year'] = driver.find_element(
            By.CSS_SELECTOR,
            '[data-testid^="item-detail-record-date-"]'
        ).text.strip()
    except: pass

    try:
        spans = driver.find_elements(
            By.CSS_SELECTOR,
            '[data-testid^="publisher-info-"] span.MuiTypography-root'
        )
        for sp in spans:
            tx = sp.text.strip()
            if re.match(r'^v\d+ n\d+.*\(\d{8}\)', tx):
                rec['volume_issue'] = tx
                m = re.search(r'\((\d{4})(\d{2})(\d{2})\)', tx)
                if m:
                    rec['publication_date'] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                break
    except: pass

    try:
        rec['doi'] = driver.find_element(
            By.CSS_SELECTOR,
            'a[data-testid="doi-link-0"]'
        ).text.strip()
    except: pass

    return rec

def scrape_journal(journal_name, issn, test_limit=TEST_LIMIT):
    print(f'\n📖 Scraping {journal_name} ({issn})')
    driver = init_driver()
    driver.get(make_search_url(issn))
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/search/detail/']"))
    )

    # Clique sur le premier résultat
    first = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/search/detail/']"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", first)
    try:
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable(first))
        first.click()
    except:
        driver.execute_script("arguments[0].click();", first)
    time.sleep(1)

    # Récupère total "Result 1 of N"
    lbl = driver.find_element(By.ID, 'result-statement').get_attribute('aria-label')
    total = int(lbl.split('of')[-1].replace(',', '').strip()) if 'of' in lbl else None

    records, seen = [], set()
    while True:
        try:
            idx = int(driver.find_element(By.ID, 'result-statement').text.split()[1])
            print(f"Progression : {idx}/{total or '?'}", end=' → ')

            rec = extract_record(driver, journal_name, issn)
            key = rec['doi'] or (rec['title'], rec['authors'])
            if rec['title'] and 'erratum' not in rec['title'].lower() and key not in seen:
                seen.add(key); records.append(rec)
                print(f"✔️ {rec['title'][:60]}…")
            else:
                print("⏭️ doublon/erratum")

            if test_limit and len(records) >= test_limit:
                print("🛑 Limite test atteinte"); break

            # Clique suivant et attend nouvel index
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'svg[data-testid="ChevronRightIcon"]'))
            )
            btn.find_element(By.XPATH, './ancestor::button').click()
            WebDriverWait(driver, 10).until(
                lambda d: int(d.find_element(By.ID, 'result-statement').text.split()[1]) > idx
            )
        except Exception as e:
            print("⚠️ Fin ou erreur :", e)
            break

    driver.quit()
    return records

def main():
    all_records = []
    for journal, issn in JOURNALS_ISSN.items():
        recs = scrape_journal(journal, issn)
        all_records.extend(recs)
        time.sleep(2)  # petite pause entre les revues

    pd.DataFrame(all_records).to_csv(OUTPUT_ALL, index=False)
    print(f"\n✅ Terminé : {len(all_records)} articles dans {OUTPUT_ALL}")

if __name__ == '__main__':
    main()
