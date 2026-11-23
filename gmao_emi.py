import streamlit as st
import pandas as pd
from datetime import datetime

# ==============================================================================
# CONFIGURATION DE LA PAGE
# ==============================================================================
st.set_page_config(
    page_title="GMAO Atelier EMI - Course de canards",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CODE_PIN_PROF = "1234"  # <-- Modifiez votre code secret professeur ici
SPREADSHEET_ID = "1oD2UwgkRhyqv9tRd3DMcF3Y20deMAa3Y8hoKgHJ5AB8"
MACHINE_UAA5 = "Course de canards (UAA5-CANARDS-01)"

# ==============================================================================
# CONNEXION GOOGLE SHEETS (AVEC REPLI EN MÉMOIRE LOCALE)
# ==============================================================================
def charger_donnees():
    """Charge les OT depuis Google Sheets si configuré, sinon utilise la session."""
    if "gsheets" in st.secrets:
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scopes)
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SPREADSHEET_ID).sheet1
            records = sheet.get_all_records()
            return records, True
        except Exception as e:
            st.sidebar.warning(f"Mode hors-ligne actif (Erreur Sheets : {e})")

    if "ordres_travail" not in st.session_state:
        st.session_state.ordres_travail = [
            {
                "ID_OT": "OT-2026-001",
                "Date": "2026-11-23 09:15",
                "Cadre": "Formatif (Entraînement)",
                "Email_Eleve": "dupont.martin@ecole.be",
                "Classe": "6TQ",
                "Machine": MACHINE_UAA5,
                "Type": "Maintenance Préventive",
                "Mesures_Elec": "L1-L2:401V | L2-L3:400V | L3-L1:402V | 24V:24.1V | T°:22°C",
                "Mesures_Pneu": "Réseau:6.5 bar | FRL:6.0 bar | Purge:Oui",
                "Compteur_h": "1420 h",
                "Anomalies": "RAS - Filtre armoire dépoussiéré",
                "Statut": "⏳ En attente validation prof"
            }
        ]
    return st.session_state.ordres_travail, False


def enregistrer_ot(nouvel_ot, connecte_gsheet):
    """Ajoute un nouvel Ordre de Travail dans Google Sheets ou en session."""
    if connecte_gsheet:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        sheet.append_row(list(nouvel_ot.values()))
    else:
        st.session_state.ordres_travail.append(nouvel_ot)


def valider_ot_gsheet(id_ot, connecte_gsheet):
    """Met à jour le statut de validation professeur."""
    if connecte_gsheet:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        cell = sheet.find(id_ot)
        if cell:
            # La colonne Statut est la 12e colonne (L)
            sheet.update_cell(cell.row, 12, "🟢 Validé par Prof")
    else:
        for ot in st.session_state.ordres_travail:
            if ot["ID_OT"] == id_ot:
                ot["Statut"] = "🟢 Validé par Prof"


ordres_travail, mode_gsheet = charger_donnees()

# ==============================================================================
# BARRE LATÉRALE : NAVIGATION & ÉTAT DU PARC
# ==============================================================================
with st.sidebar:
    st.title("⚙️ GMAO ATELIER EMI")
    st.caption("Option EMI • Collège Notre-Dame Dinant • Mr PIRET")
    if mode_gsheet:
        st.success("🟢 Base Google Sheets connectée")
    else:
        st.info("🟡 Mode démonstration (Mémoire locale)")
    st.divider()

    menu = st.radio(
        "Navigation",
        [
            "📊 Tableau de bord & Parc",
            "🛠️ Maintenance Préventive (UAA5)",
            "🚨 Maintenance Curative (À venir)",
            "🔌 Réalisation & Câblage (À venir)",
            "🔐 Validation Professeur"
        ]
    )

    st.divider()
    st.subheader("Équipement UAA5")
    st.markdown("🟢 **UAA5-CANARDS-01** : Course de canards")

# ==============================================================================
# VUE 1 : TABLEAU DE BORD & REGISTRE DES ORDRES DE TRAVAIL
# ==============================================================================
if menu == "📊 Tableau de bord & Parc":
    st.header("Tableau de bord de maintenance — Course de canards")

    nb_total = len(ordres_travail)
    nb_attente = sum(1 for x in ordres_travail if "attente" in str(x.get("Statut", "")))
    nb_valides = sum(1 for x in ordres_travail if "Validé" in str(x.get("Statut", "")))
    nb_formatif = sum(1 for x in ordres_travail if "Formatif" in str(x.get("Cadre", "")))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ordres de Travail (Total)", nb_total)
    c2.metric("En attente validation prof", nb_attente)
    c3.metric("OT Validés", nb_valides)
    c4.metric("Interventions Formatives", nb_formatif)

    st.divider()
    st.subheader("📋 Historique des interventions (Registre GMAO)")
    if ordres_travail:
        df = pd.DataFrame(ordres_travail)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun Ordre de Travail enregistré pour le moment.")

# ==============================================================================
# VUE 2 : MAINTENANCE PRÉVENTIVE (FICHE UAA5)
# ==============================================================================
elif menu == "🛠️ Maintenance Préventive (UAA5)":
    st.header("Fiche d'Activité : Maintenance Préventive (UAA5)")
    st.caption("Option EMI — Collège Notre-Dame Dinant — Mr PIRET")

    # --- EN-TÊTE IDENTIFICATION ---
    with st.container(border=True):
        st.subheader("Identification de l'Ordre de Travail")
        col_a, col_b, col_c = st.columns([2, 1, 2])
        email_eleve = col_a.text_input("E-mail Chromebook (prenom.nom@...)", placeholder="martin.dupont@ecole.be")
        classe = col_b.selectbox("Classe", ["6TQ", "5TQ", "4TQ"])
        cadre = col_c.selectbox("Cadre de l'activité", ["Formatif (Entraînement)", "Certificatif (Évaluation UAA5)"])

        col_d, col_e = st.columns([3, 1])
        machine = col_d.selectbox("Équipement / Machine contrôlée", [MACHINE_UAA5])
        compteur_h = col_e.text_input("Compteur horaire (h)", placeholder="Ex: 1450")

    def ligne_gamme(label, key):
        c_lbl, c_btn = st.columns([3, 2])
        c_lbl.markdown(f"**{label}**")
        choix = c_btn.radio(
            label,
            ["Conforme", "Anomalie", "N/A"],
            horizontal=True,
            label_visibility="collapsed",
            key=key
        )
        return choix

    anomalies_detectees = []

    # --- 1. NETTOYAGE ---
    with st.expander("1. NETTOYAGE", expanded=True):
        for lbl, k in [
            ("Ensemble : coffret et machine", "net_1"),
            ("Actionneurs (moteurs, vérins, etc.)", "net_2"),
            ("Capteurs : têtes et réflecteurs", "net_3")
        ]:
            if ligne_gamme(lbl, k) == "Anomalie":
                anomalies_detectees.append(lbl)

    # --- 2. CONTRÔLES ET TESTS (ÉLECTRIQUE ET AUTOMATISME) ---
    with st.expander("2. CONTRÔLES ET TESTS (Électrique et Automatisme)", expanded=True):
        for lbl, k in [
            ("Câbles et réseaux : vérifier câbles et tensions", "elec_1"),
            ("Actionneurs et capteurs : tester en mode MANU ou via HMI", "elec_2"),
            ("Mode Auto et diagnostic : vérifier fonctionnement en Auto et liste d'erreurs HMI", "elec_3"),
            ("Armoire : vérifier ventilateurs, filtres et voyants en façade", "elec_4"),
            ("Thermostat d'armoire : vérifier le réglage (selon données techniques)", "elec_5"),
            ("Température : contrôler l'absence d'échauffement anormal", "elec_6")
        ]:
            if ligne_gamme(lbl, k) == "Anomalie":
                anomalies_detectees.append(lbl)

        st.markdown("---")
        st.markdown("##### 📏 Relevés électriques et thermiques")
        m1, m2, m3, m4 = st.columns(4)
        u_l1l2 = m1.number_input("Tension L1-L2 (V)", value=400.0, step=0.5)
        u_l2l3 = m2.number_input("Tension L2-L3 (V)", value=400.0, step=0.5)
        u_l3l1 = m3.number_input("Tension L3-L1 (V)", value=400.0, step=0.5)
        u_24v = m4.number_input("Tension commande 24V DC (V)", value=24.0, step=0.1)

        t1, t2, t3 = st.columns(3)
        t_thermostat = t1.number_input("Réglage thermostat (°C)", value=35, step=1)
        t_armoire = t2.number_input("Température mesurée (°C)", value=22, step=1)
        defauts_hmi = t3.text_input("Liste d'erreurs / défauts HMI", value="Aucun défaut")

    # --- 3. MÉCANIQUE ET SERRAGE ---
    with st.expander("3. MÉCANIQUE ET SERRAGE", expanded=True):
        for lbl, k in [
            ("Serrage (vis) : borniers, fixations, cosses (tournevis dynamométrique)", "meca_1"),
            ("Vérification des bornes de la plaque à bornes MAT", "meca_2"),
            ("Transmissions : état/tension courroies, chaînes, accouplements et roulements", "meca_3")
        ]:
            if ligne_gamme(lbl, k) == "Anomalie":
                anomalies_detectees.append(lbl)

        obs_meca = st.text_input("Observations mécaniques / Couple de serrage", placeholder="Ex: Resserrage borniers à 2,5 Nm OK")

    # --- 4. PNEUMATIQUE ET HYDRAULIQUE ---
    with st.expander("4. PNEUMATIQUE ET HYDRAULIQUE", expanded=True):
        for lbl, k in [
            ("Étanchéité : vérifier les circuits pneumatiques et hydrauliques", "pneu_1"),
            ("Unité de conditionnement d'air (FRL) : huile, filtre et condensats", "pneu_2"),
            ("Pression : vérifier et adapter selon les données techniques", "pneu_3")
        ]:
            if ligne_gamme(lbl, k) == "Anomalie":
                anomalies_detectees.append(lbl)

        st.markdown("---")
        st.markdown("##### 📏 Relevés pneumatiques")
        p1, p2, p3 = st.columns(3)
        p_reseau = p1.number_input("Pression réseau (bar)", value=6.5, step=0.1)
        p_frl = p2.number_input("Pression régulée FRL (bar)", value=6.0, step=0.1)
        purge_ok = p3.selectbox("Purge des condensats effectuée ?", ["Oui", "Non", "N/A"])

    # --- 5. SÉCURITÉ ET REMPLACEMENT ---
    with st.expander("5. SÉCURITÉ ET REMPLACEMENT", expanded=True):
        for lbl, k in [
            ("Consignation / VAT : mise en sécurité avant intervention électrique", "secu_1"),
            ("Tester l'ARU (arrêt d'urgence) et l'interrupteur différentiel (bouton test)", "secu_2"),
            ("Éclairage de secours : contrôler le fonctionnement et la batterie", "secu_3"),
            ("Protection mécanique : plastron, carters, etc.", "secu_4"),
            ("Remplacement périodique : changer des composants après X h d'utilisation", "secu_5")
        ]:
            if ligne_gamme(lbl, k) == "Anomalie":
                anomalies_detectees.append(lbl)

        pieces_remp = st.text_input("Composants remplacés (Réf + Qté)", placeholder="Ex: Aucune ou Filtre armoire (x1)")

    # --- ANOMALIES & SOUMISSION ---
    with st.container(border=True):
        st.subheader("📝 Rapport d'intervention")
        if anomalies_detectees:
            st.error(f"⚠️ {len(anomalies_detectees)} point(s) en anomalie : {', '.join(anomalies_detectees)}")

        anomalies_txt = st.text_area(
            "ANOMALIES CONSTATÉES / PIÈCES À PRÉVOIR",
            placeholder="Notez ici les anomalies détectées, les pièces à prévoir ou vos remarques techniques..."
        )

        if st.button("✅ Enregistrer le rapport GMAO (Demande validation professeur)", type="primary", use_container_width=True):
            if not email_eleve or "@" not in email_eleve:
                st.warning("Veuillez entrer votre adresse e-mail scolaire valide.")
            elif anomalies_detectees and not anomalies_txt.strip():
                st.error("Vous avez signalé une anomalie dans la gamme : veuillez obligatoirement la décrire ci-dessus.")
            else:
                nouvel_id = f"OT-2026-{len(ordres_travail) + 1:03d}"
                nouvel_ot = {
                    "ID_OT": nouvel_id,
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Cadre": cadre,
                    "Email_Eleve": email_eleve.strip().lower(),
                    "Classe": classe,
                    "Machine": machine,
                    "Type": "Maintenance Préventive",
                    "Mesures_Elec": f"L1-L2:{u_l1l2}V | L2-L3:{u_l2l3}V | L3-L1:{u_l3l1}V | 24V:{u_24v}V | T°:{t_armoire}°C (Th:{t_thermostat}°C) | HMI:{defauts_hmi}",
                    "Mesures_Pneu": f"Réseau:{p_reseau} bar | FRL:{p_frl} bar | Purge:{purge_ok}",
                    "Compteur_h": f"{compteur_h} h" if compteur_h else "N/A",
                    "Anomalies": anomalies_txt.strip() if anomalies_txt.strip() else "RAS",
                    "Statut": "⏳ En attente validation prof"
                }
                enregistrer_ot(nouvel_ot, mode_gsheet)
                st.success(f"Rapport **{nouvel_id}** enregistré avec succès ! Présentez votre poste à Mr Piret pour validation.")

# ==============================================================================
# VUES EN ATTENTE : CURATIF & RÉALISATION
# ==============================================================================
elif menu == "🚨 Maintenance Curative (À venir)":
    st.header("Maintenance Curative (Dépannage)")
    st.info("Ce module sera activé une fois la gamme préventive testée avec la classe.")

elif menu == "🔌 Réalisation & Câblage (À venir)":
    st.header("Réalisation / Conception / Montages éphémères")
    st.info("Ce module intégrera les codes exercices (EX/SA/TP), le câblage et le paramétrage variateur/API.")

# ==============================================================================
# VUE 5 : VALIDATION PROFESSEUR
# ==============================================================================
elif menu == "🔐 Validation Professeur":
    st.header("Espace Professeur — Validation des rapports GMAO")
    pin = st.text_input("Code PIN Professeur", type="password")

    if pin == CODE_PIN_PROF:
        st.success("Session professeur déverrouillée.")
        en_attente = [ot for ot in ordres_travail if "attente" in str(ot.get("Statut", ""))]

        if not en_attente:
            st.info("Aucun rapport en attente de validation.")
        else:
            for ot in en_attente:
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"### {ot['ID_OT']} — {ot['Machine']} (`{ot['Cadre']}`)")
                        st.write(f"**Élève :** {ot['Email_Eleve']} ({ot['Classe']}) | **Date :** {ot['Date']}")
                        st.write(f"**Élec/Thermique :** {ot['Mesures_Elec']}")
                        st.write(f"**Pneumatique :** {ot['Mesures_Pneu']} | **Compteur :** {ot['Compteur_h']}")
                        st.write(f"**Anomalies / Pièces :** {ot['Anomalies']}")
                    with c2:
                        if st.button("✔️ Valider (Prof)", key=f"btn_{ot['ID_OT']}", type="primary", use_container_width=True):
                            valider_ot_gsheet(ot["ID_OT"], mode_gsheet)
                            st.toast(f"Ordre de travail {ot['ID_OT']} validé !")
                            st.rerun()
    elif pin:
        st.error("Code PIN incorrect.")
