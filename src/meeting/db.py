"""SQLite 连接与建表

使用 aiosqlite 提供异步访问，避免阻塞 aiohttp 事件循环。
数据库文件存放在仓库根目录 data/meeting.db，启动时自动建表。
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiosqlite

# 数据库路径相对仓库根目录，由 init_db 在首次启动时创建
DB_PATH = os.path.join('data', 'meeting.db')

SCHEMA_SQL = """
-- 用户: owner = 主账号 (zhaoyifei), guest = 凭分享链接登录的临时用户
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    display_name  TEXT,
    role          TEXT NOT NULL DEFAULT 'guest',  -- owner | guest
    created_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 会话 token: 简单 random token, 写库后下发给客户端
CREATE TABLE IF NOT EXISTS auth_tokens (
    token       TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    created_at  TEXT NOT NULL,
    expires_at  TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens(user_id);

-- 分享 token: 一个会议可以有多条分享链接 (例如不同有效期)
CREATE TABLE IF NOT EXISTS share_tokens (
    token       TEXT PRIMARY KEY,
    meeting_id  INTEGER NOT NULL,
    created_by  INTEGER,
    created_at  TEXT NOT NULL,
    expires_at  TEXT,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_share_tokens_meeting ON share_tokens(meeting_id);

-- 会议
CREATE TABLE IF NOT EXISTS meetings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    start_time   TEXT NOT NULL,
    end_time     TEXT,
    meeting_url  TEXT,
    meeting_code TEXT UNIQUE,
    description  TEXT,
    status       TEXT NOT NULL DEFAULT 'scheduled',
    mode         TEXT NOT NULL DEFAULT 'online',  -- online | offline | hybrid
    location     TEXT,                             -- 线下时的地点
    created_by   INTEGER,                          -- users.id, 创建者
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time);
CREATE INDEX IF NOT EXISTS idx_meetings_status     ON meetings(status);

-- 议程
-- category: project_report 项目汇报 / research_report 科研汇报 / general 综合 / other 其他
-- mode: online | offline (议程级别也允许指定, 兼容混合会议)
CREATE TABLE IF NOT EXISTS agenda_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id   INTEGER NOT NULL,
    seq          INTEGER NOT NULL,
    topic        TEXT NOT NULL,
    owner        TEXT,
    duration_min INTEGER,
    notes        TEXT,
    category     TEXT NOT NULL DEFAULT 'general',
    mode         TEXT NOT NULL DEFAULT 'online',
    created_by   INTEGER,
    created_at   TEXT,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_agenda_meeting ON agenda_items(meeting_id);

-- 参会人 + attendance 状态合并存这张表
-- user_id 非空 = 注册账号(含 guest); name 是显示名
-- attendance_status: pending | attending | declined
CREATE TABLE IF NOT EXISTS participants (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id        INTEGER NOT NULL,
    user_id           INTEGER,
    name              TEXT NOT NULL,
    email             TEXT,
    role              TEXT NOT NULL DEFAULT 'attendee', -- host | attendee | optional
    attendance_status TEXT NOT NULL DEFAULT 'pending',
    responded_at      TEXT,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_participant_meeting ON participants(meeting_id);
CREATE INDEX IF NOT EXISTS idx_participant_name    ON participants(name);
CREATE INDEX IF NOT EXISTS idx_participant_user    ON participants(user_id);

-- 指令历史
CREATE TABLE IF NOT EXISTS command_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    user_id     INTEGER,
    user_input  TEXT NOT NULL,
    intent      TEXT,
    params_json TEXT,
    result_json TEXT,
    reply_text  TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_history_ts ON command_history(ts DESC);
"""


async def init_db(db_path: str = DB_PATH) -> None:
    """创建数据目录, 建表, 并 seed 默认 owner 用户。幂等。"""
    from .legacy_schema import LEGACY_SCHEMA_SQL

    os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute('PRAGMA foreign_keys = ON;')
        await conn.executescript(SCHEMA_SQL)
        await conn.executescript(LEGACY_SCHEMA_SQL)
        await conn.commit()

    # 延迟导入避免循环依赖
    from .auth import ensure_default_owners
    await ensure_default_owners()


@asynccontextmanager
async def get_conn(db_path: str = DB_PATH) -> AsyncIterator[aiosqlite.Connection]:
    """获取数据库连接的上下文管理器，自动开启外键与 Row 工厂。"""
    conn = await aiosqlite.connect(db_path)
    try:
        await conn.execute('PRAGMA foreign_keys = ON;')
        conn.row_factory = aiosqlite.Row
        yield conn
    finally:
        await conn.close()
