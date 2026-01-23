# 민석 수정
import uuid
from geopy.geocoders import Nominatim

def get_coords(address):
    try:
        geolocator = Nominatim(user_agent=f"my_class_app_{uuid.uuid4().hex[:6]}")
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
    except:
        return None, None
    return None, None

def get_star_rating(rating):
    try:
        val = float(rating)
        return "⭐" * int(round(val))
    except:
        return "⭐"
