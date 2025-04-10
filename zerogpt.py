import requests
import json
import h5py
import pdb
import pandas as pd

url = "https://api.zerogpt.com/api/detect/detectText"
dois, is_human, fk_prct, ai_words, txt_words = [], [], [], [], []
basepath = "sample_data"
fname = "2012_vol1_1"
with h5py.File(f"{basepath}/{fname}.h5", "r") as inf:
    keys = [k for k in inf.keys()]
    for doi in keys:
        print(doi)
        sample_text = inf[doi].asstr()[()]

        payload = json.dumps({
        "input_text": sample_text[:15000]
        })
        headers = {
        'ApiKey': 'f88cc722-de5a-45a0-8d65-ad4004d425a4',
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        dois.append(doi)
        is_human.append(response.json().get("data").get("isHuman"))
        fk_prct.append(response.json().get("data").get("fakePercentage"))
        ai_words.append(response.json().get("data").get("aiWords"))
        txt_words.append(response.json().get("data").get("textWords"))
results = pd.DataFrame(dict([("doi", dois),("isHuman", is_human), ("fk_prct", fk_prct), ("ai_words",ai_words), ("txt_words", txt_words)])) 
results.to_csv(f"results/{fname}.csv", sep = "\t", index = False)
pdb.set_trace()
