# -*- coding: utf-8 -*-
"""博主看板构建（简洁初版）：读取 hotdata.json + adv.json -> 生成 repo根/index.html
独立于品牌库的博主看板（丁阿姨又瘦啦 × 抖音/小红书双平台），编导视角借势建议。
"""
import json, io, sys, os, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
base = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(base)

hot = json.load(open(os.path.join(root, 'hotdata.json'), encoding='utf-8'))
adv_data = json.load(open(os.path.join(root, 'adv.json'), encoding='utf-8'))
adv = adv_data['items']
TOP3 = adv_data.get('top3', [])

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

CSS = r'''
  :root{
    --ink:#2B211A; --bg:#FBF6EF; --card:#FFFFFF;
    --orange:#E8642C; --orange-deep:#C24A1C; --red:#B03A2E;
    --text:#1A1B1C; --sub:#6B7280; --line:#EDE3D6;
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  body{
    background:var(--bg);color:var(--text);
    font-family:'Noto Sans SC','PingFang SC','Microsoft YaHei',sans-serif;
    font-weight:400;line-height:1.6;
  }
  .wrap{max-width:960px;margin:0 auto;padding:0 20px 48px;}

  /* ===== 头部 ===== */
  header{
    background:linear-gradient(135deg,#2E2118 0%,#1C120B 100%);
    color:#FBF3EA;padding:28px 0 24px;border-bottom:3px solid var(--orange);
  }
  .h-wrap{max-width:960px;margin:0 auto;padding:0 20px;}
  .brand-line{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;}
  .brand-en{
    font-family:'Noto Serif SC',serif;font-size:22px;font-weight:700;
    letter-spacing:4px;color:#FBF3EA;
  }
  .brand-cn{font-size:14px;letter-spacing:2px;color:#D9C6B6;}
  .brand-cn b{color:var(--orange);font-weight:500;}
  .meta-line{
    margin-top:10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;
    font-size:12px;color:#BFAE9E;
  }
  .meta-line .dot{width:4px;height:4px;border-radius:50%;background:var(--orange);display:inline-block;}
  .tagline{
    margin-top:12px;font-family:'Noto Serif SC',serif;font-size:16px;color:#FBF3EA;
    letter-spacing:2px;
  }
  .assets{margin-top:10px;display:flex;flex-wrap:wrap;gap:6px;}
  .asset{
    font-size:11px;border:1px solid rgba(251,243,234,.35);color:#D9C6B6;
    border-radius:999px;padding:2px 10px;letter-spacing:.5px;
  }
  .asset.on{border-color:var(--orange);color:var(--orange);}

  /* ===== 章节标题 ===== */
  .sec-title{margin:30px 0 12px;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;}
  .sec-title h2{font-family:'Noto Serif SC',serif;font-size:19px;font-weight:600;color:var(--ink);}
  .sec-title span{font-size:12px;color:var(--sub);}

  /* ===== TOP3 ===== */
  .top3{display:flex;gap:14px;flex-wrap:wrap;}
  .t3{
    flex:1 1 280px;min-width:0;background:var(--card);border:1px solid var(--line);
    border-top:3px solid var(--orange);border-radius:10px;padding:16px;
    display:flex;flex-direction:column;gap:6px;
  }
  .t3 .no{font-family:'Noto Serif SC',serif;font-size:12px;color:var(--orange-deep);letter-spacing:1px;}
  .t3 h3{font-size:15px;font-weight:600;color:var(--ink);}
  .t3 .src{font-size:11.5px;color:var(--sub);}
  .t3 .tact{font-size:12.5px;color:var(--text);border-top:1px dashed var(--line);padding-top:8px;margin-top:2px;}
  .t3 .tact b{color:var(--orange-deep);font-weight:600;}

  /* ===== 平台切换 ===== */
  .tabs{display:flex;gap:8px;margin-bottom:14px;}
  .tab{
    font-size:13px;padding:6px 18px;border-radius:8px;border:1px solid var(--line);
    background:#FFFDF9;color:var(--ink);cursor:pointer;transition:all .15s;
    font-family:'Noto Sans SC',sans-serif;
  }
  .tab.active{background:var(--ink);color:#FBF3EA;border-color:var(--ink);}

  /* ===== 热点卡片 ===== */
  .card{
    background:var(--card);border:1px solid var(--line);border-radius:10px;
    padding:14px 16px;margin-bottom:10px;
  }
  .card-head{display:flex;gap:12px;align-items:flex-start;}
  .rank{
    font-family:'Noto Serif SC',serif;font-size:20px;font-weight:700;color:var(--ink);
    line-height:1;min-width:30px;padding-top:2px;
  }
  .card-title{font-size:15px;font-weight:600;color:var(--ink);line-height:1.4;}
  a.card-title{text-decoration:none;cursor:pointer;transition:color .2s;}
  a.card-title:hover{color:var(--orange);text-decoration:underline;text-underline-offset:3px;}
  .card-meta{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:4px;}
  .chip-cat{font-size:11px;background:rgba(43,33,26,.08);color:var(--ink);border-radius:999px;padding:1px 9px;}
  .heat{
    font-size:11px;background:rgba(232,100,44,.14);color:var(--orange-deep);
    border-radius:999px;padding:1px 9px;font-weight:500;
  }
  .heat.na{background:rgba(107,114,128,.12);color:var(--sub);}
  .tag-badge{
    font-size:11px;padding:1px 9px;border-radius:999px;font-weight:500;
  }
  .tag-angle{background:rgba(31,122,92,.12);color:#176A4E;}
  .tag-no{background:rgba(107,114,128,.12);color:var(--sub);}
  .tag-guard{background:rgba(176,58,46,.1);color:var(--red);}
  .sum{font-size:12.5px;color:var(--sub);margin-top:8px;line-height:1.65;}
  .angle{
    margin-top:8px;background:#FCF5EE;border-left:3px solid var(--orange);
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
    margin-top:30px;border-top:1px solid var(--line);padding-top:14px;
    font-size:11.5px;color:var(--sub);line-height:1.8;
  }
  footer b{color:var(--ink);font-weight:600;}

  @media (max-width:520px){
    .brand-en{font-size:18px;letter-spacing:3px;}
    .tagline{font-size:14px;}
    .sec-title h2{font-size:17px;}
    .card-title{font-size:14px;}
    .rank{font-size:18px;min-width:26px;}
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
      <span>每日 10:00 / 15:00 自动更新</span>
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
    <span>完整收录当日双平台热榜（抖音 50 / 小红书 20），按各平台原始排名展示</span>
  </section>

  <div class="tabs" id="tabs"></div>
  <section id="list"></section>

  <footer>
    <b>数据说明</b>：本看板完整收录当日抖音热榜 50 条 / 小红书热搜 20 条，未做筛选，按各平台原始榜单排名展示；榜单抓取自公开聚合源，热度值为各源参考值，随榜单实时波动。<br>
    <b>借势建议</b>：基于博主「丁阿姨又瘦啦」的人设资历按话题分类生成；「借势角度」为强相关/可承接话题，「不推荐借势」为弱相关话题并附客观理由，「克制建议」为敏感或社会事件，建议经合规审批后低调执行。所有建议遵循：不制造身材焦虑、不贩卖焦虑、不消费医疗个案、不承诺效果。<br>
    <b>更新机制</b>：本看板每日 10:00 / 15:00（北京时间）自动重跑生成当日版本。
  </footer>
</main>

<script>
(function(){
  "use strict";
  var DATA = {DATA};
  var PLATS = [
    {key:"douyin", name:"抖音热点"},
    {key:"xhs", name:"小红书热搜"}
  ];
  var state = {plat:"douyin"};

  function el(tag, cls, html){
    var e = document.createElement(tag);
    if(cls) e.className = cls;
    if(html !== undefined) e.innerHTML = html;
    return e;
  }

  function top3HTML(){
    var items = {TOP3};
    var box = document.getElementById("top3");
    items.forEach(function(it){
      var c = el("div","t3");
      c.appendChild(el("div","no",it.no));
      c.appendChild(el("h3",null,it.title));
      c.appendChild(el("div","src",it.src));
      c.appendChild(el("div","tact","<b>编导策略</b>：" + it.tact));
      box.appendChild(c);
    });
  }

  function renderTabs(){
    var box = document.getElementById("tabs");
    PLATS.forEach(function(p){
      var t = el("button","tab",p.name + " <span style='font-size:11px;opacity:.75'>" + DATA[p.key].length + "</span>");
      if(p.key === state.plat) t.classList.add("active");
      t.onclick = function(){ state.plat = p.key; renderAll(); };
      box.appendChild(t);
    });
  }

  function cardHTML(it){
    var rank = (it.rank < 10 ? "0" : "") + it.rank;
    var heatEl = it.heat ? el("span","heat",it.heat) : el("span","heat na","热榜");
    var cls = "angle", label = "借势角度", tagCls = "tag-badge tag-angle", tagLabel = "借势";
    if(it.tag === "no"){ cls = "angle no"; label = "不推荐借势"; tagCls = "tag-badge tag-no"; tagLabel = "不推荐"; }
    if(it.tag === "guard"){ cls = "angle guard"; label = "克制建议"; tagCls = "tag-badge tag-guard"; tagLabel = "克制"; }
    var card = el("article","card");
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
    tw.appendChild(titleEl);
    var meta = el("div","card-meta");
    meta.appendChild(el("span","chip-cat",it.cat));
    meta.appendChild(heatEl);
    meta.appendChild(el("span",tagCls,tagLabel));
    tw.appendChild(meta);
    head.appendChild(tw);
    card.appendChild(head);
    card.appendChild(el("p","sum",it.sum));
    var angleBox = el("div",cls);
    angleBox.innerHTML = "<b>" + label + "</b>　" + it.angle;
    card.appendChild(angleBox);
    return card;
  }

  function renderList(){
    var box = document.getElementById("list");
    box.innerHTML = "";
    var arr = DATA[state.plat] || [];
    arr.forEach(function(it){ box.appendChild(cardHTML(it)); });
  }

  function renderAll(){
    var t = document.getElementById("tabs");
    t.innerHTML = "";
    renderTabs();
    renderList();
  }

  try {
    top3HTML();
    renderAll();
  } catch(e){
    var box = document.getElementById("list");
    box.innerHTML = '<div style="text-align:center;color:var(--sub);padding:40px 0;">页面渲染异常：' + e.message + '</div>';
  }
})();
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

def build():
    data = {}
    for plat in ('douyin', 'xhs'):
        rows = []
        for it in hot[plat]:
            a = adv[it['title']]
            rows.append({
                'rank': it['rank'], 'title': it['title'], 'cat': a.get('cat', '生活方式'),
                'heat': fmt_hot(it['hot']), 'sum': a.get('sum', ''),
                'tag': a.get('tag', 'no'), 'angle': a.get('angle', '无明确承接点，客观评估后建议不借势。'),
                'plat': plat,
            })
        rows.sort(key=lambda x: x['rank'])
        data[plat] = rows
    js = json.dumps(data, ensure_ascii=False)
    return render(js, CSS)

def render(data_js, css):
    assets = '\n'.join('      <span class="asset%s">%s</span>' % (' on' if a[1] else '', a[0]) for a in META['assets'])
    now = datetime.datetime.now()
    date_cn = '%d年%d月%d日 星期%s' % (now.year, now.month, now.day, '一二三四五六日'[now.weekday()])
    out = TPL
    out = out.replace('{TITLE}', META['title'])
    out = out.replace('{EN}', META['en'])
    out = out.replace('{CN}', META['cn'])
    out = out.replace('{TAGLINE}', META['tagline'])
    out = out.replace('{ASSETS}', assets)
    out = out.replace('{DATA}', data_js)
    out = out.replace('{DATE_CN}', date_cn)
    out = out.replace('{TOP3}', json.dumps(TOP3, ensure_ascii=False))
    out = out.replace('{css}', css)
    return out

if __name__ == '__main__':
    html = build()
    out_path = os.path.join(root, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print('written:', out_path, len(html))
