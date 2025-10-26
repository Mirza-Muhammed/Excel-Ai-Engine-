import pandas as pd
from typing import Dict

def read_excel_sheets(path: str) -> Dict[str, pd.DataFrame]:
    x = pd.read_excel(path, sheet_name=None, engine='openpyxl')
    return x

def write_sheets_to_file(sheets: Dict[str, pd.DataFrame], path: str):
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=str(name)[:31], index=False)

def execute_operation_on_sheet(df: pd.DataFrame, op: dict) -> pd.DataFrame:
    t = op.get('type')
    if t == 'math':
        a, b = op['columns'][:2]
        if op['op'] == '+':
            df[op['new_column']] = df[a] + df[b]
        elif op['op'] == '-':
            df[op['new_column']] = df[a] - df[b]
        elif op['op'] == '*':
            df[op['new_column']] = df[a] * df[b]
        elif op['op'] == '/':
            df[op['new_column']] = df[a] / df[b]
        return df

    if t == 'aggregation':
        if op.get('method') == 'groupby_agg':
            gb = df.groupby(op['groupby']).agg(op['agg']).reset_index()
            return gb
        if op.get('method') == 'summary':
            res = {c: getattr(df[c], op['agg'])() for c in op['columns']}
            return pd.DataFrame([res])

    if t == 'filter':
        out = df.query(op['expr'])
        return out

    if t == 'pivot':
        pv = pd.pivot_table(df, index=op['index'], columns=op['columns'], values=op['values'], aggfunc=op.get('aggfunc','sum')).reset_index()
        if hasattr(pv.columns, 'names'):
            pv.columns = ["_".join([str(x) for x in col if x is not None]).strip() for col in pv.columns.values]
        return pv

    if t == 'unpivot':
        melted = df.melt(id_vars=op['id_vars'], value_vars=op['value_vars'], var_name=op.get('var_name','variable'), value_name=op.get('value_name','value'))
        return melted

    if t == 'date_extract':
        col = op['column']
        part = op['part']
        s = pd.to_datetime(df[col], errors='coerce')
        if part == 'month':
            df[op['new_column']] = s.dt.month
        elif part == 'year':
            df[op['new_column']] = s.dt.year
        elif part == 'day':
            df[op['new_column']] = s.dt.day
        return df

    if t == 'sql_like':
        return df.query(op['expr'])

    raise ValueError(f"Unsupported operation type: {t}")
