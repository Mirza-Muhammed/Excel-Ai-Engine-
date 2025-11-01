# tests/test_math.py
import pandas as pd
from app.services.math_operations import apply_math, aggregate

def test_apply_add_const():
    df = pd.DataFrame({"a":[1,2,3]})
    out = apply_math(df, "add", ["a"], new_col="a_plus_5", operand=5)
    assert "a_plus_5" in out.columns
    assert out["a_plus_5"].tolist() == [6,7,8]

def test_aggregate_sum():
    df = pd.DataFrame({"region":["x","x","y"], "val":[1,2,3]})
    res = aggregate(df, "val", "sum", group_by=["region"])
    assert res["x"] == 3
    assert res["y"] == 3
