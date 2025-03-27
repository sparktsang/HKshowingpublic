import json, os, re
from datetime import datetime

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

def main():
    fn = latestfn('香港現在上映電影.xlsx')
    manifest = {"latest": fn}
    with open("manifest.json", "w", encoding="utf-8") as f: json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("manifest.json updated:", manifest)

if __name__ == "__main__":
    main()
