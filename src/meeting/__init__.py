"""会议秘书模块: 会议 CRUD + LLM 意图解析 + 认证/分享/参会"""
from .db import init_db, get_conn
from .service import (
    create_meeting,
    list_meetings,
    get_meeting,
    update_meeting,
    cancel_meeting,
    delete_meeting,
    add_agenda,
    add_participant,
    set_attendance,
    list_attendance,
    log_command,
    list_command_history,
    resolve_meeting_ref,
    VALID_CATEGORIES,
    VALID_MODES,
)
from .intent import dispatch_command
from . import auth

__all__ = [
    'init_db',
    'get_conn',
    'create_meeting',
    'list_meetings',
    'get_meeting',
    'update_meeting',
    'cancel_meeting',
    'delete_meeting',
    'add_agenda',
    'add_participant',
    'set_attendance',
    'list_attendance',
    'log_command',
    'list_command_history',
    'resolve_meeting_ref',
    'dispatch_command',
    'auth',
    'VALID_CATEGORIES',
    'VALID_MODES',
]
