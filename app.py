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
            st.success("✅ Fichier conforme ! Les colonnes ont été détectées.")
            if st.button("🚀 Appliquer la mise à jour des noms"):
                st.session_state.df_main = st.session_state.df_main.merge(
                    df_upload[[col1, col2]], on=col1, how='left', suffixes=('', '_nouveau')
                )
                st.session_state.df_main.rename(columns={f"{col2}_nouveau": f"Nouveau {col2}"}, inplace=True)
                st.balloons()
                st.success("Données fusionnées avec succès dans la nouvelle colonne !")
        else:
            st.error(f"❌ Colonnes manquantes. Votre fichier contient : {list(df_upload.columns)}")
            st.info(f"Le fichier doit contenir exactement : **{col1}** et **{col2}**")
    except Exception as e:
        st.error(f"Erreur lors de la lecture : {e}")

# --- FILTRAGE FINAL ---
df_display = st.session_state.df_main.copy()
if region_filter:
    df_display = df_display[df_display["Libellé Région"].isin(region_filter)]
if dept_filter:
    df_display = df_display[df_display["Libellé Département"].isin(dept_filter)]

# --- AFFICHAGE ET EXPORT ---
st.divider()
st.subheader("📊 Visualisation et Exportation")

all_columns = df_display.columns.tolist()
default_export_cols = ["Code commune Insee", "Nom du Comité Local Pour l'Emploi"]
suggested_cols = [c for c in default_export_cols if c in all_columns]

export_cols = st.multiselect("Sélectionnez les colonnes à exporter :", options=all_columns, default=suggested_cols)

if export_cols:
    # --- MESSAGE D'AIDE SUR L'EXPORT ---
    if set(default_export_cols).issubset(set(export_cols)):
        st.info("💡 **Sélection optimale** : Ce fichier pourra être ré-uploadé pour mise à jour.")
    else:
        st.warning("⚠️ **Attention** : Il manque des colonnes clés pour permettre une mise à jour future via ce fichier.")

    st.dataframe(df_display[export_cols], use_container_width=True)
    
    csv_export = df_display[export_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    
    st.download_button(
        label="📥 Télécharger le fichier pour Excel (Accents préservés)",
        data=csv_export,
        file_name='export_cle_france.csv',
        mime='text/csv',
    )
else:
    st.info("Veuillez sélectionner au moins une colonne pour afficher les données.")
