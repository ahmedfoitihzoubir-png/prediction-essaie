import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ---------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------
st.set_page_config(
    page_title="Météo Oran",
    page_icon="⛅",
    layout="wide"
)

# Coordonnées géographiques d'Oran, Algérie
LATITUDE = 35.6969
LONGITUDE = -0.6331

# ---------------------------------------------------------
# Récupération des données météo (API Open-Meteo)
# ---------------------------------------------------------
@st.cache_data(ttl=1800)  # cache de 30 minutes
def get_weather_data(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
        "hourly": "temperature_2m,precipitation_probability",
        "timezone": "Africa/Algiers",
        "forecast_days": 7
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def weather_code_to_text(code):
    """Traduction simplifiée des codes météo WMO en français"""
    codes = {
        0: "Ciel dégagé", 1: "Principalement dégagé", 2: "Partiellement nuageux",
        3: "Couvert", 45: "Brouillard", 48: "Brouillard givrant",
        51: "Bruine légère", 53: "Bruine modérée", 55: "Bruine dense",
        61: "Pluie légère", 63: "Pluie modérée", 65: "Pluie forte",
        71: "Neige légère", 80: "Averses légères", 81: "Averses modérées",
        95: "Orage"
    }
    return codes.get(code, "Conditions variables")


# ---------------------------------------------------------
# Interface principale
# ---------------------------------------------------------
st.title("⛅ Prévision météorologique — Oran")
st.caption(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

try:
    data = get_weather_data(LATITUDE, LONGITUDE)

    # ----- Conditions actuelles -----
    current = data["current"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Température", f"{current['temperature_2m']} °C")
    col2.metric("Humidité", f"{current['relative_humidity_2m']} %")
    col3.metric("Vent", f"{current['wind_speed_10m']} km/h")
    col4.metric("Conditions", weather_code_to_text(current["weather_code"]))

    st.divider()

    # ----- Prévision sur 7 jours -----
    st.subheader("Prévision sur 7 jours")
    daily = data["daily"]
    df_daily = pd.DataFrame({
        "Date": pd.to_datetime(daily["time"]),
        "Max (°C)": daily["temperature_2m_max"],
        "Min (°C)": daily["temperature_2m_min"],
        "Précipitations (mm)": daily["precipitation_sum"],
        "Conditions": [weather_code_to_text(c) for c in daily["weather_code"]]
    })

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_daily["Date"], y=df_daily["Max (°C)"],
        mode="lines+markers", name="Température max", line=dict(color="orangered")
    ))
    fig.add_trace(go.Scatter(
        x=df_daily["Date"], y=df_daily["Min (°C)"],
        mode="lines+markers", name="Température min", line=dict(color="royalblue")
    ))
    fig.update_layout(
        xaxis_title="Date", yaxis_title="Température (°C)",
        hovermode="x unified", height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        df_daily.style.format({"Max (°C)": "{:.1f}", "Min (°C)": "{:.1f}", "Précipitations (mm)": "{:.1f}"}),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ----- Prévision horaire (aujourd'hui) -----
    st.subheader("Prévision horaire — aujourd'hui")
    hourly = data["hourly"]
    df_hourly = pd.DataFrame({
        "Heure": pd.to_datetime(hourly["time"]),
        "Température (°C)": hourly["temperature_2m"],
        "Probabilité de pluie (%)": hourly["precipitation_probability"]
    })
    df_today = df_hourly[df_hourly["Heure"].dt.date == datetime.now().date()]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_today["Heure"], y=df_today["Probabilité de pluie (%)"],
        name="Prob. de pluie (%)", marker_color="lightblue", yaxis="y2", opacity=0.5
    ))
    fig2.add_trace(go.Scatter(
        x=df_today["Heure"], y=df_today["Température (°C)"],
        mode="lines+markers", name="Température (°C)", line=dict(color="darkorange")
    ))
    fig2.update_layout(
        yaxis=dict(title="Température (°C)"),
        yaxis2=dict(title="Probabilité de pluie (%)", overlaying="y", side="right", range=[0, 100]),
        hovermode="x unified", height=400
    )
    st.plotly_chart(fig2, use_container_width=True)

except requests.exceptions.RequestException as e:
    st.error(f"Impossible de récupérer les données météo : {e}")

st.divider()
st.caption("Source des données : Open-Meteo.com (API gratuite, aucune clé requise)")
