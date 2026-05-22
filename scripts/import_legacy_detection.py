#!/usr/bin/env python3
"""将 old_data/*.sql (SQL Server INSERT) 导入 data/meeting.db 中的 legacy_* 表。

用法:
  .venv/bin/python scripts/import_legacy_detection.py \\
    --dir "/mnt/d/WeixinSave/.../old_data"
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.meeting.db import DB_PATH  # noqa: E402
from src.meeting.legacy_schema import LEGACY_SCHEMA_SQL  # noqa: E402

DEFAULT_DIR = (
    '/mnt/d/WeixinSave/xwechat_files/ff67896_bbc4/msg/file/2026-05/数据库导出/old_data'
)

RE_VALUES = re.compile(r'VALUES \((.+)\); GO\s*$')


def _split_sql_values(raw: str) -> list:
    parts: list[str] = []
    cur: list[str] = []
    in_str = False
    i = 0
    while i < len(raw):
        ch = raw[i]
        if in_str:
            cur.append(ch)
            if ch == "'" and i + 1 < len(raw) and raw[i + 1] == "'":
                cur.append(raw[i + 1])
                i += 2
                continue
            if ch == "'":
                in_str = False
            i += 1
            continue
        if ch == "'":
            in_str = True
            cur.append(ch)
            i += 1
            continue
        if ch == ',':
            parts.append(''.join(cur).strip())
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    parts.append(''.join(cur).strip())
    return parts


def _parse_val(token: str):
    if token.upper() == 'NULL':
        return None
    if token.startswith("'") and token.endswith("'"):
        return token[1:-1].replace("''", "'")
    if '.' in token or 'e' in token.lower():
        try:
            return float(token)
        except ValueError:
            pass
    return int(token)


def _read_inserts(path: str):
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if not line.startswith('INSERT'):
                continue
            m = RE_VALUES.search(line)
            if not m:
                continue
            yield [_parse_val(t) for t in _split_sql_values(m.group(1))]


def import_all(data_dir: str, db_path: str = DB_PATH) -> dict:
    os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(LEGACY_SCHEMA_SQL)
    conn.execute('DELETE FROM legacy_actions')
    conn.execute('DELETE FROM legacy_concentration')
    conn.execute('DELETE FROM legacy_emotions')
    conn.execute('DELETE FROM legacy_students')
    conn.execute('DELETE FROM legacy_import_meta')

    # students + users
    students_path = os.path.join(data_dir, 'I_Students.sql')
    users_path = os.path.join(data_dir, 'I_Users.sql')
    users = {}
    if os.path.isfile(users_path):
        for row in _read_inserts(users_path):
            uid, name = int(row[0]), row[3]
            if name and name != 'O':
                users[uid] = str(name)

    if os.path.isfile(students_path):
        batch = []
        for row in _read_inserts(students_path):
            sid, user_id, _class_id, sno = int(row[0]), int(row[1]), row[2], row[3]
            display = users.get(user_id) or f'学生 #{sid}'
            batch.append((sid, display, str(sno) if sno else None))
        conn.executemany(
            'INSERT INTO legacy_students (student_id, display_name, student_no) VALUES (?, ?, ?)',
            batch,
        )

    def _batch_insert(table: str, cols: str, rows, chunk: int = 2000):
        placeholders = ','.join(['?'] * len(cols.split(',')))
        sql = f'INSERT INTO {table} ({cols}) VALUES ({placeholders})'
        buf = []
        for row in rows:
            buf.append(row)
            if len(buf) >= chunk:
                conn.executemany(sql, buf)
                buf.clear()
        if buf:
            conn.executemany(sql, buf)

    action_path = os.path.join(data_dir, 'I_Action.sql')
    if os.path.isfile(action_path):
        def _actions():
            for row in _read_inserts(action_path):
                yield (
                    int(row[0]), int(row[1]), int(row[2]), str(row[3]),
                    int(row[4]), int(row[5]), int(row[6]), int(row[7]), int(row[8]),
                    None if row[9] is None else int(row[9]),
                )
        _batch_insert(
            'legacy_actions',
            'id,group_id,student_id,ts,eat_drink,sleep,calling,phone,rehand,study',
            _actions(),
        )

    conc_path = os.path.join(data_dir, 'I_Concentration.sql')
    if os.path.isfile(conc_path):
        def _conc():
            for row in _read_inserts(conc_path):
                yield (int(row[0]), int(row[1]), int(row[2]), str(row[3]), float(row[4]))
        _batch_insert(
            'legacy_concentration',
            'id,group_id,student_id,ts,con_score',
            _conc(),
        )

    emo_path = os.path.join(data_dir, 'I_Emotion.sql')
    if os.path.isfile(emo_path):
        def _emo():
            for row in _read_inserts(emo_path):
                yield (
                    int(row[0]), int(row[1]), int(row[2]), str(row[3]),
                    float(row[4]), float(row[5]), float(row[6]), float(row[7]),
                    float(row[8]), float(row[9]), float(row[10]),
                )
        _batch_insert(
            'legacy_emotions',
            'id,group_id,student_id,ts,angry,disgusted,fearful,happy,sad,surprised,neutral',
            _emo(),
        )

    now = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        'INSERT INTO legacy_import_meta (key, value) VALUES (?, ?)',
        [('imported_at', now), ('source_dir', data_dir)],
    )
    conn.commit()

    stats = {
        k: conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        for k, t in [
            ('students', 'legacy_students'),
            ('actions', 'legacy_actions'),
            ('concentration', 'legacy_concentration'),
            ('emotions', 'legacy_emotions'),
        ]
    }
    conn.close()
    return stats


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dir', default=DEFAULT_DIR, help='old_data 目录')
    p.add_argument('--db', default=DB_PATH, help='SQLite 路径')
    args = p.parse_args()
    if not os.path.isdir(args.dir):
        print(f'目录不存在: {args.dir}', file=sys.stderr)
        sys.exit(1)
    stats = import_all(args.dir, args.db)
    print('导入完成 ->', args.db)
    for k, v in stats.items():
        print(f'  {k}: {v:,}')


if __name__ == '__main__':
    main()
