"""
通宝奖励查询系统 - 数据库模块
"""
import sqlite3
import os
from datetime import datetime
from config import DB_PATH


def get_db():
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()

    # 创建通宝奖励记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            reward REAL NOT NULL DEFAULT 0,
            record_date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            UNIQUE(phone, record_date)
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_phone ON rewards(phone)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_record_date ON rewards(record_date)")

    # 创建同步日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_time TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            status TEXT NOT NULL,
            record_count INTEGER DEFAULT 0,
            message TEXT
        )
    """)

    conn.commit()
    conn.close()


def upsert_reward(phone, reward, record_date):
    """插入或更新一条奖励记录"""
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO rewards (phone, reward, record_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(phone, record_date)
        DO UPDATE SET reward = ?, updated_at = ?
    """, (phone, reward, record_date, now, now, reward, now))

    conn.commit()
    conn.close()


def get_rewards_by_phone(phone):
    """根据手机号查询所有奖励记录"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT phone, reward, record_date, created_at, updated_at
        FROM rewards
        WHERE phone = ?
        ORDER BY record_date DESC
    """, (phone,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_total_reward_by_phone(phone):
    """根据手机号查询总奖励"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(reward), 0) as total, COUNT(*) as days
        FROM rewards
        WHERE phone = ?
    """, (phone,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {"total": 0, "days": 0}


def get_all_phones():
    """获取所有手机号"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT phone FROM rewards ORDER BY phone")
    rows = cursor.fetchall()
    conn.close()
    return [row["phone"] for row in rows]


def get_stats():
    """获取系统统计信息"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(DISTINCT phone) as users, COUNT(*) as records, COALESCE(SUM(reward), 0) as total FROM rewards")
    stats = dict(cursor.fetchone())

    cursor.execute("""
        SELECT sync_time, status, record_count, message
        FROM sync_log
        ORDER BY sync_time DESC
        LIMIT 1
    """)
    last_sync = cursor.fetchone()
    stats["last_sync"] = dict(last_sync) if last_sync else None

    conn.close()
    return stats


def log_sync(status, record_count=0, message=""):
    """记录同步日志"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sync_log (status, record_count, message)
        VALUES (?, ?, ?)
    """, (status, record_count, message))

    conn.commit()
    conn.close()


def get_dashboard_data():
    """获取看板数据"""
    conn = get_db()
    cursor = conn.cursor()

    # 总体统计
    cursor.execute("""
        SELECT
            COUNT(DISTINCT phone) as total_users,
            COUNT(*) as total_records,
            COALESCE(SUM(reward), 0) as total_reward,
            COALESCE(AVG(reward), 0) as avg_reward
        FROM rewards
    """)
    overview = dict(cursor.fetchone())

    # 每日趋势（最近30天）
    cursor.execute("""
        SELECT
            record_date,
            COUNT(*) as record_count,
            SUM(reward) as daily_reward,
            COUNT(DISTINCT phone) as active_users
        FROM rewards
        WHERE record_date >= date('now', '-30 days')
        GROUP BY record_date
        ORDER BY record_date ASC
    """)
    daily_trend = [dict(row) for row in cursor.fetchall()]

    # 排行榜（前10名）
    cursor.execute("""
        SELECT
            phone,
            SUM(reward) as total_reward,
            COUNT(*) as record_days,
            COALESCE(AVG(reward), 0) as avg_reward
        FROM rewards
        GROUP BY phone
        ORDER BY total_reward DESC
        LIMIT 10
    """)
    leaderboard = [dict(row) for row in cursor.fetchall()]

    # 奖励分布
    cursor.execute("""
        SELECT
            CASE
                WHEN reward < 10 THEN '0-10'
                WHEN reward < 50 THEN '10-50'
                WHEN reward < 100 THEN '50-100'
                WHEN reward < 500 THEN '100-500'
                ELSE '500+'
            END as reward_range,
            COUNT(*) as count
        FROM rewards
        GROUP BY reward_range
        ORDER BY MIN(reward)
    """)
    distribution = [dict(row) for row in cursor.fetchall()]

    # 活跃度分析（按周统计）
    cursor.execute("""
        SELECT
            strftime('%W', record_date) as week_num,
            COUNT(DISTINCT phone) as active_users,
            SUM(reward) as weekly_reward
        FROM rewards
        WHERE record_date >= date('now', '-8 weeks')
        GROUP BY week_num
        ORDER BY week_num ASC
    """)
    weekly_activity = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "overview": overview,
        "daily_trend": daily_trend,
        "leaderboard": leaderboard,
        "distribution": distribution,
        "weekly_activity": weekly_activity
    }
