# 丁阿姨又瘦啦 × 抖音/小红书热点借势看板

独立于品牌库（拉夫劳伦/维密 hotspot-dashboards）的博主热点看板。

- 线上地址：<https://zyj-ui12.github.io/dingayi-hotspot/>
- 数据源：86TOOL hot-rank（抖音热榜 50 / 小红书热搜 20）
- 更新机制：纯手动更新——看板顶部「立即更新」按钮打开更新加载页（`update.html`，含步骤进度与 3～6 分钟预计时间提示），再前往 GitHub Actions 手动触发；每次计 1 次、每日上限 5 次；页面展示更新时间记录。
- 建议原则：专业编导视角、客观理性、不为蹭而蹭；不制造身材焦虑、不消费医疗个案、不承诺效果、不用极端减脂方法。

## 目录
- `scripts/fetch_hot.py` — 抓取双平台热榜 → `hotdata.json`
- `scripts/llm_advise.py` — 方舟 LLM 生成编导视角借势建议 → `adv.json`
- `scripts/build.py` — 构建 `index.html` 看板
- `history/` — 每日热榜快照（热点生命周期追踪）
