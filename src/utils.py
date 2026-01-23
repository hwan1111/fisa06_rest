# 민석 수정
import re
import uuid
from geopy.geocoders import Nominatim

def get_coords(address):
    """
    주소를 받아 정제된 주소와 (위도, 경도)를 반환합니다.
    주소 정제 및 반복 검색을 통해 정확도를 높입니다.
    """
    # 1. 주소 전처리 (불필요한 부분 제거)
    # 예: "3층", "F3", "B2", "101호", "가동", "본관", "산 21-3", "(상세주소)" 등
    noise_pattern = r"""
        \s*                                      # Optional leading whitespace
        (
            \( [^)]* \)                          # 괄호 안 내용 (e.g., ,(상세주소))
            |
            \b \d+ \s? [층Ff] \b                  # 층수 (e.g., "3층", "3 층", "3F")
            |
            \b [Bb] \s? \d+ \s? 층? \b             # 지하층 (e.g., "B1", "B 1층")
            |
            \b 지하 \s? \d* \s? 층? \b            # "지하" 또는 "지하1층"
            |
            \b [A-Za-z0-9가-힣-]+ (?:동|호|관)\b # 동/호/관 (e.g., "101호", "가-1동", "본관")
            |
            \b 산 \s? \d+ (?:-\d+)? \b           # 산 번지 (e.g., "산 21", "산 21-3")
        )
    """
    processed_address = re.sub(noise_pattern, ' ', address, flags=re.VERBOSE).strip()
    processed_address = ' '.join(processed_address.split())  # 중복 공백 제거

    geolocator = Nominatim(user_agent=f"fisa-rest-app-{uuid.uuid4().hex}")
    addr_parts = processed_address.split()

    # 2. 반복 검색 (주소 일부를 제거하며 찾기)
    while len(addr_parts) > 2:  # 최소 3단어 이상일 때까지만 검색 (e.g., "서울시 마포구")
        current_addr = " ".join(addr_parts)
        try:
            location = geolocator.geocode(current_addr, addressdetails=True)
            if location:
                # 3. 주소 재구성 (성공 시)
                raw_addr = location.raw.get('address', {})
                
                parts = []
                # 시/도
                if 'state' in raw_addr: parts.append(raw_addr['state'])
                elif 'city' in raw_addr: parts.append(raw_addr['city'])
                
                # 시/군/구 (중복 방지)
                if 'city' in raw_addr and parts and raw_addr['city'] not in parts[0]: parts.append(raw_addr['city'])
                elif 'suburb' in raw_addr: parts.append(raw_addr['suburb'])
                elif 'county' in raw_addr: parts.append(raw_addr['county'])

                # 도로명 + 건물번호
                if 'road' in raw_addr: parts.append(raw_addr['road'])
                if 'house_number' in raw_addr: parts.append(raw_addr['house_number'])
                
                cleaned_address = " ".join(list(dict.fromkeys(parts)))

                if cleaned_address:
                    return cleaned_address, location.latitude, location.longitude
                else: # 드문 경우지만, 정제 실패시 찾은 주소의 이름이라도 반환
                    return current_addr, location.latitude, location.longitude

        except Exception:
            # API 에러 등 발생 시 다음 단계로 넘어감
            pass
        
        addr_parts.pop() # 마지막 단어 제거 후 재시도

    return None, None, None # 모든 시도 실패 시

def get_star_rating(rating):
    try:
        val = float(rating)
        return "⭐" * int(round(val))
    except:
        return "⭐"
