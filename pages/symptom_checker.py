import streamlit as st

from database.db import session_scope
from database.models import SymptomCheckLog
from ml.predictor import predict
from ml.symptom_data import ALL_SYMPTOMS
from utils.ui import inject_css, page_header, urgency_badge

inject_css()
page_header("Symptom Checker", eyebrow="AI-Assisted Triage")

st.caption(
    "Select the symptoms you're experiencing. A machine learning model trained on "
    "clinically-informed symptom patterns will suggest which department to see and "
    "how urgent your case may be."
)
st.info(
    "⚠️ This is an automated estimate for triage purposes only, not a medical diagnosis. "
    "If you're experiencing a medical emergency, seek emergency care immediately regardless of this tool.",
    icon="⚠️",
)

symptoms = st.multiselect("Your symptoms", ALL_SYMPTOMS, help="Start typing to filter the list.")
check = st.button("Check symptoms", type="primary", use_container_width=True)

if check:
    if not symptoms:
        st.warning("Select at least one symptom.")
    else:
        result = predict(symptoms)
        if result["error"]:
            st.warning(result["error"])
        else:
            if result["is_emergency_override"]:
                st.error(
                    "🚨 **One or more of your symptoms is a red flag for a medical emergency.** "
                    "Please go to the nearest Emergency Room or call emergency services now."
                )
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Recommended Department", result["department"])
                    st.caption(f"Model confidence: {result['department_confidence']*100:.0f}%")
                with col2:
                    st.markdown("**Estimated Urgency**")
                    st.markdown(urgency_badge(result["urgency"]), unsafe_allow_html=True)
                    st.caption(f"Model confidence: {result['urgency_confidence']*100:.0f}%")

                st.markdown("**Other departments considered:**")
                for dept, prob in result["top_departments"][1:]:
                    st.progress(prob, text=f"{dept} — {prob*100:.0f}%")

                st.caption(
                    "You can proceed to **Book Appointment** with this department, "
                    "or ask a follow-up in the **Triage Chatbot**."
                )

            # Audit log -- lets an admin later review real usage patterns and,
            # eventually, use logged cases to retrain/improve the model.
            govt_id = st.session_state.get("patient_govt_id")
            with session_scope() as session:
                patient_id = None
                if govt_id:
                    from services.patient_service import find_patient_by_govt_id
                    p = find_patient_by_govt_id(session, govt_id)
                    patient_id = p.id if p else None
                session.add(SymptomCheckLog(
                    patient_id=patient_id,
                    symptoms_input=", ".join(sorted(symptoms)),
                    predicted_department=result["department"],
                    confidence=f"{result['department_confidence']:.2f}",
                    predicted_urgency=result["urgency"],
                ))
