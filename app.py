import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestion des CLE", layout="wide")

st.title("📍 Interface de gestion des Comités Locaux Pour l'Emploi")

# --- INITIALISATION DES DONNÉES ---
if 'df_main' not in st.session_state:
    # Création d'un jeu de données de test pour ne pas avoir une interface vide
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
st.info("Le fichier doit avoir 2 colonnes : 'Code commune Insee' et 'Nom du Comité Local Pour l'Emploi'")
uploaded_file = st.file_uploader("Choisir un fichier CSV", type="csv")

if uploaded_file:
    # Lecture en forçant le format texte pour les codes INSEE (évite de perdre le '0' au début)
    df_upload = pd.read_csv(uploaded_file, dtype={'Code commune Insee': str})
    
    if st.button("Appliquer la mise à jour"):
        # Fusion des données
        st.session_state.df_main = st.session_state.df_main.merge(
            df_upload[['Code commune Insee', 'Nom du Comité Local Pour l'Emploi']], 
            on='Code commune Insee', 
            how='left', 
            suffixes=('', '_nouveau')
        )
        # Renommage de la nouvelle colonne
        st.session_state.df_main.rename(
            columns={'Nom du Comité Local Pour l'Emploi_nouveau': 'Nouveau Nom du Comité Local Pour l'Emploi'}, 
            inplace=True
        )
        st.success("Mise à jour terminée avec succès !")

# --- FILTRAGE FINAL ---
df_display = st.session_state.df_main.copy()
if region_filter:
    df_display = df_display[df_display["Libellé Région"].isin(region_filter)]
if dept_filter:
    df_display = df_display[df_display["Libellé Département"].isin(dept_filter)]

# --- AFFICHAGE ET EXPORT ---
st.subheader("📊 Visualisation des données")
st.dataframe(df_display, use_container_width=True)

csv_export = df_display.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Exporter le résultat en CSV",
    data=csv_export,
    file_name='export_donnees_cle.csv',
    mime='text/csv',
)
