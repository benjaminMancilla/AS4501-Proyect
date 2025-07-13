import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold

df = pd.read_csv("tabular_data/baseline_data.csv", dtype={"oid": str})
oids  = df["oid"].values
labels= df["label"].values  # 'good'/'bad'

X_train_oids, X_test_oids, y_train, y_test = train_test_split(
    oids, labels,
    test_size=0.2,
    stratify=labels,
    random_state=42
)

folds_df = pd.DataFrame({"oid": oids})
folds_df["test"] = folds_df["oid"].isin(X_test_oids).astype(int)

n_folds = 5
skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

for i in range(1, n_folds+1):
    folds_df[f"train_fold{i}"] = 0
    folds_df[f"val_fold{i}"]   = 0

for fold_idx, (train_idx, val_idx) in enumerate(
        skf.split(X_train_oids, y_train), start=1):
    train_oids = X_train_oids[train_idx]
    val_oids   = X_train_oids[val_idx]
    folds_df.loc[
        folds_df["oid"].isin(train_oids),
        f"train_fold{fold_idx}"
    ] = 1
    folds_df.loc[
        folds_df["oid"].isin(val_oids),
        f"val_fold{fold_idx}"
    ] = 1

folds_df.to_csv("folds/stratified_folds.csv", index=False)
print("Folds estratificados guardados en stratified_folds.csv")
