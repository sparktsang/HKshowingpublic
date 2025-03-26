import pandas as pd, re; from datetime import date; today = date.today()
from scrapu import urlsoup; from tomatou import gettomato, tomatable
from saveload import export_xlsx, save
pd.set_option("display.max_columns", None)

def showinglist():
    s = urlsoup('https://hkmovie6.com/showing')
    txt = str(s)
    pattern = re.compile(r'href="([^"]+)"[^>]*>\s*<span[^>]*>(.*?)<\/span>', re.DOTALL)
    matches = pattern.findall(txt)[:43]
    result = [(match[0], match[1].strip()) for match in matches] # get showing film names and UUID/link
    print('mo', result)
    d = {}
    for i in result:
        s = urlsoup('https://hkmovie6.com/' + i[0])
        e = s.find('h2', attrs={"id": "banner-movieName-alt"})
        if e is None: continue
        e = e.text.strip()
        y = s.find('span', attrs={'class': "mr-2"}).text.strip()
        if not re.match(r'\d{4}', y[:4]): continue
        gr = s.find('div', {'class': 'text-white px-3 ml-1 bg-neutral-800 rounded'}).text.strip()
        d[i[1]] = [e, gr, y]
        print(i[1], d[i[1]])
    return d

def HKshowingtomato(d):
    D = {}
    for c, v in d.items():
        e, gr, y = v
        print('egr', e, gr, y)
        toma = gettomato(e, y[:4])
        if toma is not None: D[c] = [e, gr, y, *toma]; print(c, D[c])
    return D

d = showinglist()
save(f'HKshowinglist {today}.json', d)
D = HKshowingtomato(d)
save(f'HKshowingtomato {today}.json', D)

df = tomatable(D, ["英文名稱", "分級", "上映日期"])
del df['分級']
del df['爛蕃茄名稱']
width = [41, 39, 7, 14.5, 50, 7]+[15]*5
fontsize = [11, 8]+[11]*9
export_xlsx(f'香港現在上映電影 {today}.xlsx', [df], ['總覽'], width, fontsize, None, None)
