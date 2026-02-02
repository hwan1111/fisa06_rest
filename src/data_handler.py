# 민석 수정
import streamlit as st
import pandas as pd
import pymysql
from login import execute_query, get_db_connection
import uuid
from datetime import datetime
from urllib.parse import urlparse

# Google Sheets 연결 비활성화 (secrets.toml 체크 방지)
# from streamlit_gsheets import GSheetsConnection
# conn_gsheet = st.connection("gsheets", type=GSheetsConnection)

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
        print(f"쿼리 실행 실패 (fetch_query): {e}")
        if conn:
            conn.close()
        return pd.DataFrame()

def get_or_create_user(name, email):
    """이름으로 사용자를 찾거나 새로 생성합니다."""
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

def get_all_data_joined():
    """종합 데이터 조회 (DB 실패 시에도 명시적 컬럼을 가진 DataFrame 반환)"""
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
    
    expected_columns = [
        "restaurant_id", "restaurant_name", "category", "address", 
        "lat", "lon", "url", "item_name", "price", 
        "rating", "comment", "timestamp", "user_name"
    ]
    
    df = fetch_query(query)
    
    if df.empty:
        return pd.DataFrame(columns=expected_columns)
    
    # [수정] 데이터 타입 강제 변환 및 잘못된 데이터 제거
    if 'rating' in df.columns:
        # 문자열 "rating" 등이 섞여있을 경우 제거
        df = df[df['rating'] != 'rating']
        # 숫자로 변환 (변환 불가 값은 NaN 처리)
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        
    if 'lat' in df.columns:
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        
    if 'lon' in df.columns:
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    
    return df

def save_full_visit_data(
    user_name, user_email, 
    rest_name, rest_address, rest_category, rest_url, 
    menu_name, menu_price, 
    review_rating, review_comment
):
    from utils import get_coords
    cleaned_address, lat, lon = get_coords(rest_address)

    if not lat or not lon:
        st.error("주소를 좌표로 변환할 수 없습니다. 더 상세한 주소를 입력해 주세요.")
        return
    
    final_address = cleaned_address if cleaned_address else rest_address
    user_id = get_or_create_user(user_name, user_email)

    rest_df = fetch_query(
        "SELECT id FROM restaurants WHERE name = %s AND address = %s",
        params=(rest_name, final_address)
    )
    
    if not rest_df.empty:
        rest_id = rest_df.iloc[0]['id']
    else:
        rest_id = str(uuid.uuid4())[:8]
        execute_query(
            """
            INSERT INTO restaurants (id, name, category, address, lat, lon, url, added_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            params=(rest_id, rest_name, rest_category, final_address, lat, lon, rest_url)
        )

    menu_item_id = str(uuid.uuid4())[:8]
    execute_query(
        """
        INSERT INTO menu_items (id, restaurant_id, item_name, price, added_at)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        params=(menu_item_id, rest_id, menu_name, menu_price)
    )

    review_id = str(uuid.uuid4())[:8]
    execute_query(
        """
        INSERT INTO menu_reviews (id, menu_item_id, user_id, rating, comment, timestamp)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """,
        params=(review_id, menu_item_id, user_id, review_rating, review_comment)
    )
    
    st.success("리뷰가 성공적으로 등록되었습니다!")
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=60)
def get_all_restaurants():
    query = "SELECT id, name, category, address, url, lat, lon FROM restaurants;"
    df = fetch_query(query)
    
    # [수정] 타입 변환 로직 강화
    if not df.empty:
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    else:
        return pd.DataFrame(columns=["id", "name", "category", "address", "url", "lat", "lon"])
    return df

def get_reviews_by_restaurant(restaurant_id):
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
    
    # [수정] 타입 변환 로직 강화
    if not df.empty:
        if 'rating' in df.columns:
            df = df[df['rating'] != 'rating']
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    else:
        return pd.DataFrame(columns=["id", "menu_item_id", "user_id", "rating", "comment", "timestamp", "user_name", "item_name", "price"])
    return df

# =============================================================================
# Party (맛집 원정대) Functions
# =============================================================================

def create_party(restaurant_id, host_id, max_people, is_anonymous):
    party_id = str(uuid.uuid4())[:8]
    query_party = """
        INSERT INTO parties (id, restaurant_id, host_id, max_people, is_anonymous, created_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'OPEN')
    """
    params_party = (party_id, restaurant_id, host_id, max_people, is_anonymous, datetime.now())
    execute_query(query_party, params_party)
    try:
        query_host = "INSERT INTO party_participants (party_id, user_id, joined_at) VALUES (%s, %s, %s)"
        execute_query(query_host, (party_id, host_id, datetime.now()))
    except Exception as e:
        print(f"Host Join Error: {e}")
    return party_id

def join_party(party_id, user_id):
    check_query = """
        SELECT p.max_people, COUNT(pp.user_id) as current_people
        FROM parties p
        LEFT JOIN party_participants pp ON p.id = pp.party_id
        WHERE p.id = %s
        GROUP BY p.id
    """
    df = fetch_query(check_query, (party_id,))
    if df.empty:
        return False, "존재하지 않는 파티입니다."
    
    max_p = df.iloc[0]['max_people']
    curr_p = df.iloc[0]['current_people']
    
    if curr_p >= max_p:
        return False, "앗! 그 사이에 자리가 꽉 찼습니다. 😭"
    
    check_user_query = "SELECT * FROM party_participants WHERE party_id=%s AND user_id=%s"
    check_user_df = fetch_query(check_user_query, (party_id, user_id))
    if not check_user_df.empty:
        return False, "이미 참여 중인 파티입니다."

    try:
        insert_query = "INSERT INTO party_participants (party_id, user_id, joined_at) VALUES (%s, %s, %s)"
        execute_query(insert_query, (party_id, user_id, datetime.now()))
        return True, "파티 참여 성공! 🎉"
    except Exception as e:
        return False, f"오류가 발생했습니다: {str(e)}"

def leave_party(party_id, user_id):
    query = "DELETE FROM party_participants WHERE party_id = %s AND user_id = %s"
    execute_query(query, (party_id, user_id))

def get_active_parties():
    query = """
        SELECT 
            p.id, 
            p.restaurant_id, 
            r.name as restaurant_name,
            p.host_id,
            u.name as host_name,
            p.max_people,
            p.is_anonymous,
            p.created_at,
            COUNT(pp.user_id) as current_people
        FROM parties p
        JOIN restaurants r ON p.restaurant_id = r.id
        JOIN users u ON p.host_id = u.id
        LEFT JOIN party_participants pp ON p.id = pp.party_id
        WHERE p.status = 'OPEN' AND DATE(p.created_at) = CURDATE()
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """
    df = fetch_query(query)
    if df.empty:
        cols = ["id", "restaurant_id", "restaurant_name", "host_id", "host_name", 
                "max_people", "is_anonymous", "created_at", "current_people"]
        return pd.DataFrame(columns=cols)
    return df

def get_party_participants(party_id):
    query = """
        SELECT u.id, u.name
        FROM party_participants pp
        JOIN users u ON pp.user_id = u.id
        WHERE pp.party_id = %s
        ORDER BY pp.joined_at ASC
    """
    df = fetch_query(query, (party_id,))
    if df.empty:
        return pd.DataFrame(columns=["id", "name"])
    return df

def update_party(party_id, restaurant_id, max_people, is_anonymous):
    query = """
        UPDATE parties 
        SET restaurant_id = %s, max_people = %s, is_anonymous = %s
        WHERE id = %s
    """
    params = (restaurant_id, max_people, is_anonymous, party_id)
    execute_query(query, params)

def delete_party(party_id):
    query = "DELETE FROM parties WHERE id = %s"
    execute_query(query, (party_id,))