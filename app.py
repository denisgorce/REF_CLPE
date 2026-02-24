import streamlit as st
import pandas as pd
import re
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Référentiel CLPE", layout="wide", page_icon="📍")

# --- CSS POUR LES ENTÊTES SUR 2 LIGNES ---
st.markdown("""
    <style>
        div[data-testid="stDataFrame"] th {
            white-space: normal !important;
            word-wrap: break-word !important;
            line-height: 1.1 !important;
            height: auto !important;
            min-height: 60px;
            vertical-align: bottom;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES ---
C_INSEE = "Code commune Insee"
C_NOM_OFFICIEL = "Nom du Comité Local Pour l'Emploi"
C_NOUVEAU_NOM = "Nouveau Nom du Comité Local Pour l'Emploi"
C_CONTACT = "Contact"
C_DATE_MAJ_ADMIN = "Date de mise à jour admin"
C_DATE_DEMANDE = "Date de la demande de mise à jour"
# Colonnes techniques
C_REG_CODE = "Code Région"
C_REG_LIB = "Libellé Région"
C_DEPT_CODE = "Code Département"
C_DEPT_LIB = "Libellé Département"
C_CLE_CODE = "Code du Comité Local Pour l'Emploi"

# --- 1. INITIALISATION ---
if 'df_main' not in st.session_state:
    st.session_state.df_main = pd.DataFrame({
        C_REG_CODE: ["11", "24"], C_REG_LIB: ["Île-de-France", "Centre-Val de Loire"],
        C_DEPT_CODE: ["075", "028"], C_DEPT_LIB: ["Paris", "Eure-et-Loir"],
        C_INSEE: ["75001", "28001"], C_CLE_CODE: ["CLE-7501", "CLE-2801"],
        C_NOM_OFFICIEL: ["Comité Paris Centre", "Comité Chartres"],
        C_NOUVEAU_NOM: ["", ""], C_CONTACT: ["", ""],
        C_DATE_MAJ_ADMIN: ["", ""], C_DATE_DEMANDE: ["", ""]
    })

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

is_admin = st.session_state.authenticated

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.header("🔐 Administration")
    if not is_admin:
        pwd = st.text_input("Code Administrateur", type="password")
        if st.button("Connexion"):
            if pwd == "RPE_REFCLPE":
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("Code erroné")
    else:
        st.success("🔓 Mode Admin")
        if st.button("🚪 Déconnexion"):
            st.session_state.authenticated = False
            st.rerun()

    st.divider()
    st.header("🔍 Filtres")
    f_reg = st.multiselect(C_REG_LIB, options=sorted(st.session_state.df_main[C_REG_LIB].unique()), key="f_reg")
    f_dept = st.multiselect(C_DEPT_LIB, options=sorted(st.session_state.df_main[C_DEPT_LIB].unique()), key="f_dept")

# --- 3. FILTRAGE ---
df_display = st.session_state.df_main.copy()
if f_reg: df_display = df_display[df_display[C_REG_LIB].isin(f_reg)]
if f_dept: df_display = df_display[df_display[C_DEPT_LIB].isin(f_dept)]

# --- 4. SECTION UPLOAD ---
st.title("📍 Gestion du Référentiel CLPE")
st.markdown("---")
st.subheader("📥 Mise à jour par fichier")

with st.expander("❓ Aide au format du fichier"):
    st.markdown(f"Chargez un CSV avec 2 colonnes : **1. {C_INSEE}** / **2. Nom souhaité**.")
    if is_admin:
        st.info("💡 Mode Admin : Le nom officiel sera mis à jour immédiatement sans e-mail requis.")
    else:
        st.info("💡 Mode Utilisateur : Une proposition sera créée et soumise à validation.")

c_mail, c_file = st.columns([1, 2])
with c_mail:
    if not is_admin:
        contact_mail = st.text_input("📧 Votre e-mail de contact :", placeholder="exemple@mail.fr")
        email_valid = bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact_mail)) if contact_mail else False
    else:
        st.write("✅ **Admin identifié**")
        st.caption("L'e-mail n'est pas requis pour l'administrateur.")
        email_valid = True

with c_file:
    up_file = st.file_uploader("Déposer le fichier CSV", type="csv")

if up_file and email_valid:
    try:
        df_up = pd.read_csv(up_file, sep=None, engine='python', dtype=str).iloc[:, [0, 1]]
        df_up.columns = [C_INSEE, "tmp_name"]
        df_up["tmp_name"] = df_up["tmp_name"].fillna("")
        
        if st.button("🔄 Lancer la mise à jour"):
            today = datetime.now().strftime("%d/%m/%Y")
            # Mode outer pour l'admin (ajout nouvelles communes), left pour l'utilisateur
            mode = 'outer' if is_admin else 'left'
            merged = pd.merge(st.session_state.df_main, df_up, on=C_INSEE, how=mode)
            
            mask = merged["tmp_name"].notna()
            if is_admin:
                # Mise à jour directe du nom officiel
                merged.loc[mask, C_NOM_OFFICIEL] = merged.loc[mask, "tmp_name"]
                merged.loc[mask, C_DATE_MAJ_ADMIN] = today
                # On nettoie les anciennes propositions si l'admin écrase
                merged.loc[mask, [C_NOUVEAU_NOM, C_CONTACT, C_DATE_DEMANDE]] = ""
            else:
                # Création d'une proposition
                merged.loc[mask, C_NOUVEAU_NOM] = merged.loc[mask, "tmp_name"]
                merged.loc[mask, C_CONTACT] = contact_mail
                merged.loc[mask, C_DATE_DEMANDE] = today
            
            merged.drop(columns=["tmp_name"], inplace=True)
            st.session_state.df_main = merged.fillna("")
            st.success("Opération terminée avec succès.")
            st.rerun()
    except Exception as e: st.error(f"Erreur : {e}")

# --- 5. VISUALISATION ---
st.divider()

view_config = {
    C_REG_CODE: None, C_DEPT_CODE: None, C_CLE_CODE: None,
    C_REG_LIB: st.column_config.TextColumn("Libellé\nRégion", width="small"),
    C_DEPT_LIB: st.column_config.TextColumn("Libellé\nDépartement", width="small"),
    C_INSEE: st.column_config.TextColumn("Code commune\nInsee", width="small"),
    C_NOM_OFFICIEL: st.column_config.TextColumn("Nom du Comité Local\nPour l'Emploi", width="medium"),
    C_DATE_MAJ_ADMIN: st.column_config.TextColumn("Date MAJ\nAdmin", width="small"),
    C_NOUVEAU_NOM: st.column_config.TextColumn("Nouveau Nom du Comité\nLocal Pour l'Emploi", width="medium"),
    C_DATE_DEMANDE: st.column_config.TextColumn("Date de la\ndemande", width="small"),
    C_CONTACT: st.column_config.TextColumn("Contact\nE-mail", width="small")
}

if is_admin:
    st.subheader("✍️ Zone d'Édition et Validation")
    edit_mode = st.checkbox("Éditer uniquement la sélection filtrée", value=True)
    df_to_edit = df_display if edit_mode else st.session_state.df_main
    
    edited_df = st.data_editor(df_to_edit, use_container_width=True, column_config=view_config, num_rows="dynamic")
    
    ca, cb, cc = st.columns(3)
    with ca:
        if st.button("💾 Sauvegarder les saisies", use_container_width=True):
            st.session_state.df_main.update(edited_df)
            st.rerun()
    with cb:
        if st.button("🗑️ Purger les propositions", use_container_width=True):
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT, C_DATE_DEMANDE]] = ""
            st.rerun()
    with cc:
        if st.button("✅ Valider les propositions", use_container_width=True, type="primary"):
            today = datetime.now().strftime("%d/%m/%Y")
            mask = (st.session_state.df_main.index.isin(df_display.index)) & (st.session_state.df_main[C_NOUVEAU_NOM] != "")
            st.session_state.df_main.loc[mask, C_NOM_OFFICIEL] = st.session_state.df_main.loc[mask, C_NOUVEAU_NOM]
            st.session_state.df_main.loc[mask, C_DATE_MAJ_ADMIN] = today
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT, C_DATE_DEMANDE]] = ""
            st.rerun()
else:
    st.subheader("📊 Consultation du Référentiel")
    st.dataframe(df_display, use_container_width=True, column_config=view_config)

# --- 6. EXPORT ---
st.divider()
st.subheader("📥 Exportation")
sel_cols = st.multiselect("Colonnes :", options=st.session_state.df_main.columns.tolist(), default=[C_INSEE, C_NOM_OFFICIEL])
if sel_cols:
    csv = df_display[sel_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("⬇️ Télécharger CSV", data=csv, file_name="export_clpe.csv")
