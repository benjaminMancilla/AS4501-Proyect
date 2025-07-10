import os
import csv
import pandas as pd
from alerce.core import Alerce
import requests
import argparse

# Auxiliary function for removing oids of  the error log
def remove_from_error_log(target_oid):
    rows = []
    with open(error_file, newline='', encoding='utf-8') as ef:
        reader = csv.DictReader(ef)
        rows = [row for row in reader if row['oid'] != target_oid]

    with open(error_file, 'w', newline='', encoding='utf-8') as ef:
        writer = csv.DictWriter(ef, fieldnames=['oid', 'error_type', 'message'])
        writer.writeheader()
        writer.writerows(rows)


# Parse CLI arguments
parser = argparse.ArgumentParser(description="Download alert lightcurves with optional resume.")
parser.add_argument('--type', choices=['good','bad'], default='good',
                    help="Download OIDs labeled 'good' or 'bad'")
parser.add_argument('--continue', dest='resume', action='store_true',
                    help='Skip OIDs already logged as success or error')
parser.add_argument('--retry-errors', action='store_true',
                    help='Retry downloading OIDs that previously failed')
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

# Check if it is a retry
if args.retry_errors:
    oids = []
    with open(error_file, newline='', encoding='utf-8') as ef:
        reader = csv.DictReader(ef)
        oids ={row['oid'] for row in reader}
    oids = list(oids)
else:
    # Load summary and filter good oids
    df = pd.read_csv(summary_csv, dtype=str)
    oids = df.loc[df['label']==args.type, 'oid'].unique().tolist()

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

        # Log success
        with open(success_file, 'a', newline='', encoding='utf-8') as sf:
            csv.writer(sf).writerow([oid])

        # If retrying errors, remove from error log
        if args.retry_errors:
            remove_from_error_log(oid)

        if args.retry_errors:
            print(f"[+] Successfully downloaded {oid} and logged success.")

    except requests.exceptions.RequestException as http_err:
        # Log HTTP errors
        with open(error_file, 'a', newline='', encoding='utf-8') as ef:
            csv.writer(ef).writerow([oid, type(http_err).__name__, str(http_err)])
    except Exception as err:
        # Log other errors
        with open(error_file, 'a', newline='', encoding='utf-8') as ef:
            csv.writer(ef).writerow([oid, type(err).__name__, str(err)])

print("Process completed.")




