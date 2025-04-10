import urllib.request as url
import pandas as pd
import pdb
import re
import os
from textstat import *

for vl in range(1,10):
    for pg in range(1,21):
        filename = f"2012_vol{vl}_{pg}"
        basepath = "Articles_Data/articles_2012"
        if f"urls_{filename}.csv" in os.listdir(basepath):
            art_csv = pd.read_csv(f"{basepath}/urls_{filename}.csv")
            art_url = art_csv.url
            subj_csv = pd.read_csv(f"{basepath}/subjects_{filename}.csv")

            dois, cind, fks, dates = [], [], [], []
            for (i, url_i) in enumerate(art_url):
                article_page = url.urlopen(url_i)
                article_page = article_page.read().decode("utf8")
                STRT = re.search("<div class=\"main-content\">", article_page)
                if STRT is not None :
                    FNSH = STRT.span()[1] + re.search("</div>", article_page[STRT.span()[1]:]).span()[0]
                    TXT_data = article_page[STRT.span()[1]:FNSH]

                    cind.append(coleman_liau_index(TXT_data))
                    fks.append(flesch_kincaid_grade(TXT_data))
                    dois.append(art_csv.doi[i])
                    dates.append(art_csv.date[i])
                    print(f"DOI: {art_csv.doi[i]} URL: {url_i} COLE IDX: {cind[-1]} FK IDX: {fks[-1]}")
                else:
                    print(f"DOI: {art_csv.doi[i]} not accessible.")
            data = pd.DataFrame(dict([("doi",dois),("fk_idx", fks),("cole_idx", cind ), ("date", dates)]))
            data.to_csv(f"{basepath}/scores_{filename}.csv", sep="\t", index = False)
pdb.set_trace()