import pandas as pd
from sklearn.model_selection import train_test_split, KFold

# Version de test_train_folds.py adaptada para incluir etiquetas
df = pd.read_csv(
    "baseline_data_cleaned.csv",
    dtype={"oid": str},
    parse_dates=["veto_date"]
)

oids = df["oid"].values
labels = df["label"].values
X_train_oids, X_test_oids = train_test_split(
    oids,
    test_size=0.2,
    stratify=labels,
    random_state=42
)

folds_df = pd.DataFrame({"oid": oids})
folds_df["test"] = folds_df["oid"].isin(X_test_oids).astype(int)

n_folds = 5
kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)

for i in range(1, n_folds+1):
    folds_df[f"train_fold{i}"] = 0
    folds_df[f"val_fold{i}"]   = 0

for fold_idx, (train_idx, val_idx) in enumerate(
        kf.split(X_train_oids), start=1):
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

folds_df.to_csv("stratified_folds.csv", index=False)
print("Folds guardados en stratified_folds.csv")
