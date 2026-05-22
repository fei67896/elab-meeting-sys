"""会议秘书业务层

提供会议、议程、参会人、指令历史的 CRUD。
- 时间统一以 ISO 8601 字符串存储 (含时区偏移)；前端可自由格式化。
- meeting_code 用 secrets.token_urlsafe(6) 生成，唯一索引保证不冲突。
- meeting_url 占位符 https://meet.local/m/<code>，方便后续真接 Zoom/腾讯会议时替换。
"""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from .db import get_conn

# 本地默认时区：东八区
CST = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(CST).isoformat(timespec='seconds')


def _gen_meeting_code() -> str:
    # 6 个 url-safe 字节 -> 8 字符，足够避免本地碰撞
    return secrets.token_urlsafe(6)


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat((ts or '').replace('Z', '+00:00'))


def _default_title_from_start(start_time: str) -> str:
    """仅给定开始时间时生成默认会议标题。"""
    try:
        dt = _parse_iso(start_time).astimezone(CST)
        if dt.minute:
            when = f'{dt.hour}点{dt.minute:02d}分'
        else:
            when = f'{dt.hour}点'
        return f'{dt.month}月{dt.day}日{when}会议'
    except Exception:
        return '会议'


def _default_end_time(start_time: str, end_time: Optional[str]) -> Optional[str]:
    if end_time:
        return end_time
    try:
        dt = _parse_iso(start_time)
        return (dt + timedelta(hours=1)).isoformat(timespec='seconds')
    except Exception:
        return None


VALID_CATEGORIES = ('project_report', 'research_report', 'general', 'other')
VALID_MODES = ('online', 'offline', 'hybrid')


def _row_to_meeting(row) -> Dict[str, Any]:
    return {
        'id': row['id'],
        'title': row['title'],
        'start_time': row['start_time'],
        'end_time': row['end_time'],
        'meeting_url': row['meeting_url'],
        'meeting_code': row['meeting_code'],
        'description': row['description'],
        'status': row['status'],
        'mode': row['mode'] if 'mode' in row.keys() else 'online',
        'location': row['location'] if 'location' in row.keys() else None,
        'created_by': row['created_by'] if 'created_by' in row.keys() else None,
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
    }


async def create_meeting(
    title: str,
    start_time: str,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    mode: str = 'online',
    location: Optional[str] = None,
    participants: Optional[List[Dict[str, Any]]] = None,
    agendas: Optional[List[Dict[str, Any]]] = None,
    created_by: Optional[int] = None,
) -> Dict[str, Any]:
    """创建会议, 可选一次性挂入议程和参会人。仅需 start_time；标题可省略。"""
    if not start_time:
        raise ValueError('start_time 必填')

    title = (title or '').strip() or _default_title_from_start(start_time)
    end_time = _default_end_time(start_time, end_time)

    if mode not in VALID_MODES:
        mode = 'online'

    code = _gen_meeting_code()
    url = f'https://meet.local/m/{code}'
    now = _now_iso()

    async with get_conn() as conn:
        cur = await conn.execute(
            """INSERT INTO meetings
               (title, start_time, end_time, meeting_url, meeting_code,
                description, status, mode, location, created_by,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'scheduled', ?, ?, ?, ?, ?)""",
            (title, start_time, end_time, url, code, description,
             mode, location, created_by, now, now),
        )
        meeting_id = cur.lastrowid

        if participants:
            for p in participants:
                await conn.execute(
                    """INSERT INTO participants
                       (meeting_id, user_id, name, email, role, attendance_status)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        meeting_id,
                        p.get('user_id'),
                        p.get('name', ''),
                        p.get('email'),
                        p.get('role', 'attendee'),
                        p.get('attendance_status', 'pending'),
                    ),
                )

        if agendas:
            for idx, a in enumerate(agendas, start=1):
                cat = a.get('category', 'general')
                if cat not in VALID_CATEGORIES:
                    cat = 'general'
                amode = a.get('mode', mode)
                if amode not in ('online', 'offline'):
                    amode = 'online'
                await conn.execute(
                    """INSERT INTO agenda_items
                       (meeting_id, seq, topic, owner, duration_min, notes,
                        category, mode, created_by, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (meeting_id, a.get('seq', idx), a.get('topic', ''),
                     a.get('owner'), a.get('duration_min'), a.get('notes'),
                     cat, amode, created_by, now),
                )

        await conn.commit()

    return await get_meeting(meeting_id)


async def get_meeting(meeting_id: int) -> Optional[Dict[str, Any]]:
    """读取单条会议含议程和参会人 (含 attendance_status)。"""
    async with get_conn() as conn:
        cur = await conn.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,))
        row = await cur.fetchone()
        if row is None:
            return None

        meeting = _row_to_meeting(row)

        cur = await conn.execute(
            'SELECT * FROM agenda_items WHERE meeting_id = ? ORDER BY seq',
            (meeting_id,),
        )
        meeting['agendas'] = [dict(r) for r in await cur.fetchall()]

        cur = await conn.execute(
            'SELECT * FROM participants WHERE meeting_id = ? ORDER BY id',
            (meeting_id,),
        )
        meeting['participants'] = [dict(r) for r in await cur.fetchall()]

        # 汇总参会统计
        st = {'attending': 0, 'declined': 0, 'pending': 0}
        for p in meeting['participants']:
            st[p.get('attendance_status', 'pending')] = st.get(p.get('attendance_status', 'pending'), 0) + 1
        meeting['attendance_summary'] = st

        return meeting


async def list_meetings(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    keyword: Optional[str] = None,
    participant: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """按条件查询会议；支持时间区间、标题/描述关键词、参会人姓名模糊匹配、状态。"""
    sql = """SELECT DISTINCT m.* FROM meetings m
             LEFT JOIN participants p ON p.meeting_id = m.id
             WHERE 1=1"""
    args: list = []

    if date_from:
        sql += ' AND m.start_time >= ?'
        args.append(date_from)
    if date_to:
        sql += ' AND m.start_time <= ?'
        args.append(date_to)
    if keyword:
        sql += ' AND (m.title LIKE ? OR m.description LIKE ?)'
        args.extend([f'%{keyword}%', f'%{keyword}%'])
    if participant:
        sql += ' AND p.name LIKE ?'
        args.append(f'%{participant}%')
    if status:
        sql += ' AND m.status = ?'
        args.append(status)

    sql += ' ORDER BY m.start_time ASC LIMIT ?'
    args.append(limit)

    async with get_conn() as conn:
        cur = await conn.execute(sql, args)
        rows = await cur.fetchall()
        meetings = [_row_to_meeting(r) for r in rows]

        # 批量补 agendas / participants，避免 N+1 的极端情况
        if meetings:
            ids = [m['id'] for m in meetings]
            placeholder = ','.join('?' * len(ids))

            cur = await conn.execute(
                f'SELECT * FROM agenda_items WHERE meeting_id IN ({placeholder}) ORDER BY seq',
                ids,
            )
            agendas_map: Dict[int, List[dict]] = {}
            for r in await cur.fetchall():
                agendas_map.setdefault(r['meeting_id'], []).append(dict(r))

            cur = await conn.execute(
                f'SELECT * FROM participants WHERE meeting_id IN ({placeholder}) ORDER BY id',
                ids,
            )
            parts_map: Dict[int, List[dict]] = {}
            for r in await cur.fetchall():
                parts_map.setdefault(r['meeting_id'], []).append(dict(r))

            for m in meetings:
                m['agendas'] = agendas_map.get(m['id'], [])
                m['participants'] = parts_map.get(m['id'], [])

        return meetings


async def update_meeting(meeting_id: int, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新会议主表字段。允许字段白名单内修改。"""
    allowed = {'title', 'start_time', 'end_time', 'description',
               'status', 'mode', 'location'}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return await get_meeting(meeting_id)

    sets = ', '.join(f'{k} = ?' for k in updates.keys())
    args = list(updates.values()) + [_now_iso(), meeting_id]

    async with get_conn() as conn:
        await conn.execute(
            f'UPDATE meetings SET {sets}, updated_at = ? WHERE id = ?',
            args,
        )
        await conn.commit()

    return await get_meeting(meeting_id)


async def cancel_meeting(meeting_id: int) -> Optional[Dict[str, Any]]:
    """软取消：把 status 改成 cancelled，保留记录方便审计。"""
    return await update_meeting(meeting_id, {'status': 'cancelled'})


async def delete_meeting(meeting_id: int) -> bool:
    async with get_conn() as conn:
        cur = await conn.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))
        await conn.commit()
        return cur.rowcount > 0


async def add_agenda(
    meeting_id: int,
    topic: str,
    owner: Optional[str] = None,
    duration_min: Optional[int] = None,
    notes: Optional[str] = None,
    seq: Optional[int] = None,
    category: str = 'general',
    mode: str = 'online',
    created_by: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """追加一条议程。seq 默认取当前最大 +1。"""
    if category not in VALID_CATEGORIES:
        category = 'general'
    if mode not in ('online', 'offline'):
        mode = 'online'

    now = _now_iso()
    async with get_conn() as conn:
        if seq is None:
            cur = await conn.execute(
                'SELECT COALESCE(MAX(seq), 0) AS m FROM agenda_items WHERE meeting_id = ?',
                (meeting_id,),
            )
            r = await cur.fetchone()
            seq = (r['m'] or 0) + 1

        await conn.execute(
            """INSERT INTO agenda_items
               (meeting_id, seq, topic, owner, duration_min, notes,
                category, mode, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (meeting_id, seq, topic, owner, duration_min, notes,
             category, mode, created_by, now),
        )
        await conn.execute(
            'UPDATE meetings SET updated_at = ? WHERE id = ?',
            (now, meeting_id),
        )
        await conn.commit()

    return await get_meeting(meeting_id)


async def add_participant(
    meeting_id: int,
    name: str,
    email: Optional[str] = None,
    role: str = 'attendee',
    user_id: Optional[int] = None,
    attendance_status: str = 'pending',
) -> Optional[Dict[str, Any]]:
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO participants
               (meeting_id, user_id, name, email, role, attendance_status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (meeting_id, user_id, name, email, role, attendance_status),
        )
        await conn.execute(
            'UPDATE meetings SET updated_at = ? WHERE id = ?',
            (_now_iso(), meeting_id),
        )
        await conn.commit()

    return await get_meeting(meeting_id)


# ============ attendance ============

async def set_attendance(
    meeting_id: int,
    user_id: Optional[int],
    name: str,
    status: str,
    email: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """设置参会状态。

    优先按 user_id 匹配现有 participant; 没有就按 name; 都没有就新插一条。
    status: pending | attending | declined
    """
    if status not in ('pending', 'attending', 'declined'):
        raise ValueError(f'非法 attendance_status: {status}')

    now = _now_iso()
    async with get_conn() as conn:
        row = None
        if user_id is not None:
            cur = await conn.execute(
                'SELECT id FROM participants WHERE meeting_id = ? AND user_id = ? LIMIT 1',
                (meeting_id, user_id),
            )
            row = await cur.fetchone()
        if row is None and name:
            cur = await conn.execute(
                'SELECT id FROM participants WHERE meeting_id = ? AND name = ? LIMIT 1',
                (meeting_id, name),
            )
            row = await cur.fetchone()

        if row:
            await conn.execute(
                """UPDATE participants
                      SET user_id = COALESCE(?, user_id),
                          name = COALESCE(?, name),
                          email = COALESCE(?, email),
                          attendance_status = ?,
                          responded_at = ?
                    WHERE id = ?""",
                (user_id, name, email, status, now, row['id']),
            )
        else:
            await conn.execute(
                """INSERT INTO participants
                   (meeting_id, user_id, name, email, role, attendance_status, responded_at)
                   VALUES (?, ?, ?, ?, 'attendee', ?, ?)""",
                (meeting_id, user_id, name or '匿名', email, status, now),
            )

        await conn.execute(
            'UPDATE meetings SET updated_at = ? WHERE id = ?',
            (now, meeting_id),
        )
        await conn.commit()

    return await get_meeting(meeting_id)


async def list_attendance(meeting_id: int) -> List[Dict[str, Any]]:
    async with get_conn() as conn:
        cur = await conn.execute(
            'SELECT * FROM participants WHERE meeting_id = ? ORDER BY id',
            (meeting_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def resolve_meeting_ref(ref: Any) -> Optional[Dict[str, Any]]:
    """把自然语言里的"会议引用"解析成具体记录。

    支持：纯数字 id、meeting_code、'latest'、'today'、标题模糊匹配。
    """
    if ref is None:
        return None

    # 1) 数字 id
    if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
        return await get_meeting(int(ref))

    s = str(ref).strip()

    # 2) 关键字 latest / today
    if s.lower() in ('latest', '最近', '最新', '上一个'):
        ms = await list_meetings(limit=1)
        # list_meetings 按 start_time 升序，取最后一个反而更"latest"，
        # 但用户语义通常指"刚才创建/修改的那个"——按 updated_at 取
        async with get_conn() as conn:
            cur = await conn.execute(
                'SELECT id FROM meetings ORDER BY updated_at DESC LIMIT 1'
            )
            row = await cur.fetchone()
            if row:
                return await get_meeting(row['id'])
        return ms[0] if ms else None

    if s.lower() in ('today', '今天', '今日'):
        today = datetime.now(CST).date().isoformat()
        ms = await list_meetings(date_from=today, date_to=today + 'T23:59:59+08:00')
        return ms[0] if ms else None

    # 3) meeting_code (8 字符 url-safe)
    async with get_conn() as conn:
        cur = await conn.execute(
            'SELECT id FROM meetings WHERE meeting_code = ?', (s,)
        )
        row = await cur.fetchone()
        if row:
            return await get_meeting(row['id'])

        # 4) 标题模糊匹配，返回最近一条
        cur = await conn.execute(
            """SELECT id FROM meetings WHERE title LIKE ?
               ORDER BY updated_at DESC LIMIT 1""",
            (f'%{s}%',),
        )
        row = await cur.fetchone()
        if row:
            return await get_meeting(row['id'])

    return None


# ============ 指令历史 ============

async def log_command(
    user_input: str,
    intent: Optional[str],
    params: Optional[Dict[str, Any]],
    result: Optional[Dict[str, Any]],
    reply_text: Optional[str],
    user_id: Optional[int] = None,
) -> int:
    async with get_conn() as conn:
        cur = await conn.execute(
            """INSERT INTO command_history
               (ts, user_id, user_input, intent, params_json, result_json, reply_text)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                _now_iso(),
                user_id,
                user_input,
                intent,
                json.dumps(params, ensure_ascii=False) if params is not None else None,
                json.dumps(result, ensure_ascii=False, default=str) if result is not None else None,
                reply_text,
            ),
        )
        await conn.commit()
        return cur.lastrowid


async def list_command_history(limit: int = 50, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    async with get_conn() as conn:
        if user_id is None:
            cur = await conn.execute(
                'SELECT * FROM command_history ORDER BY ts DESC LIMIT ?',
                (limit,),
            )
        else:
            cur = await conn.execute(
                """SELECT * FROM command_history WHERE user_id = ?
                   ORDER BY ts DESC LIMIT ?""",
                (user_id, limit),
            )
        rows = await cur.fetchall()
        out = []
        for r in rows:
            d = dict(r)
            for k in ('params_json', 'result_json'):
                if d.get(k):
                    try:
                        d[k[:-5]] = json.loads(d[k])
                    except json.JSONDecodeError:
                        d[k[:-5]] = None
            out.append(d)
        return out
