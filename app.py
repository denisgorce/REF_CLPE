import streamlit as st
import pandas as pd

# CONFIGURATION
st.set_page_config(page_title="Référentiel CLPE", layout="wide")

# --- 1. INITIALISATION DES DONNÉES ---
if 'df_main' not in st.session_state:
    data = {
        "Code Région": ["11", "24", "44", "32"],
        "Libellé Région": ["Île-de-France", "Centre-Val de Loire", "Grand Est", "Hauts-de-France"],
        "Code Département": ["075", "028", "067", "059"],
        "Libellé Département": ["Paris", "Eure-et-Loir", "Bas-Rhin", "Nord"],
        "Code commune Insee": ["75001", "28001", "67001", "59001"],
        "Nom du Comité Local Pour l'Emploi": ["Comité Paris Centre", "Comité Chartres", "Comité Strasbourg", "Comité Lille"]
    }
    st.session_state.df_main = pd.DataFrame(data)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 2. BARRE LATÉRALE (Filtres & Connexion) ---
regions = []
depts = []

with st.sidebar:
    st.header("🔐 Administration")
    if not st.session_state.authenticated:
        admin_code = st.text_input("Code Administrateur", type="password")
        if st.button("Connexion"):
            if admin_code == "RPE_REFCLPE":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Code incorrect")
    else:
        st.success("🔓 Mode Admin activé")
        if st.button("🚪 Se déconnecter"):
            st.session_state.authenticated = False
            st.rerun()

    is_admin = st.session_state.authenticated

    st.divider()
    st.header("🔍 Filtres d'affichage")
    regions = st.multiselect("Filtrer par Région", options=sorted(st.session_state.df_main["Libellé Région"].unique()))
    depts = st.multiselect("Filtrer par Département", options=sorted(st.session_state.df_main["Libellé Département"].unique()))

# --- 3. CALCUL DU TABLEAU FILTRÉ ---
df_display = st.session_state.df_main.copy()
if regions:
    df_display = df_display[df_display["Libellé Région"].isin(regions)]
if depts:
    df_display = df_display[df_display["Libellé Département"].isin(depts)]

# --- 4. SECTION UPLOAD (VISIBLE PAR TOUS) ---
st.title("📍 Gestion du Référentiel CLPE")
st.subheader("📥 Mise à jour par fichier CSV")
with st.expander("💡 Aide : Comment procéder ?"):
    st.write("Exportez les colonnes INSEE et Nom, modifiez-les, puis uploadez le fichier ici.")

uploaded_file = st.file_uploader("Choisir un fichier CSV", type="csv")
if uploaded_file:
    try:
        df_up = pd.read_csv(uploaded_file, sep=None, engine='python', dtype={"Code commune Insee": str}, encoding='utf-8-sig')
        df_up.columns = df_up.columns.str.strip()
        c_insee, c_nom = "Code commune Insee", "Nom du Comité Local Pour l'Emploi"
        new_col = "Nouveau Nom du Comité Local Pour l'Emploi"

        if c_insee in df_up.columns and c_nom in df_up.columns:
            st.success(f"✅ Fichier conforme ({len(df_up)} lignes).")
            if st.button("🔄 Préparer la fusion"):
                if new_col in st.session_state.df_main.columns:
                    st.session_state.df_main.drop(columns=[new_col], inplace=True)
                st.session_state.df_main = st.session_state.df_main.merge(df_up[[c_insee, c_nom]], on=c_insee, how='left', suffixes=('', '_nouveau'))
                st.session_state.df_main.rename(columns={f"{c_nom}_nouveau": new_col}, inplace=True)
                st.session_state.df_main[new_col] = st.session_state.df_main[new_col].fillna("")
                st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# --- 5. ZONE D'ÉDITION OU VISUALISATION ---
st.divider()
if is_admin:
    st.subheader("✍️ Édition Directe (Admin)")
    edited_df = st.data_editor(st.session_state.df_main, use_container_width=True, num_rows="dynamic")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Enregistrer les modifications manuelles"):
            st.session_state.df_main = edited_df
            st.rerun()
    with c2:
        new_c = "Nouveau Nom du Comité Local Pour l'Emploi"
        if new_c in st.session_state.df_main.columns:
            if st.button("✅ Valider l'import CSV définitivement"):
                base_c = "Nom du Comité Local Pour l'Emploi"
                mask = st.session_state.df_main[new_c] != ""
                st.session_state.df_main.loc[mask, base_c] = st.session_state.df_main.loc[mask, new_c]
                st.session_state.df_main.drop(columns=[new_c], inplace=True)
                st.rerun()
else:
    st.subheader("📊 Visualisation des données")
    st.dataframe(df_display, use_container_width=True)

# --- 6. EXPORT ---
st.divider()
all_cols = df_display.columns.tolist()
export_sel = st.multiselect("Colonnes à exporter", options=all_cols, default=all_cols[:5])
if export_sel:
    csv = df_display[export_sel].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("📥 Télécharger l'export CSV", data=csv, file_name="export_clpe.csv")
