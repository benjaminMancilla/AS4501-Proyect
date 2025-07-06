
from sklearn.model_selection import train_test_split, KFold
import pandas as pd

# Particion: separando en datos de test, train y validation
df_obj = pd.read_csv('oids_ra_dec.csv') 
X = df_obj['oid'].values
X_train, X_test = train_test_split(X, random_state=42)

# DF para guardar folds y test
df = pd.DataFrame({'oid': X})
df['test'] = df['oid'].isin(X_test).astype(int)

# Número de folds para train/validation
n_folds = 5
kf = KFold(n_splits=n_folds,shuffle=True, random_state=42)

# Columnas para los folds
for i in range(n_folds): # empiezan con valor 0
    df[f'train_fold{i+1}'] = 0
    df[f'val_fold{i+1}'] = 0

# Haciendo KFolds y agregando 1 cuando está en el fold como train o validation
for fold, (train_idx, val_idx) in enumerate(kf.split(X_train)):
    train_oids = X_train[train_idx]
    val_oids = X_train[val_idx]  

    df.loc[df['oid'].isin(train_oids), f'train_fold{fold+1}'] = 1
    df.loc[df['oid'].isin(val_oids), f'val_fold{fold+1}'] = 1   

df.to_csv('test_train_folds.csv')