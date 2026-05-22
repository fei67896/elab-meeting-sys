"""aiohttp middleware: 解析 Authorization: Bearer <token>, 并在受保护路径上拦截匿名访问。

设计原则:
- 凡 /api/* 路径默认需要登录, 但白名单里的 path 例外 (登录/分享登录/健康)。
- 其余非 /api/* (例如 /human, /offer, /asr, /record, 静态资源) 维持原有的开放语义, 因为
  这些是原 Linly-Talker 协议路径, 不引入鉴权。
- 解析出的用户挂在 request['user']; access_token 挂在 request['access_token']。
"""
from __future__ import annotations

import json
from aiohttp import web

from src.meeting import auth as auth_mod


PUBLIC_API_PATHS = {
    '/api/auth/login',
    '/api/auth/login-by-share',
}


def _unauth(msg='未登录'):
    return web.Response(
        status=401,
        content_type='application/json',
        text=json.dumps({'code': -401, 'msg': msg}, ensure_ascii=False),
    )


@web.middleware
async def auth_middleware(request, handler):
    # 提取 token (优先 Authorization header, 兼容 ?access_token= 查询参数)
    token = None
    header = request.headers.get('Authorization', '')
    if header.startswith('Bearer '):
        token = header[7:].strip()
    if not token:
        token = request.query.get('access_token')

    request['access_token'] = token
    request['user'] = None
    if token:
        user = await auth_mod.resolve_token(token)
        if user:
            request['user'] = user

    # 是否需要鉴权
    path = request.path
    if path.startswith('/api/') and path not in PUBLIC_API_PATHS:
        if not request['user']:
            return _unauth()

    return await handler(request)
