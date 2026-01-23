import streamlit as st
import pandas as pd
from sqlalchemy import text
import uuid
from datetime import datetime
import re

# Centralized connection
conn_sql = st.connection("mysql", type="sql")

def execute_query(query, params=None):
    """For INSERT, UPDATE, DELETE queries."""
    with conn_sql.session as s:
        s.execute(text(query), params)
        s.commit()

def fetch_query(query, params=None, as_df=True):
    """For SELECT queries. Returns a pandas DataFrame by default."""
    result_df = conn_sql.query(sql=query, params=params, ttl=0)
    if as_df:
        return result_df
    else:
        # Return as list of lists for simpler iteration if needed
        return result_df.values.tolist()

# --- Email Validation ---
def is_valid_email(email):
    """이메일 형식을 정규 표현식으로 검사"""
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email) is not None

# --- User Management ---
def get_or_create_user(name, email):
    """
    Fetches a user by name or creates a new one if they don't exist.
    Requires email for creation. Returns the user's ID.
    """
    user_df = fetch_query("SELECT id FROM users WHERE name = :name", params={"name": name})
    if not user_df.empty:
        return user_df.iloc[0]['id']
    else:
        user_id = str(uuid.uuid4())[:8]
        execute_query(
            "INSERT INTO users (id, name, email, joined_at) VALUES (:id, :name, :email, :at)",
            params={"id": user_id, "name": name, "email": email, "at": datetime.now()}
        )
        return user_id

def get_all_users():
    """Fetches all users for login selection."""
    return fetch_query("SELECT id, name FROM users ORDER BY name")

# --- Auth Functions (Login.py style) ---
def register_user(user_id, email, name):
    """회원가입 함수"""
    query = """
    INSERT INTO users (id, email, name, joined_at)
    VALUES (:id, :email, :name, :at)
    """
    params = {"id": user_id, "email": email, "name": name, "at": datetime.now()}
    try:
        execute_query(query, params)
        st.success("회원가입이 완료되었습니다.")
    except Exception as e:
        st.error(f"회원가입 실패: {e}")

def login_user(user_id, email):
    """로그인 처리. 성공 시 True, 실패 시 False 반환."""
    query = "SELECT name FROM users WHERE id = :id AND email = :email"
    params = {"id": user_id, "email": email}
    result_df = fetch_query(query, params)
    
    if not result_df.empty:
        stored_name = result_df.iloc[0]['name']
        
        # 로그인 세션 관리
        st.session_state.user_id = user_id
        st.session_state.email = email
        st.session_state.logged_in = True
        st.session_state.user_name = stored_name
        st.success(f"로그인 성공! 환영합니다, {stored_name}님.")
        return True
    else:
        st.error("존재하지 않는 사용자이거나 이메일이 잘못되었습니다.")
        return False

def logout_user():
    """로그아웃 처리. 세션 상태를 초기화합니다."""
    # 세션 상태 초기화
    if 'user_id' in st.session_state:
        del st.session_state.user_id
    if 'email' in st.session_state:
        del st.session_state.email
    if 'logged_in' in st.session_state:
        del st.session_state.logged_in
    if 'user_name' in st.session_state:
        del st.session_state.user_name
    st.success("로그아웃되었습니다.")
    st.rerun()

# --- Login UI Functions (Login.py style) ---
def display_login_page():
    """로그인 페이지 표시"""
    st.title("로그인 페이지")
    user_id = st.text_input("아이디", placeholder="아이디를 입력해주세요.")
    email = st.text_input("이메일", placeholder="example@gmail.com")

    if st.button("로그인"):
        if not is_valid_email(email):
            st.error(
                "잘못된 이메일 형식입니다. 유효한 이메일 주소를 입력해주세요."
            )
        else:
            success = login_user(user_id, email)
            if success:
                st.rerun()

def display_register_page():
    """회원가입 페이지 표시"""
    st.title("회원가입 페이지")
    user_id = st.text_input("아이디", placeholder="사용하실 아이디를 입력하세요")
    email = st.text_input("이메일", placeholder="example@gmail.com")
    name = st.text_input("이름", placeholder="홍길동")

    if st.button("회원가입"):
        if not is_valid_email(email):
            st.error(
                "잘못된 이메일 형식입니다. 유효한 이메일 주소를 입력해주세요."
            )
        else:
            register_user(user_id, email, name)

# --- Login UI (Login.py style) ---
def show_login_page():
    """
    Login.py 스타일의 로그인 페이지를 표시합니다.
    Returns True if a user is logged in, False otherwise.
    """
    if st.session_state.get("logged_in"):
        return True

    # 로그인 전: 로그인/회원가입만 표시
    page = st.sidebar.selectbox("페이지 선택", ["로그인", "회원가입"])
    if page == "로그인":
        display_login_page()
    else:
        display_register_page()
            
    return False