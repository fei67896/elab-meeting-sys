"""会议秘书 Agent MCP 工具注册与卡片展示映射。

将 LLM function calling 工具抽象为 MCP 风格能力，供前端四角功能卡片展示。
角位 slot: lt 左上前 / lb 左下 / rt 右上 / rb 右下
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

# card_id -> 元数据
MCP_CARDS: Dict[str, Dict[str, Any]] = {
    'book': {
        'id': 'book',
        'side': 'left',
        'slot': 'lt',
        'title': '预订会议',
        'description': '说出日期时间即可预定，标题可选',
        'tools': {
            'create_meeting',
            'add_regular_meeting',
            'cancel_meeting',
        },
    },
    'roster': {
        'id': 'roster',
        'side': 'left',
        'slot': 'lb',
        'title': '议程参会',
        'description': '添加议程、参会人与出席登记',
        'tools': {
            'add_agenda',
            'add_participant',
            'set_attendance',
        },
    },
    'query': {
        'id': 'query',
        'side': 'right',
        'slot': 'rt',
        'title': '查询会议',
        'description': '按条件检索或查看单场详情',
        'tools': {
            'list_meetings',
            'get_meeting',
        },
    },
    'history': {
        'id': 'history',
        'side': 'right',
        'slot': 'rb',
        'title': '会议历史',
        'description': '近期语音指令与处理记录',
        'tools': {'list_command_history'},
    },
}

TOOL_TO_CARD: Dict[str, str] = {}
for _cid, _meta in MCP_CARDS.items():
    for _t in _meta['tools']:
        TOOL_TO_CARD[_t] = _cid

SLOT_ORDER = ('lt', 'lb', 'rt', 'rb')


def list_mcp_cards() -> List[Dict[str, Any]]:
    """返回全部卡片定义 (前端初始化用)。"""
    out = []
    for slot in SLOT_ORDER:
        for m in MCP_CARDS.values():
            if m['slot'] == slot:
                out.append({
                    'id': m['id'],
                    'side': m['side'],
                    'slot': m['slot'],
                    'title': m['title'],
                    'description': m['description'],
                })
                break
    return out


def _fmt_dt(iso: Optional[str]) -> str:
    if not iso:
        return '—'
    try:
        dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
        return dt.strftime('%m-%d %H:%M')
    except Exception:
        return str(iso)[:16]


def _format_lines(tool: str, result: Dict[str, Any]) -> List[str]:
    if not result:
        return ['无返回数据']
    if result.get('error'):
        return [str(result['error'])]

    if tool in ('create_meeting', 'add_regular_meeting'):
        return [
            result.get('title') or '会议',
            f"{_fmt_dt(result.get('start_time'))} ~ {_fmt_dt(result.get('end_time'))}",
            f"形式 {result.get('mode', 'online')}",
        ]

    if tool == 'add_agenda':
        agendas = result.get('agendas') or []
        last = agendas[-1] if agendas else {}
        return [
            f"议程 {len(agendas)} 项",
            last.get('topic') or '—',
            f"负责人 {last.get('owner') or '待定'}",
        ]

    if tool == 'add_participant':
        parts = result.get('participants') or []
        names = ', '.join((p.get('name') or '') for p in parts[-3:])
        return [f"参会人 {len(parts)} 位", names or '—']

    if tool == 'set_attendance':
        sm = result.get('attendance_summary') or {}
        return [
            f"参加 {sm.get('attending', 0)} 人",
            f"不参加 {sm.get('declined', 0)} 人",
            f"待定 {sm.get('pending', 0)} 人",
        ]

    if tool == 'list_meetings':
        items = result.get('items') or []
        lines = [f"共 {result.get('count', len(items))} 场"]
        for m in items[:4]:
            lines.append(f"{_fmt_dt(m.get('start_time'))} {m.get('title', '')}")
        if len(items) > 4:
            lines.append(f"… 另有 {len(items) - 4} 场")
        return lines

    if tool == 'get_meeting':
        return [
            result.get('title') or '会议',
            f"{_fmt_dt(result.get('start_time'))}",
            f"状态 {result.get('status', '')}",
            f"议程 {len(result.get('agendas') or [])} 项",
        ]

    if tool == 'cancel_meeting':
        return [f"已取消 {result.get('title', '会议')}"]

    if tool == 'list_command_history':
        items = result.get('items') or []
        lines = [f"最近 {result.get('count', len(items))} 条"]
        for row in items[:5]:
            intent = row.get('intent') or '—'
            text = (row.get('user_input') or '')[:20]
            ts = (row.get('ts') or '')[:10]
            lines.append(f"{ts} {intent}: {text}")
        return lines

    if tool == 'chitchat':
        reply = (result.get('reply') or '')[:60]
        return [reply or '—']

    return ['已完成']


def build_mcp_call(
    tool: str,
    params: Dict[str, Any],
    result: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """单次 tool 调用 -> 前端卡片更新载荷。"""
    card_id = TOOL_TO_CARD.get(tool)
    if not card_id:
        return None
    card = MCP_CARDS[card_id]
    ok = 'error' not in (result or {})
    return {
        'mcp_tool': tool,
        'card_id': card_id,
        'side': card['side'],
        'slot': card['slot'],
        'card_title': card['title'],
        'status': 'success' if ok else 'error',
        'lines': _format_lines(tool, result),
        'params': params,
        'result': result,
        'at': datetime.now().astimezone().isoformat(),
    }


def build_agent_response(
    intent: str,
    params: Dict[str, Any],
    result: Dict[str, Any],
    reply_text: str,
    *,
    log_id: Optional[int] = None,
) -> Dict[str, Any]:
    """组装带 Agent/MCP 元数据的完整 API 响应。"""
    mcp_call = build_mcp_call(intent, params, result)
    return {
        'intent': intent,
        'params': params,
        'result': result,
        'reply_text': reply_text,
        'log_id': log_id,
        'agent': {
            'mode': 'mcp',
            'framework': 'function_calling',
        },
        'mcp_calls': [mcp_call] if mcp_call else [],
        'mcp_cards': list_mcp_cards(),
    }
