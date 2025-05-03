import urllib.request as url
import pandas as pd
import pdb
import re
import os 
data_list = []
subjects_list = []
for yr in [2020,2021,2022,2023,2024,2025]:
    for fname in os.listdir(f"Articles_Data/articles_{yr}"):
        if "scores" in fname:
            data_list.append(pd.read_csv(f"Articles_Data/articles_{yr}/{fname}", sep = "\t"))
        if "subjects" in fname:
            subjects_list.append(pd.read_csv(f"Articles_Data/articles_{yr}/{fname}", sep = "\t"))
pd.concat(data_list).to_csv("sample_data/Nature_scores.csv")
pd.concat(subjects_list).to_csv("sample_data/Nature_subjects.csv")

pdb.set_trace()

yr = 2025
for vl in range(1,11):
    for pg in range(1,21):
        filename = f"{yr}_vol{vl}_{pg}"
        basepath = f"Articles_Data/articles_{yr}"
        if f"urls_{filename}.csv" in os.listdir(basepath):
            art_csv = pd.read_csv(f"{basepath}/urls_{filename}.csv", sep = "\t")
            art_url = art_csv.url
            subj_csv = pd.read_csv(f"{basepath}/subjects_{filename}.csv", sep = "\t")

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