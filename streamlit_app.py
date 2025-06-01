import streamlit as st
from src.data_loader import load_data, load_gdf
from src.style_utils import set_custom_theme

st.set_page_config(page_title="Uber Eats Ops Dashboard", layout="wide")
set_custom_theme()
st.title("✍️ Introduction")
st.title("Welcome to Uber Eats Delivery Intelligence Dashboard")

st.markdown("""
This dashboard provides an overview on UberEats delivery performance across regions to help you
monitor, inquire, dive deep and optimize delivery and operations at scale.
            
The logic is divided in three main sections:
1. **Conversation Openers**: This section provides an overview of key performance indicators (KPIs) and visuals showcasig only one variable at a time for a quick overview of the health of your operations and to start asking questions.

2. **Root Cause Anlysis**: This sections is designed to help you identifty more complex relationships, study multiple variables at once, and explore the root causes of performance issues. 

3. **Advanced models**: Both Model Studio and Planning Simulator are designed to help you understand the impact certain changes in key variables have on your KPIs and use this level of insights to asses your plans for the week. 

The filters on the left side bar are global and will apply to all pages. Use them to narrow down your data by date, hour, region, and other key variables.

Data is updated on a weekly basis, so the recommended practice is to come back every Monday to see the latest performance metrics and trends to define and asses your plans for the upcoming week.          
""")


if "df" not in st.session_state:
    df, df_prep = load_data()
    gdf = load_gdf()
    st.session_state.df = df
    st.session_state.gdf = gdf
    st.session_state.df_prep = df_prep


