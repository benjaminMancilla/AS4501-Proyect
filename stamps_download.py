from alerce.core import Alerce
import os
import glob
import pandas as pd
import ast
import gzip

detections_dir = 'alerce_lightcurves'
out_dir = 'alerce_stamps'
os.makedirs(out_dir, exist_ok=True)

alerce = Alerce()

for filepath in glob.glob(os.path.join(detections_dir, '*_detections.csv')):
    oid = os.path.basename(filepath).split('_')[0]
    df_lc = pd.read_csv(filepath, dtype=str)
    # Parse 
    try:
        detections_list = ast.literal_eval(df_lc.loc[0, 'detections'])
    except Exception:
        print(f"{oid}: can not parse detection, continue.")
        continue

    df_det = pd.DataFrame(detections_list)
    if df_det.empty:
        print(f"{oid}: no detections found, continue.")
        continue

    # Only keep detections with stamps
    df_det = df_det[df_det.get('has_stamp') == True]
    if df_det.empty:
        print(f"{oid}: no detections with stamps, continue.")
        continue

    for candid in df_det['candid'].unique():
        print(f"Downloading stamps for {oid}, candid={candid}...")
        try:
            # Download the stamps as HDUList
            hdulist = alerce.get_stamps(oid, candid=int(candid), format='HDUList')
            for ext, name in enumerate(['science','template','difference']):
                path = os.path.join(out_dir, f"{oid}_{candid}_{name}.fits")
                hdulist[ext].writeto(path, overwrite=True)
        except gzip.BadGzipFile:
            print(f" Candind {candid} for {oid} returned a bad gzip file, skipping.")
        except Exception as e:
            print(f"Error downloading stamps for {oid}, candid={candid}: {e}")


print("Process completed.")




