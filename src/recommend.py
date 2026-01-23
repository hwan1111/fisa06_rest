import streamlit as st
import requests
import json
from openai import OpenAI

# 1. secrets.toml에서 OpenAI 키만 가져오기 (날씨 키 필요 없음!)
try:
    OPENAI_API_KEY = st.secrets["openai"]["api_key"]
except Exception:
    st.error("🚨 .streamlit/secrets.toml 파일에 [openai] api_key가 설정되지 않았습니다.")
    st.stop()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------------------------------------
# 🌤️ Open-Meteo 날씨 관련 함수들
# ---------------------------------------------------------

def get_wmo_description(code):
    """
    Open-Meteo의 날씨 코드(숫자)를 한국어 설명과 이모지로 변환
    참고: WMO Weather interpretation codes (WW)
    """
    if code == 0: 
        return "맑음 ☀️"
    elif 1 <= code <= 3: 
        return "구름  ⛅"
    elif 45 <= code <= 48: 
        return "안개 🌫️"
    elif 51 <= code <= 67: 
        return "비 🌧️" # 이슬비 포함
    elif 71 <= code <= 77: 
        return "눈 ☃️"
    elif 80 <= code <= 82: 
        return "소나기 ☔"
    elif 95 <= code <= 99: 
        return "천둥번개 ⛈️"
    else: 
        return "흐림 ☁️"

def get_weather(lat, lon):
    """
    Open-Meteo API를 사용하여 날씨 정보 가져오기 (API Key 불필요)
    """
    # 무료 API 엔드포인트
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            current = data['current_weather']
            
            # 숫자 코드를 사람이 읽기 쉬운 글자로 변환
            weather_desc = get_wmo_description(current['weathercode'])
            temperature = current['temperature']
            
            return {
                "main": weather_desc,  # 예: "비 🌧️"
                "temp": temperature    # 예: 24.5
            }
    except Exception as e:
        print(f"Open-Meteo API 에러: {e}")
        return None
    
    return None

# ---------------------------------------------------------
# 🤖 OpenAI 기능 관련 함수들
# ---------------------------------------------------------

def get_ai_recommendation(weather_info, candidates, user_budget):
    """
    [기능 1] 날씨와 예산 근접도를 고려한 AI 추천 멘트 생성
    """
    # 1. 메뉴 데이터 정리 (예산 근접도를 위해 가격 정보 강조)
    menu_str = ""
    for idx, c in enumerate(candidates[:10]):
        menu_str += f"{idx+1}. [{c['category']}] {c['r_name']} - {c['item_name']} ({c['price']}원)\n"
    
    # 2. 시스템 프롬프트 (예산 근접도 + 날씨 연관성 강화)
    system_instruction = f"""
    당신은 사용자의 지갑 사정과 날씨를 완벽하게 분석하는 '특급 맛집 컨설턴트'입니다.
    사용자가 제시한 예산은 **[{user_budget}원]**입니다. 

    [추천 핵심 원칙]
    1. **예산 근접도 (Best Value)**: 
       - 후보 메뉴 중 사용자의 예산({user_budget}원)에 **가장 근접한 가격**의 메뉴를 우선적으로 고려하세요. 
       - 너무 싼 메뉴보다는, 예산 범위 내에서 가장 풍족하게 즐길 수 있는 메뉴를 추천하여 만족도를 높이세요.
    2. **날씨 연관성 (Weather Logic)**: 
       - 현재 날씨({weather_info['main']}, {weather_info['temp']}도)와 음식의 온도, 식감, 분위기를 논리적으로 연결하세요.
    3. **식당 정체성 (Brand Story)**:
       - 식당 이름에서 느껴지는 이미지를 활용하여 추천 이유를 더 풍성하게 만드세요.
       - 메뉴의 카테고리와 특징을 반영하여 추천 멘트에 개성을 부여하세요.
       - 식당 이름이 메뉴와 어울리지 않는다면, 메뉴의 특성에 집중하세요.
       - 식당 이름이 베이커리, 카페, 디저트, 베이글, 빵 관련일 경우, 국물이 있는 음식이나 해장 음식과 어울리는 멘트는 피하세요.
       - 식당 이름이 베이커리, 카페, 디저트, 베이글, 빵 관련일 경우, 따뜻한 음료나 디저트와 어울리는 멘트를 작성하세요.

    [카테고리별 금지 규칙]
    - [카페/디저트/베이커리]는 추워도 "국물/해장/밥도둑" 금지. "따뜻한 온기/달콤한 위로" 등으로 표현.

    [작성 가이드]
    - "오늘 {user_budget}원이라는 예산에 딱 맞춰서, 날씨까지 고려한 최고의 선택은 바로 이곳입니다!"라는 뉘앙스로 시작하세요.
    - 말투는 다정하고 전문적인 큐레이터처럼 (이모지 활용).
    - 3~4줄로 작성.
    """

    user_prompt = f"""
    내 예산 {user_budget}원에 가장 잘 맞으면서, 오늘 날씨에 먹으면 행복해질 메뉴를 하나만 골라줘:
    
    [후보 메뉴 리스트]
    {menu_str}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"추천 멘트 생성 중 오류가 발생했어요: {e}"

def get_review_analysis(rest_name, reviews_text):
    """
    [기능 2] 리뷰 텍스트를 분석하여 5각형 그래프용 점수와 요약 반환
    """
    # 너무 긴 리뷰는 잘라서 보냄 (비용 절약)
    safe_reviews = reviews_text[:3000]
    
    prompt = f"""
    식당 이름: {rest_name}
    리뷰 데이터: "{safe_reviews}"
    
    위 리뷰를 분석해서 5가지 항목(맛, 가성비, 서비스, 위생, 분위기)에 대해 1~10점 점수를 매기고,
    전체적인 내용을 요약한 한줄평을 작성해줘.
    
    반드시 아래 JSON 형식으로만 응답해 (다른 말 금지):
    {{
        "scores": [맛, 가성비, 서비스, 위생, 분위기],
        "summary": "한줄평 내용"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5, # 분석 일관성을 위해 낮게 설정
            response_format={"type": "json_object"} # JSON 모드 활성화 (안정성 UP)
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # 에러 발생 시 그래프가 깨지지 않도록 기본값 반환
        print(f"리뷰 분석 에러: {e}")
        return {"scores": [5,5,5,5,5], "summary": "분석에 실패했습니다. (AI 응답 오류)"}