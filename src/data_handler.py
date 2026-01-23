# 민석 수정
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import pymysql

# Google Sheets 연결 (기존 코드)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gsheet_data(worksheet_name):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        if df is None or df.empty: raise ValueError
        if worksheet_name == "restaurants":
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        else:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        return df
    except:
        if worksheet_name == "restaurants":
            return pd.DataFrame(columns=["id", "name", "category", "address", "url", "lat", "lon"])
        else:
            return pd.DataFrame(columns=["id", "rest_id", "parent_id", "rating", "comment", "timestamp", "user"])

def save_gsheet_data(df, worksheet_name):
    conn.update(worksheet=worksheet_name, data=df)
    st.cache_data.clear()

# ========== SQL 버전 함수들 ==========

def get_db_connection():
    """데이터베이스 연결 함수"""
    try:
        # .streamlit/secrets.toml에서 MySQL 연결 정보 가져오기
        mysql_config = st.secrets["connections"]["mysql"]
        # URL 형식: mysql+pymysql://user:password@host:port/database
        url = mysql_config["url"]
        # URL 파싱
        url = url.replace("mysql+pymysql://", "")
        user_pass, host_db = url.split("@")
        user, password = user_pass.split(":")
        host_port, database = host_db.split("/")
        
        # 포트가 있는지 확인
        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port
            port = 3306  # 기본 포트
        
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        return conn
    except Exception as e:
        st.error(f"데이터베이스 연결 실패: {e}")
        return None

@st.cache_data(ttl=60)
def get_all_restaurants():
    """모든 맛집 데이터를 가져오는 함수"""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame(columns=["id", "name", "category", "address", "url", "lat", "lon"])
    
    try:
        query = "SELECT id, name, category, address, url, lat, lon FROM restaurants;"
        df = pd.read_sql(query, conn)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        conn.close()
        return df
    except Exception as e:
        st.error(f"맛집 데이터 조회 실패: {e}")
        conn.close()
        return pd.DataFrame(columns=["id", "name", "category", "address", "url", "lat", "lon"])

@st.cache_data(ttl=60)
def get_all_reviews():
    """모든 리뷰 데이터를 가져오는 함수"""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame(columns=["id", "restaurant_id", "user_id", "rating", "comment", "created_at", "parent_id"])
    
    try:
        query = """
        SELECT r.id, r.restaurant_id, r.user_id, r.rating, r.comment, r.created_at, r.parent_id,
               u.name as user_name
        FROM reviews r
        LEFT JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC;
        """
        df = pd.read_sql(query, conn)
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        conn.close()
        return df
    except Exception as e:
        st.error(f"리뷰 데이터 조회 실패: {e}")
        conn.close()
        return pd.DataFrame(columns=["id", "restaurant_id", "user_id", "rating", "comment", "created_at", "parent_id"])

def add_restaurant(name, category, address, url, lat, lon):
    """맛집 추가 함수. 추가된 맛집의 ID를 반환"""
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO restaurants (name, category, address, url, lat, lon, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW());
        """
        params = (name, category, address, url, float(lat), float(lon))
        cursor.execute(query, params)
        conn.commit()
        restaurant_id = cursor.lastrowid
        cursor.close()
        conn.close()
        st.cache_data.clear()  # 캐시 초기화
        return restaurant_id
    except Exception as e:
        st.error(f"맛집 추가 실패: {e}")
        conn.close()
        return None

def add_review(restaurant_id, user_id, rating, comment, parent_id=None):
    """리뷰 추가 함수"""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        if parent_id is None:
            query = """
            INSERT INTO reviews (restaurant_id, user_id, rating, comment, created_at)
            VALUES (%s, %s, %s, %s, NOW());
            """
            params = (restaurant_id, user_id, float(rating), comment)
        else:
            query = """
            INSERT INTO reviews (restaurant_id, user_id, rating, comment, parent_id, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW());
            """
            params = (restaurant_id, user_id, float(rating), comment, parent_id)
        
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()
        st.cache_data.clear()  # 캐시 초기화
        return True
    except Exception as e:
        st.error(f"리뷰 추가 실패: {e}")
        conn.close()
        return False

def get_reviews_by_restaurant(restaurant_id):
    """특정 맛집의 모든 리뷰를 가져오는 함수"""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame(columns=["id", "restaurant_id", "user_id", "rating", "comment", "created_at", "parent_id", "user_name"])
    
    try:
        query = """
        SELECT r.id, r.restaurant_id, r.user_id, r.rating, r.comment, r.created_at, r.parent_id,
               u.name as user_name
        FROM reviews r
        LEFT JOIN users u ON r.user_id = u.id
        WHERE r.restaurant_id = %s
        ORDER BY r.created_at ASC;
        """
        df = pd.read_sql(query, conn, params=(restaurant_id,))
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        conn.close()
        return df
    except Exception as e:
        st.error(f"리뷰 조회 실패: {e}")
        conn.close()
        return pd.DataFrame(columns=["id", "restaurant_id", "user_id", "rating", "comment", "created_at", "parent_id", "user_name"])
