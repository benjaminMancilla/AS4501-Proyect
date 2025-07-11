import pandas as pd


sheets = pd.read_excel(
    'VETOS/Vetoes2.xlsx',
    sheet_name=None,      
    header=1,                
    dtype=str,
    usecols=lambda c: c in ['oid','AM','FB','FF','GP','pipeline'],
    na_filter=False,
    parse_dates=False,
    engine='openpyxl'
)

dfs = []
for name, df in sheets.items():
    if name.lower() == 'satellites':
        continue
    for col in ['oid','AM','FB','FF','GP','pipeline']:
        if col not in df.columns:
            df[col] = ""        
    df = df[['oid','AM','FB','FF','GP','pipeline']]
    df['date'] = name
    dfs.append(df)

vetoes_df = pd.concat(dfs, ignore_index=True)
vetoes_df.to_csv('vetoes2.csv', index=False)









