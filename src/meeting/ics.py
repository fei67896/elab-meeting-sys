"""RFC 5545 ICS 文件生成 (手写, 不引入新依赖)。

仅覆盖单事件 (VEVENT)，包含开始/结束时间、标题、描述、地点 (meeting_url)、
参会人 (ATTENDEE)，适合导入 Outlook/Google Calendar/Apple Calendar。
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict

CST = timezone(timedelta(hours=8))


def _to_utc_basic(iso_str: str) -> str:
    """把 ISO 8601 (含时区) 转成 ICS 要求的 UTC 紧凑格式 YYYYMMDDTHHMMSSZ。"""
    if not iso_str:
        return ''
    try:
        # python 3.11+ 支持 fromisoformat 解析 +08:00；3.10 也支持。
        dt = datetime.fromisoformat(iso_str)
    except ValueError:
        # 容错：尝试当作 naive 时间按 CST 解析
        dt = datetime.strptime(iso_str[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=CST)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=CST)
    return dt.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def _escape(text: str) -> str:
    """ICS 文本字段转义。"""
    if text is None:
        return ''
    return (
        str(text)
        .replace('\\', '\\\\')
        .replace(';', r'\;')
        .replace(',', r'\,')
        .replace('\n', r'\n')
    )


def build_ics(meeting: Dict[str, Any]) -> str:
    """生成单个会议的 ICS 字符串。"""
    start = _to_utc_basic(meeting.get('start_time', ''))
    end_raw = meeting.get('end_time')
    if end_raw:
        end = _to_utc_basic(end_raw)
    else:
        # 没有结束时间默认 +1 小时
        try:
            dt = datetime.fromisoformat(meeting.get('start_time', ''))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=CST)
            end = (dt + timedelta(hours=1)).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        except (ValueError, TypeError):
            end = start

    uid = f"{meeting.get('meeting_code', meeting.get('id', 'meeting'))}@linly-talker-stream"
    dtstamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Linly-Talker-Stream//Meeting Secretary//ZH',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'BEGIN:VEVENT',
        f'UID:{uid}',
        f'DTSTAMP:{dtstamp}',
        f'DTSTART:{start}',
        f'DTEND:{end}',
        f"SUMMARY:{_escape(meeting.get('title', ''))}",
        f"DESCRIPTION:{_escape(meeting.get('description', '') or '')}",
        f"LOCATION:{_escape(meeting.get('meeting_url', '') or '')}",
        f"STATUS:{'CANCELLED' if meeting.get('status') == 'cancelled' else 'CONFIRMED'}",
    ]

    for p in meeting.get('participants', []) or []:
        name = _escape(p.get('name', ''))
        email = p.get('email') or 'unknown@meet.local'
        role = (p.get('role') or 'attendee').lower()
        partstat = 'ACCEPTED' if role == 'host' else 'NEEDS-ACTION'
        cu_type = 'INDIVIDUAL'
        attendee_role = 'CHAIR' if role == 'host' else (
            'OPT-PARTICIPANT' if role == 'optional' else 'REQ-PARTICIPANT'
        )
        lines.append(
            f'ATTENDEE;CN={name};ROLE={attendee_role};PARTSTAT={partstat};CUTYPE={cu_type}:mailto:{email}'
        )

    lines += ['END:VEVENT', 'END:VCALENDAR']

    # ICS 行长度上限 75 字节, 用 \r\n 拼接
    return '\r\n'.join(lines) + '\r\n'
