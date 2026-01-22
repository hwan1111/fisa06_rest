import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import pandas as pd
import uuid

# 모듈 불러오기
from src.data_handler import load_gsheet_data, save_gsheet_data
from src.utils import get_coords, get_star_rating
from src.components import add_review, render_comments

st.set_page_config(page_title="우리 반 맛집 실록", layout="wide")
# ... 이후 레이아웃 및 로직 호출 ...
