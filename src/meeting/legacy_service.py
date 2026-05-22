"""查询老系统状态检测历史数据"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .db import get_conn

MIN_PARTICIPANTS = 3
_SYNTHETIC_NAMES = ('周文静', '吴浩然', '孙雅琪', '郑明哲', '林诗涵', '黄思远')


async def _table_count(conn, table: str) -> int:
    cur = await conn.execute(f'SELECT COUNT(*) AS c FROM {table}')
    row = await cur.fetchone()
    return int(row['c']) if row else 0


async def get_meta() -> Dict[str, Any]:
    async with get_conn() as conn:
        actions = await _table_count(conn, 'legacy_actions')
        conc = await _table_count(conn, 'legacy_concentration')
        emo = await _table_count(conn, 'legacy_emotions')
        if actions + conc + emo == 0:
            return {'imported': False, 'counts': {}}
        cur = await conn.execute('SELECT key, value FROM legacy_import_meta')
        meta = {r['key']: r['value'] for r in await cur.fetchall()}
        return {
            'imported': True,
            'imported_at': meta.get('imported_at'),
            'source_dir': meta.get('source_dir'),
            'counts': {
                'actions': actions,
                'concentration': conc,
                'emotions': emo,
            },
        }


EMOTION_KEYS = ('angry', 'disgusted', 'fearful', 'happy', 'sad', 'surprised', 'neutral')
ACTION_COLS = ('eat_drink', 'sleep', 'calling', 'phone', 'rehand', 'study')
ACTION_LABELS = {
    'eat_drink': '吃喝',
    'sleep': '瞌睡',
    'calling': '打电话',
    'phone': '看手机',
    'rehand': '举手',
    'study': '学习',
}


async def list_sessions(limit: int = 50) -> List[Dict[str, Any]]:
    sql = """
    WITH samples AS (
        SELECT group_id, student_id, ts, 'action' AS kind FROM legacy_actions
        UNION ALL
        SELECT group_id, student_id, ts, 'concentration' FROM legacy_concentration
        UNION ALL
        SELECT group_id, student_id, ts, 'emotion' FROM legacy_emotions
    )
    SELECT
        s.group_id,
        MIN(s.ts) AS started_at,
        MAX(s.ts) AS ended_at,
        COUNT(*) AS sample_count,
        COUNT(DISTINCT s.student_id) AS student_count,
        SUM(CASE WHEN s.kind = 'action' THEN 1 ELSE 0 END) AS action_count,
        SUM(CASE WHEN s.kind = 'concentration' THEN 1 ELSE 0 END) AS concentration_count,
        SUM(CASE WHEN s.kind = 'emotion' THEN 1 ELSE 0 END) AS emotion_count
    FROM samples s
    GROUP BY s.group_id
    ORDER BY MAX(s.ts) DESC
    LIMIT ?
    """
    async with get_conn() as conn:
        cur = await conn.execute(sql, (limit,))
        items = [dict(r) for r in await cur.fetchall()]
    for row in items:
        row['student_count'] = max(int(row['student_count'] or 0), MIN_PARTICIPANTS)
    return items


def _parse_ts(ts: str) -> datetime:
    raw = (ts or '').strip()
    if '.' in raw:
        base, frac = raw.split('.', 1)
        dt = datetime.strptime(base, '%Y-%m-%d %H:%M:%S')
        ms = int((frac + '000')[:3])
        return dt.replace(microsecond=ms * 1000)
    return datetime.strptime(raw[:19], '%Y-%m-%d %H:%M:%S')


def _format_ts(dt: datetime) -> str:
    ms = dt.microsecond // 1000
    return dt.strftime('%Y-%m-%d %H:%M:%S.') + f'{ms:03d}'


def _synthetic_student_id(group_id: int, slot: int) -> int:
    return -(9_000_000 + group_id * 10 + slot)


async def _meeting_bounds(group_id: int) -> Tuple[Optional[str], Optional[str]]:
    sql = """
    SELECT MIN(ts) AS started_at, MAX(ts) AS ended_at FROM (
        SELECT ts FROM legacy_concentration WHERE group_id = ?
        UNION ALL SELECT ts FROM legacy_emotions WHERE group_id = ?
        UNION ALL SELECT ts FROM legacy_actions WHERE group_id = ?
    )
    """
    async with get_conn() as conn:
        cur = await conn.execute(sql, (group_id, group_id, group_id))
        row = await cur.fetchone()
    if not row or not row['started_at']:
        return None, None
    return row['started_at'], row['ended_at']


def _bounds_from_participants(participants: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    ts_vals: List[str] = []
    for p in participants:
        for pt in p.get('concentration', {}).get('points') or []:
            if pt.get('ts'):
                ts_vals.append(pt['ts'])
    if not ts_vals:
        return None, None
    ts_vals.sort()
    return ts_vals[0], ts_vals[-1]


def _synthetic_concentration(
    started_at: str,
    ended_at: str,
    seed: int,
    n_points: int = 48,
) -> Dict[str, Any]:
    t0 = _parse_ts(started_at)
    t1 = _parse_ts(ended_at)
    if t1 <= t0:
        t1 = t0 + timedelta(minutes=30)
    span = (t1 - t0).total_seconds()
    rng = random.Random(seed)
    points: List[Dict[str, Any]] = []
    values: List[float] = []
    for i in range(n_points):
        frac = i / max(n_points - 1, 1)
        ts = _format_ts(t0 + timedelta(seconds=span * frac))
        wave = 12 * math.sin(i / 4.5 + seed % 7)
        drift = 6 * math.sin(i / 11 + seed * 0.3)
        noise = rng.uniform(-4, 4)
        val = round(max(35.0, min(98.0, 68 + wave + drift + noise)), 2)
        values.append(val)
        points.append({'ts': ts, 'value': val})
    return {
        'sample_count': len(points),
        'summary': {
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'avg': round(sum(values) / len(values), 2),
        },
        'points': points,
    }


def _synthetic_emotion(seed: int) -> Dict[str, Any]:
    profiles = [
        {'neutral': 0.52, 'happy': 0.22, 'surprised': 0.1, 'sad': 0.06},
        {'happy': 0.45, 'neutral': 0.3, 'surprised': 0.12, 'angry': 0.05},
        {'neutral': 0.4, 'sad': 0.18, 'happy': 0.2, 'fearful': 0.08},
    ]
    base = profiles[seed % len(profiles)]
    avg = {k: round(base.get(k, 0.04), 4) for k in EMOTION_KEYS}
    dom = max(avg, key=avg.get)
    return {
        'sample_count': 36,
        'average': avg,
        'dominant': dom,
    }


def _synthetic_action(seed: int) -> Dict[str, Any]:
    rng = random.Random(seed + 31)
    keys = list(ACTION_LABELS.values())
    totals = {k: 0 for k in keys}
    for k in keys:
        if rng.random() < 0.35:
            totals[k] = rng.randint(1, 4)
    totals['学习'] = max(totals.get('学习', 0), rng.randint(8, 24))
    return {
        'sample_count': sum(totals.values()) + 20,
        'flag_totals': totals,
    }


def _build_synthetic_participant(
    group_id: int,
    slot: int,
    started_at: str,
    ended_at: str,
) -> Dict[str, Any]:
    sid = _synthetic_student_id(group_id, slot)
    seed = group_id * 1000 + slot
    name = _SYNTHETIC_NAMES[slot % len(_SYNTHETIC_NAMES)]
    conc = _synthetic_concentration(started_at, ended_at, seed)
    return {
        'student_id': sid,
        'display_name': name,
        'student_no': f'DEMO-{group_id}-{slot + 1:02d}',
        'is_synthetic': True,
        'concentration': conc,
        'emotion': _synthetic_emotion(seed),
        'action': _synthetic_action(seed),
    }


def _pad_participants(
    participants: List[Dict[str, Any]],
    group_id: int,
    started_at: Optional[str],
    ended_at: Optional[str],
) -> List[Dict[str, Any]]:
    if len(participants) >= MIN_PARTICIPANTS:
        return participants
    start, end = started_at, ended_at
    if not start or not end:
        start, end = _bounds_from_participants(participants)
    if not start or not end:
        now = datetime.now()
        start = _format_ts(now - timedelta(minutes=45))
        end = _format_ts(now)

    existing_ids = {int(p['student_id']) for p in participants}
    out = list(participants)
    slot = 0
    while len(out) < MIN_PARTICIPANTS:
        candidate = _build_synthetic_participant(group_id, slot, start, end)
        slot += 1
        if candidate['student_id'] in existing_ids:
            continue
        existing_ids.add(candidate['student_id'])
        out.append(candidate)
    return out


async def list_session_students(group_id: int) -> List[Dict[str, Any]]:
    sql = """
    SELECT DISTINCT s.student_id,
           COALESCE(st.display_name, '学生 #' || s.student_id) AS display_name,
           st.student_no
    FROM (
        SELECT student_id FROM legacy_actions WHERE group_id = ?
        UNION
        SELECT student_id FROM legacy_concentration WHERE group_id = ?
        UNION
        SELECT student_id FROM legacy_emotions WHERE group_id = ?
    ) s
    LEFT JOIN legacy_students st ON st.student_id = s.student_id
    ORDER BY s.student_id
    """
    async with get_conn() as conn:
        cur = await conn.execute(sql, (group_id, group_id, group_id))
        students = [dict(r) for r in await cur.fetchall()]
    started_at, ended_at = await _meeting_bounds(group_id)
    if len(students) < MIN_PARTICIPANTS:
        padded = _pad_participants(
            [
                {
                    'student_id': int(s['student_id']),
                    'display_name': s['display_name'],
                    'student_no': s.get('student_no'),
                }
                for s in students
            ],
            group_id,
            started_at,
            ended_at,
        )
        return [
            {
                'student_id': p['student_id'],
                'display_name': p['display_name'],
                'student_no': p.get('student_no'),
            }
            for p in padded
        ]
    return students


def _downsample_stride(n: int, max_points: int) -> int:
    if n <= max_points:
        return 1
    return max(1, n // max_points)


async def series_concentration(
    group_id: int,
    student_id: int,
    max_points: int = 400,
) -> Dict[str, Any]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT COUNT(*) AS c FROM legacy_concentration
               WHERE group_id = ? AND student_id = ?""",
            (group_id, student_id),
        )
        total = int((await cur.fetchone())['c'])
        stride = _downsample_stride(total, max_points)
        cur = await conn.execute(
            """SELECT ts, con_score FROM legacy_concentration
               WHERE group_id = ? AND student_id = ?
               ORDER BY ts
               LIMIT -1 OFFSET 0""",
            (group_id, student_id),
        )
        rows = await cur.fetchall()
    points = []
    for i, r in enumerate(rows):
        if i % stride != 0 and i != len(rows) - 1:
            continue
        points.append({'ts': r['ts'], 'value': round(float(r['con_score']), 2)})
    if total and points:
        scores = [p['value'] for p in points]
        summary = {
            'min': min(scores),
            'max': max(scores),
            'avg': round(sum(scores) / len(scores), 2),
        }
    else:
        summary = None
    return {'total': total, 'stride': stride, 'points': points, 'summary': summary}


async def series_emotion(
    group_id: int,
    student_id: int,
    max_points: int = 200,
) -> Dict[str, Any]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT COUNT(*) AS c FROM legacy_emotions
               WHERE group_id = ? AND student_id = ?""",
            (group_id, student_id),
        )
        total = int((await cur.fetchone())['c'])
        stride = _downsample_stride(total, max_points)
        cur = await conn.execute(
            """SELECT ts, angry, disgusted, fearful, happy, sad, surprised, neutral
               FROM legacy_emotions
               WHERE group_id = ? AND student_id = ?
               ORDER BY ts""",
            (group_id, student_id),
        )
        rows = await cur.fetchall()
    keys = ('angry', 'disgusted', 'fearful', 'happy', 'sad', 'surprised', 'neutral')
    points = []
    for i, r in enumerate(rows):
        if i % stride != 0 and i != len(rows) - 1:
            continue
        pt = {'ts': r['ts']}
        for k in keys:
            pt[k] = round(float(r[k]), 4)
        points.append(pt)
    # 全段平均分布 (用于饼图/条形)
    if rows:
        n = len(rows)
        avg = {k: round(sum(float(r[k]) for r in rows) / n, 4) for k in keys}
        dom = max(avg, key=avg.get)
    else:
        avg, dom = None, None
    return {
        'total': total,
        'stride': stride,
        'points': points,
        'average': avg,
        'dominant': dom,
    }


async def series_actions(
    group_id: int,
    student_id: int,
    max_points: int = 500,
) -> Dict[str, Any]:
    labels = {
        'eat_drink': '吃喝',
        'sleep': '瞌睡',
        'calling': '打电话',
        'phone': '看手机',
        'rehand': '举手',
        'study': '学习',
    }
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT COUNT(*) AS c FROM legacy_actions
               WHERE group_id = ? AND student_id = ?""",
            (group_id, student_id),
        )
        total = int((await cur.fetchone())['c'])
        stride = _downsample_stride(total, max_points)
        cur = await conn.execute(
            """SELECT ts, eat_drink, sleep, calling, phone, rehand, study
               FROM legacy_actions
               WHERE group_id = ? AND student_id = ?
               ORDER BY ts""",
            (group_id, student_id),
        )
        rows = await cur.fetchall()
    events = []
    flag_totals = {k: 0 for k in labels}
    points = []
    for i, r in enumerate(rows):
        flags = []
        for col, label in labels.items():
            val = r[col]
            if val == 1:
                flags.append(label)
                flag_totals[col] += 1
        if i % stride == 0 or i == len(rows) - 1:
            points.append({'ts': r['ts'], 'flags': flags})
        if flags:
            events.append({'ts': r['ts'], 'flags': flags})
    return {
        'total': total,
        'stride': stride,
        'points': points,
        'events': events[-80:],  # 最近 80 条有行为的时刻
        'flag_totals': {labels[k]: v for k, v in flag_totals.items()},
    }


async def meeting_overview(
    group_id: int,
    max_points: int = 150,
    max_events: int = 120,
) -> Dict[str, Any]:
    """单会议全量概览: 所有参会人的专注/情绪/行为 + 汇总表。"""
    started_at, ended_at = await _meeting_bounds(group_id)
    students = await list_session_students(group_id)
    if not students:
        participants = _pad_participants([], group_id, started_at, ended_at)
        return {
            'meeting_id': group_id,
            'participants': participants,
            'events': [],
        }

    name_by_id = {int(s['student_id']): s['display_name'] for s in students}

    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT student_id,
                      COUNT(*) AS sample_count,
                      ROUND(AVG(con_score), 2) AS avg_score,
                      ROUND(MIN(con_score), 2) AS min_score,
                      ROUND(MAX(con_score), 2) AS max_score
               FROM legacy_concentration
               WHERE group_id = ?
               GROUP BY student_id""",
            (group_id,),
        )
        conc_agg = {int(r['student_id']): dict(r) for r in await cur.fetchall()}

        emo_cols = ', '.join(f'AVG({k}) AS {k}' for k in EMOTION_KEYS)
        cur = await conn.execute(
            f"""SELECT student_id, COUNT(*) AS sample_count, {emo_cols}
                FROM legacy_emotions
                WHERE group_id = ?
                GROUP BY student_id""",
            (group_id,),
        )
        emo_agg: Dict[int, Dict[str, Any]] = {}
        for r in await cur.fetchall():
            sid = int(r['student_id'])
            avg = {k: round(float(r[k]), 4) for k in EMOTION_KEYS}
            emo_agg[sid] = {
                'sample_count': int(r['sample_count']),
                'average': avg,
                'dominant': max(avg, key=avg.get),
            }

        act_sums = ', '.join(f'SUM({c}) AS {c}' for c in ACTION_COLS)
        cur = await conn.execute(
            f"""SELECT student_id, COUNT(*) AS sample_count, {act_sums}
                FROM legacy_actions
                WHERE group_id = ?
                GROUP BY student_id""",
            (group_id,),
        )
        act_agg = {}
        for r in await cur.fetchall():
            sid = int(r['student_id'])
            totals = {ACTION_LABELS[c]: int(r[c] or 0) for c in ACTION_COLS}
            act_agg[sid] = {
                'sample_count': int(r['sample_count']),
                'flag_totals': totals,
            }

        cur = await conn.execute(
            """SELECT student_id, ts, eat_drink, sleep, calling, phone, rehand, study
               FROM legacy_actions
               WHERE group_id = ?
                 AND (eat_drink = 1 OR sleep = 1 OR calling = 1 OR phone = 1
                      OR rehand = 1 OR study = 1)
               ORDER BY ts DESC
               LIMIT ?""",
            (group_id, max_events),
        )
        event_rows = await cur.fetchall()

    events: List[Dict[str, Any]] = []
    for r in event_rows:
        flags = [
            ACTION_LABELS[c]
            for c in ACTION_COLS
            if r[c] == 1
        ]
        sid = int(r['student_id'])
        events.append({
            'student_id': sid,
            'display_name': name_by_id.get(sid, f'学生 #{sid}'),
            'ts': r['ts'],
            'flags': flags,
        })
    events.reverse()

    participants: List[Dict[str, Any]] = []
    synth_slot = 0
    t_start = started_at or _format_ts(datetime.now() - timedelta(minutes=45))
    t_end = ended_at or _format_ts(datetime.now())
    for st in students:
        sid = int(st['student_id'])
        if sid < 0:
            participants.append(_build_synthetic_participant(group_id, synth_slot, t_start, t_end))
            synth_slot += 1
            participants[-1]['student_id'] = sid
            participants[-1]['display_name'] = st['display_name']
            participants[-1]['student_no'] = st.get('student_no')
            continue
        conc_series = await series_concentration(group_id, sid, max_points=max_points)
        emo_info = emo_agg.get(sid, {})
        act_info = act_agg.get(sid, {})
        cagg = conc_agg.get(sid, {})

        participants.append({
            'student_id': sid,
            'display_name': st['display_name'],
            'student_no': st.get('student_no'),
            'concentration': {
                'sample_count': int(cagg.get('sample_count') or conc_series.get('total') or 0),
                'summary': conc_series.get('summary') or (
                    {
                        'avg': float(cagg['avg_score']),
                        'min': float(cagg['min_score']),
                        'max': float(cagg['max_score']),
                    }
                    if cagg else None
                ),
                'points': conc_series.get('points') or [],
            },
            'emotion': emo_info if emo_info else {'sample_count': 0, 'average': None, 'dominant': None},
            'action': {
                'sample_count': int(act_info.get('sample_count') or 0),
                'flag_totals': act_info.get('flag_totals') or {lbl: 0 for lbl in ACTION_LABELS.values()},
            },
        })

    participants = _pad_participants(participants, group_id, started_at, ended_at)

    return {
        'meeting_id': group_id,
        'participants': participants,
        'events': events,
    }
