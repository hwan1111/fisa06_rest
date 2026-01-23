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
        return "구름 조금/많음 ⛅"
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

def get_ai_recommendation(weather_info, candidates):
    """
    [기능 1] 날씨 정보와 메뉴 후보 리스트를 받아 AI 추천 멘트 생성
    """
    # 토큰 절약을 위해 상위 10개 메뉴만 문자열로 변환
    # candidates 리스트 안에는 {'r_name':..., 'item_name':..., 'price':...} 딕셔너리가 들어있음
    menu_str = "\n".join([
        f"- {c['r_name']}의 {c['item_name']}: {c['price']}원 ({c['category']})" 
        for c in candidates[:10]
    ])
    
    prompt = f"""
    현재 날씨: {weather_info['main']}, 기온: {weather_info['temp']}도.
    
    내 예산으로 먹을 수 있는 후보 메뉴들:
    {menu_str}
    
    이 날씨와 분위기에 가장 잘 어울리는 메뉴 하나를 '강력 추천'해주고,
    왜 추천했는지 감성적인 이유를 3줄 이내로 작성해줘.
    말투는 친절하고 센스있는 맛집 큐레이터처럼 해줘.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "너는 센스있는 맛집 큐레이터야."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 추천 중 오류 발생: {e}"

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