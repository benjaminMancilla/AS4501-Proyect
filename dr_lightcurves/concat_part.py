import os
import glob
import pandas as pd
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Concatena todos los CSV de DR de una parte en un solo archivo"  
    )
    parser.add_argument(
        '--part-dir', '-d', required=True,
        help="Directorio base de DR (ej. dr_lightcurves/part2)"
    )
    parser.add_argument(
        '--output', '-o', default='combined_dr.csv',
        help="Nombre del CSV de salida"
    )
    args = parser.parse_args()

    part_dir = args.part_dir
    pattern = os.path.join(part_dir, "*_dr.csv")
    files = glob.glob(pattern)
    if not files:
        print(f"No se encontraron archivos DR en {part_dir}")
        exit(1)

    df_list = []
    for fpath in files:
        try:
            df = pd.read_csv(fpath)
            # Asegurar columnas esperadas
            expected = ['hmjd','mag','magerr','ID','filterid','oid']
            if all(col in df.columns for col in expected):
                df_list.append(df[expected])
            else:
                print(f"Archivo {fpath} omite columnas faltantes, se ignora.")
        except Exception as e:
            print(f"Error leyendo {fpath}: {e}")

    if not df_list:
        print("Ningún CSV válido para concatenar.")
        exit(1)

    combined = pd.concat(df_list, ignore_index=True)
    combined.to_csv(args.output, index=False)
    print(f"CSV combinado guardado en: {args.output}")