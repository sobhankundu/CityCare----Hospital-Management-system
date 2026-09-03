"""
Domain knowledge for the symptom checker: which symptoms are characteristic
of which department, and which symptoms indicate a medical emergency.

IMPORTANT: this mapping was written for a portfolio/demo project, not
clinically validated. See the disclaimer shown in the app UI.

Keeping this as data (rather than hard-coded if/elif chains, as the original
project did for doctor assignment) is what lets the dataset generator, the
trainer, and the live predictor all stay in sync from one source of truth.
"""

DEPARTMENT_SYMPTOMS = {
    "General Medicine": [
        "fever", "fatigue", "body ache", "chills", "mild headache",
        "general weakness", "loss of appetite", "dizziness",
    ],
    "Cardiology": [
        "chest pain", "palpitations", "shortness of breath",
        "high blood pressure", "swelling in legs", "cold sweats",
        "irregular heartbeat", "severe chest pain",
    ],
    "Orthopaedics": [
        "joint pain", "back pain", "fracture", "muscle stiffness",
        "knee pain", "swelling in joints", "difficulty walking", "sports injury",
    ],
    "Neurology": [
        "severe headache", "migraine", "seizures", "numbness",
        "tingling sensation", "memory loss", "loss of balance",
        "blurred vision", "slurred speech",
    ],
    "Gynaecology": [
        "abdominal cramps", "irregular periods", "pelvic pain",
        "pregnancy related", "vaginal bleeding", "menstrual issues",
        "heavy vaginal bleeding",
    ],
    "Dermatology": [
        "skin rash", "itching", "acne", "hair loss",
        "skin discoloration", "allergic reaction", "hives",
    ],
    "ENT": [
        "sore throat", "ear pain", "hearing loss", "sinus congestion",
        "nasal blockage", "tonsillitis", "ringing in ears",
    ],
    "Pediatrics": [
        "child fever", "growth concerns", "vaccination due",
        "feeding issues in infant", "childhood rash", "high fever in infant",
    ],
    "Pulmonology": [
        "persistent cough", "wheezing", "breathlessness", "chest tightness",
        "coughing blood", "asthma symptoms", "difficulty breathing",
    ],
    "Gastroenterology": [
        "stomach pain", "nausea", "vomiting", "diarrhea",
        "constipation", "acid reflux", "blood in stool", "bloating",
    ],
}

# Symptoms that, on their own, indicate the patient needs urgent attention
# regardless of which department they map to.
EMERGENCY_SYMPTOMS = {
    "severe chest pain", "difficulty breathing", "loss of consciousness",
    "seizures", "coughing blood", "slurred speech",
    "heavy vaginal bleeding", "blood in stool", "high fever in infant",
}

# Symptoms that raise concern but aren't automatically an emergency.
HIGH_RISK_SYMPTOMS = {
    "chest pain", "shortness of breath", "irregular heartbeat",
    "severe headache", "numbness", "blurred vision", "vomiting",
    "fracture", "vaginal bleeding",
}

ALL_SYMPTOMS = sorted({s for symptoms in DEPARTMENT_SYMPTOMS.values() for s in symptoms})
ALL_DEPARTMENTS = sorted(DEPARTMENT_SYMPTOMS.keys())
