import streamlit as st
import pandas as pd
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Référentiel CLPE", layout="wide", page_icon="📍")

# --- CSS POUR FORCER LE RETOUR À LA LIGNE DANS LES ENTÊTES ---
st.markdown("""
    <style>
        /* Tente de forcer le wrap dans les cellules d'entête du dataframe */
        [data-testid="stHeader"] th {
            white-space: normal !important;
            word-wrap: break-word !important;
            line-height: 1.2 !important;
            height: 50px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES (NOMS ORIGINAUX) ---
C_INSEE = "Code commune Insee"
C_NOM_OFFICIEL = "Nom du Comité Local Pour l'Emploi"
C_NOUVEAU_NOM = "Nouveau Nom du Comité Local Pour l'Emploi"
C_CONTACT = "Contact"
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
        C_NOUVEAU_NOM: ["", ""], C_CONTACT: ["", ""]
    })

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.header("🔐 Administration")
    if not st.session_state.authenticated:
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
    regions = st.multiselect(C_REG_LIB, options=sorted(st.session_state.df_main[C_REG_LIB].unique()), key="f_reg")
    depts = st.multiselect(C_DEPT_LIB, options=sorted(st.session_state.df_main[C_DEPT_LIB].unique()), key="f_dept")
    contacts = st.multiselect("Filtrer par Contact", options=sorted([c for c in st.session_state.df_main[C_CONTACT].unique() if c]), key="f_cont")

# --- 3. FILTRAGE ---
df_display = st.session_state.df_main.copy()
if regions: df_display = df_display[df_display[C_REG_LIB].isin(regions)]
if depts: df_display = df_display[df_display[C_DEPT_LIB].isin(depts)]
if contacts: df_display = df_display[df_display[C_CONTACT].isin(contacts)]

# --- 4. UPLOAD ---
st.title("📍 Gestion du Référentiel CLPE")
st.markdown("---")
st.subheader("📥 Soumettre une évolution")

with st.expander("❓ Guide : Comment effectuer une mise à jour ?"):
    st.markdown(f"""
    **Format du fichier CSV :**
    - Colonne 1 : **{C_INSEE}**
    - Colonne 2 : **{C_NOUVEAU_NOM}**
    - *L'ordre des colonnes prime sur leurs noms.*
    """)

c_mail, c_file = st.columns([1, 2])
with c_mail:
    contact_mail = st.text_input("📧 Votre e-mail :", placeholder="exemple@mail.fr")
    email_ok = bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact_mail)) if contact_mail else False

with c_file:
    up_file = st.file_uploader("Fichier CSV", type="csv")

if up_file and email_ok:
    try:
        df_up = pd.read_csv(up_file, sep=None, engine='python', dtype=str).iloc[:, [0, 1]]
        df_up.columns = [C_INSEE, "tmp_name"]
        df_up["tmp_name"] = df_up["tmp_name"].fillna("")
        
        if st.button("🔄 Appliquer les modifications"):
            mode = 'outer' if st.session_state.authenticated else 'left'
            merged = pd.merge(st.session_state.df_main, df_up, on=C_INSEE, how=mode)
            mask = merged["tmp_name"].notna()
            merged.loc[mask, C_NOUVEAU_NOM] = merged.loc[mask, "tmp_name"]
            merged.loc[mask, C_CONTACT] = contact_mail
            merged.drop(columns=["tmp_name"], inplace=True)
            st.session_state.df_main = merged.fillna("")
            st.rerun()
    except Exception as e: st.error(f"Erreur : {e}")

# --- 5. VISUALISATION (ENTÊTES SUR 2 LIGNES) ---
st.divider()

# Pour forcer les 2 lignes, on insère un \n dans le label du column_config
view_config = {
    C_REG_CODE: None, C_DEPT_CODE: None, C_CLE_CODE: None,
    C_REG_LIB: st.column_config.TextColumn("Libellé\nRégion", width="small"),
    C_DEPT_LIB: st.column_config.TextColumn("Libellé\nDépartement", width="small"),
    C_INSEE: st.column_config.TextColumn("Code\nInsee", width="small"),
    C_NOM_OFFICIEL: st.column_config.TextColumn("Nom Officiel\ndu Comité", width="medium"),
    C_NOUVEAU_NOM: st.column_config.TextColumn("Nouveau Nom\nproposé", width="medium"),
    C_CONTACT: st.column_config.TextColumn("Contact\nEmail", width="small")
}



if st.session_state.authenticated:
    st.subheader("✍️ Administration")
    edit_mode = st.checkbox("Filtrer l'édition", value=True)
    df_to_edit = df_display if edit_mode else st.session_state.df_main
    
    edited_df = st.data_editor(df_to_edit, use_container_width=True, column_config=view_config, num_rows="dynamic")
    
    ca, cb, cc = st.columns(3)
    with ca:
        if st.button("💾 Sauvegarder"):
            st.session_state.df_main.update(edited_df)
            st.rerun()
    with cb:
        if st.button("🗑️ Purger"):
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT]] = ""
            st.rerun()
    with cc:
        if st.button("✅ Valider", type="primary"):
            mask = (st.session_state.df_main.index.isin(df_display.index)) & (st.session_state.df_main[C_NOUVEAU_NOM] != "")
            st.session_state.df_main.loc[mask, C_NOM_OFFICIEL] = st.session_state.df_main.loc[mask, C_NOUVEAU_NOM]
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT]] = ""
            st.rerun()
else:
    st.subheader("📊 Référentiel")
    st.dataframe(df_display, use_container_width=True, column_config=view_config)

# --- 6. EXPORT ---
st.divider()
st.subheader("📥 Exportation")
sel_cols = st.multiselect("Colonnes :", options=st.session_state.df_main.columns.tolist(), default=[C_INSEE, C_NOM_OFFICIEL])
if sel_cols:
    csv = df_display[sel_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("⬇️ Télécharger CSV", data=csv, file_name="export_clpe.csv")
