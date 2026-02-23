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
    # On ajoute sep=None et engine='python' pour qu'il détecte automatiquement si c'est une virgule ou un point-virgule
    df_upload = pd.read_csv(uploaded_file, sep=None, engine='python', dtype={"Code commune Insee": str})
       
    if st.button("Appliquer la mise à jour"):
        # Ce qui est ci-dessous est décalé de deux niveaux (8 espaces)
        st.session_state.df_main = st.session_state.df_main.merge(
            df_upload[["Code commune Insee", "Nom du Comité Local Pour l'Emploi"]], 
            on="Code commune Insee", 
            how="left", 
            suffixes=("", "_nouveau")
        )
        
        st.session_state.df_main.rename(
            columns={"Nom du Comité Local Pour l'Emploi_nouveau": "Nouveau Nom du Comité Local Pour l'Emploi"}, 
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
st.subheader("📊 Visualisation et Exportation")

# 1. Choix des colonnes à exporter
all_columns = df_display.columns.tolist()
default_export_cols = ["Code commune Insee", "Nom du Comité Local Pour l'Emploi"]

# On vérifie que les colonnes par défaut existent avant de les suggérer
suggested_cols = [c for c in default_export_cols if c in all_columns]

export_cols = st.multiselect(
    "Sélectionnez les variables à inclure dans l'export :",
    options=all_columns,
    default=suggested_cols
)

# 2. Affichage du tableau filtré par colonnes
if export_cols:
    st.dataframe(df_display[export_cols], use_container_width=True)

    # 3. Bouton d'exportation
    csv_export = df_display[export_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    
    # Message d'aide contextuel
    if set(default_export_cols).issubset(set(export_cols)):
        st.info("💡 Votre sélection inclut les colonnes nécessaires pour une mise à jour ultérieure.")
    else:
        st.warning("⚠️ Pour pouvoir ré-uploader ce fichier plus tard, assurez-vous d'inclure 'Code commune Insee' et 'Nom du Comité Local Pour l'Emploi'.")

    st.download_button(
        label=f"📥 Télécharger l'export ({len(export_cols)} colonnes)",
        data=csv_export,
        file_name='export_personnalise_cle.csv',
        mime='text/csv',
    )
else:
    st.warning("Veuillez sélectionner au moins une colonne pour visualiser et exporter les données.")
