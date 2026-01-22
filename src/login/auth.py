import streamlit as st
from .login_data_handle import execute_query, fetch_query

# 회원가입 함수 - minseok
def register_user(user_id, email=None, name=None):
    # 쿼리문 저장 ㄱ
    query = """
    INSERT INTO users (id, email, name, joined_at)
    VALUES (%s, %s, %s, NOW());
    """
    params = (user_id, email, name)
    try:
        execute_query(query, params)
        st.success("회원가입이 완료되었습니다.")
    except Exception as e:
        st.error(f"회원가입 실패: {e}")

# 로그인 함수 - minseok
def login_user(user_id, email):
    query = "SELECT name FROM users WHERE id = %s AND email = %s;"
    params = (user_id, email)
    result = fetch_query(query, params)

    if result:
        stored_name = result[0][0]
        
        # 로그인 세션 관리 <- 아주 중요합니다잉~~
        st.session_state.user_id = user_id # 사용자 아이디 저장
        st.session_state.email = email      # 사용자 이메일 저장
        st.session_state.logged_in = True # 사용자 이메일 저장
        st.session_state.user_name = stored_name # 사용자 이름 세션에 저장
        st.success(f"로그인 성공! 환영합니다, {stored_name}님.") 
    else: 
        st.error("존재하지 않는 사용자이거나 이메일이 잘못되었습니다.")




