import streamlit as st
import pandas as pd

st.set_page_config(page_title="Référentiel CLPE", layout="wide", initial_sidebar_state="expanded")

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

# --- 2. BARRE LATÉRALE (Filtres & Admin) ---
# INITIALISATION DES VARIABLES DE FILTRE (Pour éviter le NameError)
regions = []
depts = []

with st.sidebar:
    st.header("🔐 Administration")
    
    # Utilisation d'une clé pour le widget
    admin_code = st.text_input(
        "Code Administrateur", 
        type="password", 
        key="admin_input"
    )
    
    is_admin = (admin_code == "RPE_REFCLPE")
    
    if is_admin:
        st.success("🔓 Mode Admin activé")
        if st.button("🚪 Se déconnecter"):
            # Pour vider le champ, on réinitialise la clé dans le session_state
            st.session_state.admin_input = ""
            st.rerun()
    else:
        st.info("🔒 Mode Consultation")

    st.divider()
    st.header("🔍 Filtres d'affichage")
    
    # On assigne les valeurs aux variables déjà créées plus haut
    regions = st.multiselect(
        "Filtrer par Région", 
        options=sorted(st.session_state.df_main["Libellé Région"].unique())
    )
    depts = st.multiselect(
        "Filtrer par Département", 
        options=sorted(st.session_state.df_main["Libellé Département"].unique())
    )

# --- 3. CALCUL DU TABLEAU FILTRÉ ---
df_display = st.session_state.df_main.copy()
if regions:
    df_display = df_display[df_display["Libellé Région"].isin(regions)]
if depts:
    df_display = df_display[df_display["Libellé Département"].isin(depts)]
    

# --- 4. ZONE D'UPLOAD (Mise à jour massive) ---
st.subheader("📥 Mise à jour par fichier CSV")
with st.expander("💡 Aide : Comment procéder à une mise à jour ?"):
    st.markdown("""
    1. **Exportez** la liste actuelle en bas de page (colonnes Code INSEE et Nom obligatoires).
    2. **Modifiez** les noms dans Excel.
    3. **Déposez** le fichier ci-dessous.
    4. **Validez** en zone Administration (code requis).
    """)

uploaded_file = st.file_uploader("Glissez votre fichier ici", type="csv")

if uploaded_file:
    try:
        df_up = pd.read_csv(uploaded_file, sep=None, engine='python', dtype={"Code commune Insee": str}, encoding='utf-8-sig')
        df_up.columns = df_up.columns.str.strip()
        
        c_insee, c_nom = "Code commune Insee", "Nom du Comité Local Pour l'Emploi"
        new_col = "Nouveau Nom du Comité Local Pour l'Emploi"

        if c_insee in df_up.columns and c_nom in df_up.columns:
            st.success(f"✅ Fichier valide ({len(df_up)} communes détectées)")
            if st.button("🔄 Préparer la fusion (Prévisualisation)"):
                # Nettoyage d'une ancienne fusion
                if new_col in st.session_state.df_main.columns:
                    st.session_state.df_main.drop(columns=[new_col], inplace=True)
                
                # Fusion
                st.session_state.df_main = st.session_state.df_main.merge(
                    df_up[[c_insee, c_nom]], on=c_insee, how='left', suffixes=('', '_nouveau')
                )
                st.session_state.df_main.rename(columns={f"{c_nom}_nouveau": new_col}, inplace=True)
                st.session_state.df_main[new_col] = st.session_state.df_main[new_col].fillna("")
                st.rerun()
        else:
            st.error(f"Colonnes manquantes. Trouvées : {list(df_up.columns)}")
    except Exception as e:
        st.error(f"Erreur technique : {e}")

# --- 5. VISUALISATION ET ÉDITION ---
st.divider()
st.subheader("📊 Données et Modifications")

if is_admin:
    st.warning("✍️ Vous modifiez directement la base principale. N'oubliez pas d'enregistrer.")
    # Le data_editor permet de modifier les cellules comme dans Excel
    edited_df = st.data_editor(st.session_state.df_main, use_container_width=True, num_rows="dynamic")
    
    col_save, col_val = st.columns(2)
    with col_save:
        if st.button("💾 Enregistrer les modifications manuelles"):
            st.session_state.df_main = edited_df
            st.success("Base mise à jour !")
            st.rerun()
    
    with col_val:
        if "Nouveau Nom du Comité Local Pour l'Emploi" in st.session_state.df_main.columns:
            if st.button("✅ Appliquer définitivement l'import CSV"):
                n_col = "Nouveau Nom du Comité Local Pour l'Emploi"
                b_col = "Nom du Comité Local Pour l'Emploi"
                mask = st.session_state.df_main[n_col] != ""
                st.session_state.df_main.loc[mask, b_col] = st.session_state.df_main.loc[mask, n_col]
                st.session_state.df_main.drop(columns=[n_col], inplace=True)
                st.balloons()
                st.rerun()
else:
    # Vue utilisateur (lecture seule avec filtres)
    st.dataframe(df_display, use_container_width=True)

# --- 6. EXPORTATION ---
st.divider()
st.subheader("📥 Exportation des données")
all_cols = df_display.columns.tolist()
# Présélection des colonnes utiles pour un ré-import futur
default_cols = ["Code commune Insee", "Nom du Comité Local Pour l'Emploi"]
export_sel = st.multiselect("Choisir les colonnes à exporter", options=all_cols, default=[c for c in default_cols if c in all_cols])

if export_sel:
    csv_data = df_display[export_sel].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="⬇️ Télécharger le fichier CSV (Format Excel)",
        data=csv_data,
        file_name="referentiel_clpe_export.csv",
        mime="text/csv"
    )
