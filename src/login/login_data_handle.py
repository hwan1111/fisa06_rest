import pymysql # minseok
from .login_config import get_db_connection # minseok

# 쿼리 실행 함수  - minseok
def execute_query(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    cursor.close()
    conn.close()

# 쿼리 결과 반환 함수 - minseok
def fetch_query(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result