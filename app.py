import json
import random
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from src.io import load_yaml, load_json, load_csv, append_row_csv

st.set_page_config(page_title="Artist Compass", page_icon="🎛️", layout="wide")


# -------------------- CONFIG --------------------
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


def normalize_list(x):
    return x if isinstance(x, list) else ([] if x is None else [x])


# -------------------- LOAD DATA --------------------
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
templates = load_json("templates.json", default=[])

df_journal = load_csv("journal.csv", default_columns=JOURNAL_COLS)
df_journal["date_parsed"] = pd.to_datetime(df_journal.get("date", ""), errors="coerce")
if "temps_min" not in df_journal.columns:
    df_journal["temps_min"] = 0
if "etat" not in df_journal.columns:
    df_journal["etat"] = ""


# -------------------- SESSION STATE --------------------
if "style_pick" not in st.session_state:
    st.session_state.style_pick = None

if "active_template_name" not in st.session_state:
    st.session_state.active_template_name = None

if "templates_local" not in st.session_state:
    # permet d’ajouter des templates sans écrire sur disque (cloud-safe)
    st.session_state.templates_local = templates.copy()


# -------------------- UI STYLE --------------------
st.markdown(
    """
<style>
.block-card {
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 16px 16px 10px 16px;
    background: rgba(255,255,255,0.02);
}
.block-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 4px;
}
.block-sub {
    opacity: 0.75;
    margin-bottom: 10px;
}
hr.soft {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.10);
    margin: 14px 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------- HEADER --------------------
pseudo = profile.get("pseudo", "Artiste")
niveau = profile.get("niveau", "débutante")
obj_3m = (profile.get("objectifs", {}) or {}).get("3_mois", "")
obj_1a = (profile.get("objectifs", {}) or {}).get("1_an", "")
focus_styles = normalize_list(profile.get("styles_cibles", []))[:2]

st.title("🎧 Artist Compass")
st.caption("Ton cockpit. Pas ton tribunal. Mais il sait quand tu procrastines 😇")

m1, m2, m3, m4 = st.columns([1.2, 1.2, 1.2, 1.2])
with m1:
    st.metric("Profil", f"{pseudo} · {niveau}")
with m2:
    st.metric("Objectif 3 mois", obj_3m if obj_3m else "—")
with m3:
    st.metric("Objectif 1 an", obj_1a if obj_1a else "—")
with m4:
    st.metric("Focus styles", ", ".join(focus_styles) if focus_styles else "—")

st.divider()


# -------------------- QUICK START (3 CARDS) --------------------
left_card, mid_card, right_card = st.columns([1, 1, 1])

# Prépare listes
styles_names = [s.get("style", "Sans nom") for s in styles if isinstance(s, dict)]
templates_names = [t.get("name", "Sans nom") for t in st.session_state.templates_local if isinstance(t, dict)]

# Style prioritisation: styles_cibles en haut
prioritized_styles = []
if styles_names:
    for name in styles_names:
        if name in focus_styles:
            prioritized_styles.append(name)
    for name in styles_names:
        if name not in prioritized_styles:
            prioritized_styles.append(name)

def get_style_obj(style_name: str):
    for s in styles:
        if isinstance(s, dict) and s.get("style") == style_name:
            return s
    return None

def get_template_obj(template_name: str):
    for t in st.session_state.templates_local:
        if isinstance(t, dict) and t.get("name") == template_name:
            return t
    return None

# ---- Card 1: Style du jour
with left_card:
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown('<div class="block-title">🎯 Choisir ton terrain</div>', unsafe_allow_html=True)
    st.markdown('<div class="block-sub">Un style = un brief. On évite le freestyle mental.</div>', unsafe_allow_html=True)

    if not prioritized_styles:
        st.warning("Ajoute des styles dans `data/styles.json`.")
    else:
        picked = st.selectbox("Style du jour", prioritized_styles, key="qs_style_select")
        cA, cB = st.columns([1, 1])
        with cA:
            if st.button("✅ Fixer ce style", use_container_width=True):
                st.session_state.style_pick = picked
        with cB:
            if st.button("🎲 Random", use_container_width=True):
                st.session_state.style_pick = random.choice(prioritized_styles)

        final_style = st.session_state.style_pick or picked
        style_obj = get_style_obj(final_style)

        st.markdown('<hr class="soft">', unsafe_allow_html=True)
        if style_obj:
            bpm = style_obj.get("bpm", None)
            mood = style_obj.get("mood", [])
            st.write(f"**Sélection :** {final_style}")
            if bpm:
                if isinstance(bpm, list) and len(bpm) == 2:
                    st.write(f"**BPM :** {bpm[0]}–{bpm[1]}")
                else:
                    st.write(f"**BPM :** {bpm}")
            if mood:
                st.write(f"**Mood :** {', '.join(mood)}")
        else:
            st.caption("Style introuvable dans styles.json (nom différent ?)")

    st.markdown("</div>", unsafe_allow_html=True)

# ---- Card 2: Templates (lancer + checklist)
with mid_card:
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown('<div class="block-title">⚡ Démarrer avec un template</div>', unsafe_allow_html=True)
    st.markdown('<div class="block-sub">Pour produire sans repartir de zéro (et garder ton cerveau en laisse).</div>', unsafe_allow_html=True)

    if not templates_names:
        st.warning("Ajoute des templates dans `data/templates.json` (même 2 suffisent).")
    else:
        default_idx = 0
        if st.session_state.active_template_name in templates_names:
            default_idx = templates_names.index(st.session_state.active_template_name)

        chosen_t = st.selectbox("Template", templates_names, index=default_idx, key="qs_template_select")

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("🚀 Charger la checklist", use_container_width=True):
                st.session_state.active_template_name = chosen_t
        with c2:
            if st.button("🎲 Random template", use_container_width=True):
                st.session_state.active_template_name = random.choice(templates_names)

        active_name = st.session_state.active_template_name or chosen_t
        t_obj = get_template_obj(active_name)

        st.markdown('<hr class="soft">', unsafe_allow_html=True)
        if t_obj:
            st.write(f"**Actif :** {t_obj.get('name', active_name)}")
            bpm = t_obj.get("bpm", "—")
            st.write(f"**BPM conseillé :** {bpm}")

            checklist = t_obj.get("checklist", [])
            if checklist:
                st.caption("Checklist (cocher = tu avances, c’est radical)")
                for i, item in enumerate(checklist, start=1):
                    st.checkbox(f"{i}. {item}", key=f"tpl_{active_name}_{i}")
            else:
                st.caption("Pas de checklist dans ce template.")
        else:
            st.caption("Template introuvable (nom différent ?)")

    st.markdown("</div>", unsafe_allow_html=True)

# ---- Card 3: Ajouter un template (cloud-safe) + download
with right_card:
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown('<div class="block-title">➕ Ajouter un template</div>', unsafe_allow_html=True)
    st.markdown('<div class="block-sub">Tu construis ta boîte à outils. Pas une cathédrale.</div>', unsafe_allow_html=True)

    with st.expander("Créer un nouveau template"):
        with st.form("add_template_form", clear_on_submit=True):
            name = st.text_input("Nom du template", placeholder="ex: Rap FR sombre — Starter")
            bpm = st.number_input("BPM conseillé", min_value=40, max_value=220, value=140, step=1)
            raw = st.text_area(
                "Checklist (1 ligne = 1 item)",
                placeholder="ex:\nChoisir tonalité mineur\nDrums kick/snare/hat\n808 simple\nHook 8 mesures\nBounce mp3",
                height=140,
            )
            add = st.form_submit_button("Ajouter")

        if add:
            if not name.strip():
                st.error("Il faut un nom.")
            else:
                checklist = [line.strip() for line in raw.splitlines() if line.strip()]
                new_t = {"name": name.strip(), "bpm": int(bpm), "checklist": checklist}
                st.session_state.templates_local.append(new_t)
                st.session_state.active_template_name = new_t["name"]
                st.success("Template ajouté (en mémoire). Télécharge le JSON pour le garder.")

    # Download des templates (pour persistance cloud)
    export_templates = json.dumps(st.session_state.templates_local, ensure_ascii=False, indent=2)
    st.download_button(
        "📥 Télécharger templates.json",
        data=export_templates.encode("utf-8"),
        file_name="templates.json",
        mime="application/json",
        use_container_width=True,
    )
    st.caption("Astuce : remplace `data/templates.json` par ce fichier, commit/push, et c’est permanent.")

    st.markdown("</div>", unsafe_allow_html=True)


st.divider()

# -------------------- MAIN PAGE (2 COLS) --------------------
left, right = st.columns([1.35, 1])

# ----- LEFT : Focus du jour détaillé + Journal quick add -----
with left:
    st.subheader("🧭 Focus du jour (détaillé)")

    if prioritized_styles:
        final_style_name = st.session_state.style_pick or prioritized_styles[0]
        style_obj = get_style_obj(final_style_name)

        if style_obj:
            bpm = style_obj.get("bpm", [])
            mood = style_obj.get("mood", [])
            contraintes = style_obj.get("contraintes", [])
            refs = style_obj.get("refs", [])

            st.write(f"**Style :** {style_obj.get('style')}")
            if bpm:
                st.write(f"**BPM :** {bpm[0]}–{bpm[1]}" if isinstance(bpm, list) and len(bpm) == 2 else f"**BPM :** {bpm}")
            if mood:
                st.write(f"**Mood :** {', '.join(mood)}")

            st.markdown("**Contraintes (mini-brief)**")
            if contraintes:
                for i, c in enumerate(contraintes, start=1):
                    st.checkbox(f"{i}. {c}", key=f"contraintes_{final_style_name}_{i}")
            else:
                st.caption("Ajoute `contraintes` dans styles.json.")

            with st.expander("🎧 Références"):
                if refs:
                    for r in refs:
                        st.write(f"- {r}")
                else:
                    st.caption("Ajoute `refs` (3 titres suffisent).")

            st.markdown("### ✅ Plan express (45–90 min)")
            st.write("1) 10 min : choisir 1 son / 1 patch / 1 vibe")
            st.write("2) 25 min : loop A (drums + harmonie OU drums + bass)")
            st.write("3) 25 min : variation B (même idée, plus d’énergie ou moins)")
            st.write("4) 10 min : bounce mp3 + note 3 améliorations")
        else:
            st.info("Style non trouvé (vérifie styles.json).")
    else:
        st.info("Ajoute des styles dans `data/styles.json` pour activer le focus du jour.")

    st.divider()

    st.subheader("📝 Ajout rapide au journal (preuve que l’app vit)")

    # Préremplissage intelligent
    default_style = st.session_state.style_pick or (prioritized_styles[0] if prioritized_styles else "")
    default_template = st.session_state.active_template_name or ""

    with st.form("quick_journal", clear_on_submit=True):
        titre = st.text_input("Titre du projet", placeholder="ex: NOCTURNE_140BPM_v1")
        style = st.text_input("Style", value=default_style)
        etat = st.selectbox("État", ETATS, index=1)
        temps_min = st.number_input("Temps (min)", min_value=0, max_value=600, value=60, step=5)
        objectif_du_jour = st.text_input("Objectif du jour", placeholder="ex: loop + variation + bounce")
        apprentissage = st.text_input("Ce que tu as appris", placeholder="ex: hats trop chargés → simplifier")
        next_step = st.text_input("Prochaine étape", placeholder="ex: hook + prise voix test")
        score = st.slider("Score 'montrable' (0–5)", 0, 5, 2)
        lien_audio = st.text_input("Lien audio (optionnel)", placeholder="Drive/SoundCloud/local path…")

        if default_template:
            st.caption(f"Template actif : **{default_template}** (pratique pour retrouver ta méthode)")

        submitted = st.form_submit_button("Ajouter au journal")

    if submitted:
        if not titre.strip():
            st.error("Donne au moins un titre (même moche).")
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
            st.success("Ajouté ✅ (sur Streamlit Cloud, exporte le CSV régulièrement).")

    export_df = df_journal.drop(columns=["date_parsed"], errors="ignore")
    st.download_button(
        "📥 Télécharger le journal (CSV)",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name="journal.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ----- RIGHT : stats + dernières entrées + raccourcis -----
with right:
    st.subheader("📈 Stats rapides")

    total = len(df_journal)
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    last7 = df_journal[df_journal["date_parsed"] >= week_ago] if total else df_journal.iloc[0:0]
    mins_last7 = sum(safe_int(x, 0) for x in last7.get("temps_min", []).tolist()) if len(last7) else 0

    a, b = st.columns(2)
    with a:
        st.metric("Projets trackés", total)
    with b:
        st.metric("Temps 7 jours (min)", mins_last7)

    st.markdown("**Répartition par état**")
    if total:
        counts = df_journal["etat"].value_counts(dropna=False).to_dict()
        for k in ETATS:
            st.write(f"- {k} : {counts.get(k, 0)}")
    else:
        st.caption("Aucune entrée pour l’instant.")

    st.divider()

    st.subheader("🗂️ Dernières entrées")
    if total:
        show = df_journal.sort_values("date_parsed", ascending=False, na_position="last").head(8)
        cols_show = ["date", "titre", "style", "etat", "temps_min", "score_monstrable"]
        cols_show = [c for c in cols_show if c in show.columns]
        st.dataframe(show[cols_show], use_container_width=True, hide_index=True)
    else:
        st.info("Ajoute 2–3 entrées via le formulaire : ça allume le dashboard.")

    st.divider()

    st.subheader("🧩 Raccourcis")
    st.markdown(
        """
- **Profil & Boussole** : objectifs + règles (anti-dispersion)
- **Styles & Références** : bibliothèque + contraintes
- **Production/Templates** : tes checklists “anti-page blanche”
- **Journal** : suivi + preuve de progression
"""
    )
