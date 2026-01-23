import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Import the centralized query functions from login.py
from login import execute_query, fetch_query

# =============================================================================
# Google Sheets Data Functions
# =============================================================================

conn_gsheet = st.connection("gsheets", type=GSheetsConnection)

def load_gsheet_data(worksheet_name):
    try:
        df = conn_gsheet.read(worksheet=worksheet_name, ttl=0)
        if df is None or df.empty: raise ValueError
        if worksheet_name == "restaurants":
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        else:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        return df
    except:
        if worksheet_name == "restaurants":
            return pd.DataFrame(columns=["id", "name", "category", "address", "url", "lat", "lon"])
        else:
            return pd.DataFrame(columns=["id", "rest_id", "parent_id", "rating", "comment", "timestamp", "user"])

def save_gsheet_data(df, worksheet_name):
    conn_gsheet.update(worksheet=worksheet_name, data=df)
    st.cache_data.clear()


# =============================================================================
# MySQL Data Functions
# =============================================================================

# --- Restaurant-related Functions ---
def add_restaurant(name, category, address, url, lat, lon):
    """Adds a new restaurant to the database and returns its new ID."""
    rest_id = str(uuid.uuid4())[:8]
    query = '''
        INSERT INTO restaurants (id, name, category, address, lat, lon, url, added_at)
        VALUES (:id, :name, :category, :address, :lat, :lon, :url, :added_at)
    '''
    params = {
        "id": rest_id, "name": name, "category": category, "address": address, 
        "lat": lat, "lon": lon, "url": url, "added_at": datetime.now()
    }
    execute_query(query, params)
    return rest_id

def get_all_restaurants():
    """Fetches all restaurant data from the database."""
    return fetch_query("SELECT * FROM restaurants")

# --- Review-related Functions ---
def add_review(restaurant_id, user_id, rating, content, parent_id=None):
    """Adds a new review to the database."""
    review_id = str(uuid.uuid4())[:8]
    query = """
        INSERT INTO reviews (id, restaurant_id, user_id, rating, content, parent_id, created_at) 
        VALUES (:id, :rid, :uid, :rating, :content, :pid, :created_at)
    """
    params = {
        "id": review_id, "rid": restaurant_id, "uid": user_id,
        "rating": rating, "content": content, "pid": parent_id, 
        "created_at": datetime.now()
    }
    execute_query(query, params)

def get_all_reviews():
    """Fetches all review data for trend analysis."""
    return fetch_query("SELECT * FROM reviews")

def get_reviews_by_restaurant(restaurant_id):
    """Fetches all reviews for a specific restaurant, joined with user names."""
    query = '''
        SELECT r.*, u.name as user_name
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.restaurant_id = :rid
        ORDER BY r.created_at DESC
    '''
    return fetch_query(query, params={"rid": restaurant_id})
