import pymysql

def get_db_connection():
    return pymysql.connect(
        host="118.67.131.22",    # 실제 MySQL 서버의 호스트 IP
        port=3306,               # MySQL 기본 포트
        user="fisaai6",          # MySQL 사용자명
        password="Woorifisa!6",  # MySQL 비밀번호
        database="matjeomyo"     # 사용할 데이터베이스명
    )
