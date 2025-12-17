import random
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

# Si ton projet a bien src/__init__.py + src/io.py
from src.io import load_yaml, load_json, load_csv, append_row_csv

st.set_page_config(page_title="Artist Compass", page_icon="🎛️", layout="wide")


# ---------- Helpers ----------
JOURNAL_COLS = [
    "date", "titre", "style", "etat", "temps_min",
    "objectif_du_jour", "blocage", "apprentissage", "next_step",
    "lien_audio", "score_monstrable"
]

ETATS = ["idée", "démo", "presque fini", "sorti"]


def safe_int(x, default=0):
    try:
        if pd.isna(x):
            return default
        return int(float(x))
    except Exception:
        return default


def pick_style(styles_list):
    if not styles_list:
        return None
    return random.choice(styles_list)


# ---------- Load data ----------
profile = load_yaml(
    "profile.yaml",
    default={
        "pseudo": "Artiste",
        "styles_cibles": [],
        "influences": [],
        "niveau": "débutante",
        "objectifs": {"3_mois": "", "1_an": ""},
        "points": {"technique_a_bosser": [], "creatif_a_bosser": [], "mental_a_proteger": []},
        "regles": {"focus_styles_max": 2, "terminer_avant_nouveau": True},
    },
)

styles = load_json("styles.json", default=[])
df_journal = load_csv("journal.csv", default_columns=JOURNAL_COLS)

# normalisation douce
if "date" in df_journal.columns:
    # tente de parser la date si possible
    try:
        df_journal["date_parsed"] = pd.to_datetime(df_journal["date"], errors="coerce")
    except Exception:
        df_journal["date_parsed"] = pd.NaT
else:
    df_journal["date"] = ""
    df_journal["date_parsed"] = pd.NaT

if "etat" not in df_journal.columns:
    df_journal["etat"] = ""

if "temps_min" not in df_journal.columns:
    df_journal["temps_min"] = 0


# ---------- Header ----------
pseudo = profile.get("pseudo", "Artiste")
niveau = profile.get("niveau", "débutante")
obj_3m = (profile.get("objectifs", {}) or {}).get("3_mois", "")
obj_1a = (profile.get("objectifs", {}) or {}).get("1_an", "")

st.title("🎧 Artist Compass")
st.caption("Ton cockpit. Pas ton tribunal. Mais il sait quand tu procrastines 😇")

c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 1.2])
with c1:
    st.metric("Profil", f"{pseudo} · {niveau}")
with c2:
    st.metric("Objectif 3 mois", obj_3m if obj_3m else "—")
with c3:
    st.metric("Objectif 1 an", obj_1a if obj_1a else "—")
with c4:
    focus_styles = profile.get("styles_cibles", []) or []
    st.metric("Focus styles", ", ".join(focus_styles[:2]) if focus_styles else "—")


st.divider()

# ---------- Dashboard layout ----------
left, right = st.columns([1.35, 1])

# ===== LEFT: Focus du jour + plan =====
with left:
    st.subheader("🧭 Focus du jour")

    if "style_pick" not in st.session_state:
        st.session_state.style_pick = None

    # choix style : priorise styles_cibles si dispo
    styles_cibles = profile.get("styles_cibles", []) or []
    styles_names = [s.get("style", "Sans nom") for s in styles if isinstance(s, dict)]

    prioritized = []
    if styles_cibles and styles_names:
        # remet en tête ceux qui matchent
        for name in styles_names:
            if name in styles_cibles:
                prioritized.append(name)
        for name in styles_names:
            if name not in prioritized:
                prioritized.append(name)
    else:
        prioritized = styles_names

    colA, colB = st.columns([1, 1])
    with colA:
        chosen_name = st.selectbox(
            "Choisis un style (ou laisse-toi guider)",
            options=(prioritized if prioritized else ["—"]),
            index=0,
            disabled=(not prioritized),
        )
    with colB:
        if st.button("🎲 Tirage au sort (anti-prise de tête)", use_container_width=True, disabled=not styles):
            pick = pick_style(styles)
            st.session_state.style_pick = pick.get("style") if pick else None

    # Résout le style final
    final_style_name = st.session_state.style_pick or (chosen_name if chosen_name != "—" else None)
    style_obj = None
    if final_style_name and styles:
        for s in styles:
            if isinstance(s, dict) and s.get("style") == final_style_name:
                style_obj = s
                break

    if not style_obj:
        st.info("Ajoute des styles dans `data/styles.json` pour activer le mode focus du jour.")
    else:
        bpm = style_obj.get("bpm", [])
        mood = style_obj.get("mood", [])
        contraintes = style_obj.get("contraintes", [])
        refs = style_obj.get("refs", [])

        st.write(f"**Style :** {style_obj.get('style')}")
        if bpm:
            st.write(f"**BPM :** {bpm[0]}–{bpm[1]}" if isinstance(bpm, list) and len(bpm) == 2 else f"**BPM :** {bpm}")
        if mood:
            st.write(f"**Mood :** {', '.join(mood)}")

        st.markdown("**Contraintes (ton mini-brief du jour)**")
        if contraintes:
            for i, c in enumerate(contraintes, start=1):
                st.checkbox(f"{i}. {c}", key=f"contraintes_{final_style_name}_{i}")
        else:
            st.caption("Pas de contraintes renseignées → ajoute `contraintes` dans styles.json.")

        with st.expander("🎧 Références"):
            if refs:
                for r in refs:
                    st.write(f"- {r}")
            else:
                st.caption("Ajoute `refs` dans styles.json (3 titres suffisent).")

        st.markdown("### ✅ Plan express (45–90 min)")
        st.write("1) 10 min : choisir 1 son / 1 patch / 1 vibe")
        st.write("2) 25 min : loop A (drums + harmonie OU drums + bass)")
        st.write("3) 25 min : variation B (même idée, plus d’énergie ou moins)")
        st.write("4) 10 min : bounce mp3 + note 3 améliorations")

    st.divider()

    st.subheader("📝 Ajout rapide au journal (preuve que l’app vit)")
    with st.form("quick_journal", clear_on_submit=True):
        titre = st.text_input("Titre du projet", placeholder="ex: NOCTURNE_140BPM_v1")
        style = st.text_input("Style", value=(final_style_name or ""))
        etat = st.selectbox("État", ETATS, index=1)  # par défaut "démo"
        temps_min = st.number_input("Temps (min)", min_value=0, max_value=600, value=60, step=5)
        objectif_du_jour = st.text_input("Objectif du jour", placeholder="ex: faire loop + variation")
        apprentissage = st.text_input("Ce que tu as appris", placeholder="ex: hats trop chargés → simplifier")
        next_step = st.text_input("Prochaine étape", placeholder="ex: écrire hook + prise voix test")
        score = st.slider("Score 'montrable' (0–5)", 0, 5, 2)
        lien_audio = st.text_input("Lien audio (optionnel)", placeholder="Drive/SoundCloud/local path…")

        submitted = st.form_submit_button("Ajouter au journal")

    if submitted:
        if not titre.strip():
            st.error("Donne au moins un titre (même nul). Sinon tu vas perdre la trace, et ton futur-toi va te détester.")
        else:
            row = {
                "date": str(date.today()),
                "titre": titre.strip(),
                "style": style.strip(),
                "etat": etat,
                "temps_min": temps_min,
                "objectif_du_jour": objectif_du_jour.strip(),
                "apprentissage": apprentissage.strip(),
                "next_step": next_step.strip(),
                "score_monstrable": score,
                "lien_audio": lien_audio.strip(),
            }
            df_journal = append_row_csv("journal.csv", row, default_columns=JOURNAL_COLS)
            st.success("Ajouté ✅ (si tu es sur Streamlit Cloud, pense à exporter régulièrement le CSV).")

    # Export CSV
    export_df = df_journal.drop(columns=["date_parsed"], errors="ignore")
    st.download_button(
        "📥 Télécharger le journal (CSV)",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name="journal.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ===== RIGHT: Stats + derniers projets =====
with right:
    st.subheader("📈 Stats rapides")

    total = len(df_journal)
    by_state = df_journal["etat"].value_counts(dropna=False).to_dict() if total else {}

    # 7 derniers jours
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    last7 = df_journal[df_journal["date_parsed"] >= week_ago] if "date_parsed" in df_journal else df_journal.iloc[0:0]

    mins_last7 = 0
    if len(last7) and "temps_min" in last7.columns:
        mins_last7 = sum(safe_int(x, 0) for x in last7["temps_min"].tolist())

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Projets trackés", total)
    with c2:
        st.metric("Temps 7 jours (min)", mins_last7)

    st.markdown("**Répartition par état**")
    if by_state:
        for k in ETATS:
            st.write(f"- {k} : {by_state.get(k, 0)}")
    else:
        st.caption("Aucune entrée dans le journal pour l’instant.")

    st.divider()

    st.subheader("🗂️ Dernières entrées")
    if total:
        show = df_journal.sort_values("date_parsed", ascending=False, na_position="last").head(8)
        cols_show = ["date", "titre", "style", "etat", "temps_min", "score_monstrable"]
        cols_show = [c for c in cols_show if c in show.columns]
        st.dataframe(show[cols_show], use_container_width=True, hide_index=True)
    else:
        st.info("Ajoute 2–3 entrées dans le journal à gauche et tu auras un vrai dashboard.")

    st.divider()

    st.subheader("🧩 Raccourcis")
    st.markdown(
        """
- **Profil & Boussole** : objectifs + règles (anti-dispersion)
- **Styles & Références** : choisir ton terrain du jour
- **Production/Templates** : démarrer vite avec des checklists
- **Journal** : suivre tes morceaux + progrès
"""
    )
