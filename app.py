import streamlit as st
import pandas as pd
import re

# CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Référentiel CLPE - Gestion", 
    layout="wide", 
    page_icon="📍"
)

# --- CONSTANTES ---
c_insee = "Code commune Insee"
c_nom = "Nom du Comité Local Pour l'Emploi"
new_col = "Nouveau Nom du Comité Local Pour l'Emploi"
c_contact = "Contact"

# --- 1. INITIALISATION DES DONNÉES (SESSION STATE) ---
if 'df_main' not in st.session_state:
    data = {
        "Code Région": ["11", "24", "44", "32"],
        "Libellé Région": ["Île-de-France", "Centre-Val de Loire", "Grand Est", "Hauts-de-France"],
        "Code Département": ["075", "028", "067", "059"],
        "Libellé Département": ["Paris", "Eure-et-Loir", "Bas-Rhin", "Nord"],
        c_insee: ["75001", "28001", "67001", "59001"],
        "Code du Comité Local Pour l'Emploi": ["CLE-7501", "CLE-2801", "CLE-6701", "CLE-5901"],
        c_nom: ["Comité Paris Centre", "Comité Chartres", "Comité Strasbourg", "Comité Lille"],
        # Les colonnes de suivi sont initialisées à vide pour être toujours visibles
        new_col: ["", "", "", ""],
        c_contact: ["", "", "", ""]
    }
    st.session_state.df_main = pd.DataFrame(data)

# État de connexion Admin
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 2. BARRE LATÉRALE (CONNEXION & FILTRES) ---
regions, depts = [], []

with st.sidebar:
    st.title("⚙️ Configuration")
    st.header("🔐 Administration")
    
    if not st.session_state.authenticated:
        admin_code = st.text_input("Code Administrateur", type="password", help="Saisissez RPE_REFCLPE")
        if st.button("Se connecter"):
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
    regions = st.multiselect("Filtrer par Région", options=sorted(st.session_state.df_main["Libellé Région"].dropna().unique()))
    depts = st.multiselect("Filtrer par Département", options=sorted(st.session_state.df_main["Libellé Département"].dropna().unique()))

# --- 3. LOGIQUE DE FILTRAGE ---
df_display = st.session_state.df_main.copy()
if regions:
    df_display = df_display[df_display["Libellé Région"].isin(regions)]
if depts:
    df_display = df_display[df_display["Libellé Département"].isin(depts)]

# --- 4. SECTION UPLOAD ---
st.title("📍 Gestion du Référentiel CLPE")
st.markdown("---")
st.subheader("📥 Mise à jour via fichier CSV")

with st.expander("❓ Guide : Comment effectuer une mise à jour de masse ?"):
    st.markdown(f"""
    **Étape 1 :** Exportez la table actuelle en utilisant les colonnes `{c_insee}` et `{c_nom}`.  
    **Étape 2 :** Modifiez les noms. *(Note : Seul l'administrateur peut ajouter de nouveaux codes INSEE).* **Étape 3 :** Renseignez votre e-mail et déposez le fichier.  
    **Étape 4 :** Cliquez sur **Ajoute un Nouveau Nom...**. Les modifications seront visibles par tous.  
    **Étape 5 :** L'administrateur valide ensuite le remplacement définitif.
    """)

uploaded_file = st.file_uploader("Déposer le CSV de mise à jour (Séparateur ';' ou ',')", type="csv")

if uploaded_file:
    try:
        df_up = pd.read_csv(uploaded_file, sep=None, engine='python', dtype={c_insee: str}, encoding='utf-8-sig')
        df_up.columns = df_up.columns.str.strip()

        if c_insee in df_up.columns and c_nom in df_up.columns:
            st.success(f"✅ Fichier lu avec succès : {len(df_up)} lignes détectées.")
            
            # Champ Email obligatoire
            st.markdown("#### 👤 Identification requise")
            contact_mail = st.text_input("Veuillez saisir votre adresse e-mail pour soumettre ces modifications :")
            
            email_ok = False
            if contact_mail:
                # Vérification regex du format email
                if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact_mail):
                    email_ok = True
                else:
                    st.error("⚠️ Le format de l'e-mail est invalide.")

            if email_ok:
                if st.button(f"🔄 Ajoute un {new_col}"):
                    
                    # Logique : l'admin peut ajouter des lignes (outer), l'utilisateur normal met à jour (left)
                    if not is_admin:
                        # On ne garde que les INSEE qui existent déjà dans la base
                        df_up = df_up[df_up[c_insee].isin(st.session_state.df_main[c_insee])]
                        merge_how = 'left'
                    else:
                        merge_how = 'outer'
                    
                    # Création d'un tableau temporaire (staging) avec les nouvelles données et l'email
                    df_staging = pd.DataFrame({
                        c_insee: df_up[c_insee],
                        new_col + "_staging": df_up[c_nom],
                        c_contact + "_staging": contact_mail
                    })
                    
                    # Fusion intelligente
                    merged = pd.merge(st.session_state.df_main, df_staging, on=c_insee, how=merge_how)
                    
                    # combine_first permet d'écraser la valeur existante par la nouvelle (si elle existe)
                    merged[new_col] = merged[new_col + "_staging"].combine_first(merged[new_col]).fillna("")
                    merged[c_contact] = merged[c_contact + "_staging"].combine_first(merged[c_contact]).fillna("")
                    
                    # Nettoyage des colonnes temporaires et des NaN (cas de nouvelles lignes)
                    merged.drop(columns=[new_col + "_staging", c_contact + "_staging"], inplace=True)
                    merged.fillna("", inplace=True)
                    
                    st.session_state.df_main = merged
                    
                    st.warning(f"🔔 **Demande enregistrée** : Les modifications de {contact_mail} sont visibles en attente de validation.")
                    st.rerun()
        else:
            st.error(f"❌ Colonnes manquantes. Votre fichier doit contenir : '{c_insee}' et '{c_nom}'.")
    except Exception as e:
        st.error(f"⚠️ Erreur de lecture : {e}")

# --- 5. VISUALISATION ET ÉDITION ---
st.divider()

# Vérification s'il y a des modifications en attente (une ligne a un email)
has_pending = (st.session_state.df_main[c_contact] != "").any()

if is_admin:
    st.subheader("✍️ Zone d'Édition Directe (Admin)")
    st.info("📝 Mode Admin : Éditez directement les cellules ou validez les imports en attente.")
    
    if has_pending:
        st.error(f"📢 **ACTION REQUISE** : Des modifications proposées par des utilisateurs sont en attente de validation.")

    edited_df = st.data_editor(st.session_state.df_main, use_container_width=True, num_rows="dynamic")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💾 Enregistrer les modifications manuelles"):
            st.session_state.df_main = edited_df
            st.success("Modifications enregistrées.")
            st.rerun()
    with col_b:
        if has_pending:
            if st.button("✅ Valider TOUTES les modifications en attente"):
                mask = st.session_state.df_main[new_col] != ""
                # Remplacement du nom officiel
                st.session_state.df_main.loc[mask, c_nom] = st.session_state.df_main.loc[mask, new_col]
                # On VIDE les colonnes de suivi au lieu de les supprimer
                st.session_state.df_main[new_col] = ""
                st.session_state.df_main[c_contact] = ""
                
                st.balloons()
                st.success("Base officielle mise à jour. Les colonnes de suivi ont été réinitialisées.")
                st.rerun()
else:
    st.subheader("📊 Visualisation des données")
    if has_pending:
        st.info("👀 **Information :** Des modifications sont actuellement en attente de validation par un administrateur (voir colonnes de droite).")
    st.dataframe(df_display, use_container_width=True)

# --- 6. EXPORTATION ---
st.divider()
st.subheader("📥 Exportation")

all_cols = df_display.columns.tolist()
# Présélection intelligente incluant les nouvelles colonnes
default_export = [c_insee, c_nom, new_col, c_contact]

export_sel = st.multiselect(
    "Sélectionnez les colonnes à exporter :", 
    options=all_cols, 
    default=[c for c in default_export if c in all_cols]
)

if export_sel:
    if c_insee not in export_sel:
        st.warning(f"⚠️ N'oubliez pas d'inclure '{c_insee}' si vous souhaitez ré-importer ce fichier.")
        
    csv = df_display[export_sel].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label=f"📥 Télécharger le CSV ({len(df_display)} lignes)", 
        data=csv, 
        file_name="referentiel_clpe_export.csv", 
        mime="text/csv"
    )
