"""
Plot the ZTF light curve for a given OID from pre-downloaded CSVs.

Usage:
    python plot_lightcurve.py --oid ZTF23abcd1234 --lc-dir path/to/alerce_lightcurves
"""
import os
import glob
import argparse
import pandas as pd
import ast
import matplotlib.pyplot as plt


def plot_lightcurve(oid, lc_dir):
    # Construct expected CSV path
    pattern = os.path.join(lc_dir, f"{oid}_detections.csv")
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No detections CSV found for OID '{oid}' in '{lc_dir}'")
    csv_file = matches[0]

    # Read and parse the detections list
    df_raw = pd.read_csv(csv_file, dtype=str)
    raw_list = df_raw.loc[0, 'detections']
    detections = ast.literal_eval(raw_list)
    df_det = pd.DataFrame(detections)

    # Convert columns to numeric
    df_det['mjd'] = df_det['mjd'].astype(float)
    df_det['magpsf'] = df_det['magpsf'].astype(float)
    df_det['sigmapsf'] = df_det['sigmapsf'].astype(float)

    # Plot
    plt.figure()
    plt.errorbar(
        df_det['mjd'],
        df_det['magpsf'],
        yerr=df_det['sigmapsf'],
        fmt='o',
        capsize=3
    )
    plt.gca().invert_yaxis()
    plt.xlabel('MJD')
    plt.ylabel('PSF Magnitude')
    title_oid = os.path.basename(csv_file).replace('_detections.csv', '')
    plt.title(f'Lightcurve of {title_oid}')
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Plot ZTF light curve from local CSV for a given OID."
    )
    parser.add_argument(
        '--oid', required=True,
        help="ZTF object identifier (e.g. ZTF23abcd1234)"
    )
    parser.add_argument(
        '--lc-dir', default='alerce_lightcurves',
        help="Directory containing '*_detections.csv' files"
    )
    args = parser.parse_args()

    plot_lightcurve(args.oid, args.lc_dir)


if __name__ == '__main__':
    main()
