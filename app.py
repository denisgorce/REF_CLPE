import streamlit as st
import pandas as pd
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Référentiel CLPE - Gestion", 
    layout="wide", 
    page_icon="📍"
)

# --- CONSTANTES (NOMS DE CHAMPS ORIGINAUX) ---
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
        C_REG_CODE: ["11", "24", "44", "32"],
        C_REG_LIB: ["Île-de-France", "Centre-Val de Loire", "Grand Est", "Hauts-de-France"],
        C_DEPT_CODE: ["075", "028", "067", "059"],
        C_DEPT_LIB: ["Paris", "Eure-et-Loir", "Bas-Rhin", "Nord"],
        C_INSEE: ["75001", "28001", "67001", "59001"],
        C_CLE_CODE: ["CLE-7501", "CLE-2801", "CLE-6701", "CLE-5901"],
        C_NOM_OFFICIEL: ["Comité Paris Centre", "Comité Chartres", "Comité Strasbourg", "Comité Lille"],
        C_NOUVEAU_NOM: ["", "", "", ""], 
        C_CONTACT: ["", "", "", ""]
    }
    st.session_state.df_main = pd.DataFrame(data)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 2. BARRE LATÉRALE (CONNEXION & FILTRES PERSISTANTS) ---
with st.sidebar:
    st.header("🔐 Administration")
    if not st.session_state.authenticated:
        pwd = st.text_input("Code Administrateur", type="password", help="Saisissez le code pour activer les droits d'édition et de validation.")
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
    
    st.header("🔍 Filtres d'affichage")
    regions = st.multiselect(C_REG_LIB, options=sorted(st.session_state.df_main[C_REG_LIB].unique()), key="f_reg_key")
    depts = st.multiselect(C_DEPT_LIB, options=sorted(st.session_state.df_main[C_DEPT_LIB].unique()), key="f_dept_key")
    
    contacts_dispo = sorted([c for c in st.session_state.df_main[C_CONTACT].unique() if c != ""])
    contact_filter = st.multiselect("Filtrer par Contact (Auteur)", options=contacts_dispo, key="f_contact_key")

# --- 3. LOGIQUE DE FILTRAGE ---
df_display = st.session_state.df_main.copy()
if regions:
    df_display = df_display[df_display[C_REG_LIB].isin(regions)]
if depts:
    df_display = df_display[df_display[C_DEPT_LIB].isin(depts)]
if contact_filter:
    df_display = df_display[df_display[C_CONTACT].isin(contact_filter)]

# --- 4. SECTION UPLOAD ---
st.title("📍 Gestion du Référentiel CLPE")
st.markdown("---")
st.subheader("📥 Soumettre une évolution")

# AIDE CONTEXTUELLE RÉTABLIE
with st.expander("❓ Guide : Comment effectuer une mise à jour ?"):
    st.markdown(f"""
    **Fichier CSV attendu :**
    - **Colonne 1** : {C_INSEE}
    - **Colonne 2** : {C_NOUVEAU_NOM}
    - *Les intitulés des colonnes dans votre fichier n'ont pas d'importance, l'ordre prévaut.*
    
    **Règles de gestion :**
    - Si le champ dans votre fichier est **vide**, la proposition sera affichée comme vide dans le tableau.
    - L'administrateur peut importer de nouveaux codes Insee non présents en base.
    """)

col_mail, col_file = st.columns([1, 2])
with col_mail:
    contact_mail = st.text_input("📧 Votre e-mail de contact (obligatoire) :", placeholder="jean.dupont@exemple.fr")
    email_valid = bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact_mail)) if contact_mail else False

with col_file:
    up_file = st.file_uploader("Charger le fichier CSV de mise à jour", type="csv")

if up_file and email_valid:
    try:
        df_up = pd.read_csv(up_file, sep=None, engine='python', dtype=str, encoding='utf-8-sig')
        if len(df_up.columns) >= 2:
            df_up = df_up.iloc[:, [0, 1]].copy()
            df_up.columns = [C_INSEE, "tmp_name"]
            df_up["tmp_name"] = df_up["tmp_name"].fillna("")
            
            if st.button(f"🔄 Appliquer en tant que '{C_NOUVEAU_NOM}'"):
                mode = 'outer' if is_admin else 'left'
                merged = pd.merge(st.session_state.df_main, df_up, on=C_INSEE, how=mode)
                
                # Identification de la source du changement
                mask = merged["tmp_name"].notna()
                merged.loc[mask, C_NOUVEAU_NOM] = merged.loc[mask, "tmp_name"]
                merged.loc[mask, C_CONTACT] = contact_mail
                
                merged.drop(columns=["tmp_name"], inplace=True)
                merged.fillna("", inplace=True)
                st.session_state.df_main = merged
                st.success("✅ Vos propositions ont été ajoutées au tableau ci-dessous.")
                st.rerun()
    except Exception as e:
        st.error(f"⚠️ Erreur lors de la lecture du fichier : {e}")
elif up_file and not email_valid:
    st.info("ℹ️ Veuillez renseigner un e-mail valide pour débloquer l'application du fichier.")

# --- 5. VISUALISATION (VERSION COMPACTE SANS SCROLL) ---
st.divider()

# Configuration pour masquer le superflu technique et ajuster les largeurs
view_config = {
    C_REG_CODE: None, 
    C_DEPT_CODE: None, 
    C_CLE_CODE: None,
    C_REG_LIB: st.column_config.TextColumn(width="small"),
    C_DEPT_LIB: st.column_config.TextColumn(width="small"),
    C_INSEE: st.column_config.TextColumn(width="small"),
    C_NOM_OFFICIEL: st.column_config.TextColumn(width="medium"),
    C_NOUVEAU_NOM: st.column_config.TextColumn(width="medium"),
    C_CONTACT: st.column_config.TextColumn(width="small")
}



if is_admin:
    st.subheader("✍️ Zone d'Édition et Validation (Administration)")
    edit_filtered = st.checkbox("Éditer uniquement la sélection filtrée", value=True, help="Si décoché, vous éditerez l'intégralité de la base de données.")
    
    df_to_edit = df_display if edit_filtered else st.session_state.df_main
    edited_df = st.data_editor(df_to_edit, use_container_width=True, column_config=view_config, num_rows="dynamic")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Sauvegarder les saisies", use_container_width=True):
            st.session_state.df_main.update(edited_df)
            st.success("Modifications manuelles enregistrées.")
            st.rerun()
    with c2:
        if st.button("🗑️ Purger les propositions", use_container_width=True, help="Efface les propositions et contacts pour la sélection actuelle."):
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT]] = ""
            st.rerun()
    with c3:
        if st.button("✅ Valider et Écraser", use_container_width=True, type="primary", help="Remplace le nom officiel par la proposition pour les lignes filtrées."):
            mask_val = (st.session_state.df_main.index.isin(df_display.index)) & (st.session_state.df_main[C_NOUVEAU_NOM] != "")
            st.session_state.df_main.loc[mask_val, C_NOM_OFFICIEL] = st.session_state.df_main.loc[mask_val, C_NOUVEAU_NOM]
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT]] = ""
            st.balloons()
            st.rerun()
else:
    st.subheader("📊 Visualisation du Référentiel")
    st.info("💡 Les modifications en attente sont visibles dans les deux colonnes de droite.")
    st.dataframe(df_display, use_container_width=True, column_config=view_config)

# --- 6. EXPORTATION ---
st.divider()
st.subheader("📥 Exportation des données")
with st.expander("ℹ️ Aide à l'export"):
    st.write("Le fichier CSV utilise le point-virgule (;) comme séparateur pour Excel.")

all_cols = st.session_state.df_main.columns.tolist()
default_export = [C_INSEE, C_NOM_OFFICIEL]

sel_cols = st.multiselect("Sélectionnez les colonnes à exporter :", 
                          options=all_cols, 
                          default=default_export,
                          help=f"Par défaut, seuls le code INSEE et le nom officiel sont sélectionnés.")

if sel_cols:
    csv_data = df_display[sel_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label=f"📥 Télécharger le CSV ({len(df_display)} lignes)", 
        data=csv_data, 
        file_name="referentiel_clpe.csv", 
        mime="text/csv"
    )
