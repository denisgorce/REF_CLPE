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
    # Données de démonstration (à remplacer par votre import CSV initial si besoin)
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

# État de connexion Admin
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
        admin_code = st.text_input("Code Administrateur", type="password", help="Saisissez le code pour activer l'édition")
        if st.button("Se connecter"):
            if admin_code == "RPE_REFCLPE":
                st.session_state.authenticated = True
                st.success("Accès autorisé")
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
    
    # Filtres
    st.header("🔍 Filtres d'affichage")
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
with st.expander("❓ Comment mettre à jour les noms massivement ?"):
    st.markdown("""
    1. **Préparez votre fichier** : Il doit contenir les colonnes exactes `Code commune Insee` et `Nom du Comité Local Pour l'Emploi`.
    2. **Déposez le fichier** : Utilisez la zone ci-dessous.
    3. **Prévisualisez** : Cliquez sur 'Préparer la fusion' pour voir les changements sans écraser l'original.
    4. **Validez (Admin)** : Si vous êtes satisfait, utilisez le bouton de validation définitive en zone admin.
    """)

uploaded_file = st.file_uploader("Déposer le CSV de mise à jour", type="csv")

if uploaded_file:
    try:
        df_up = pd.read_csv(uploaded_file, sep=None, engine='python', dtype={"Code commune Insee": str}, encoding='utf-8-sig')
        df_up.columns = df_up.columns.str.strip()
        
        c_insee, c_nom = "Code commune Insee", "Nom du Comité Local Pour l'Emploi"
        new_col = "Nouveau Nom du Comité Local Pour l'Emploi"

        if c_insee in df_up.columns and c_nom in df_up.columns:
            st.success(f"✅ Fichier conforme : {len(df_up)} lignes détectées.")
            
            if st.button("🔄 Préparer la fusion (Prévisualisation)"):
                if new_col in st.session_state.df_main.columns:
                    st.session_state.df_main.drop(columns=[new_col], inplace=True)
                
                # Fusion
                st.session_state.df_main = st.session_state.df_main.merge(
                    df_up[[c_insee, c_nom]], on=c_insee, how='left', suffixes=('', '_nouveau')
                )
                st.session_state.df_main.rename(columns={f"{c_nom}_nouveau": new_col}, inplace=True)
                st.session_state.df_main[new_col] = st.session_state.df_main[new_col].fillna("")
                st.info("💡 Les nouveaux noms ont été ajoutés en fin de tableau pour vérification.")
                st.rerun()
        else:
            st.error(f"❌ Colonnes manquantes. Votre fichier contient : {list(df_up.columns)}")
    except Exception as e:
        st.error(f"⚠️ Erreur lors de la lecture du fichier : {e}")

# --- 5. VISUALISATION ET ÉDITION ---
st.divider()
if is_admin:
    st.subheader("✍️ Zone d'Édition Directe")
    st.info("☝️ En tant qu'administrateur, vous pouvez modifier les cellules directement dans le tableau ci-dessous.")
    
    edited_df = st.data_editor(st.session_state.df_main, use_container_width=True, num_rows="dynamic")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💾 Enregistrer les modifications manuelles"):
            st.session_state.df_main = edited_df
            st.success("Modifications enregistrées !")
            st.rerun()
    with col_b:
        if "Nouveau Nom du Comité Local Pour l'Emploi" in st.session_state.df_main.columns:
            if st.button("✅ Valider l'import CSV définitivement"):
                n_c, b_c = "Nouveau Nom du Comité Local Pour l'Emploi", "Nom du Comité Local Pour l'Emploi"
                mask = st.session_state.df_main[n_c] != ""
                st.session_state.df_main.loc[mask, b_c] = st.session_state.df_main.loc[mask, n_c]
                st.session_state.df_main.drop(columns=[n_c], inplace=True)
                st.balloons()
                st.rerun()
else:
    st.subheader("📊 Visualisation des données")
    st.info("💡 Utilisez les filtres en barre latérale pour affiner votre recherche.")
    st.dataframe(df_display, use_container_width=True)

# --- 6. EXPORTATION AVEC PRÉSÉLECTION ---
st.divider()
st.subheader("📥 Exportation")

all_cols = df_display.columns.tolist()
# Présélection par défaut (Insee + Nom)
default_export = ["Code commune Insee", "Nom du Comité Local Pour l'Emploi"]
if "Nouveau Nom du Comité Local Pour l'Emploi" in all_cols:
    default_export.append("Nouveau Nom du Comité Local Pour l'Emploi")

export_sel = st.multiselect(
    "Colonnes à inclure dans l'export :", 
    options=all_cols, 
    default=[c for c in default_export if c in all_cols]
)

if export_sel:
    csv = df_display[export_sel].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="⬇️ Télécharger le CSV", 
        data=csv, 
        file_name="referentiel_clpe.csv", 
        mime="text/csv",
        help="Format compatible Excel (UTF-8 avec BOM, séparateur point-virgule)"
    )
