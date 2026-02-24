import streamlit as st
import pandas as pd
import re
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Référentiel CLPE - Gestion des évolutions", 
    layout="wide", 
    page_icon="📍"
)

# --- CSS POUR FORCER LE RETOUR À LA LIGNE DES ENTÊTES ---
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

# --- CONSTANTES (LIBELLÉS ORIGINAUX) ---
C_INSEE = "Code commune Insee"
C_NOM_OFFICIEL = "Nom du Comité Local Pour l'Emploi"
C_NOUVEAU_NOM = "Nouveau Nom du Comité Local Pour l'Emploi"
C_CONTACT = "Contact"
C_DATE_MAJ_ADMIN = "Date de mise à jour admin"
C_DATE_DEMANDE = "Date de la demande de mise à jour"
C_REG_CODE = "Code Région"
C_REG_LIB = "Libellé Région"
C_DEPT_CODE = "Code Département"
C_DEPT_LIB = "Libellé Département"
C_CLE_CODE = "Code du Comité Local Pour l'Emploi"

# --- 1. INITIALISATION DES DONNÉES ET ÉTATS ---
if 'df_main' not in st.session_state:
    data = {
        C_REG_CODE: ["11", "24", "44"], C_REG_LIB: ["Île-de-France", "Centre-Val de Loire", "Grand Est"],
        C_DEPT_CODE: ["075", "028", "067"], C_DEPT_LIB: ["Paris", "Eure-et-Loir", "Bas-Rhin"],
        C_INSEE: ["75001", "28001", "67001"], C_CLE_CODE: ["CLE-7501", "CLE-2801", "CLE-6701"],
        C_NOM_OFFICIEL: ["Comité Paris Centre", "Comité Chartres", "Comité Strasbourg"],
        C_NOUVEAU_NOM: ["", "", ""], C_CONTACT: ["", "", ""],
        C_DATE_MAJ_ADMIN: ["", "", ""], C_DATE_DEMANDE: ["", "", ""]
    }
    st.session_state.df_main = pd.DataFrame(data)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Clé dynamique pour purger l'uploader après traitement
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# Stockage des sauvegardes horodatées
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
    f_reg = st.multiselect(C_REG_LIB, options=sorted(st.session_state.df_main[C_REG_LIB].unique()), key="perm_reg", help="Filtrer les données par région.")
    f_dept = st.multiselect(C_DEPT_LIB, options=sorted(st.session_state.df_main[C_DEPT_LIB].unique()), key="perm_dept", help="Filtrer les données par département.")
    
    # RETOUR DU FILTRE CONTACT
    contacts_list = sorted([c for c in st.session_state.df_main[C_CONTACT].unique() if c != ""])
    f_contact = st.multiselect("Filtrer par Contact (Auteur)", options=contacts_list, key="perm_contact", help="Affiche uniquement les propositions soumises par cet e-mail.")

# --- 3. LOGIQUE DE FILTRAGE ---
df_display = st.session_state.df_main.copy()
if f_reg:
    df_display = df_display[df_display[C_REG_LIB].isin(f_reg)]
if f_dept:
    df_display = df_display[df_display[C_DEPT_LIB].isin(f_dept)]
if f_contact:
    df_display = df_display[df_display[C_CONTACT].isin(f_contact)]

# --- 4. SECTION UPLOAD ET GUIDE ---
st.title("📍 Référentiel des Comités Locaux Pour l'Emploi")
st.markdown("---")
st.subheader("📥 Mise à jour du référentiel")

with st.expander("❓ Guide complet : Comment importer vos modifications ?"):
    # TOUTE LA LOGIQUE MAILTO EST ICI
    destinataire = "denis.gorce@francetravail.fr"
    sujet = "Mise à jour du référentiel CLPE"
    corps_email = (
        "Bonjour, je souhaiterais apporter les modifications suivantes au référentiel des CLPE :\n\n"
        "- Ajout des communes suivantes et nom du CLPE de rattachement (mettre le code Insee et le nom du CLPE associé).\n"
        "- Modification du nom d'un CLPE (mettre le nom actuel et le nom souhaité).\n"
        "- Modification d'affectation des communes à un CLPE (mettre les codes commune Insee concernées et le nouveau nom du CLPE associé)."
    )
    # Encodage spécifique pour l'URL
    mail_url = f"mailto:{destinataire}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(corps_email)}"

    # Utilisation de triple guillemets clairs pour éviter le SyntaxError
    st.markdown(f"""
**Format du fichier CSV attendu :**
- **Colonne 1** : Doit contenir le **{C_INSEE}** (ex: 75001).
- **Colonne 2** : Doit contenir le nom souhaité pour le comité.

**Règles de traitement :**
1. **Utilisateur** : E-mail obligatoire. Remplit la colonne *{C_NOUVEAU_NOM}*.
2. **Administrateur** : Pas d'e-mail requis. Met à jour directement le nom officiel.

---
**Une difficulté ou une demande spécifique ?**
Si vous ne parvenez pas à utiliser l'outil de chargement ou si votre demande concerne :
- L'ajout de nouveaux codes commune Insee.
- La modification de l'affectation d'une commune.
- Un changement de nom complexe.

Veuillez cliquer sur le bouton ci-dessous pour nous envoyer un e-mail pré-rempli :
""")
    
    st.link_button(
        "📧 Contactez le support (Help)", 
        mail_url, 
        help="Vous ne parvenez pas à utiliser l'outil de chargement de fichier ou votre demande concerne l'ajout de codes commune."
    )

col_mail, col_file = st.columns([1, 2])
with col_mail:
    if not is_admin:
        contact_mail = st.text_input("📧 Votre e-mail de contact :", placeholder="prenom.nom@domaine.fr", help="Obligatoire pour tracer l'origine de la demande (Visible dans la colonne Contact).")
        email_valid = bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact_mail)) if contact_mail else False
    else:
        st.info("✅ **Identifié comme Administrateur**")
        st.caption("Les modifications seront appliquées directement sans validation intermédiaire.")
        email_valid = True

with col_file:
    # L'utilisation de st.session_state.uploader_key permet de réinitialiser/purger le composant après succès
    up_file = st.file_uploader("Charger le fichier CSV de mise à jour", type="csv", key=f"uploader_{st.session_state.uploader_key}", help="Sélectionnez un fichier CSV encodé en UTF-8.")

if up_file and email_valid:
    try:
        df_up = pd.read_csv(up_file, sep=None, engine='python', dtype=str, encoding='utf-8-sig').iloc[:, [0, 1]]
        df_up.columns = [C_INSEE, "tmp_name"]
        df_up["tmp_name"] = df_up["tmp_name"].fillna("")
        
        # --- BLOC DE TRAITEMENT DE L'IMPORT CSV ---
        if st.button("🔄 Lancer l'intégration du fichier", help="Cliquez pour traiter le fichier et mettre à jour la base de données ci-dessous."):
            today = datetime.now().strftime("%d/%m/%Y")
            
            # Détermination du mode de fusion
            mode = 'outer' if is_admin else 'left'
            
            merged = pd.merge(st.session_state.df_main, df_up, on=C_INSEE, how=mode)
            mask = merged["tmp_name"].notna()
            
            if is_admin:
                # --- LOGIQUE ADMINISTRATEUR ---
                merged.loc[mask, C_NOM_OFFICIEL] = merged.loc[mask, "tmp_name"]
                merged.loc[mask, C_DATE_MAJ_ADMIN] = today
                # Nettoyage des anciennes demandes
                merged.loc[mask, [C_NOUVEAU_NOM, C_CONTACT, C_DATE_DEMANDE]] = ""
            else:
                # --- LOGIQUE UTILISATEUR STANDARD ---
                merged.loc[mask, C_NOUVEAU_NOM] = merged.loc[mask, "tmp_name"]
                merged.loc[mask, C_CONTACT] = contact_mail
                merged.loc[mask, C_DATE_DEMANDE] = today
            
            merged.drop(columns=["tmp_name"], inplace=True)
            st.session_state.df_main = merged.fillna("")
            
            # On incrémente la clé pour purger visuellement le fichier uploadé
            st.session_state.uploader_key += 1
            
            st.success("✅ L'intégration a été effectuée avec succès. Le fichier a été purgé.")
            st.rerun()
            
    except Exception as e:
        st.error(f"⚠️ Erreur lors de la lecture du fichier : {e}")
elif up_file and not email_valid:
    st.warning("ℹ️ Veuillez renseigner un e-mail valide pour soumettre vos modifications.")


# --- 5. VISUALISATION ET ÉDITION ---
st.divider()

view_config = {
    C_REG_CODE: None, C_DEPT_CODE: None, C_CLE_CODE: None,
    C_REG_LIB: st.column_config.TextColumn("Libellé\nRégion", width="small"),
    C_DEPT_LIB: st.column_config.TextColumn("Libellé\nDépartement", width="small"),
    C_INSEE: st.column_config.TextColumn("Code commune\nInsee", width="small"),
    C_NOM_OFFICIEL: st.column_config.TextColumn("Nom du Comité Local\nPour l'Emploi", width="medium"),
    C_DATE_MAJ_ADMIN: st.column_config.TextColumn("Date mise à jour\nAdmin", width="small"),
    C_NOUVEAU_NOM: st.column_config.TextColumn("Nouveau Nom du Comité\nLocal Pour l'Emploi", width="medium"),
    C_DATE_DEMANDE: st.column_config.TextColumn("Date de la\ndemande", width="small"),
    C_CONTACT: st.column_config.TextColumn("Contact\nE-mail", width="small")
}

if is_admin:
    st.subheader("✍️ Zone d'Administration (Édition & Validation)")
    f_edit = st.checkbox("Éditer uniquement la sélection filtrée", value=True, help="Si décoché, vous accéderez à toute la base de données, y compris les éléments masqués par les filtres.")
    
    df_to_edit = df_display if f_edit else st.session_state.df_main
    edited_df = st.data_editor(df_to_edit, use_container_width=True, column_config=view_config, num_rows="dynamic")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Sauvegarder les saisies manuelles", use_container_width=True, help="Enregistre les modifications que vous venez de taper directement dans le tableau ci-dessus."):
            st.session_state.df_main.update(edited_df)
            st.success("Modifications manuelles enregistrées.")
            st.rerun()
    with c2:
        if st.button("🗑️ Purger les propositions", use_container_width=True, help="Annule et efface toutes les demandes de 'Nouveau Nom' visibles dans le tableau actuel."):
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT, C_DATE_DEMANDE]] = ""
            st.rerun()
    with c3:
        if st.button("✅ Valider et Écraser les noms", use_container_width=True, type="primary", help="Approuve les propositions visibles : le 'Nouveau Nom' devient le 'Nom Officiel' et la date de mise à jour admin est enregistrée."):
            today = datetime.now().strftime("%d/%m/%Y")
            mask_v = (st.session_state.df_main.index.isin(df_display.index)) & (st.session_state.df_main[C_NOUVEAU_NOM] != "")
            st.session_state.df_main.loc[mask_v, C_NOM_OFFICIEL] = st.session_state.df_main.loc[mask_v, C_NOUVEAU_NOM]
            st.session_state.df_main.loc[mask_v, C_DATE_MAJ_ADMIN] = today
            st.session_state.df_main.loc[df_display.index, [C_NOUVEAU_NOM, C_CONTACT, C_DATE_DEMANDE]] = ""
            st.balloons()
            st.rerun()
            
    # --- GESTION DES SAUVEGARDES HORODATÉES ---
    st.divider()
    st.subheader("🗄️ Gestion des sauvegardes de la base")
    st.info("💡 Vous pouvez créer un point de restauration de la base de données actuelle avant de faire des modifications massives ou après une session de validation.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("💾 Créer une nouvelle sauvegarde", help="Capture l'état exact de la base de données à cet instant et le stocke en mémoire."):
            timestamp_backup = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            st.session_state.backups[timestamp_backup] = st.session_state.df_main.copy()
            st.success(f"✅ Sauvegarde créée avec succès le {timestamp_backup}")
            st.rerun()
            
    with col_b2:
        if st.session_state.backups:
            backup_options = list(st.session_state.backups.keys())
            backup_options.sort(reverse=True)
            
            selected_backup = st.selectbox("Choisir une sauvegarde à restaurer :", options=backup_options, help="Sélectionnez l'horodatage d'une ancienne sauvegarde à recharger.")
            if st.button("⚠️ Restaurer cette sauvegarde", type="secondary", help="Attention, cela écrasera l'état actuel de la base de données par l'état sélectionné."):
                st.session_state.df_main = st.session_state.backups[selected_backup].copy()
                st.success(f"🔄 Base de données restaurée à l'état du {selected_backup}")
                st.rerun()
        else:
            st.write("Aucune sauvegarde disponible pour le moment.")

else:
    st.subheader("📊 Consultation du Référentiel")
    st.info("💡 Les colonnes de droite affichent les demandes de changement en cours de validation.")
    st.dataframe(df_display, use_container_width=True, column_config=view_config)

# --- 6. EXPORTATION ---
st.divider()
st.subheader("📥 Exportation")
sel_cols = st.multiselect("Sélectionnez les colonnes à exporter :", options=st.session_state.df_main.columns.tolist(), default=[C_INSEE, C_NOM_OFFICIEL], help="Ajoutez ou retirez des colonnes pour générer votre fichier CSV sur mesure.")

if sel_cols:
    csv_data = df_display[sel_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(label=f"⬇️ Télécharger le CSV ({len(df_display)} lignes)", data=csv_data, file_name="referentiel_clpe_export.csv", mime="text/csv", help="Cliquez pour obtenir le fichier exploitable dans Excel (séparateur point-virgule).")
