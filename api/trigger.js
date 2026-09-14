// Vercel Serverless Function: 触发 GitHub Actions workflow_dispatch
// 部署后在 Vercel Project Settings → Environment Variables 添加 GITHUB_TOKEN
// 国内可直接访问，token 存服务端不进前端

export default async function handler(req, res) {
  // CORS：允许看板页面跨域调用
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    return res.status(500).json({ ok: false, error: '服务端未配置 GITHUB_TOKEN' });
  }

  const REPO = 'ZYJ-ui12/dingayi-hotspot';
  const WORKFLOW = 'daily.yml';

  try {
    const r = await fetch(
      `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
      {
        method: 'POST',
        headers: {
          Authorization: `token ${token}`,
          Accept: 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
          'User-Agent': 'dingayi-trigger',
        },
        body: JSON.stringify({ ref: 'main' }),
      }
    );

    if (r.status === 204) {
      return res.status(200).json({ ok: true });
    }

    const text = await r.text();
    let msg = `GitHub ${r.status}`;
    try {
      const j = JSON.parse(text);
      if (j && j.message) msg = j.message;
    } catch (e) {}
    return res.status(502).json({ ok: false, error: msg });
  } catch (e) {
    return res.status(500).json({ ok: false, error: String(e) });
  }
}
