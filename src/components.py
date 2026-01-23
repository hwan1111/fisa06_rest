# 민석 수정
import streamlit as st
import uuid
import time
from datetime import datetime
import pandas as pd
# Make sure to handle imports carefully to avoid circular dependencies
import data_handler as dh
from utils import get_star_rating
import folium
from folium.plugins import MarkerCluster, Fullscreen

# =============================================================================
# GSheet Components
# =============================================================================

def add_review_gsheet(rest_id, comment, rating, user, parent_id="root"):
    """Adds a review to the Google Sheet."""
    current_rev_df = dh.load_gsheet_data("reviews")
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
    dh.save_gsheet_data(updated_rev_df, "reviews")
    st.success("등록되었습니다!")
    time.sleep(0.5)
    st.rerun()

def render_comments_gsheet(rest_id, rev_df, parent_id="root", depth=0):
    """Renders comments from a GSheet DataFrame."""
    # This function is specific to the gsheet data structure
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
            with st.form(key=f"reply_form_gsheet_{r['id']}"):
                # In gsheet version, user name is entered manually
                re_user = st.text_input("이름", value="익명", key=f"user_gsheet_{r['id']}")
                re_comment = st.text_area("내용", key=f"comm_gsheet_{r['id']}")
                if st.form_submit_button("답글 등록"):
                    if re_comment:
                        # Call the gsheet-specific add_review function
                        add_review_gsheet(rest_id, re_comment, 0, re_user, parent_id=r['id'])
                    else:
                        st.warning("내용을 입력해 주세요.")
        render_comments_gsheet(rest_id, rev_df, r['id'], depth + 1)


# =============================================================================
# SQL Components
# =============================================================================

def render_comments_sql(restaurant_id, reviews_df):
    """
    Renders menu reviews from a SQL DataFrame. 
    Displays menu item name, price, rating, and comment.
    """
    if reviews_df.empty:
        st.info("아직 작성된 메뉴 리뷰가 없습니다.")
        return

    for _, r in reviews_df.iterrows():
        st.markdown(f"""
        <div style="border-left: 3px solid #ddd; padding-left: 15px; margin-bottom: 10px; background-color: #f9f9f9; padding: 12px; border-radius: 8px;">
            <p>
                <strong>{r['item_name']}</strong> - 
                <span style="color: #555;">{r['price']:,}원</span>
            </p>
            <small><b>@{r['user_name']}</b> · {r['timestamp'].strftime('%Y-%m-%d %H:%M')}</small><br>
            <span style="color: #f39c12;">{get_star_rating(r['rating'])}</span> ({r['rating']})<br>
            <div style="margin-top:5px;">{r['comment']}</div>
        </div>
        """, unsafe_allow_html=True)

# Renaming original functions to be specific
add_review = add_review_gsheet
render_comments = render_comments_gsheet

def render_pro_map(disp_df):
    """
    Generates a professional-looking Folium map with advanced features.
    
    Args:
        disp_df (pd.DataFrame): DataFrame containing restaurant and review data,
                                already filtered for the current view.

    Returns:
        folium.Map: The generated Folium map object.
    """
    
    # 1. 지도 초기화
    # 'CartoDB Positron' 타일을 사용하여 깔끔한 배경을 만듭니다.
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=12, tiles='CartoDB Positron')

    # 2. 카테고리별 스타일 정의
    # FontAwesome 아이콘과 색상을 지정합니다.
    category_styles = {
        '한식': ('#d9534f', 'leaf'),        # 빨간색, 잎
        '중식': ('#f0ad4e', 'fire'),         # 주황색, 불
        '일식': ('#337ab7', 'cutlery'),    # 파란색, 식기
        '양식': ('#5cb85c', 'glass'),        # 초록색, 유리잔
        '카페/디저트': ('#5bc0de', 'coffee'),  # 하늘색, 커피
        '기타': ('#777777', 'info-sign')     # 회색, 정보
    }

    # 3. 마커 클러스터링 및 전체화면 버튼 추가
    marker_cluster = MarkerCluster().add_to(m)
    Fullscreen().add_to(m)

    # 4. 지도에 맛집 마커 추가
    # 중복을 제거한 맛집 목록을 만듭니다.
    unique_restaurants = disp_df.dropna(subset=['restaurant_id']).drop_duplicates(subset=['restaurant_id'])
    
    if unique_restaurants.empty:
        return m

    locations = []
    for _, rest in unique_restaurants.iterrows():
        # 마커 위치 및 정보
        lat, lon = rest['lat'], rest['lon']
        locations.append([lat, lon])
        
        # 카테고리 스타일 가져오기 (없으면 '기타' 스타일 사용)
        cat = rest.get('category', '기타')
        color, icon_name = category_styles.get(cat, category_styles['기타'])

        # 해당 맛집의 모든 리뷰를 가져와 평균 별점 계산
        all_reviews = disp_df[disp_df['restaurant_id'] == rest['restaurant_id']]
        avg_rating = all_reviews['rating'].mean()
        
        # 5. 커스텀 HTML 팝업 디자인
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 220px;">
            <h4 style="margin:5px 0; font-weight:bold; color:#333;">{rest['restaurant_name']}</h4>
            <p style="margin:5px 0; color:#555;">
                <span style="color:#f39c12; font-size:1.2em;">{get_star_rating(avg_rating)}</span>
                <span style="font-size:0.9em; margin-left:5px;">{avg_rating:.2f} / 5.0</span>
            </p>
            <p style="margin:5px 0; font-size:0.9em; color:#666;">
                <i class="fa fa-{icon_name}" style="color:{color};"></i> &nbsp; {cat}
            </p>
            <a href="{rest['url']}" target="_blank" style="
                display: block;
                text-align: center;
                padding: 8px;
                margin-top: 10px;
                background-color: {color};
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 0.9em;
            ">지도에서 보기</a>
        </div>
        """
        
        # 팝업 및 마커 생성
        popup = folium.Popup(popup_html, max_width=250)
        icon = folium.Icon(color=color, icon=icon_name, prefix='glyphicon')
        
        folium.Marker(
            location=[lat, lon],
            popup=popup,
            icon=icon,
            tooltip=rest['restaurant_name']
        ).add_to(marker_cluster)

    # 6. 자동 줌 및 중앙 설정 (fit_bounds)
    if locations:
        m.fit_bounds(locations, padding=(50, 50))
        
    return m