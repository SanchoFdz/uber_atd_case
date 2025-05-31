import streamlit as st
from src.data_loader import load_data
from src.style_utils import set_custom_theme

st.set_page_config(page_title="Uber Eats Ops Dashboard", layout="wide")
set_custom_theme()

if "df" not in st.session_state:
    df = load_data()
    st.session_state.df = df


