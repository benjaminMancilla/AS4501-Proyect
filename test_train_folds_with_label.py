import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold

df = pd.read_csv("baseline_data_cleaned.csv", dtype={"oid": str})

oids = df["oid"].values
y    = df["label"].values  # 'good'/'bad'

folds = pd.DataFrame({"oid": oids})
folds["test"] = 0
n_folds = 5
for i in range(1, n_folds+1):
    folds[f"train_fold{i}"] = 0
    folds[f"val_fold{i}"]   = 0

# StratifiedKFold sobre los indices
skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
for fold_idx, (train_idx, val_idx) in enumerate(skf.split(oids, y), start=1):
    # Marcar
    folds.loc[train_idx, f"train_fold{fold_idx}"] = 1
    folds.loc[val_idx,   f"val_fold{fold_idx}"] = 1

folds.to_csv("stratified_folds.csv", index=False)
