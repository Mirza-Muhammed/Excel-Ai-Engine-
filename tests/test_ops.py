import pandas as pd
from app.services.excel_ops import execute_operation_on_sheet

def test_math_add():
    df = pd.DataFrame({'a':[1,2,3],'b':[10,20,30]})
    op = {'type':'math','op':'+','columns':['a','b'],'new_column':'a_plus_b'}
    out = execute_operation_on_sheet(df, op)
    assert 'a_plus_b' in out.columns
    assert out['a_plus_b'].tolist() == [11,22,33]

def test_groupby_mean():
    df = pd.DataFrame({'dept':['x','x','y'],'salary':[10,30,20]})
    op = {'type':'aggregation','method':'groupby_agg','groupby':['dept'],'agg':{'salary':'mean'}}
    out = execute_operation_on_sheet(df, op)
    assert 'salary' in out.columns
    assert set(out['dept'].tolist()) == {'x','y'}
