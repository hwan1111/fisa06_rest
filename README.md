# 🍴 WooriFISA Foodie Map - 우리 반 맛집 실록

<div align="center">
  <img src="./image/title.png" alt="프로젝트 타이틀" width="80%">
</div>

> **부트캠프 동료들과 함께하는 맛집 공유 및 분석 플랫폼**

본 프로젝트는 부트캠프 동료들 간의 맛집 정보와 리뷰를 공유할 수 있는 서비스입니다. 기존의 단편적인 시스템을 넘어 **MySQL 기반의 관계형 데이터베이스(RDBMS)**를 활용해 데이터 무결성을 확보하고, **메뉴 중심의 리뷰** 및 **AI 기반 분석**을 제공하는 Streamlit 웹 애플리케이션입니다.

---

## 📋 목차
- [프로젝트 개요](#-프로젝트-개요)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [시스템 아키텍처](#-시스템-아키텍처)
- [프로젝트 구조](#-프로젝트-구조)
- [데이터베이스 설계](#-데이터베이스-설계)
- [주요 모듈 설명](#-주요-모듈-설명)
- [로그인 기능](#-로그인-기능)
- [팀원 소개](#-팀원-소개)
- [트러블슈팅](#-트러블슈팅)

---

## 🎯 프로젝트 개요

### 1. 프로젝트 목표
- **경험 공유**: 부트캠프 동료들이 직접 가본 맛집의 위치와 메뉴별 상세 리뷰 아카이빙
- **데이터 활용**: 입력받은 데이터를 DB에 적재하고, 목적에 적합한 방식으로 시각화 및 인사이트 제공
- **기술 실습**: 부트캠프에서 학습한 데이터 처리, 분석, 시각화 기술의 실전 적용

### 2. 주요 변경 및 고도화 사항
- ✅ **저장소 전환**: Google Sheets → MySQL (데이터 관리 고도화)
- ✅ **리뷰 고도화**: 식당 중심 → **메뉴 아이템 중심**의 상세 평가
- ✅ **지능형 서비스**: OpenAI API를 활용한 리뷰 분석 및 메뉴 추천 시스템
- ✅ **사용자 시스템**: 회원가입 및 세션 기반 로그인 기능 도입

---

## ✨ 주요 기능

<div align="center">
  <img src="./image/user_flow.png" alt="주요 기능" width="70%">
</div>

1. **로그인 및 회원가입**: 사용자 인증을 통한 개인화 서비스 제공
2. **메뉴 중심 맛집 등록**: 식당 정보와 함께 특정 메뉴에 대한 별점, 후기, URL 등록 (Geopy 자동 주소 변환)
3. **통합 식당 카드 UI**: 동일 식당의 리뷰를 그룹화하여 실시간 평균 별점 및 최신순 리뷰 표시
4. **팀원 모집**: 함께 맛집을 방문할 동료를 구하는 커뮤니티 기능
5. **데이터 시각화 및 분석**:
    - **지도**: Folium 기반 위치 마커 표시
    - **통계**: Plotly를 활용한 카테고리별 평점 추이 및 통계 차트
    - **AI 분석**: OpenAI 기반의 리뷰 요약(맛/가성비/서비스 등 5개 항목) 및 날씨 맞춤형 메뉴 추천

---

## 🛠 기술 스택

<div align="center">
  <img src="./image/stack.png" alt="기술 스택" width="70%">
</div>

- **Frontend/UI**: ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
- **Language/Library**: ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
- **Database**: ![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
- **Visualization**: ![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat-square&logo=plotly&logoColor=white) ![Folium](https://img.shields.io/badge/Folium-77B829?style=flat-square&logo=folium&logoColor=white)
- **External API**: OpenAI (AI 분석), Open-Meteo (날씨), Geopy (좌표 변환)

---

## 🏗 시스템 아키텍처

<div align="center">
  <img src="./image/cicd1.png" alt="시스템 아키텍처" width="70%">
</div>

- **Presentation Layer**: Streamlit 기반 사용자 인터페이스 및 결과 시각화
- **Application Logic**: `data_handler.py`, `recommend.py`를 통한 비즈니스 로직 및 API 연동
- **Data Layer**: MySQL을 통한 정규화된 데이터 모델링 및 저장
- **GIS Layer**: Geopy와 Folium을 결합한 지리 정보 처리

---

## 📁 프로젝트 구조

프로젝트는 **로그인 기능**을 중심으로 구성되어 있으며, 모듈화된 구조로 관리됩니다.

```
WooriFISA-foodie-map/
├── Login.py                      # 로그인 메인 페이지
├── AI 맛집 추천.py               # AI 기반 맛집 추천 메인 앱
├── components.py                 # UI 컴포넌트 모음
├── data_handler.py               # 데이터 처리 및 DB CRUD 로직
├── recommend.py                  # AI/날씨 추천 로직 모듈
├── utils.py                      # 유틸리티 함수 (주소→좌표 변환 등)
├── login/
│   ├── auth.py                   # 로그인 인증 처리
│   ├── login_config.py           # 로그인 관련 설정
│   └── login_data_handle.py      # 로그인 데이터 처리
├── pages/
│   └── 미슐랭 서비스.py           # 미슐랭 서비스 페이지
├── image/                        # 이미지 리소스
├── requirements.txt              # 프로젝트 의존성 패키지
└── README.md                     # 프로젝트 문서
```

### 각 파일의 역할

#### 메인 애플리케이션
- **`Login.py`**: 사용자 아이디와 이메일을 입력받아 로그인 처리
- **`AI 맛집 추천.py`**: 예산별 맞춤 추천 및 리뷰 심층 분석 화면 제공

#### 로그인 모듈 (`login/`)
- **`auth.py`**: 사용자 인증 및 세션 관리
- **`login_config.py`**: DB 연결 설정 및 로그인 관련 설정
- **`login_data_handle.py`**: 사용자 정보 조회/삽입 기능

#### 핵심 모듈
- **`recommend.py`**: 날씨 정보 조회, AI 추천, 리뷰 분석 함수 제공
- **`data_handler.py`**: DB CRUD 헬퍼 및 비즈니스 로직
- **`components.py`**: Streamlit UI 컴포넌트
- **`utils.py`**: 공통 유틸리티 함수

---

## 💾 데이터베이스 설계 (ERD)

데이터의 일관성을 위해 6개의 테이블이 외래키(FK)로 연결되어 있습니다.

<div align="center">
  <img src="./image/ERD.png" alt="ERD" width="60%">
</div>

| 테이블명 | 설명 | 핵심 컬럼 |
|---------|------|----------|
| **USERS** | 사용자 정보 | user_id, username, password, email |
| **RESTAURANTS** | 맛집 정보 | restaurant_id, name, address, category |
| **MENU_ITEMS** | 메뉴 정보 | menu_id, restaurant_id, menu_name, price |
| **MENU_REVIEWS** | 리뷰 데이터 | review_id, menu_id, user_id, rating, comment |
| **PARTIES** | 모집 게시판 | party_id, restaurant_id, host_id |

---

## 🐍 주요 모듈 설명

### 1. `AI 맛집 추천.py` (Streamlit 메인 앱)

**역할**: 서비스 화면(탭 UI) 렌더링 및 "예산별 추천/리뷰 분석" 전체 플로우를 담당합니다.

#### 주요 화면

**탭1: 예산별 맞춤 추천**
- 주소 입력 → (Geopy) 위경도 변환 → (Open-Meteo) 날씨 조회
- 예산 이하 메뉴를 DB에서 조회 후 **TOP 5**만 추려서 AI 추천 문구 생성
- TOP 5 가격 비교 차트(Plotly) + 상세 테이블 표시

**탭2: 리뷰 심층 분석**
- 식당 선택 → 해당 식당의 메뉴/리뷰를 **JOIN 쿼리**로 가져와 텍스트 결합
- OpenAI로 5개 항목(맛/가성비/서비스/위생/분위기) 점수 + 한줄평 생성
- 레이더 차트 + 워드클라우드로 시각화

#### DB 연동 포인트
- `st.connection("mysql", type="sql")` 기반으로 SQL을 실행
- 리뷰 분석 관계: `menu_reviews.menu_item_id` → `menu_items.id` → `restaurants.id`

#### 성능 최적화
- `@st.cache_data`로 주소 지오코딩/날씨 조회/DB 조회를 캐싱
- `st.session_state`로 탭별 분석 결과를 유지하여 리렌더링 시 UX 향상

---

### 2. `recommend.py` (AI/날씨 로직 모듈)

**역할**: 외부 API를 호출하여 "날씨 정보"와 "AI 결과"를 생성하는 모듈입니다.

#### 주요 함수

```python
def get_weather(lat, lon)
# Open-Meteo를 호출해 현재 날씨/기온을 가져옵니다.

def get_ai_recommendation(weather_info, candidates, user_budget)
# 후보 메뉴 리스트 + 예산 + 날씨를 입력으로
# 예산 근접도와 날씨 연관성을 반영한 추천 멘트를 생성합니다.

def get_review_analysis(rest_name, reviews_text)
# 리뷰 텍스트를 기반으로 5개 항목 점수와 한줄평을 JSON 형태로 반환합니다.
```

---

### 3. `login/auth.py` (로그인 인증 모듈)

**역할**: 사용자 로그인 처리 및 세션 관리를 담당합니다.

#### 로그인 함수

```python
def login_user(user_id, email):
    """
    사용자 로그인 함수
    - 입력된 아이디와 이메일을 비교하여 로그인 처리
    """
    query = "SELECT name FROM users WHERE id = %s AND email = %s;"
    params = (user_id, email)
    result = fetch_query(query, params)

    if result:
        stored_name = result[0][0]
        # 세션 상태 저장
        st.session_state.user_id = user_id
        st.session_state.email = email
        st.session_state.logged_in = True
        st.session_state.user_name = stored_name
        st.success(f"로그인 성공! 환영합니다, {stored_name}님.")
    else:
        st.error("존재하지 않는 사용자이거나 이메일이 잘못되었습니다.")
```

#### 로그인 처리 과정

1. 사용자가 아이디와 이메일을 입력하고 로그인 버튼 클릭
2. `login_user` 함수가 DB에서 아이디와 이메일을 조회
3. 사용자가 존재하면 로그인 상태를 `st.session_state`에 저장
4. 환영 메시지 출력 또는 에러 메시지 표시

---

## 🔐 로그인 기능

### 세션 상태 관리

Streamlit의 `st.session_state`를 활용하여 로그인 상태를 유지하고, 다른 페이지나 컴포넌트에서 사용자 정보를 활용할 수 있습니다.

#### 로그인 후 세션 저장

```python
# 로그인 후 세션 상태에 정보 저장
st.session_state.user_id = user_id
st.session_state.email = email
st.session_state.logged_in = True
st.session_state.user_name = user_name
```

#### 다른 페이지에서 로그인 정보 사용

```python
# 다른 페이지에서 세션 상태 확인
if 'logged_in' in st.session_state and st.session_state.logged_in:
    user_id = st.session_state['user_id']
    st.write(f"현재 로그인한 사용자: {user_id}")
else:
    st.write("로그인되지 않았습니다.")
```

### 세션 상태 활용

`st.session_state`는 세션 동안 전역 상태를 관리하는 객체로, 로그인 정보, 사용자 아이디, 이메일 등을 저장하고 다른 페이지나 컴포넌트에서 계속 사용할 수 있게 해줍니다.

---

## 👥 팀원 소개

| 이름 | 역할 | 주요 기여 |
|------|------|----------|
| **김동환** | 팀장 / Full-stack | 아이디어 기획 및 Streamlit 앱 메인 프레임 개발 |
| **김유정** | Backend / Data | MySQL 연동, 데이터 분석 및 가격 시각화 로직 구현 |
| **권민석** | Frontend / DevOps | 로그인 시스템 개발, Folium 지도 렌더링 최적화(깜빡임 해결) |
| **이주형** | Database / Data | 데이터베이스 모델링(ERD) 및 기초 데이터 정제 |

---

## 🔧 트러블슈팅

### 1. Folium 지도 깜빡임 현상
**증상**: Streamlit 리렌더링 시 지도가 계속 초기화됨  
**해결**: `st.session_state`에 지도 객체를 캐싱하여 상태를 유지함

### 2. 주소 변환(Geocoding) 오류
**원인**: 잘못된 주소 입력으로 인한 위경도 추출 실패  
**해결**: Geopy 예외 처리 로직 추가 및 주소 검증 단계 도입

### 3. 로그인 후 페이지 이동 및 사용자 정보 전달 문제

#### 문제 상황
Dart와 같은 프론트엔드 언어를 사용할 때는 로그인 페이지에서 다른 페이지로 바로 이동하거나, URL 파라미터나 폼 데이터를 사용하여 사용자 정보를 넘겨주는 방식으로 페이지 간 데이터를 주고받을 수 있었습니다.

그러나 Streamlit을 사용하면서 다음과 같은 문제를 겪었습니다:

**페이지 간 이동 방식의 차이**
- Streamlit에서는 다른 페이지로 이동하는 방식이 아니라 `st.session_state`에 사용자 정보를 저장하여 다른 페이지에서 이를 활용하는 방식으로 동작합니다.
- URL 파라미터나 폼 데이터를 사용하는 대신, 세션 상태를 통해 서버 측에서 상태를 유지하는 방식이기 때문에 적응이 필요했습니다.

#### 해결 방법

**세션 상태 (st.session_state) 사용**
- Streamlit에서는 페이지 간에 사용자 정보를 넘기는 방식 대신, 세션 상태에 사용자 정보를 저장하고 다른 페이지에서 이 정보를 참조하는 방식으로 작업을 진행했습니다.

```python
# 로그인 후 세션 상태에 정보 저장
st.session_state.user_id = user_id
st.session_state.logged_in = True
```

**다른 페이지에서 세션 값 사용**
- 다른 페이지에서는 `st.session_state`를 통해 로그인된 사용자의 아이디나 이메일을 쉽게 가져올 수 있습니다.

```python
# 다른 페이지에서 세션 상태에서 사용자 정보 가져오기
if 'logged_in' in st.session_state and st.session_state.logged_in:
    user_id = st.session_state['user_id']
    st.write(f"현재 로그인한 사용자: {user_id}")
```

### 4. 리뷰가 0개로 나오는 경우 체크리스트

리뷰 데이터가 제대로 표시되지 않을 때 다음을 확인하세요:

- `menu_reviews.menu_item_id` 값이 실제 `menu_items.id`와 일치하는지
- `menu_items.restaurant_id` 값이 선택한 `restaurants.id`와 일치하는지

아래 쿼리로 식당별 리뷰 수 확인:

```sql
-- 메뉴 아이템 수 확인
SELECT COUNT(*) FROM menu_items WHERE restaurant_id = <rest_id>;

-- 리뷰 수 확인
SELECT COUNT(*) 
FROM menu_reviews rv 
JOIN menu_items m ON rv.menu_item_id = m.id 
WHERE m.restaurant_id = <rest_id>;
```

---

## 🎓 기술적 성과 및 결과

- **보안성**: `secrets.toml` 활용으로 DB 접속 정보 격리
- **효율성**: SQL JOIN 최적화를 통해 복잡한 데이터 관계를 단일 쿼리로 조회
- **무결성**: RDBMS 제약 조건을 통한 데이터 정합성 유지
- **사용자 경험**: 세션 기반 로그인 시스템으로 개인화된 서비스 제공
- **성능**: 캐싱과 상태 관리를 통한 불필요한 재렌더링 방지

---

## 📦 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 설정

`.streamlit/secrets.toml` 파일에 MySQL 및 API 키 설정:

```toml
[connections.mysql]
dialect = "mysql"
host = "your-host"
port = 3306
database = "your-database"
username = "your-username"
password = "your-password"

[api]
openai_key = "your-openai-api-key"
```

### 3. 애플리케이션 실행

```bash
streamlit run Login.py
```

---

**Developed with ❤️ by Team Restaurant Guide (우리FISA AI Engineering 6기)**