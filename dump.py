import mysql.connector
from config import Config

def dump():
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        port=Config.MYSQL_PORT,
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    for r in cursor.fetchall():
        print(r)
    cursor.close()
    conn.close()

if __name__ == "__main__":
    dump()
