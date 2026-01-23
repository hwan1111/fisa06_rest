import streamlit as st
import pandas as pd
from sqlalchemy import text
import uuid
from datetime import datetime

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

# --- Login UI ---
def show_login_page():
    """
    Displays a simple login page for user selection or creation.
    Returns True if a user is logged in, False otherwise.
    """
    if st.session_state.get("logged_in"):
        return True

    st.header("👤 사용자 선택 또는 생성")
    st.write("맛집을 등록하고 리뷰를 남기려면 먼저 사용자를 선택해야 합니다.")
    
    users = get_all_users()
    user_list = [""] + users['name'].tolist()
    
    # User selection dropdown
    selected_user_name = st.selectbox("기존 사용자 선택:", user_list)
    
    if st.button("✅ 선택한 사용자로 계속하기"):
        if selected_user_name:
            user_info = users[users['name'] == selected_user_name].iloc[0]
            st.session_state["logged_in"] = True
            st.session_state["user_name"] = user_info['name']
            st.session_state["user_id"] = user_info['id']
            st.rerun()
        else:
            st.warning("목록에서 사용자를 선택해 주세요.")

    st.markdown("---")

    # New user creation
    st.subheader("새 사용자 만들기")
    new_user_name = st.text_input("새로운 사용자 이름:")
    new_user_email = st.text_input("이메일:") # Add email input

    if st.button("🚀 새 이름으로 시작하기"):
        if new_user_name and new_user_email:
            if new_user_name in user_list:
                st.error("이미 존재하는 이름입니다. 위 목록에서 선택해 주세요.")
            else:
                user_id = get_or_create_user(new_user_name, new_user_email)
                st.session_state["logged_in"] = True
                st.session_state["user_name"] = new_user_name
                st.session_state["user_id"] = user_id
                st.rerun()
        else:
            st.warning("새로운 사용자 이름과 이메일을 모두 입력해 주세요.")
            
    return False