import streamlit as st
import re
import pymysql
from urllib.parse import urlparse  # [수정] URL 파싱 모듈 추가

def get_db_connection():
    """데이터베이스 연결 함수 (pymysql 전용)"""
    try:
        # secrets.toml에서 정보 가져오기
        mysql_config = st.secrets["connections"]["mysql"]
        url = mysql_config["url"]
        
        # [수정] urllib를 사용하여 안전하게 파싱
        parsed = urlparse(url)
        
        # 호스트와 포트 분리
        host = parsed.hostname
        port = parsed.port or 3306
        user = parsed.username
        password = parsed.password
        database = parsed.path.lstrip("/")  # 앞에 붙은 '/' 제거

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
    """쿼리 실행 함수"""
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
    """쿼리 결과 반환 함수"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        st.error(f"쿼리 실행 실패: {e}")
        conn.close()
        return None
def is_valid_email(email):
    """이메일 형식을 정규 표현식으로 검사"""
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email) is not None
def register_user(user_id, email, name):
    """회원가입 처리"""
    # 중복 체크
    check_query = "SELECT id FROM users WHERE id = %s OR email = %s;"
    check_params = (user_id, email)
    existing = fetch_query(check_query, check_params)
    if existing:
        st.error("이미 존재하는 아이디 또는 이메일입니다.")
        return False
    # 회원가입 쿼리
    query = """
    INSERT INTO users (id, email, name, joined_at)
    VALUES (%s, %s, %s, NOW());
    """
    params = (user_id, email, name)
    if execute_query(query, params):
        st.success("회원가입이 완료되었습니다. 로그인해주세요.")
        return True
    else:
        return False
def login_user(user_id, email):
    """로그인 처리. 성공 시 True, 실패 시 False 반환."""
    query = "SELECT name FROM users WHERE id = %s AND email = %s;"
    params = (user_id, email)
    result = fetch_query(query, params)
    if result:
        stored_name = result[0][0]
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
def show_login_page():
    """로그인 페이지를 표시하고, 로그인 성공 시 True를 반환"""
    # 이미 로그인되어 있으면 True 반환
    if "logged_in" in st.session_state and st.session_state.logged_in:
        return True
    # 로그인/회원가입 탭 선택
    tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])
    with tab1:
        st.markdown("### 로그인")
        st.markdown("---")
        with st.form("login_form", clear_on_submit=False):
            user_id = st.text_input("아이디", placeholder="아이디를 입력해주세요.", key="login_id")
            email = st.text_input("이메일", placeholder="example@gmail.com", key="login_email")
            submitted = st.form_submit_button("로그인", use_container_width=True)
            if submitted:
                if not user_id:
                    st.error("아이디를 입력해주세요.")
                elif not email:
                    st.error("이메일을 입력해주세요.")
                elif not is_valid_email(email):
                    st.error("잘못된 이메일 형식입니다. 유효한 이메일 주소를 입력해주세요.")
                else:
                    success = login_user(user_id, email)
                    if success:
                        st.rerun()
    with tab2:
        st.markdown("### 회원가입")
        st.markdown("---")
        with st.form("register_form", clear_on_submit=True):
            user_id = st.text_input("아이디", placeholder="사용하실 아이디를 입력하세요", key="register_id")
            email = st.text_input("이메일", placeholder="example@gmail.com", key="register_email")
            name = st.text_input("이름", placeholder="홍길동", key="register_name")
            submitted = st.form_submit_button("회원가입", use_container_width=True)
            if submitted:
                if not user_id:
                    st.error("아이디를 입력해주세요.")
                elif not email:
                    st.error("이메일을 입력해주세요.")
                elif not name:
                    st.error("이름을 입력해주세요.")
                elif not is_valid_email(email):
                    st.error("잘못된 이메일 형식입니다. 유효한 이메일 주소를 입력해주세요.")
                else:
                    success = register_user(user_id, email, name)
                    if success:
                        st.info("로그인 탭에서 로그인해주세요.")
    return False
def logout_user():
    """로그아웃 처리"""
    # 세션 상태 초기화
    if "logged_in" in st.session_state:
        del st.session_state.logged_in
    if "user_id" in st.session_state:
        del st.session_state.user_id
    if "email" in st.session_state:
        del st.session_state.email
    if "user_name" in st.session_state:
        del st.session_state.user_name
    st.success("로그아웃되었습니다.")
    st.rerun()