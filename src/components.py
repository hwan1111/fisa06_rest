import streamlit as st
import uuid
import time
from datetime import datetime
import pandas as pd
from data_handler import load_gsheet_data, save_gsheet_data
from utils import get_star_rating

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