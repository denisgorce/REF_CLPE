import streamlit as st
import pandas as pd

# CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Référentiel CLPE - Gestion", 
    layout="wide", 
    page_icon="📍"
)

# --- 1. INITIALISATION DES DONNÉES (SESSION STATE) ---
if 'df_main' not in st.session_state:
    data = {
        "Code Région": ["11", "24", "44", "32"],
        "Libellé Région": ["Île-de-France", "Centre-Val de Loire", "Grand Est", "Hauts-de-France"],
        "Code Département": ["075", "028", "067", "059"],
        "Libellé Département": ["Paris", "Eure-et-Loir", "Bas-Rhin", "Nord"],
        "Code commune Insee": ["75001", "28001", "67001", "59001"],
        "Code du Comité Local Pour l'Emploi": ["CLE-7501", "CLE-2801", "CLE-6701", "CLE-5901"],
        "Nom du Comité Local Pour l'Emploi": ["Comité Paris Centre", "Comité Chartres", "Comité Strasbourg", "Comité Lille"]
    }
    st.session_state.df_main = pd.DataFrame(data)

# État de connexion Admin (Interrupteur sécurisé)
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 2. BARRE LATÉRALE (CONNEXION & FILTRES) ---
regions = []
depts = []

with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Zone Admin
    st.header("🔐 Administration")
    if not st.session_state.authenticated:
        admin_code = st.text_input("Code Administrateur", type="password", help="Saisissez le code RPE_REFCLPE pour activer l'édition")
        if st.button("Se connecter"):
            if admin_code == "RPE_REFCLPE":
                st.session_state.authenticated = True
                st.success("Accès autorisé")
                st.rerun()
            else:
                st.error("Code incorrect")
    else:
        st.success("🔓 Mode Admin activé")
        if st.button("🚪 Se déconnecter du mode admin"):
            st.session_state.authenticated = False
            st.rerun()

    is_admin = st.session_state.authenticated

    st.divider()
    
    # Filtres
    st.header("🔍 Filtres d'affichage")
    st.info("💡 Ces filtres impactent uniquement la vue 'Visualisation' et l'export.")
    regions = st.multiselect(
        "Filtrer par Région", 
        options=sorted(st.session_state.df_main["Libellé Région"].unique())
    )
    depts = st.multiselect(
        "Filtrer par Département", 
        options=sorted(st.session_state.df_main["Libellé Département"].unique())
    )

# --- 3. LOGIQUE DE FILTRAGE ---
df_display = st.session_state.df_main.copy()
if regions:
    df_display = df_display[df_display["Libellé Région"].isin(regions)]
if depts:
    df_display = df_display[df_display["Libellé Département"].isin(depts)]

# --- 4. SECTION UPLOAD (MISE À JOUR MASSIVE) ---
st.title("📍 Gestion du Référentiel CLPE")
st.markdown("---")
st.subheader("📥 Mise à jour via fichier CSV")

# AIDE UTILISATEUR UPLOAD
with st.expander("❓ Guide : Comment effectuer une mise à jour de masse ?"):
    st.markdown("""
    **Étape 1 :** Exportez la table actuelle en utilisant les colonnes `Code commune Insee` et `Nom du Comité Local Pour l'Emploi`.  
    **Étape 2 :** Modifiez les noms dans votre tableur (Excel, LibreOffice).  
    **Étape 3 :** Déposez le fichier modifié ci-dessous.  
    **Étape 4 :** Cliquez sur **Préparer la fusion**. Une colonne de contrôle apparaîtra.  
    **Étape 5 :** Un administrateur devra ensuite valider définitivement les changements en bas de page.
    """)

uploaded_file = st.file_uploader("Déposer le CSV de mise à jour (Séparateur ';' ou ',')", type="csv")

if uploaded_file:
    try:
        df_up = pd.read_csv(uploaded_file, sep=None, engine='python', dtype={"Code commune Insee": str}, encoding='utf-8-sig')
        df_up.columns = df_up.columns.str.strip()
        
        c_insee, c_nom = "Code commune Insee", "Nom du Comité Local Pour l'Emploi"
        new_col = "Nouveau Nom du Comité Local Pour l'Emploi"

        if c_insee in df_up.columns and c_nom in df_up.columns:
            st.success(f"✅ Fichier conforme : {len(df_up)} lignes détectées.")
            
            if st.button("🔄 Préparer la fusion"):
                if new_col in st.session_state.df_main.columns:
                    st.session_state.df_main.drop(columns=[new_col], inplace=True)
                
                # Fusion (Left Join)
                st.session_state.df_main = st.session_state.df_main.merge(
                    df_up[[c_insee, c_nom]], on=c_insee, how='left', suffixes=('', '_nouveau')
                )
                st.session_state.df_main.rename(columns={f"{c_nom}_nouveau": new_col}, inplace=True)
                st.session_state.df_main[new_col] = st.session_state.df_main[new_col].fillna("")
                
                # Message d'étape crucial
                st.warning(f"🔔 **Données chargées** : Les modifications sont visibles dans la colonne `{new_col}`. Elles sont en attente de validation définitive par l'administrateur.")
                st.rerun()
        else:
            st.error(f"❌ Format invalide. Colonnes attendues : '{c_insee}' et '{c_nom}'.")
    except Exception as e:
        st.error(f"⚠️ Erreur lors de la lecture du fichier : {e}")

# --- 5. VISUALISATION ET ÉDITION ---
st.divider()
if is_admin:
    st.subheader("✍️ Zone d'Édition Directe (Admin)")
    st.info("📝 En mode Admin, vous pouvez modifier directement les valeurs dans les cellules du tableau. N'oubliez pas d'enregistrer vos modifications manuelles.")
    
    # Détection d'un import en attente
    new_c = "Nouveau Nom du Comité Local Pour l'Emploi"
    if new_c in st.session_state.df_main.columns:
        st.error(f"📢 **Action requise** : Un import CSV est en attente de validation pour la colonne `{new_c}`.")

    edited_df = st.data_editor(st.session_state.df_main, use_container_width=True, num_rows="dynamic")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💾 Enregistrer les modifications manuelles"):
            st.session_state.df_main = edited_df
            st.success("Les modifications manuelles ont été enregistrées en base.")
            st.rerun()
    with col_b:
        if new_c in st.session_state.df_main.columns:
            if st.button("✅ Valider l'import CSV (Écrasement définitif)"):
                base_c = "Nom du Comité Local Pour l'Emploi"
                mask = st.session_state.df_main[new_c] != ""
                st.session_state.df_main.loc[mask, base_c] = st.session_state.df_main.loc[mask, new_c]
                st.session_state.df_main.drop(columns=[new_c], inplace=True)
                st.balloons()
                st.success("La base officielle a été mise à jour avec les nouveaux noms.")
                st.rerun()
else:
    st.subheader("📊 Visualisation des données")
    st.info("💡 Utilisez la barre latérale pour filtrer les résultats. L'édition est réservée aux administrateurs.")
    st.dataframe(df_display, use_container_width=True)

# --- 6. EXPORTATION ---
st.divider()
st.subheader("📥 Exportation personnalisée")
with st.expander("ℹ️ Aide à l'export"):
    st.write("Le fichier généré est au format CSV (séparateur ';'), compatible avec Microsoft Excel.")

all_cols = df_display.columns.tolist()
# Présélection automatique des colonnes vitales
default_export = ["Code commune Insee", "Nom du Comité Local Pour l'Emploi"]
if "Nouveau Nom du Comité Local Pour l'Emploi" in all_cols:
    default_export.append("Nouveau Nom du Comité Local Pour l'Emploi")

export_sel = st.multiselect(
    "Sélectionnez les colonnes à exporter :", 
    options=all_cols, 
    default=[c for c in default_export if c in all_cols],
    help="Par défaut, les colonnes nécessaires à une future mise à jour sont cochées."
)

if export_sel:
    csv = df_display[export_sel].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label=f"📥 Télécharger le CSV ({len(df_display)} lignes)", 
        data=csv, 
        file_name="referentiel_clpe_export.csv", 
        mime="text/csv"
    )
