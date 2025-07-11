import re
import csv
import json
from collections import defaultdict

unknown_labels = []

def normalize_label(cell, oid, date, column):
    if not cell or not cell.strip():
        return None
    m = re.search(r'\b(CR|SH|BD|DR|SAT|HL|ID|OK)\b\??', cell.strip(), re.IGNORECASE)
    if m:
        return m.group(1).upper()
    unknown_labels.append({
        'oid': oid,
        'date': date,
        'column': column,
        'value': cell
    })
    return None


def build_veto_dict(csv_path):

    vetoes = defaultdict(list)
    desired_experts = ('AM', 'FB', 'FF', 'GP')

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            oid = row['oid']
            date = row['date']
            labels = []

            for col in desired_experts:
                cell = row.get(col, '')
                lbl = normalize_label(cell, oid, date, col)
                if lbl:
                    labels.append(lbl)
            # OK RULE
            if 'OK' in labels:
                continue
            # BAD RULE
            bad = [l for l in labels if l in {'CR','SH','BD','DR','SAT','ID'}]
            if not bad:
                continue
            vetoes[oid].append(date)


    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vetoes.setdefault(row['oid'], [])

    return vetoes

if __name__ == "__main__":
    csv_file = 'vetoes.csv'
    veto_dict = build_veto_dict(csv_file)

    with open('veto_dict.json', 'w', encoding='utf-8') as out:
        json.dump(veto_dict, out, ensure_ascii=False, indent=2)

    with open('unknown_labels.json', 'w', encoding='utf-8') as out:
        json.dump(unknown_labels, out, ensure_ascii=False, indent=2)

    print(f"Vetoes found: {len(veto_dict)}")


