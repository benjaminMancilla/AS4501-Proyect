import glob
import pandas as pd
import ast
import matplotlib.pyplot as plt

csv_files = glob.glob('alerce_lightcurves/*.csv')
if not csv_files:
    raise FileNotFoundError("No se encontraron archivos CSV en 'alerce_lightcurves/'.")

csv_file = csv_files[6]
df_csv = pd.read_csv(csv_file, dtype=str)

raw = df_csv.loc[0, 'detections']
detections_list = ast.literal_eval(raw)

df_det = pd.DataFrame(detections_list)
df_det['mjd'] = df_det['mjd'].astype(float)
df_det['magpsf'] = df_det['magpsf'].astype(float)
df_det['sigmapsf'] = df_det['sigmapsf'].astype(float)

plt.figure()
plt.errorbar(df_det['mjd'], df_det['magpsf'], yerr=df_det['sigmapsf'], fmt='o', capsize=3)
plt.gca().invert_yaxis()
plt.xlabel('MJD')
plt.ylabel('PSF Magnitude')
plt.title(f'Lightcurve: {csv_file.split("/")[-1].replace(".csv","")}')
plt.tight_layout()
plt.show()