# -*- coding: utf-8 -*-
"""博主借势建议生成：读取 repo根/hotdata.json（抖音+小红书），调用方舟 Ark API
按「专业编导视角 + 客观不硬蹭」为博主丁阿姨又瘦啦生成每日热榜借势建议 -> repo根/adv.json
adv.json 结构:
{
  "items": { "标题": {"cat":"..","sum":"..","tag":"angle|no|guard","angle":"..","content_template":{...}}, ... },
  "top3": [ {"no":"借势机会 01","title":"..","src":"..","tact":".."} x3 ]
}
"""
import os, json, re, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_URL = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
MODEL = os.environ.get('ARK_MODEL', 'ep-20260910121246-2xkh5')

BRIEF = """博主：丁阿姨又瘦啦（抖音 + 小红书双平台减脂博主，小红书号 49328232714，IP属地上海）
【人设与资历】
- 胖了30年的阿姨，第3次减肥成功："气血丰盈地瘦"（不靠极端节食、不损害健康，反对饿瘦）
- 体脂从 40% 降到 23%；168cm，从 130 斤减到 108 斤，目前还在继续瘦
- 自我描述：ENFJ宝剑姐 | 快乐老狗 | 走地鸡（乐观自嘲、接地气、有烟火气）
【内容版块】
1. 真实减脂记录：体重/体脂变化、旧衣服对比、瘦下来脸不垮不松（"不垮无纹"）
2. 饮食方法论：控糖、干净饮食、主食替换、家常做法，强调可持续不反弹
3. 测评打假：干净饮食口气测评（"你以为的干净饮食到底有多臭"）、口腔益生菌等好物测评，客观不拉踩
4. 养生变美：气血、护肤、妆后状态（如"妆后垮脸馒化"）、年前变美冲刺
【受众】25-60 岁女性为主（"姐姐们"）：想减肥但怕饿、怕反弹、怕伤身体、没时间去健身房的人群
【调性】真实、快乐、有烟火气；不制造身材焦虑、不贩卖焦虑、不消费医疗个案、不承诺效果"""

RULES = """你是资深短视频编导 + 内容借势策划，为减脂博主「丁阿姨又瘦啦」生成每日热榜借势建议。要求客观理性、有策略深度，不为蹭而蹭；能借才借，不能借就明确说不借并给出理由。

【核心规则】
1) tag 三选一：
   - angle=强相关可借势（必须给具体内容落点 + content_template 内容模板 + director_notes 编导执行）
   - no=弱相关/无承接（给客观理由，说明为什么不适合借势，不生成 content_template）
   - guard=敏感/灾害/医疗个案/恶性事件（给克制口径，不借势不评论，不生成 content_template）
2) cat 分类（十选一）：时尚穿搭/体育赛事/影视综艺/情感话题/生活方式/知识科普/社会事件/科技财经/美食探店/娱乐八卦
3) sum：一句话客观摘要（不含观点，20字内）

【angle 文案要求 —— 专业编导视角，必须有具体执行，禁止泛泛而谈】
每条 angle 建议的 angle 字段（60-100字）直接写策略，包含：
- 内容形式：抖音=短视频（口播/实拍/对比打卡/测评），小红书=图文笔记或短视频（封面党/清单体/教程体）
- 具体切入角度：从热点里提取哪个情绪/场景/人群/话题点与博主减脂人设结合，说明为什么这个热点和「减肥/饮食/养生/变美」有关联
- 可执行内容方向：如"减脂期怎么吃火锅的点菜清单"、"干净饮食口气测评"、"旧衣服对比打卡"
- 人设一致性：是否符合"气血丰盈地瘦、快乐老狗、不贩卖焦虑"的调性

【content_template 内容模板 —— 仅 angle 类型必须生成】
{
  "titles": ["标题1","标题2","标题3"],  // 3个内容标题，符合平台调性（抖音口语化有钩子，小红书种草感/清单感）
  "copy_direction": "文案方向：...",  // 50-80字，开头钩子+中间干货+结尾互动，结合平台用户阅读习惯
  "tags": ["#标签1","#标签2","#标签3"],  // 3-5个标签：平台热搜词+博主垂直词（减脂/控糖/养生/气血）+品类词
  "director_notes": "编导执行：...",  // 60-100字，必须具体：拍摄场景（厨房/客厅/菜市场/镜子前/称重台）、镜头语言（口播怼脸/前后对比/细节特写/字幕钩子/节奏）、开头3秒钩子怎么设计、结尾怎么引导互动，以及人设/合规检查（不夸张效果、不极端节食、测评客观）
  "distribution": "内容分发策略：...",  // 80-120字，官方号怎么发（时间点、发布节奏、如何借话题）+ 互动引导（评论区置顶问题/打卡话题）+ 直播承接（如何把热点话题引流到减脂直播间），双平台（抖音+小红书）如何差异化分发
  "marketing_analysis": "营销分析：...",  // 80-120字，为什么这个热点值得借势、目标受众、传播逻辑、对博主能解决什么问题（涨粉/互动/人设强化/带货转化）、短期与长期价值
  "platform_fit": "平台契合度：..."  // 60-100字，分析热点在当前平台的传播特点、用户参与方式、内容形式偏好，以及博主内容如何适配平台调性与算法逻辑
}

【不硬蹭规则】
- 科技数码（苹果发布会等）/游戏/纯娱乐八卦/体育赛事/时政外交/旅游风景/宠物等无承接点的标 no，给客观理由
- 政治外交/灾害/医疗个案/传染病/人物离世/社会争议标 guard，不借势
- 涉及健康风险的话题（如肥胖致病）：只能做科普向内容、引用医生或权威观点，绝不消费个案、不制造焦虑、不夸大后果
- 任何减肥建议不极端：禁止节食/断食/药物/过度运动等危险方法，不承诺具体效果数字
- 教师节等节日：除非有人设内合理落点，否则不硬蹭；明星无合作不借肖像

【TOP3 生成】
top3：选今日最适合借势的 3 条（综合热度×契合度×可执行性），每项：
- no: "借势机会 01/02/03"
- title: 短标题（8字内，有编导策略感）
- src: 引用上榜话题与热度（如"抖音「我选择火锅作为入秋仪式感」762万"）
- tact: 策略80-120字，说明核心创意、内容形式、平台、镜头怎么拍、预期效果

【输出格式】
只输出 JSON，不要多余文字。结构：
{"items":{"标题":{"cat":"..","sum":"..","tag":"..","angle":"..","content_template":{...}}},"top3":[...]}
注意：content_template 仅当 tag=angle 时存在，tag=no/guard 时不生成。"""

def call_llm(messages):
    body = json.dumps({
        'model': MODEL,
        'messages': messages,
        'temperature': 0.3,
        'max_tokens': 14000,
    }).encode('utf-8')
    req = urllib.request.Request(API_URL, data=body, method='POST', headers={
        'Authorization': 'Bearer ' + os.environ['ARK_API_KEY'],
        'Content-Type': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.loads(r.read().decode('utf-8'))
    return resp['choices'][0]['message']['content']

def extract_json(text):
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text.strip())
    m = re.search(r'\{.*\}', text, re.S)
    raw = m.group(0)
    return json.loads(raw)

def main():
    hot = json.load(open(os.path.join(ROOT, 'hotdata.json'), encoding='utf-8'))
    items, top3 = {}, []
    plat_meta = {
        'douyin': ('抖音', '抖音短视频', '口播/实拍/对比打卡/测评'),
        'xhs': ('小红书', '小红书图文笔记或短视频', '封面党/清单体/教程体'),
    }
    for plat in ('douyin', 'xhs'):
        pname, pform, pstyle = plat_meta[plat]
        rows = hot[plat]
        prompt = RULES + '\n\n【' + pname + '热榜 ' + str(len(rows)) + ' 条】以下所有条目均来自' + pname + '平台，借势建议必须使用' + pform + '形式（' + pstyle + '），绝对不能跨平台。\n'
        for it in rows:
            prompt += '%d. %s（热度 %s）\n' % (it['rank'], it['title'], it['hot'])
        for attempt in range(3):
            try:
                out = extract_json(call_llm([
                    {'role': 'system', 'content': '你是资深短视频编导和内容借势策划，客观理性，不为蹭而蹭。当前处理的是' + pname + '热榜，所有建议必须用' + pform + '。'},
                    {'role': 'user', 'content': BRIEF + '\n\n' + prompt},
                ]))
                for title, v in out['items'].items():
                    v.setdefault('cat', '生活方式'); v.setdefault('sum', '')
                    v.setdefault('tag', 'no'); v.setdefault('angle', '无明确承接点，客观评估后建议不借势。')
                    items[title] = v
                if plat == 'xhs':  # 在最后一个平台收集 top3
                    top3 = out.get('top3', [])[:3]
                break
            except Exception as e:
                print('retry %s attempt %d: %s' % (plat, attempt + 1, e))
                time.sleep(5)
        else:
            raise SystemExit('LLM 建议生成失败: ' + plat)

    # 校验覆盖，缺失条目自动补 fallback（不中断）
    missing = []
    for plat in ('douyin', 'xhs'):
        for it in hot[plat]:
            if it['title'] not in items:
                missing.append(plat + '|' + it['title'])
                items[it['title']] = {
                    'cat': '生活方式', 'sum': it['title'], 'tag': 'no',
                    'angle': '无明确承接点，客观评估后建议不借势。',
                }
    if missing:
        print('WARN missing %d items, auto-filled as no-recommend:' % len(missing), missing[:5])
    print('advice coverage OK:', sum(len(v) for v in hot.values()), 'items')
    out = {'items': items, 'top3': top3}
    with open(os.path.join(ROOT, 'adv.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('saved', os.path.join(ROOT, 'adv.json'))

if __name__ == '__main__':
    if not os.environ.get('ARK_API_KEY'):
        raise SystemExit('缺少 ARK_API_KEY 环境变量')
    main()
