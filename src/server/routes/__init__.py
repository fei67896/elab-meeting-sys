"""路由模块"""
from .webrtc import offer
from .chat import human, interrupt_talk, is_speaking, clear_history
from .audio import humanaudio, asr, transcribe
from .video import set_audiotype, record, download_record
from .health import health_check
from .auth import login, login_by_share, logout, me
from .legacy import (
    legacy_meta,
    legacy_sessions,
    legacy_session_students,
    legacy_meeting_overview,
    legacy_series,
)
from .meeting import (
    secretary_command,
    secretary_history,
    list_meetings,
    create_meeting,
    get_meeting,
    update_meeting,
    delete_meeting,
    add_agenda,
    add_participant,
    download_ics,
    create_share,
    list_shares,
    set_attendance,
    list_attendance,
)

__all__ = [
    'offer',
    'human',
    'interrupt_talk',
    'is_speaking',
    'clear_history',
    'humanaudio',
    'asr',
    'transcribe',
    'set_audiotype',
    'record',
    'download_record',
    'health_check',
    'login',
    'login_by_share',
    'logout',
    'me',
    'secretary_command',
    'secretary_history',
    'list_meetings',
    'create_meeting',
    'get_meeting',
    'update_meeting',
    'delete_meeting',
    'add_agenda',
    'add_participant',
    'download_ics',
    'create_share',
    'list_shares',
    'set_attendance',
    'list_attendance',
    'legacy_meta',
    'legacy_sessions',
    'legacy_session_students',
    'legacy_meeting_overview',
    'legacy_series',
]
