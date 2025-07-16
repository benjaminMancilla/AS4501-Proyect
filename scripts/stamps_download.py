import os
import csv
import argparse
import pandas as pd
import ast
import gzip
from alerce.core import Alerce

# Argument parser
def parse_args():
    p = argparse.ArgumentParser(
        description="Download stamps for good or bad OIDs with logging, resume, and retry.")
    p.add_argument('--type', choices=['good','bad'], default='good',
                   help="Process 'good' or 'bad' OIDs")
    p.add_argument('--continue', dest='resume', action='store_true',
                   help="Skip OIDs already processed")
    p.add_argument('--retry', action='store_true',
                   help="Retry OIDs that previously failed due to missing CSV")
    p.add_argument('--retry-csv', default=None,
                   help="Path to master detections CSV for retry (--retry)")
    p.add_argument('--lc-dir', default='alerce_lightcurves_alerts',
                   help="Directory containing detection CSVs")
    p.add_argument('--out-dir', default='alerce_stamps',
                   help="Base output directory for FITS stamps")
    return p.parse_args()

# Main logic
def main():
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

    # Retry mode: handle missing-CSV errors
    if args.retry:
        if not args.retry_csv:
            print("[ERROR] --retry requires --retry-csv <path>")
            return
        # Read error log and get missing OIDs
        err_df = pd.read_csv(error_csv, dtype=str)
        missing = err_df.loc[err_df['error_type']=='NoCSV', 'oid'].str.strip().unique().tolist()
        if not missing:
            print("No 'Detections CSV not found' errors to retry.")
            return
        # Prepare ALeRCE client
        alerce = Alerce()
        new_errors = []
        new_success = []
        # Process each missing oid in chunks to handle large CSV
        for oid in missing:
            found = False
            # iterate through master CSV in chunks
            for chunk in pd.read_csv(args.retry_csv, dtype=str, chunksize=100000):
                # clean and filter
                chunk['oid'] = chunk['oid'].str.strip()
                df_subset = chunk.loc[chunk['oid']==oid]
                if not df_subset.empty:
                    found = True
                # process any rows in this chunk
                for _, row in df_subset.iterrows():
                    candid = str(row['candid']).strip()
                    try:
                        hdulist = alerce.get_stamps(oid, candid=int(candid), format='HDUList')
                        for ext, name in enumerate(['science','template','difference']):
                            out_path = os.path.join(output_dir, f"{oid}_{candid}_{name}.fits")
                            hdulist[ext].writeto(out_path, overwrite=True)
                        new_success.append({'oid': oid, 'candid': candid})
                    except gzip.BadGzipFile:
                        new_errors.append({'oid':oid, 'candid':candid,
                                           'error_type':'BadGzipFile',
                                           'message':'Not a gzipped FITS'})
                    except Exception as e:
                        new_errors.append({'oid':oid, 'candid':candid,
                                           'error_type': type(e).__name__,
                                           'message': str(e)})
            if not found:
                print(f"[WARN] {oid} not found in {args.retry_csv}, leaving error logged.")
            else:
                # remove previous NoCSV entries
                err_df = err_df[~((err_df['oid']==oid)&(err_df['error_type']=='NoCSV'))]
        # update logs
        err_df = pd.concat([err_df, pd.DataFrame(new_errors)], ignore_index=True)
        err_df.to_csv(error_csv, index=False)
        succ_df = pd.read_csv(success_csv, dtype=str)
        succ_df = pd.concat([succ_df, pd.DataFrame(new_success)], ignore_index=True)
        succ_df.to_csv(success_csv, index=False)
        print("Retry complete. Logs updated.")
        return

    # Normal mode: load summary and process
    df = pd.read_csv('veto_summary.csv', dtype=str)
    oids = df.loc[df['label']==args.type, 'oid'].str.strip().unique().tolist()

    processed = set()
    if args.resume:
        for log in (success_csv, error_csv):
            with open(log, newline='', encoding='utf-8') as f:
                reader = csv.reader(f); next(reader)
                for row in reader:
                    processed.add((row[0].strip(), row[1].strip() if len(row)>1 else None))

    alerce = Alerce()
    # Loop over OIDs
    for oid in oids:
        csv_path = os.path.join(args.lc_dir, args.type, f"{oid}_detections.csv")
        if not os.path.exists(csv_path):
            print(f"[ERROR] No detections CSV for {oid}, logging error and continuing.")
            with open(error_csv, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([oid, '', 'NoCSV', 'Detections CSV not found'])
            continue
        df_lc = pd.read_csv(csv_path, dtype=str)
        try:
            det_list = ast.literal_eval(df_lc.loc[0,'detections'])
        except Exception:
            print(f"[WARN] {oid}: parse error, skipping.")
            continue
        df_det = pd.DataFrame(det_list)
        df_det = df_det[df_det.get('has_stamp') == True]

        for candid in df_det['candid'].astype(str).unique():
            key = (oid, candid)
            if args.resume and key in processed:
                continue
            try:
                hdulist = alerce.get_stamps(oid, candid=int(candid), format='HDUList')
                for ext, name in enumerate(['science','template','difference']):
                    out_path = os.path.join(output_dir, f"{oid}_{candid}_{name}.fits")
                    hdulist[ext].writeto(out_path, overwrite=True)
                with open(success_csv, 'a', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow([oid, candid])
            except gzip.BadGzipFile:
                with open(error_csv, 'a', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow([oid, candid, 'BadGzipFile', 'Not a gzipped FITS'])
            except Exception as e:
                with open(error_csv, 'a', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow([oid, candid, type(e).__name__, str(e)])

    print(f"Done processing {args.type} stamps. Output in {output_dir}")

if __name__ == "__main__":
    main()