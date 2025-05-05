import sys
import logging
import time
import json
import warnings
from pathlib import Path

# Suppress common warnings (e.g., DeprecationWarning, InsecureRequestWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
try:
    import urllib3
    warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import textstat
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
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
START_YEAR = 2020
END_YEAR = 2025
CROSSREF_URL = "https://api.crossref.org/journals/{issn}/works"
SEMANTIC_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_FIELDS = "title,url,year,venue,authors,externalIds,abstract"
PAGE_SIZE = 100
TIMEOUT = 15  # seconds
DELAY = 1     # seconds
MAX_SCORES_PER_JOURNAL = 5
PROGRESS_FILE = 'progress.json'
SEMANTIC_API_KEY = '<YOUR_API_KEY>'  # <-- insert your key here
MIN_WORDS = 500  # lower threshold for debugging

# --- LOGGER SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Warn if Semantic API key is missing
if SEMANTIC_API_KEY == '<YOUR_API_KEY>':
    logger.warning("Semantic Scholar API key not set; metadata retrieval (step2) will likely fail.")

# --- HTTP SESSION WITH RETRIES ---
session = requests.Session()
retry = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
session.mount('http://', HTTPAdapter(max_retries=retry))
session.mount('https://', HTTPAdapter(max_retries=retry))
session.headers.update({
    'User-Agent': 'ArticleAnalysis/1.0',
    'x-api-key': SEMANTIC_API_KEY
})

# --- UTILS ---
def safe_get(url, **kwargs):
    """Wrapper around session.get with logging and exception handling."""
    try:
        resp = session.get(url, **kwargs)
        resp.raise_for_status()
        return resp
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def write_progress(step, done, total):
    pct = (done / total * 100) if total else 0
    logger.info(f"[{step}] {done}/{total} ({pct:.1f}%)")
    path = Path(PROGRESS_FILE)
    try:
        data = json.loads(path.read_text()) if path.exists() else {}
    except json.JSONDecodeError:
        data = {}
    data[step] = pct
    path.write_text(json.dumps(data, indent=2))

# --- STEP 1: THEORETICAL COUNTS ---
def get_expected_counts():
    records = []
    tasks = len(JOURNALS_ISSN) * (END_YEAR - START_YEAR + 1)
    done = 0
    for journal, issn in JOURNALS_ISSN.items():
        for year in range(START_YEAR, END_YEAR + 1):
            url = CROSSREF_URL.format(issn=issn)
            params = {
                'filter': f'from-pub-date:{year}-01-01,until-pub-date:{year}-12-31',
                'rows': 0
            }
            resp = safe_get(url, params=params, timeout=TIMEOUT)
            count = 0
            if resp:
                try:
                    count = resp.json().get('message', {}).get('total-results', 0)
                except ValueError as e:
                    logger.error(f"JSON decode error for {url}: {e}")
            records.append({'journal': journal, 'year': year, 'expected_count': count})
            done += 1
            write_progress('step1', done, tasks)
            time.sleep(DELAY)
    df = pd.DataFrame(records)
    df.to_csv('expected_counts.csv', index=False)
    return df

# --- STEP 2: METADATA RETRIEVAL ---
def fetch_metadata():
    records = []
    tasks = len(JOURNALS_ISSN) * (END_YEAR - START_YEAR + 1)
    done = 0
    for journal in JOURNALS_ISSN:
        for year in range(START_YEAR, END_YEAR + 1):
            offset = 0
            while True:
                params = {
                    'query': f'venue:"{journal}" year:{year}',
                    'fields': SEMANTIC_FIELDS,
                    'limit': PAGE_SIZE,
                    'offset': offset
                }
                resp = safe_get(SEMANTIC_URL, params=params, timeout=TIMEOUT)
                data = []
                if resp:
                    try:
                        data = resp.json().get('data', [])
                    except ValueError as e:
                        logger.error(f"JSON decode error for Semantic Scholar: {e}")
                        break
                if not data:
                    break
                for item in data:
                    authors = ', '.join(a.get('name', '') for a in item.get('authors', []))
                    records.append({
                        'journal': journal,
                        'title': item.get('title', ''),
                        'year': item.get('year', ''),
                        'subject': '',
                        'authors': authors,
                        'corresponding_email': '',
                        'doi': item.get('externalIds', {}).get('DOI', ''),
                        'url': item.get('url', ''),
                        'abstract': item.get('abstract', '')
                    })
                offset += PAGE_SIZE
                time.sleep(DELAY)
            done += 1
            write_progress('step2', done, tasks)
    df = pd.DataFrame(records)
    df.to_csv('meta_data.csv', index=False)
    return df

# --- STEP 3: STATS UPDATE ---
def update_retrieval_stats(meta_df, expected_df):
    counts = meta_df.groupby(['journal', 'year']).size().reset_index(name='retrieved_count')
    merged = expected_df.merge(counts, on=['journal', 'year'], how='left')
    merged['retrieved_count'] = merged['retrieved_count'].fillna(0).astype(int)
    merged['completion_rate'] = (
        merged['retrieved_count'] / merged['expected_count'].replace(0, pd.NA)
    ).fillna(0) * 100
    merged.to_csv('retrieval_stats.csv', index=False)
    return merged

# --- STEP 4: READABILITY ---
def compute_readability(meta_df):
    fk_rows, cl_rows = [], []
    score_counts = {j: 0 for j in JOURNALS_ISSN}
    total = len(meta_df)
    for idx, row in meta_df.iterrows():
        write_progress('step4', idx+1, total)
        journal = row['journal']
        if score_counts[journal] >= MAX_SCORES_PER_JOURNAL:
            continue
        doi = row.get('doi')
        if not doi:
            continue
        resp = safe_get(f'https://doi.org/{doi}', timeout=TIMEOUT)
        if not resp:
            continue
        text = BeautifulSoup(resp.content, 'lxml').get_text(' ', strip=True)
        if len(text.split()) < MIN_WORDS:
            continue
        fk = textstat.flesch_kincaid_grade(text)
        cl = textstat.coleman_liau_index(text)
        base = {k: row[k] for k in ['journal', 'title', 'year', 'authors', 'subject']}
        fk_rows.append({**base, 'fkgl': fk})
        cl_rows.append({**base, 'coleman': cl})
        score_counts[journal] += 1
        time.sleep(DELAY)
    pd.DataFrame(fk_rows).to_csv('fkgl_scores.csv', index=False)
    pd.DataFrame(cl_rows).to_csv('coleman_scores.csv', index=False)

# --- TESTS ---
def _test_update_retrieval_stats():
    df_exp = pd.DataFrame([{'journal':'TestJ', 'year':2020, 'expected_count':10}])
    df_meta = pd.DataFrame([{'journal':'TestJ', 'year':2020}] * 5)
    result = update_retrieval_stats(df_meta, df_exp)
    assert result.loc[0, 'retrieved_count'] == 5, "retrieved_count should be 5"
    assert result.loc[0, 'completion_rate'] == 50.0, "completion_rate should be 50.0"
    print("_test_update_retrieval_stats passed!")

# --- MAIN ---
if __name__ == '__main__':
    step = sys.argv[1].lower() if len(sys.argv) > 1 else 'all'
    if step == 'test':
        _test_update_retrieval_stats()
        sys.exit(0)

    expected_df = pd.DataFrame()
    meta_df = pd.DataFrame()
    if step in ('1', 'step1', 'all'):
        expected_df = get_expected_counts()
    if step in ('2', 'step2', 'all'):
        meta_df = fetch_metadata()
    if step in ('3', 'step3', 'all') and not expected_df.empty and not meta_df.empty:
        update_retrieval_stats(meta_df, expected_df)
    if step in ('4', 'step4', 'all') and not meta_df.empty:
        compute_readability(meta_df)
    logger.info('✅ Pipeline completed.')
