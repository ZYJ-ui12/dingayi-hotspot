// ============================================================
// 丁阿姨又瘦啦 · 看板更新触发器（Cloudflare Worker）
// 作用：代理 GitHub Actions workflow_dispatch，
//       让看板用户无需 GitHub 账号即可点击触发更新。
// 部署：Cloudflare Workers → Create Worker → 粘贴本代码 →
//       Settings → Variables → 添加加密变量 GITHUB_TOKEN（你的 GitHub PAT，需 repo 权限）
// 防刷依赖 GitHub workflow 每日上限 5 次，无需额外密钥
// ============================================================

// 允许跨域调用的来源（看板域名）
const ALLOWED_ORIGINS = [
  'https://zyj-ui12.github.io',
];

// 目标仓库与 workflow
const REPO = 'ZYJ-ui12/dingayi-hotspot';
const WORKFLOW = 'daily.yml';

export default {
  async fetch(request, env) {
    // CORS 预检
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders(request) });
    }

    const headers = corsHeaders(request);

    // 仅接受 POST
    if (request.method !== 'POST') {
      return new Response(
        JSON.stringify({ ok: false, error: 'Method not allowed' }),
        { status: 405, headers }
      );
    }

    const githubToken = env.GITHUB_TOKEN;
    if (!githubToken) {
      return new Response(
        JSON.stringify({ ok: false, error: '服务端未配置 GITHUB_TOKEN' }),
        { status: 500, headers }
      );
    }

    try {
      const resp = await fetch(
        `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
        {
          method: 'POST',
          headers: {
            'Authorization': `token ${githubToken}`,
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            'User-Agent': 'dingayi-hotspot-trigger',
          },
          body: JSON.stringify({ ref: 'main' }),
        }
      );

      if (resp.status === 204) {
        return new Response(
          JSON.stringify({ ok: true, message: '更新已触发，预计 3-6 分钟完成' }),
          { status: 200, headers }
        );
      }

      const text = await resp.text();
      return new Response(
        JSON.stringify({ ok: false, error: `GitHub API 返回 ${resp.status}`, detail: text }),
        { status: 502, headers }
      );
    } catch (e) {
      return new Response(
        JSON.stringify({ ok: false, error: '网络错误', detail: String(e) }),
        { status: 500, headers }
      );
    }
  },
};

function corsHeaders(request) {
  const origin = request.headers.get('Origin') || '';
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowed,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
  };
}
