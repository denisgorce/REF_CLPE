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

# Petit guide d'aide pour l'utilisateur
with st.expander("❓ Guide : Comment préparer votre fichier ?"):
    st.write("""
    - Utilisez un fichier **CSV** (séparateur point-virgule ou virgule).
    - Le fichier doit contenir au moins ces deux colonnes exactement : 
      **'Code commune Insee'** et **'Nom du Comité Local Pour l'Emploi'**.
    - L'application fera correspondre les noms grâce au code INSEE.
    """)

uploaded_file = st.file_uploader("Choisir un fichier CSV pour la mise à jour", type="csv")

if uploaded_file:
    try:
        # 1. Lecture du fichier avec détection automatique
        df_upload = pd.read_csv(
            uploaded_file, 
            sep=None, 
            engine='python', 
            dtype={"Code commune Insee": str}, 
            encoding='utf-8-sig'
        )
        
        # Nettoyage des noms de colonnes (espaces superflus)
        df_upload.columns = df_upload.columns.str.strip()

        # Définition des noms de colonnes cibles
        col_insee = "Code commune Insee"
        col_nom = "Nom du Comité Local Pour l'Emploi"
        new_col_name = "Nouveau Nom du Comité Local Pour l'Emploi"

        # 2. Test de conformité des colonnes
        if col_insee in df_upload.columns and col_nom in df_upload.columns:
            st.success(f"✅ Fichier conforme ! {len(df_upload)} lignes prêtes pour la mise à jour.")
            
            # Aperçu des données pour rassurer l'utilisateur
            with st.expander("👁️ Aperçu des données détectées"):
                st.dataframe(df_upload[[col_insee, col_nom]].head(10))

            # 3. Bouton d'action pour déclencher la fusion
            if st.button("🚀 Lancer la mise à jour de la base"):
                
                # --- PROTECTION ANTI-DOUBLONS ---
                # Si la colonne de mise à jour existe déjà, on la supprime avant de recommencer
                if new_col_name in st.session_state.df_main.columns:
                    st.session_state.df_main = st.session_state.df_main.drop(columns=[new_col_name])
                
                # Fusion des données (Left Join)
                updated_df = st.session_state.df_main.merge(
                    df_upload[[col_insee, col_nom]], 
                    on=col_insee, 
                    how='left', 
                    suffixes=('', '_nouveau')
                )
                
                # Renommage et nettoyage des valeurs vides (NaN)
                updated_df.rename(columns={f"{col_nom}_nouveau": new_col_name}, inplace=True)
                updated_df[new_col_name] = updated_df[new_col_name].fillna("")
                
                # Sauvegarde dans la mémoire de l'application
                st.session_state.df_main = updated_df
                
                # Feedback visuel final
                st.balloons()
                st.info(f"✨ Mise à jour terminée. La colonne '{new_col_name}' est maintenant disponible dans le tableau ci-dessous.")
        
        else:
            # Message d'erreur si les colonnes ne correspondent pas
            st.error("❌ Erreur de format : Colonnes obligatoires introuvables.")
            st.markdown(f"""
            L'application a trouvé les colonnes suivantes : `{list(df_upload.columns)}`  
            Veuillez renommer vos colonnes en :  
            - **{col_insee}** - **{col_nom}**
            """)
            
    except Exception as e:
        st.error(f"⚠️ Une erreur technique est survenue lors de la lecture : {e}")
        

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
