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
def get_all_data_joined():
    """
    Returns a comprehensive DataFrame by joining restaurants, menu_items, 
    menu_reviews, and users.
    """
    query = """
        SELECT 
            r.id as restaurant_id,
            r.name as restaurant_name,
            r.category,
            r.address,
            r.lat,
            r.lon,
            r.url,
            mi.item_name,
            mi.price,
            mr.rating,
            mr.comment,
            mr.timestamp,
            u.name as user_name
        FROM restaurants r
        LEFT JOIN menu_items mi ON r.id = mi.restaurant_id
        LEFT JOIN menu_reviews mr ON mi.id = mr.menu_item_id
        LEFT JOIN users u ON mr.user_id = u.id
    """
    return fetch_query(query)

def save_full_visit_data(
    user_name, user_email, 
    rest_name, rest_address, rest_category, rest_url, 
    menu_name, menu_price, 
    review_rating, review_comment
):
    """
    Handles the atomic insertion of a new visit, including user, restaurant,
    menu item, and menu review.
    """
    # 1. Get or create user
    user_id = get_or_create_user(user_name, user_email)

    # 2. Get or create restaurant
    rest_df = fetch_query(
        "SELECT id FROM restaurants WHERE name = :name AND address = :address",
        params={"name": rest_name, "address": rest_address}
    )
    if not rest_df.empty:
        rest_id = rest_df.iloc[0]['id']
    else:
        from utils import get_coords
        lat, lon = get_coords(rest_address)
        if not lat:
            st.error("Could not geocode address.")
            return
        
        rest_id = str(uuid.uuid4())[:8]
        execute_query(
            """
            INSERT INTO restaurants (id, name, category, address, lat, lon, url, added_at)
            VALUES (:id, :name, :category, :address, :lat, :lon, :url, :added_at)
            """,
            params={
                "id": rest_id, "name": rest_name, "category": rest_category, 
                "address": rest_address, "lat": lat, "lon": lon, 
                "url": rest_url, "added_at": datetime.now()
            }
        )

    # 3. Create menu item
    menu_item_id = str(uuid.uuid4())[:8]
    execute_query(
        """
        INSERT INTO menu_items (id, restaurant_id, item_name, price, added_at)
        VALUES (:id, :rest_id, :name, :price, :added_at)
        """,
        params={
            "id": menu_item_id, "rest_id": rest_id, "name": menu_name, 
            "price": menu_price, "added_at": datetime.now()
        }
    )

    # 4. Create menu review
    review_id = str(uuid.uuid4())[:8]
    execute_query(
        """
        INSERT INTO menu_reviews (id, menu_item_id, user_id, rating, comment, timestamp)
        VALUES (:id, :menu_id, :user_id, :rating, :comment, :timestamp)
        """,
        params={
            "id": review_id, "menu_id": menu_item_id, "user_id": user_id,
            "rating": review_rating, "comment": review_comment, "timestamp": datetime.now()
        }
    )
    
    st.success("리뷰가 성공적으로 등록되었습니다!")
    st.rerun()

# Import get_or_create_user from login and utility functions
from login import get_or_create_user
