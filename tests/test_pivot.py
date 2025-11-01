# tests/test_pivot.py
import pandas as pd
from app.services.pivot_engine import create_pivot, unpivot

def test_pivot_unpivot():
    df = pd.DataFrame({
        "Region":["A","A","B"],
        "Product":["p1","p2","p1"],
        "Sales":[10,20,5]
    })
    pivot = create_pivot(df, index=["Region"], columns=["Product"], values="Sales", aggfunc="sum")
    assert "Region" in pivot.columns
    unp = unpivot(pivot, id_vars=["Region"], value_vars=[c for c in pivot.columns if c!="Region"])
    assert "variable" in unp.columns
