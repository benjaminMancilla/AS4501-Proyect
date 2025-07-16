import os
import re
import numpy as np
import pandas as pd
from astropy.io import fits

# Carga robusta de un FITS a array numpy
# y guarda como .npy para memmap

def load_and_save_fits(path, out_dir, oid, candid, stamp_type):
    """
    Carga el primer HDU con datos y guarda como .npy en out_dir.
    Devuelve la ruta al .npy creado, o None si falla.
    """
    try:
        with fits.open(path, memmap=True) as hdulist:
            for hdu in hdulist:
                data = hdu.data
                if data is not None:
                    arr = data.astype(np.float32)
                    # asegura directorio
                    os.makedirs(out_dir, exist_ok=True)
                    fname = f"{oid}_{candid}_{stamp_type}.npy"
                    fpath = os.path.join(out_dir, fname)
                    # guardar con numpy.save
                    np.save(fpath, arr)
                    return fpath
    except Exception as e:
        print(f"[WARN] no pude procesar {path}: {e}")
    return None

# Construcción del DataFrame maestro de stamps con rutas a .npy

def build_stamps_index(root_dir='alerce_stamps', out_dir='stamps_arrays'):
    records = []
    pattern = re.compile(r'^(?P<oid>[^_]+)_(?P<candid>\d+)_(?P<type>difference|science|template)\.fits$')

    for label in ['good', 'bad']:
        folder = os.path.join(root_dir, label)
        if not os.path.isdir(folder):
            print(f"[WARN] Carpeta no encontrada: {folder}, saltando.")
            continue
        print(f"[INFO] Procesando carpeta: {folder}")

        by_obs = {}
        for fname in os.listdir(folder):
            m = pattern.match(fname)
            if not m:
                continue
            oid = m.group('oid')
            candid = m.group('candid')
            itype = m.group('type')
            key = (oid, candid, label)
            by_obs.setdefault(key, {})[itype] = os.path.join(folder, fname)

        print(f"[INFO] Encontradas {len(by_obs)} observaciones en {folder}.")
        counter = 0
        for (oid, candid, lbl), paths in by_obs.items():
            row = {
                'oid': oid,
                'candid': candid,
                'difference': None,
                'science': None,
                'template': None,
                'label': lbl
            }
            for t in ['difference', 'science', 'template']:
                fits_path = paths.get(t)
                if fits_path:
                    npy_path = load_and_save_fits(
                        fits_path,
                        out_dir=os.path.join(out_dir, label),
                        oid=oid,
                        candid=candid,
                        stamp_type=t
                    )
                    row[t] = npy_path
            records.append(row)
            counter += 1
            if counter % 100 == 0:
                print(f"[INFO] Procesadas {counter} observaciones...")

    df = pd.DataFrame(records, columns=['oid','candid','difference','science','template','label'])
    return df

# Script principal

def main():
    # build index and save small pickle
    df_index = build_stamps_index(root_dir='alerce_stamps', out_dir='stamps_arrays')

    pkl_path = 'stamps_master_index.pkl'
    print(f"[INFO] Guardando índice en {pkl_path}...")
    df_index.to_pickle(pkl_path)

    print("Listo. Ahora tienes un pickle ligero con rutas .npy; carga con pandas y usa np.load(mmap_mode='r') para cada stamp.")

if __name__ == "__main__":
    main()