"""认证路由

接口:
- POST /api/auth/login         {username, password}            -> {token, user}
- POST /api/auth/login-by-share {share_token, display_name?}   -> {token, user, meeting_id}
- POST /api/auth/logout                                          -> {ok}
- GET  /api/auth/me                                              -> {user}
"""
from __future__ import annotations

import json
from aiohttp import web

from src.utils.logging import logger
from src.meeting import auth, service


def _ok(data=None, msg='ok'):
    return web.Response(
        content_type='application/json',
        text=json.dumps({'code': 0, 'msg': msg, 'data': data}, ensure_ascii=False),
    )


def _err(msg, code=-1, status=400):
    return web.Response(
        status=status,
        content_type='application/json',
        text=json.dumps({'code': code, 'msg': str(msg)}, ensure_ascii=False),
    )


def _user_public(u):
    if not u:
        return None
    return {
        'id': u.get('id'),
        'username': u.get('username'),
        'display_name': u.get('display_name') or u.get('username'),
        'role': u.get('role'),
    }


async def login(request):
    try:
        body = await request.json()
        username = (body.get('username') or '').strip()
        password = body.get('password') or ''
        if not username or not password:
            return _err('用户名和密码不能为空')

        user = await auth.get_user_by_username(username)
        if not user or not auth.verify_password(password, user.get('password_hash') or ''):
            return _err('用户名或密码错误', status=401)

        token = await auth.issue_token(user['id'])
        return _ok({'token': token, 'user': _user_public(user)})
    except Exception as e:
        logger.exception('[auth] login 失败')
        return _err(e, status=500)


async def login_by_share(request):
    try:
        body = await request.json()
        share_token = (body.get('share_token') or '').strip()
        display_name = (body.get('display_name') or '').strip() or '访客'

        if not share_token:
            return _err('share_token 不能为空')

        share = await auth.resolve_share_token(share_token)
        if not share:
            return _err('分享链接无效或已过期', status=403)

        meeting = await service.get_meeting(share['meeting_id'])
        if not meeting:
            return _err('对应会议不存在', status=404)

        guest = await auth.create_guest_user(display_name)
        token = await auth.issue_token(guest['id'])

        return _ok({
            'token': token,
            'user': _user_public(guest),
            'meeting_id': meeting['id'],
            'meeting': {
                'id': meeting['id'],
                'title': meeting['title'],
                'start_time': meeting['start_time'],
                'meeting_code': meeting['meeting_code'],
            },
        })
    except Exception as e:
        logger.exception('[auth] login_by_share 失败')
        return _err(e, status=500)


async def logout(request):
    user = request.get('user')
    token = request.get('access_token')
    if token:
        await auth.revoke_token(token)
    return _ok({'logout': True, 'user': _user_public(user)})


async def me(request):
    user = request.get('user')
    if not user:
        return _err('未登录', code=-401, status=401)
    return _ok({'user': _user_public(user)})
