import streamlit as st
import joblib
import pandas as pd

# test commit connection

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------

st.set_page_config(page_title="Risikoeinschätzung", layout="wide")

st.markdown("""
<style>

.form-card {
    background-color: var(--secondary-background-color);
    padding: 25px;
    border-radius: 14px;
}

.big-percentage {
    font-size: 48px;
    font-weight: 800;
    margin-bottom: 10px;
}

.risk-label {
    font-size: 14px;
    letter-spacing: 1px;
    color: var(--text-color);
    opacity: 0.6;
    text-transform: uppercase;
}

</style>
""", unsafe_allow_html=True)

st.title("Individuelle Krebs-Risikoeinschätzung")

st.markdown("""
Bitte geben Sie die folgenden Informationen ein.  
Die Einschätzung basiert auf statistischen Modellen und ersetzt keine ärztliche Diagnose.
""")

# -------------------------------------------------
# LOAD MODEL
# -------------------------------------------------

from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
model_path = BASE_DIR / "models" / "risk_model_lvl2.pkl"

model = joblib.load(model_path)

# -------------------------------------------------
# FEATURE ORDER
# -------------------------------------------------

expected_features = [
    "Alter",
    "Geschlecht",
    "Ethnie",
    "Höchster Bildungsabschluss",
    "Familienstand",
    "Verhältnis zwischen Familieneinkommen und Armut",
    "mind. 100 Zigaretten geraucht",
    "mind. einmal Alkohol getrunken",
    "wie oft wird Alkohol getrunken?",
    "Gibt es Zeiträume in denen sie täglich getrunken haben?",
    "Häufigkeit moderate körperliche Aktivitäten in Freizeit",
    "Sitzzeit pro Tag",
    "Trouble sleeping or sleeping too much",
    "Asthma",
    "COPD",
    "Athritis",
    "Herzinfarkt",
    "Schlaganfall",
    "Schilddrüsenprobleme",
    "BMI",
    "Depressive Symptome",
    "Hüftumfang (cm)",
    "Gewicht (kg)",
    "pulse",
    "sys_bp",
    "dia_bp",
    "Dauer der moderaten Aktivitäten",
    "Häufigkeit körperl. anstrengender Aktivitäten",
    "Schalfstunden unter der Woche",
    "Schalfstunden am Wochenende",
    "Energy (kcal)",
    "Total sugars (gm)",
    "Total fat (gm)",
    "Dietary fiber (gm)",
    "Protein (gm)",
    "Cholesterol (mg)"
]

# -------------------------------------------------
# LAYOUT
# -------------------------------------------------

col1, col2, col3 = st.columns([1.2, 1.2, 0.9])

# =================================================
# COLUMN 1
# =================================================

with col1:
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    st.header("Demografie")

    age = st.number_input("Alter", 18, 90, 45)

    geschlecht_map = {"Männlich": 1.0, "Weiblich": 2.0}
    geschlecht = geschlecht_map[st.selectbox("Geschlecht", list(geschlecht_map.keys()))]

    ethnie_map = {
        "Mexikanisch": 1.0,
        "Andere hispanische Herkunft": 2.0,
        "Weiß": 3.0,
        "Schwarz": 4.0,
        "Andere": 5.0
    }
    ethnie = ethnie_map[st.selectbox("Ethnie", list(ethnie_map.keys()))]

    education_map = {
        "Hauptschule": 1.0,
        "Realschule": 2.0,
        "Abitur": 3.0,
        "Studium abgebrochen": 4.0,
        "Universitärer Abschluss": 5.0
    }
    education = education_map[st.selectbox("Höchster Bildungsabschluss", list(education_map.keys()))]

    family_map = {
        "Verheiratet/Lebensgemeinschaft": 1.0,
        "Geschieden/Getrennt/Verwitwet": 2.0,
        "Ledig": 3.0
    }
    familienstand = family_map[st.selectbox("Familienstand", list(family_map.keys()))]

    income_map = {
        "Unter Armutsgrenze": 0.8,
        "Nahe Armutsgrenze": 1.2,
        "Mittleres Einkommen": 2.5,
        "Überdurchschnittliches Einkommen": 4.0,
        "Hohes Einkommen": 5.0
    }
    income_ratio = income_map[st.selectbox("Haushaltseinkommen (Einschätzung)", list(income_map.keys()))]

    st.header("Körpermaße")

    gewicht = st.number_input("Gewicht (kg)", 40.0, 200.0, 75.0)
    groesse = st.number_input("Körpergröße (cm)", 140.0, 220.0, 170.0)

    bmi = gewicht / ((groesse / 100) ** 2)
    st.write(f"Berechneter BMI: **{bmi:.1f}**")

    hueftumfang = st.number_input("Hüftumfang (cm)", 60.0, 180.0, 95.0)

    st.header("Gesundheitszustand")

    asthma = st.checkbox("Asthma")
    copd = st.checkbox("COPD")
    arthritis = st.checkbox("Arthritis")
    herzinfarkt = st.checkbox("Herzinfarkt")
    schlaganfall = st.checkbox("Schlaganfall")
    schilddruese = st.checkbox("Schilddrüsenprobleme")

    st.markdown('</div>', unsafe_allow_html=True)

# =================================================
# COLUMN 2
# =================================================

with col2:
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    st.header("Blutdruck & Puls")

    sys_bp = st.number_input("Systolischer Blutdruck (mmHg)", 80.0, 220.0, 120.0)
    dia_bp = st.number_input("Diastolischer Blutdruck (mmHg)", 40.0, 140.0, 80.0)
    pulse = st.number_input("Puls", 40.0, 140.0, 70.0)

    st.header("Lebensstil")

    raucher = st.checkbox("Mindestens 100 Zigaretten im Leben")
    alkohol = st.checkbox("Alkohol konsumiert")
    alkohol_freq = st.slider("Alkoholkonsum (0=nie, 10=sehr häufig)", 0, 10, 2)
    alkohol_daily = st.checkbox("Phasen mit täglichem Alkoholkonsum")

    aktivitaet_mod = st.slider("Moderate Aktivität (Tage/Woche)", 0, 7, 2)
    aktivitaet_mod_dauer = st.number_input("Dauer moderater Aktivität (Minuten/Tag)", 0, 300, 30)
    aktivitaet_vig_freq = st.slider("Anstrengende Aktivität (Tage/Woche)", 0, 7, 1)

    sitzzeit = st.slider("Sitzzeit pro Tag (Stunden)", 0, 16, 6)

    schlafproblem = st.checkbox("Schlafprobleme")
    schlaf_woche = st.slider("Schlafstunden unter der Woche", 3, 12, 7)
    schlaf_wochenende = st.slider("Schlafstunden am Wochenende", 3, 12, 8)

    depression = st.checkbox("Depressive Symptome")

    st.markdown('</div>', unsafe_allow_html=True)

# =================================================
# RESULT COLUMN
# =================================================

with col3:

    st.markdown("""
    <div style="
        background-color: white;
        padding: 30px;
        border-radius: 14px;
        border-left: 8px solid #2a6f97;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    ">
    <h3 style="margin-top:0;">Risikobewertung</h3>
    """, unsafe_allow_html=True)

    result_placeholder = st.empty()

    with result_placeholder.container():
        st.markdown("""
        <div style="
            background-color: var(--secondary-background-color);
            padding:15px;
            border-radius:10px;
        ">
        Bitte füllen Sie das Formular aus und klicken Sie auf <b>'Risiko berechnen'</b>.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# BUTTON + CALCULATION
# -------------------------------------------------

if st.button("Risiko berechnen"):

    user_input = {
        "Alter": age,
        "Geschlecht": geschlecht,
        "Ethnie": ethnie,
        "Höchster Bildungsabschluss": education,
        "Familienstand": familienstand,
        "Verhältnis zwischen Familieneinkommen und Armut": income_ratio,
        "mind. 100 Zigaretten geraucht": int(raucher),
        "mind. einmal Alkohol getrunken": int(alkohol),
        "wie oft wird Alkohol getrunken?": alkohol_freq,
        "Gibt es Zeiträume in denen sie täglich getrunken haben?": int(alkohol_daily),
        "Häufigkeit moderate körperliche Aktivitäten in Freizeit": aktivitaet_mod,
        "Sitzzeit pro Tag": sitzzeit,
        "Trouble sleeping or sleeping too much": int(schlafproblem),
        "Asthma": int(asthma),
        "COPD": int(copd),
        "Athritis": int(arthritis),
        "Herzinfarkt": int(herzinfarkt),
        "Schlaganfall": int(schlaganfall),
        "Schilddrüsenprobleme": int(schilddruese),
        "BMI": bmi,
        "Depressive Symptome": int(depression),
        "Hüftumfang (cm)": hueftumfang,
        "Gewicht (kg)": gewicht,
        "pulse": pulse,
        "sys_bp": sys_bp,
        "dia_bp": dia_bp,
        "Dauer der moderaten Aktivitäten": aktivitaet_mod_dauer,
        "Häufigkeit körperl. anstrengender Aktivitäten": aktivitaet_vig_freq,
        "Schalfstunden unter der Woche": schlaf_woche,
        "Schalfstunden am Wochenende": schlaf_wochenende,
        "Energy (kcal)": 1926.73,
        "Total sugars (gm)": 89.9,
        "Total fat (gm)": 80.7,
        "Dietary fiber (gm)": 15.41,
        "Protein (gm)": 71.56,
        "Cholesterol (mg)": 276.7
    }

    input_df = pd.DataFrame([user_input])
    input_df = input_df[expected_features]

    prob = model.predict_proba(input_df)[0][1]
    threshold = 0.40

    with result_placeholder.container():

        st.markdown(f"""
        <div class="risk-label">Risikowahrscheinlichkeit</div>
        <div class="big-percentage">{prob*100:.1f} %</div>
        """, unsafe_allow_html=True)

        if prob >= threshold:
            st.error("Erhöhtes Risiko")
            st.warning("Bitte ärztliche Beratung in Betracht ziehen.")
        else:
            st.success("Niedriges Risiko")