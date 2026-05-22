"""认证模块

- 密码哈希: PBKDF2-SHA256 + 每用户随机 salt (标准库, 不引入新依赖)。
- access token: secrets.token_urlsafe(32), 存 auth_tokens 表, 默认 7 天有效。
- share token: secrets.token_urlsafe(16), 存 share_tokens 表, 默认 30 天有效。
- 主账号 zhaoyifei/123456 在 init_db 后自动 seed (如果不存在)。
"""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from .db import get_conn

CST = timezone(timedelta(hours=8))
TOKEN_TTL = timedelta(days=7)
SHARE_TTL = timedelta(days=30)

# 默认主账号 (owner 列表). 启动时若 username 不存在则 seed; 已存在的不动 (不改密码/姓名).
# 想批量重置密码请直接走 DB 或后续加专门的管理接口.
DEFAULT_OWNERS = [
    {'username': 'zhaoyifei',     'display_name': '赵一飞',   'password': '123456'},
    {'username': 'zhaofanyu',     'display_name': '赵梵宇',   'password': '123456'},
    {'username': 'linyixuan',     'display_name': '林易宣',   'password': '123456'},
    {'username': 'wushengtang',   'display_name': '吴晟堂',   'password': '123456'},
    {'username': 'zhangzhongyuan','display_name': '张忠远',   'password': '123456'},
]


def _now_iso() -> str:
    return datetime.now(CST).isoformat(timespec='seconds')


# ============ 密码哈希 ============

def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """返回格式: pbkdf2_sha256$<iter>$<salt_hex>$<hash_hex>。"""
    if salt is None:
        salt = os.urandom(16)
    iterations = 120_000
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f'pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}'


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    try:
        algo, iters, salt_hex, hash_hex = stored.split('$')
    except ValueError:
        return False
    if algo != 'pbkdf2_sha256':
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(hash_hex)
    digest = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, int(iters)
    )
    return secrets.compare_digest(digest, expected)


# ============ 用户管理 ============

async def ensure_default_owners() -> None:
    """启动时确保所有内置 owner 都存在。已存在的不会被覆盖。"""
    async with get_conn() as conn:
        now = _now_iso()
        for cfg in DEFAULT_OWNERS:
            cur = await conn.execute(
                'SELECT id FROM users WHERE username = ?', (cfg['username'],)
            )
            if await cur.fetchone():
                continue
            await conn.execute(
                """INSERT INTO users (username, password_hash, display_name, role, created_at)
                   VALUES (?, ?, ?, 'owner', ?)""",
                (
                    cfg['username'],
                    hash_password(cfg['password']),
                    cfg['display_name'],
                    now,
                ),
            )
        await conn.commit()


# 兼容旧名字 (db.py 旧代码可能还在调)
ensure_default_owner = ensure_default_owners


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    async with get_conn() as conn:
        cur = await conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    async with get_conn() as conn:
        cur = await conn.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def create_guest_user(display_name: str) -> Dict[str, Any]:
    """创建一个临时 guest 用户, username 用 guest_<rand>。"""
    username = f'guest_{secrets.token_urlsafe(6)}'
    async with get_conn() as conn:
        cur = await conn.execute(
            """INSERT INTO users (username, password_hash, display_name, role, created_at)
               VALUES (?, NULL, ?, 'guest', ?)""",
            (username, display_name or username, _now_iso()),
        )
        await conn.commit()
        return {
            'id': cur.lastrowid,
            'username': username,
            'display_name': display_name or username,
            'role': 'guest',
        }


# ============ access token ============

async def issue_token(user_id: int, ttl: timedelta = TOKEN_TTL) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(CST)
    expires = (now + ttl).isoformat(timespec='seconds')
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO auth_tokens (token, user_id, created_at, expires_at)
               VALUES (?, ?, ?, ?)""",
            (token, user_id, now.isoformat(timespec='seconds'), expires),
        )
        await conn.commit()
    return token


async def resolve_token(token: str) -> Optional[Dict[str, Any]]:
    """凭 token 取 user dict, 失效返回 None。"""
    if not token:
        return None
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT t.token, t.expires_at, u.id AS uid, u.username, u.display_name, u.role
                 FROM auth_tokens t JOIN users u ON t.user_id = u.id
                WHERE t.token = ?""",
            (token,),
        )
        row = await cur.fetchone()
        if not row:
            return None
        # 过期校验
        if row['expires_at']:
            try:
                exp = datetime.fromisoformat(row['expires_at'])
                if datetime.now(CST) > exp:
                    return None
            except ValueError:
                pass
        return {
            'id': row['uid'],
            'username': row['username'],
            'display_name': row['display_name'],
            'role': row['role'],
        }


async def revoke_token(token: str) -> None:
    if not token:
        return
    async with get_conn() as conn:
        await conn.execute('DELETE FROM auth_tokens WHERE token = ?', (token,))
        await conn.commit()


# ============ share token ============

async def create_share_token(
    meeting_id: int,
    created_by: Optional[int] = None,
    ttl: timedelta = SHARE_TTL,
) -> Dict[str, Any]:
    token = secrets.token_urlsafe(16)
    now = datetime.now(CST)
    expires = (now + ttl).isoformat(timespec='seconds')
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO share_tokens (token, meeting_id, created_by, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?)""",
            (token, meeting_id, created_by, now.isoformat(timespec='seconds'), expires),
        )
        await conn.commit()
    return {
        'token': token,
        'meeting_id': meeting_id,
        'expires_at': expires,
    }


async def resolve_share_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    async with get_conn() as conn:
        cur = await conn.execute(
            'SELECT * FROM share_tokens WHERE token = ?', (token,)
        )
        row = await cur.fetchone()
        if not row:
            return None
        if row['expires_at']:
            try:
                exp = datetime.fromisoformat(row['expires_at'])
                if datetime.now(CST) > exp:
                    return None
            except ValueError:
                pass
        return dict(row)


async def list_share_tokens(meeting_id: int):
    async with get_conn() as conn:
        cur = await conn.execute(
            'SELECT * FROM share_tokens WHERE meeting_id = ? ORDER BY created_at DESC',
            (meeting_id,),
        )
        return [dict(r) for r in await cur.fetchall()]
