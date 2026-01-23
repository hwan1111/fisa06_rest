import streamlit as st
import recommend  # 같은 폴더에 있는 recommend.py 불러오기

st.title("🧪 기능 점검 (Test Run)")

# 1. 시크릿 키 확인
st.subheader("1. secrets.toml 인식 확인")
try:
    api_key = st.secrets["openai"]["api_key"]
    st.success(f"✅ OpenAI 키 인식 성공! (앞자리: {api_key[:5]}...)")
except Exception as e:
    st.error("❌ secrets.toml 파일을 못 찾거나 [openai] 설정이 틀렸습니다.")
    st.code(str(e))

# 2. 날씨 API 확인 (Open-Meteo)
st.subheader("2. 날씨 API 테스트 (무료/키 불필요)")
if st.button("서울 날씨 가져오기"):
    # 서울 시청 좌표
    weather = recommend.get_weather(37.5665, 126.9780)
    if weather:
        st.success(f"성공! 상태: {weather['main']}, 기온: {weather['temp']}도")
    else:
        st.error("날씨 API 호출 실패")

# 3. AI 추천 기능 확인
st.subheader("3. AI 메뉴 추천 (가짜 데이터 사용)")
if st.button("AI에게 추천받기"):
    # 테스트용 가짜 데이터 (DB 연결 X)
    dummy_candidates = [
        {'r_name': '테스트식당', 'item_name': '뜨끈한 국밥', 'price': 9000, 'category': '한식'},
        {'r_name': '테스트카페', 'item_name': '아이스 아메리카노', 'price': 4000, 'category': '카페'},
    ]
    dummy_weather = {'main': '비 🌧️', 'temp': 15.0}

    with st.spinner("AI가 생각 중입니다..."):
        try:
            result = recommend.get_ai_recommendation(dummy_weather, dummy_candidates)
            st.info(result)
        except Exception as e:
            st.error(f"AI 호출 에러: {e}")

# 4. 리뷰 분석 확인
st.subheader("4. 리뷰 분석 테스트")
if st.button("리뷰 분석하기"):
    dummy_review = "음식은 정말 맛있는데 가격이 조금 비싸요. 매장은 청결합니다."
    with st.spinner("분석 중..."):
        try:
            result = recommend.get_review_analysis("테스트식당", dummy_review)
            st.json(result)
        except Exception as e:
            st.error(f"분석 에러: {e}")