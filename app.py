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
        "Code Région": ["11", "24", "44", "32"],
        "Libellé Région": ["Île-de-France", "Centre-Val de Loire", "Grand Est", "Hauts-de-France"],
        "Code Département": ["075", "028", "067", "059"],
        "Libellé Département": ["Paris", "Eure-et-Loir", "Bas-Rhin", "Nord"],
        C_INSEE: ["75001", "28001", "67001", "59001"],
        C_NOM_OFFICIEL: ["Comité Paris Centre", "Comité Chartres", "Comité Strasbourg", "Comité Lille"],
        C_NOUVEAU_NOM: ["", "Comité Chartres Agglo", "", ""], 
        C_CONTACT: ["", "jean.dupont@test.fr", "", ""]
    }
    st.session_state.df_main = pd.DataFrame(data)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 2. BARRE LATÉRALE (CONNEXION & FILTRES) ---
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
    
    # NOUVEAU : Filtre par Contact
    contacts_dispo = sorted([c for c in st.session_state.df_main[C_CONTACT].unique() if c != ""])
    contact_filter = st.multiselect("Filtrer par Contact (Auteur)", options=contacts_dispo)

# --- 3. LOGIQUE DE FILTRAGE ---
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

with st.expander("❓ Guide : Format et règles de gestion"):
    st.markdown(f"""
    - **Fichier CSV** : 2 colonnes minimum (1: Code INSEE, 2: Nouveau Nom).
    - **Valeurs vides** : Si le nom est vide dans votre fichier, il apparaîtra comme vide dans la table (demande de suppression).
    - **Utilisateur** : Met à jour les communes existantes.
    - **Admin** : Peut ajouter de nouvelles communes via l'import.
    """)

col_mail, col_file = st.columns([1, 2])
with col_mail:
    contact_mail = st.text_input("📧 Votre e-mail de contact :", placeholder="nom@exemple.fr")
    email_valid = bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact_mail)) if contact_mail else False

with col_file:
    up_file = st.file_uploader("Charger le fichier CSV", type="csv")

if up_file and email_valid:
    try:
        # On lit tout en string pour garder les codes INSEE intacts
        df_up = pd.read_csv(up_file, sep=None, engine='python', dtype=str, encoding='utf-8-sig')
        
        if len(df_up.columns) >= 2:
            # On prend les 2 premières colonnes peu importe leurs noms
            df_up = df_up.iloc[:, [0, 1]].copy()
            df_up.columns = [C_INSEE, "tmp_name"]
            
            # Traitement des noms vides (on force en string vide plutôt qu'en NaN)
            df_up["tmp_name"] = df_up["tmp_name"].fillna("")
            
            if st.button(f"🔄 Appliquer en tant que '{C_NOUVEAU_NOM}'"):
                df_staging = df_up.copy()
                df_staging["tmp_contact"] = contact_mail

                mode = 'outer' if is_admin else 'left'
                merged = pd.merge(st.session_state.df_main, df_staging, on=C_INSEE, how=mode)

                # Si une ligne était dans l'upload (tmp_contact non nul), on écrase avec les nouvelles valeurs
                # même si tmp_name est vide.
                mask = merged["tmp_contact"].notna()
                merged.loc[mask, C_NOUVEAU_NOM] = merged.loc[mask, "tmp_name"]
                merged.loc[mask, C_CONTACT] = merged.loc[mask, "tmp_contact"]
                
                merged.drop(columns=["tmp_name", "tmp_contact"], inplace=True)
                merged.fillna("", inplace=True)
                st.session_state.df_main = merged
                
                st.success("✅ Proposition enregistrée.")
                st.rerun()
        else:
            st.error("Le fichier doit contenir 2 colonnes.")
    except Exception as e:
        st.error(f"Erreur : {e}")

# --- 5. VISUALISATION ET ACTIONS ADMIN ---
st.divider()
has_updates = (st.session_state.df_main[C_CONTACT] != "").any()

if is_admin:
    st.subheader("✍️ Zone d'Édition et Validation (Admin)")
    
    # Rappel du filtre actif pour la purge
    if (regions or depts or contact_filter):
        st.info(f"Filtre actif : {len(df_display)} lignes sélectionnées.")

    edited_df = st.data_editor(st.session_state.df_main, use_container_width=True, num_rows="dynamic")
    
    # BOUTONS D'ACTION
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Sauvegarder saisies manuelles", use_container_width=True):
            st.session_state.df_main = edited_df
            st.success("Enregistré.")
            st.rerun()
    
    with c2:
        # NOUVEAU : Bouton de purge des propositions filtrées
        if st.button("🗑️ Purger les propositions filtrées", use_container_width=True, help="Efface le 'Nouveau Nom' et le 'Contact' pour les lignes affichées."):
            indices_a_purger = df_display.index
            st.session_state.df_main.loc[indices_a_purger, [C_NOUVEAU_NOM, C_CONTACT]] = ""
            st.warning("Propositions purgées pour la sélection.")
            st.rerun()

    with c3:
        if st.button("✅ Valider et Écraser (Définitif)", use_container_width=True, type="primary"):
            mask = st.session_state.df_main[C_NOUVEAU_NOM] != ""
            st.session_state.df_main.loc[mask, C_NOM_OFFICIEL] = st.session_state.df_main.loc[mask, C_NOUVEAU_NOM]
            st.session_state.df_main[[C_NOUVEAU_NOM, C_CONTACT]] = ""
            st.balloons()
            st.rerun()
else:
    st.subheader("📊 Référentiel CLPE")
    st.dataframe(df_display, use_container_width=True)

# --- 6. EXPORTATION ---
st.divider()
st.subheader("📥 Exportation")

all_cols = df_display.columns.tolist()
# Par défaut : uniquement Insee et Nom Officiel
default_export = [C_INSEE, C_NOM_OFFICIEL]

sel_cols = st.multiselect(
    "Colonnes à inclure :", 
    options=all_cols, 
    default=[c for c in default_export if c in all_cols]
)

if sel_cols:
    csv_data = df_display[sel_cols].to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("⬇️ Télécharger le CSV", data=csv_data, file_name="referentiel_clpe.csv", mime="text/csv")
