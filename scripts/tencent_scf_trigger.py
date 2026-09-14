# -*- coding: utf-8 -*-
# 腾讯云 SCF 云函数：触发 GitHub Actions workflow_dispatch
# 运行环境：Python 3.7
# 部署后在函数配置 → 环境变量 添加 GITHUB_TOKEN
# 触发器：API 网关触发，启用集成响应
# 国内可直接访问，token 存服务端不进前端

import json
import os
import urllib.request
import urllib.error

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
REPO = 'ZYJ-ui12/dingayi-hotspot'
WORKFLOW = 'daily.yml'

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json; charset=utf-8',
}


def _resp(status_code, body):
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body, ensure_ascii=False),
    }


def main_handler(event, context):
    method = event.get('httpMethod', 'GET').upper()

    if method == 'OPTIONS':
        return _resp(200, {})

    if method != 'POST':
        return _resp(405, {'ok': False, 'error': 'Method not allowed'})

    if not GITHUB_TOKEN:
        return _resp(500, {'ok': False, 'error': '服务端未配置 GITHUB_TOKEN'})

    url = 'https://api.github.com/repos/%s/actions/workflows/%s/dispatches' % (REPO, WORKFLOW)
    data = json.dumps({'ref': 'main'}).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', 'token %s' % GITHUB_TOKEN)
    req.add_header('Accept', 'application/vnd.github.v3+json')
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'dingayi-trigger')

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        if resp.getcode() == 204:
            return _resp(200, {'ok': True})
        return _resp(502, {'ok': False, 'error': 'GitHub %s' % resp.getcode()})
    except urllib.error.HTTPError as e:
        msg = 'GitHub %s' % e.code
        try:
            err_body = json.loads(e.read().decode('utf-8'))
            if err_body.get('message'):
                msg = err_body['message']
        except Exception:
            pass
        return _resp(502, {'ok': False, 'error': msg})
    except Exception as e:
        return _resp(500, {'ok': False, 'error': str(e)})
