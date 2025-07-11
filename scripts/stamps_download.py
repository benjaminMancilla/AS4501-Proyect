import os
import glob
import csv
import argparse
import pandas as pd
import ast
import gzip
from alerce.core import Alerce

# Argument parser
def parse_args():
    p = argparse.ArgumentParser(description="Download stamps for good or bad OIDs with logging and resume.")
    p.add_argument('--type', choices=['good','bad'], default='good',
                   help="Process 'good' or 'bad' OIDs")
    p.add_argument('--continue', dest='resume', action='store_true',
                   help="Skip OIDs already processed")
    p.add_argument('--lc-dir', default='alerce_lightcurves',
                   help="Directory containing detection CSVs")
    p.add_argument('--out-dir', default='alerce_stamps',
                   help="Base output directory for FITS stamps")
    return p.parse_args()

# Initialize
args = parse_args()
logs_dir = os.path.join('logs', 'stamps', args.type)
success_csv = os.path.join(logs_dir, 'success.csv')
error_csv   = os.path.join(logs_dir, 'errors.csv')
output_dir  = os.path.join(args.out_dir, args.type)

os.makedirs(logs_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# Initialize log files if missing
if not os.path.exists(success_csv):
    with open(success_csv, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(['oid','candid'])
if not os.path.exists(error_csv):
    with open(error_csv, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(['oid','candid','error_type','message'])

# Load summary and filter OIDs by type
df = pd.read_csv('veto_summary.csv', dtype=str)
if args.type == 'good':
    oids = df.loc[df['label']=='good','oid'].unique().tolist()
else:
    oids = df.loc[df['label']=='bad','oid'].unique().tolist()

# If resume, remove processed
if args.resume:
    processed = set()
    for log in (success_csv, error_csv):
        with open(log, newline='', encoding='utf-8') as f:
            reader = csv.reader(f); next(reader)
            for row in reader: processed.add((row[0], row[1] if len(row)>1 else None))

# ALeRCE client
alerce = Alerce()

# Loop over OIDs
for oid in oids:
    # find CSV
    csv_path = os.path.join(args.lc_dir, args.type, f"{oid}_detections.csv")
    if not os.path.exists(csv_path):
        print(f"[ERROR] No detections CSV for {oid}, logging error and continuing.")
        with open(error_csv, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([oid, '', 'NoCSV', 'Detections CSV not found'])
        continue
    df_lc = pd.read_csv(csv_path, dtype=str)
    # parse detections list
    try:
        det_list = ast.literal_eval(df_lc.loc[0,'detections'])
    except Exception:
        print(f"[WARN] {oid}: parse error, skipping.")
        continue
    df_det = pd.DataFrame(det_list)
    df_det = df_det[df_det.get('has_stamp') == True]

    for candid in df_det['candid'].unique():
        key = (oid, candid)
        if args.resume and key in processed:
            continue
        try:
            hdulist = alerce.get_stamps(oid, candid=int(candid), format='HDUList')
            for ext, name in enumerate(['science','template','difference']):
                out_path = os.path.join(output_dir, f"{oid}_{candid}_{name}.fits")
                hdulist[ext].writeto(out_path, overwrite=True)
            # log success
            with open(success_csv, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([oid, candid])
        except gzip.BadGzipFile:
            # log error
            with open(error_csv, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([oid, candid, 'BadGzipFile', 'Not a gzipped FITS'])
        except Exception as e:
            with open(error_csv, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([oid, candid, type(e).__name__, str(e)])

print(f"Done processing {args.type} stamps. Output in {output_dir}")





