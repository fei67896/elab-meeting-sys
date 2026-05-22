"""LLM 意图解析

把用户自然语言指令 (中文为主) 通过 qwen-plus 的 function calling 路由到
service.py 的具体函数，并生成一段适合数字人播报的回复文本。

设计要点：
- 不在客户端做规则解析，全部交给 LLM 输出 tool_call。
- 工具集尽量小但覆盖最常用 6 个动作 + 1 个兜底闲聊。
- 时间统一让 LLM 输出 ISO 8601 (含 +08:00 偏移)，避免本地化歧义。
- 失败回退：LLM 没给 tool_call 时按 chitchat 返回原文。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from src.utils.logging import logger
from src.utils.tts_text import prepare_speech_text
from . import service

CST = timezone(timedelta(hours=8))

# ============ 例会规则 (硬编码; 后续可挪到 DB / 用户配置) ============
# 每周三 18:30, 时长 90 分钟, 线上
REGULAR_MEETING = {
    'title': '例会',
    'weekday': 2,          # Monday=0 ... Wednesday=2
    'hour': 18,
    'minute': 30,
    'duration_min': 90,
    'mode': 'online',
    'description': '常规周会',
}


def _now_for_prompt() -> str:
    """给 LLM 当前时间用于解析"明天/下周三"等相对表达"""
    return datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %A (+0800)')


def _next_regular_slot(now: Optional[datetime] = None) -> datetime:
    """计算下一次例会时间.

    规则:
      - 找到 (今天 ~ 今天+7) 内第一个 weekday == REGULAR_MEETING['weekday'] 的日子;
      - 若那天就是今天且现在已经过了开始时刻, 顺延 7 天到下周。
    """
    now = now or datetime.now(CST)
    target_wd = REGULAR_MEETING['weekday']
    days_ahead = (target_wd - now.weekday()) % 7
    candidate = (now + timedelta(days=days_ahead)).replace(
        hour=REGULAR_MEETING['hour'],
        minute=REGULAR_MEETING['minute'],
        second=0,
        microsecond=0,
    )
    if candidate <= now:
        candidate += timedelta(days=7)
    return candidate


# ============ 工具定义 ============

_CATEGORY_ENUM = ['project_report', 'research_report', 'general', 'other']
_MODE_ENUM = ['online', 'offline']


TOOLS: List[Dict[str, Any]] = [
    {
        'type': 'function',
        'function': {
            'name': 'create_meeting',
            'description': (
                '创建/预定一场新会议。用户只要说明日期和时间即可调用本工具, '
                '标题、参会人、议程均可省略; 未给标题时系统自动按时间生成。'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'title': {
                        'type': 'string',
                        'description': '会议标题, 可选; 用户未提供时不要编造, 留空即可',
                    },
                    'start_time': {
                        'type': 'string',
                        'description': '会议开始时间, ISO 8601 含时区偏移, 例如 2026-05-22T15:00:00+08:00',
                    },
                    'end_time': {
                        'type': 'string',
                        'description': '会议结束时间, ISO 8601, 可省略, 省略时系统默认开始后 1 小时',
                    },
                    'description': {'type': 'string', 'description': '会议描述/备注'},
                    'mode': {
                        'type': 'string',
                        'enum': ['online', 'offline', 'hybrid'],
                        'description': '会议形式: online 线上, offline 线下, hybrid 混合',
                    },
                    'location': {'type': 'string', 'description': '线下会议地点'},
                    'participants': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'email': {'type': 'string'},
                                'role': {
                                    'type': 'string',
                                    'enum': ['host', 'attendee', 'optional'],
                                },
                            },
                            'required': ['name'],
                        },
                    },
                    'agendas': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'topic': {'type': 'string'},
                                'owner': {'type': 'string'},
                                'duration_min': {'type': 'integer'},
                                'notes': {'type': 'string'},
                                'category': {'type': 'string', 'enum': _CATEGORY_ENUM},
                                'mode': {'type': 'string', 'enum': _MODE_ENUM},
                            },
                            'required': ['topic'],
                        },
                    },
                },
                'required': ['start_time'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'add_regular_meeting',
            'description': (
                '添加"例会/常规会议/周会"。当用户说"加例会/添加例会/把例会加上/'
                '安排个周会"等含"例会"或"常规"或"周会"的指令时使用; '
                '时间和标题完全由系统硬编码 (当前规则: 每周三 18:30), 不需要 LLM 给参数。'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'note': {
                        'type': 'string',
                        'description': '可选: 用户额外补充的说明 (会写进会议描述)',
                    },
                },
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'add_agenda',
            'description': '给已存在的会议追加议程条目。category 必须从枚举中选择, 否则按 general 处理。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'meeting_ref': {
                        'type': 'string',
                        'description': '会议引用：id、meeting_code、"latest"/"today"/"current"(嘉宾默认当前会议) 或标题关键字',
                    },
                    'topic': {'type': 'string'},
                    'owner': {'type': 'string'},
                    'duration_min': {'type': 'integer'},
                    'notes': {'type': 'string'},
                    'category': {
                        'type': 'string',
                        'enum': _CATEGORY_ENUM,
                        'description': 'project_report 项目汇报 / research_report 科研汇报 / general 综合 / other 其他',
                    },
                    'mode': {
                        'type': 'string',
                        'enum': _MODE_ENUM,
                        'description': '议程形式 online 线上 / offline 线下',
                    },
                },
                'required': ['topic'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'set_attendance',
            'description': '设置当前用户是否参加某个会议',
            'parameters': {
                'type': 'object',
                'properties': {
                    'meeting_ref': {'type': 'string'},
                    'status': {
                        'type': 'string',
                        'enum': ['attending', 'declined', 'pending'],
                        'description': '参会状态: attending 参加 / declined 不参加 / pending 待定',
                    },
                },
                'required': ['status'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'add_participant',
            'description': '给已存在的会议追加参会人',
            'parameters': {
                'type': 'object',
                'properties': {
                    'meeting_ref': {'type': 'string'},
                    'name': {'type': 'string'},
                    'email': {'type': 'string'},
                    'role': {
                        'type': 'string',
                        'enum': ['host', 'attendee', 'optional'],
                    },
                },
                'required': ['meeting_ref', 'name'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_meetings',
            'description': '按时间区间/关键词/参会人/状态查询会议列表',
            'parameters': {
                'type': 'object',
                'properties': {
                    'date_from': {
                        'type': 'string',
                        'description': 'ISO 8601 开始时间, 例如 2026-05-22T00:00:00+08:00',
                    },
                    'date_to': {'type': 'string'},
                    'keyword': {'type': 'string', 'description': '标题/描述模糊关键字'},
                    'participant': {'type': 'string', 'description': '参会人姓名'},
                    'status': {
                        'type': 'string',
                        'enum': ['scheduled', 'ongoing', 'completed', 'cancelled'],
                    },
                },
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_meeting',
            'description': '查询单场会议的详细信息',
            'parameters': {
                'type': 'object',
                'properties': {
                    'meeting_ref': {'type': 'string'},
                },
                'required': ['meeting_ref'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'cancel_meeting',
            'description': '取消一场会议 (软删, 把 status 置为 cancelled)',
            'parameters': {
                'type': 'object',
                'properties': {
                    'meeting_ref': {'type': 'string'},
                },
                'required': ['meeting_ref'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_command_history',
            'description': '查看近期语音/文字指令处理记录 (会议秘书历史)',
            'parameters': {
                'type': 'object',
                'properties': {
                    'limit': {
                        'type': 'integer',
                        'description': '返回条数, 默认 10, 最大 30',
                    },
                },
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'chitchat',
            'description': '当用户没有明确的会议秘书指令时, 返回闲聊回复',
            'parameters': {
                'type': 'object',
                'properties': {
                    'reply': {'type': 'string', 'description': '直接给用户的回答文本'},
                },
                'required': ['reply'],
            },
        },
    },
]


SYSTEM_PROMPT_TEMPLATE = """你是一位专业的会议秘书 AI 助理, 负责帮助用户管理线上/线下会议。

当前用户角色: {role}
{role_hint}
当前时间: {now}
{context_hint}

规则:
1. 当用户说"明天/下周/今天下午 3 点"时, 你必须基于"当前时间"计算 ISO 8601 时间, 带 +08:00 时区。
2. 一次只调用一个工具, 不要并行调用。
3. 工具参数必须是结构化字段, 不要塞自然语言。
4. 预定会议: 用户只要说了日期和时间 (如"明天下午三点""5月20号上午10点") 就必须调用 create_meeting,
    不要追问标题、参会人或议程; title 可省略, 系统会按时间自动生成标题。
5. 如果用户没说结束时间, 不要填写 end_time, 系统默认会议时长 1 小时。
6. 议程的 category 必须是: project_report(项目汇报) / research_report(科研汇报) / general(综合) / other(其他) 之一; 用户没明说就用 general。
7. mode 必须是 online/offline; 没明说时, 沿用会议自身的 mode 或 online。
8. 若用户想订会议但未说明任何日期或时间, 用 chitchat 简短追问何时开会; 其他含糊指令再走 chitchat。
9. 所有回复必须使用简体中文, 不要使用繁体字。
10. 回复将用于语音播报: 不要使用冒号、斜杠、括号、英文状态词等特殊符号; 时间用口语表达 (如"明天下午三点"), 不要写 ISO 格式。
11. 用户说"例会 / 常规会议 / 周会 / 添加例会 / 加例会"等指令时, 必须调用 add_regular_meeting,
    不要自己用 create_meeting + 估计时间; 时间已经在系统里硬编码 (每周三 18:30)。
"""

ROLE_HINTS = {
    'owner': '作为系统主账号, 可以执行全部操作 (创建/取消/分享 等)。',
    'guest': '当前是嘉宾(通过分享链接进入)。只能针对"当前会议"做 add_agenda / set_attendance / get_meeting / list_meetings / chitchat, 不能新建或取消会议。',
}

OWNER_TOOL_NAMES = {
    'create_meeting', 'add_regular_meeting', 'add_agenda', 'add_participant',
    'set_attendance', 'list_meetings', 'get_meeting', 'cancel_meeting',
    'list_command_history', 'chitchat',
}
GUEST_TOOL_NAMES = {
    'add_agenda', 'set_attendance', 'list_meetings', 'get_meeting',
    'list_command_history', 'chitchat',
}


def _filter_tools(role: str) -> List[Dict[str, Any]]:
    allowed = OWNER_TOOL_NAMES if role == 'owner' else GUEST_TOOL_NAMES
    return [t for t in TOOLS if t['function']['name'] in allowed]


# ============ 执行器 ============

async def _resolve_or_current(ref: Any, current_meeting_id: Optional[int]):
    """优先按 ref 解析; ref 是 'current'/None 时, 回退到 current_meeting_id。"""
    if ref in (None, '', 'current', '当前会议') and current_meeting_id is not None:
        return await service.get_meeting(current_meeting_id)
    return await service.resolve_meeting_ref(ref)


async def _execute_tool(
    name: str,
    args: Dict[str, Any],
    *,
    user: Optional[Dict[str, Any]] = None,
    current_meeting_id: Optional[int] = None,
) -> Dict[str, Any]:
    """把 LLM 返回的 tool_call 真正落到 service 上。"""
    user = user or {}
    user_id = user.get('id')

    if name == 'create_meeting':
        return await service.create_meeting(
            title=args.get('title', ''),
            start_time=args.get('start_time', ''),
            end_time=args.get('end_time'),
            description=args.get('description'),
            mode=args.get('mode', 'online'),
            location=args.get('location'),
            participants=args.get('participants') or [],
            agendas=args.get('agendas') or [],
            created_by=user_id,
        )

    if name == 'add_regular_meeting':
        start = _next_regular_slot()
        end = start + timedelta(minutes=REGULAR_MEETING['duration_min'])
        note = (args.get('note') or '').strip()
        desc = REGULAR_MEETING['description']
        if note:
            desc = f"{desc}; {note}"
        return await service.create_meeting(
            title=REGULAR_MEETING['title'],
            start_time=start.isoformat(),
            end_time=end.isoformat(),
            description=desc,
            mode=REGULAR_MEETING['mode'],
            location=None,
            participants=[],
            agendas=[],
            created_by=user_id,
        )

    if name == 'add_agenda':
        meeting = await _resolve_or_current(args.get('meeting_ref'), current_meeting_id)
        if not meeting:
            return {'error': f"未找到匹配的会议: {args.get('meeting_ref')}"}
        return await service.add_agenda(
            meeting_id=meeting['id'],
            topic=args.get('topic', ''),
            owner=args.get('owner'),
            duration_min=args.get('duration_min'),
            notes=args.get('notes'),
            category=args.get('category', 'general'),
            mode=args.get('mode', meeting.get('mode', 'online') if meeting.get('mode') != 'hybrid' else 'online'),
            created_by=user_id,
        )

    if name == 'add_participant':
        meeting = await _resolve_or_current(args.get('meeting_ref'), current_meeting_id)
        if not meeting:
            return {'error': f"未找到匹配的会议: {args.get('meeting_ref')}"}
        return await service.add_participant(
            meeting_id=meeting['id'],
            name=args.get('name', ''),
            email=args.get('email'),
            role=args.get('role', 'attendee'),
        )

    if name == 'set_attendance':
        meeting = await _resolve_or_current(args.get('meeting_ref'), current_meeting_id)
        if not meeting:
            return {'error': '未指定会议, 且当前没有上下文会议'}
        status = args.get('status', 'pending')
        if status not in ('pending', 'attending', 'declined'):
            return {'error': f'非法状态: {status}'}
        return await service.set_attendance(
            meeting_id=meeting['id'],
            user_id=user_id,
            name=user.get('display_name') or user.get('username') or '匿名',
            status=status,
        )

    if name == 'list_meetings':
        rows = await service.list_meetings(
            date_from=args.get('date_from'),
            date_to=args.get('date_to'),
            keyword=args.get('keyword'),
            participant=args.get('participant'),
            status=args.get('status'),
        )
        return {'count': len(rows), 'items': rows}

    if name == 'get_meeting':
        meeting = await _resolve_or_current(args.get('meeting_ref'), current_meeting_id)
        return meeting or {'error': f"未找到会议: {args.get('meeting_ref')}"}

    if name == 'cancel_meeting':
        meeting = await _resolve_or_current(args.get('meeting_ref'), current_meeting_id)
        if not meeting:
            return {'error': f"未找到会议: {args.get('meeting_ref')}"}
        return await service.cancel_meeting(meeting['id'])

    if name == 'list_command_history':
        limit = min(max(int(args.get('limit') or 10), 1), 30)
        uid = None if (user or {}).get('role') == 'owner' else (user or {}).get('id')
        rows = await service.list_command_history(limit=limit, user_id=uid)
        return {'count': len(rows), 'items': rows}

    if name == 'chitchat':
        return {'reply': args.get('reply', '请问还有什么可以帮您?')}

    return {'error': f'未知工具: {name}'}


def _summarize_result(intent: str, result: Dict[str, Any]) -> str:
    """把执行结果转成数字人能播报的一段口语化中文。"""
    if not result:
        return '操作未返回结果。'

    if 'error' in result:
        return f"操作失败: {result['error']}"

    # 短回复: CPU 跑 Wav2Lip 速度有限, 让数字人说的尽量短
    if intent == 'create_meeting':
        title = result.get('title', '会议')
        start_iso = result.get('start_time')
        when = ''
        if start_iso:
            try:
                dt = datetime.fromisoformat(start_iso.replace('Z', '+00:00')).astimezone(CST)
                when = f'{dt.month}月{dt.day}日{dt.hour}点'
                if dt.minute:
                    when += f'{dt.minute}分'
            except Exception:
                pass
        return f"已预定{when}的{title}。" if when else f"已预定 {title}。"

    if intent == 'add_regular_meeting':
        # 把 ISO 时间转成口语 "本周三晚上六点半 / 下周三晚上六点半"
        start_iso = result.get('start_time')
        when = '下一个周三晚上六点半'
        if start_iso:
            try:
                dt = datetime.fromisoformat(start_iso)
                now = datetime.now(CST)
                same_week = (dt - now).days < 7 and dt.isocalendar().week == now.isocalendar().week
                when = ('本周三' if same_week else '下周三') + '晚上六点半'
            except Exception:
                pass
        return f"已添加例会，{when}开始。"

    if intent == 'add_agenda':
        return f"已加入议程，共 {len(result.get('agendas', []))} 项。"

    if intent == 'add_participant':
        return f"已添加参会人，共 {len(result.get('participants', []))} 位。"

    if intent == 'set_attendance':
        sm = result.get('attendance_summary', {})
        return f"已登记。共 {sm.get('attending', 0)} 人参加。"

    if intent == 'list_meetings':
        n = result.get('count', 0)
        if n == 0:
            return '没有符合条件的会议。'
        return f"查到 {n} 场会议。"

    if intent == 'get_meeting':
        status = result.get('status', '')
        status_zh = {
            'scheduled': '已排期',
            'ongoing': '进行中',
            'completed': '已完成',
            'cancelled': '已取消',
        }.get(status, status or '未知')
        return f"{result.get('title', '会议')}，{status_zh}。"

    if intent == 'cancel_meeting':
        return f"已取消 {result.get('title', '会议')}。"

    if intent == 'list_command_history':
        n = result.get('count', 0)
        if n == 0:
            return '暂无指令历史。'
        return f"最近有 {n} 条指令记录。"

    if intent == 'chitchat':
        # chitchat 文本 LLM 自己写的, 可能很长, 截短到 40 字内
        reply = result.get('reply', '')
        return reply if len(reply) <= 40 else reply[:38] + '。'

    return '已完成。'


# ============ 对外入口 ============

async def dispatch_command(
    user_input: str,
    api_key: str,
    base_url: str = 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: str = 'qwen-plus',
    user_role: str = 'owner',
    user: Optional[Dict[str, Any]] = None,
    current_meeting_id: Optional[int] = None,
) -> Dict[str, Any]:
    """主入口: 把一段用户输入转换成 {intent, params, result, reply_text}。

    - user_role: owner | guest, 决定可见的 tool 子集。
    - current_meeting_id: 嘉宾页面会带上, 让 LLM 不需要再"识别"具体会议。
    出错时仍返回结构化结果, 让前端能稳定渲染。
    """
    if not user_input or not user_input.strip():
        return {
            'intent': 'chitchat',
            'params': {},
            'result': {'reply': '请告诉我您想做什么。'},
            'reply_text': '请告诉我您想做什么。',
        }

    role_hint = ROLE_HINTS.get(user_role, ROLE_HINTS['owner'])
    context_hint = ''
    if current_meeting_id is not None:
        try:
            ctx_meeting = await service.get_meeting(current_meeting_id)
        except Exception:
            ctx_meeting = None
        if ctx_meeting:
            context_hint = (
                f"当前上下文会议: id={ctx_meeting['id']}, 标题='{ctx_meeting['title']}', "
                f"开始 {ctx_meeting['start_time']}, mode={ctx_meeting.get('mode')}。"
                f"用户不指定 meeting_ref 时, 默认就是这个会议。"
            )

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        now=_now_for_prompt(),
        role=user_role,
        role_hint=role_hint,
        context_hint=context_hint,
    )

    tools = _filter_tools(user_role)

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        completion = await client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_input},
            ],
            tools=tools,
            tool_choice='auto',
            temperature=0.2,
        )

        msg = completion.choices[0].message
        tool_calls = getattr(msg, 'tool_calls', None) or []

        if not tool_calls:
            reply = prepare_speech_text(msg.content or '好的。') or '好的。'
            return {
                'intent': 'chitchat',
                'params': {},
                'result': {'reply': reply},
                'reply_text': reply,
            }

        call = tool_calls[0]
        name = call.function.name
        try:
            args = json.loads(call.function.arguments or '{}')
        except json.JSONDecodeError:
            args = {}

        # 权限再校验一遍, 防止 LLM 越权调用
        allowed = OWNER_TOOL_NAMES if user_role == 'owner' else GUEST_TOOL_NAMES
        if name not in allowed:
            logger.warning(f'[secretary] tool={name} 被角色 {user_role} 拦截')
            return {
                'intent': 'chitchat',
                'params': {},
                'result': {'reply': '当前权限不允许此操作。'},
                'reply_text': '抱歉, 您当前的身份不能执行这个操作。',
            }

        logger.info(f'[secretary] role={user_role} tool={name} args={args}')

        exec_user = dict(user or {})
        exec_user.setdefault('role', user_role)
        result = await _execute_tool(
            name, args,
            user=exec_user, current_meeting_id=current_meeting_id,
        )
        reply = prepare_speech_text(_summarize_result(name, result)) or '已完成。'

        return {
            'intent': name,
            'params': args,
            'result': result,
            'reply_text': reply,
        }

    except Exception as e:
        logger.exception('[secretary] dispatch failed')
        return {
            'intent': 'error',
            'params': {},
            'result': {'error': str(e)},
            'reply_text': f'处理指令时出错: {e}',
        }
