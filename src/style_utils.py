import streamlit as st

def set_custom_theme():
    st.markdown("""
    <style>
    body {
        background-color: rgba(63, 192, 96, 0.04);
    }
    .block-container {
        padding-top: 1rem;
    }
    .kpi-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def format_number(value, is_currency=False):
    if isinstance(value, float):
        if abs(value) > 1e6:
            return f"{value:,.0f}"
        elif is_currency:
            return f"${value:,.2f}"
        else:
            return f"{value:,.2f}"
    elif isinstance(value, int):
        return f"{value:,}"
    else:
        return str(value)