import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF

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

COLONNES_SHEET = [
    "ID_OT", "Date", "Cadre", "Email_Eleve", "Classe", "Machine",
    "Type", "Mesures_Elec", "Mesures_Pneu", "Compteur_h",
    "Anomalies", "Correction_Effectuee", "Etat_Machine", "Statut"
]

# ==============================================================================
# GÉNÉRATION DU RAPPORT PDF (POUR DOSSIER UAA5 ÉLÈVE)
# ==============================================================================
def nettoyer_pdf(texte):
    """Nettoie les emojis et caractères spéciaux pour compatibilité PDF latin-1."""
    if texte is None:
        return ""
    s = str(texte)
    remplacements = {
        "🟢": "[OK]",
        "🟠": "[RESERVE]",
        "🔴": "[HORS SERVICE]",
        "⏳": "[EN ATTENTE]",
        "✔️": "[VALIDE]",
        "⚠️": "[!]",
        "—": "-",
        "–": "-",
        "’": "'",
        "œ": "oe",
        "Œ": "OE"
    }
    for k, v in remplacements.items():
        s = s.replace(k, v)
    return s.encode("latin-1", errors="replace").decode("latin-1")


def generer_pdf_ot(ot):
    """Génère un fichier PDF A4 formaté pour le dossier UAA5 de l'élève."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Bandeau d'en-tête bleu industriel
    pdf.set_fill_color(27, 54, 93)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 11, nettoyer_pdf("RAPPORT D'INTERVENTION GMAO - MAINTENANCE PREVENTIVE"), ln=True, align="C", fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, nettoyer_pdf("Option EMI - College Notre-Dame Dinant - Mr PIRET (Referentiel UAA5)"), ln=True, align="C", fill=True)
    pdf.ln(6)

    # Identification de l'OT
    pdf.set_text_color(27, 54, 93)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, nettoyer_pdf(f"ORDRE DE TRAVAIL : {ot.get('ID_OT', '')}"), ln=True)
    pdf.set_draw_color(27, 54, 93)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_text_color(30, 30, 30)
    infos = [
        ("Date d'intervention :", ot.get("Date", "")),
        ("Equipement concerne :", ot.get("Machine", "")),
        ("Cadre pedagogique :", ot.get("Cadre", "")),
        ("Intervenant (Eleve) :", f"{ot.get('Email_Eleve', '')}  (Classe : {ot.get('Classe', '')})"),
        ("Compteur horaire :", str(ot.get("Compteur_h", "N/A"))),
        ("Validation GMAO :", ot.get("Statut", ""))
    ]
    for label, val in infos:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(52, 7, nettoyer_pdf(label), border=0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, nettoyer_pdf(val), ln=True)

    pdf.ln(4)

    # Section Relevés métrologiques
    pdf.set_text_color(27, 54, 93)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, nettoyer_pdf("1. RELEVES METROLOGIQUES & CONTROLES"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, nettoyer_pdf("Controles electriques et thermiques :"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, nettoyer_pdf(ot.get("Mesures_Elec", "N/A")), border=1)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, nettoyer_pdf("Controles pneumatiques et hydrauliques :"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, nettoyer_pdf(ot.get("Mesures_Pneu", "N/A")), border=1)
    pdf.ln(5)

    # Section Diagnostic, Anomalies et Remise en service
    pdf.set_text_color(27, 54, 93)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, nettoyer_pdf("2. DIAGNOSTIC, ACTION CORRECTIVE & REMISE EN SERVICE"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, nettoyer_pdf("Anomalie(s) constatee(s) / Pieces a prevoir :"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, nettoyer_pdf(ot.get("Anomalies", "RAS")), border=1)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, nettoyer_pdf("Action corrective realisee sur place :"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, nettoyer_pdf(ot.get("Correction_Effectuee", "Aucune")), border=1)
    pdf.ln(3)

    pdf.set_fill_color(235, 242, 248)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 9, nettoyer_pdf(f"  STATUT FINAL DE L'EQUIPEMENT : {ot.get('Etat_Machine', '')}"), border=1, ln=True, fill=True)
    pdf.ln(10)

    # Encadrés de signatures pour le dossier papier
    y_sig = pdf.get_y()
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(90, 22, nettoyer_pdf(" Signature de l'eleve :"), border=1, align="L")
    pdf.cell(10, 22, "", border=0)
    pdf.cell(90, 22, nettoyer_pdf(" Visa Professeur (Mr Piret) - Dossier UAA5 :"), border=1, align="L")

    return bytes(pdf.output())


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
        st.session_state.ordres_travail = []
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
        ligne = [nouvel_ot.get(col, "") for col in COLONNES_SHEET]
        sheet.append_row(ligne)
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
        headers = sheet.row_values(1)
        if cell and "Statut" in headers:
            col_statut = headers.index("Statut") + 1
            sheet.update_cell(cell.row, col_statut, "🟢 Validé par Prof")
    else:
        for ot in st.session_state.ordres_travail:
            if ot["ID_OT"] == id_ot:
                ot["Statut"] = "🟢 Validé par Prof"


ordres_travail, mode_gsheet = charger_donnees()

# Détermination dynamique de l'état actuel de la machine selon le dernier OT
etat_actuel_machine = "🟢 Opérationnel"
if ordres_travail:
    dernier_etat = str(ordres_travail[-1].get("Etat_Machine", ""))
    if "Hors service" in dernier_etat:
        etat_actuel_machine = "🔴 Hors service / Consigné"
    elif "réserve" in dernier_etat:
        etat_actuel_machine = "🟠 Opérationnel (Réserve)"
    else:
        etat_actuel_machine = "🟢 Opérationnel"

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
            "📊 Tableau de bord & Rapports PDF",
            "🛠️ Maintenance Préventive (UAA5)",
            "🚨 Maintenance Curative (À venir)",
            "🔌 Réalisation & Câblage (À venir)",
            "🔐 Validation Professeur"
        ]
    )

    st.divider()
    st.subheader("Équipement UAA5")
    st.markdown("**UAA5-CANARDS-01** : Course de canards")
    st.markdown(f"État actuel : **{etat_actuel_machine}**")

# ==============================================================================
# VUE 1 : TABLEAU DE BORD & CONSULTATION / EXPORT PDF DES OT
# ==============================================================================
if menu == "📊 Tableau de bord & Rapports PDF":
    st.header("Tableau de bord de maintenance — Course de canards")

    nb_total = len(ordres_travail)
    nb_attente = sum(1 for x in ordres_travail if "attente" in str(x.get("Statut", "")))
    nb_valides = sum(1 for x in ordres_travail if "Validé" in str(x.get("Statut", "")))
    nb_corrigees = sum(1 for x in ordres_travail if "corrigée" in str(x.get("Etat_Machine", "")))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ordres de Travail (Total)", nb_total)
    c2.metric("En attente validation prof", nb_attente)
    c3.metric("OT Validés", nb_valides)
    c4.metric("Anomalies détectées & corrigées", nb_corrigees)

    st.divider()

    if not ordres_travail:
        st.info("Aucun Ordre de Travail enregistré pour le moment.")
    else:
        # 1. FICHE DÉTAILLÉE & EXPORT PDF (SANS ASCENSEUR HORIZONTAL)
        st.subheader("📄 Consulter ou imprimer une fiche d'intervention (Dossier UAA5)")

        options_ot = [
            f"{ot.get('ID_OT', '')} — {ot.get('Email_Eleve', '')} ({ot.get('Date', '')}) [{ot.get('Statut', '')}]"
            for ot in ordres_travail
        ]
        # Sélectionne automatiquement l'intervention la plus récente
        choix_index = st.selectbox(
            "Sélectionnez l'intervention à afficher :",
            range(len(options_ot)),
            index=len(options_ot) - 1,
            format_func=lambda i: options_ot[i]
        )
        ot_sel = ordres_travail[choix_index]

        with st.container(border=True):
            top_l, top_r = st.columns([3, 1])
            with top_l:
                st.markdown(f"### {ot_sel.get('ID_OT', '')} • {ot_sel.get('Machine', '')}")
                st.markdown(
                    f"**Élève :** `{ot_sel.get('Email_Eleve', '')}` ({ot_sel.get('Classe', '')})  |  "
                    f"**Date :** {ot_sel.get('Date', '')}  |  "
                    f"**Cadre :** {ot_sel.get('Cadre', '')}"
                )
            with top_r:
                pdf_bytes = generer_pdf_ot(ot_sel)
                nom_fichier = f"{ot_sel.get('ID_OT', 'OT')}_{ot_sel.get('Email_Eleve', 'eleve').split('@')[0]}.pdf"
                st.download_button(
                    label="📄 Télécharger PDF (UAA5)",
                    data=pdf_bytes,
                    file_name=nom_fichier,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )

            st.divider()

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown("**⚡ Relevés Électriques & Thermiques**")
                st.info(ot_sel.get("Mesures_Elec", "N/A"))
            with col_m2:
                st.markdown("**💨 Relevés Pneumatiques & Compteur**")
                st.info(f"{ot_sel.get('Mesures_Pneu', 'N/A')}  |  **Compteur :** {ot_sel.get('Compteur_h', 'N/A')}")

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown("**🔍 Anomalie(s) constatée(s)**")
                anom = str(ot_sel.get("Anomalies", "RAS"))
                if anom == "RAS":
                    st.success("RAS (Aucune anomalie détectée)")
                else:
                    st.warning(anom)
            with col_d2:
                st.markdown("**🔧 Action corrective réalisée sur place**")
                st.write(ot_sel.get("Correction_Effectuee", "Aucune"))

            st.markdown(f"**État final de la machine :** {ot_sel.get('Etat_Machine', 'N/A')}   •   **Validation :** {ot_sel.get('Statut', '')}")

        st.divider()

        # 2. VUE SYNTHÉTIQUE COMPACTE (TIENS SUR L'ÉCRAN SANS SCROLL)
        st.subheader("📋 Liste synthétique des interventions")
        df_complet = pd.DataFrame(ordres_travail)
        cols_compactes = [c for c in ["ID_OT", "Date", "Email_Eleve", "Classe", "Cadre", "Statut"] if c in df_complet.columns]
        st.dataframe(df_complet[cols_compactes], use_container_width=True, hide_index=True)

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

    # --- BILAN : ANOMALIES, CORRECTION & STATUT FINAL ---
    with st.container(border=True):
        st.subheader("📝 Bilan d'intervention, Correction & Remise en service")

        if anomalies_detectees:
            st.warning(f"⚠️ **{len(anomalies_detectees)} anomalie(s) détectée(s) durant le contrôle :** {', '.join(anomalies_detectees)}")
            st.info("Décrivez ci-dessous l'anomalie constatée puis l'action corrective que vous avez réalisée pour remettre l'équipement en service.")

        col_anom, col_corr = st.columns(2)
        with col_anom:
            anomalies_txt = st.text_area(
                "1. ANOMALIES CONSTATÉES / PIÈCES À PRÉVOIR",
                placeholder="Ex: Capteur optique S2 encrassé et désaligné + pression FRL à 4,5 bar au lieu de 6 bar."
            )
        with col_corr:
            correction_txt = st.text_area(
                "2. ACTION CORRECTIVE RÉALISÉE SUR PLACE",
                placeholder="Ex: Nettoyage et réalignement du capteur S2 + réglage du régulateur FRL à 6,0 bar. Essai fonctionnel OK."
            )

        options_etat = [
            "🟢 Opérationnel (Aucune anomalie)",
            "🟢 Opérationnel (Anomalie(s) détectée(s) et corrigée(s))",
            "🟠 Opérationnel avec réserve (Pièce à prévoir)",
            "🔴 Hors service / Consigné (Anomalie non résolue)"
        ]
        index_defaut = 1 if anomalies_detectees else 0
        etat_machine_final = st.selectbox(
            "3. STATUT FINAL DE L'ÉQUIPEMENT APRÈS INTERVENTION",
            options_etat,
            index=index_defaut
        )

        if st.button("✅ Clôturer l'intervention et demander la validation professeur", type="primary", use_container_width=True):
            if not email_eleve or "@" not in email_eleve:
                st.warning("Veuillez entrer votre adresse e-mail scolaire valide.")
            elif (anomalies_detectees or "corrigée" in etat_machine_final or "réserve" in etat_machine_final or "Hors service" in etat_machine_final) and not anomalies_txt.strip():
                st.error("Veuillez décrire l'anomalie constatée dans la case 1.")
            elif ("corrigée" in etat_machine_final) and not correction_txt.strip():
                st.error("Vous avez indiqué que l'anomalie a été corrigée : décrivez obligatoirement l'action corrective effectuée dans la case 2.")
            else:
                nouvel_id = f"OT-2026-{len(ordres_travail) + 1:03d}"
                resume_anomalies = anomalies_txt.strip() if anomalies_txt.strip() else "RAS"
                if anomalies_detectees:
                    resume_anomalies = f"[{', '.join(anomalies_detectees)}] {resume_anomalies}"

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
                    "Anomalies": resume_anomalies,
                    "Correction_Effectuee": correction_txt.strip() if correction_txt.strip() else "Aucune (RAS)",
                    "Etat_Machine": etat_machine_final,
                    "Statut": "⏳ En attente validation prof"
                }
                enregistrer_ot(nouvel_ot, mode_gsheet)
                st.success(f"Rapport **{nouvel_id}** enregistré ({etat_machine_final}) ! Appelez Mr Piret pour validation.")

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
                        st.write(f"**Anomalie(s) détectée(s) :** {ot.get('Anomalies', 'RAS')}")
                        st.write(f"**Action corrective réalisée :** {ot.get('Correction_Effectuee', 'Aucune')}")
                        st.write(f"**État final déclaré :** {ot.get('Etat_Machine', 'N/A')}")
                    with c2:
                        if st.button("✔️ Valider (Prof)", key=f"btn_{ot['ID_OT']}", type="primary", use_container_width=True):
                            valider_ot_gsheet(ot["ID_OT"], mode_gsheet)
                            st.toast(f"Ordre de travail {ot['ID_OT']} validé !")
                            st.rerun()
    elif pin:
        st.error("Code PIN incorrect.")
