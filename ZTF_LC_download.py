import os
import csv
import pandas as pd
from alerce.core import Alerce
import requests
import argparse

# Parse CLI arguments
parser = argparse.ArgumentParser(description="Download alert lightcurves with optional resume.")
parser.add_argument('--type', choices=['good','bad'], default='good',
                    help="Download OIDs labeled 'good' or 'bad'")
parser.add_argument('--continue', dest='resume', action='store_true',
                    help='Skip OIDs already logged as success or error')
args = parser.parse_args()

# File paths
summary_csv   = 'veto_summary.csv'
logs_dir    = os.path.join('logs', 'lc', args.type)
success_file = os.path.join(logs_dir, 'success.csv')
error_file   = os.path.join(logs_dir, 'errors.csv')
out_dir     = os.path.join('alerce_lightcurves', args.type)

# Ensure directories and log headers
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)

if not os.path.exists(success_file):
    with open(success_file, 'w', newline='', encoding='utf-8') as sf:
        csv.writer(sf).writerow(['oid'])
if not os.path.exists(error_file):
    with open(error_file, 'w', newline='', encoding='utf-8') as ef:
        csv.writer(ef).writerow(['oid','error_type','message'])

# Load summary and filter good oids
df = pd.read_csv(summary_csv, dtype=str)
if args.type == 'good':
    oids = df.loc[df['label']=='good','oid'].unique().tolist()
else:
    oids = df.loc[df['label']=='bad','oid'].unique().tolist()

# If resume, remove already processed oids
if args.resume:
    processed = set()
    with open(success_file, newline='', encoding='utf-8') as sf:
        next(sf)
        for row in csv.reader(sf): processed.add(row[0])
    with open(error_file, newline='', encoding='utf-8') as ef:
        next(ef)
        for row in csv.reader(ef): processed.add(row[0])
    oids = [oid for oid in oids if oid not in processed]

alerce = Alerce()

# Download loop
for oid in oids:
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




