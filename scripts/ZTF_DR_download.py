import os
import csv
import pandas as pd
import numpy as np
import requests
import argparse
import json
import time
from io import BytesIO
import threading
from concurrent.futures import ThreadPoolExecutor

# Thread-safe lock for log writes\log_lock = threading.Lock()
log_lock = threading.Lock()

# Auxiliary function for removing oids from the error log
def remove_from_error_log(target_oid, error_file):
    with log_lock:
        rows = []
        if os.path.exists(error_file):
            with open(error_file, newline='', encoding='utf-8') as ef:
                reader = csv.DictReader(ef)
                rows = [row for row in reader if row['oid'] != target_oid]
        with open(error_file, 'w', newline='', encoding='utf-8') as ef:
            writer = csv.DictWriter(ef, fieldnames=['oid', 'error_type', 'message'])
            writer.writeheader()
            writer.writerows(rows)

# Fetch lightcurve from ALeRCE DR API
def get_DR(oid, ra, dec, url="https://api.alerce.online/ztf/dr/v1/light_curve/"):
    query = {'ra': ra, 'dec': dec, 'radius': 1.5}
    response = requests.get(url, params=query)
    response.raise_for_status()
    output = response.json()
    dfs = []
    for det in output:
        df_det = pd.DataFrame({
            'hmjd': np.array(det['hmjd']),
            'mag': np.array(det['mag']),
            'magerr': np.array(det['magerr'])
        })
        df_det['ID'] = int(det['_id'])
        df_det['filterid'] = int(det['filterid'])
        df_det['oid'] = oid
        dfs.append(df_det)
    return (pd.concat(dfs, ignore_index=True) if dfs else None), output

# Fetch full lightcurve from IRSA by list of IDs
def get_ZTF_DR_full(IDs, url="https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?"):
    params = "".join([f"ID={ID}&" for ID in IDs])
    url_full = url + params + "BAD_CATFLAGS_MASK=32768&FORMAT=CSV"
    response = requests.get(url_full)
    response.raise_for_status()
    return pd.read_csv(BytesIO(response.content))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Download DR lightcurves with logging, resume, partitioning, full mode, and test mode."
    )
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--retry-errors', action='store_true')
    parser.add_argument('--part', type=int, choices=[1,2,3])
    parser.add_argument('--test-oid', type=str)
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()

    # Determine summary CSV
    if args.full:
        summary_csv = 'tabular_data/data_release.csv'
        part_label = 'full'
    else:
        summary_csv = 'other/oids_ra_dec.csv'
        part_label = f"part{args.part}" if args.part else 'all'

    logs_dir = os.path.join('logs', 'dr', part_label)
    out_dir  = os.path.join('dr_lightcurves', part_label)
    success_file = os.path.join(logs_dir, 'success.csv')
    error_file   = os.path.join(logs_dir, 'errors.csv')

    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    # Initialize logs
    with log_lock:
        if not os.path.exists(success_file):
            with open(success_file,'w',newline='',encoding='utf-8') as sf:
                csv.writer(sf).writerow(['oid'])
        if not os.path.exists(error_file):
            with open(error_file,'w',newline='',encoding='utf-8') as ef:
                csv.writer(ef).writerow(['oid','error_type','message'])

    # Load records
    if args.full:
        df_ids = pd.read_csv(summary_csv, dtype={'oid':str,'ID':str})
        grouped = df_ids.groupby('oid')['ID'].unique().reset_index()
        grouped['ID'] = grouped['ID'].apply(list)
        records = grouped.to_dict('records')
    else:
        df = pd.read_csv(summary_csv, dtype={'oid':str,'ra':float,'dec':float})
        records = df.to_dict('records')

    # Resume or retry logic
    if args.retry_errors:
        with log_lock, open(error_file,newline='',encoding='utf-8') as ef:
            errs = {row['oid'] for row in csv.DictReader(ef)}
        records = [r for r in records if r['oid'] in errs]
    elif args.test_oid:
        records = [r for r in records if r['oid']==args.test_oid]
    elif args.resume:
        done = set()
        with log_lock, open(success_file,newline='',encoding='utf-8') as sf:
            next(sf)
            for row in csv.reader(sf): done.add(row[0])
        with log_lock, open(error_file,newline='',encoding='utf-8') as ef:
            next(ef)
            for row in csv.reader(ef): done.add(row[0])
        records = [r for r in records if r['oid'] not in done]

    # Partitioning for non-full mode
    if not args.full and args.part and not args.retry_errors and not args.test_oid:
        total = len(records)
        blk = total // 3
        start = blk*(args.part-1)
        end = blk*args.part if args.part<3 else total
        records = records[start:end]
        print(f"Downloading part {args.part}: records {start}-{end} of {total}.")

    # Download loop
    if args.full:
        def download_full(rec):
            oid = rec['oid']
            try:
                df_full = get_ZTF_DR_full(rec['ID'])
                df_full.to_csv(os.path.join(out_dir, f"{oid}_full.csv"), index=False)
                with log_lock, open(success_file, 'a', newline='', encoding='utf-8') as sf:
                    csv.writer(sf).writerow([oid])
                print(f"[+] Successfully downloaded {oid} (full)")
                time.sleep(0.5)
            except Exception as e:
                with log_lock, open(error_file, 'a', newline='', encoding='utf-8') as ef:
                    csv.writer(ef).writerow([oid, type(e).__name__, str(e)])

        # Parallel execution across 4 workers
        n_workers = 4
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            executor.map(download_full, records)
    else:
        for rec in records:
            oid = rec['oid']
            try:
                lc, raw = get_DR(oid, rec.get('ra'), rec.get('dec'))
                if lc is not None:
                    lc.to_csv(os.path.join(out_dir, f"{oid}_dr.csv"), index=False)
                if args.test_oid:
                    with log_lock, open(os.path.join(out_dir, f"{oid}_dr.json"), 'w', encoding='utf-8') as jf:
                        json.dump(raw, jf, indent=2)
                with log_lock, open(success_file, 'a', newline='', encoding='utf-8') as sf:
                    csv.writer(sf).writerow([oid])
                print(f"[+] Successfully downloaded {oid}")
                time.sleep(0.5)
                if args.retry_errors:
                    remove_from_error_log(oid, error_file)
            except Exception as e:
                with log_lock, open(error_file, 'a', newline='', encoding='utf-8') as ef:
                    csv.writer(ef).writerow([oid, type(e).__name__, str(e)])

    print("Process completed.")