import streamlit as st
from datetime import date
from src.io import load_csv, append_row_csv

st.title("📝 Journal")

cols = ["date", "titre", "style", "etat", "blocage", "apprentissage", "next_step", "lien_audio"]
df = load_csv("journal.csv", default_columns=cols)

with st.form("add"):
    titre = st.text_input("Titre")
    style = st.text_input("Style")
    etat = st.selectbox("État", ["idée", "démo", "presque fini", "sorti"])
    submitted = st.form_submit_button("Ajouter")

if submitted and titre:
    df = append_row_csv("journal.csv", {
        "date": str(date.today()),
        "titre": titre,
        "style": style,
        "etat": etat,
    }, default_columns=cols)
    st.success("Ajouté.")

st.dataframe(df, use_container_width=True)
