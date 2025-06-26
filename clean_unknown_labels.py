import json
import re
import pandas as pd
from collections import defaultdict

"""
There is varius labels that are not recognized by the script. We need to
map them to the standard labels used in the script. (Clean data)
"""

"""
  10  -> M31
   6  -> already reported
   3  -> CV
   2  -> offset?
   2  -> moving object
   2  -> many detection, but only one stamp visible  
   2  -> ?
   2  -> M31 nova/*
   1  -> already reported
   1  -> offset
   1  -> um not sure
   1  -> M31 point src
   1  -> faint LSDR9 host at position
   1  -> why did we miss this on thursday???
   1  -> central but looks strong to me (many detections, rising)
   1  -> Host less (good)
   1  -> clarly risign, this a good one
   1  -> DE
   1  -> has faint host in LSDR10 (not in DR9)
   1  -> 2 SNe?
   1  -> looks good
   1  -> hostless
   1  -> (shape looks bad, but same as nearby star => keep?)
   1  -> I agree, keep
   1  -> agree
   1  -> weak?
   1  -> !!! (very interesting)
   1  -> very faint host in LSDR9
   1  -> it looks fine to me
   1  -> Report, but unusual, as it is a optically red, radio source
   1  -> stamp no load
   1  -> same as ZTF18aawourc
   1  -> same as ZTF22ablbolm
   1  -> brght star contamination ?
   1  -> has faint LSDR9 blue extended host
   1  -> GOOD. 2 srcs? => Grav Len QSO?
   1  -> strange ATLAS LC ~3 mag difference , most be something wrong with ATLAS
   1  -> in m31
   1  -> offset from nucleus?
   1  -> offset from nucleus. good for me
"""

# Manual mapping of unknown labels to standard tags
TEXT_TO_TAG = {
    r'good':                            'OK',
    r'clarly risign, this a good one': 'OK',
    r'looks good':                      'OK',
    r'it looks fine to me':            'OK',
    r'host less \(good\)':           'OK',
    r'\bagree\b':                     'OK',
    r'i agree, keep':                  'OK',
    r'keep\?':                        'OK',
    r'central but looks strong to me': 'OK',
    r'!!!':                             'OK',
    r'already reported':                'DR',
    r'\bCV\b':                        'ID',
    r'\boffset\b':                    'OK', # offset => OK (clearly offset)
    r'offset\?':                      'OK',
    r'offset from nucleus\?':         'OK',
    r'offset from nucleus\. good for me': 'OK',
    r'moving object':                  'BD',
    r'many detection, but only one stamp visible': 'SH',
    r'2 SNe\?':                       'BD',
    r'brght star contamination \?':   'SH',
    r'strange ATLAS LC ~3 mag difference': 'BD',
    r'report, but unusual, as it is a optically red, radio source': 'DR', #I guess? It's a report
    r'stamp no load':                  '',
    r'2 srcs\? => Grav Len QSO\?':    'OK',
    r'^\?$':                           '', # ???????????????
    r'^M31$':                          '',
    r'\bin m31\b':                   '', # similar
    r'm31 nova/\*':                   'DR', # I guess this is a report
    r'm31 point src':                  'ID',
    r'hostless':                       'HL',
    r'weak\?':                        '',
    # This ones are tricky 
    r'has faint lsdr9 host at position': '',
    r'has faint host in lsdr10 \(not in dr9\)': '',
    r'very faint host in lsdr9':      '',
    r'has faint lsdr9 blue extended host': '',
    r'um not sure':                    '',
    r'why did we miss this on thursday\?\?\?': '', #What happened on freaky Thursday?
    r'^DE$':                           'DR', #What??????
    r'\(shape looks bad, but same as nearby star => keep\?\)': 'OK',
    r'same as ZTF18aawourc':           'ID', #???
    r'same as ZTF22ablbolm':           'ID', #???
    r'faint LSDR9 host at position':   '', #???
    r'report':                         'DR',
}


def map_text_to_tag(text):
    t = text.lower().strip()
    for key, tag in TEXT_TO_TAG.items():
        if re.search(key, t, re.IGNORECASE):
            return tag

    if t:
        raise ValueError(f"Unknown label: '{text}'")
    return ''


csv_path = 'vetoes_all.csv'
json_old = 'veto_dict.json'    
json_unknown = 'unknown_labels.json'

df = pd.read_csv(csv_path, dtype=str)
with open(json_old, 'r', encoding='utf-8') as f:
    veto_clean = json.load(f)
with open(json_unknown, 'r', encoding='utf-8') as f:
    unknowns = json.load(f)


for u in unknowns:
    oid = u['oid']
    date = u['date']
    col = u['column']
    raw = u['value']
    tag = map_text_to_tag(raw)
    mask = (df['oid'] == oid) & (df['date'] == date)
    df.loc[mask, col] = tag

# We revisited the DataFrame to update labels
veto_new = defaultdict(list)
for _, row in df.iterrows():
    oid = row['oid']
    date = row['date']
    labels = [row[c] for c in ['AM','FB','FF','GP'] if pd.notna(row[c])]
    if any(lbl.upper() == 'OK' for lbl in labels):
        continue
    bads = [lbl for lbl in labels if lbl.upper() in {'CR','SH','BD','DR','SAT','ID'}]
    if bads:
        veto_new[oid].append(date)
    else:
        veto_new.setdefault(oid, [])

for oid, dates in veto_new.items():
    if oid in veto_clean:
        for d in dates:
            if d not in veto_clean[oid]:
                veto_clean[oid].append(d)
    else:
        veto_clean[oid] = dates


with open('veto_dict_updated.json', 'w', encoding='utf-8') as f:
    json.dump(veto_clean, f, ensure_ascii=False, indent=2)

print("Veto dictionary updated and saved to 'veto_dict_updated.json'.")