import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import pymysql
import uuid
from datetime import datetime

# Google Sheets 연결 (기존 코드)
conn_gsheet = st.connection("gsheets", type=GSheetsConnection)

def load_gsheet_data(worksheet_name):
    try:
        df = conn_gsheet.read(worksheet=worksheet_name, ttl=0)
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
    conn_gsheet.update(worksheet=worksheet_name, data=df)
    st.cache_data.clear()


# =============================================================================
# MySQL 데이터베이스 연결 및 유틸리티 함수
# =============================================================================

def get_db_connection():
    """데이터베이스 연결 함수"""
    try:
        mysql_config = st.secrets["connections"]["mysql"]
        url = mysql_config["url"]
        url = url.replace("mysql+pymysql://", "")
        user_pass, host_db = url.split("@")
        user, password = user_pass.split(":")
        host_port, database = host_db.split("/")
        
        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port
            port = 3306
        
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

def execute_query(query, params=None):
    """쿼리 실행 함수 (INSERT, UPDATE, DELETE)"""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"쿼리 실행 실패: {e}")
        conn.close()
        return False

def fetch_query(query, params=None):
    """쿼리 결과 반환 함수 (SELECT) - DataFrame으로 반환"""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"쿼리 실행 실패: {e}")
        conn.close()
        return pd.DataFrame()


# =============================================================================
# 사용자 관리 함수
# =============================================================================

def get_or_create_user(name, email):
    """
    이름으로 사용자를 찾거나 새로 생성합니다.
    사용자 ID를 반환합니다.
    """
    user_df = fetch_query("SELECT id FROM users WHERE name = %s", params=(name,))
    if not user_df.empty:
        return user_df.iloc[0]['id']
    else:
        user_id = str(uuid.uuid4())[:8]
        execute_query(
            "INSERT INTO users (id, name, email, joined_at) VALUES (%s, %s, %s, NOW())",
            params=(user_id, name, email)
        )
        return user_id


# =============================================================================
# 메인 데이터 조회 함수
# =============================================================================

def get_all_data_joined():
    """
    restaurants, menu_items, menu_reviews, users를 조인하여
    종합적인 DataFrame을 반환합니다.
    """
    query = """
        SELECT 
            r.id as restaurant_id,
            r.name as restaurant_name,
            r.category,
            r.address,
            r.lat,
            r.lon,
            r.url,
            mi.item_name,
            mi.price,
            mr.rating,
            mr.comment,
            mr.timestamp,
            u.name as user_name
        FROM restaurants r
        LEFT JOIN menu_items mi ON r.id = mi.restaurant_id
        LEFT JOIN menu_reviews mr ON mi.id = mr.menu_item_id
        LEFT JOIN users u ON mr.user_id = u.id
    """
    return fetch_query(query)


# =============================================================================
# 데이터 저장 함수
# =============================================================================

def save_full_visit_data(
    user_name, user_email, 
    rest_name, rest_address, rest_category, rest_url, 
    menu_name, menu_price, 
    review_rating, review_comment
):
    """
    사용자, 맛집, 메뉴, 리뷰를 한 번에 처리하여 저장합니다.
    """
    # 1. 사용자 가져오기 또는 생성
    user_id = get_or_create_user(user_name, user_email)

    # 2. 맛집 가져오기 또는 생성
    rest_df = fetch_query(
        "SELECT id FROM restaurants WHERE name = %s AND address = %s",
        params=(rest_name, rest_address)
    )
    
    if not rest_df.empty:
        rest_id = rest_df.iloc[0]['id']
    else:
        # 주소로 좌표 가져오기
        from utils import get_coords
        lat, lon = get_coords(rest_address)
        if not lat:
            st.error("주소를 좌표로 변환할 수 없습니다.")
            return
        
        rest_id = str(uuid.uuid4())[:8]
        execute_query(
            """
            INSERT INTO restaurants (id, name, category, address, lat, lon, url, added_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            params=(rest_id, rest_name, rest_category, rest_address, lat, lon, rest_url)
        )

    # 3. 메뉴 아이템 생성
    menu_item_id = str(uuid.uuid4())[:8]
    execute_query(
        """
        INSERT INTO menu_items (id, restaurant_id, item_name, price, added_at)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        params=(menu_item_id, rest_id, menu_name, menu_price)
    )

    # 4. 메뉴 리뷰 생성
    review_id = str(uuid.uuid4())[:8]
    execute_query(
        """
        INSERT INTO menu_reviews (id, menu_item_id, user_id, rating, comment, timestamp)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """,
        params=(review_id, menu_item_id, user_id, review_rating, review_comment)
    )
    
    st.success("리뷰가 성공적으로 등록되었습니다!")
    st.cache_data.clear()  # 캐시 초기화
    st.rerun()


# =============================================================================
# 기타 조회 함수들 (필요시 사용)
# =============================================================================

@st.cache_data(ttl=60)
def get_all_restaurants():
    """모든 맛집 데이터를 가져오는 함수"""
    query = "SELECT id, name, category, address, url, lat, lon FROM restaurants;"
    df = fetch_query(query)
    if not df.empty:
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    return df

def get_reviews_by_restaurant(restaurant_id):
    """특정 맛집의 모든 리뷰를 가져오는 함수"""
    query = """
        SELECT mr.id, mr.menu_item_id, mr.user_id, mr.rating, mr.comment, mr.timestamp,
               u.name as user_name, mi.item_name, mi.price
        FROM menu_reviews mr
        LEFT JOIN users u ON mr.user_id = u.id
        LEFT JOIN menu_items mi ON mr.menu_item_id = mi.id
        WHERE mi.restaurant_id = %s
        ORDER BY mr.timestamp DESC;
    """
    df = fetch_query(query, params=(restaurant_id,))
    if not df.empty:
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    return df