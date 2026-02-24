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
    # Création de la structure de base avec les colonnes de suivi permanentes
    data = {
        "Code Région": ["11", "24"],
        "Libellé Région": ["Île-de-France", "Centre-Val de Loire"],
        "Code Département": ["075", "028"],
        "Libellé Département": ["Paris", "Eure-et-Loir"],
        C_INSEE: ["75001", "28001"],
        "Code du Comité": ["CLE-7501", "CLE-2801"],
        C_NOM_OFFICIEL: ["Comité Paris Centre", "Comité Chartres"],
        C_NOUVEAU_NOM: ["", ""], # Toujours visible
        C_CONTACT: ["", ""]      # Toujours visible
    }
    st.session_state.df_main = pd.DataFrame(data)

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

# --- 3. FILTRAGE ---
df_display = st.session_state.df_main.copy()
if regions:
    df_display = df_display[df_display["Libellé Région"].isin(regions)]
if depts:
    df_display = df_display[df_display["Libellé Département"].isin(depts)]

# --- 4. UPLOAD & PROPOSITION ---
st.title("📍 Référentiel des Comités Locaux Pour l'Emploi")
st.subheader("📥 Soumettre une évolution")

with st.expander("❓ Guide : Comment proposer une modification ?"):
    st.markdown(f"""
    1. Votre fichier CSV doit contenir au moins les colonnes **{C_INSEE}** et **{C_NOM_OFFICIEL}** (ce dernier servira de proposition).
    2. Renseignez votre e-mail de contact ci-dessous.
    3. Cliquez sur le bouton de chargement.
    4. **Note Admin :** En mode connecté, l'import permet d'ajouter de nouvelles lignes (Insee inconnus).
    """)

# Formulaire d'identification
col_mail, col_file = st.columns([1, 2])
with col_mail:
    contact_mail = st.text_input("📧 Votre e-mail de contact :", placeholder="exemple@domaine.fr")
    email_valid = bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact_mail)) if contact_mail else False

with col_file:
    up_file = st.file_uploader("Déposer le fichier CSV", type="csv")

if up_file and not email_valid:
    st.warning("⚠️ Veuillez saisir un e-mail valide pour débloquer l'ajout.")

if up_file and email_valid:
    try:
        df_up = pd.read_csv(up_file, sep=None, engine='python', dtype={C_INSEE: str}, encoding='utf-8-sig')
        df_up.columns = df_up.columns.str.strip()

        if C_INSEE in df_up.columns and C_NOM_OFFICIEL in df_up.columns:
            if st.button(f"🔄 Appliquer en tant que '{C_NOUVEAU_NOM}'"):
                
                # Préparation des données de mise à jour
                df_staging = pd.DataFrame({
                    C_INSEE: df_up[C_INSEE],
                    "tmp_name": df_up[C_NOM_OFFICIEL],
                    "tmp_contact": contact_mail
                })

                # Fusion : 'outer' pour l'admin (ajoute des lignes), 'left' pour l'utilisateur
                mode = 'outer' if is_admin else 'left'
                merged = pd.merge(st.session_state.df_main, df_staging, on=C_INSEE, how=mode)

                # Transfert des valeurs vers les colonnes permanentes
                merged[C_NOUVEAU_NOM] = merged["tmp_name"].combine_first(merged[C_NOUVEAU_NOM])
                merged[C_CONTACT] = merged["tmp_contact"].combine_first(merged[C_CONTACT])
                
                # Nettoyage
                merged.drop(columns=["tmp_name", "tmp_contact"], inplace=True)
                merged.fillna("", inplace=True)
                st.session_state.df_main = merged
                
                st.success("✅ Proposition enregistrée en attente de validation.")
                st.rerun()
        else:
            st.error(f"❌ Colonnes '{C_INSEE}' ou '{C_NOM_OFFICIEL}' manquantes.")
    except Exception as e:
        st.error(f"⚠️ Erreur : {e}")

# --- 5. VISUALISATION / ÉDITION ---
st.divider()
has_updates = (st.session_state.df_main[C_CONTACT] != "").any()

if is_admin:
    st.subheader("🔐 Espace Administration (Édition Directe)")
    if has_updates:
        st.error("📢 Des modifications sont en attente de validation.")
    
    # Éditeur dynamique
    edited_df = st.data_editor(st.session_state.df_main, use_container_width=True, num_rows="dynamic")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Sauvegarder les modifications manuelles"):
            st.session_state.df_main = edited_df
            st.success("Enregistré.")
            st.rerun()
    with c2:
        if has_updates and st.button("✅ Valider et écraser les noms officiels"):
            mask = st.session_state.df_main[C_NOUVEAU_NOM] != ""
            st.session_state.df_main.loc[mask, C_NOM_OFFICIEL] = st.session_state.df_main.loc[mask, C_NOUVEAU_NOM]
            st.session_state.df_main[C_NOUVEAU_NOM] = ""
            st.session_state.df_main[C_CONTACT] = ""
            st.balloons()
            st.rerun()
else:
    st.subheader("📊 Référentiel et évolutions en cours")
    if has_updates:
        st.info("ℹ️ Les lignes contenant un contact indiquent une modification en cours de validation.")
    st.dataframe(df_display, use_container_width=True)

# --- 6. EXPORT ---
st.divider()
st.subheader("📥 Exportation")
all_cols = df_display.columns.tolist()

# Définition des colonnes par défaut : on EXCLUT le contact ici
default_cols = [C_INSEE, "Libellé Région", "Libellé Département", C_NOM_OFFICIEL, C_NOUVEAU_NOM]
current_default = [c for c in default_cols if c in all_cols]

sel_cols = st.multiselect("Sélectionnez les colonnes à exporter", options=all_cols, default=current_default)

if sel_cols:
    csv_data = df_display[sel_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("⬇️ Télécharger le CSV", data=csv_data, file_name="export_clpe.csv", mime="text/csv")
