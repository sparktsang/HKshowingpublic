import numpy as np, pandas as pd

def getcol(df, a): return df.columns.get_loc(a) # 欄名a位於表格第幾欄，首欄為第零欄

def movecol(df, a, b): # 將表格中之A欄移至B欄之前
    df.insert(getcol(df, b), a, df.pop(a))
    
def applyfunc(df, f, arg): # 本式於表格中，根據既有欄目，用公式創造新欄，一欄多欄皆可：f為要應用之函式，arg為函式內的數值所屬欄目
    return df.apply(lambda r: f(*[r[i] for i in arg]), axis=1, result_type='expand')

def pct2f(x): # 可將百分比轉為浮點
    if isinstance(x, str) and '%' in x: return float(x.rstrip('%')) / 100
    elif x != x: return np.nan
    else: 
        try: return float(x)
        except ValueError: return x # 用於全表格之法：df = df.applymap(pct2f)
        
def twocol2d(df, a, b): # 從表格中取出a, b兩欄，製作出字典，鍵為a欄資料，值為b欄的對應數
    return df[[a, b]].set_index(a).to_dict()[b]

def d2twocol(d, a, b): # 上式之相反，a及b為欄目名稱
    return pd.DataFrame(d.items(), columns=([a, b]))
