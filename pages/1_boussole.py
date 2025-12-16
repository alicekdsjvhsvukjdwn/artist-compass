import streamlit as st
from src.io import load_yaml, save_yaml

st.title("🧭 Profil & Boussole")

profile = load_yaml("profile.yaml", default={"pseudo": "", "niveau": "débutante"})

pseudo = st.text_input("Pseudo", value=profile.get("pseudo", ""))
niveau = st.selectbox("Niveau", ["débutante", "intermédiaire", "avancée"],
                      index=["débutante","intermédiaire","avancée"].index(profile.get("niveau","débutante")))

if st.button("💾 Sauvegarder"):
    profile["pseudo"] = pseudo
    profile["niveau"] = niveau
    save_yaml("profile.yaml", profile)
    st.success("Sauvegardé.")
