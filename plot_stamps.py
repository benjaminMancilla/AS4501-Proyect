"""
Plot a single FITS stamp (science, template, difference) by index for a given ZTF OID.
Usage:
    python plot_stamps.py --oid ZTF23abcdefg --dir alerce_stamps --index 0
"""
import os
import glob
import argparse

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits


def plot_stamps(oid, stamps_dir='alerce_stamps', index=0):
    """
    Plot the stamp at position `index` for each of the three types
    (science, template, difference) for the given OID.
    """
    types = ['science', 'template', 'difference']
    files_for_type = {}
    for st_type in types:
        pattern = os.path.join(stamps_dir, f"{oid}_*_{st_type}.fits")
        matched = sorted(glob.glob(pattern))
        if not matched:
            print(f"[!] No files found for {st_type}")
            files_for_type[st_type] = None
        else:
            if index < 0 or index >= len(matched):
                print(f"[!] Index {index} out of range for {st_type} (0–{len(matched)-1})")
                files_for_type[st_type] = None
            else:
                files_for_type[st_type] = matched[index]

    # Prepare 1x3 grid
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, st_type in zip(axes, types):
        filepath = files_for_type.get(st_type)
        if filepath and os.path.exists(filepath):
            data = fits.getdata(filepath)
            vmin, vmax = np.percentile(data, [5, 99])
            ax.imshow(data, origin='lower', cmap='gray', vmin=vmin, vmax=vmax)
            ax.set_title(f"{st_type}\n{os.path.basename(filepath)}", fontsize=8)
        else:
            ax.text(0.5, 0.5, 'N/A', ha='center', va='center')
        ax.axis('off')

    plt.suptitle(f"{oid} stamps @ index {index}", fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot one stamp by index for each type for a ZTF OID")
    parser.add_argument('--oid',   required=True, help="ZTF object ID")
    parser.add_argument('--dir',   default='alerce_stamps', help="Folder with FITS stamps")
    parser.add_argument('--index', type=int, default=0, help="Which stamp index to plot (0-based)")
    args = parser.parse_args()

    plot_stamps(args.oid, stamps_dir=args.dir, index=args.index)

if __name__ == '__main__':
    main()
