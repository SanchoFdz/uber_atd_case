import streamlit as st

def set_custom_theme():
    """
    Aplica un tema visual personalizado a la aplicación de Streamlit mediante CSS embebido.

    Este estilo ajusta:
    - El fondo general de la aplicación
    - El espaciado del contenedor principal
    - El diseño de tarjetas KPI (colores, bordes, sombras)

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
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
    """
    Formatea un valor numérico para su despliegue visual en dashboard.

    Si el valor es:
    - un número grande (> 1 millón): lo redondea sin decimales y con comas.
    - un número monetario: incluye símbolo de pesos y dos decimales.
    - un entero: agrega separador de miles.
    - otro tipo: lo convierte a string.

    Parameters
    ----------
    value : int, float, or any
        Valor a formatear.
    is_currency : bool, optional
        Si es True, el valor se formatea como monto en MXN. Por defecto es False.

    Returns
    -------
    str
        Representación formateada del valor.
    """
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