"""会议秘书的数据模型 (dataclass)

仅用于在 service 层做类型注解和 to_dict 输出。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Participant:
    id: Optional[int] = None
    meeting_id: Optional[int] = None
    name: str = ''
    email: Optional[str] = None
    role: str = 'attendee'  # host | attendee | optional

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgendaItem:
    id: Optional[int] = None
    meeting_id: Optional[int] = None
    seq: int = 1
    topic: str = ''
    owner: Optional[str] = None
    duration_min: Optional[int] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Meeting:
    id: Optional[int] = None
    title: str = ''
    start_time: str = ''      # ISO 8601 e.g. 2026-05-22T15:00:00+08:00
    end_time: Optional[str] = None
    meeting_url: Optional[str] = None
    meeting_code: Optional[str] = None
    description: Optional[str] = None
    status: str = 'scheduled'  # scheduled | ongoing | completed | cancelled
    created_at: str = ''
    updated_at: str = ''
    agendas: List[AgendaItem] = field(default_factory=list)
    participants: List[Participant] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d['agendas'] = [a if isinstance(a, dict) else a.to_dict() for a in self.agendas]
        d['participants'] = [p if isinstance(p, dict) else p.to_dict() for p in self.participants]
        return d


@dataclass
class CommandLog:
    id: Optional[int] = None
    ts: str = ''
    user_input: str = ''
    intent: Optional[str] = None
    params_json: Optional[str] = None
    result_json: Optional[str] = None
    reply_text: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
