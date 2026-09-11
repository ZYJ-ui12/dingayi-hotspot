# -*- coding: utf-8 -*-
"""博主看板构建：读取 hotdata.json + adv.json -> 生成 repo根/index.html
独立于品牌库的博主看板（丁阿姨又瘦啦 × 抖音/小红书双平台），编导视角借势建议。
"""
import json, io, sys, os, re, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
base = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(base)

hot = json.load(open(os.path.join(root, 'hotdata.json'), encoding='utf-8'))
adv_data = json.load(open(os.path.join(root, 'adv.json'), encoding='utf-8'))
adv = adv_data['items']
TOP3 = adv_data.get('top3', [])

# 手动更新限额记录（云端工作流维护，仅 workflow_dispatch 计次；自动更新不计）
manual_today = 0
try:
    ulog = json.load(open(os.path.join(root, 'update-log.json'), encoding='utf-8'))
    manual_today = int(ulog.get(datetime.date.today().isoformat(), 0))
except Exception:
    manual_today = 0
MANUAL_LIMIT = 5

# 更新时间记录（云端工作流每次成功更新后追加；页面展示最近 12 条）
update_history = []
try:
    uh = json.load(open(os.path.join(root, 'update-history.json'), encoding='utf-8'))
    if isinstance(uh, list):
        update_history = uh[-12:]
except Exception:
    pass

missing = []
for plat in ('douyin', 'xhs'):
    for it in hot[plat]:
        if it['title'] not in adv:
            missing.append(plat + '|' + it['title'])
if missing:
    print('MISSING ADVICE:', missing)
    sys.exit(1)
print('advice coverage OK:', sum(len(v) for v in hot.values()), 'items')

def fmt_hot(v):
    try:
        n = float(str(v).replace(',', ''))
    except Exception:
        return ''
    if n <= 0:
        return ''
    w = n / 10000.0
    if w >= 1000:
        return str(int(round(w))) + '万'
    if w >= 100:
        return ('%.1f' % w).rstrip('0').rstrip('.') + '万'
    return ('%.1f' % w).rstrip('0').rstrip('.') + '万'

def build():
    data = {}
    all_heats = []
    for plat in ('douyin', 'xhs'):
        for it in hot[plat]:
            try:
                all_heats.append(float(str(it['hot']).replace('万', '0000').replace('亿', '00000000')))
            except (ValueError, TypeError):
                pass
    max_heat = max(all_heats) if all_heats else 1
    min_heat = min(all_heats) if all_heats else 0

    history = {}
    hist_dir = os.path.join(root, 'history')
    if os.path.isdir(hist_dir):
        for fname in sorted(os.listdir(hist_dir)):
            if fname.endswith('.json'):
                try:
                    d = json.load(open(os.path.join(hist_dir, fname), encoding='utf-8'))
                    date_key = fname.replace('.json', '')
                    for plat_key in ('douyin', 'xhs'):
                        for item in d.get(plat_key, []):
                            title = item.get('title', '')
                            history.setdefault(title, []).append({'date': date_key, 'heat': item.get('hot', 0), 'rank': item.get('rank', 0)})
                except Exception:
                    pass

    def calc_priority(heat_str, tag):
        try:
            h = float(str(heat_str).replace('万', '0000').replace('亿', '00000000'))
            heat_score = ((h - min_heat) / (max_heat - min_heat) * 50) if max_heat > min_heat else 25
        except (ValueError, TypeError, ZeroDivisionError):
            heat_score = 25
        fit_score = {'angle': 50, 'no': 10, 'guard': 5}.get(tag, 15)
        return round(heat_score), round(fit_score), round(heat_score + fit_score)

    for plat in ('douyin', 'xhs'):
        rows = []
        for it in hot[plat]:
            a = adv[it['title']]
            tag = a.get('tag', 'no')
            angle = a.get('angle', '无明确承接点，客观评估后建议不借势。')
            content_tpl = a.get('content_template') if isinstance(a.get('content_template'), dict) and tag == 'angle' else None
            heat_score, fit_score, priority = calc_priority(it['hot'], tag)
            life_days = 1
            heat_trend = []
            if it['title'] in history:
                hist = history[it['title']]
                life_days = len(hist) + 1
                heat_trend = [h.get('heat', 0) for h in hist]
            try:
                cur_heat = float(str(it['hot']).replace('万', '0000').replace('亿', '00000000'))
                heat_trend.append(cur_heat)
            except (ValueError, TypeError):
                pass
            rows.append({
                'rank': it['rank'], 'title': it['title'], 'cat': a.get('cat', '生活方式'),
                'heat': fmt_hot(it['hot']), 'sum': a.get('sum', ''),
                'tag': tag, 'angle': angle, 'content_template': content_tpl,
                'priority': priority, 'heat_score': heat_score, 'fit_score': fit_score,
                'life_days': life_days,
                'heat_trend': heat_trend[-7:] if len(heat_trend) > 7 else heat_trend,
                'plat': plat,
            })
        rows.sort(key=lambda x: x['rank'])
        data[plat] = rows
    js = json.dumps(data, ensure_ascii=False)
    return render(js, CSS)

CSS = r'''
  :root{
    --ink:#2B211A; --ink2:#1C120B; --bg:#FBF6EF; --card:#FFFFFF;
    --orange:#E8642C; --orange-deep:#C24A1C; --red:#B03A2E;
    --teal:#1F7A5C; --text:#1A1B1C; --sub:#6B7280; --line:#EDE3D6;
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{
    background:var(--bg);color:var(--text);
    font-family:'Noto Sans SC','PingFang SC','Microsoft YaHei',sans-serif;
    font-weight:400;line-height:1.6;
  }
  .wrap{max-width:1060px;margin:0 auto;padding:0 20px 48px;}

  /* ===== 头部 ===== */
  header{
    background:linear-gradient(135deg,#2E2118 0%,#1C120B 100%);
    color:#FBF3EA;padding:30px 0 26px;border-bottom:3px solid var(--orange);
  }
  .h-wrap{max-width:1060px;margin:0 auto;padding:0 20px;}
  .brand-line{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;}
  .brand-en{
    font-family:'Noto Serif SC',serif;font-size:24px;font-weight:700;
    letter-spacing:4px;color:#FBF3EA;
  }
  .brand-cn{font-size:15px;letter-spacing:3px;color:#D9C6B6;}
  .brand-cn b{color:var(--orange);font-weight:500;}
  .meta-line{
    margin-top:10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;
    font-size:12.5px;color:#BFAE9E;
  }
  .meta-line .dot{width:4px;height:4px;border-radius:50%;background:var(--orange);display:inline-block;}
  .update-box{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:12px;background:rgba(255,255,255,.06);border:1px dashed rgba(232,100,44,.55);border-radius:10px;padding:9px 14px;}
  .update-info{font-size:12px;color:#D9C6B6;}
  .update-info b{color:var(--orange);font-weight:700;}
  .update-btn{display:inline-flex;align-items:center;gap:5px;background:var(--orange);color:#fff;text-decoration:none;font-size:12.5px;font-weight:600;padding:7px 16px;border-radius:8px;transition:background .2s;}
  .update-btn:hover{background:var(--orange-deep);}
  .update-history{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:8px;font-size:12px;color:#C9B7A6;}
  .uh-label{color:#FBF3EA;font-weight:600;letter-spacing:1px;white-space:nowrap;}
  .uh-list{display:flex;flex-wrap:wrap;gap:6px 10px;}
  .uh-item{white-space:nowrap;}
  .uh-item .uh-time{color:#FBF3EA;}
  .uh-item .uh-type{color:var(--orange);}
  .tagline{
    margin-top:14px;font-family:'Noto Serif SC',serif;font-size:17px;color:#FBF3EA;
    letter-spacing:2px;
  }
  .tagline em{font-style:normal;color:var(--orange);}
  .assets{margin-top:14px;display:flex;flex-wrap:wrap;gap:6px;}
  .asset{
    font-size:11px;border:1px solid rgba(251,243,234,.35);color:#D9C6B6;
    border-radius:999px;padding:2px 10px;letter-spacing:.5px;
  }
  .asset.on{border-color:var(--orange);color:var(--orange);}

  /* ===== 章节标题 ===== */
  .sec-title{margin:34px 0 14px;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;}
  .sec-title h2{font-family:'Noto Serif SC',serif;font-size:20px;font-weight:600;color:var(--ink);}
  .sec-title span{font-size:12px;color:var(--sub);}

  /* ===== TOP3 ===== */
  .top3{display:flex;gap:14px;flex-wrap:wrap;}
  .t3{
    flex:1 1 280px;min-width:0;background:var(--card);border:1px solid var(--line);
    border-top:3px solid var(--orange);border-radius:10px;padding:16px 16px 14px;
    display:flex;flex-direction:column;gap:6px;
  }
  .t3 .no{font-family:'Noto Serif SC',serif;font-size:12px;color:var(--orange-deep);letter-spacing:1px;}
  .t3 h3{font-size:16px;font-weight:600;color:var(--ink);}
  .t3 .src{font-size:11.5px;color:var(--sub);}
  .t3 .tact{font-size:12.5px;color:var(--text);border-top:1px dashed var(--line);padding-top:8px;margin-top:2px;}
  .t3 .tact b{color:var(--orange-deep);font-weight:600;}

  /* ===== 看板控制 ===== */
  .controls{
    background:var(--card);border:1px solid var(--line);border-radius:10px;
    padding:12px 14px;display:flex;flex-direction:column;gap:10px;margin-bottom:16px;
  }
  .tabs{display:flex;gap:8px;flex-wrap:wrap;}
  .tab{
    font-size:13px;padding:6px 18px;border-radius:8px;border:1px solid var(--line);
    background:#FFFDF9;color:var(--ink);cursor:pointer;transition:all .15s;
    font-family:'Noto Sans SC',sans-serif;
  }
  .tab.active{background:var(--ink);color:#FBF3EA;border-color:var(--ink);}
  .chips{display:flex;gap:6px;flex-wrap:wrap;}
  .chip{
    font-size:11.5px;padding:3px 11px;border-radius:999px;border:1px solid var(--line);
    background:#FFFDF9;color:var(--sub);cursor:pointer;transition:all .15s;
  }
  .chip.active{background:var(--orange);color:#fff;border-color:var(--orange);}
  .count-hint{font-size:11.5px;color:var(--sub);}
  .ctrl-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
  .ctrl-label{font-size:11.5px;color:var(--sub);white-space:nowrap;letter-spacing:1px;}
  .chips .cnt{font-size:10.5px;opacity:.8;margin-left:4px;}

  /* ===== 热点卡片 ===== */
  .card{
    background:var(--card);border:1px solid var(--line);border-radius:10px;
    padding:14px 16px;margin-bottom:12px;
  }
  .card-head{display:flex;gap:12px;align-items:flex-start;}
  .rank{
    font-family:'Noto Serif SC',serif;font-size:22px;font-weight:700;color:var(--ink);
    line-height:1;min-width:34px;padding-top:2px;
  }
  .card-title{font-size:15.5px;font-weight:600;color:var(--ink);line-height:1.4;}
  a.card-title{text-decoration:none;cursor:pointer;transition:color .2s;}
  a.card-title:hover{color:var(--orange);text-decoration:underline;text-underline-offset:3px;}
  .card-meta{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:5px;}
  .chip-cat{font-size:11px;background:rgba(43,33,26,.08);color:var(--ink);border-radius:999px;padding:1px 9px;}
  .heat{
    font-size:11px;background:rgba(232,100,44,.14);color:var(--orange-deep);
    border-radius:999px;padding:1px 9px;font-weight:500;
  }
  .heat.na{background:rgba(107,114,128,.12);color:var(--sub);}
  .sum{font-size:12.5px;color:var(--sub);margin-top:9px;line-height:1.65;}
  .angle{
    margin-top:9px;background:#FCF5EE;border-left:3px solid var(--orange);
    border-radius:0 8px 8px 0;padding:8px 12px;font-size:12.5px;color:var(--text);
    line-height:1.65;
  }
  .angle b{color:var(--orange-deep);font-weight:600;}
  .angle.guard{border-left-color:var(--red);background:#FBF5F2;}
  .angle.guard b{color:var(--red);}
  .angle.no{border-left-color:#9aa1a9;background:#f7f8f9;}
  .angle.no b{color:#5b6470;}

  /* ===== 底部 ===== */
  footer{
    margin-top:34px;border-top:1px solid var(--line);padding-top:16px;
    font-size:11.5px;color:var(--sub);line-height:1.8;
  }
  footer b{color:var(--ink);font-weight:600;}
  .empty{text-align:center;color:var(--sub);padding:40px 0;font-size:13px;}

  /* ===== Apple 风格优化 ===== */
  header{
    backdrop-filter:blur(20px) saturate(180%);
    -webkit-backdrop-filter:blur(20px) saturate(180%);
    background:rgba(28,18,11,0.85);
  }
  .card{
    transition:transform .35s cubic-bezier(.4,0,.2,1),box-shadow .35s cubic-bezier(.4,0,.2,1),border-color .35s;
    box-shadow:0 1px 3px rgba(0,0,0,.04),0 4px 12px rgba(0,0,0,.03);
  }
  .card:hover{
    transform:translateY(-3px);
    box-shadow:0 8px 30px rgba(0,0,0,.08),0 2px 8px rgba(0,0,0,.04);
    border-color:rgba(232,100,44,.25);
  }
  .t3{
    transition:transform .35s cubic-bezier(.4,0,.2,1),box-shadow .35s cubic-bezier(.4,0,.2,1);
    box-shadow:0 1px 3px rgba(0,0,0,.04),0 4px 12px rgba(0,0,0,.03);
  }
  .t3:hover{
    transform:translateY(-3px);
    box-shadow:0 10px 32px rgba(232,100,44,.12),0 3px 10px rgba(0,0,0,.05);
  }
  .filter-btn,.cat-btn{transition:all .28s cubic-bezier(.4,0,.2,1);cursor:pointer;}
  .filter-btn:hover,.cat-btn:hover{transform:translateY(-1px);}
  .filter-btn.active,.cat-btn.active{transform:scale(1.02);}
  .asset{transition:all .25s ease;cursor:default;}
  .asset:hover{border-color:var(--orange);color:var(--orange);}
  .rank{transition:transform .3s cubic-bezier(.4,0,.2,1);}
  .card:hover .rank{transform:scale(1.08);}
  .card,.t3{opacity:0;transform:translateY(12px);animation:fadeUp .5s cubic-bezier(.4,0,.2,1) forwards;}
  @keyframes fadeUp{to{opacity:1;transform:translateY(0);}}
  .card:hover{animation:none;opacity:1;transform:translateY(-3px);}

  /* ===== P0 功能 ===== */
  .ctrl-row-bottom{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;}
  .sort-wrap{display:flex;align-items:center;gap:8px;}
  .sort-select{
    padding:6px 12px;border:1px solid var(--line);border-radius:8px;
    background:var(--card);color:var(--text);font-size:12.5px;cursor:pointer;
    transition:border-color .25s,box-shadow .25s;
  }
  .sort-select:hover{border-color:var(--orange);box-shadow:0 2px 8px rgba(232,100,44,.1);}
  .sort-select:focus{outline:none;border-color:var(--orange);}
  .export-wrap{display:flex;gap:8px;flex-wrap:wrap;}
  .export-btn{
    padding:6px 14px;border:1px solid var(--line);border-radius:8px;
    background:var(--card);color:var(--text);font-size:12px;cursor:pointer;
    transition:all .25s cubic-bezier(.4,0,.2,1);
  }
  .export-btn:hover{border-color:var(--orange);color:var(--orange);transform:translateY(-1px);box-shadow:0 4px 12px rgba(232,100,44,.12);}
  .pri{
    font-size:11px;padding:2px 8px;border-radius:999px;
    background:rgba(107,114,128,.1);color:var(--sub);font-weight:500;
  }
  .pri-mid{background:rgba(245,158,11,.12);color:#B45309;}
  .pri-high{background:rgba(232,100,44,.12);color:var(--orange-deep);font-weight:600;}
  .angle{position:relative;}
  .copy-btn{
    position:absolute;top:8px;right:8px;
    padding:3px 10px;border:1px solid var(--line);border-radius:6px;
    background:var(--card);color:var(--sub);font-size:11px;cursor:pointer;
    transition:all .2s;opacity:0;
  }
  .card:hover .copy-btn{opacity:1;}
  .copy-btn:hover{border-color:var(--orange);color:var(--orange);}
  .copy-btn.copied{background:var(--orange);color:#fff;border-color:var(--orange);}

  /* ===== 内容模板 & 优先级 & 生命周期 ===== */
  .expand-btn{
    padding:4px 12px;border:1px solid var(--line);border-radius:999px;
    background:transparent;color:var(--sub);font-size:11px;cursor:pointer;
    transition:all .25s;flex-shrink:0;align-self:center;
  }
  .expand-btn:hover{border-color:var(--orange);color:var(--orange);}
  .card.expanded .expand-btn{border-color:var(--orange);color:var(--orange);background:rgba(232,100,44,.06);}
  .life-badge{
    font-size:10px;padding:2px 7px;border-radius:999px;
    background:rgba(31,122,92,.1);color:#176A4E;font-weight:500;
  }
  .pri-bar{
    display:flex;align-items:center;gap:16px;flex-wrap:wrap;
    padding:8px 0;margin-top:-4px;
  }
  .pri-bar-item{display:flex;align-items:center;gap:6px;}
  .pri-bar-label{font-size:10px;color:var(--sub);width:24px;flex-shrink:0;}
  .pri-bar-track{width:50px;height:5px;background:rgba(0,0,0,.06);border-radius:999px;overflow:hidden;}
  .pri-bar-fill{height:100%;border-radius:999px;transition:width .5s ease;}
  .heat-fill{background:linear-gradient(90deg,#f59e0b,#ef4444);}
  .fit-fill{background:linear-gradient(90deg,var(--orange),var(--orange-deep));}
  .pri-bar-val{font-size:10px;color:var(--sub);font-weight:600;width:18px;}
  .pri-trend{display:flex;align-items:center;gap:6px;margin-left:auto;}
  .spark{opacity:.7;}
  .trend-label{font-size:10px;color:var(--sub);}
  .card-detail{
    max-height:0;overflow:hidden;transition:max-height .4s ease,padding .4s ease,margin .4s ease;
    padding:0 16px;margin-top:0;border-top:1px solid transparent;
  }
  .card-detail.open{
    max-height:2400px;padding:16px;margin-top:8px;border-top-color:var(--line);
    background:rgba(232,100,44,.02);
  }
  .detail-section{margin-bottom:14px;}
  .detail-section:last-child{margin-bottom:0;}
  .detail-title{
    font-size:11px;font-weight:600;color:var(--orange-deep);
    text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;
    display:flex;align-items:center;gap:6px;
  }
  .detail-title::before{content:"";width:3px;height:12px;background:var(--orange);border-radius:2px;}
  .detail-text{font-size:12.5px;line-height:1.7;color:var(--text);}
  .detail-text.marketing{background:rgba(232,100,44,.05);padding:10px 12px;border-radius:8px;border-left:3px solid var(--orange);}
  .detail-text.distribution{background:rgba(31,122,92,.06);padding:10px 12px;border-radius:8px;border-left:3px solid var(--teal);}
  .detail-text.platform{background:rgba(59,130,246,.05);padding:10px 12px;border-radius:8px;border-left:3px solid #3b82f6;}
  .detail-text.director{background:rgba(139,92,246,.06);padding:10px 12px;border-radius:8px;border-left:3px solid #8b5cf6;}
  .detail-titles{display:flex;flex-direction:column;gap:6px;}
  .detail-title-item{
    display:flex;align-items:flex-start;gap:8px;
    font-size:12.5px;line-height:1.6;padding:8px 10px;
    background:var(--bg);border-radius:8px;border:1px solid var(--line);
  }
  .title-num{
    flex-shrink:0;width:20px;height:20px;border-radius:50%;
    background:var(--orange);color:#fff;font-size:10px;font-weight:700;
    display:flex;align-items:center;justify-content:center;margin-top:1px;
  }
  .detail-tags{display:flex;flex-wrap:wrap;gap:6px;}
  .detail-tag{
    font-size:11px;padding:3px 10px;border-radius:999px;
    background:rgba(232,100,44,.08);color:var(--orange-deep);
    border:1px solid rgba(232,100,44,.15);
  }

  @media (max-width:520px){
    .brand-en{font-size:20px;letter-spacing:3px;}
    .tagline{font-size:15px;}
    .sec-title h2{font-size:18px;}
    .card-title{font-size:14.5px;}
    .rank{font-size:19px;min-width:28px;}
  }
'''

TPL = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE}</title>
<link rel="stylesheet" href="https://miaoda.feishu.cn/fonts/css2?family=Noto+Serif+SC:wght@500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap">
<style>
{css}
</style>
</head>
<body>

<header>
  <div class="h-wrap">
    <div class="brand-line">
      <span class="brand-en">{EN}</span>
      <span class="brand-cn">{CN} · <b>双平台热点借势看板</b></span>
    </div>
    <div class="meta-line">
      <span>{DATE_CN}</span><span class="dot"></span>
      <span>数据源：抖音热榜 / 小红书热搜</span><span class="dot"></span>
      <span>手动更新 · 每日上限 5 次</span>
    </div>
    <div class="update-box">
      <span class="update-info">今日已手动更新 <b id="manual-used">{MANUAL_USED}</b> / {MANUAL_LIMIT} 次</span>
      <a class="update-btn" href="update.html" target="_blank" rel="noopener">↻ 立即更新</a>
    </div>
    <div class="update-history" id="update-history">
      <span class="uh-label">更新时间记录</span>
      <span class="uh-list">{UPDATE_HISTORY}</span>
    </div>
    <div class="tagline">{TAGLINE}</div>
    <div class="assets">
{ASSETS}
    </div>
  </div>
</header>

<main class="wrap">

  <section class="sec-title">
    <h2>今日博主借势 TOP3</h2>
    <span>综合「平台热度 × 人设契合度 × 可执行性」选取，编导优先执行</span>
  </section>
  <section class="top3" id="top3"></section>

  <section class="sec-title">
    <h2>分平台热点 × 借势建议</h2>
    <span>完整收录当日双平台热榜（抖音 50 / 小红书 20），按各平台原始排名展示，不做筛选；每条建议以专业编导视角生成，发布前请运营与合规审核</span>
  </section>

  <div class="controls">
    <div class="tabs" id="tabs"></div>
    <div class="ctrl-row"><span class="ctrl-label">推荐类型</span><div class="chips" id="rec-chips"></div></div>
    <div class="ctrl-row"><span class="ctrl-label">内容类型</span><div class="chips" id="cat-chips"></div></div>
    <div class="ctrl-row ctrl-row-bottom">
      <div class="sort-wrap">
        <span class="ctrl-label">排序</span>
        <select class="sort-select" id="sort-select">
          <option value="rank">按排名</option>
          <option value="heat">按热度</option>
          <option value="priority">按优先级</option>
        </select>
      </div>
      <div class="export-wrap">
        <button class="export-btn" id="export-csv">导出 CSV</button>
        <button class="export-btn" id="export-md">复制为表格</button>
        <button class="export-btn" id="export-top3">复制 TOP3 简报</button>
      </div>
    </div>
    <div class="count-hint" id="count"></div>
  </div>

  <section id="list"></section>

  <footer>
    <b>数据说明</b>：本看板完整收录当日抖音热榜 50 条 / 小红书热搜 20 条，未做筛选，按各平台原始榜单排名展示；榜单抓取自公开聚合源（86TOOL hot-rank 抖音/小红书热搜榜），抓取时间 {DATE_CN} 上午；热度值为各源参考值，随榜单实时波动。<br>
    <b>借势建议</b>：基于博主「丁阿姨又瘦啦」的人设资历（胖 30 年阿姨第 3 次减脂成功 · 体脂 40%→23% · 气血丰盈地瘦）按话题分类生成；「借势角度」为强相关/可承接话题并附编导执行与内容模板，「不推荐借势」为弱相关话题并附客观理由，「克制建议」为敏感、医疗个案或社会事件，建议不借势或经合规审批后低调执行。所有建议遵循：不制造身材焦虑、不贩卖焦虑、不消费医疗个案、不承诺效果、不用极端减脂方法。<br>
    <b>更新机制</b>：本看板每日 10:00 自动重跑生成当日版本，数据与建议随当日热榜更新。
  </footer>
</main>

<script>
(function(){{
  "use strict";
  var DATA = {DATA};
  var CATS = {CATS};
  var PLATS = [
    {{key:"douyin", name:"抖音热点"}},
    {{key:"xhs", name:"小红书热搜"}}
  ];
  var state = {{plat:"douyin", rec:"全部", cat:"全部"}};
  var RECS = [
    {{key:"全部", label:"全部"}},
    {{key:"angle", label:"借势角度"}},
    {{key:"no", label:"不推荐借势"}},
    {{key:"guard", label:"克制建议"}}
  ];

  function el(tag, cls, html){{
    var e = document.createElement(tag);
    if(cls) e.className = cls;
    if(html !== undefined) e.innerHTML = html;
    return e;
  }}

  function top3HTML(){{
    var items = {TOP3};
    var box = document.getElementById("top3");
    items.forEach(function(it){{
      var c = el("div","t3");
      c.appendChild(el("div","no",it.no));
      c.appendChild(el("h3",null,it.title));
      c.appendChild(el("div","src",it.src));
      c.appendChild(el("div","tact","<b>编导策略</b>：" + it.tact));
      box.appendChild(c);
    }});
  }}

  function renderTabs(){{
    var box = document.getElementById("tabs");
    PLATS.forEach(function(p){{
      var t = el("button","tab",p.name + " <span style='font-size:11px;opacity:.75'>" + DATA[p.key].length + "</span>");
      if(p.key === state.plat) t.classList.add("active");
      t.onclick = function(){{ state.plat = p.key; state.cat = "全部"; renderAll(); }};
      box.appendChild(t);
    }});
  }}

  function renderRecChips(){{
    var box = document.getElementById("rec-chips");
    var arr = DATA[state.plat] || [];
    var cnt = {{}};
    arr.forEach(function(x){{ cnt[x.tag] = (cnt[x.tag]||0) + 1; }});
    RECS.forEach(function(r){{
      var n = r.key === "全部" ? arr.length : (cnt[r.key] || 0);
      if(r.key !== "全部" && n === 0) return;
      var ch = el("button","chip", r.label + "<span class='cnt'>" + n + "</span>");
      if(state.rec === r.key) ch.classList.add("active");
      ch.onclick = function(){{ state.rec = r.key; renderAll(); }};
      box.appendChild(ch);
    }});
  }}

  function renderCatChips(){{
    var box = document.getElementById("cat-chips");
    var arr = DATA[state.plat] || [];
    var cnt = {{}};
    arr.forEach(function(x){{ cnt[x.cat] = (cnt[x.cat]||0) + 1; }});
    var all = el("button","chip", "全部<span class='cnt'>" + arr.length + "</span>");
    if(state.cat === "全部") all.classList.add("active");
    all.onclick = function(){{ state.cat = "全部"; renderAll(); }};
    box.appendChild(all);
    CATS.forEach(function(c){{
      var n = cnt[c] || 0;
      if(n === 0) return;
      var ch = el("button","chip", c + "<span class='cnt'>" + n + "</span>");
      if(state.cat === c) ch.classList.add("active");
      ch.onclick = function(){{ state.cat = c; renderAll(); }};
      box.appendChild(ch);
    }});
  }}

  function sparkline(data, w, h){{
    if(!data || data.length < 2) return "";
    var max = Math.max.apply(null, data), min = Math.min.apply(null, data);
    var range = max - min || 1;
    var pts = data.map(function(v, i){{
      var x = (i / (data.length - 1)) * (w - 4) + 2;
      var y = h - 2 - ((v - min) / range) * (h - 4);
      return x.toFixed(1) + "," + y.toFixed(1);
    }}).join(" ");
    return '<svg class="spark" width="' + w + '" height="' + h + '"><polyline points="' + pts + '" fill="none" stroke="var(--orange)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  }}

  function cardHTML(it){{
    var rank = (it.rank < 10 ? "0" : "") + it.rank;
    var heatEl = it.heat ? el("span","heat",it.heat) : el("span","heat na","热榜");
    var cls = "angle", label = "借势角度";
    if(it.tag === "no"){{ cls = "angle no"; label = "不推荐借势"; }}
    if(it.tag === "guard"){{ cls = "angle guard"; label = "克制建议"; }}
    var priCls = "pri";
    if(it.priority >= 80) priCls += " pri-high";
    else if(it.priority >= 60) priCls += " pri-mid";
    var hasTpl = it.content_template && it.tag === "angle";
    var card = el("article","card" + (hasTpl ? " expandable" : ""));
    var head = el("div","card-head");
    head.appendChild(el("span","rank",rank));
    var tw = el("div");
    tw.style.minWidth = "0";
    tw.style.flex = "1";
    var searchUrl = "";
    if(it.plat === "douyin") searchUrl = "https://www.douyin.com/search/" + encodeURIComponent(it.title);
    else if(it.plat === "xhs") searchUrl = "https://www.xiaohongshu.com/search_result?keyword=" + encodeURIComponent(it.title);
    var titleEl = el("a","card-title",it.title);
    titleEl.href = searchUrl;
    titleEl.target = "_blank";
    titleEl.rel = "noopener noreferrer";
    titleEl.title = "点击跳转到" + (it.plat === "douyin" ? "抖音" : "小红书") + "搜索页";
    tw.appendChild(titleEl);
    var meta = el("div","card-meta");
    meta.appendChild(el("span","chip-cat",it.cat));
    meta.appendChild(heatEl);
    meta.appendChild(el("span",priCls,"优先级 " + it.priority));
    if(it.life_days > 1) meta.appendChild(el("span","life-badge","已上榜" + it.life_days + "天"));
    tw.appendChild(meta);
    head.appendChild(tw);
    if(hasTpl){{
      var expBtn = el("button","expand-btn","展开");
      expBtn.onclick = function(e){{
        e.stopPropagation();
        var detail = card.querySelector(".card-detail");
        var isOpen = detail.classList.contains("open");
        detail.classList.toggle("open");
        expBtn.textContent = isOpen ? "展开" : "收起";
        card.classList.toggle("expanded");
      }};
      head.appendChild(expBtn);
    }}
    card.appendChild(head);
    card.appendChild(el("p","sum",it.sum));
    var priBar = el("div","pri-bar");
    priBar.innerHTML = '<div class="pri-bar-item"><span class="pri-bar-label">热度</span><div class="pri-bar-track"><div class="pri-bar-fill heat-fill" style="width:' + it.heat_score*2 + '%"></div></div><span class="pri-bar-val">' + it.heat_score + '</span></div>' +
      '<div class="pri-bar-item"><span class="pri-bar-label">契合</span><div class="pri-bar-track"><div class="pri-bar-fill fit-fill" style="width:' + it.fit_score*2 + '%"></div></div><span class="pri-bar-val">' + it.fit_score + '</span></div>';
    if(it.heat_trend && it.heat_trend.length >= 2){{
      priBar.innerHTML += '<div class="pri-trend">' + sparkline(it.heat_trend, 80, 24) + '<span class="trend-label">热度趋势</span></div>';
    }}
    card.appendChild(priBar);
    var angleBox = el("div",cls);
    angleBox.innerHTML = "<b>" + label + "</b>　" + it.angle;
    var copyBtn = el("button","copy-btn","复制");
    copyBtn.onclick = function(e){{
      e.stopPropagation();
      var text = it.title + "\\n" + label + "：" + it.angle + "\\n优先级：" + it.priority + "（热度" + it.heat_score + "+契合" + it.fit_score + "）| 热度：" + it.heat + " | 分类：" + it.cat;
      navigator.clipboard.writeText(text).then(function(){{
        copyBtn.textContent = "已复制";
        copyBtn.classList.add("copied");
        setTimeout(function(){{ copyBtn.textContent = "复制"; copyBtn.classList.remove("copied"); }}, 1500);
      }});
    }};
    angleBox.appendChild(copyBtn);
    card.appendChild(angleBox);
    if(hasTpl){{
      var tpl = it.content_template;
      var detail = el("div","card-detail");
      var html = '<div class="detail-section"><div class="detail-title">内容标题建议</div><div class="detail-titles">';
      (tpl.titles || []).forEach(function(t, i){{ html += '<div class="detail-title-item"><span class="title-num">' + (i+1) + '</span>' + t + '</div>'; }});
      html += '</div></div>';
      if(tpl.copy_direction) html += '<div class="detail-section"><div class="detail-title">文案方向</div><div class="detail-text">' + tpl.copy_direction + '</div></div>';
      if(tpl.tags && tpl.tags.length) html += '<div class="detail-section"><div class="detail-title">推荐标签</div><div class="detail-tags">' + tpl.tags.map(function(t){{ return '<span class="detail-tag">' + t + '</span>'; }}).join("") + '</div></div>';
      if(tpl.director_notes) html += '<div class="detail-section"><div class="detail-title">编导执行</div><div class="detail-text director">' + tpl.director_notes + '</div></div>';
      if(tpl.distribution) html += '<div class="detail-section"><div class="detail-title">内容分发策略</div><div class="detail-text distribution">' + tpl.distribution + '</div></div>';
      if(tpl.marketing_analysis) html += '<div class="detail-section"><div class="detail-title">营销分析</div><div class="detail-text marketing">' + tpl.marketing_analysis + '</div></div>';
      if(tpl.platform_fit) html += '<div class="detail-section"><div class="detail-title">平台契合度</div><div class="detail-text platform">' + tpl.platform_fit + '</div></div>';
      detail.innerHTML = html;
      card.appendChild(detail);
    }}
    return card;
  }}

  function renderList(){{
    var box = document.getElementById("list");
    box.innerHTML = "";
    var arr = DATA[state.plat] || [];
    var list = arr.filter(function(x){{
      var okCat = state.cat === "全部" || x.cat === state.cat;
      var okRec = state.rec === "全部" || x.tag === state.rec;
      return okCat && okRec;
    }});
    var sortBy = document.getElementById("sort-select").value;
    if(sortBy === "heat"){{
      list.sort(function(a,b){{ return parseHeat(b.heat) - parseHeat(a.heat); }});
    }} else if(sortBy === "priority"){{
      list.sort(function(a,b){{ return b.priority - a.priority; }});
    }} else {{
      list.sort(function(a,b){{ return a.rank - b.rank; }});
    }}
    document.getElementById("count").textContent = "共 " + list.length + " 条";
    if(!list.length){{
      box.appendChild(el("div","empty","该分类下暂无条目"));
      return;
    }}
    list.forEach(function(it){{ box.appendChild(cardHTML(it)); }});
  }}

  function parseHeat(s){{
    if(!s) return 0;
    s = String(s).replace(/[^0-9.\u4e07\u4ebf]/g, "");
    if(s.indexOf("\u4e07") >= 0) return parseFloat(s) * 10000;
    if(s.indexOf("\u4ebf") >= 0) return parseFloat(s) * 100000000;
    return parseFloat(s) || 0;
  }}

  function getFilteredList(){{
    var arr = DATA[state.plat] || [];
    return arr.filter(function(x){{
      var okCat = state.cat === "全部" || x.cat === state.cat;
      var okRec = state.rec === "全部" || x.tag === state.rec;
      return okCat && okRec;
    }});
  }}

  function exportCSV(){{
    var list = getFilteredList();
    var platName = state.plat === "douyin" ? "抖音" : "小红书";
    var header = ["排名","标题","平台","热度","内容类型","推荐类型","优先级","借势建议","摘要"];
    var rows = list.map(function(it){{
      var tagLabel = it.tag === "angle" ? "借势角度" : (it.tag === "no" ? "不推荐借势" : "克制建议");
      return [it.rank, it.title, platName, it.heat, it.cat, tagLabel, it.priority, it.angle.replace(/"/g, "\\\"\\\""), it.sum.replace(/"/g, "\\\"\\\"")];
    }});
    var csv = "\\uFEFF" + [header].concat(rows).map(function(r){{
      return r.map(function(c){{ return "\\\"" + String(c).replace(/"/g, "\\\"\\\"") + "\\\""; }}).join(",");
    }}).join("\\n");
    var blob = new Blob([csv], {{type:"text/csv;charset=utf-8"}});
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = "博主借势_" + platName + "_" + new Date().toISOString().slice(0,10) + ".csv";
    a.click(); URL.revokeObjectURL(url);
  }}

  function exportMarkdown(){{
    var list = getFilteredList();
    var platName = state.plat === "douyin" ? "抖音" : "小红书";
    var md = "## " + platName + "热点借势建议（" + list.length + "条）\\n\\n";
    md += "| 排名 | 标题 | 热度 | 类型 | 推荐 | 优先级 | 借势建议 |\\n";
    md += "|---|---|---|---|---|---|---|\\n";
    list.forEach(function(it){{
      var tagLabel = it.tag === "angle" ? "✅借势" : (it.tag === "no" ? "❌不推荐" : "⚠️克制");
      md += "| " + it.rank + " | " + it.title + " | " + it.heat + " | " + it.cat + " | " + tagLabel + " | " + it.priority + " | " + it.angle + " |\\n";
    }});
    navigator.clipboard.writeText(md).then(function(){{
      var btn = document.getElementById("export-md");
      var old = btn.textContent; btn.textContent = "已复制到剪贴板";
      setTimeout(function(){{ btn.textContent = old; }}, 1500);
    }});
  }}

  function exportTop3(){{
    var items = {TOP3};
    var md = "## 今日博主借势 TOP3\\n\\n";
    items.forEach(function(it){{
      md += "### " + it.no + "：" + it.title + "\\n\\n";
      md += "- **来源**：" + it.src + "\\n";
      md += "- **编导策略**：" + it.tact + "\\n\\n";
    }});
    navigator.clipboard.writeText(md).then(function(){{
      var btn = document.getElementById("export-top3");
      var old = btn.textContent; btn.textContent = "已复制到剪贴板";
      setTimeout(function(){{ btn.textContent = old; }}, 1500);
    }});
  }}

  function renderAll(){{
    var t = document.getElementById("tabs");
    var rc = document.getElementById("rec-chips");
    var cc = document.getElementById("cat-chips");
    t.innerHTML = ""; rc.innerHTML = ""; cc.innerHTML = "";
    renderTabs(); renderRecChips(); renderCatChips(); renderList();
  }}

  try {{
    top3HTML();
    renderAll();
    document.getElementById("sort-select").addEventListener("change", renderList);
    document.getElementById("export-csv").addEventListener("click", exportCSV);
    document.getElementById("export-md").addEventListener("click", exportMarkdown);
    document.getElementById("export-top3").addEventListener("click", exportTop3);
  }} catch(e){{
    var box = document.getElementById("list");
    box.innerHTML = '<div class="empty">页面渲染异常：' + e.message + '</div>';
  }}
}})();
</script>
</body>
</html>
'''

META = {
    'title': '丁阿姨又瘦啦 × 抖音/小红书热点借势看板',
    'en': 'DING AYI', 'cn': '丁阿姨又瘦啦',
    'tagline': '气血丰盈地瘦 · 快乐老狗不走捷径 —— 博主 × 双平台每日热点结合',
    'assets': [
        ('人设：胖 30 年 · 第 3 次减脂成功 · 体脂 40%→23%', 0),
        ('数据：168cm · 130→108 斤（还在瘦）', 0),
        ('内容：真实减脂 / 饮食方法 / 测评打假 / 养生变美', 0),
        ('平台：小红书主阵地 · 抖音同步', 1),
        ('调性：真实 · 气血 · 快乐 · 不制造焦虑', 1),
    ],
}

def render(data_js, css):
    assets = '\n'.join('      <span class="asset%s">%s</span>' % (' on' if a[1] else '', a[0]) for a in META['assets'])
    cats = ["全部","时尚穿搭","体育赛事","影视综艺","情感话题","生活方式","知识科普","社会事件","科技财经","美食探店","娱乐八卦"]
    now = datetime.datetime.now()
    date_cn = '%d年%d月%d日 星期%s' % (now.year, now.month, now.day, '一二三四五六日'[now.weekday()])
    uh_items = []
    for h in reversed(update_history[-12:]):
        t = str(h.get('time', ''))[:16]
        typ = '手动' if h.get('type') == 'manual' else '自动'
        uh_items.append('<span class="uh-item"><span class="uh-time">%s</span> <span class="uh-type">%s</span></span>' % (t, typ))
    uh_html = '（暂无更新记录）' if not uh_items else ''.join(uh_items)
    out = TPL.format(
        TITLE=META['title'], EN=META['en'], CN=META['cn'], TAGLINE=META['tagline'],
        ASSETS=assets, DATA=data_js, DATE_CN=date_cn,
        MANUAL_USED=manual_today, MANUAL_LIMIT=MANUAL_LIMIT,
        UPDATE_HISTORY=uh_html,
        CATS=json.dumps(cats, ensure_ascii=False),
        TOP3=json.dumps(TOP3, ensure_ascii=False),
        css=css,
    )
    return out

if __name__ == '__main__':
    html = build()
    out_path = os.path.join(root, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print('written:', out_path, len(html))
