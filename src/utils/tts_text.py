"""数字人 TTS 播报前的文本清洗。

- 去掉会被 Edge 等引擎读出来的符号 (冒号、斜杠、括号等)
- 繁体转简体, 避免 Qwen 偶发繁体输出
- 保留中文、数字、字母与基本句读 (，。！？)
"""
from __future__ import annotations

import re
from typing import Optional

# 直接删除的符号 (不转成停顿; 空格保留, 最后统一折叠)
_STRIP_CHARS = (
    ':：;；、·•|/\\*#@$%^&+=<>[]{}\"\'`~'
    '「」『』【】（）《》〈〉[]()'
    '…—～｜・-_'
)

_STATUS_EN_ZH = {
    'scheduled': '已排期',
    'ongoing': '进行中',
    'completed': '已完成',
    'cancelled': '已取消',
    'pending': '待确认',
    'attending': '参加',
    'declined': '不参加',
}

_STRIP_TABLE = str.maketrans('', '', _STRIP_CHARS)

# 常见 emoji 区段
_EMOJI_RE = re.compile(
    '['
    '\U0001F300-\U0001FAFF'
    '\U00002600-\U000027BF'
    '\U0001F600-\U0001F64F'
    ']+',
    flags=re.UNICODE,
)

# Markdown / URL
_MD_RE = re.compile(r'[*_#`]+')
_URL_RE = re.compile(r'https?://\S+|www\.\S+', re.I)

# ISO 时间串 (播报不友好)
_ISO_TIME_RE = re.compile(
    r'\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}(?::\d{2})?(?:[+-]\d{2}:?\d{2}|Z)?'
)

_zhconv_convert: Optional[object] = None
_zhconv_tried = False


def _to_simplified(text: str) -> str:
    global _zhconv_convert, _zhconv_tried
    if not text:
        return text
    if not _zhconv_tried:
        _zhconv_tried = True
        try:
            import zhconv
            _zhconv_convert = zhconv.convert
        except ImportError:
            _zhconv_convert = None
    if _zhconv_convert is not None:
        try:
            return _zhconv_convert(text, 'zh-cn')
        except Exception:
            pass
    return text


def prepare_speech_text(text: str) -> str:
    """清洗后用于 TTS; 空串表示无需播报。"""
    if not text or not str(text).strip():
        return ''

    s = str(text).strip()
    s = _to_simplified(s)
    s = _URL_RE.sub('', s)
    s = _MD_RE.sub('', s)
    s = _ISO_TIME_RE.sub(' ', s)
    s = _EMOJI_RE.sub('', s)

    # 括号保留内容, 去掉括号本身
    s = re.sub(r'[（(]([^）)]*)[）)]', r'\1', s)
    s = s.translate(_STRIP_TABLE)

    for en, zh in _STATUS_EN_ZH.items():
        s = re.sub(rf'\b{en}\b', zh, s, flags=re.I)

    s = re.sub(r'[\t\n\r]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'^[，。！？、\s]+', '', s)
    s = re.sub(r'[，。！？、\s]+$', '', s)

    # 连续句读合并
    s = re.sub(r'[，]{2,}', '，', s)
    s = re.sub(r'[。]{2,}', '。', s)

    return s.strip()
