from ml.predictor import predict
from ml.chatbot import ChatState, respond, extract_symptoms


def test_predict_returns_known_department():
    result = predict(["chest pain", "shortness of breath", "cold sweats"])
    assert result["department"] in [
        "Cardiology", "General Medicine", "Pulmonology", "Neurology",
        "Orthopaedics", "Gynaecology", "Dermatology", "ENT", "Pediatrics", "Gastroenterology",
    ]
    assert 0.0 <= result["department_confidence"] <= 1.0


def test_predict_emergency_symptom_forces_emergency_urgency():
    result = predict(["severe chest pain"])
    assert result["urgency"] == "Emergency"
    assert result["is_emergency_override"] is True


def test_predict_unknown_symptoms_returns_error():
    result = predict(["not a real symptom"])
    assert result["error"] is not None
    assert result["department"] is None


def test_extract_symptoms_direct_match():
    found = extract_symptoms("I have a sore throat and ear pain")
    assert "sore throat" in found
    assert "ear pain" in found


def test_extract_symptoms_typo_tolerance():
    found = extract_symptoms("I have a severe hedache today")
    assert "severe headache" in found


def test_extract_symptoms_does_not_conflate_severity_levels():
    """Regression test: 'chest pain' must NOT fuzzy-match 'severe chest pain'.
    These map to different urgency tiers (High vs Emergency), so blurring
    them would create false emergency triggers in the triage chatbot."""
    found = extract_symptoms("I have chest pain and shortness of breath")
    assert "chest pain" in found
    assert "severe chest pain" not in found


def test_chatbot_emergency_interrupt_short_circuits():
    state = ChatState()
    reply, state = respond("I have severe chest pain", state)
    assert "Emergency Room" in reply or "emergency" in reply.lower()
    assert state.finalized is True


def test_chatbot_normal_flow_reaches_recommendation():
    state = ChatState()
    _, state = respond("hello", state)
    _, state = respond("I have joint pain and back pain", state)
    reply, state = respond("done", state)
    assert "Recommended department" in reply
    assert state.finalized is True
