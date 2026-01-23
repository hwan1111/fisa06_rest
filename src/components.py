# 민석 수정
import streamlit as st
import uuid
import time
from datetime import datetime
import pandas as pd
from data_handler import load_gsheet_data, save_gsheet_data
from utils import get_star_rating
import data_handler as dh

def add_review(rest_id, comment, rating, user, parent_id="root"):
    current_rev_df = load_gsheet_data("reviews")
    new_rev = {
        "id": str(uuid.uuid4())[:8],
        "rest_id": rest_id,
        "parent_id": parent_id,
        "rating": float(rating),
        "comment": comment,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user": user
    }
    updated_rev_df = pd.concat([current_rev_df, pd.DataFrame([new_rev])], ignore_index=True)
    save_gsheet_data(updated_rev_df, "reviews")
    st.success("등록되었습니다!")
    time.sleep(0.5)
    st.rerun()

def render_comments(rest_id, rev_df, parent_id="root", depth=0):
    mask = (rev_df['rest_id'] == rest_id) & (rev_df['parent_id'].fillna("root") == parent_id)
    sub_comments = rev_df[mask]
    
    for _, r in sub_comments.iterrows():
        margin_left = depth * 25
        st.markdown(f"""
        <div style="margin-left: {margin_left}px; border-left: 3px solid #ddd; padding-left: 15px; margin-bottom: 10px; background-color: #f9f9f9; padding: 12px; border-radius: 8px;">
            <small><b>@{r['user']}</b> · {r['timestamp']}</small><br>
            <span style="color: #f39c12;">{get_star_rating(r['rating'])}</span><br>
            <div style="margin-top:5px;">{r['comment']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(f"↳ 답글 쓰기", expanded=False):
            with st.form(key=f"reply_form_{r['id']}"):
                re_user = st.text_input("이름", value="익명", key=f"user_{r['id']}")
                re_comment = st.text_area("내용", key=f"comm_{r['id']}")
                if st.form_submit_button("답글 등록"):
                    if re_comment:
                        add_review(rest_id, re_comment, 0, re_user, parent_id=r['id'])
                    else:
                        st.warning("내용을 입력해 주세요.")
        render_comments(rest_id, rev_df, r['id'], depth + 1)

# SQL 버전 함수들
def add_review_sql(restaurant_id, comment, rating, user_id, parent_id=None):
    """SQL 버전의 리뷰 추가 함수"""
    # dh.add_review가 parent_id를 지원하는지 확인 필요
    # 일단 parent_id가 None이면 일반 리뷰, 아니면 답글로 처리
    # data_handler의 add_review 함수 시그니처에 맞게 호출
    # parent_id가 있으면 별도 처리 필요 (data_handler에 함수 추가 필요할 수 있음)
    if parent_id is None:
        dh.add_review(restaurant_id, user_id, rating, comment)
    else:
        # 답글인 경우 - data_handler에 add_reply 같은 함수가 필요할 수 있음
        # 일단 동일한 함수 호출 (parent_id 지원 여부 확인 필요)
        try:
            dh.add_review(restaurant_id, user_id, rating, comment, parent_id=parent_id)
        except TypeError:
            # parent_id를 지원하지 않으면 기본 호출
            dh.add_review(restaurant_id, user_id, rating, comment)
    st.success("등록되었습니다!")
    time.sleep(0.5)
    st.rerun()

def render_comments_sql(restaurant_id, rev_df, parent_id=None, depth=0):
    """SQL 버전의 댓글 렌더링 함수"""
    # parent_id가 None이면 최상위 댓글, 아니면 답글
    if parent_id is None:
        mask = (rev_df['restaurant_id'] == restaurant_id) & (rev_df['parent_id'].isna())
    else:
        mask = (rev_df['restaurant_id'] == restaurant_id) & (rev_df['parent_id'] == parent_id)
    
    sub_comments = rev_df[mask]
    
    for _, r in sub_comments.iterrows():
        margin_left = depth * 25
        
        # 사용자 이름 가져오기 (user_id가 있으면 사용자 이름 조회, 없으면 user_name 컬럼 사용)
        user_name = r.get('user_name', r.get('user', '익명'))
        if 'user_id' in r and pd.notna(r['user_id']):
            # user_id로 사용자 이름 조회 (필요시)
            # 일단 user_name 컬럼이 있으면 사용, 없으면 user_id 표시
            if 'user_name' not in r or pd.isna(r.get('user_name')):
                user_name = f"사용자 {r['user_id']}"
        
        # 날짜 포맷팅
        if 'created_at' in r:
            timestamp = pd.to_datetime(r['created_at']).strftime("%Y-%m-%d %H:%M") if pd.notna(r['created_at']) else ""
        else:
            timestamp = r.get('timestamp', '')
        
        st.markdown(f"""
        <div style="margin-left: {margin_left}px; border-left: 3px solid #ddd; padding-left: 15px; margin-bottom: 10px; background-color: #f9f9f9; padding: 12px; border-radius: 8px;">
            <small><b>@{user_name}</b> · {timestamp}</small><br>
            <span style="color: #f39c12;">{get_star_rating(r['rating'])}</span><br>
            <div style="margin-top:5px;">{r['comment']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(f"↳ 답글 쓰기", expanded=False):
            with st.form(key=f"reply_form_sql_{r['id']}"):
                re_comment = st.text_area("내용", key=f"comm_sql_{r['id']}")
                if st.form_submit_button("답글 등록"):
                    if re_comment:
                        # 로그인된 사용자의 ID 사용
                        user_id = st.session_state.get("user_id")
                        if user_id:
                            add_review_sql(restaurant_id, re_comment, 0, user_id, parent_id=r['id'])
                        else:
                            st.warning("로그인이 필요합니다.")
                    else:
                        st.warning("내용을 입력해 주세요.")
        # 재귀적으로 답글 렌더링
        render_comments_sql(restaurant_id, rev_df, r['id'], depth + 1)
