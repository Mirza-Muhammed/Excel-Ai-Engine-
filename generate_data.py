import pandas as pd
import numpy as np
from pathlib import Path
OUT = Path('data/synthetic_data.xlsx')
OUT.parent.mkdir(parents=True, exist_ok=True)
np.random.seed(42)
N = 1000
structured = pd.DataFrame({
    'ID': range(1, N+1),
    'Age': np.random.randint(20, 65, N),
    'Salary': np.random.randint(20000, 200000, N),
    'Department': np.random.choice(['HR','IT','Finance','Sales','Ops'], N),
    'JoinDate': pd.to_datetime('2017-01-01') + pd.to_timedelta(np.random.randint(0, 365*6, N), unit='D'),
    'PerformanceScore': np.random.randint(1, 11, N),
    'TenureMonths': np.random.randint(0, 120, N),
    'BonusPct': np.round(np.random.random(N)*0.2, 3),
    'Country': np.random.choice(['India','USA','UK','Germany','France'], N),
    'Projects': np.random.randint(0, 10, N)
})

texts = [f"Employee {i} had an experience with project {np.random.randint(1,20)}; performance was {'good' if np.random.rand()>0.3 else 'needs improvement'}." for i in range(1, N+1)]
unstructured = pd.DataFrame({
    'ID': range(1, N+1),
    'Feedback': texts,
    'Notes': [' '.join(np.random.choice(['stable','delayed','on-time','over-budget','exceeded expectations'], 5)) for _ in range(N)],
    'ManagerComment': ['Nice work' if np.random.rand()>0.6 else 'Needs improvement' for _ in range(N)],
    'SentimentHint': np.random.choice(['positive','neutral','negative'], N)
})

with pd.ExcelWriter(OUT, engine='openpyxl') as w:
    structured.to_excel(w, sheet_name='Structured', index=False)
    unstructured.to_excel(w, sheet_name='Unstructured', index=False)

print('Wrote', OUT)
