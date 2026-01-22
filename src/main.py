import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import pandas as pd
import uuid

# 모듈 불러오기
from data_handler import load_gsheet_data, save_gsheet_data
from utils import get_coords, get_star_rating
from components import add_review, render_comments

st.set_page_config(page_title="우리 반 맛집 실록", layout="wide")
st.title("🍴 우리 반 맛집 미슐랭 가이드")

rest_df = load_gsheet_data("restaurants")
rev_df = load_gsheet_data("reviews")

CATEGORIES = ["전체", "한식", "중식", "일식", "양식", "카페/디저트", "기타"]

# 사이드바 등록 폼
with st.sidebar:
    st.header("🏠 맛집 등록 및 리뷰")
    with st.form("main_registration", clear_on_submit=True):
        u_name = st.text_input("가게 이름")
        u_address = st.text_input("상세 주소")
        u_category = st.selectbox("카테고리", CATEGORIES[1:])
        u_rating = st.slider("별점", 1, 5, 3)
        u_comment = st.text_area("방문 후기")
        u_url = st.text_input("네이버 지도 링크")
        u_user = st.text_input("작성자 성함", value="익명")
        
        submitted = st.form_submit_button("등록 완료")
        
        if submitted:
            if u_name and u_address:
                # 중복 체크를 위해 최신 데이터 다시 로드
                current_rest_df = load_gsheet_data("restaurants")
                existing = current_rest_df[(current_rest_df['name'] == u_name) | (current_rest_df['address'] == u_address)]
                
                if not existing.empty:
                    st.info("📍 이미 등록된 장소입니다. 리뷰만 추가됩니다.")
                    rest_id = existing.iloc[0]['id']
                else:
                    with st.spinner("위치를 찾는 중입니다..."):
                        lat, lon = get_coords(u_address)
                    
                    if lat:
                        rest_id = str(uuid.uuid4())[:8]
                        new_rest = {
                            "id": rest_id, "name": u_name, "category": u_category, 
                            "address": u_address, "url": u_url, "lat": lat, "lon": lon
                        }
                        updated_rest_df = pd.concat([current_rest_df, pd.DataFrame([new_rest])], ignore_index=True)
                        save_gsheet_data(updated_rest_df, "restaurants")
                    else:
                        st.error("❌ 주소를 찾을 수 없습니다. 주소를 다시 확인해 주세요.")
                        rest_id = None
                
                if rest_id:
                    add_review(rest_id, u_comment, u_rating, u_user)
            else:
                st.warning("이름과 주소는 필수입니다.")

# 메인 탭
tab_map, tab_trend = st.tabs(["📍 지도 및 목록", "📊 별점 트렌드"])

with tab_map:
    st.subheader("📁 카테고리 필터")
    selected_cat = st.radio("분류", CATEGORIES, horizontal=True)
    disp_rest = rest_df if selected_cat == "전체" else rest_df[rest_df['category'] == selected_cat]
    
    if not disp_rest.empty:
        # 지도 생성
        m = folium.Map(location=[disp_rest['lat'].mean(), disp_rest['lon'].mean()], zoom_start=15)
        for _, row in disp_rest.iterrows():
            folium.Marker([row['lat'], row['lon']], tooltip=row['name']).add_to(m)
        st_folium(m, width="100%", height=450)

        st.markdown("---")
        
        # 그리드 카드 뷰
        cols = st.columns(3)
        for i, (_, row) in enumerate(disp_rest.iterrows()):
            with cols[i % 3]:
                with st.container(border=True):
                    this_revs = rev_df[rev_df['rest_id'] == row['id']]
                    avg_rating = this_revs['rating'].mean() if not this_revs.empty else 0
                    
                    st.markdown(f"### {row['name']}")
                    st.write(f"**{row['category']}** | {get_star_rating(avg_rating)} ({avg_rating:.1f})")
                    st.caption(f"📍 {row['address']}")
                    
                    with st.expander("💬 리뷰 및 대댓글 보기"):
                        render_comments(row['id'], rev_df)
                    
                    if row['url']:
                        st.link_button("네이버 지도", row['url'], use_container_width=True)
    else:
        st.info("데이터가 없습니다.")

with tab_trend:
    st.subheader("📈 맛집별 별점 추이")
    if not rev_df.empty and not rest_df.empty:
        try:
            merged = pd.merge(rev_df, rest_df[['id', 'name']], left_on='rest_id', right_on='id')
            merged['date'] = pd.to_datetime(merged['timestamp']).dt.date
            daily_avg = merged.groupby(['date', 'name'])['rating'].mean().reset_index()
            
            selected_res = st.multiselect("추이를 비교할 맛집 선택", daily_avg['name'].unique())
            if selected_res:
                filtered = daily_avg[daily_avg['name'].isin(selected_res)]
                fig = px.line(filtered, x='date', y='rating', color='name', markers=True)
                fig.update_yaxes(range=[0, 5.5])
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"데이터 분석 중 오류: {e}")
