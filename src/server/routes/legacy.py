"""老系统状态检测历史 API"""
from __future__ import annotations

import json

from aiohttp import web

from src.meeting import legacy_service as legacy


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


def _parse_int(val, name: str) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        raise ValueError(f'{name} 无效') from None


async def legacy_meta(request):
    data = await legacy.get_meta()
    return _ok(data)


async def legacy_sessions(request):
    limit = int(request.rel_url.query.get('limit', '50'))
    items = await legacy.list_sessions(limit=min(limit, 200))
    return _ok({'items': items})


async def legacy_session_students(request):
    try:
        gid = _parse_int(request.match_info.get('group_id'), 'group_id')
    except ValueError as e:
        return _err(str(e))
    items = await legacy.list_session_students(gid)
    return _ok({'group_id': gid, 'students': items})


async def legacy_meeting_overview(request):
    try:
        mid = _parse_int(request.match_info.get('group_id'), 'meeting_id')
    except ValueError as e:
        return _err(str(e))
    max_points = min(int(request.query.get('max_points', '150')), 400)
    max_events = min(int(request.query.get('max_events', '120')), 500)
    data = await legacy.meeting_overview(mid, max_points=max_points, max_events=max_events)
    return _ok(data)


async def legacy_series(request):
    try:
        gid = _parse_int(request.match_info.get('group_id'), 'group_id')
        sid = _parse_int(request.query.get('student_id'), 'student_id')
    except ValueError as e:
        return _err(str(e))
    kind = (request.query.get('type') or 'concentration').strip().lower()
    max_points = min(int(request.query.get('max_points', '400')), 2000)

    if kind == 'concentration':
        data = await legacy.series_concentration(gid, sid, max_points=max_points)
    elif kind == 'emotion':
        data = await legacy.series_emotion(gid, sid, max_points=max_points)
    elif kind == 'action':
        data = await legacy.series_actions(gid, sid, max_points=max_points)
    else:
        return _err('type 须为 concentration | emotion | action')
    return _ok({'group_id': gid, 'student_id': sid, 'type': kind, **data})
