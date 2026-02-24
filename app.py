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

# --- 1. INITIALISATION (SESSION STATE) ---
if 'df_main' not in st.session_state:
    data = {
        "Code Région": ["11", "24", "44"],
        "Libellé Région": ["Île-de-France", "Centre-Val de Loire", "Grand Est"],
        "Code Département": ["075", "028", "067"],
        "Libellé Département": ["Paris", "Eure-et-Loir", "Bas-Rhin"],
        C_INSEE: ["75001", "28001", "67001"],
        C_NOM_OFFICIEL: ["Comité Paris Centre", "Comité Chartres", "Comité Strasbourg"],
        C_NOUVEAU_NOM: ["", "", ""], # Permanent
        C_CONTACT: ["", "", ""]      # Permanent
    }
    st.session_state.df_main = pd.DataFrame(data)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 2. BARRE LATÉRALE (CONNEXION & FILTRES) ---
with st.sidebar:
    st.header("🔐 Administration")
    if not st.session_state.authenticated:
        pwd = st.text_input("Code Administrateur", type="password", help="Saisissez le code pour activer l'ajout de communes et la validation.")
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
    regions = st.multiselect("Régions", options=sorted(st.session_state.df_main["Libellé Région"].dropna().unique()))
    depts = st.multiselect("Départements", options=sorted(st.session_state.df_main["Libellé Département"].dropna().unique()))

# --- 3. LOGIQUE DE FILTRAGE ---
df_display = st.session_state.df_main.copy()
if regions:
    df_display = df_display[df_display["Libellé Région"].isin(regions)]
if depts:
    df_display = df_display[df_display["Libellé Département"].isin(depts)]

# --- 4. SECTION UPLOAD ---
st.title("📍 Gestion du Référentiel CLPE")
st.markdown("---")
st.subheader("📥 Soumettre une évolution")

# AIDE CONTEXTUELLE
with st.expander("❓ Guide : Format du fichier et procédure"):
    st.markdown(f"""
    **Format du fichier CSV :**
    - Le fichier doit avoir **2 colonnes**.
    - **Colonne 1** : Le Code INSEE de la commune.
    - **Colonne 2** : Le **{C_NOUVEAU_NOM}**. 
    - *Note : Les intitulés des colonnes n'ont pas d'importance.*

    **Droits :**
    - **Utilisateur** : Peut proposer des nouveaux noms pour des communes existantes.
    - **Administrateur** : Peut ajouter des nouvelles lignes (communes absentes de la base).
    """)

# Formulaire d'identification
col_mail, col_file = st.columns([1, 2])
with col_mail:
    contact_mail = st.text_input("📧 Votre e-mail de contact (obligatoire) :", placeholder="exemple@domaine.fr")
    email_valid = bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact_mail)) if contact_mail else False

with col_file:
    up_file = st.file_uploader("Déposer le fichier CSV", type="csv")

if up_file and email_valid:
    try:
        # Lecture flexible (détection séparateur)
        df_up = pd.read_csv(up_file, sep=None, engine='python', dtype=str, encoding='utf-8-sig')
        
        if len(df_up.columns) >= 2:
            # On renomme arbitrairement pour la logique interne
            # Col 0 = INSEE, Col 1 = Nouveau Nom
            df_up = df_up.iloc[:, [0, 1]]
            df_up.columns = [C_INSEE, "tmp_name"]
            
            st.success(f"✅ Fichier détecté ({len(df_up)} lignes).")
            
            if st.button(f"🔄 Appliquer en tant que '{C_NOUVEAU_NOM}'"):
                # Préparation du staging
                df_staging = df_up.copy()
                df_staging["tmp_contact"] = contact_mail

                # Fusion : Admin = ajout (outer), User = mise à jour seule (left)
                mode = 'outer' if is_admin else 'left'
                merged = pd.merge(st.session_state.df_main, df_staging, on=C_INSEE, how=mode)

                # Transfert des données et gestion des types
                merged[C_NOUVEAU_NOM] = merged["tmp_name"].combine_first(merged[C_NOUVEAU_NOM])
                merged[C_CONTACT] = merged["tmp_contact"].combine_first(merged[C_CONTACT])
                
                # Nettoyage
                merged.drop(columns=["tmp_name", "tmp_contact"], inplace=True)
                merged.fillna("", inplace=True)
                st.session_state.df_main = merged
                
                st.warning(f"🔔 **Mise à jour effectuée** : La colonne '{C_NOUVEAU_NOM}' a été complétée. En attente de validation admin.")
                st.rerun()
        else:
            st.error("❌ Le fichier doit contenir au moins deux colonnes (INSEE et Nouveau Nom).")
    except Exception as e:
        st.error(f"⚠️ Erreur lors de la lecture : {e}")
elif up_file and not email_valid:
    st.info("ℹ️ Veuillez saisir une adresse e-mail valide pour débloquer l'envoi du fichier.")

# --- 5. VISUALISATION ET ÉDITION ---
st.divider()
has_updates = (st.session_state.df_main[C_CONTACT] != "").any()



if is_admin:
    st.subheader("✍️ Zone d'Édition et Validation (Admin)")
    if has_updates:
        st.error("📢 Des modifications proposées par des utilisateurs sont en attente.")
    
    # Éditeur pour l'admin
    edited_df = st.data_editor(st.session_state.df_main, use_container_width=True, num_rows="dynamic")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Enregistrer les saisies manuelles"):
            st.session_state.df_main = edited_df
            st.success("Modifications enregistrées.")
            st.rerun()
    with c2:
        if has_updates and st.button("✅ Valider et écraser définitivement les noms officiels"):
            mask = st.session_state.df_main[C_NOUVEAU_NOM] != ""
            st.session_state.df_main.loc[mask, C_NOM_OFFICIEL] = st.session_state.df_main.loc[mask, C_NOUVEAU_NOM]
            # Réinitialisation des champs de suivi
            st.session_state.df_main[C_NOUVEAU_NOM] = ""
            st.session_state.df_main[C_CONTACT] = ""
            st.balloons()
            st.rerun()
else:
    st.subheader("📊 Référentiel CLPE")
    st.info("💡 Les colonnes de droite affichent les propositions en cours de validation.")
    st.dataframe(df_display, use_container_width=True)

# --- 6. EXPORTATION ---
st.divider()
st.subheader("📥 Exportation")

all_cols = df_display.columns.tolist()

# CONFIGURATION DEMANDÉE : INSEE et NOM OFFICIEL par défaut uniquement
default_export = [C_INSEE, C_NOM_OFFICIEL]
current_default = [c for c in default_export if c in all_cols]

sel_cols = st.multiselect(
    "Sélectionnez les colonnes à inclure dans l'export :", 
    options=all_cols, 
    default=current_default,
    help="Par défaut, seules les colonnes officielles sont sélectionnées."
)

if sel_cols:
    csv_data = df_display[sel_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label=f"📥 Télécharger le fichier CSV ({len(df_display)} lignes)", 
        data=csv_data, 
        file_name="referentiel_clpe.csv", 
        mime="text/csv"
    )
