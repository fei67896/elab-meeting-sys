"""老系统状态检测数据表 (SQL Server 导出 -> SQLite)"""

LEGACY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS legacy_students (
    student_id    INTEGER PRIMARY KEY,
    display_name  TEXT,
    student_no    TEXT
);

CREATE TABLE IF NOT EXISTS legacy_actions (
    id         INTEGER PRIMARY KEY,
    group_id   INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    ts         TEXT NOT NULL,
    eat_drink  INTEGER NOT NULL DEFAULT 0,
    sleep      INTEGER NOT NULL DEFAULT 0,
    calling    INTEGER NOT NULL DEFAULT 0,
    phone      INTEGER NOT NULL DEFAULT 0,
    rehand     INTEGER NOT NULL DEFAULT 0,
    study      INTEGER
);

CREATE INDEX IF NOT EXISTS idx_legacy_actions_group_student
    ON legacy_actions(group_id, student_id, ts);

CREATE TABLE IF NOT EXISTS legacy_concentration (
    id         INTEGER PRIMARY KEY,
    group_id   INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    ts         TEXT NOT NULL,
    con_score  REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_legacy_conc_group_student
    ON legacy_concentration(group_id, student_id, ts);

CREATE TABLE IF NOT EXISTS legacy_emotions (
    id         INTEGER PRIMARY KEY,
    group_id   INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    ts         TEXT NOT NULL,
    angry      REAL NOT NULL,
    disgusted  REAL NOT NULL,
    fearful    REAL NOT NULL,
    happy      REAL NOT NULL,
    sad        REAL NOT NULL,
    surprised  REAL NOT NULL,
    neutral    REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_legacy_emo_group_student
    ON legacy_emotions(group_id, student_id, ts);

CREATE TABLE IF NOT EXISTS legacy_import_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""
