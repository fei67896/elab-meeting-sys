"""会议秘书 HTTP 路由

所有路径前缀 /api/, 风格保持与现有路由一致 (json body + {code, msg, data})。
"""
from __future__ import annotations

import json
from aiohttp import web

from src.utils.logging import logger
from src.server.state import state
from src.meeting import service, intent, auth
from src.meeting.ics import build_ics
from src.meeting.mcp_registry import build_agent_response, list_mcp_cards


# ============ 辅助 ============

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


def _require_owner(request):
    """检查当前请求是否为 owner; 否则返回 _err 响应, 由调用方直接 return。"""
    user = request.get('user') or {}
    if user.get('role') != 'owner':
        return _err('仅会议拥有者可执行此操作', status=403)
    return None


# ============ /api/secretary/command ============

async def secretary_command(request):
    """主入口：用户文本指令 -> LLM 意图解析 -> 落库 -> 数字人播报。

    body: { text, sessionid?, speak?: bool = true, meeting_id? }
    返回: { intent, params, result, reply_text, log_id }
    """
    try:
        body = await request.json()
        text = (body.get('text') or '').strip()
        sessionid = body.get('sessionid', 0)
        speak = body.get('speak', True)
        meeting_id = body.get('meeting_id')

        if not text:
            return _err('text 不能为空')

        llm_cfg = state.config.llm if state.config else None
        if not llm_cfg or not llm_cfg.api_key or llm_cfg.api_key == 'your_api_key_here':
            return _err('LLM 未配置 api_key, 请设置 DASHSCOPE_API_KEY 后重启后端', status=500)

        user = request.get('user') or {}
        user_role = user.get('role') or 'owner'

        result = await intent.dispatch_command(
            user_input=text,
            api_key=llm_cfg.api_key,
            base_url=llm_cfg.base_url,
            model=llm_cfg.model,
            user_role=user_role,
            user=user,
            current_meeting_id=meeting_id,
        )

        log_id = await service.log_command(
            user_input=text,
            intent=result.get('intent'),
            params=result.get('params'),
            result=result.get('result'),
            reply_text=result.get('reply_text'),
            user_id=user.get('id'),
        )
        payload = build_agent_response(
            result.get('intent') or 'chitchat',
            result.get('params') or {},
            result.get('result') or {},
            result.get('reply_text') or '',
            log_id=log_id,
        )

        # 触发数字人播报。失败不影响主流程, 仅记录日志。
        if speak and payload.get('reply_text'):
            reply = payload['reply_text']
            try:
                stream = state.avatar_streams.get(sessionid)
                if stream is not None:
                    stream.put_msg_txt(reply)
                else:
                    logger.warning(
                        f'[secretary] session {sessionid} 无数字人流, 跳过播报'
                    )
            except Exception:
                logger.exception('[secretary] 推送数字人播报失败')

        return _ok(payload)
    except Exception as e:
        logger.exception('[secretary] command 失败')
        return _err(e, status=500)


# ============ /api/secretary/history ============

async def secretary_mcp_cards(request):
    """返回 Agent MCP 功能卡片元数据 (左右侧栏初始化)。"""
    return _ok({'cards': list_mcp_cards()})


async def secretary_history(request):
    """读取指令历史。owner 看全部, guest 仅看自己。"""
    try:
        limit = int(request.query.get('limit', 50))
        user = request.get('user') or {}
        user_id = None if user.get('role') == 'owner' else user.get('id')
        rows = await service.list_command_history(limit=limit, user_id=user_id)
        return _ok({'count': len(rows), 'items': rows})
    except Exception as e:
        return _err(e, status=500)


# ============ /api/meetings ============

async def list_meetings(request):
    try:
        q = request.query
        rows = await service.list_meetings(
            date_from=q.get('from') or q.get('date_from'),
            date_to=q.get('to') or q.get('date_to'),
            keyword=q.get('keyword'),
            participant=q.get('participant'),
            status=q.get('status'),
            limit=int(q.get('limit', 200)),
        )
        return _ok({'count': len(rows), 'items': rows})
    except Exception as e:
        return _err(e, status=500)


async def create_meeting(request):
    deny = _require_owner(request)
    if deny is not None:
        return deny
    try:
        body = await request.json()
        user = request.get('user') or {}
        m = await service.create_meeting(
            title=body.get('title', ''),
            start_time=body.get('start_time', ''),
            end_time=body.get('end_time'),
            description=body.get('description'),
            mode=body.get('mode', 'online'),
            location=body.get('location'),
            participants=body.get('participants') or [],
            agendas=body.get('agendas') or [],
            created_by=user.get('id'),
        )
        return _ok(m)
    except ValueError as ve:
        return _err(ve, status=400)
    except Exception as e:
        return _err(e, status=500)


async def get_meeting(request):
    try:
        meeting_id = int(request.match_info['id'])
        m = await service.get_meeting(meeting_id)
        if not m:
            return _err('会议不存在', status=404)
        return _ok(m)
    except Exception as e:
        return _err(e, status=500)


async def update_meeting(request):
    deny = _require_owner(request)
    if deny is not None:
        return deny
    try:
        meeting_id = int(request.match_info['id'])
        body = await request.json()
        m = await service.update_meeting(meeting_id, body)
        if not m:
            return _err('会议不存在', status=404)
        return _ok(m)
    except Exception as e:
        return _err(e, status=500)


async def delete_meeting(request):
    deny = _require_owner(request)
    if deny is not None:
        return deny
    try:
        meeting_id = int(request.match_info['id'])
        ok = await service.delete_meeting(meeting_id)
        if not ok:
            return _err('会议不存在', status=404)
        return _ok({'deleted': True})
    except Exception as e:
        return _err(e, status=500)


async def add_agenda(request):
    try:
        meeting_id = int(request.match_info['id'])
        body = await request.json()
        user = request.get('user') or {}
        m = await service.add_agenda(
            meeting_id=meeting_id,
            topic=body.get('topic', ''),
            owner=body.get('owner'),
            duration_min=body.get('duration_min'),
            notes=body.get('notes'),
            seq=body.get('seq'),
            category=body.get('category', 'general'),
            mode=body.get('mode', 'online'),
            created_by=user.get('id'),
        )
        if not m:
            return _err('会议不存在', status=404)
        return _ok(m)
    except Exception as e:
        return _err(e, status=500)


async def add_participant(request):
    deny = _require_owner(request)
    if deny is not None:
        return deny
    try:
        meeting_id = int(request.match_info['id'])
        body = await request.json()
        m = await service.add_participant(
            meeting_id=meeting_id,
            name=body.get('name', ''),
            email=body.get('email'),
            role=body.get('role', 'attendee'),
            user_id=body.get('user_id'),
            attendance_status=body.get('attendance_status', 'pending'),
        )
        if not m:
            return _err('会议不存在', status=404)
        return _ok(m)
    except Exception as e:
        return _err(e, status=500)


# ============ 分享 ============

async def create_share(request):
    """生成会议分享 token; 仅 owner 可调用。"""
    try:
        user = request.get('user') or {}
        if user.get('role') != 'owner':
            return _err('仅会议拥有者可以生成分享链接', status=403)

        meeting_id = int(request.match_info['id'])
        meeting = await service.get_meeting(meeting_id)
        if not meeting:
            return _err('会议不存在', status=404)

        share = await auth.create_share_token(meeting_id, created_by=user.get('id'))
        return _ok({
            'token': share['token'],
            'expires_at': share['expires_at'],
            'meeting_id': meeting_id,
        })
    except Exception as e:
        return _err(e, status=500)


async def list_shares(request):
    try:
        user = request.get('user') or {}
        if user.get('role') != 'owner':
            return _err('仅会议拥有者可以查看分享列表', status=403)

        meeting_id = int(request.match_info['id'])
        rows = await auth.list_share_tokens(meeting_id)
        return _ok({'items': rows})
    except Exception as e:
        return _err(e, status=500)


# ============ 参会状态 ============

async def set_attendance(request):
    """登记/更新当前用户对该会议的参会状态。

    body: { status: 'attending'|'declined'|'pending', name?, email? }
    """
    try:
        meeting_id = int(request.match_info['id'])
        body = await request.json()
        status = body.get('status') or 'pending'

        user = request.get('user') or {}
        name = (body.get('name') or '').strip() or user.get('display_name') or user.get('username') or '匿名'
        email = body.get('email')

        meeting = await service.set_attendance(
            meeting_id=meeting_id,
            user_id=user.get('id'),
            name=name,
            status=status,
            email=email,
        )
        if not meeting:
            return _err('会议不存在', status=404)
        return _ok(meeting)
    except ValueError as ve:
        return _err(ve, status=400)
    except Exception as e:
        return _err(e, status=500)


async def list_attendance(request):
    try:
        meeting_id = int(request.match_info['id'])
        rows = await service.list_attendance(meeting_id)
        return _ok({'items': rows})
    except Exception as e:
        return _err(e, status=500)


async def download_ics(request):
    try:
        meeting_id = int(request.match_info['id'])
        m = await service.get_meeting(meeting_id)
        if not m:
            return _err('会议不存在', status=404)
        body = build_ics(m)
        filename = f"meeting-{m.get('meeting_code') or meeting_id}.ics"
        return web.Response(
            body=body.encode('utf-8'),
            content_type='text/calendar',
            charset='utf-8',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        return _err(e, status=500)
