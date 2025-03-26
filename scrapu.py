# 此為擷取相關函式之模組庫
import calendar, numpy as np, pandas as pd, re, requests, time
from datetime import datetime
from bs4 import BeautifulSoup; from selenium import webdriver
ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
from selenium.webdriver.chrome.service import Service # https://stackoverflow.com/questions/76550506
service = Service(executable_path=r'C:\Users\user\Downloads\chromedriver-win64\chromedriver.exe') 
from selenium.webdriver.chrome.options import Options
from saveload import loadelsedef, save
from dfu import twocol2d, d2twocol
options = Options()
options.add_argument("--headless=new")
# 若遇極難問題，有擷取網頁之收費服務可參考：https://www.zenrows.com/

def urlsoup(u): # 一般方法擷取網頁內容
    while 1: 
        try: r = requests.get(u, headers={'User-Agent': ua}, timeout=10); break
        except requests.exceptions.Timeout: print('重新擷取')
    return BeautifulSoup(r.text, "html.parser")

def urlsouptit(u, h): # 一直嘗試直至擷取正確網頁內容
    while 1:
        s = urlsoup(u)
        tit = s.title.text
        print(f'目前網頁標題：{tit}')
        if h in tit: break
    return s

headless = 1
def urlsoupsel(url, iden='MacroTrends'): # 無法以上式擷取，因被截僅得「just a moment...」之頁面時，用selenium擷取
    global headless
    i = 1
    while 1: # iden為網頁標題中有的辨識詞，判斷頁面有效否
        if headless == 1:
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(60)
            driver.get(url)
            print(f'Headless狀態：{headless}；目前網頁標題：{driver.title}')
            if iden in driver.title: break
            driver.close()
            headless = 0 # 放棄嘗試headless
            time.sleep(3)
        driver = webdriver.Chrome(service=service)
        driver.set_page_load_timeout(60)
        driver.get(url)
        print(f'目前網頁標題：{driver.title}')
        if iden in driver.title: break # 若為「請稍候」之頁面，則稍候重來
        driver.close()
        if i % 3 == 0: time.sleep(60)
        elif i % 10 == 0: time.sleep(120)
        else: time.sleep(15)
        i += 1
    html = driver.page_source
    driver.quit()
    return BeautifulSoup(html,'html.parser') # 參: https://stackoverflow.com/questions/74022759

import cloudscraper # 跳過Cloudfare封鎖之擷取手段，參:https://stackoverflow.com/questions/49087990
def urlsoupcloudscr(url, iden='MacroTrends'): 
    i = 1
    while 1: 
        scraper = cloudscraper.create_scraper()
        html = scraper.get(url).text
        s = BeautifulSoup(html, 'html.parser')
        tit = s.title.text
        print(f'目前網頁標題：{tit}')
        if iden in tit: break
        if i % 3 == 0: time.sleep(60)
        elif i % 10 == 0: time.sleep(120)
        else: time.sleep(15)
        i += 1
    return s

normd = {'-': ' ', 'the ': '', ',': '', ':': '', "'": '', '"': ''}
def mulreplace(t, d=normd):
    for i, j in d.items(): t = t.replace(i, j)
    return t

def tablerow(soup, string='', col=None, subst=None): # 於已擷取網頁資料中勾出表格
    R = []
    for tr in soup.select('tr'): # soup從網址可如此擷取而得：urlsoup(url)
        r = [td.text for td in tr.select('td, th') if td.text]
        if r == []: continue
        if col != None: 
            if isinstance(col, int): # col為包括索引在內，表格的欄數多少，可為整數或範圍
                if len(r) != col: continue 
            elif len(r) not in range(*col): continue # col為範圍時之處理，如col=(7,10)即為7, 8, 9
            elif len(r) == col[0]: r = [string] + r # 填補標題列之缺值，用於如擷取晨星Dior，處理方法可再改良
        r = [re.sub(r'\s+', ' ', i.strip()) for i in r] # 移除無謂空格
        if subst != None: r = [mulreplace(i, subst) for i in r] # 需要取代的字樣，如subst={",": ""}
        r = [np.nan if x == '-' else x for x in r] # 處理"-"
        R.append(r)
    return R

def rowtable(R, string='', num=0):
    st = 0
    for r in R:
        if st == 0 and string in r[num]:  # string為表格左上用以識別之字，num為string於首行串列之位置，最左上則為0
            st = 1
            df = pd.DataFrame(columns=r)
        elif st == 0: continue
        else: 
            if '2019' in r and '2019' not in df.columns and len(df) > 10 and 'Fiscal Period' in r[0]:
                df.insert(1, '2019', np.nan) # 應對marketscreener抄錄ABNB失敗情況
            elif len(df.columns) == len(r) - 1: df.insert(0, string, np.nan)
            elif len(df.columns) == len(r) + 1: continue
            df.loc[len(df)] = r
    return df

def table(soup, string='', col=None, num=0, subst=None):
    R = tablerow(soup, string, col, subst)
    return rowtable(R, string, num)
    
def oldtable(soup, string, col=None, num=0, subst=None): # 於已擷取網頁資料中勾出表格
    st = 0
    for tr in soup.select('tr'): # soup從網址可如此擷取而得：urlsoup(url)
        r = [td.text for td in tr.select('td, th') if td.text]
        if r == []: continue
        if col != None: 
            if isinstance(col, int): # col為包括索引在內，表格的欄數多少，可為整數或範圍
                if len(r) != col: continue 
            elif len(r) not in range(*col): continue # col為範圍時之處理，如col=(7,10)即為7, 8, 9
            elif len(r) == col[0]: r = [string] + r # 填補標題列之缺值，用於如擷取晨星Dior，處理方法可再改良
        r = [re.sub(r'\s+', ' ', i.strip()) for i in r] # 移除無謂空格
        if subst != None: r = [mulreplace(i, subst) for i in r] # 需要取代的字樣，如subst={",": ""}
        r = [np.nan if x == '-' else x for x in r] # 處理"-"

        if st == 0 and string in r[num]:  # string為表格左上用以識別之字，num為string於首行串列之位置，最左上則為0
            st = 1
            df = pd.DataFrame(columns=r)
        elif st == 0: continue
        else: 
            if '2019' in r and '2019' not in df.columns and len(df) > 10 and 'Fiscal Period' in r[0]:
                df.insert(1, '2019', np.nan) # 應對marketscreener抄錄ABNB失敗情況
            elif len(df.columns) == len(r) - 1: df.insert(0, string, np.nan)
            df.loc[len(df)] = r
    return df

def dcv(d): return datetime.strptime(d, '%b %d, %Y').strftime('%Y-%m-%d') # date convert

def SPXPE(): # 取得標普市盈表
    df = table(urlsoup('https://www.multpl.com/s-p-500-pe-ratio/table/by-month'), 'Date')
    df['Date'] = df['Date'].apply(dcv)
    df = df.rename(columns = {'Value': 'PE'})
    df = df.replace("†", "", regex=True)
    df['PE'] = df['PE'].astype(float)
    df = df.set_index('Date').sort_index()
    df = df.reset_index(level=0)
    return df

def searchMS(st, highest=False, namematch=True): # 以股名或股號搜尋市場篩選網站，得出最高成交的上市股票，可查出多處上市企業之最有代表性上市地及股號
    u = 'https://www.marketscreener.com/search/instruments?q=' + st
    s = urlsoup(u)
    R = tablerow(s, '')
    R[0].insert(1, 'Ticker')
    R = [r + ['NA'] if len(r) == 5 else r for r in R]
    df = rowtable(R)
    del df['Type']; del df['Price']
    df = df.dropna()
    if namematch: df = df[df['Name'].str.contains(st.upper())]
    df['Average volume'] = df['Average volume'].str.replace(',', '', regex=True).astype(int)
    df = df[~(df[['Average volume']] == 0).any(axis=1)]
    df = df.sort_values(by='Average volume', ascending=False).reset_index(drop=True)
    df['Stock exchange'] = df['Stock exchange'].str.replace(r' \+\d Other', '', regex=True)
    if highest: return df.iloc[0].tolist() # [股名、股號、交易所、平均成交量]
    return df # 得出以成交量排行的完整列表


# getnationengtochi式群
def removecit(s): # 整走'[15]'之類的註腳
    a = stringsearch(s, r'(.*)\[\d+\]')
    return s if a is None else a

def getnationengtochi(): # 抄錄英文國名對中文國名之字典
    i = {'USA': '美國', 'South Korea': '韓國', 'UK': '英國', 'Italy': '意大利', 'Australia': '澳洲', 
         'Russia': '俄羅斯', 'UAE': '阿聯酋', 'Unknown': '不詳', 'Soviet Union': '蘇聯'}
    u = 'https://www.webdesigntooler.com/internet-country-code-table'
    d = twocol2d(table(urlsoup(u), '中文'), '英文', '中文')
    d.update(i)
    u = 'https://zh.wikipedia.org/zh-hk/%E5%9B%BD%E5%AE%B6%E4%BB%A3%E7%A0%81%E5%AF%B9%E7%85%A7%E8%A1%A8'
    D = twocol2d(table(urlsoup(u), '國家/地區', 6), '英文名稱', '國家/地區')
    D = {removecit(k).replace('The ', ''): v for k, v in D.items()}
    D.update(d)
    return D

# 正則表達式相關
def stringextract(s, p, defau=None, g=1): # 以正則表達式試抽取合模式的元素，s, p, g分指statement, pattern, group number
    m = re.match(p, s)
    return m.group(g) if m else defau

def stringsearch(s, p, defau=None, g=1): # 上式需從一開始即吻合，此式則在中間找到吻合即能抽取
    m = re.search(p, s)
    return m.group(g) if m else defau
# regex cheatsheet ref: https://cheatography.com/davechild/cheat-sheets/regular-expressions/

# getfinan_yf式群
def textlist(l): return [i.text for i in l if i.text != '']
    
def svelte(s): # 擷取雅虎財務網站表格的特殊方法，2024-05-06更新
    s = s.find('div', {'class': 'tableContainer svelte-1pgoo1f'})
    coln = [h.get_text(strip=True) for h in s.select('.tableHeader .row .column')]
    rs = []
    for r in s.select('.tableBody .row'):
        cols = r.select('.column')
        d = [c.get_text(strip=True) for c in cols]
        rs.append(d)
    return pd.DataFrame(rs, columns=coln).set_index('Breakdown')

def getyhft(t, stm='balance-sheet'): # 根據報表種類，由雅虎財務網站取得特定股票的報表
    s = urlsoup('https://finance.yahoo.com/quote/' + t + '/' + stm)
    return svelte(s)

def tickercurr(t): # 根據股號，經雅虎財務，得出該股之交易貨幣
    d = {'005930.KS': 'KRW', 'AAPL': 'USD', 'ABBNY': 'USD', 'ABBV': 'USD', 'ABNB': 'USD', 'ABT': 'USD', 'ACN': 'USD', 'ADBE': 'USD', 'ADI': 'USD', 'ADP': 'USD', 'ADDYY': 'USD', 'AIQUY': 'USD', 'ALIZY': 'USD', 'AMAT': 'USD', 'AMD': 'USD', 'AMGN': 'USD', 'AMT': 'USD', 'AMZN': 'USD', 'ANET': 'USD', 'ASML': 'USD', 'ATLKY': 'USD', 'AVGO': 'USD', 'AXAHY': 'USD', 'AXON': 'USD', 'AXP': 'USD', 'AZN': 'USD', 'BA': 'USD', 'BABA': 'USD', 'BAC': 'USD', 'BHP': 'USD', 'BLK': 'USD', 'BMO': 'USD', 'BMY': 'USD', 'BNPQY': 'USD', 'BKNG': 'USD', 'BP': 'USD', 'BRK-B': 'USD', 'BSX': 'USD', 'BUD': 'USD', 'BX': 'USD', 'C': 'USD', 'CAT': 'USD', 'CB': 'USD', 'CFRUY': 'USD', 'CHTR': 'USD', 'CI': 'USD', 'COP': 'USD', 'COST': 'USD', 'CSCO': 'USD', 'CMCSA': 'USD', 'CME': 'USD', 'CMG': 'USD', 'CMWAY': 'USD', 'CNC': 'USD', 'CRM': 'USD', 'CSLLY': 'USD', 'CVS': 'USD', 'CVX': 'USD', 'DE': 'USD', 'DELL': 'USD', 'DFS': 'USD', 'DHR': 'USD', 'DIS': 'USD', 'DPZ': 'USD', 'DTEGY': 'USD', 'EA': 'USD', 'EADSY': 'USD', 'EL': 'USD', 'ELV': 'USD', 'ENLAY': 'USD', 'EPAM': 'USD', 'ESLOY': 'USD', 'ETN': 'USD', 'F': 'USD', 'FDX': 'USD', 'FI': 'USD', 'FRCOY': 'USD', 'FTNT': 'USD', 'GE': 'USD', 'GM': 'USD', 'GOOGL': 'USD', 'GS': 'USD', 'GSK': 'USD', 'HCA': 'USD', 'HD': 'USD', 'HDB': 'USD', 'HESAY': 'USD', 'HMC': 'USD', 'HON': 'USD', 'HPQ': 'USD', 'HSBC': 'USD', 'HTHIY': 'USD', 'HUM': 'USD', 'IBKR': 'USD', 'IBM': 'USD', 'ICE': 'USD', 'IDEXY': 'USD', 'ILMN': 'USD', 'INTC': 'USD', 'INTU': 'USD', 'ISRG': 'USD', 'JNJ': 'USD', 'JPM': 'USD', 'KLAC': 'USD', 'KKR': 'USD', 'KO': 'USD', 'KYCCF': 'USD', 'LIN': 'USD', 'LLY': 'USD', 'LMT': 'USD', 'LOW': 'USD', 'LRCX': 'USD', 'LRLCY': 'USD', 'LULU': 'USD', 'LVMUY': 'USD', 'MA': 'USD', 'MAR': 'USD', 'MBGAF': 'USD', 'MCD': 'USD', 'MCO': 'USD', 'MDLZ': 'USD', 'MDT': 'USD', 'MELI': 'USD', 'MET': 'USD', 'META': 'USD', 'MFC': 'USD', 'MMC': 'USD', 'MMM': 'USD', 'MOH': 'USD', 'MRK': 'USD', 'MS': 'USD', 'MSBHF': 'USD', 'MSFT': 'USD', 'MSI': 'USD', 'MU': 'USD', 'MUFG': 'USD', 'NEE': 'USD', 'NOW': 'USD', 'NSRGY': 'USD', 'NTDOY': 'USD', 'NTTYY': 'USD', 'NVO': 'USD', 'NKE': 'USD', 'NFLX': 'USD', 'NVDA': 'USD', 'NVS': 'USD', 'NXPI': 'USD', 'ORCL': 'USD', 'PANW': 'USD', 'PBR': 'USD', 'PEP': 'USD', 'PFE': 'USD', 'PG': 'USD', 'PGR': 'USD', 'PLD': 'USD', 'PM': 'USD', 'POAHY': 'USD', 'PYPL': 'USD', 'QCOM': 'USD', 'RACE': 'USD', 'REGN': 'USD', 'RIO': 'USD', 'RHHBY': 'USD', 'RTX': 'USD', 'RY': 'USD', 'SAFRY': 'USD', 'SAP': 'USD', 'SBGSY': 'USD', 'SBUX': 'USD', 'SCCO': 'USD', 'SCHW': 'USD', 'SFTBY': 'USD', 'SHEL': 'USD', 'SHOP': 'USD', 'SIEGY': 'USD', 'SNPS': 'USD', 'SO': 'USD', 'SONY': 'USD', 'SPGI': 'USD', 'SPOT': 'USD', 'SNY': 'USD', 'STZ': 'USD', 'SVNDY': 'USD', 'SYK': 'USD', 'T': 'USD', 'TCEHY': 'USD', 'TD': 'USD', 'TER': 'USD', 'TJX': 'USD', 'TM': 'USD', 'TMO': 'USD', 'TMUS': 'USD', 'TOELY': 'USD', 'TRI': 'USD', 'TSLA': 'USD', 'TSM': 'USD', 'TTE': 'USD', 'TTWO': 'USD', 'TXN': 'USD', 'UBER': 'USD', 'UBS': 'USD', 'UL': 'USD', 'UNH': 'USD', 'UNP': 'USD', 'UPS': 'USD', 'V': 'USD', 'VRTX': 'USD', 'VZ': 'USD', 'WFC': 'USD', 'WM': 'USD', 'WMT': 'USD', 'XOM': 'USD', 'ZBRA': 'USD'}
    if t in d: return d[t]
    while 1:
        s = urlsoup('https://finance.yahoo.com/quote/' + t + '/')
        f = s.find('i', {'data-svelte-h': "svelte-sg6bkb"})
        if f is None: print('疑遭暫鎖，候兩分鐘'); time.sleep(120)
        else: break
    return f.find_next('span').text

def fism(t): # 由雅虎財務取得股票之結算月份
    df = getyhft(t)
    return int(stringextract(df.columns[0], r'(\d{1,2})/\d{1,2}/\d{4}'))

def yfinanDatetoYM(y): # 日期格式轉換：'6/30/2023'->'2023-06'
    def month2dg(m): return m if len(m) == 2 else '0' + m
    y = re.findall(r'(\d+)\/(\d+)\/(\d{4})', y)[0]
    ym = y[-1] + '-' + month2dg(y[0])
    return ym

def getfinan_yf(t, ym, finan='Total Assets'): # 以股號及年月，向雅虎財務數據網，查詢資產負債表中的財務資料
    df = getyhft(t)
    if df is None: return None
    try: mdy = [d for d in list(df.columns) if yfinanDatetoYM(d) == ym][0]
    except IndexError: print(f'於雅虎財務庫擷取{t} {ym} {finan}發生錯誤，該年月無數據'); return None
    value = df.loc[finan, mdy]
    return float(value.replace(',', '')) * 1000
# https://finance.yahoo.com/quote/MSFT/balance-sheet

# marketcaplist式群
def slicelist(l, n): # 將一個串列分解成多個串列，每個小串列有n個元素
    def s(l, n):
        for i in range(0, len(l), n): yield l[i:i + n]
    return list(s(l, n))

def compn(s): return s.select_one('div.company-name').text.strip(), s.select_one('div.company-code').text.strip()

def marketcap(n=1): # 取得世界最高市值股票表格，擷取方式特殊
    s = urlsoup('https://companiesmarketcap.com/page/' + str(n)) # n為頁數，每頁百股
    tab = s.select_one('table.default-table.table.marketcap-table.dataTable')
    header = tab.select('th')
    td = tab.select('td')
    td = header + td
    # 分解含企業名稱與股號之td標籤，否則將連體難以處理
    td = [compn(i) if i.select_one('div.company-name') else i.text.strip().replace('Close Ad X', '') for i in td] 
    td = [i for i in td if i != '']
    td.remove('Price (30 days)') # 此header中的欄目無文字內容
    header, td = td[:6], td[6:]
    
    #R = slicelist(td, 6) # 原本做法，若遇國家資料缺失則發生錯誤
    R = []; r = []
    for i in td:
        if isinstance(i, str) and re.match(r'^\d+$', i): 
            if r != []: R.append(r); r = [] # 以排名數字為新一行
        r.append(i)
    R.append(r) # 加入最後一行
    for r in R:
        if len(r) == 5:  # 國家資料缺失，以致一行不足六個元素
            if 'Philippine' in r[1][0]: r.append('Philippines') # 'Bank of the Philippine Islands'資料缺漏國家
            elif r[1][1].endswith('.DE'): r.append('Germany')
            else: 
                print('市值表以下一列缺失一項資料：', r)
                r.append(np.nan) # 意外情況，填空值
    df = pd.DataFrame(columns=header)
    for r in R: df.loc[len(df)] = r # 匯成表格
    del df['Today']
    
    d = df.to_dict('index')
    D = {}
    for k, v in d.items():
        D[k] = v
        D[k]['Company Name'] = D[k]['Name'][0] # 解開企業名稱與股號兩者
        D[k]['Ticker'] = D[k]['Name'][1]
        del D[k]['Name']
        
    df = pd.DataFrame.from_dict(D, 'index').set_index('Rank')
    df.insert(0, 'Ticker', df.pop('Ticker')) # 重排欄目
    df.insert(0, 'Company Name', df.pop('Company Name'))
    df['Country'] = df['Country'].str.replace(r'^\S{2} ', '', regex=True)
    return df

def marketcaplist(n=1): return marketcap(n)['Ticker'].tolist()

def marketcaprank(n=500):
    l = []
    for i in range(n//100):
        df = marketcap(i+1)
        l.append(df)
    df = pd.concat(l)
    return df

ustickconvd = {'GOOG': 'GOOGL', 'MC.PA': 'LVMUY', 'NESN.SW': 'NSRGY', 'ROG.SW': 'RHHBY', 
               '6861.T': 'KYCCF', 'SIE.DE': 'SIEGY', 'OR.PA': 'LRLCY', 'AIR.PA': 'EADSY', 'SU.PA': 'SBGSY', 
               'DTE.DE': 'DTEGY', '8035.T': 'TOELY', 'AI.PA': 'AIQUY', 'EL.PA': 'ESLOY', 'MBG.DE': 'MBGAF', 
               'ABBN.SW': 'ABBNY', 'CFR.SW': 'CFRUY', '6501.T': 'HTHIY', '8058.T': 'MSBHF', 'NPPXF': 'NTTYY', 
               'ATCO-B.ST': 'ATLKY', 'P911.DE': 'POAHY', 'ALV.DE': 'ALIZY', 'CBA.AX': 'CMWAY', 'SAF.PA': 'SAFRY', 
               'CSL.AX': 'CSLLY', 'BNP.PA': 'BNPQY', 'CDI.PA': 'CHDRY', 'RMS.PA': 'HESAY', 'PRX.AS': 'PROSY', 
               '000660.KS': 'HXSCL', '9983.T': 'FRCOY', 'CS.PA': 'AXAHY', '9984.T': 'SFTBY', 'ENEL.MI': 'ENLAY',
               '7974.T': 'NTDOY', 'ADS.DE': 'ADDYY', '3382.T': 'SVNDY'} # 市值排行表上的股號對換美國上市股號
def ustickconv(): return ustickconvd # 轉化marketcap上的股號為見於殘極系統之常用美股股號


# monthname式群
def getmonthname(): # 取得每月的所有語言名稱
    u = 'https://www.omniglot.com/language/time/months.htm'
    df = table(u, 'January', 1, 12)
    d = df.to_dict('list')
    del d['Unnamed: 0']; del d['\xa0']
    return d

def month(n): # 轉譯外語月份名稱成數字，如 'Juli' -> 7; 'Maart' -> 3
    l = list(calendar.month_name)
    if n in l: return l.index(n)
    m = None; print(f'特別月份名稱：{n}')
    
    d = loadelsedef(r'C:\Users\user\.spyder-py3\utility\monthname.json')
    if d == {}: 
        d = getmonthname()
        save(r'C:\Users\user\.spyder-py3\utility\monthname.json', d)
    for k, v in d.items():
        for i in v:
            if n.lower() in i.lower(): m = k; break; break
    return l.index(m)


# GDP相關式群
import json
from urllib.request import urlopen
ny = datetime.now().year
C = {'EUR': 'EURO', 'USD': 'USA', 'CNY': 'CHN', 'GBP': 'GBR', 
     'JPY': 'JPN', 'KRW': 'KOR', 'SGD': 'SGP', 
     'CAD': 'CAN', 'MYR': 'MYS', 'THB': 'THA', 'VND': 'VNM',
     'HKD': 'HKG', 'AUD': 'AUS',
     'CHF': 'CHE', 'SEK': 'SWE', 'NZD': 'NZL', 'INR': 'IND',
     'NOK': 'NOR', 'TWD': 'TWN'}

def currnation(): return C

def wbGDP(c): # 世界銀行數據，惟未有最近兩年數據
    ci = C[c] if c != 'EUR' else 'EMU'
    u = "https://api.worldbank.org/v2/en/country/" + ci + "?downloadformat=excel"
    df = pd.read_excel(u, skiprows=3)
    df = df[df['Indicator Name'] == 'GDP (current US$)'].iloc[:,4:].T
    df.index.names = ['Year']
    df.columns = ['GDP']
    df['GDP'] = df['GDP'].astype(float)
    df = df.rename(columns = {'GDP': c+'GDP'})
    df = df.sort_index()
    df = df.reset_index(level=0)
    return df

def IMFGDP(c): # 國際貨幣基金會數據，歐元區GDP數據始於1991，美國、中國始於1980，含多年預測數據
    res = urlopen('https://www.imf.org/external/datamapper/api/v1/NGDPD/' + C[c]) 
    d = json.loads(res.read())
    d = d['values']['NGDPD'][C[c]]
    df = pd.DataFrame(d.items(), columns=['Year', c+'GDP'])
    df['Year'] = df['Year'].astype(int)
    df[c+'GDP'] = df[c+'GDP'].astype(float)
    return df[df['Year'] <= ny]

def statistaGDP(c): # 世銀與基金會俱無台灣數據，需另覓此渠道
    if c == 'TWD': nn = 'taiwan'
    else: raise Exception('需指定幣種，可建立幣種與statista連結字串對譯表')
    u = "https://www.statista.com/statistics/727589/gross-domestic-product-gdp-in-"
    s = urlsoup(u + nn)  # Replace with the actual URL
    tab = s.find("table", id="statTableHTML")
    d = {}
    for r in tab.find_all("tr")[1:]:
        td = r.find_all("td")
        d[int(td[0].text.strip("*"))] = float(td[1].text.replace(",", ""))
    df = pd.DataFrame(d.items(), columns=['Year', c+'GDP'])
    df = df[df['Year'] <= ny]
    return df.sort_values(by='Year').reset_index(drop=True)


# 2024年經濟自由度數據
econfree = {'Albania': 64.8, 'Algeria': 43.9, 'Angola': 54.3, 'Argentina': 49.9, 'Armenia': 64.9, 
            'Australia': 76.2, 'Austria': 68.4, 'Azerbaijan': 61.6, 'The Bahamas': 62.5, 'Bahrain': 63.4, 
            'Bangladesh': 54.4, 'Barbados': 66.8, 'Belarus': 48.4, 'Belgium': 65.6, 'Belize': 61.2, 
            'Benin': 57.7, 'Bhutan': 55.4, 'Bolivia': 43.5, 'Bosnia and Herzegovina': 62.0, 'Botswana': 68.0, 
            'Brazil': 53.2, 'Brunei Darussalam': 65.9, 'Bulgaria': 68.5, 'Burkina Faso': 51.9, 'Burma': 42.2, 
            'Burundi': 38.4, 'Cabo Verde': 62.9, 'Cambodia': 55.6, 'Cameroon': 53.6, 'Canada': 72.4, 
            'Central African Republic': 41.3, 'Chad': 51.4, 'Chile': 71.4, 'China': 48.5, 'Colombia': 59.2, 
            'Comoros': 52.0, 'Democratic Republic of Congo': 47.6, 'Republic of Congo': 47.8, 
            'Costa Rica': 67.7, "Côte d'Ivoire": 58.4, 'Croatia': 67.2, 'Cuba': 25.7, 'Cyprus': 72.2, 
            'Czech Republic': 70.2, 'Denmark': 77.8, 'Djibouti': 55.8, 'Dominica': 54.0, 
            'Dominican Republic': 62.9, 'Ecuador': 55.0, 'Egypt': 49.7, 'El Salvador': 54.4, 
            'Equatorial Guinea': 47.7, 'Eritrea': 39.5, 'Estonia': 77.8, 'Eswatini': 55.6, 'Ethiopia': 47.9, 
            'Fiji': 58.0, 'Finland': 76.3, 'France': 62.5, 'Gabon': 56.9, 'The Gambia': 58.2, 'Georgia': 68.4, 
            'Germany': 72.1, 'Ghana': 55.8, 'Greece': 55.1, 'Guatemala': 62.4, 'Guinea': 53.3, 
            'Guinea-Bissau': 42.7, 'Guyana': 57.3, 'Haiti': 48.2, 'Honduras': 58.6, 'Hungary': 61.2, 
            'Iceland': 70.5, 'India': 52.9, 'Indonesia': 63.5, 'Iran': 41.2, 'Ireland': 82.6, 'Israel': 70.1, 
            'Italy': 60.1, 'Jamaica': 68.1, 'Japan': 67.5, 'Jordan': 58.3, 'Kazakhstan': 62.0, 'Kenya': 53.6, 
            'Kiribati': 51.3, 'North Korea': 2.9, 'South Korea': 73.1, 'Kosovo': 60.6, 'Kuwait': 58.5, 
            'Kyrgyz Republic': 55.2, 'Laos': 50.6, 'Latvia': 71.5, 'Lebanon': 48.3, 'Lesotho': 51.9, 
            'Liberia': 49.9, 'Lithuania': 72.9, 'Luxembourg': 79.2, 'Madagascar': 57.3, 'Malawi': 52.1, 
            'Malaysia': 65.7, 'Maldives': 47.8, 'Mali': 52.5, 'Malta': 64.5, 'Mauritania': 55.3, 
            'Mauritius': 71.5, 'Mexico': 62.0, 'Micronesia': 61.0, 'Moldova': 57.1, 'Mongolia': 60.6, 
            'Montenegro': 59.7, 'Morocco': 56.8, 'Mozambique': 50.7, 'Namibia': 57.5, 'Nepal': 52.1, 
            'Netherlands': 77.3, 'New Zealand': 77.8, 'Nicaragua': 53.4, 'Niger': 52.3, 'Nigeria': 53.1, 
            'North Macedonia': 61.4, 'Norway': 77.5, 'Oman': 62.9, 'Pakistan': 49.5, 'Panama': 64.1, 
            'Papua New Guinea': 49.4, 'Paraguay': 60.1, 'Peru': 64.8, 'The Philippines': 59.0, 
            'Poland': 66.0, 'Portugal': 68.7, 'Qatar': 68.8, 'Romania': 64.4, 'Russia': 52.0, 
            'Rwanda': 51.6, 'Samoa': 67.2, 'São Tomé and Príncipe': 60.5, 'Saudi Arabia': 61.9, 
            'Senegal': 55.4, 'Serbia': 62.7, 'Seychelles': 60.4, 'Sierra Leone': 44.6, 'Singapore': 83.5, 
            'Slovakia': 68.1, 'Slovenia': 65.9, 'Solomon Islands': 55.0, 'South Africa': 55.3, 'Spain': 63.3, 
            'Sri Lanka': 49.2, 'Saint Lucia': 62.2, 'Saint Vincent and the Grenadines': 59.8, 
            'Sudan': 33.9, 'Suriname': 46.7, 'Sweden': 77.5, 'Switzerland': 83.0, 'Taiwan': 80.0, 
            'Tajikistan': 51.3, 'Tanzania': 59.1, 'Thailand': 59.0, 'Timor-Leste': 50.2, 'Togo': 50.9, 
            'Tonga': 59.2, 'Trinidad and Tobago': 60.4, 'Tunisia': 48.8, 'Türkiye': 56.2, 
            'Turkmenistan': 46.3, 'Uganda': 50.7, 'United Arab Emirates': 71.1, 'United Kingdom': 68.6, 
            'United States': 70.1, 'Uruguay': 69.8, 'Uzbekistan': 55.9, 'Vanuatu': 62.2, 'Venezuela': 28.1, 
            'Vietnam': 62.8, 'Zambia': 48.4, 'Zimbabwe': 38.2}

def geteconfree(): # 以上數據取得方法
    # 此檔案目前須每年往下網下載
    # https://www.heritage.org/index/pages/all-country-scores
    fn = r'C:\Users\user\Downloads\2024_indexofeconomicfreedom_data.xlsx'
    df = pd.read_excel(fn, header=1)
    df = df[['Country', 'Overall Score']].dropna()
    d = twocol2d(df, 'Country', 'Overall Score')
    return d

def econfreedf(): return d2twocol(econfree, 'Country', 'Overall Score')


# 貨幣名稱
def wikiu(s): return 'https://en.wikipedia.org/wiki/' + s
def currency(): return table(urlsoup(wikiu('List_of_circulating_currencies')), 'State or territory', 6)

def currencylist(): # 所有貨幣之ISO名稱列表
    l = set(currency()['ISO code[3]'].tolist())
    l.remove('(none)')
    return list(l)