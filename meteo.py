import streamlit as st
import math

# Configuration de la page
st.set_page_config(
    page_title="Calculateur de Surface d'un Cercle",
    page_icon="⭕",
    layout="centered"
)

st.title("⭕ Calculateur de Surface d'un Cercle")

st.write("Entrez le diamètre du cercle pour calculer sa surface.")

# Saisie du diamètre
diametre = st.number_input(
    "Diamètre",
    min_value=0.0,
    value=10.0,
    step=0.1
)

if st.button("Calculer"):
    rayon = diametre / 2
    surface = math.pi * rayon**2

    st.success(f"Surface du cercle : **{surface:.2f} unités²**")

    st.write("### Détails du calcul")
    st.write(f"- Diamètre : {diametre:.2f}")
    st.write(f"- Rayon : {rayon:.2f}")
    st.write(f"- Formule : π × r²")
    st.write(f"- Calcul : π × ({rayon:.2f})² = **{surface:.2f}**")
