import streamlit as st
import pandas as pd
import re
from datetime import datetime
import urllib.parse

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Référentiel CLPE - Gestion des évolutions", 
    layout="wide", 
    page_icon="📍"
)

# --- CSS POUR LES ENTÊTES ---
st.markdown("""
    <style>
        div[data-testid="stDataFrame"] th {
            white-space: normal !important;
            word-wrap: break-word !important;
            line-height: 1.1 !important;
            height: auto !important;
            min-height: 50px;
            vertical-align: bottom;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES (LIBELLÉS ORIGINAUX) ---
C_REG_CODE = "Code Région"
C_REG_LIB = "Libellé Région"
C_DEPT_CODE = "Code Département"
C_DEPT_LIB = "Libellé Département"
C_INSEE = "Code commune Insee"
C_CLE_CODE = "Code du Comité Local Pour l'Emploi"
C_NOM_OFFICIEL = "Nom du Comité Local Pour l'Emploi"
C_DATE_MAJ_ADMIN = "Date de mise à jour admin"
C_NOUVEAU_NOM = "Nouveau Nom du Comité Local Pour l'Emploi"
C_DATE_DEMANDE = "Date de la demande de mise à jour"
C_CONTACT = "Contact"

# --- 1. INITIALISATION DES DONNÉES ET ÉTATS ---
if 'df_main' not in st.session_state:
    data = {
        C_REG_CODE: ["11", "24", "44"], 
        C_REG_LIB: ["Île-de-France", "Centre-Val de Loire", "Grand Est"],
        C_DEPT_CODE: ["075", "028", "067"], 
        C_DEPT_LIB: ["Paris", "Eure-et-Loir", "Bas-Rhin"],
        C_INSEE: ["75001", "28001", "67001"], 
        C_CLE_CODE: ["CLE-7501", "CLE-2801", "CLE-6701"],
        C_NOM_OFFICIEL: ["Comité Paris Centre", "Comité Chartres", "Comité Strasbourg"],
        C_DATE_MAJ_ADMIN: ["", "", ""],
        C_NOUVEAU_NOM: ["", "", ""], 
        C_DATE_DEMANDE: ["", "", ""],
        C_CONTACT: ["", "", ""]
    }
    st.session_state.df_main = pd.DataFrame(data)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0
if 'backups' not in st.session_state:
    st.session_state.backups = {}

is_admin = st.session_state.authenticated

# --- 2. BARRE LATÉRALE (ADMIN & FILTRES) ---
with st.sidebar:
    st.header("🔐 Administration")
    if not is_admin:
        pwd = st.text_input("Code Administrateur", type="password", help="Saisissez le code pour activer les droits de modification directe, de validation et de sauvegarde.")
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

    st.divider()
    st.header("🔍 Filtres d'affichage")
    f_reg = st.multiselect(C_REG_LIB, options=sorted(st.session_state.df_main[C_REG_LIB].unique()), key="perm_reg", help="Filtre les données par région.")
    f_dept = st.multiselect(C_DEPT_LIB, options=sorted(st.session_state.df_main[C_DEPT_LIB].unique()), key="perm_dept", help="Filtre les données par département.")
    contacts_list = sorted([c for c in st.session_state.df_main[C_CONTACT].unique() if c != ""])
    f_contact = st.multiselect("Filtrer par Contact (Auteur)", options=contacts_list, key="perm_contact", help="Affiche uniquement les propositions d'un utilisateur.")

# --- 3. LOGIQUE DE FILTRAGE ---
df_display = st.session_state.df_main.copy()
if f_reg: df_display = df_display[df_display[C_REG_LIB].isin(f_reg)]
if f_dept: df_display = df_display[df_display[C_DEPT_LIB].isin(f_dept)]
if f_contact: df_display = df_display[df_display[C_CONTACT].isin(f_contact)]

# --- 4. SECTION UPLOAD ET GUIDE ---
st.title("📍 Référentiel des Comités Locaux Pour l'Emploi")
st.markdown("---")
st.subheader("📥 Mise à jour du référentiel")

with st.expander("❓ Guide complet : Comment importer vos modifications ?"):
    destinataire = "denis.gorce@francetravail.fr"
    sujet = "Mise à jour du référentiel CLPE"
    corps_email = "Bonjour, je souhaiterais apporter les modifications suivantes au référentiel des CLPE..."
    mail_url = f"mailto:{destinataire}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(corps_email)}"

    st.markdown(f"""
**Format du fichier CSV attendu :**
- **Mode Utilisateur** : 2 colonnes ({C_INSEE} et Nouveau Nom).
- **Mode Administrateur** : Import complet possible. Le fichier doit contenir au moins la colonne **{C_INSEE}** pour identifier les lignes. Vous pouvez inclure les colonnes Région, Département ou Code CLPE pour les mettre à jour.

**Règles de traitement :**
1. **Utilisateur** : Renseigne uniquement le champ *{C_NOUVEAU_NOM}*.
2. **Administrateur** : Écrase directement les données officielles et peut créer de nouvelles lignes.
""")
    st.link_button("📧 Contactez le support (Help)", mail_url, help="Ouvrir un mail pré-rempli pour assistance.")

col_mail, col_file = st.columns([1, 2])
with col_mail:
    if not is_admin:
        contact_mail = st.text_input("📧 Votre e-mail de contact :", placeholder="prenom.nom@domaine.fr", help="Requis pour tracer l'auteur de la proposition.")
        email_valid = bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact_mail)) if contact_mail else False
    else:
        st.info("🛠️ **Mode Admin : Import complet**")
        email_valid = True

with col_file:
    up_file = st.file_uploader("Charger le fichier CSV", type="csv", key=f"uploader_{st.session_state.uploader_key}", help="Fichier CSV (séparateur ';' ou ',').")

if up_file and email_valid:
    try:
        df_up = pd.read_csv(up_file, sep=None, engine='python', dtype=str, encoding='utf-8-sig')
        if st.button("🔄 Lancer l'intégration", help="Fusionner les données du fichier avec la base actuelle."):
            today = datetime.now().strftime("%d/%m/%Y")
            df_main = st.session_state.df_main.copy()

            if is_admin:
                if C_INSEE not in df_up.columns:
                    st.error(f"Colonne '{C_INSEE}' manquante.")
                else:
                    cols_to_update = [c for c in df_up.columns if c in df_main.columns and c != C_INSEE]
                    for _, row in df_up.iterrows():
                        idx_insee = row[C_INSEE]
                        if idx_insee in df_main[C_INSEE].values:
                            for col in cols_to_update:
                                if pd.notna(row[col]): df_main.loc[df_main[C_INSEE] == idx_insee, col] = row[col]
                            df_main.loc[df_main[C_INSEE] == idx_insee, C_DATE_MAJ_ADMIN] = today
                        else:
                            new_row = {c: row[c] if c in df_up.columns else "" for c in df_main.columns}
                            new_row[C_DATE_MAJ_ADMIN] = today
                            df_main = pd.concat([df_main, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.df_main = df_main
                    st.success("✅ Base admin mise à jour.")
            else:
                df_up = df_up.iloc[:, [0, 1]]
                df_up.columns = [C_INSEE, "tmp_name"]
                merged = pd.merge(df_main, df_up, on=C_INSEE, how='left')
                mask = merged["tmp_name"].notna()
                merged.loc[mask, C_NOUVEAU_NOM] = merged.loc[mask, "tmp_name"]
                merged.loc[mask, C_CONTACT] = contact_mail
                merged.loc[mask, C_DATE_DEMANDE] = today
                st.session_state.df_main = merged.drop(columns=["tmp_name"]).fillna("")
                st.success("✅ Propositions transmises.")

            st.session_state.uploader_key += 1
            st.rerun()
    except Exception as e:
        st.error(f"⚠️ Erreur : {e}")

# --- 5. VISUALISATION ET ÉDITION ---
st.divider()

# CONFIGURATION DES LARGEURS (Optimisation pour éviter le scroll)
view_config = {
    C_REG_CODE: st.column_config.TextColumn(width=60),
    C_DEPT_CODE: st.column_config.TextColumn(width=60),
    C_INSEE: st.column_config.TextColumn(width=70),
    C_CLE_CODE: st.column_config.TextColumn(width=80),
    C_REG_LIB: st.column_config.TextColumn(width=120),
    C_DEPT_LIB: st.column_config.TextColumn(width=120),
    C_NOM_OFFICIEL: st.column_config.TextColumn(width=200),
    C_DATE_MAJ_ADMIN: st.column_config.TextColumn(width=90),
    C_NOUVEAU_NOM: st.column_config.TextColumn(width=200),
    C_DATE_DEMANDE: st.column_config.TextColumn(width=90),
    C_CONTACT: st.column_config.TextColumn(width=120)
}

if is_admin:
    st.subheader("✍️ Administration")
    f_edit = st.checkbox("Éditer uniquement la sélection filtrée", value=True)
    df_to_edit = df_display if f_edit else st.session_state.df_main
    edited_df = st.data_editor(df_to_edit, use_container_width=True, column_config=view_config, num_rows="dynamic")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Sauvegarder saisies", use_container_width=True, help="Enregistre les modifications faites dans le tableau."):
            st.session_state.df_main.update(edited_df); st.rerun()
    with c2:
        if st.button("🗑️ Purger propositions", use_container_width=True, help="Supprime les demandes de nouveaux noms affichées."):
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT, C_DATE_DEMANDE]] = ""; st.rerun()
    with c3:
        if st.button("✅ Valider changements", use_container_width=True, type="primary", help="Approuve les nouveaux noms comme noms officiels."):
            mask_v = (st.session_state.df_main.index.isin(df_display.index)) & (st.session_state.df_main[C_NOUVEAU_NOM] != "")
            st.session_state.df_main.loc[mask_v, C_NOM_OFFICIEL] = st.session_state.df_main.loc[mask_v, C_NOUVEAU_NOM]
            st.session_state.df_main.loc[mask_v, C_DATE_MAJ_ADMIN] = datetime.now().strftime("%d/%m/%Y")
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT, C_DATE_DEMANDE]] = ""; st.balloons(); st.rerun()

    # SAUVEGARDES
    st.divider()
    cb1, cb2 = st.columns(2)
    with cb1:
        if st.button("💾 Créer sauvegarde", help="Point de restauration."):
            ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            st.session_state.backups[ts] = st.session_state.df_main.copy()
            st.success(f"Sauvegarde {ts} créée.")
    with cb2:
        if st.session_state.backups:
            sel_b = st.selectbox("Restaurer :", options=sorted(st.session_state.backups.keys(), reverse=True))
            if st.button("⚠️ Restaurer"): st.session_state.df_main = st.session_state.backups[sel_b].copy(); st.rerun()
else:
    st.subheader("📊 Consultation")
    st.dataframe(df_display, use_container_width=True, column_config=view_config)

# --- 6. EXPORTATION ---
st.divider()
st.subheader("📥 Exportation")
sel_cols = st.multiselect("Colonnes :", options=st.session_state.df_main.columns.tolist(), default=[C_INSEE, C_NOM_OFFICIEL], help="Sélectionnez les champs pour l'export CSV.")
if sel_cols:
    csv = df_display[sel_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(f"⬇️ Télécharger CSV ({len(df_display)} lignes)", csv, "export_clpe.csv", "text/csv")
