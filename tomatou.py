import numpy as np, pandas as pd, re; from unidecode import unidecode; from datetime import datetime
from scrapu import getnationengtochi, mulreplace, stringsearch, urlsoup
nowy = datetime.now().year
pd.options.mode.chained_assignment = None

def d4(s): return True if re.search(r'\b\d{4}\b', s) else False 

# gettomato式群
def getsoupfromtit(tit): # 由電影標題，得出爛蕃茄搜尋網頁內容
    tit = tit.replace(' ', '%20')
    u = f"https://www.rottentomatoes.com/search?search={tit}"
    return urlsoup(u)

def tomatosearch(s): # 從爛蕃茄搜尋網頁內容中，取得搜尋結果
    s = s.find('search-page-result', {"type": "movie"})
    if s is None: return None
    s = s.find_all('search-page-media-row')
    d = []
    for r in s:
        infon = r.find('a', {'data-qa': 'info-name'})
        tit, u = infon.text.strip(), infon['href']
        yr = r['releaseyear']
        d.append([tit, yr, u])
    return d

def tomatolinkfmse(d, tit, y): # 由搜尋結果字典中取出吻合的連結
    for l in d:
        if l[1] == y or l[1] == str(int(y)-1): return l[0], l[-1] # 爛蕃茄電影標題、對應連結

def get_year(s): # 字串中取出四位數字年份
    m = re.search(r'\b(19\d{2}|20\d{2})\b', s)
    return m.group(1) if m else None

def is_movie_time(s): return bool(re.match(r'^\d+h\s*\d+m$', s))

def gettomatostat(s): # 由爛蕃茄電影頁面連結，取得其數據
    if '404 - Not Found' in s.find('div', {'id': 'main-page-content'}).find('h1').text: return None
    txt = s.find('script', {'id': 'media-hero-json'})
    txtd = txt.contents[0].strip()
    d = eval(txtd, {'true': True, 'false': False, 'null': None})# 強制將字串轉成字典
    print('d', d)
    content = d['content']
    tit = content['title']
    gr = '/'.join(content['metadataGenres'])
    t = mulreplace(content['metadataProps'][-1], {'.': '', ' hr': 'h', ' min': 'm'})
    if is_movie_time(t) == False: t = None
    
    y = None
    y = get_year(content['metadataProps'][0])
    if y is None and len(content['metadataProps']) > 1: 
        y = get_year(content['metadataProps'][1])
    if y is None: 
        ydiv = s.find_all('div', class_='category-wrap')
        ye = None
        for d in ydiv: 
            if 'Release Date' in d.text.strip(): ye = d.find('dd')
        if ye: y = ye.text
    if y is None:
        yp = content['metadataProps'][0]
        if yp == 'Now Playing' or 'In Theaters' in yp: y = str(nowy)
    if y is None:
        yp = content['metadataProps'][1]
        if yp == 'Now Playing' or 'In Theaters' in yp: y = str(nowy)
    else: y = stringsearch(y, r'(\d{4})')
    
    s = s.find('div', {'class': "media-scorecard no-border"})
    def findtag(x): return x.text.strip().replace('%', '') if x else np.nan
    tomato = findtag(s.find('rt-text', {'slot': "criticsScore"}))
    audi = findtag(s.find('rt-text', {'slot': "audienceScore"}))
    rn = findtag(s.find('rt-link', {'slot': "criticsReviews"}))
    an = findtag(s.find('rt-link', {'slot': "audienceReviews"}))
    return [tit, y, gr, t, tomato, rn, audi, an]
    
def gettomato(tit, y): # 由電影標題及年份，得出爛蕃茄數據
    s = getsoupfromtit(tit) # 標題搜尋頁內容
    d = tomatosearch(s) # 搜尋結果
    if d is None: return None
    tu = tomatolinkfmse(d, tit, y)
    if tu is None: return None
    u = tu[-1] # 吻合的連結
    if u == '': return None
    print('link', u)
    s = urlsoup(u) # 上述連結的網頁內容
    d = gettomatostat(s) # 該網頁的爛蕃茄數據
    return d

# ismatch式群
def normal(tit): # 將電影標題格式化以便比較
    tit = tit.lower()
    tit = mulreplace(tit)
    tit = unidecode(tit)
    if d4(tit[-4:]): tit = tit[:-4] # 若有年份，移除
    return tit

def listremove(l, rm=['the', 'x', '×']):
    for i in rm:
        if i in l: l.remove(i)
    return l

def checkmatch(t1, t2): # 兩個電影標題是否超過一半的字吻合
    w1 = re.findall(r'\w+', t1.lower()) # 拆為字
    w2 = re.findall(r'\w+', t2.lower())
    if all(w in w2 for w in w1) and all(w in w1 for w in w2): return True # 所有字均吻合
    w1 = listremove(w1); w2 = listremove(w2)
    if len(w1) < len(w2): w1, w2 = w2, w1 # w1字數應多於w2
    max_len = len(w1)
    match = sum(1 for w1 in w1 if w1 in w2) # 核對w1吻合w2之字數
    if max_len > 6 and match > max_len / 3 * 2: return True # 字逾六個之下，超過三分之二的字吻合
    return False

def ismatch(t1, t2): # 檢查兩個英語電影標題是否應為同一電影
    t1 = normal(t1); t2 = normal(t2)
    if t1 == t2: return True
    elif checkmatch(t1, t2): return True
    else: return False
    
# tomatable式群
def getp(x, p): return stringsearch(x, p, x)
def imbd(x): return np.nan if pd.isna(x) else float(getp(x, r'IMDb: (\d+(.\d+)?)')) # 轉寫IMDb欄目為點數
def revn(x): return getp(x, r'(\d+) Reviews') if x != 'Review' else np.nan # 轉寫影評人數欄目為整數
'''
Nd = getnationengtochi() # 取得英語國名譯為中文的字典
def nation(x): # 國名翻譯
    if pd.isna(x) or re.search('\d+ min', x): return np.nan
    def splitgetchi(a): # 將英語國名分開譯成中文
        s = a.split(' / ')
        if len(s) == 1: s = s[0].split(' | ')
        if len(s) == 1: s = s[0].split('/')
        s = '/'.join([Nd.get(i, i) for i in s])
        return s
    x = splitgetchi(x.replace('Republic of ', ''))
    return Nd.get(x, x).replace('澳大利亞', '澳洲').replace('印度尼西亞', '印尼')
'''
def datechitonum(d): # '2024年3月21日' -> '21/3/2024'
    m = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', d)
    return '/'.join([m.group(3), m.group(2), m.group(1)])


def audin(x): # 轉寫觀眾評價數目
    if re.search('Fewer than 50 (Verified )?Ratings', x): return int(0)
    return stringsearch(x.replace(',', ''), r'(\d+)\+ (Verified )?Ratings')

def spscore(TS, rv, AS, rw, y): # 自創綜合評分
    def t(x): return 100 * 0.75**(2-np.log10(x)) if x <= 100 else 100
    def yj(x): return 0.95 ** ((nowy - x)/10) # year adjustment factor
    
    if TS > t(rv) and rv < 100: # 爛蕃茄評分高但影評人少，則有條件用上Audience Score
        if AS != None and rw >= 100: s = t(rv)/100 * TS + (1-t(rv)/100) * AS if AS < TS else TS
        else: return np.nan
    else: s = TS
    return s * yj(y)

def notnalambda(f): return lambda x: f(x) if pd.notna(x) else x

toma1a = ["爛蕃茄名稱", "年份"]; toma1b = ["片種", "片長"]
toma2 = ["Tomatometer", "影評人數", "Audience Score", "觀眾評價數目"]
toma = toma1a + toma1b + toma2
impt = toma2 + ["年份"]
tradchi = {'只手': '隻手', '另一只': '另一隻', '大只佬': '大隻佬', '魔發': '魔髮', '白發魔女': '白髮魔女', '理發': '理髮', '房間里': '房間裡', '庭院里': '庭院裡', '攻壳机动队': '攻殻機動隊'}

def tomatable(data, col=["movieffm英文名稱", "IMDb", "國家"]): # 將含爛蕃茄數據的字典變為表格
    col = col + toma
    df = pd.DataFrame.from_dict(data).T
    df.columns = col
    df[impt] = df[impt].replace('', np.nan)
    df = df[df['Tomatometer'].notna()]
    
    df = df[df[[col[0], "爛蕃茄名稱"]].notna().all(1)]
    df = df[df.apply(lambda row: ismatch(row[col[0]], row["爛蕃茄名稱"]), axis=1)] # 僅留兩個電影名稱吻合者
    df.index = [mulreplace(i, tradchi) for i in df.index]

    if 'IMDb' in df: df["IMDb"] = df["IMDb"].apply(imbd)
    if '國家' in df: df['國家'] = df['國家'].apply(nation)
    if '上映日期' in df: df['上映日期'] = df['上映日期'].apply(datechitonum)
    df['影評人數'] = df['影評人數'].apply(notnalambda(revn))
    df['觀眾評價數目'] = df['觀眾評價數目'].apply(notnalambda(audin))

    
    df[impt] = df[impt].fillna(-99).astype('int64').replace(-99, np.nan)
    df = df.sort_values(by=impt, ascending=[False]*5)
    df = df[[col[0], *toma1a, col[2], *toma1b, *toma2, col[1]]]
    return df

def spscoretable(df): # 加上自創綜合評分
    df = df[df[impt].notna().all(axis=1)]
    df['綜合評分'] = df.apply(lambda r: spscore(r["Tomatometer"], r["影評人數"], r['Audience Score'], r['觀眾評價數目'], r['年份']), axis=1)
    df = df.sort_values(by=['綜合評分']+impt, ascending=[False]*6)
    df.insert(df.columns.get_loc('Tomatometer'), '綜合評分', df.pop('綜合評分'))
    return df[df['綜合評分'].notna()]