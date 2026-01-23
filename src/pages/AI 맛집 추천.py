import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import sys
import os

# recommend.py 불러오기
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import recommend
import data_handler as dh  # 기존에 있던 함수(식당 목록 등)는 그대로 사용

st.set_page_config(page_title="AI 맛집 추천", page_icon="🤖", layout="wide")

# --- 스타일링 ---
st.markdown("""
<style>
    .stContainer {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .big-font { font-size: 20px !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("손쉽게 메뉴 결정! AI 맛집 추천 서비스 🍽️")
st.markdown("데이터와 AI가 만나 당신의 **오늘 뭐 먹지?** 고민을 해결해 드립니다.")
st.markdown("---")

# 🟢 [핵심] DB 연결 객체 생성 (data_handler 수정 없이 여기서 바로 연결!)
# secrets.toml의 [connections.mysql] 설정을 자동으로 사용합니다.
conn = st.connection("mysql", type="sql")

tab1, tab2 = st.tabs(["💰 예산별 맞춤 추천", "📊 리뷰 정밀 분석"])

# =========================================================
# 탭 1: 예산 추천 (여기서 직접 쿼리 실행!)
# =========================================================
with tab1:
    col_input, col_result = st.columns([1, 2])
    
    with col_input:
        with st.container(border=True):
            st.subheader("🔍 검색 조건")
            budget = st.number_input("예산 (원)", min_value=1000, value=10000, step=1000)
            user_lat, user_lon = 37.5665, 126.9780 
            search_btn = st.button("AI 추천 받기 🚀", type="primary", use_container_width=True)

    with col_result:
        if search_btn:
            try:
                # 🟢 [수정됨] data_handler 함수 대신, 여기서 직접 SQL 실행
                # SQL: 가격이 예산보다 싼 메뉴와 식당 정보를 조인(Join)해서 가져옴
                query = f"""
                    SELECT r.name as r_name, r.category, m.item_name, m.price
                    FROM menu_items m
                    JOIN restaurants r ON m.restaurant_id = r.id
                    WHERE m.price <= {budget}
                    ORDER BY m.price DESC
                """
                
                # Streamlit의 쿼리 기능 사용 (결과를 바로 DataFrame으로 줌)
                df = conn.query(query, ttl=0)
                
                if not df.empty:
                    # DataFrame을 딕셔너리 리스트로 변환 (AI 함수에 넣기 위해)
                    candidates = df.to_dict('records')

                    # 1. AI 추천 및 날씨 정보
                    with st.spinner("🌥️ 날씨를 확인하고 메뉴를 고르는 중..."):
                        weather = recommend.get_weather(user_lat, user_lon)
                        if weather:
                            rec_text = recommend.get_ai_recommendation(weather, candidates)
                            
                            st.info(f"📍 현재 날씨: **{weather['main']}** ({weather['temp']}°C)")
                            st.markdown(f"""
                            <div style="background-color:#e8f4f8; padding:15px; border-radius:10px; border-left: 5px solid #00a8cc;">
                                <h4>🤖 AI's Pick</h4>
                                <p style="font-size:16px;">{rec_text}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # 2. 시각화: 가격대 분포
                    st.subheader("📊 메뉴 가격 분포")
                    fig = px.histogram(df, x="price", nbins=10, 
                                     color="category", 
                                     title=f"{budget}원 이하 메뉴들의 가격 분포",
                                     labels={"price": "가격", "count": "메뉴 개수"})
                    st.plotly_chart(fig, use_container_width=True)

                    # 3. 데이터 테이블
                    st.subheader(f"📋 검색 결과 ({len(df)}개)")
                    st.dataframe(
                        df, 
                        column_config={
                            "r_name": "식당 이름",
                            "item_name": "메뉴명",
                            "price": st.column_config.NumberColumn("가격", format="%d원"),
                            "category": "종류"
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("💸 해당 예산으로 먹을 수 있는 메뉴가 없습니다.")
            except Exception as e:
                st.error(f"데이터 조회 오류: {e}")

# =========================================================
# 탭 2: 리뷰 분석 (워드클라우드 개선 버전)
# =========================================================
with tab2:
    st.subheader("🧐 리뷰 심층 분석")
    
    db_rest_list = [] 

    # 1. 데이터 가져오기 (리스트 변환 안전장치 포함)
    try:
        raw_data = dh.get_all_restaurants()
        if hasattr(raw_data, 'to_dict'): 
            db_rest_list = raw_data.to_dict('records')
        elif isinstance(raw_data, list):
            db_rest_list = raw_data
    except Exception:
        pass 

    if not db_rest_list:
        try:
            df_rest = conn.query("SELECT * FROM restaurants", ttl=0)
            if not df_rest.empty:
                db_rest_list = df_rest.to_dict('records')
        except Exception as e:
            st.error(f"식당 목록 로딩 실패: {e}")
            db_rest_list = []

    if db_rest_list:
        rest_names = [r['name'] for r in db_rest_list]
        selected_rest_name = st.selectbox("분석할 식당을 선택하세요", rest_names)
        
        selected_rest_id = next(item['id'] for item in db_rest_list if item['name'] == selected_rest_name)

        if st.button("리뷰 분석 시작 ✨"):
            try:
                reviews = []
                try:
                    raw_reviews = dh.get_reviews_by_restaurant(selected_rest_id)
                    if hasattr(raw_reviews, 'to_dict'):
                        reviews = raw_reviews.to_dict('records')
                    elif isinstance(raw_reviews, list):
                        reviews = raw_reviews
                except:
                    q = f"SELECT content FROM reviews WHERE restaurant_id = '{selected_rest_id}'"
                    reviews_df = conn.query(q, ttl=0)
                    if not reviews_df.empty:
                        reviews = reviews_df.to_dict('records')

                reviews_text = " ".join([r['content'] for r in reviews]) if reviews else ""
                
                if reviews_text:
                    # AI 분석 (스피너 안에서는 계산만)
                    result = None
                    with st.spinner("AI가 리뷰를 읽고 있습니다..."):
                        result = recommend.get_review_analysis(selected_rest_name, reviews_text)
                    
                    # 화면 그리기 (스피너 밖)
                    if result:
                        col_chart, col_summary = st.columns([1, 1])
                        
                        with col_chart:
                            # 오각형 차트
                            categories = ['맛', '가성비', '서비스', '위생', '분위기']
                            fig = go.Figure()
                            fig.add_trace(go.Scatterpolar(
                                r=result['scores'], 
                                theta=categories, 
                                fill='toself', 
                                name=selected_rest_name,
                                line_color='#FF6B6B' # 라인 색상 변경 (예쁨 추가)
                            ))
                            fig.update_layout(
                                polar=dict(radialaxis=dict(visible=True, range=[0, 10])), 
                                showlegend=False,
                                title=dict(text="5대 지표 분석", x=0.5)
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        with col_summary:
                            # 한줄평
                            st.markdown(f"""
                            <div style="background-color:#fff3cd; padding:20px; border-radius:10px; margin-top: 50px;">
                                <h3>📝 AI 한줄 요약</h3>
                                <p class="big-font">"{result['summary']}"</p>
                            </div>
                            """, unsafe_allow_html=True)

                        st.divider()
                        
                        # -----------------------------------------------------
                        # [수정됨] 워드 클라우드 & Top 3 키워드
                        # -----------------------------------------------------
                        st.subheader("☁️ 리뷰 키워드 분석")
                        try:
                            font_path = 'C:/Windows/Fonts/malgun.ttf'
                            if not os.path.exists(font_path): font_path = None

                            # 1. 워드클라우드 생성 (설정 강화)
                            wc = WordCloud(
                                font_path=font_path,
                                background_color='white',
                                colormap='Dark2',    # 글자색을 진하고 선명하게
                                width=600, height=300, # 이미지 해상도 조정
                                max_font_size=100,     # 가장 큰 글자 크기 제한
                                relative_scaling=0.5,  # 빈도수에 따른 크기 차이
                                prefer_horizontal=0.9  # 대부분 가로로 표시 (읽기 쉽게)
                            ).generate(reviews_text)
                            
                            # 2. 🔥 Top 3 키워드 추출
                            # wc.words_ 는 {단어: 빈도수} 딕셔너리입니다.
                            top_keywords = sorted(wc.words_.items(), key=lambda x: x[1], reverse=True)[:3]
                            top_keywords_str = " ".join([f"#{k[0]}" for k in top_keywords])
                            
                            # 3. 키워드 표시 (차트 위에 예쁘게)
                            st.markdown(f"### 🔥 핵심 키워드: <span style='color:#e03131;'>{top_keywords_str}</span>", unsafe_allow_html=True)
                            
                            # 4. 작아진 그래프 그리기
                            # figsize를 (6, 3)으로 줄임
                            fig_wc, ax = plt.subplots(figsize=(6, 3)) 
                            ax.imshow(wc, interpolation='bilinear')
                            ax.axis('off')
                            # 그래프 여백 제거 (더 깔끔하게)
                            plt.tight_layout(pad=0)
                            st.pyplot(fig_wc)
                            
                        except Exception as e:
                            st.warning(f"워드 클라우드 오류: {e}")
                else:
                    st.info("이 식당에 등록된 리뷰가 없습니다.")
            except Exception as e:
                st.error(f"리뷰 조회 중 오류 발생: {e}")
    else:
        st.warning("등록된 식당이 없습니다.")