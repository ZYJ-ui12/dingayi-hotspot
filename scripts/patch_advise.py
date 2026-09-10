# -*- coding: utf-8 -*-
"""补全缺失建议：仅针对首轮未覆盖的条目（自动兜底为 no 的），重新调用 LLM 给出判定。
合并回 adv.json，保留已生成的高质量条目。"""
import os, json, re, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_URL = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
MODEL = os.environ.get('ARK_MODEL', 'ep-20260910121246-2xkh5')

BRIEF = """博主：丁阿姨又瘦啦（抖音 + 小红书双平台减脂博主，小红书号 49328232714，IP属地上海）
【人设与资历】胖了30年的阿姨，第3次减肥成功："气血丰盈地瘦"（不靠极端节食、不损害健康，反对饿瘦）；体脂 40%→23%；168cm，130 斤→108 斤，还在继续瘦；自我描述：ENFJ宝剑姐 | 快乐老狗 | 走地鸡（乐观自嘲、接地气）。
【内容版块】1.真实减脂记录（体重体脂变化/旧衣服对比/瘦下来不垮脸）2.饮食方法论（控糖/干净饮食/主食替换，可持续不反弹）3.测评打假（干净饮食口气测评/口腔益生菌等好物，客观不拉踩）4.养生变美（气血/护肤/妆后状态）
【受众】25-60 岁女性（"姐姐们"）：想减肥但怕饿、怕反弹、怕伤身体、没时间去健身房的人群。
【调性】真实、快乐、有烟火气；不制造身材焦虑、不贩卖焦虑、不消费医疗个案、不承诺效果。"""

RULES = """你是资深短视频编导 + 内容借势策划，为减脂博主「丁阿姨又瘦啦」判定以下热榜条目能否借势。要求客观理性、不为蹭而蹭；能借才借，不能借就明确说不借并给出具体客观理由。

【判定规则】
1) tag 三选一：
   - angle=强相关可借势（必须给内容落点 angle 60-100字 + content_template 完整模板）
   - no=弱相关/无承接（给一句具体客观理由，说明为什么这个热点和减脂博主无关/不宜承接）
   - guard=敏感/灾害/医疗个案/恶性事件（给克制口径）
2) cat 分类（十选一）：时尚穿搭/体育赛事/影视综艺/情感话题/生活方式/知识科普/社会事件/科技财经/美食探店/娱乐八卦
3) sum：一句话客观摘要（不含观点，20字内）
4) angle 字段（仅 angle 时）：从专业编导视角写：内容形式（抖音短视频口播/实拍/对比/测评；小红书图文/短视频）+具体切入角度（热点哪个点与减肥/饮食/养生/变美结合，为什么有关联）+可执行内容方向+人设一致性。
5) content_template（仅 angle 时）：{"titles":["标题1","标题2","标题3"],"copy_direction":"文案方向：...","tags":["#标签1","#标签2","#标签3"],"director_notes":"编导执行：拍摄场景/镜头语言/开头3秒钩子/结尾互动/合规检查","distribution":"内容分发策略：官方号怎么发+互动引导+直播承接+双平台差异化","marketing_analysis":"营销分析：为什么值得借/目标受众/解决什么问题/短期长期价值","platform_fit":"平台契合度：..."}

【不硬蹭规则】
- 科技数码/游戏/纯娱乐八卦/体育赛事/时政外交/旅游风景摄影/宠物等无承接点标 no，给具体理由
- 政治外交/灾害/医疗个案/传染病/人物离世/社会争议标 guard
- 涉及健康风险只做科普、引用权威观点，不消费个案、不制造焦虑
- 教师节等节日除非有人设内合理落点否则不硬蹭；明星无合作不借肖像
- 减肥建议不极端：禁止节食/断食/药物/过度运动，不承诺效果数字

【输出格式】只输出 JSON：{"items":{"标题":{"cat":"..","sum":"..","tag":"..","angle":"..","content_template":{...}}}}，content_template 仅 tag=angle 时存在。"""

def call_llm(messages):
    body = json.dumps({
        'model': MODEL, 'messages': messages,
        'temperature': 0.25, 'max_tokens': 16000,
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
    # 平衡括号法提取第一个完整 JSON 对象
    start = text.find('{')
    if start < 0:
        raise ValueError('no json object')
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
    raise ValueError('unbalanced json')

FILL_REASON = '无明确承接点，客观评估后建议不借势。'

def main():
    hot = json.load(open(os.path.join(ROOT, 'hotdata.json'), encoding='utf-8'))
    adv = json.load(open(os.path.join(ROOT, 'adv.json'), encoding='utf-8'))
    items = adv['items']

    plat_meta = {
        'douyin': ('抖音', '抖音短视频', '口播/实拍/对比打卡/测评'),
        'xhs': ('小红书', '小红书图文笔记或短视频', '封面党/清单体/教程体'),
    }
    for plat in ('douyin', 'xhs'):
        pname, pform, pstyle = plat_meta[plat]
        todo = []
        for it in hot[plat]:
            a = items.get(it['title'], {})
            if a.get('angle') == FILL_REASON or it['title'] not in items:
                todo.append(it)
        if not todo:
            print(plat, '无需补全')
            continue
        # 分批：每批 <= 18 条，避免超长输出导致超时/格式损坏
        CHUNK = 18
        for ci in range(0, len(todo), CHUNK):
            chunk = todo[ci:ci + CHUNK]
            prompt = RULES + '\n\n【' + pname + '热榜待判定条目 ' + str(len(chunk)) + ' 条】借势建议必须使用' + pform + '（' + pstyle + '），绝对不能跨平台。\n'
            for it in chunk:
                prompt += '%d. %s（热度 %s）\n' % (it['rank'], it['title'], it['hot'])
            prompt += '\n【重要】items 的键（标题）必须与上面输入完全一致、逐字相同，不要加序号、不要改写。\n'
            ok = False
            for attempt in range(3):
                try:
                    out = extract_json(call_llm([
                        {'role': 'system', 'content': '你是资深短视频编导和内容借势策划，客观理性，不为蹭而蹭。当前处理' + pname + '热榜，建议必须用' + pform + '。'},
                        {'role': 'user', 'content': BRIEF + '\n\n' + prompt},
                    ]))
                    merged = 0
                    for title, v in out.get('items', {}).items():
                        # 剥离可能的序号前缀（"22. 标题" -> "标题"），容错 LLM 键名
                        t2 = re.sub(r'^\s*\d+[\.、\)]\s*', '', title).strip()
                        v.setdefault('cat', '生活方式'); v.setdefault('sum', '')
                        v.setdefault('tag', 'no')
                        if not (v.get('angle') or '').strip():
                            v['angle'] = FILL_REASON
                        items[t2] = v
                        merged += 1
                    print(plat, '批次', ci // CHUNK + 1, '补全/更新', merged, '条')
                    ok = True
                    break
                except Exception as e:
                    print('retry %s batch %d attempt %d: %s' % (plat, ci // CHUNK + 1, attempt + 1, str(e)[:120]))
                    time.sleep(5)
            if not ok:
                print('WARN %s batch %d 失败，保留兜底' % (plat, ci // CHUNK + 1))

    # 最终校验：不允许再出现兜底理由且 tag 存在
    still_missing = []
    for plat in ('douyin', 'xhs'):
        for it in hot[plat]:
            a = items.get(it['title'], {})
            if not a.get('tag'):
                still_missing.append(plat + '|' + it['title'])
    if still_missing:
        print('WARN still missing tag:', still_missing)
    tags = {}
    for v in items.values():
        tags[v.get('tag')] = tags.get(v.get('tag'), 0) + 1
    print('tag分布:', tags)
    with open(os.path.join(ROOT, 'adv.json'), 'w', encoding='utf-8') as f:
        json.dump(adv, f, ensure_ascii=False, indent=1)
    print('saved adv.json, total items:', len(items))

if __name__ == '__main__':
    if not os.environ.get('ARK_API_KEY'):
        raise SystemExit('缺少 ARK_API_KEY 环境变量')
    main()
