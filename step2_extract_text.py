#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import time
import shutil
import requests
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pdfminer.high_level import extract_text
from sklearn.feature_extraction.text import TfidfVectorizer
import textstat

# ─── CONFIGURATION ──────────────────────────────────────────────────────
INPUT_CSV       = "worldcat_all.csv"
OUTPUT_CSV      = "step2_results.csv"
PDF_DIR         = "step2_pdfs"
TXT_DIR         = "step2_txts"
LIMIT           = 20
CHROMEDRIVER    = "/usr/local/bin/chromedriver"  # ← ajuste ton path sur Mac
# ─────────────────────────────────────────────────────────────────────────

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)

# ─── UTILS ────────────────────────────────────────────────────────────────

def download_pdf_direct(doi):
    """Tente le téléchargement direct via l’URL nature.com/articles/{suffix}.pdf"""
    suffix = doi.split("/",1)[1]
    url = f"https://www.nature.com/articles/{quote(suffix)}.pdf"
    try:
        r = requests.get(url, stream=True, timeout=30)
        if r.status_code == 200 and "pdf" in r.headers.get("Content-Type",""):
            path = os.path.join(PDF_DIR, f"{suffix}.pdf")
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return path
    except Exception:
        pass
    return None

def download_pdf_selenium(doi):
    """Fallback Selenium: va sur la page nature, clique Download PDF"""
    suffix = doi.split("/",1)[1]
    url = f"https://www.nature.com/articles/{quote(suffix)}"
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    driver = webdriver.Chrome(service=ChromeService(CHROMEDRIVER), options=opts)
    driver.get(url)
    try:
        btn = WebDriverWait(driver,10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,".c-pdf-download__link"))
        )
        btn.click()
        time.sleep(5)
        # trouve le dernier fichier dans папка downloads
        # OU récupère response via requête network…
        # (implémentation laissée simple ici)
    except:
        driver.quit()
        return None
    driver.quit()
    return os.path.join(PDF_DIR, f"{suffix}.pdf")  # à ajuster si path différent

def pdf_to_text(pdf_path):
    """Extrait le texte, nettoie annexes/figures/références"""
    txt = extract_text(pdf_path)
    # naive strip en-dessous de "References" / "Acknowledgements"
    for marker in ("References", "REFERENCES", "Acknowledgements", "ACKNOWLEDGEMENTS"):
        if marker in txt:
            txt = txt.split(marker)[0]
    return txt

def extract_keywords(documents, top_k=10):
    """TF–IDF sur le corpus -> top_k keywords par doc"""
    vec = TfidfVectorizer(stop_words="english", max_features=5000)
    X = vec.fit_transform(documents)
    terms = vec.get_feature_names_out()
    kwds = []
    for row in X:
        idxs = row.toarray()[0].argsort()[::-1][:top_k]
        kwds.append("; ".join(terms[i] for i in idxs))
    return kwds

# ─── BOUCLE PRINCIPALE ───────────────────────────────────────────────────

results = []
dois, rows = [], []

with open(INPUT_CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i,row in enumerate(reader):
        if i>=LIMIT: break
        dois.append(row["doi"])
        rows.append(row)

# Télécharger et traiter
texts = []
for idx,(doi,row) in enumerate(zip(dois,rows), start=1):
    journal = row["journal"]
    print(f"Article {idx}/{len(dois)} → DOI={doi} | Journal={journal}")
    if journal!="Nature":
        print("  ⚠️ Skip non-Nature")
        continue

    # 1) Télécharger PDF
    pdf = download_pdf_direct(doi)
    if not pdf:
        print("  ⚠️ Direct fail, fallback Selenium…")
        pdf = download_pdf_selenium(doi)
    if not pdf or not os.path.exists(pdf):
        print("  ❌ PDF non dispo, skip")
        continue
    print("  ✔️ PDF:", pdf)

    # 2) PDF → texte
    txt = pdf_to_text(pdf)
    texts.append(txt)

    # 3) Supprimer PDF
    os.remove(pdf)

# 4) Extraction keywords & lisibilité
keywords = extract_keywords(texts, top_k=8)
for (doi,row), txt, kw in zip(zip(dois,rows), texts, keywords):
    res = {
        "doi": doi,
        "title": row["title"],
        "authors": row["authors"],
        "journal": row["journal"],
        "publication_date": row.get("publication_date",""),
        "keywords": kw,
        "flesch_reading_ease": textstat.flesch_reading_ease(txt),
        "smog_index": textstat.smog_index(txt),
        "flesch_kincaid_grade": textstat.flesch_kincaid_grade(txt),
        "dale_chall_readability_score": textstat.dale_chall_readability_score(txt),
        "text_path": os.path.join(TXT_DIR, f"{doi.split('/',1)[1]}.txt")
    }
    # sauvegarde txt
    with open(res["text_path"], "w", encoding="utf-8") as f:
        f.write(txt)
    results.append(res)

# 5) Écriture du CSV final
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    writer.writeheader()
    writer.writerows(results)

print(f"✅ Étape 2 terminée — {len(results)} articles traités, CSV → {OUTPUT_CSV}")
