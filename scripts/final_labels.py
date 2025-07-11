import json
import pandas as pd

with open('veto_dict_updated.json', 'r', encoding='utf-8') as f:
    veto_dict = json.load(f)

rows = []
for oid, dates in veto_dict.items():
    # bad
    if dates:
        veto_date = min(dates)
        label = 'bad'
    # good
    else:
        veto_date = ''
        label = 'good'
    rows.append({'oid': oid, 'veto_date': veto_date, 'label': label})

df = pd.DataFrame(rows)
df.to_csv('veto_summary.csv', index=False)
print("Veto summary saved to 'veto_summary.csv'.")
