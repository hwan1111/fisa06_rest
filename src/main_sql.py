# 민석 수정
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import pandas as pd
import uuid

# 모듈 불러오기
import data_handler as dh
from utils import get_coords, get_star_rating
# SQL용 컴포넌트와 로그인 페이지를 가져옴
from components import render_comments_sql
from login import show_login_page

st.set_page_config(page_title="우리 반 맛집 실록 (SQL)", layout="wide")
st.title("🍴 우리 반 맛집 미슐랭 가이드 (MySQL)")

# --- 0. 로그인 처리 ---
# 로그인이 되어있지 않으면 로그인 페이지를 보여주고, 앱의 나머지 부분은 실행하지 않음
if not show_login_page():
    st.stop()

# --- 1. 데이터 초기 로드 (MySQL에서) ---
# 로그인 성공 후에만 데이터를 로드
rest_df = dh.get_all_restaurants()
rev_df = dh.get_all_reviews()

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

    with st.form("main_registration", clear_on_submit=True):
        u_name = st.text_input("가게 이름")
        u_address = st.text_input("상세 주소")
        u_category = st.selectbox("카테고리", CATEGORIES[1:])
        u_rating = st.slider("별점", 1, 5, 3)
        u_comment = st.text_area("방문 후기")
        u_url = st.text_input("네이버 지도 링크")
        
        submitted = st.form_submit_button("등록 완료")
        
        if submitted:
            if u_name and u_address:
                # 중복 체크
                existing = rest_df[(rest_df['name'] == u_name) | (rest_df['address'] == u_address)]
                
                if not existing.empty:
                    st.info("📍 이미 등록된 장소입니다. 리뷰만 추가됩니다.")
                    rest_id = existing.iloc[0]['id']
                else:
                    with st.spinner("위치를 찾는 중입니다..."):
                        lat, lon = get_coords(u_address)
                    
                    if lat:
                        rest_id = dh.add_restaurant(u_name, u_category, u_address, u_url, lat, lon)
                        st.success(f"'{u_name}' 정보가 신규 등록되었습니다!")
                    else:
                        st.error("❌ 주소를 찾을 수 없습니다. 다시 확인해 주세요.")
                        rest_id = None
                
                if rest_id:
                    # 로그인된 사용자의 ID를 사용
                    user_id = st.session_state["user_id"]
                    dh.add_review(rest_id, user_id, u_rating, u_comment)
                    st.success("리뷰가 등록되었습니다!")
                    st.rerun()
            else:
                st.warning("이름과 주소는 필수입니다.")

# --- 3. 메인 화면: 탭 구성 ---
tab_map, tab_trend = st.tabs(["📍 지도 및 목록", "📊 별점 트렌드"])

with tab_map:
    st.subheader("📁 카테고리 필터")
    selected_cat = st.radio("분류", CATEGORIES, horizontal=True)
    
    disp_rest = rest_df if selected_cat == "전체" else rest_df[rest_df['category'] == selected_cat]
    
    if not disp_rest.empty:
        disp_rest['lat'] = pd.to_numeric(disp_rest['lat'])
        disp_rest['lon'] = pd.to_numeric(disp_rest['lon'])
        
        m = folium.Map(location=[disp_rest['lat'].mean(), disp_rest['lon'].mean()], zoom_start=15)
        for _, row in disp_rest.iterrows():
            folium.Marker(
                [row['lat'], row['lon']], 
                tooltip=row['name'],
                icon=folium.Icon(color='red') ####################
            ).add_to(m)
        st_folium(m, width="100%", height=450)

        st.markdown("---")
        
        cols = st.columns(3)
        for i, (_, row) in enumerate(disp_rest.iterrows()):
            with cols[i % 3]:
                with st.container(border=True):
                    this_revs = rev_df[rev_df['restaurant_id'] == row['id']]
                    avg_rating = pd.to_numeric(this_revs['rating']).mean() if not this_revs.empty else 0
                    
                    st.markdown(f"### {row['name']}")
                    st.write(f"**{row['category']}** | {get_star_rating(avg_rating)} ({avg_rating:.1f})")
                    st.caption(f"📍 {row['address']}")
                    
                    with st.expander("💬 리뷰 및 대댓글 보기"):
                        full_reviews = dh.get_reviews_by_restaurant(row['id'])
                        # SQL용 댓글 렌더링 함수 호출
                        render_comments_sql(row['id'], full_reviews)
                    
                    if row['url']:
                        st.link_button("네이버 지도", row['url'], use_container_width=True)
    else:
        st.info("데이터가 없습니다.")

with tab_trend:
    st.subheader("📈 맛집별 별점 추이")
    if not rev_df.empty and not rest_df.empty:
        try:
            merged = pd.merge(rev_df, rest_df[['id', 'name']], left_on='restaurant_id', right_on='id')
            merged['date'] = pd.to_datetime(merged['created_at']).dt.date
            merged['rating'] = pd.to_numeric(merged['rating'])
            
            daily_avg = merged.groupby(['date', 'name'])['rating'].mean().reset_index()
            
            selected_res = st.multiselect("추이를 비교할 맛집 선택", daily_avg['name'].unique())
            if selected_res:
                filtered = daily_avg[daily_avg['name'].isin(selected_res)]
                fig = px.line(filtered, x='date', y='rating', color='name', markers=True)
                fig.update_yaxes(range=[0, 5.5])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("비교할 맛집을 선택해 주세요.")
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
    else:
        st.info("분석할 리뷰 데이터가 없습니다.")
