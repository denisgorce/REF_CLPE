import streamlit as st
import pandas as pd
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Référentiel CLPE - Gestion des évolutions", 
    layout="wide", 
    page_icon="📍"
)

# --- CSS POUR FORCER LE WRAP DES ENTÊTES ---
st.markdown("""
    <style>
        /* Force le texte des entêtes à passer à la ligne */
        div[data-testid="stTable"] th, 
        div[data-testid="stDataFrame"] th,
        .st-emotion-cache-18ni77z th {
            white-space: normal !important;
            word-wrap: break-word !important;
            line-height: 1.1 !important;
            height: auto !important;
            min-height: 50px;
            vertical-align: bottom;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES (STRICTEMENT RESPECTÉES) ---
C_INSEE = "Code commune Insee"
C_NOM_OFFICIEL = "Nom du Comité Local Pour l'Emploi"
C_NOUVEAU_NOM = "Nouveau Nom du Comité Local Pour l'Emploi"
C_CONTACT = "Contact"
C_REG_CODE = "Code Région"
C_REG_LIB = "Libellé Région"
C_DEPT_CODE = "Code Département"
C_DEPT_LIB = "Libellé Département"
C_CLE_CODE = "Code du Comité Local Pour l'Emploi"

# --- 1. INITIALISATION DES DONNÉES (SESSION STATE) ---
if 'df_main' not in st.session_state:
    data = {
        C_REG_CODE: ["11", "24", "44"],
        C_REG_LIB: ["Île-de-France", "Centre-Val de Loire", "Grand Est"],
        C_DEPT_CODE: ["075", "028", "067"],
        C_DEPT_LIB: ["Paris", "Eure-et-Loir", "Bas-Rhin"],
        C_INSEE: ["75001", "28001", "67001"],
        C_CLE_CODE: ["CLE-7501", "CLE-2801", "CLE-6701"],
        C_NOM_OFFICIEL: ["Comité Paris Centre", "Comité Chartres", "Comité Strasbourg"],
        C_NOUVEAU_NOM: ["", "", ""], 
        C_CONTACT: ["", "", ""]
    }
    st.session_state.df_main = pd.DataFrame(data)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 2. BARRE LATÉRALE (ADMIN & FILTRES PERSISTANTS) ---
with st.sidebar:
    st.header("🔐 Espace Administration")
    if not st.session_state.authenticated:
        pwd = st.text_input("Code Administrateur", type="password", help="Le mode admin permet d'ajouter des communes et de valider les noms.")
        if st.button("Connexion"):
            if pwd == "RPE_REFCLPE":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Code erroné")
    else:
        st.success("🔓 Mode Admin activé")
        if st.button("🚪 Déconnexion"):
            st.session_state.authenticated = False
            st.rerun()

    is_admin = st.session_state.authenticated
    st.divider()
    
    st.header("🔍 Filtres de recherche")
    f_reg = st.multiselect(C_REG_LIB, options=sorted(st.session_state.df_main[C_REG_LIB].unique()), key="perm_reg")
    f_dept = st.multiselect(C_DEPT_LIB, options=sorted(st.session_state.df_main[C_DEPT_LIB].unique()), key="perm_dept")
    
    contacts_list = sorted([c for c in st.session_state.df_main[C_CONTACT].unique() if c != ""])
    f_contact = st.multiselect("Filtrer par Contact (Auteur)", options=contacts_list, key="perm_contact")

# --- 3. LOGIQUE DE FILTRAGE ---
df_display = st.session_state.df_main.copy()
if f_reg:
    df_display = df_display[df_display[C_REG_LIB].isin(f_reg)]
if f_dept:
    df_display = df_display[df_display[C_DEPT_LIB].isin(f_dept)]
if f_contact:
    df_display = df_display[df_display[C_CONTACT].isin(f_contact)]

# --- 4. SECTION UPLOAD ---
st.title("📍 Référentiel des Comités Locaux Pour l'Emploi")
st.markdown("---")
st.subheader("📥 Proposer une modification de nom")

with st.expander("❓ Guide complet : Format du fichier et règles"):
    st.markdown(f"""
    **Structure du fichier CSV à importer :**
    - **Colonne 1** : Doit contenir le **{C_INSEE}**.
    - **Colonne 2** : Doit contenir le **{C_NOUVEAU_NOM}**.
    - *Note : Les noms des entêtes dans votre fichier n'ont pas d'importance, seul l'ordre compte.*
    
    **Effets de l'import :**
    - Vos propositions apparaîtront dans la colonne de suivi pour être validées par un administrateur.
    - Si le champ nom est vide dans votre fichier, la proposition sera enregistrée comme vide.
    - En mode **Admin**, l'import permet également d'ajouter de nouveaux codes INSEE à la base.
    """)

col_mail, col_file = st.columns([1, 2])
with col_mail:
    contact_mail = st.text_input("📧 Votre e-mail de contact (obligatoire) :", placeholder="prenom.nom@domaine.fr")
    email_valid = bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact_mail)) if contact_mail else False

with col_file:
    up_file = st.file_uploader("Choisir le fichier CSV", type="csv")

if up_file and email_valid:
    try:
        df_up = pd.read_csv(up_file, sep=None, engine='python', dtype=str, encoding='utf-8-sig')
        if len(df_up.columns) >= 2:
            df_up = df_up.iloc[:, [0, 1]].copy()
            df_up.columns = [C_INSEE, "tmp_name"]
            df_up["tmp_name"] = df_up["tmp_name"].fillna("")
            
            if st.button(f"🔄 Soumettre les nouveaux noms"):
                mode = 'outer' if is_admin else 'left'
                merged = pd.merge(st.session_state.df_main, df_up, on=C_INSEE, how=mode)
                
                # Appliquer la proposition sur les lignes concernées par l'upload
                mask = merged["tmp_name"].notna()
                merged.loc[mask, C_NOUVEAU_NOM] = merged.loc[mask, "tmp_name"]
                merged.loc[mask, C_CONTACT] = contact_mail
                
                merged.drop(columns=["tmp_name"], inplace=True)
                st.session_state.df_main = merged.fillna("")
                st.success("✅ Vos modifications ont été soumises avec succès.")
                st.rerun()
    except Exception as e:
        st.error(f"⚠️ Erreur lors du traitement du fichier : {e}")
elif up_file and not email_valid:
    st.warning("⚠️ Veuillez saisir une adresse e-mail valide pour pouvoir soumettre le fichier.")

# --- 5. VISUALISATION (ENTÊTES SUR 2 LIGNES + COMPACT) ---
st.divider()

# Configuration des colonnes pour un affichage sur deux lignes via \n
# Et masquage des colonnes codes pour éviter le scroll horizontal
view_config = {
    C_REG_CODE: None,
    C_DEPT_CODE: None,
    C_CLE_CODE: None,
    C_REG_LIB: st.column_config.TextColumn("Libellé\nRégion", width="small"),
    C_DEPT_LIB: st.column_config.TextColumn("Libellé\nDépartement", width="small"),
    C_INSEE: st.column_config.TextColumn("Code commune\nInsee", width="small"),
    C_NOM_OFFICIEL: st.column_config.TextColumn("Nom du Comité Local\nPour l'Emploi", width="medium"),
    C_NOUVEAU_NOM: st.column_config.TextColumn("Nouveau Nom du Comité\nLocal Pour l'Emploi", width="medium"),
    C_CONTACT: st.column_config.TextColumn("Contact\nE-mail", width="medium")
}

if is_admin:
    st.subheader("✍️ Zone d'Édition et de Validation (Administrateur)")
    f_edit = st.checkbox("Éditer uniquement la sélection filtrée", value=True)
    df_to_edit = df_display if f_edit else st.session_state.df_main

    # Éditeur de données
    edited_df = st.data_editor(df_to_edit, use_container_width=True, column_config=view_config, num_rows="dynamic")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Sauvegarder les saisies manuelles", use_container_width=True):
            st.session_state.df_main.update(edited_df)
            st.success("Modifications enregistrées.")
            st.rerun()
    with c2:
        if st.button("🗑️ Purger les propositions affichées", use_container_width=True):
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT]] = ""
            st.rerun()
    with c3:
        if st.button("✅ Valider et Écraser les noms", use_container_width=True, type="primary"):
            # Ne valide que les lignes affichées qui ont une proposition
            mask_v = (st.session_state.df_main.index.isin(df_display.index)) & (st.session_state.df_main[C_NOUVEAU_NOM] != "")
            st.session_state.df_main.loc[mask_v, C_NOM_OFFICIEL] = st.session_state.df_main.loc[mask_v, C_NOUVEAU_NOM]
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT]] = ""
            st.balloons()
            st.rerun()
else:
    st.subheader("📊 Consultation du Référentiel")
    st.dataframe(df_display, use_container_width=True, column_config=view_config)

# --- 6. EXPORTATION ---
st.divider()
st.subheader("📥 Exportation des données")

# Par défaut : uniquement Insee et Nom Officiel
exp_cols = st.multiselect(
    "Sélectionnez les colonnes pour l'export CSV :", 
    options=st.session_state.df_main.columns.tolist(),
    default=[C_INSEE, C_NOM_OFFICIEL]
)

if exp_cols:
    csv_data = df_display[exp_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label=f"⬇️ Télécharger le CSV ({len(df_display)} lignes)", 
        data=csv_data, 
        file_name="referentiel_clpe_export.csv", 
        mime="text/csv"
    )
