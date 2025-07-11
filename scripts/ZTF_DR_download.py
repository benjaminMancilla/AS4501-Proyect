import os
import csv
import pandas as pd
import numpy as np
import requests
import argparse
import time
import json

# Auxiliary function for removing oids from the error log
def remove_from_error_log(target_oid):
    rows = []
    if os.path.exists(error_file):
        with open(error_file, newline='', encoding='utf-8') as ef:
            reader = csv.DictReader(ef)
            rows = [row for row in reader if row['oid'] != target_oid]
        with open(error_file, 'w', newline='', encoding='utf-8') as ef:
            writer = csv.DictWriter(ef, fieldnames=['oid', 'error_type', 'message'])
            writer.writeheader()
            writer.writerows(rows)

# Function to download the DR lightcurve given oid, ra, dec
def get_DR(oid, ra, dec, url="https://api.alerce.online/ztf/dr/v1/light_curve/"):
    query = {'ra': ra, 'dec': dec, 'radius': 1.5}
    response = requests.get(url, params=query)
    response.raise_for_status()
    output = response.json()

    dfs = []
    for i in output:
        aux = pd.DataFrame({
            'hmjd': np.array(i['hmjd']),
            'mag': np.array(i['mag']),
            'magerr': np.array(i['magerr'])
        })
        aux['ID'] = int(i['_id'])
        aux['filterid'] = int(i['filterid'])
        aux['oid'] = oid
        dfs.append(aux)

    df = pd.concat(dfs, ignore_index=True) if dfs else None
    return df, output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Download DR lightcurves with logging, resume, partitioning, and test mode."
    )
    parser.add_argument('--resume', action='store_true', help='Skip oids already processed in logs.')
    parser.add_argument('--retry-errors', action='store_true', help='Retry downloading oids that previously failed.')
    parser.add_argument('--part', type=int, choices=[1, 2, 3], help='Download only this third of oids.')
    parser.add_argument('--test-oid', type=str, help='If provided, download only this single oid.')
    args = parser.parse_args()

    # File paths and directories
    summary_csv = 'oids_ra_dec.csv'
    part_label = f"part{args.part}" if args.part else 'all'
    logs_dir = os.path.join('logs', 'dr', part_label)
    success_file = os.path.join(logs_dir, 'success.csv')
    error_file = os.path.join(logs_dir, 'errors.csv')
    out_dir = os.path.join('dr_lightcurves', part_label)

    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    # Initialize log files
    if not os.path.exists(success_file):
        with open(success_file, 'w', newline='', encoding='utf-8') as sf:
            csv.writer(sf).writerow(['oid'])
    if not os.path.exists(error_file):
        with open(error_file, 'w', newline='', encoding='utf-8') as ef:
            csv.writer(ef).writerow(['oid', 'error_type', 'message'])

    # Load oids, ra, dec
    df = pd.read_csv(summary_csv, dtype={'oid': str, 'ra': float, 'dec': float})
    records = df.to_dict('records')

    if args.retry_errors:
        with open(error_file, newline='', encoding='utf-8') as ef:
            reader = csv.DictReader(ef)
            error_oids = {row['oid'] for row in reader}
        records = [r for r in records if r['oid'] in error_oids]
    elif args.test_oid:
        records = [r for r in records if r['oid'] == args.test_oid]
    else:
        if args.resume:
            processed = set()
            with open(success_file, newline='', encoding='utf-8') as sf:
                next(sf)
                for row in csv.reader(sf):
                    processed.add(row[0])
            with open(error_file, newline='', encoding='utf-8') as ef:
                next(ef)
                for row in csv.reader(ef):
                    processed.add(row[0])
            records = [r for r in records if r['oid'] not in processed]

    # Partitioning 
    if args.part and not args.retry_errors and not args.test_oid:
        total   = len(records)
        block   = total // 3
        start   = block * (args.part - 1)
        # for part 3, include any remainder
        end     = block * args.part if args.part < 3 else total
        records = records[start:end]
        print(f"Downloading part {args.part} with {len(records)} records.")
        print(f"Processing records from {start} to {end} of total {total}.")

    # Download loop
    for rec in records:
        oid = rec['oid']
        ra = rec['ra']
        dec = rec['dec']
        try:
            lc, raw_json = get_DR(oid, ra, dec)
            if lc is not None:
                lc.to_csv(os.path.join(out_dir, f"{oid}_dr.csv"), index=False)

            # In test mode, also save raw JSON
            if args.test_oid:
                json_path = os.path.join(out_dir, f"{oid}_dr.json")
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump(raw_json, jf, ensure_ascii=False, indent=2)

            # Log success
            with open(success_file, 'a', newline='', encoding='utf-8') as sf:
                csv.writer(sf).writerow([oid])

            if args.retry_errors:
                remove_from_error_log(oid)

            print(f"[+] Successfully downloaded {oid}")

        except requests.exceptions.RequestException as http_err:
            with open(error_file, 'a', newline='', encoding='utf-8') as ef:
                csv.writer(ef).writerow([oid, type(http_err).__name__, str(http_err)])
        except Exception as err:
            with open(error_file, 'a', newline='', encoding='utf-8') as ef:
                csv.writer(ef).writerow([oid, type(err).__name__, str(err)])

    print("Process completed.")