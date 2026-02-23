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
    # Données initiales (structure de référence)
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

# Noms des colonnes clés pour cohérence dans tout le code
c_insee = "Code commune Insee"
c_nom = "Nom du Comité Local Pour l'Emploi"
new_col = "Nouveau Nom du Comité Local Pour l'Emploi"

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
    st.info("💡 Ces filtres impactent la vue 'Visualisation' et l'export CSV.")
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
    st.markdown(f"""
    **Étape 1 :** Exportez la table actuelle (en bas de page) avec au moins les colonnes `{c_insee}` et `{c_nom}`.  
    **Étape 2 :** Modifiez les noms dans votre tableur (Excel).  
    **Étape 3 :** Déposez le fichier modifié ci-dessous.  
    **Étape 4 :** Cliquez sur le bouton bleu **'Ajoute un Nouveau Nom...'**. Cela crée une colonne de test.  
    **Étape 5 :** L'administrateur valide ensuite le remplacement définitif en bas de page.
    """)

uploaded_file = st.file_uploader("Déposer le CSV de mise à jour (Séparateur ';' ou ',')", type="csv")

if uploaded_file:
    try:
        df_up = pd.read_csv(uploaded_file, sep=None, engine='python', dtype={c_insee: str}, encoding='utf-8-sig')
        df_up.columns = df_up.columns.str.strip()

        if c_insee in df_up.columns and c_nom in df_up.columns:
            st.success(f"✅ Fichier conforme : {len(df_up)} lignes détectées.")
            
            if st.button(f"🔄 Ajoute un {new_col}"):
                # Nettoyage si une version précédente existe
                if new_col in st.session_state.df_main.columns:
                    st.session_state.df_main.drop(columns=[new_col], inplace=True)
                
                # Fusion (Left Join)
                st.session_state.df_main = st.session_state.df_main.merge(
                    df_up[[c_insee, c_nom]], on=c_insee, how='left', suffixes=('', '_nouveau')
                )
                st.session_state.df_main.rename(columns={f"{c_nom}_nouveau": new_col}, inplace=True)
                st.session_state.df_main[new_col] = st.session_state.df_main[new_col].fillna("")
                
                st.warning(f"🔔 **Données en attente** : La table a été mise à jour avec la variable `{new_col}`. Un administrateur doit maintenant valider le remplacement définitif.")
                st.rerun()
        else:
            st.error(f"❌ Colonnes attendues non trouvées. Vérifiez que votre fichier contient bien : '{c_insee}' et '{c_nom}'.")
    except Exception as e:
        st.error(f"⚠️ Erreur lors de la lecture : {e}")

# --- 5. VISUALISATION ET ÉDITION ---
st.divider()

if is_admin:
    st.subheader("✍️ Zone d'Édition Directe (Admin)")
    st.info("📝 Mode Admin : Vous pouvez modifier les noms directement dans le tableau. Pensez à 'Enregistrer les modifications manuelles'.")
    
    # Alerte spécifique si une fusion CSV est en attente
    if new_col in st.session_state.df_main.columns:
        st.error(f"📢 **IMPORT EN ATTENTE** : Une colonne `{new_col}` est présente. Voulez-vous remplacer officiellement les anciens noms ?")

    # Éditeur de données
    edited_df = st.data_editor(st.session_state.df_main, use_container_width=True, num_rows="dynamic")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💾 Enregistrer les modifications manuelles"):
            st.session_state.df_main = edited_df
            st.success("Modifications enregistrées en base.")
            st.rerun()
    with col_b:
        if new_col in st.session_state.df_main.columns:
            if st.button("✅ Valider définitivement le remplacement des noms"):
                # Masque pour ne remplacer que là où on a fourni un nouveau nom
                mask = st.session_state.df_main[new_col] != ""
                st.session_state.df_main.loc[mask, c_nom] = st.session_state.df_main[new_col]
                # On supprime la colonne temporaire
                st.session_state.df_main.drop(columns=[new_col], inplace=True)
                st.balloons()
                st.success("Mise à jour officielle terminée.")
                st.rerun()
else:
    st.subheader("📊 Visualisation des données")
    st.info("💡 Consultez le référentiel ci-dessous. Pour toute modification, connectez-vous via la barre latérale.")
    st.dataframe(df_display, use_container_width=True)

# --- 6. EXPORTATION ---
st.divider()
st.subheader("📥 Exportation")
with st.expander("ℹ️ Aide à l'export"):
    st.write("Le fichier CSV généré utilise le point-virgule (;) comme séparateur pour une compatibilité parfaite avec Excel France.")

all_cols = df_display.columns.tolist()
# Présélection intelligente
default_export = [c_insee, c_nom]
if new_col in all_cols:
    default_export.append(new_col)

export_sel = st.multiselect(
    "Sélectionnez les colonnes à exporter :", 
    options=all_cols, 
    default=[c for c in default_export if c in all_cols],
    help="Les colonnes nécessaires au ré-import sont cochées par défaut."
)

if export_sel:
    # Message de prévention
    if c_insee not in export_sel:
        st.warning(f"⚠️ N'oubliez pas d'inclure '{c_insee}' si vous prévoyez de ré-importer ce fichier plus tard.")
        
    csv = df_display[export_sel].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label=f"📥 Télécharger le CSV ({len(df_display)} lignes)", 
        data=csv, 
        file_name="referentiel_clpe_export.csv", 
        mime="text/csv"
    )
