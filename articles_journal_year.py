import urllib.request as url
import pdb
import http
import pandas as pd
import re
import numpy as np 

base_url = "https://www.nature.com"
### for yr 2012 .. 2024
yr = 2023
### for volume 1 .. 10
vl = 1
### FOR LOOP through pages 1...20
def clip(target, strt, fnsh, offset = 0):
    STRT = re.search(strt, target) 
    if STRT is None:
        return STRT
    FNSH = STRT.span()[1] + offset + re.search(fnsh, target[STRT.span()[1] + offset:]).span()[0]
    return target[STRT.span()[1]+offset:FNSH]
    
for pg in range(3,21):


    # def fetch_data_tbl(yr, vl, pg, base_url = "https://www.nature.com"):
    search_url = f"{base_url}/search?date_range={yr}-{yr}&volume={vl}&page={pg}"
    dois, urls, auth, email, title, date = [], [], [], [], [], []

    search_page = url.urlopen(search_url)
    page = search_page.read().decode("utf8")

    #### Subjects tbl
    dois_tbl, sub_tbl = [], np.array([])

    idx, doi_end = 0, 0
    

    while (idx + doi_end) < len(page):
        
        idx = 0 + doi_end
        doi_start = idx + re.search("\/articles\/s", page[idx:]).span()[1]
        doi_end = doi_start + re.search("\"", page[doi_start:]).span()[0]
        doi = page[doi_start:doi_end]
        article_url = f"{base_url}/articles/s{doi}"
        dois.append(doi)
        urls.append(article_url)
        print(article_url)
        ## parsed from query page
        article_page = url.urlopen(article_url)
        article_page = article_page.read().decode("utf8")
        ## authors "contentInfo":{"authors"
        art_aut = clip(article_page, "\"authors\"", "\"", offset=3)
        auth.append(art_aut) 
        ## correspond. auth. "email":"claus.lamm@univie.ac.at"
        art_cauth = clip(article_page, "\"email\":", "\"", offset=3)
        email.append(art_cauth) if art_cauth is not None else email.append("")
        ## <title>
        art_title = clip(article_page, "<title>", "</title>")
        title.append(art_title)
        ## "datePublished"
        art_date = clip(article_page, "datePublished", "\"", offset = 3)
        date.append(art_date)
        ## subjects
        art_subjects = clip(article_page, "subjects\":\"", "\"")
        art_subjects = art_subjects.split(",")
        sub_tbl = np.concatenate([sub_tbl, art_subjects])
        [dois_tbl.append(doi) for i in range(len(art_subjects))]

    ### SAVES the subjects table    
    subjects_table = pd.DataFrame(dict([("doi", dois_tbl), ("subject",sub_tbl)]))
    subjects_table.to_csv(f"subjects_{yr}_vol{vl}_{pg}.csv", index = False)

    ## SAVES the urls
    results = pd.DataFrame(dict([("doi", dois), ("author",auth), ("title", title), ("email",email),("url",urls),("date",date)]))
    results.to_csv(f"urls_{yr}_vol{vl}_{pg}.csv", index = False)

pdb.set_trace()