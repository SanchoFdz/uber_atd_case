import pandas as pd
import streamlit as st
import numpy as np

@st.cache_data
def load_data():

    df = pd.read_csv("./data/raw/BC_A&A_with_ATD.csv")
    timestamp_cols = [
    'restaurant_offered_timestamp_utc',
    'order_final_state_timestamp_local',
    'eater_request_timestamp_local'
    ]

    for col in timestamp_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    df['restaurant_offered_timestamp_local'] = df['restaurant_offered_timestamp_utc'].dt.tz_localize('UTC').dt.tz_convert('America/Mexico_City')
    df['eater_request_timestamp_local'] = df['eater_request_timestamp_local'].dt.tz_localize('America/Mexico_City')
    df['order_final_state_timestamp_local'] = df['order_final_state_timestamp_local'].dt.tz_localize('America/Mexico_City')

    categorical_cols = [
        'region', 'territory', 'country_name', 'courier_flow',
        'geo_archetype', 'merchant_surface'
    ]

    df[categorical_cols] = df[categorical_cols].astype('category')

    uuid_cols = ['workflow_uuid', 'driver_uuid', 'delivery_trip_uuid']
    df[uuid_cols] = df[uuid_cols].astype(str)

    numeric_cols = ['pickup_distance', 'dropoff_distance']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

    df.replace('\\N', np.nan, inplace=True)

    df['date'] = df['eater_request_timestamp_local'].dt.date
    df['hour'] = df['eater_request_timestamp_local'].dt.hour
    df['day_of_week'] = df['eater_request_timestamp_local'].dt.day_of_week
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

    st.session_state.df = df

    return df