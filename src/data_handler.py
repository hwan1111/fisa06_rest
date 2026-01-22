import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection


conn = st.connection("gsheets", type=GSheetsConnection)

def load_gsheet_data(worksheet_name):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
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
    conn.update(worksheet=worksheet_name, data=df)
    st.cache_data.clear()

