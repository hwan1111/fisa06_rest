import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
from wordcloud import WordCloud
from geopy.geocoders import Nominatim
import sys
import os

# recommend.py 불러오기
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import recommend
import data_handler as dh  # (프로젝트 호환 위해 유지)

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

# ✅ DB 연결
conn = st.connection("mysql", type="sql")

# =========================================================
# 캐시 함수들 (과도한 API/DB 호출 방지)
# =========================================================
@st.cache_data(show_spinner=False, ttl=60 * 30)
def geocode_address(address: str):
    """주소 -> (lat, lon). 실패하면 None."""
    try:
        geolocator = Nominatim(user_agent="foodie_map_app", timeout=5)
        loc = geolocator.geocode(address)
        if loc:
            return float(loc.latitude), float(loc.longitude)
    except Exception:
        pass
    return None

@st.cache_data(show_spinner=False, ttl=60 * 10)
def get_weather_cached(lat: float, lon: float):
    """날씨 API 호출 캐시"""
    return recommend.get_weather(lat, lon)

@st.cache_data(show_spinner=False, ttl=60)
def fetch_menu_df(budget: int):
    """예산 이하 메뉴 조회 (파라미터 바인딩)"""
    sql = """
        SELECT
            r.name AS r_name,
            r.category,
            m.item_name,
            m.price,
            r.address
        FROM menu_items m
        JOIN restaurants r ON m.restaurant_id = r.id
        WHERE m.price IS NOT NULL
          AND m.price <= :budget
        ORDER BY m.price DESC
    """
    df = conn.query(sql, params={"budget": int(budget)}, ttl=60)

    # price 타입 방어
    if not df.empty and "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df = df.dropna(subset=["price"])
        df["price"] = df["price"].astype(int)
    return df

@st.cache_data(show_spinner=False, ttl=60)
def fetch_restaurants():
    return conn.query("SELECT * FROM restaurants", ttl=60)

@st.cache_data(show_spinner=False, ttl=60)
def fetch_reviews_by_restaurant(rest_id: int):
    sql = """
        SELECT r.comment AS content, r.rating
        FROM menu_reviews r
        JOIN menu_items m ON r.menu_item_id = m.id
        WHERE m.restaurant_id = :rest_id
    """
    return conn.query(sql, params={"rest_id": int(rest_id)}, ttl=60)

# =========================================================
# 세션 상태 초기화
# =========================================================
if "tab1" not in st.session_state:
    st.session_state.tab1 = {
        "searched": False,
        "address": None,
        "budget": None,
        "lat": None,
        "lon": None,
        "weather": None,
        "weather_summary": "",
        "location_name": "검색 전",
        "df": pd.DataFrame(),
        "rec_text": None,
    }

if "tab2" not in st.session_state:
    st.session_state.tab2 = {
        "analyzed": False,
        "rest_name": None,
        "result": None,
        "reviews_text": None,
    }

tab1, tab2 = st.tabs(["💰 예산별 맞춤 추천", "📊 리뷰 정밀 분석"])

# =========================================================
# 탭 1: 예산별 추천 (✅ TOP 5 고정)
# =========================================================
with tab1:
    st.markdown("### 💸 내 지갑 사정에 딱 맞는 맛집")
    st.caption("원하는 동네를 입력하면, 그곳의 날씨와 예산을 고려해 AI가 추천합니다.")

    col_input, col_weather = st.columns([1, 1], gap="large")

    # 1) 왼쪽: 검색 옵션
    with col_input:
        with st.container(border=True):
            st.subheader("🔍 검색 옵션")

            address_input = st.text_input(
                "어디서 드시나요?(상세 주소 입력)",
                value=st.session_state.tab1["address"] or "상암동",
                placeholder="예: 서울 시청, 부산 해운대"
            )

            budget = st.number_input(
                "오늘 내 지갑 사정 💸(숫자로 입력하세요)",
                min_value=1000,
                value=int(st.session_state.tab1["budget"] or 10000),
                step=1000,
                format="%d"
            )
            budget = int(budget)

            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

            # 버튼 스타일링
            st.markdown("""
            <style>
                div.stButton > button:first-child {
                    background-color: #00B4D8;
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 10px;
                    border: none;
                    box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
                    transition: 0.3s;
                }
                div.stButton > button:first-child:hover {
                    background-color: #0077B6;
                    color: white;
                    transform: scale(1.02);
                }
            </style>
            """, unsafe_allow_html=True)

            search_btn = st.button("AI 맛집 추천 시작 🚀", use_container_width=True, key="search_btn")

    # 2) 버튼 클릭 시 로직 실행 + session_state 저장
    if search_btn:
        # 기본 좌표(상암동 근처)
        user_lat, user_lon = 37.5786, 126.8972
        location_name = address_input

        geo = geocode_address(address_input)
        if geo:
            user_lat, user_lon = geo
        else:
            st.toast("📍 위치를 못 찾아서 기본 위치로 검색합니다.", icon="⚠️")

        weather = None
        weather_summary = ""

        with st.spinner("🌞오늘 날씨 확인 중..."):
            weather = get_weather_cached(user_lat, user_lon)

        if weather:
            main_w = weather.get("main", "")
            temp = weather.get("temp", 0)

            if "Rain" in main_w:
                weather_summary = "☔ 비가 오네요, 감성 있는 식사가 필요해요."
            elif "Snow" in main_w:
                weather_summary = "☃️ 눈이 와요! 따뜻한 곳이 좋겠어요."
            elif "Clear" in main_w:
                weather_summary = "☀️ 맑은 날씨! 밖이 보이는 식당은 어때요?"
            elif "Cloud" in main_w:
                weather_summary = "☁️ 흐린 날엔 기분 전환할 맛집이 딱이죠."
            elif temp < 5:
                weather_summary = "❄️ 날이 춥습니다. 뜨끈한 국물이 당기네요."
            elif temp > 28:
                weather_summary = "🔥 무더위엔 시원한 메뉴가 최고죠!"
            else:
                weather_summary = "🙂 활동하기 좋은 날씨네요!"
        else:
            weather_summary = "🌥️ 날씨 정보를 가져오지 못했어요. 예산 기반으로 추천할게요."

        # DB 조회
        with st.spinner("📦 예산에 맞는 메뉴를 불러오는 중..."):
            df = fetch_menu_df(budget)

        # ✅ TOP 5 후보만 AI에 전달 (예산 이하에서 가격 높은 순)
        rec_text = None
        if not df.empty:
            top5_df = df.sort_values("price", ascending=False).head(5)
            candidates = top5_df.to_dict("records")

            with st.spinner("🤖 AI가 메뉴를 고르는 중..."):
                try:
                    if weather:
                        rec_text = recommend.get_ai_recommendation(weather, candidates, budget)
                    else:
                        # fallback: TOP 5를 텍스트로 구성
                        lines = [f"- {c['r_name']} | {c['item_name']} ({int(c['price']):,}원)" for c in candidates]
                        rec_text = "예산 안에서 가격이 높은 메뉴 TOP 5를 골랐어요!\n" + "\n".join(lines)
                except Exception:
                    lines = [f"- {c['r_name']} | {c['item_name']} ({int(c['price']):,}원)" for c in candidates]
                    rec_text = "예산 안에서 가격이 높은 메뉴 TOP 5를 골랐어요!\n" + "\n".join(lines)

        # ✅ 상태 저장
        st.session_state.tab1.update({
            "searched": True,
            "address": address_input,
            "budget": budget,
            "lat": user_lat,
            "lon": user_lon,
            "weather": weather,
            "weather_summary": weather_summary,
            "location_name": location_name,
            "df": df,
            "rec_text": rec_text,
        })

    # 3) 오른쪽: 날씨 정보
    with col_weather:
        with st.container(border=True):
            st.subheader("🌤️ 현재 날씨 정보")

            if st.session_state.tab1["searched"]:
                weather = st.session_state.tab1["weather"]
                location_name = st.session_state.tab1["location_name"]
                weather_summary = st.session_state.tab1["weather_summary"]

                if weather:
                    st.info(f"💡 {weather_summary}")
                    st.markdown("---")
                    m_col1, m_col2, m_col3 = st.columns(3)
                    with m_col1:
                        st.metric("상태", weather.get("main", "-"))
                    with m_col2:
                        st.metric("기온", f"{weather.get('temp','-')}°C")
                    with m_col3:
                        st.metric("위치", location_name)
                    st.caption(f"📍 기준: {location_name} 주변 실시간 데이터")
                else:
                    st.info(weather_summary)
                    st.caption("날씨 정보 없이 예산 기반 추천을 진행했습니다.")
            else:
                st.markdown("<div style='height: 130px;'></div>", unsafe_allow_html=True)
                st.info("👈 왼쪽에서 시작 버튼을 눌러보세요.")
                st.caption("검색 결과가 여기에 표시됩니다.")

    # 4) 하단 결과 (✅ TOP 5만 추천/차트/표)
    if st.session_state.tab1["searched"]:
        st.divider()

        df = st.session_state.tab1["df"]
        budget = st.session_state.tab1["budget"]

        if df.empty:
            st.error("😭 해당 예산으로는 먹을 수 있는 메뉴가 없어요...")
        else:
            # AI 추천 박스
            if st.session_state.tab1["rec_text"]:
                st.markdown(f"""
                <div style="background-color:#e8f4f8; padding:15px; border-radius:10px; border-left: 5px solid #00a8cc; margin-bottom: 20px;">
                    <h4 style="color:#007ea7;">🤖 AI's Pick</h4>
                    <p style="font-size:16px; white-space: pre-wrap;">{st.session_state.tab1["rec_text"]}</p>
                </div>
                """, unsafe_allow_html=True)

            # (선택) 카테고리 필터는 유지하되, 추천은 항상 필터 기준 TOP 5
            with st.container(border=True):
                st.subheader("🎛️ 결과 필터 (선택)")
                all_categories = sorted(df["category"].dropna().unique().tolist())
                sel_categories = st.multiselect("종류(카테고리) 필터", all_categories, default=all_categories)

            df_f = df[df["category"].isin(sel_categories)] if sel_categories else df

            # ✅ TOP 5
            df_top5 = df_f.sort_values("price", ascending=False).head(5)

            st.subheader("🏆 예산 꽉 채운 추천 TOP 5")
            st.dataframe(
                df_top5,
                column_config={
                    "r_name": "식당 이름",
                    "item_name": "메뉴명",
                    "price": st.column_config.NumberColumn("가격", format="%d원"),
                    "category": "종류",
                    "address": "위치"
                },
                use_container_width=True,
                hide_index=True
            )

            # 가격 비교 차트 (TOP 5만)
            st.subheader("📊 추천 TOP 5 가격 비교")
            df_chart = df_top5.sort_values("price", ascending=True)

            fig = px.bar(
                df_chart,
                x="price",
                y="item_name",
                color="category",
                orientation="h",
                title=f"💰 예산({budget:,}원) 꽉 채운 추천 메뉴 TOP {len(df_top5)}",
                labels={"price": "가격 (원)", "item_name": "메뉴명"},
                text="price",
                hover_data=["r_name", "category", "address"]
            )
            fig.update_traces(texttemplate="%{text:,}원", textposition="outside")
            fig.update_layout(
                showlegend=True,
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(range=[0, budget * 1.15]),
                height=420
            )
            fig.add_vline(x=budget, line_dash="dash", line_color="red",
                          annotation_text="내 예산", annotation_position="bottom right")
            st.plotly_chart(fig, use_container_width=True)

            # 전체 결과는 접어두기
            with st.expander(f"📋 전체 검색 결과 보기 ({len(df_f)}개)"):
                st.dataframe(
                    df_f,
                    column_config={
                        "r_name": "식당 이름",
                        "item_name": "메뉴명",
                        "price": st.column_config.NumberColumn("가격", format="%d원"),
                        "category": "종류",
                        "address": "위치"
                    },
                    use_container_width=True,
                    hide_index=True
                )

# =========================================================
# 탭 2: 리뷰 분석
# =========================================================
with tab2:
    st.subheader("🧐 리뷰 심층 분석")

    # 1) 식당 목록
    try:
        df_rest = fetch_restaurants()
        db_rest_list = df_rest.to_dict("records") if not df_rest.empty else []
    except Exception as e:
        st.error(f"식당 목록 로딩 실패: {e}")
        db_rest_list = []

    if not db_rest_list:
        st.warning("등록된 식당이 없습니다.")
    else:
        rest_names = [r["name"] for r in db_rest_list]
        selected_rest_name = st.selectbox("분석할 식당을 선택하세요", rest_names, key="rest_select")

        selected_rest_id = next(item["id"] for item in db_rest_list if item["name"] == selected_rest_name)

        review_btn = st.button("리뷰 분석 시작 ✨", key="review_btn")

        if review_btn:
            try:
                reviews_df = fetch_reviews_by_restaurant(selected_rest_id)

                if reviews_df.empty:
                    st.session_state.tab2.update({"analyzed": True, "rest_name": selected_rest_name, "result": None, "reviews_text": ""})
                else:
                    reviews = reviews_df.to_dict("records")
                    reviews_text = " ".join([str(r["content"]) for r in reviews if r.get("content")])

                    st.session_state.tab2.update({"analyzed": True, "rest_name": selected_rest_name, "reviews_text": reviews_text})

                    if reviews_text.strip():
                        with st.spinner("💭 AI가 손님들의 마음을 읽고 있어요..."):
                            result = recommend.get_review_analysis(selected_rest_name, reviews_text)
                        st.session_state.tab2["result"] = result
                    else:
                        st.session_state.tab2["result"] = None

            except Exception as e:
                st.error(f"리뷰 분석 중 오류 발생: {e}")

        # ✅ 분석 결과 표시
        if st.session_state.tab2["analyzed"] and st.session_state.tab2["rest_name"] == selected_rest_name:
            reviews_text = st.session_state.tab2.get("reviews_text", "")
            result = st.session_state.tab2.get("result")

            if not reviews_text.strip():
                st.info("리뷰 텍스트가 비어있습니다.")
            elif result is None:
                st.info("이 식당에 등록된 리뷰가 없습니다(또는 분석 결과가 없습니다).")
            else:
                col_chart, col_summary = st.columns([1.2, 0.8])

                with col_chart:
                    categories = ['맛', '가성비', '서비스', '위생', '분위기']

                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=result["scores"],
                        theta=categories,
                        fill="toself",
                        name=selected_rest_name,
                        fillcolor="rgba(255, 127, 80, 0.35)",
                        line=dict(color="#FF7F50", width=2),
                        marker=dict(size=6, color="#FF4500")
                    ))

                    fig.update_layout(
                        polar=dict(
                            bgcolor="rgba(255,255,255,0.9)",
                            radialaxis=dict(
                                visible=True,
                                range=[0, 5],
                                tickvals=[1, 2, 3, 4, 5],
                                ticktext=["1", "2", "3", "4", "5"],
                                linecolor="lightgray",
                                gridcolor="whitesmoke",
                                showline=False
                            ),
                            angularaxis=dict(
                                showline=False,
                                showticklabels=True,
                                tickfont=dict(size=14, family="Malgun Gothic", color="#333")
                            )
                        ),
                        showlegend=False,
                        margin=dict(l=40, r=40, t=80, b=40),
                        title=dict(
                            text="✨ 맛집 5대 매력 지수",
                            x=0.5, y=0.95,
                            xanchor="center", yanchor="top",
                            font=dict(size=25, color="#333", family="Malgun Gothic")
                        )
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col_summary:
                    st.markdown(f"""
                    <div style="background-color:#fff0f6; padding:20px; border-radius:15px; margin-top: 30px; border: 1px solid #ffdeeb;">
                        <h3 style="color:#d63384; margin-bottom:10px;">📝 AI 한줄평</h3>
                        <p style="font-size:16px; line-height:1.6; color:#555;">"{result['summary']}"</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.divider()
                st.subheader("☁️ 손님들이 자주 쓰는 표현")

                # 한글 폰트 경로 후보 (Windows / macOS / Linux)
                font_candidates = [
                    "C:/Windows/Fonts/malgun.ttf",
                    "/System/Library/Fonts/AppleGothic.ttf",
                    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
                ]
                font_path = next((p for p in font_candidates if os.path.exists(p)), None)

                try:
                    x, y = np.ogrid[:300, :300]
                    mask = (x - 150) ** 2 + (y - 150) ** 2 > 130 ** 2
                    mask = 255 * mask.astype(int)

                    wc = WordCloud(
                        font_path=font_path,
                        background_color="white",
                        mask=mask,
                        colormap="plasma",
                        width=300,
                        height=300,
                        max_font_size=80,
                        repeat=True,
                        prefer_horizontal=0.8
                    ).generate(reviews_text)

                    top_keywords = sorted(wc.words_.items(), key=lambda x: x[1], reverse=True)[:3]
                    top_keywords_str = " ".join([f"#{k[0]}" for k in top_keywords])

                    st.markdown(f"""
                        <div style='text-align: left; margin-bottom: 20px; margin-top: 10px;'>
                            <span style='font-size: 22px; font-weight: bold; color: #555; margin-right: 8px;'>🔥 핵심 키워드:</span>
                            <span style='font-size: 30px; font-weight: bold; color: #e03131;'>{top_keywords_str}</span>
                        </div>
                    """, unsafe_allow_html=True)

                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c2:
                        fig_wc, ax = plt.subplots(figsize=(5, 5))
                        ax.imshow(wc, interpolation="bilinear")
                        ax.axis("off")
                        plt.tight_layout(pad=0)
                        st.pyplot(fig_wc)

                except Exception as e:
                    st.warning(f"워드 클라우드 오류: {e}")
