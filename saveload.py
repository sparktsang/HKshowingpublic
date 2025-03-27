# 此為以json、pickle形式存取檔案相關函式之模組庫
import json, os, re, pickle
from datetime import datetime

def loadjson(fn):
    with open(fn, "rb") as f: d = json.load(f)
    return d

def loadpickle(fn):
    with open(fn, 'rb') as f: d = pickle.load(f)
    return d

def loadtxt(fn):
    with open(fn, encoding="utf-8") as f: s = f.read()
    return s

def savejson(fn, d):
    with open(fn, 'w') as f: json.dump(d, f, indent=4)

def savepickle(fn, d):
    with open(fn, 'wb') as f: pickle.dump(d, f)
    
def load(fn):
    fname, fe = os.path.splitext(fn) # 檔名與副檔名
    if fe == '.json': return loadjson(fn)
    elif fe == '.pkl': return loadpickle(fn)
    elif fe == '.txt': return loadtxt(fn)
    else: raise Exception('此檔案非 json、pickle或txt')

def loadelsedef(fn, d={}): # 倘有檔案則開檔案，無檔案則賦值
    if os.path.isfile(fn): return load(fn)
    else: return d

def save(fn, d):
    fname, fe = os.path.splitext(fn) # 檔名與副檔名
    if fe == '.json': savejson(fn, d)
    elif fe == '.pkl': savepickle(fn, d)
    else: raise Exception('此檔案非 json 或 pickle')

def allfn(a):
    file_list = []
    fn, fs = os.path.splitext(a)
    ff = fn + r' ([0-9]{4}(?:[-.][0-9]{2}){2})' + fs
    pattern = re.compile(ff)
    for root, dirs, files in os.walk("."):
        for f in files:
            if pattern.match(f):
                file_list.append(f)
    return file_list

def latestfn(a):
    files = allfn(a)
    
    def extract_date(fname):
        # 從檔名中提取日期字串
        m = re.search(r'\d{4}(?:[-.]\d{2}){2}', fname)
        if m:
            # 統一使用 '-' 作分隔符，方便轉換為 datetime 物件
            date_str = m.group(0).replace('.', '-')  
            return datetime.strptime(date_str, '%Y-%m-%d')
        return datetime.min

    if files:
        sorted_files = sorted(files, key=extract_date)
        return sorted_files[-1]  # 最新檔案
    else:
        return None

def today(): from datetime import date; return date.today()

# 將一串列的表格，加入格式輸出成同一檔案中的試算表
import pandas as pd
def export_xlsx(file, dfs, sheetns, width, fontsize, twodg, hidecol, font='CALIBRI', f={'align': 'center', 'valign': 'vcenter'}):
    W = pd.ExcelWriter(file, engine='xlsxwriter') # file為檔名
    for i, df in enumerate(dfs): df.to_excel(W, sheet_name=sheetns[i]) # sheetns為表格的對應工作表名稱的串列
    
    coln = len(df.columns) + 1; zero = [0] * coln
    def hotkeys(l):
        r = zero.copy()
        for i in l: r[i] = 1
        return r
    if isinstance(width, int): width = [width] * coln
    if isinstance(fontsize, int): fontsize = [fontsize] * coln
    if twodg is None: twodg = zero
    elif len(twodg) != coln: twodg = hotkeys(twodg)
    if hidecol is None: hidecol = zero
    elif len(hidecol) != coln: hidecol = hotkeys(hidecol)
    
    wb = W.book
    f.update({'font_name': font}) # font是整個表的字體名稱
    for sheetn in sheetns: 
        ws = W.sheets[sheetn]
        for i in range(coln): # 加上沒被計算的索引欄 
            F = {**f, **{'font_size': fontsize[i]}} # fontsize為表示各欄字體大小的數字串列
            if twodg[i] == 1: F.update({'num_format': '0.00_);(0.00)'}) # twodg為表示各欄要否轉成兩個小數點的0, 1串列
            ws.set_column(i, i, width[i], wb.add_format(F), {'hidden': hidecol[i]}) # width為表示各欄闊度的數字串列，hidecol為表示各欄要否隱藏的0, 1串列
    W.close()