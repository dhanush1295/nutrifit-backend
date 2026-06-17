"""
Database helper – thin wrapper around mysql.connector with connection pooling.
All route modules import `get_db()` to obtain a connection.
"""

import mysql.connector
from mysql.connector import pooling
from config import Config

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="nutrifit_pool",
            pool_size=5,
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
        )
    return _pool


def get_db():
    """Return a connection from the pool. Caller must call conn.close() when done."""
    return _get_pool().get_connection()


# ---------------------------------------------------------------------------
# DDL – executed once by seed_db.py
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) DEFAULT '',
    phone           VARCHAR(50)  DEFAULT '',
    gender          VARCHAR(10)  DEFAULT 'Male',
    age             INT          DEFAULT 25,
    height_cm       DOUBLE       DEFAULT 170,
    weight_kg       DOUBLE       DEFAULT 70,
    diet            VARCHAR(50)  DEFAULT 'pureVegetarian',
    conditions      TEXT,
    fasting_glucose DOUBLE       DEFAULT 110,
    carb_limit      VARCHAR(20)  DEFAULT 'moderate',
    healthkit_enabled TINYINT(1) DEFAULT 1,
    profile_photo   VARCHAR(255) DEFAULT NULL,
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS otp_codes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    email       VARCHAR(255) NOT NULL,
    code        VARCHAR(6)   NOT NULL,
    expires_at  TIMESTAMP    NOT NULL,
    used        TINYINT(1)   DEFAULT 0,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS meal_plans (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    plan_date   DATE         NOT NULL,
    meal_type   VARCHAR(20)  NOT NULL,
    food_name   VARCHAR(255) NOT NULL,
    emoji       VARCHAR(10)  DEFAULT '',
    calories    INT          DEFAULT 0,
    protein     INT          DEFAULT 0,
    carbs       INT          DEFAULT 0,
    fat         INT          DEFAULT 0,
    subtitle    VARCHAR(255) DEFAULT '',
    ingredients TEXT,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_date_meal (user_id, plan_date, meal_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS intake_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    log_date    DATE         NOT NULL,
    meal_name   VARCHAR(255) DEFAULT '',
    calories    INT          DEFAULT 0,
    protein     INT          DEFAULT 0,
    carbs       INT          DEFAULT 0,
    fat         INT          DEFAULT 0,
    portion_g   INT          DEFAULT 150,
    logged_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    role        VARCHAR(10)  NOT NULL,
    content     TEXT         NOT NULL,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS notifications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    icon        VARCHAR(50)  DEFAULT 'bell',
    icon_color  VARCHAR(20)  DEFAULT '#A78BFA',
    icon_bg     VARCHAR(20)  DEFAULT '#2D1B69',
    title       VARCHAR(255) NOT NULL,
    body        TEXT         NOT NULL,
    is_new      TINYINT(1)   DEFAULT 1,
    is_read     TINYINT(1)   DEFAULT 0,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS foods (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    emoji       VARCHAR(10)  DEFAULT '',
    calories    INT          DEFAULT 0,
    protein     INT          DEFAULT 0,
    carbs       INT          DEFAULT 0,
    fat         INT          DEFAULT 0,
    diet        VARCHAR(50)  DEFAULT 'pureVegetarian',
    avoid_for   TEXT,
    safe_for    TEXT,
    meal_times  TEXT,
    subtitle    VARCHAR(255) DEFAULT '',
    ingredients TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def create_tables():
    """Execute the DDL statements to create all tables."""
    conn = get_db()
    cursor = conn.cursor()
    for stmt in SCHEMA_SQL.split(";"):
        stmt = stmt.strip()
        if stmt:
            cursor.execute(stmt)
    conn.commit()
    cursor.close()
    conn.close()
