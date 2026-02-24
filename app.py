import streamlit as st
import pandas as pd
import re

# CONFIGURATION
st.set_page_config(page_title="Référentiel CLPE", layout="wide", page_icon="📍")

# --- CONSTANTES ---
C_INSEE = "Code commune Insee"
C_NOM_OFFICIEL = "Nom du Comité Local Pour l'Emploi"
C_NOUVEAU_NOM = "Nouveau Nom du Comité Local Pour l'Emploi"
C_CONTACT = "Contact"

# --- 1. INITIALISATION DES DONNÉES ---
if 'df_main' not in st.session_state:
    data = {
        "Code Région": ["11", "24", "44", "32"],
        "Libellé Région": ["Île-de-France", "Centre-Val de Loire", "Grand Est", "Hauts-de-France"],
        "Code Département": ["075", "028", "067", "059"],
        "Libellé Département": ["Paris", "Eure-et-Loir", "Bas-Rhin", "Nord"],
        C_INSEE: ["75001", "28001", "67001", "59001"],
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
        pwd = st.text_input("Code Administrateur", type="password")
        if st.button("Connexion"):
            if pwd == "RPE_REFCLPE":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Code erroné")
    else:
        st.success("🔓 Mode Admin")
        if st.button("🚪 Déconnexion"):
            st.session_state.authenticated = False
            st.rerun()

    is_admin = st.session_state.authenticated
    st.divider()
    
    st.header("🔍 Filtres")
    # L'ajout de 'key=' permet aux filtres de survivre à la déconnexion
    regions = st.multiselect("Régions", 
                            options=sorted(st.session_state.df_main["Libellé Région"].dropna().unique()),
                            key="filter_regions")
    
    depts = st.multiselect("Départements", 
                           options=sorted(st.session_state.df_main["Libellé Département"].dropna().unique()),
                           key="filter_depts")
    
    contacts_dispo = sorted([c for c in st.session_state.df_main[C_CONTACT].unique() if c != ""])
    contact_filter = st.multiselect("Filtrer par Contact", 
                                    options=contacts_dispo,
                                    key="filter_contacts")

# --- 3. LOGIQUE DE FILTRAGE UNIFIÉE ---
df_display = st.session_state.df_main.copy()
if regions:
    df_display = df_display[df_display["Libellé Région"].isin(regions)]
if depts:
    df_display = df_display[df_display["Libellé Département"].isin(depts)]
if contact_filter:
    df_display = df_display[df_display[C_CONTACT].isin(contact_filter)]

# --- 4. SECTION UPLOAD ---
st.title("📍 Gestion du Référentiel CLPE")
st.markdown("---")
st.subheader("📥 Soumettre une évolution")

col_mail, col_file = st.columns([1, 2])
with col_mail:
    contact_mail = st.text_input("📧 Votre e-mail :", placeholder="nom@exemple.fr")
    email_valid = bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact_mail)) if contact_mail else False

with col_file:
    up_file = st.file_uploader("Charger le fichier CSV (Col 1: INSEE, Col 2: Nouveau Nom)", type="csv")

if up_file and email_valid:
    try:
        df_up = pd.read_csv(up_file, sep=None, engine='python', dtype=str, encoding='utf-8-sig')
        if len(df_up.columns) >= 2:
            df_up = df_up.iloc[:, [0, 1]].copy()
            df_up.columns = [C_INSEE, "tmp_name"]
            df_up["tmp_name"] = df_up["tmp_name"].fillna("") # Gestion des noms vides demandée
            
            if st.button(f"🔄 Appliquer en tant que '{C_NOUVEAU_NOM}'"):
                mode = 'outer' if is_admin else 'left'
                merged = pd.merge(st.session_state.df_main, df_up, on=C_INSEE, how=mode)
                
                # Mise à jour des champs de proposition
                mask = merged["tmp_name"].notna()
                merged.loc[mask, C_NOUVEAU_NOM] = merged.loc[mask, "tmp_name"]
                merged.loc[mask, C_CONTACT] = contact_mail
                
                merged.drop(columns=["tmp_name"], inplace=True)
                merged.fillna("", inplace=True)
                st.session_state.df_main = merged
                st.success("Proposition enregistrée.")
                st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# --- 5. VISUALISATION ET ACTIONS ---
st.divider()

if is_admin:
    st.subheader("✍️ Zone d'Édition et Validation (Admin)")
    
    # Choix de la vue pour l'admin
    edit_filtered = st.checkbox("Éditer uniquement la sélection filtrée", value=True)
    df_to_edit = df_display if edit_filtered else st.session_state.df_main

    edited_df = st.data_editor(df_to_edit, use_container_width=True, num_rows="dynamic")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Sauvegarder les saisies manuelles", use_container_width=True):
            st.session_state.df_main.update(edited_df)
            st.success("Modifications enregistrées.")
            st.rerun()
    
    with c2:
        if st.button("🗑️ Purger les propositions affichées", use_container_width=True):
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT]] = ""
            st.warning("Propositions purgées pour la sélection.")
            st.rerun()

    with c3:
        if st.button("✅ Valider la sélection", use_container_width=True, type="primary"):
            # On ne valide que ce qui est affiché ET qui a un nouveau nom
            mask_val = (st.session_state.df_main.index.isin(df_display.index)) & (st.session_state.df_main[C_NOUVEAU_NOM] != "")
            st.session_state.df_main.loc[mask_val, C_NOM_OFFICIEL] = st.session_state.df_main.loc[mask_val, C_NOUVEAU_NOM]
            # Reset des champs de suivi pour la sélection
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT]] = ""
            st.balloons()
            st.rerun()
else:
    st.subheader("📊 Référentiel CLPE")
    st.dataframe(df_display, use_container_width=True)

# --- 6. EXPORTATION ---
st.divider()
st.subheader("📥 Exportation")
default_export = [C_INSEE, C_NOM_OFFICIEL]
sel_cols = st.multiselect("Colonnes :", options=df_display.columns.tolist(), default=default_export)

if sel_cols:
    csv_data = df_display[sel_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("⬇️ Télécharger le CSV", data=csv_data, file_name="referentiel_clpe.csv", mime="text/csv")
