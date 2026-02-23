import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestion des CLE", layout="wide")

st.title("📍 Interface de gestion des Comités Locaux Pour l'Emploi")

# --- INITIALISATION DES DONNÉES ---
if 'df_main' not in st.session_state:
    data = {
        "Code Région": ["11", "24"],
        "Libellé Région": ["Île-de-France", "Centre-Val de Loire"],
        "Code Département": ["075", "028"],
        "Libellé Département": ["Paris", "Eure-et-Loir"],
        "Code commune Insee": ["75001", "28001"],
        "Code du Comité Local Pour l'Emploi": ["CLE-001", "CLE-002"],
        "Nom du Comité Local Pour l'Emploi": ["Comité Paris Centre", "Comité Chartres"]
    }
    st.session_state.df_main = pd.DataFrame(data)

# --- BARRE LATÉRALE : FILTRES ---
st.sidebar.header("🔍 Filtres")
region_filter = st.sidebar.multiselect("Filtrer par Région", options=st.session_state.df_main["Libellé Région"].unique())
dept_filter = st.sidebar.multiselect("Filtrer par Département", options=st.session_state.df_main["Libellé Département"].unique())

# --- SECTION UPLOAD ---
st.subheader("📥 Mise à jour via CSV")
with st.expander("❓ Comment mettre à jour les noms ?"):
    st.write("""
    1. **Exportez** les données en bas de page en cochant au minimum 'Code commune Insee' et 'Nom du Comité Local Pour l'Emploi'.
    2. **Ouvrez** le fichier dans Excel et modifiez les noms dans la colonne 'Nom du Comité Local Pour l'Emploi'.
    3. **Enregistrez** et **Uploadez** le fichier ici.
    """)

uploaded_file = st.file_uploader("Choisir un fichier CSV", type="csv")

if uploaded_file:
    try:
        df_upload = pd.read_csv(uploaded_file, sep=None, engine='python', dtype={"Code commune Insee": str}, encoding='utf-8-sig')
        df_upload.columns = df_upload.columns.str.strip()

        col1, col2 = "Code commune Insee", "Nom du Comité Local Pour l'Emploi"

        if col1 in df_upload.columns and col2 in df_upload.columns:
            st.success("✅ Fichier conforme !")
            if st.button("🚀 Appliquer la mise à jour des noms"):
                # --- ACTION CRUCIALE ICI ---
                # On crée le nouveau dataframe avec la fusion
                updated_df = st.session_state.df_main.merge(
                    df_upload[[col1, col2]], on=col1, how='left', suffixes=('', '_nouveau')
                )
                
                # On renomme la nouvelle colonne
                updated_df.rename(columns={f"{col2}_nouveau": "Nouveau Nom du Comité Local Pour l'Emploi"}, inplace=True)
                
                # ON MET À JOUR LA SESSION STATE (C'est ce qui permet au tableau du bas de voir le changement)
                st.session_state.df_main = updated_df
                
                st.balloons()
                st.success("Mise à jour effectuée ! Regardez le tableau ci-dessous.")
        else:
            st.error(f"Colonnes manquantes : {list(df_upload.columns)}")
    except Exception as e:
        st.error(f"Erreur : {e}")
    

# --- FILTRAGE FINAL ---
df_display = st.session_state.df_main.copy()
if region_filter:
    df_display = df_display[df_display["Libellé Région"].isin(region_filter)]
if dept_filter:
    df_display = df_display[df_display["Libellé Département"].isin(dept_filter)]

# --- AFFICHAGE ET EXPORT ---
st.divider()
st.subheader("📊 Visualisation et Exportation")

# 1. On récupère la liste de toutes les colonnes actuelles
all_columns = df_display.columns.tolist()

# 2. On définit les colonnes que l'on veut cocher par défaut pour l'export
key_cols = ["Code commune Insee", "Nom du Comité Local Pour l'Emploi"]
# On s'assure qu'elles existent dans le DataFrame avant de les proposer
default_cols = [c for c in key_cols if c in all_columns]

# 3. Le sélecteur pour l'export (pré-rempli avec les 2 colonnes clés)
export_selection = st.multiselect(
    "Quelles colonnes souhaitez-vous exporter ?",
    options=all_columns,
    default=default_cols,
    help="Par défaut, les colonnes nécessaires à la mise à jour sont sélectionnées."
)

# 4. AFFICHAGE VISUEL : On affiche TOUT le tableau pour le confort de l'utilisateur
st.write("Aperçu complet des données :")
st.dataframe(df_display, use_container_width=True)

# 5. LOGIQUE D'EXPORT : Uniquement les colonnes cochées dans le multiselect
if export_selection:
    csv_export = df_display[export_selection].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    
    st.download_button(
        label=f"📥 Télécharger l'export ({len(export_selection)} colonnes)",
        data=csv_export,
        file_name='export_cle_selection.csv',
        mime='text/csv',
    )
    
    # Message de rappel si l'utilisateur décoche les colonnes vitales
    if not set(key_cols).issubset(set(export_selection)):
        st.warning("⚠️ Attention : Votre sélection actuelle ne permet pas de réaliser une mise à jour par upload plus tard.")
else:
    st.info("Sélectionnez au moins une colonne ci-dessus pour activer le bouton de téléchargement.")
