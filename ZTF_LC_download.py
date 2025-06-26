import os
import csv
import pandas as pd
from alerce.core import Alerce
import requests

df = pd.read_csv('veto_summary.csv', dtype=str)
good_oids = df.loc[df['label']=='good', 'oid'].unique().tolist() 

alerce = Alerce()

os.makedirs('logs', exist_ok=True)
success_file = os.path.join('logs', 'success.csv')
error_file   = os.path.join('logs', 'errors.csv')

with open(success_file, 'w', newline='', encoding='utf-8') as sf, \
     open(error_file,   'w', newline='', encoding='utf-8') as ef:
    writer_s = csv.writer(sf)
    writer_e = csv.writer(ef)
    writer_s.writerow(['oid'])  
    writer_e.writerow(['oid','error_type','message']) 

out_dir = 'alerce_lightcurves'
os.makedirs(out_dir, exist_ok=True)
for oid in good_oids:
    try:

        result = alerce.query_lightcurve(oid, format='pandas')
        df_det = pd.DataFrame(result['detections'])

        path = os.path.join(out_dir, f"{oid}_detections.csv")
        df_det.to_csv(path, index=False)       

        with open(success_file, 'a', newline='', encoding='utf-8') as sf:
            csv.writer(sf).writerow([oid])

    except requests.exceptions.RequestException as http_err:
        with open(error_file, 'a', newline='', encoding='utf-8') as ef:
            csv.writer(ef).writerow([oid, type(http_err).__name__, str(http_err)])
    except Exception as err:
        with open(error_file, 'a', newline='', encoding='utf-8') as ef:
            csv.writer(ef).writerow([oid, type(err).__name__, str(err)])

print("Process completed.")



