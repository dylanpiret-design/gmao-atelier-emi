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
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
MACHINE_UAA5 = "Course de canards (UAA5-CANARDS-01)"

COLONNES_SHEET = [
    "ID_OT", "Date_Debut", "Date_Fin", "Cadre", "Email_Eleve", "Classe",
    "Machine", "Type", "LMRA", "Mesures_Elec", "Mesures_Pneu", "Compteur_h",
    "Anomalies", "Correction_Effectuee", "Etat_Machine", "Statut"
]

# ==============================================================================
# UTILITAIRES : EXTRACTION NOM/PRÉNOM & NETTOYAGE PDF
# ==============================================================================
def extraire_identite_email(email):
    """Extrait automatiquement le Prénom et le NOM depuis prenom.nom@domaine."""
    if not email or "@" not in email:
        return "Non renseigné", ""
    identifiant = email.strip().split("@")[0]
    if "." in identifiant:
        morceaux = identifiant.split(".")
        prenom = "-".join(p.capitalize() for p in morceaux[0].split("-"))
        nom = " ".join(morceaux[1:]).upper()
        return prenom, nom
    return identifiant.capitalize(), ""


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
        "→": "->",
        "—": "-",
        "–": "-",
        "’": "'",
        "œ": "oe",
        "Œ": "OE"
    }
    for k, v in remplacements.items():
        s = s.replace(k, v)
    return s.encode("latin-1", errors="replace").decode("latin-1")


# ==============================================================================
# GÉNÉRATION DU RAPPORT PDF A4 (POUR DOSSIER UAA5 ÉLÈVE)
# ==============================================================================
def generer_pdf_ot(ot):
    """Génère un rapport PDF complet sur une page A4 pour le dossier UAA5."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    email = ot.get("Email_Eleve", "")
    prenom, nom = extraire_identite_email(email)
    nom_complet = f"{prenom} {nom}".strip()

    # Extraction Date, Heure début, Heure fin et Durée
    debut_str = str(ot.get("Date_Debut", ""))
    fin_str = str(ot.get("Date_Fin", ""))
    date_jour = debut_str[:10]
    heure_debut = debut_str[11:16] if len(debut_str) >= 16 else "N/A"
    heure_fin = fin_str[11:16] if len(fin_str) >= 16 else "N/A"
    duree_txt = ""
    try:
        dt_deb = datetime.strptime(debut_str[:16], "%Y-%m-%d %H:%M")
        dt_fin = datetime.strptime(fin_str[:16], "%Y-%m-%d %H:%M")
        date_jour = dt_deb.strftime("%d/%m/%Y")
        mins = max(0, int((dt_fin - dt_deb).total_seconds() // 60))
        duree_txt = f" ({mins} min)"
    except Exception:
        pass

    # --- EN-TÊTE ---
    pdf.set_fill_color(27, 54, 93)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12.5)
    pdf.cell(0, 9.5, nettoyer_pdf("RAPPORT D'INTERVENTION GMAO - MAINTENANCE PREVENTIVE"), ln=True, align="C", fill=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, nettoyer_pdf("Option EMI - College Notre-Dame Dinant - Mr PIRET (Referentiel UAA5)"), ln=True, align="C", fill=True)
    pdf.ln(3.5)

    # --- BLOC 1 : IDENTIFICATION & HORODATAGE ---
    pdf.set_text_color(27, 54, 93)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, nettoyer_pdf(f"1. IDENTIFICATION DE L'INTERVENTION ({ot.get('ID_OT', '')})"), ln=True)
    pdf.set_draw_color(27, 54, 93)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_text_color(30, 30, 30)

    def ligne_double(lbl1, val1, lbl2, val2):
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(36, 5.5, nettoyer_pdf(lbl1))
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(59, 5.5, nettoyer_pdf(val1))
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(40, 5.5, nettoyer_pdf(lbl2))
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5.5, nettoyer_pdf(val2), ln=True)

    ligne_double("Eleve :", f"{nom_complet} ({ot.get('Classe', '')})", "Cadre pedagogique :", ot.get("Cadre", ""))
    ligne_double("Adresse e-mail :", email, "Equipement :", ot.get("Machine", ""))
    ligne_double("Date :", date_jour, "Compteur horaire :", str(ot.get("Compteur_h", "N/A")))
    ligne_double("Heure de debut :", heure_debut, "Heure de fin :", f"{heure_fin}{duree_txt}")
    ligne_double("Validation prof :", ot.get("Statut", ""), "", "")
    pdf.ln(2.5)

    # --- BLOC 2 : SÉCURITÉ / LMRA VOLTA ---
    pdf.set_text_color(27, 54, 93)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, nettoyer_pdf("2. ANALYSE DES RISQUES DE DERNIERE MINUTE (LMRA - VOLTA)"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 8.8)
    pdf.multi_cell(0, 5, nettoyer_pdf(ot.get("LMRA", "Non renseignee")), border=1)
    pdf.ln(2.5)

    # --- BLOC 3 : RELEVÉS MÉTROLOGIQUES ---
    pdf.set_text_color(27, 54, 93)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, nettoyer_pdf("3. RELEVES METROLOGIQUES & CONTROLES TECHNIQUES"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 4.8, nettoyer_pdf("Controles electriques et thermiques :"), ln=True)
    pdf.set_font("Helvetica", "", 8.8)
    pdf.multi_cell(0, 5, nettoyer_pdf(ot.get("Mesures_Elec", "N/A")), border=1)
    pdf.ln(1.5)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 4.8, nettoyer_pdf("Controles pneumatiques, hydrauliques et mecaniques :"), ln=True)
    pdf.set_font("Helvetica", "", 8.8)
    pdf.multi_cell(0, 5, nettoyer_pdf(ot.get("Mesures_Pneu", "N/A")), border=1)
    pdf.ln(2.5)

    # --- BLOC 4 : DIAGNOSTIC, CORRECTIONS & STATUT FINAL ---
    pdf.set_text_color(27, 54, 93)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, nettoyer_pdf("4. ANOMALIES CONSTATEES, ACTIONS CORRECTIVES & REMISE EN SERVICE"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 4.8, nettoyer_pdf("Anomalie(s) detectee(s) / Pieces a prevoir :"), ln=True)
    pdf.set_font("Helvetica", "", 8.8)
    pdf.multi_cell(0, 5, nettoyer_pdf(ot.get("Anomalies", "RAS")), border=1)
    pdf.ln(1.5)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 4.8, nettoyer_pdf("Action(s) corrective(s) realisee(s) sur place :"), ln=True)
    pdf.set_font("Helvetica", "", 8.8)
    pdf.multi_cell(0, 5, nettoyer_pdf(ot.get("Correction_Effectuee", "Aucune")), border=1)
    pdf.ln(2.5)

    pdf.set_fill_color(235, 242, 248)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(0, 7.5, nettoyer_pdf(f"  STATUT FINAL DE L'EQUIPEMENT : {ot.get('Etat_Machine', '')}"), border=1, ln=True, fill=True)
    pdf.ln(5)

    # --- SIGNATURES ---
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(90, 19, nettoyer_pdf(f" Signature de l'eleve ({nom_complet}) :"), border=1, align="L")
    pdf.cell(10, 19, "", border=0)
    pdf.cell(90, 19, nettoyer_pdf(" Visa Professeur (Mr Piret) - Dossier UAA5 :"), border=1, align="L")

    return bytes(pdf.output())


# ==============================================================================
# CONNEXION GOOGLE SHEETS (LECTURE/ÉCRITURE EXACTE SUR COLONNES A:P)
# ==============================================================================
def get_gsheet():
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    if sheet.row_values(1) != COLONNES_SHEET:
        sheet.update("A1:P1", [COLONNES_SHEET])
    return sheet


def charger_donnees():
    """Charge toutes les lignes non vides depuis Google Sheets."""
    if "gsheets" in st.secrets:
        try:
            sheet = get_gsheet()
            all_rows = sheet.get_all_values()
            records = []
            for row in all_rows[1:]:
                if any(cell.strip() for cell in row):
                    padded = row + [""] * (len(COLONNES_SHEET) - len(row))
                    records.append(dict(zip(COLONNES_SHEET, padded[:len(COLONNES_SHEET)])))
            return records, True
        except Exception as e:
            st.sidebar.warning(f"Mode hors-ligne actif (Erreur Sheets : {e})")

    if "ordres_travail" not in st.session_state:
        st.session_state.ordres_travail = []
    return st.session_state.ordres_travail, False


def enregistrer_ot(nouvel_ot, connecte_gsheet):
    """Écrit le nouvel OT sur la prochaine ligne libre A:P."""
    if connecte_gsheet:
        sheet = get_gsheet()
        all_rows = sheet.get_all_values()
        next_row = len(all_rows) + 1
        ligne = [str(nouvel_ot.get(col, "")) for col in COLONNES_SHEET]
        sheet.update(f"A{next_row}:P{next_row}", [ligne])
    else:
        st.session_state.ordres_travail.append(nouvel_ot)


def valider_ot_gsheet(id_ot, connecte_gsheet):
    """Met à jour le statut de validation professeur sur la ligne correspondante."""
    if connecte_gsheet:
        sheet = get_gsheet()
        all_rows = sheet.get_all_values()
        col_statut = COLONNES_SHEET.index("Statut") + 1
        for idx, row in enumerate(all_rows):
            if idx > 0 and len(row) > 0 and row[0].strip() == id_ot:
                sheet.update_cell(idx + 1, col_statut, "🟢 Validé par Prof")
                break
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
    head_l, head_r1 = st.columns([5, 1])
    head_l.header("Tableau de bord de maintenance — Course de canards")
    if head_r1.button("🔄 Actualiser", use_container_width=True):
        st.rerun()

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
        st.subheader("📄 Consulter ou imprimer une fiche d'intervention (Dossier UAA5)")

        options_ot = []
        for ot in ordres_travail:
            p, n = extraire_identite_email(ot.get("Email_Eleve", ""))
            identite = f"{p} {n}".strip() if n else ot.get("Email_Eleve", "Inconnu")
            options_ot.append(f"{ot.get('ID_OT', '')} — {identite} ({ot.get('Cadre', '')}) • {ot.get('Date_Debut', '')} [{ot.get('Statut', '')}]")

        choix_index = st.selectbox(
            "Sélectionnez l'intervention à afficher :",
            range(len(options_ot)),
            index=len(options_ot) - 1,
            format_func=lambda i: options_ot[i]
        )
        ot_sel = ordres_travail[choix_index]
        prenom_sel, nom_sel = extraire_identite_email(ot_sel.get("Email_Eleve", ""))

        with st.container(border=True):
            top_l, top_r = st.columns([3, 1])
            with top_l:
                st.markdown(f"### {ot_sel.get('ID_OT', '')} • {prenom_sel} {nom_sel} ({ot_sel.get('Classe', '')})")
                st.markdown(
                    f"**E-mail :** `{ot_sel.get('Email_Eleve', '')}`  |  "
                    f"**Cadre :** `{ot_sel.get('Cadre', '')}`  |  "
                    f"**Début :** {ot_sel.get('Date_Debut', '')}  |  "
                    f"**Fin :** {ot_sel.get('Date_Fin', '')}"
                )
            with top_r:
                pdf_bytes = generer_pdf_ot(ot_sel)
                suffixe_nom = f"{nom_sel}_{prenom_sel}" if nom_sel else "eleve"
                nom_fichier = f"{ot_sel.get('ID_OT', 'OT')}_{suffixe_nom}.pdf".replace(" ", "_")
                st.download_button(
                    label="📄 Télécharger PDF (UAA5)",
                    data=pdf_bytes,
                    file_name=nom_fichier,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )

            st.markdown(f"**🛡️ LMRA VOLTA :** {ot_sel.get('LMRA', 'Non renseignée')}")
            st.divider()

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown("**⚡ Relevés Électriques & Thermiques**")
                st.info(ot_sel.get("Mesures_Elec", "N/A"))
            with col_m2:
                st.markdown("**💨 Relevés Pneumatiques, Méca & Compteur**")
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

        st.subheader("📋 Liste synthétique des interventions")
        df_complet = pd.DataFrame(ordres_travail)
        cols_compactes = [c for c in ["ID_OT", "Date_Debut", "Date_Fin", "Email_Eleve", "Classe", "Cadre", "Statut"] if c in df_complet.columns]
        st.dataframe(df_complet[cols_compactes], use_container_width=True, hide_index=True)

# ==============================================================================
# VUE 2 : MAINTENANCE PRÉVENTIVE (LMRA VOLTA + FICHE UAA5)
# ==============================================================================
elif menu == "🛠️ Maintenance Préventive (UAA5)":
    st.header("Fiche d'Activité : Maintenance Préventive (UAA5)")
    st.caption("Option EMI — Collège Notre-Dame Dinant — Mr PIRET")

    if "heure_debut_ot" not in st.session_state:
        st.session_state.heure_debut_ot = datetime.now().time().replace(second=0, microsecond=0)
    if "pieges_lmra" not in st.session_state:
        st.session_state.pieges_lmra = {}

    # --- EN-TÊTE IDENTIFICATION ---
    with st.container(border=True):
        st.subheader("Identification de l'Ordre de Travail")
        col_a, col_b, col_c = st.columns([2, 1, 1.5])
        email_eleve = col_a.text_input("E-mail Chromebook (prenom.nom@...)", placeholder="martin.dupont@ecole.be")
        classe = col_b.selectbox("Classe", ["6TQ", "5TQ", "4TQ"])
        cadre = col_c.selectbox("Cadre pédagogique", ["Formatif", "Certificatif"])

        if email_eleve and "@" in email_eleve:
            p_prev, n_prev = extraire_identite_email(email_eleve)
            if n_prev:
                st.caption(f"👤 Élève identifié pour le rapport PDF : **{p_prev} {n_prev}**")

        col_d, col_e, col_f = st.columns([2.5, 1, 1])
        machine = col_d.selectbox("Équipement / Machine contrôlée", [MACHINE_UAA5])
        compteur_h = col_e.text_input("Compteur horaire (h)", placeholder="Ex: 1450")
        heure_debut_saisie = col_f.time_input("Heure de début", value=st.session_state.heure_debut_ot)

    # ==========================================================================
    # ÉTAPE PRÉALABLE OBLIGATOIRE : LMRA (MODÈLE VOLTA AVEC DÉTECTION DE PIÈGES)
    # ==========================================================================
    with st.container(border=True):
        st.subheader("🛡️ LMRA — Analyse des Risques de Dernière Minute (VOLTA)")
        st.caption("Inspectez votre environnement de travail et répondez honnêtement à chaque point. Si une condition n'est pas remplie (NON), corrigez-la puis réévaluez-la à OUI.")

        def question_lmra_ab(label, key):
            c_q, c_r = st.columns([3.5, 1.5])
            c_q.markdown(label)
            rep = c_r.radio(
                label,
                ["OUI", "NON"],
                index=None,
                horizontal=True,
                label_visibility="collapsed",
                key=key
            )
            # Si l'élève détecte un problème (NON), on le mémorise pour le dossier
            if rep == "NON":
                st.session_state.pieges_lmra[key] = label
            return rep

        col_lmra_a, col_lmra_b = st.columns(2)

        # --- GROUPE A : CONNAISSANCES / INFORMATIONS ---
        with col_lmra_a:
            st.markdown("#### A. Connaissances / Informations")
            st.caption("Étape 1 : De quelles connaissances et informations ai-je besoin pour réaliser la mission en toute sécurité ?")
            questions_a = [
                ("Je connais ma tâche ?", "lmra_a1"),
                ("Je sais quels EPI je dois porter ?", "lmra_a2"),
                ("Je connais le contenu des instructions de travail / de la TRA / du permis de travail ?", "lmra_a3"),
                ("Connaît-on l'endroit où je travaille ?", "lmra_a4"),
                ("Je sais où se trouvent les douches d'urgence, les extincteurs, les lieux de rassemblement et le chemin d'évacuation ?", "lmra_a5")
            ]
            reponses_a = [question_lmra_ab(q, k) for q, k in questions_a]
            a_valide = all(r == "OUI" for r in reponses_a)

        # --- GROUPE B : CONDITIONS POUR UN TRAVAIL EN TOUTE SÉCURITÉ ---
        with col_lmra_b:
            st.markdown("#### B. Conditions pour un travail en toute sécurité")
            st.caption("Étape 1 : Définissez les conditions nécessaires pour réaliser la tâche en toute sécurité.")
            questions_b = [
                ("Mon lieu de travail est-il rangé ?", "lmra_b1"),
                ("Mes EPI offrent-ils une protection suffisante ?", "lmra_b2"),
                ("Les conditions climatiques sont-elles adaptées ?", "lmra_b3"),
                ("Je dispose des bons équipements de travail ?", "lmra_b4"),
                ("Mon outil est-il en bon état ?", "lmra_b5"),
                ("Mon lieu de travail est-il suffisamment éclairé ?", "lmra_b6"),
                ("La partie de l'installation est-elle sécurisée ?", "lmra_b7"),
                ("Ma zone de travail est-elle délimitée ?", "lmra_b8")
            ]
            reponses_b = [question_lmra_ab(q, k) for q, k in questions_b]
            b_valide = all(r == "OUI" for r in reponses_b)

        # --- BOUCLE ÉTAPE 2 VOLTA : CORRECTION DES PIÈGES DÉTECTÉS ---
        corrections_pieges_ok = True
        resume_pieges_corr = []

        if st.session_state.pieges_lmra:
            st.markdown("---")
            st.warning("⚠️ **Étape 2 (VOLTA) — Condition(s) non conforme(s) / Piège(s) détecté(s) :** Apportez les corrections nécessaires sur le poste, notez l'action réalisée ci-dessous, puis **réévaluez le point à « OUI »**.")
            for k_piege, lbl_piege in list(st.session_state.pieges_lmra.items()):
                col_p1, col_p2 = st.columns([5, 1])
                with col_p1:
                    txt_corr = st.text_input(
                        f"Action corrective réalisée pour : « {lbl_piege} »",
                        placeholder="Ex: J'ai rallumé l'éclairage de l'atelier / J'ai balisé la zone / J'ai mis mes EPI.",
                        key=f"corr_{k_piege}"
                    )
                with col_p2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("↩️ Annuler", key=f"del_{k_piege}", help="Supprimer si erreur de clic"):
                        del st.session_state.pieges_lmra[k_piege]
                        st.rerun()

                if not txt_corr.strip():
                    corrections_pieges_ok = False
                else:
                    resume_pieges_corr.append(f"{lbl_piege.replace(' ?', '')} -> Corrigé : {txt_corr.strip()}")

        st.markdown("---")
        # --- GROUPE C : RISQUES ---
        st.markdown("#### C. Risques présents pendant les travaux")
        st.caption("Étape 1 : Quels risques sont (restent) présents pendant les travaux ?")
        questions_c = [
            ("Existe-t-il un danger de trébuchement ?", "lmra_c1"),
            ("Y a-t-il un danger de chute d'objet ?", "lmra_c2"),
            ("Y a-t-il un danger de chute en cas de travail en hauteur ?", "lmra_c3"),
            ("Y a-t-il un risque d'électrocution ?", "lmra_c4"),
            ("Y a-t-il un risque d'explosion ?", "lmra_c5"),
            ("Une exposition à des substances dangereuses est-elle possible ?", "lmra_c6"),
            ("Est-il possible de se faire mal et/ou de se cogner ?", "lmra_c7"),
            ("Y a-t-il un danger pour l'environnement ?", "lmra_c8")
        ]

        col_c1, col_c2 = st.columns(2)
        risques_presents = []
        reponses_c = []
        for idx, (q, k) in enumerate(questions_c):
            target_col = col_c1 if idx < 4 else col_c2
            with target_col:
                c_q, c_r = st.columns([3.5, 1.5])
                c_q.markdown(q)
                rep_c = c_r.radio(
                    q,
                    ["OUI", "NON"],
                    index=None,
                    horizontal=True,
                    label_visibility="collapsed",
                    key=k
                )
                reponses_c.append(rep_c)
                if rep_c == "OUI":
                    risques_presents.append(q.replace(" ?", ""))

        c_tous_repondus = all(r in ["OUI", "NON"] for r in reponses_c)
        mesures_lmra_c = ""
        c_valide = c_tous_repondus

        if risques_presents:
            st.warning(f"⚠️ **Étape 2 (Groupe C) — Risque(s) identifié(s) :** {', '.join(risques_presents)}")
            mesures_lmra_c = st.text_input(
                "Déterminez et appliquez les mesures adaptées pour supprimer ou limiter ces risques :",
                placeholder="Ex: Consignation électrique + VAT effectuée, balisage de la zone et rangement des câbles au sol."
            )
            risques_maitrises = st.checkbox(
                "Je confirme que les mesures nécessaires sont prises et que tous les risques repris en C disparaissent ou sont suffisamment évités."
            )
            c_valide = c_tous_repondus and bool(mesures_lmra_c.strip()) and risques_maitrises

        lmra_complete = a_valide and b_valide and corrections_pieges_ok and c_valide

        # --- FEU VERT PROFESSEUR (SI PIÈGE NON CORRIGEABLE PAR L'ÉLÈVE) ---
        feu_vert_prof = False
        if not lmra_complete:
            with st.expander("🔑 Feu vert Professeur (Déblocage PIN si condition bloquante)"):
                pin_lmra = st.text_input("Code PIN Mr Piret pour autoriser le démarrage", type="password", key="pin_lmra_override")
                if pin_lmra == CODE_PIN_PROF:
                    feu_vert_prof = True
                    st.success("Feu vert professeur accordé.")
                elif pin_lmra:
                    st.error("Code PIN incorrect.")

    # ==========================================================================
    # VERROU DE SÉCURITÉ : ACCÈS À LA GAMME PRÉVENTIVE UNIQUEMENT SI LMRA OK
    # ==========================================================================
    if not (lmra_complete or feu_vert_prof):
        st.error("🛑 **INTERVENTION BLOQUÉE (LMRA VOLTA INCOMPLÈTE)** : Répondez à toutes les questions A, B et C. Si vous avez détecté une anomalie (NON), corrigez-la sur le poste, notez l'action réalisée et réévaluez le point à « OUI ».")
        st.stop()

    st.success("✅ **LMRA VOLTA VALIDÉE** — Vous êtes autorisé à démarrer la gamme de maintenance préventive.")

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
                anomalies_detectees.append(f"[Nettoyage] {lbl}")

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
                anomalies_detectees.append(f"[Élec/Auto] {lbl}")

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
                anomalies_detectees.append(f"[Mécanique] {lbl}")

        obs_meca = st.text_input("Observations mécaniques / Couple de serrage", placeholder="Ex: Resserrage borniers à 2,5 Nm OK")

    # --- 4. PNEUMATIQUE ET HYDRAULIQUE ---
    with st.expander("4. PNEUMATIQUE ET HYDRAULIQUE", expanded=True):
        for lbl, k in [
            ("Étanchéité : vérifier les circuits pneumatiques et hydrauliques", "pneu_1"),
            ("Unité de conditionnement d'air (FRL) : huile, filtre et condensats", "pneu_2"),
            ("Pression : vérifier et adapter selon les données techniques", "pneu_3")
        ]:
            if ligne_gamme(lbl, k) == "Anomalie":
                anomalies_detectees.append(f"[Pneumatique] {lbl}")

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
                anomalies_detectees.append(f"[Sécurité] {lbl}")

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
                donnees_fraiches, _ = charger_donnees()
                numeros_existants = []
                for x in donnees_fraiches:
                    parts = str(x.get("ID_OT", "")).split("-")
                    if len(parts) == 3 and parts[2].isdigit():
                        numeros_existants.append(int(parts[2]))
                prochain_num = (max(numeros_existants) + 1) if numeros_existants else 1
                nouvel_id = f"OT-2026-{prochain_num:03d}"

                maintenant = datetime.now()
                dt_debut_complet = datetime.combine(maintenant.date(), heure_debut_saisie)

                # Synthèse LMRA complète (incluant pièges détectés/corrigés & risques C)
                morceaux_lmra = ["Validée" if lmra_complete else "Feu vert Prof (PIN)"]
                if resume_pieges_corr:
                    morceaux_lmra.append("Condition(s) corrigée(s) : " + " ; ".join(resume_pieges_corr))
                if risques_presents:
                    morceaux_lmra.append(f"Risques C : {', '.join(risques_presents)} -> Mesures : {mesures_lmra_c.strip()}")
                else:
                    morceaux_lmra.append("Risques C : Aucun")
                resume_lmra = " | ".join(morceaux_lmra)

                # Regroupement complet des anomalies cochées + diagnostic texte
                liste_anom_pdf = []
                if anomalies_detectees:
                    liste_anom_pdf.append("Points non conformes : " + " ; ".join(anomalies_detectees))
                if anomalies_txt.strip():
                    liste_anom_pdf.append("Diagnostic : " + anomalies_txt.strip())
                resume_anomalies = " | ".join(liste_anom_pdf) if liste_anom_pdf else "RAS"

                # Regroupement des corrections + pièces remplacées
                liste_corr_pdf = []
                if correction_txt.strip():
                    liste_corr_pdf.append(correction_txt.strip())
                if pieces_remp.strip():
                    liste_corr_pdf.append(f"Pièces remplacées : {pieces_remp.strip()}")
                resume_corrections = " | ".join(liste_corr_pdf) if liste_corr_pdf else "Aucune (RAS)"

                # Ajout des observations mécaniques aux relevés fluides/méca
                mesures_pneu_meca = f"Réseau:{p_reseau} bar | FRL:{p_frl} bar | Purge:{purge_ok}"
                if obs_meca.strip():
                    mesures_pneu_meca += f" | Méca : {obs_meca.strip()}"

                nouvel_ot = {
                    "ID_OT": nouvel_id,
                    "Date_Debut": dt_debut_complet.strftime("%Y-%m-%d %H:%M"),
                    "Date_Fin": maintenant.strftime("%Y-%m-%d %H:%M"),
                    "Cadre": cadre,
                    "Email_Eleve": email_eleve.strip().lower(),
                    "Classe": classe,
                    "Machine": machine,
                    "Type": "Maintenance Préventive",
                    "LMRA": resume_lmra,
                    "Mesures_Elec": f"L1-L2:{u_l1l2}V | L2-L3:{u_l2l3}V | L3-L1:{u_l3l1}V | 24V:{u_24v}V | T°:{t_armoire}°C (Th:{t_thermostat}°C) | HMI:{defauts_hmi}",
                    "Mesures_Pneu": mesures_pneu_meca,
                    "Compteur_h": f"{compteur_h} h" if compteur_h else "N/A",
                    "Anomalies": resume_anomalies,
                    "Correction_Effectuee": resume_corrections,
                    "Etat_Machine": etat_machine_final,
                    "Statut": "⏳ En attente validation prof"
                }
                enregistrer_ot(nouvel_ot, mode_gsheet)
                st.session_state.heure_debut_ot = datetime.now().time().replace(second=0, microsecond=0)
                st.session_state.pieges_lmra = {}
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
# VUE 5 : VALIDATION PROFESSEUR (AVEC ACCÈS DIRECT AU GOOGLE SHEET)
# ==============================================================================
elif menu == "🔐 Validation Professeur":
    st.header("Espace Professeur — Validation des rapports GMAO")
    pin = st.text_input("Code PIN Professeur", type="password")

    if pin == CODE_PIN_PROF:
        bar_l, bar_r = st.columns([4, 1])
        bar_l.success("Session professeur déverrouillée.")
        bar_r.link_button("📊 Ouvrir Google Sheet", SHEET_URL, use_container_width=True)

        en_attente = [ot for ot in ordres_travail if "attente" in str(ot.get("Statut", ""))]

        if not en_attente:
            st.info("Aucun rapport en attente de validation.")
        else:
            for ot in en_attente:
                p_val, n_val = extraire_identite_email(ot.get("Email_Eleve", ""))
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"### {ot['ID_OT']} — {p_val} {n_val} (`{ot['Cadre']}`)")
                        st.write(f"**E-mail :** {ot['Email_Eleve']} ({ot['Classe']}) | **Début :** {ot.get('Date_Debut', '')} | **Fin :** {ot.get('Date_Fin', '')}")
                        st.write(f"**LMRA VOLTA :** {ot.get('LMRA', 'N/A')}")
                        st.write(f"**Élec/Thermique :** {ot['Mesures_Elec']}")
                        st.write(f"**Pneumatique/Méca :** {ot['Mesures_Pneu']} | **Compteur :** {ot['Compteur_h']}")
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
