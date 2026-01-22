import streamlit as st
import re  # 정규 표현식을 사용하기 위해 추가
from login.auth import register_user, login_user 

# 이메일 형식 검사 함수
def is_valid_email(email):
    """ 이메일 형식을 정규 표현식으로 검사 """
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

# 로그인/회원가입 화면
def display_login_page():
    st.title("로그인 페이지")

    # 기본 예시값을 설정 (아이디, 이메일, 이름)
    user_id = st.text_input("아이디", placeholder="아이디를 입력해주세요.")
    email = st.text_input("이메일", placeholder="example@gmail.com")

    # 로그인 버튼 클릭 시에만 이메일 형식 검사를 하도록 조건문 추가
    if st.button("로그인"):
        if not is_valid_email(email):
            st.error("잘못된 이메일 형식입니다. 유효한 이메일 주소를 입력해주세요.")
        else:
            login_user(user_id, email)

# 로그인 상태 확인 화면
def display_logged_in_page():
    st.title(f"안녕하세요, {st.session_state.user_name}님!")
    st.write("로그인에 성공하셨습니다.")
    # 로그아웃 버튼 추가
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None

# 회원가입 화면 [닉네임, 이메일, 이름]
def display_register_page():
    st.title("회원가입 페이지")

    # 기본 예시값을 설정 (아이디, 이메일, 이름)
    user_id = st.text_input("아이디", placeholder="사용하실 아이디를 입력하세요")
    email = st.text_input("이메일", placeholder="example@gmail.com")
    name = st.text_input("이름", placeholder="홍길동")

    # 회원가입 버튼 클릭 시에만 이메일 형식 검사를 하도록 조건문 추가
    if st.button("회원가입"):
        if not is_valid_email(email):
            st.error("잘못된 이메일 형식입니다. 유효한 이메일 주소를 입력해주세요.")
        else:
            register_user(user_id, email, name)

# 페이지 선택
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    page = st.sidebar.selectbox("페이지 선택", ["로그인", "회원가입"])

    if page == "로그인":
        display_login_page()
    else:
        display_register_page()
else:
    display_logged_in_page()
