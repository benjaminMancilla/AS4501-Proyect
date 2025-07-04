#!/usr/bin/env python3
"""
Plot FITS stamps (science/template/difference) for a given ZTF OID.
If --index is provided, plot only that stamp for each type; otherwise plot all stamps per type as separate grids.

Usage:
    python plot_stamps.py --oid ZTF23abcdefg --dir alerce_stamps [--index N]
"""
import os
import glob
import argparse

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits


def plot_stamps(oid, stamps_dir='alerce_stamps', index=None):
    types = ['science', 'template', 'difference']

    for st_type in types:
        pattern = os.path.join(stamps_dir, f"{oid}_*_{st_type}.fits")
        files = sorted(glob.glob(pattern))
        if not files:
            print(f"[!] No files found for {st_type}")
            continue

        # If index is None, plot all stamps in a grid; else plot single index
        if index is None:
            n = len(files)
            cols = min(5, n)
            rows = (n + cols - 1) // cols
            fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
            axes = axes.flatten()
            for ax, filepath in zip(axes, files):
                data = fits.getdata(filepath)
                vmin, vmax = np.percentile(data, [5, 99])
                ax.imshow(data, origin='lower', cmap='gray', vmin=vmin, vmax=vmax)
                ax.set_title(os.path.basename(filepath), fontsize=8)
                ax.axis('off')
            # disable extra
            for ax in axes[len(files):]:
                ax.axis('off')
            plt.suptitle(f"{oid} — all {st_type}", fontsize=14)
            plt.tight_layout(rect=[0,0,1,0.95])
            plt.show()
        else:
            if index < 0 or index >= len(files):
                print(f"[!] Index {index} out of range for {st_type} (0–{len(files)-1})")
                continue
            filepath = files[index]
            data = fits.getdata(filepath)
            vmin, vmax = np.percentile(data, [5, 99])
            fig, ax = plt.subplots(1, 1, figsize=(6, 6))
            ax.imshow(data, origin='lower', cmap='gray', vmin=vmin, vmax=vmax)
            ax.set_title(f"{st_type}\n{os.path.basename(filepath)}", fontsize=10)
            ax.axis('off')
            plt.suptitle(f"{oid} — {st_type} @ index {index}", fontsize=14)
            plt.tight_layout(rect=[0,0,1,0.95])
            plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Plot FITS stamps for a ZTF OID; all if no index, or one by index."
    )
    parser.add_argument(
        '--oid', required=True, help="ZTF object ID (e.g. ZTF23abcd...)")
    parser.add_argument(
        '--dir', dest='stamps_dir', default='alerce_stamps',
        help="Folder with FITS stamps"
    )
    parser.add_argument(
        '--index', type=int, default=None,
        help="Which stamp index to plot (0-based). If omitted, plots all."
    )
    args = parser.parse_args()

    plot_stamps(args.oid, stamps_dir=args.stamps_dir, index=args.index)

if __name__ == '__main__':
    main()

