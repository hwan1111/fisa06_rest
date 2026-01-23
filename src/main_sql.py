import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import pandas as pd

# 모듈 불러오기
import data_handler as dh
from utils import get_star_rating
# SQL용 컴포넌트와 로그인 페이지를 가져옴
from login import show_login_page

st.set_page_config(page_title="우리 반 맛집 실록 (SQL)", layout="wide")
st.title("🍴 우리 반 맛집 미슐랭 가이드 (MySQL)")

# --- 0. 로그인 처리 ---
if not show_login_page():
    st.stop()

# --- 1. 데이터 초기 로드 (단일 조인 함수 사용) ---
all_data_df = dh.get_all_data_joined()

CATEGORIES = ["전체", "한식", "중식", "일식", "양식", "카페/디저트", "기타"]

# --- 2. 사이드바: 맛집 등록 및 리뷰 ---
with st.sidebar:
    st.header(f"👋 {st.session_state['user_name']}님, 환영합니다!")
    # 로그아웃 버튼
    from login import logout_user
    if st.button("🚪 로그아웃", use_container_width=True):
        logout_user()
    st.markdown("---")
    st.subheader("🏠 맛집 등록 및 리뷰")

    with st.form("menu_review_registration", clear_on_submit=True):
        u_rest_name = st.text_input("가게 이름")
        u_menu_name = st.text_input("메뉴 이름")
        u_menu_price = st.number_input("가격", min_value=0, step=1000)
        u_rating = st.slider("별점", 1, 5, 3)
        u_comment = st.text_area("리뷰")
        u_category = st.selectbox("카테고리", CATEGORIES[1:])
        u_address = st.text_input("가게 주소")
        u_url = st.text_input("지도 링크 (Google/Naver)")
        
        submitted = st.form_submit_button("등록 완료")
        
        if submitted:
            if u_rest_name and u_address and u_menu_name:
                dh.save_full_visit_data(
                    user_name=st.session_state["user_name"],
                    user_email=st.session_state["email"],
                    rest_name=u_rest_name,
                    rest_address=u_address,
                    rest_category=u_category,
                    rest_url=u_url,
                    menu_name=u_menu_name,
                    menu_price=u_menu_price,
                    review_rating=u_rating,
                    review_comment=u_comment
                )
            else:
                st.warning("가게 이름, 주소, 메뉴 이름은 필수 항목입니다.")

# --- 3. 메인 화면: 탭 구성 ---
tab_map, tab_trend = st.tabs(["📍 지도 및 목록", "📊 별점 트렌드"])

with tab_map:
    st.subheader("📁 카테고리 필터")
    selected_cat = st.radio("분류", CATEGORIES, horizontal=True)
    
    # Filter data based on category
    if selected_cat == "전체":
        disp_df = all_data_df.copy()
    else:
        disp_df = all_data_df[all_data_df['category'] == selected_cat]

    # Group by restaurant to render one card per restaurant
    # Dropping rows where restaurant_id is NaN (for restaurants with no reviews yet)
    unique_restaurants = disp_df.dropna(subset=['restaurant_id']).drop_duplicates(subset=['restaurant_id'])
    
    if not unique_restaurants.empty:
        # Map rendering
        m = folium.Map(location=[unique_restaurants['lat'].mean(), unique_restaurants['lon'].mean()], zoom_start=15)
        for _, row in unique_restaurants.iterrows():
            folium.Marker([row['lat'], row['lon']], tooltip=row['restaurant_name']).add_to(m)
        st_folium(m, width="100%", height=450)

        st.markdown("---")
        
        # Restaurant cards rendering
        cols = st.columns(3)
        for i, (_, rest_row) in enumerate(unique_restaurants.iterrows()):
            with cols[i % 3]:
                with st.container(border=True):
                    # Get all reviews for this restaurant
                    rest_reviews = disp_df[disp_df['restaurant_id'] == rest_row['restaurant_id']].dropna(subset=['timestamp'])
                    
                    # Calculate overall restaurant rating
                    overall_rating = rest_reviews['rating'].mean()
                    
                    st.markdown(f"### {rest_row['restaurant_name']}")
                    st.write(f"**{rest_row['category']}** | {get_star_rating(overall_rating)} ({overall_rating:.2f})")
                    st.caption(f"📍 {rest_row['address']}")
                    
                    with st.expander("💬 메뉴별 리뷰 보기"):
                        if not rest_reviews.empty:
                            # Sort reviews by timestamp
                            sorted_reviews = rest_reviews.sort_values(by='timestamp', ascending=False)
                            for _, review_row in sorted_reviews.iterrows():
                                st.markdown(f"""
                                <div style="border-left: 3px solid #ddd; padding-left: 15px; margin-bottom: 10px; background-color: #f9f9f9; padding: 12px; border-radius: 8px;">
                                    <p>
                                        <strong>{review_row['item_name']}</strong> - 
                                        <span style="color: #555;">{review_row['price']:,}원</span>
                                    </p>
                                    <small><b>@{review_row['user_name']}</b> · {pd.to_datetime(review_row['timestamp']).strftime('%Y-%m-%d %H:%M')}</small><br>
                                    <span style="color: #f39c12;">{get_star_rating(review_row['rating'])}</span> ({review_row['rating']})<br>
                                    <div style="margin-top:5px;">{review_row['comment']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("아직 리뷰가 없습니다.")
                    
                    if pd.notna(rest_row['url']):
                        st.link_button("지도 링크", rest_row['url'], use_container_width=True)
    else:
        st.info("선택된 카테고리에 해당하는 맛집이 없습니다.")

with tab_trend:
    st.subheader("📈 맛집별 별점 추이")
    if not all_data_df.dropna(subset=['timestamp']).empty:
        try:
            # Prepare data for trend analysis
            trend_df = all_data_df.dropna(subset=['timestamp', 'rating']).copy()
            trend_df['date'] = pd.to_datetime(trend_df['timestamp']).dt.date
            trend_df['rating'] = pd.to_numeric(trend_df['rating'])
            
            daily_avg = trend_df.groupby(['date', 'restaurant_name'])['rating'].mean().reset_index()
            
            selected_res = st.multiselect("추이를 비교할 맛집 선택", daily_avg['restaurant_name'].unique())
            if selected_res:
                filtered = daily_avg[daily_avg['restaurant_name'].isin(selected_res)]
                fig = px.line(filtered, x='date', y='rating', color='restaurant_name', markers=True, labels={"restaurant_name": "맛집"})
                fig.update_yaxes(range=[0, 5.5])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("비교할 맛집을 선택해 주세요.")
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
    else:
        st.info("분석할 리뷰 데이터가 없습니다.")
