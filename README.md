# 🍴 우리 반 맛집 실록 (MySQL Edition)

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
- [데이터베이스 설계](#-데이터베이스-설계)
- [주요 모듈 설명](#-python-파일-기능-설명)
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
  <img src="./image/image3.png" alt="주요 기능" width="70%">
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
  <img src="./image/arc.png" alt="시스템 아키텍처" width="70%">
</div>

- **Presentation Layer**: Streamlit 기반 사용자 인터페이스 및 결과 시각화
- **Application Logic**: `data_handler.py`, `recommend.py`를 통한 비즈니스 로직 및 API 연동
- **Data Layer**: MySQL을 통한 정규화된 데이터 모델링 및 저장
- **GIS Layer**: Geopy와 Folium을 결합한 지리 정보 처리

---

## 💾 데이터베이스 설계 (ERD)

데이터의 일관성을 위해 6개의 테이블이 외래키(FK)로 연결되어 있습니다.

<img src='https://github.com/hwan1111/fisa06_rest/blob/main/ERD.png' width="60%">

| 테이블명 | 설명 | 핵심 컬럼 |
|---------|------|----------|
| **USERS** | 사용자 정보 | user_id, username, password |
| **RESTAURANTS** | 맛집 정보 | restaurant_id, name, address, category |
| **MENU_ITEMS** | 메뉴 정보 | menu_id, restaurant_id, menu_name, price |
| **MENU_REVIEWS** | 리뷰 데이터 | review_id, menu_id, user_id, rating, comment |
| **PARTIES** | 모집 게시판 | party_id, restaurant_id, host_id |

## 🐍 Python 파일 기능 설명

프로젝트는 Streamlit 기반 UI(프론트) + MySQL(백엔드 데이터) + OpenAI/Open‑Meteo(외부 API)로 구성되어 있습니다.  
아래는 주요 `.py` 파일별 역할과 핵심 함수(또는 동작) 요약입니다.

### 1) `AI 맛집 추천.py` (Streamlit 메인 앱)
- **역할**: 서비스 화면(탭 UI) 렌더링 및 “예산별 추천/리뷰 분석” 전체 플로우를 담당합니다.
- **주요 화면**
  - **탭1: 예산별 맞춤 추천**
    - 주소 입력 → (Geopy) 위경도 변환 → (Open‑Meteo) 날씨 조회
    - 예산 이하 메뉴를 DB에서 조회 후 **TOP 5**만 추려서 AI 추천 문구 생성
    - TOP 5 가격 비교 차트(Plotly) + 상세 테이블 표시
  - **탭2: 리뷰 심층 분석**
    - 식당 선택 → 해당 식당의 메뉴/리뷰를 **JOIN 쿼리**로 가져와 텍스트 결합
    - OpenAI로 5개 항목(맛/가성비/서비스/위생/분위기) 점수 + 한줄평 생성
    - 레이더 차트 + 워드클라우드로 시각화
- **DB 연동 포인트**
  - `st.connection("mysql", type="sql")` 기반으로 SQL을 실행합니다.
  - 리뷰 분석은 다음 관계를 사용합니다:
    - `menu_reviews.menu_item_id` → `menu_items.id`
    - `menu_items.restaurant_id` → `restaurants.id`
- **성능 최적화**
  - `@st.cache_data`로 **주소 지오코딩/날씨 조회/DB 조회**를 캐싱하여 불필요한 재호출을 줄입니다.
  - `st.session_state`로 탭별 분석 결과를 유지해 리렌더링 시 UX가 깨지지 않게 했습니다.

### 2) `recommend.py` (AI/날씨 로직 모듈)
- **역할**: 외부 API를 호출하여 “날씨 정보”와 “AI 결과”를 만들어 메인 앱에서 재사용하도록 분리한 모듈입니다.
- **주요 함수**
  - `get_weather(lat, lon)`  
    - Open‑Meteo를 호출해 현재 날씨/기온을 가져옵니다.
  - `get_ai_recommendation(weather_info, candidates, user_budget)`  
    - 후보 메뉴 리스트(메뉴명/식당명/카테고리/가격) + 예산 + 날씨를 입력으로,
      **예산 근접도**와 **날씨 연관성**을 반영한 추천 멘트를 생성합니다.
  - `get_review_analysis(rest_name, reviews_text)`  
    - 리뷰 텍스트를 기반으로 5개 항목 점수와 한줄평을 **JSON 형태**로 반환합니다.

### 3) (선택) `data_handler.py`, `login.py` 등 보조 모듈
> 레포에 포함된 경우에만 사용됩니다. (팀 버전에 따라 파일/역할이 다를 수 있어요.)

- `data_handler.py`: DB CRUD(조회/삽입/수정/삭제) 헬퍼 및 비즈니스 로직 모음 (프로젝트 호환을 위해 import 유지)
- `login.py`: 로그인/회원가입 등 사용자 인증 흐름을 분리한 모듈
- `utils.py`: 주소→좌표 변환 등 공통 유틸 함수

---

### 🧩 “리뷰가 0개로 나오는 경우” 체크리스트
- `menu_reviews.menu_item_id` 값이 실제 `menu_items.id`와 일치하는지
- `menu_items.restaurant_id` 값이 선택한 `restaurants.id`와 일치하는지
- 아래 쿼리로 식당별 리뷰 수가 0인지 확인:
  - `SELECT COUNT(*) FROM menu_items WHERE restaurant_id = <rest_id>;`
  - `SELECT COUNT(*) FROM menu_reviews rv JOIN menu_items m ON rv.menu_item_id=m.id WHERE m.restaurant_id=<rest_id>;`

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
- **증상**: Streamlit 리렌더링 시 지도가 계속 초기화됨
- **해결**: `st.session_state`에 지도 객체를 캐싱하여 상태를 유지함

### 2. 주소 변환(Geocoding) 오류
- **원인**: 잘못된 주소 입력으로 인한 위경도 추출 실패
- **해결**: Geopy 예외 처리 로직 추가 및 주소 검증 단계 도입

### 3. 풀 리퀘스트오류

---

## 🎓 기술적 성과 및 결과
- **보안성**: `secrets.toml` 활용으로 DB 접속 정보 격리
- **효율성**: SQL JOIN 최적화를 통해 복잡한 데이터 관계를 단일 쿼리로 조회
- **무결성**: RDBMS 제약 조건을 통한 데이터 정합성 유지

---
**Developed with ❤️ by Team Restaurant Guide (우리FISA AI Engineering 6기)**
