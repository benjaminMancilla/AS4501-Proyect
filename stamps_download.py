from alerce.core import Alerce
import os
import pandas as pd

# Not working yet, is beter to download de lc an then the stamps

df = pd.read_csv('veto_summary.csv', dtype=str)
good_oids = df.loc[df['label']=='good', 'oid'].unique().tolist()

alerce = Alerce()

out_dir = 'alerce_stamps'
os.makedirs(out_dir, exist_ok=True)

for oid in good_oids:
    lc = alerce.query_lightcurve(oid, format='pandas')
    df_det = pd.DataFrame(lc['detections'])
    if df_det.empty:
        print(f"{oid}: sin detecciones → salto")
        continue

    print(df_det) 
    for candid in df_det['candid'].unique():
        print(f"Descargando stamps para {oid}, candid={candid} …")
        hdulist = alerce.get_stamps(oid, candid=int(candid), format='HDUList')
        for ext, name in enumerate(['science', 'template', 'difference']):
            filename = f"{oid}_{candid}_{name}.fits"
            path = os.path.join(out_dir, filename)
            hdulist[ext].writeto(path, overwrite=True)

print("All stamps saved in ", out_dir)

