"""
Rule-based triage chatbot.

This deliberately does NOT use a large language model -- a hospital triage
tool needs to be predictable and auditable, so symptom extraction is done
with transparent keyword + fuzzy-matching against a known vocabulary
(ml.symptom_data.ALL_SYMPTOMS), and the actual department/urgency call is
delegated to the trained classifier in ml.predictor. That combination
(structured NLP front-end + ML back-end) is a common, explainable pattern
in real clinical decision-support tools.
"""
import difflib
import re
from dataclasses import dataclass, field

from ml.symptom_data import ALL_SYMPTOMS, EMERGENCY_SYMPTOMS
from ml.predictor import predict

_GREETING_RE = re.compile(r"\b(hi|hello|hey|namaste)\b", re.IGNORECASE)
_DONE_RE = re.compile(r"\b(done|no|nothing else|that'?s all|finish|finali[sz]e)\b", re.IGNORECASE)

MIN_TURNS_BEFORE_SUGGESTING_FINISH = 1


@dataclass
class ChatState:
    collected_symptoms: set = field(default_factory=set)
    turn_count: int = 0
    finalized: bool = False


def extract_symptoms(text: str) -> set:
    """Matches known symptom phrases in free text, with a fuzzy fallback for
    typos (e.g. 'hedache' -> 'headache')."""
    text_lower = text.lower()
    found = {s for s in ALL_SYMPTOMS if s in text_lower}

    words = re.findall(r"[a-z]+", text_lower)
    # Every word of the symptom phrase must have a fuzzy match, including
    # severity qualifiers like "severe"/"mild" -- those aren't safe to strip,
    # since "chest pain" and "severe chest pain" map to different urgency
    # levels and conflating them would create false emergency triggers.
    for symptom in ALL_SYMPTOMS:
        if symptom in found:
            continue
        symptom_words = symptom.split()
        matched_words = 0
        for sw in symptom_words:
            if any(difflib.SequenceMatcher(None, sw, w).ratio() >= 0.82 for w in words):
                matched_words += 1
        if matched_words == len(symptom_words):
            found.add(symptom)
    return found


def _format_symptom_list(symptoms) -> str:
    return ", ".join(sorted(symptoms))


def _final_recommendation(state: ChatState) -> str:
    result = predict(list(state.collected_symptoms))
    if result["error"]:
        return (
            "I couldn't map what you've described to a specific department. "
            "Please book a **General Medicine** appointment and the doctor will refer you onward if needed."
        )

    lines = [
        f"Based on: *{_format_symptom_list(state.collected_symptoms)}*",
        "",
        f"**Recommended department:** {result['department']} "
        f"({result['department_confidence']*100:.0f}% model confidence)",
        f"**Estimated urgency:** {result['urgency']}",
    ]
    if result["is_emergency_override"]:
        lines.append(
            "\n🚨 **This includes a red-flag symptom. Please go to the nearest "
            "Emergency Room or call emergency services now instead of booking a routine appointment.**"
        )
    else:
        lines.append(
            "\nYou can book an appointment with this department from the "
            "**Book Appointment** page. A doctor will confirm the diagnosis in person."
        )
    lines.append(
        "\n_This is an automated, non-clinical estimate for triage purposes only "
        "and is not a medical diagnosis._"
    )
    return "\n".join(lines)


def respond(user_message: str, state: ChatState) -> tuple:
    """Returns (bot_reply: str, updated_state: ChatState)."""
    state.turn_count += 1
    new_symptoms = extract_symptoms(user_message)

    # Immediate red-flag interrupt, regardless of conversation stage.
    emergency_hit = new_symptoms & EMERGENCY_SYMPTOMS
    if emergency_hit:
        state.collected_symptoms |= new_symptoms
        reply = (
            f"🚨 You mentioned **{_format_symptom_list(emergency_hit)}**, which can indicate a medical emergency.\n\n"
            "Please go to the nearest Emergency Room or call emergency services right away. "
            "Don't wait to book a routine appointment for this."
        )
        state.finalized = True
        return reply, state

    if _DONE_RE.search(user_message) and state.collected_symptoms:
        state.finalized = True
        return _final_recommendation(state), state

    if not new_symptoms and not state.collected_symptoms:
        if _GREETING_RE.search(user_message) or state.turn_count == 1:
            return (
                "Hi, I'm the triage assistant. Describe what you're feeling in your own words "
                "(e.g. \"I have a sore throat and ear pain\") and I'll suggest which department to book with.",
                state,
            )
        return (
            "I didn't catch any specific symptoms in that. Could you describe how you're feeling? "
            "For example: fever, joint pain, skin rash, chest pain, etc.",
            state,
        )

    state.collected_symptoms |= new_symptoms

    ack = f"Noted: {_format_symptom_list(new_symptoms)}." if new_symptoms else "Got it."
    if state.turn_count <= MIN_TURNS_BEFORE_SUGGESTING_FINISH:
        reply = (
            f"{ack} Any other symptoms? If not, type **\"done\"** and I'll give you a recommendation."
        )
    else:
        reply = (
            f"{ack} Type **\"done\"** for my recommendation, or keep describing symptoms."
        )
    return reply, state
