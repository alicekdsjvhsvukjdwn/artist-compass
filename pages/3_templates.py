import streamlit as st
from src.io import load_json

st.title("🥁 Production & Templates")

templates = load_json("templates.json", default=[])

if not templates:
    st.error("Aucun template trouvé. Vérifie que `data/templates.json` existe et est bien push sur GitHub.")
    st.stop()

names = [t.get("name", "Sans nom") for t in templates]
choice = st.selectbox("Choisir un template", names)

t = next(x for x in templates if x.get("name") == choice)

st.write(f"**BPM conseillé :** {t.get('bpm', '—')}")
st.markdown("### Checklist")
for item in t.get("checklist", []):
    st.checkbox(item, key=f"{choice}-{item}")
