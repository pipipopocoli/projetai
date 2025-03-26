import urllib.request as url
import pdb
import http
import pandas as pd
import re

yr_min = 2023
yr_max = 2025
base_url = "https://www.nature.com"

search_url = f"{base_url}/search?order=relevance&date_range={yr_min}-{yr_max}&journal=ncomms"
urls, auth, email, title, date = [], [], [], [], []

### FOR LOOP through pages 1...448
search_page = url.urlopen(search_url)
page = search_page.read().decode("utf8")


idx, doi_end = 0, 0

while (idx + doi_end) < len(page):
    
    idx = 0 + doi_end
    doi_start = idx + re.search("\/articles\/s", page[idx:]).span()[1]
    doi_end = doi_start + re.search("\"", page[doi_start:]).span()[0]
    doi = page[doi_start:doi_end]
    article_url = f"{base_url}/articles/s{doi}"
    urls.append(article_url)
    print(article_url)
    ## parsed from query page
    article_page = url.urlopen(article_url)
    article_page = article_page.read().decode("utf8")
    
    ## authors "contentInfo":{"authors"
    auth_span_start = re.search("\"authors\"", article_page).span()[1] + 3
    auth_span_end = auth_span_start + re.search("\"", article_page[auth_span_start:]).span()[0]
    auth.append(article_page[auth_span_start:auth_span_end])
    ## correspond. auth. "email":"claus.lamm@univie.ac.at"
    cauth_span_start = re.search("\"email\":", article_page).span()[1] + 3
    cauth_span_end = cauth_span_start + re.search("\"", article_page[cauth_span_start:]).span()[0]
    email.append(article_page[cauth_span_start:cauth_span_end])
    ## <title>
    title_span_start = re.search("<title>", article_page).span()[1]
    title_span_end = title_span_start + re.search("</title>", article_page[title_span_start:]).span()[0] 
    title.append(article_page[title_span_start:title_span_end])
    ## "datePublished"
    date_span_start = re.search("datePublished", article_page).span()[1] + 3
    date_span_end = date_span_start + re.search("\"", article_page[date_span_start:]).span()[0] 
    date.append(article_page[date_span_start:date_span_end])
## SAVES results
results = pd.DataFrame(dict([("author",auth), ("email",email),("url",urls),("date",date)]))
results.to_csv("page1_test.csv", index = False)
pdb.set_trace()