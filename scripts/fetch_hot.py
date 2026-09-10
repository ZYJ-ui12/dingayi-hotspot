# -*- coding: utf-8 -*-
"""抓取 86TOOL 抖音/小红书双平台热榜 -> repo根/hotdata.json（抖音50/小红书20）
独立于品牌库的博主看板流水线，仅保留用户要求的双平台。
"""
import os, re, json, ssl, urllib.request

URL = 'https://tool.caizhichao.cn/hot-rank.html'
CTX = ssl._create_unverified_context()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fetch():
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
        return r.read().decode('utf-8', errors='replace')

def parse(html):
    parts = re.split(r'<div class="list-container">', html)[1:]
    result = {'douyin': [], 'xhs': []}
    pat = re.compile(r'<li class="list-item">.*?<span class="item-index">(\d+)</span>\s*<span>(.*?)</span>.*?<span class="item-time">([\d.]+)</span>', re.S)
    for c in parts:
        m = re.search(r'<h3>(.*?)</h3>', c, re.S)
        if not m:
            continue
        name = m.group(1).strip()
        plat = None
        if '抖音热搜' in name:
            plat = 'douyin'
        elif '小红书热搜' in name:
            plat = 'xhs'
        if not plat:
            continue
        rows = []
        for rank, title, hot in pat.findall(c):
            title = re.sub(r'&ldquo;|&rdquo;', '"', title)
            title = re.sub(r'&amp;', '&', title)
            title = re.sub(r'<[^>]+>', '', title).strip()
            rows.append({'rank': int(rank), 'title': title, 'hot': hot.strip()})
        result[plat] = rows
    return result

if __name__ == '__main__':
    data = parse(fetch())
    total = sum(len(v) for v in data.values())
    print('douyin %d | xhs %d | total %d' % (len(data['douyin']), len(data['xhs']), total))
    if len(data['douyin']) < 40 or len(data['xhs']) < 15:
        raise SystemExit('榜单数量异常，疑似抓取失败，中止更新')
    with open(os.path.join(ROOT, 'hotdata.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('saved', os.path.join(ROOT, 'hotdata.json'))
