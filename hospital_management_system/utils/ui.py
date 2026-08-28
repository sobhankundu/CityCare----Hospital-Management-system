"""
Shared visual identity for the app.

Design intent: a "clinical calm" palette (deep teal / soft mint) instead of
the generic default-blue Streamlit look, paired with a serif display face
(Fraunces) for headers against a clean sans body face (IBM Plex Sans) so the
app doesn't read as an out-of-the-box template. Patient/queue/token numbers
are rendered in a monospace face styled like a physical hospital display
board -- a small detail grounded in the actual subject matter.
"""
import streamlit as st

URGENCY_COLORS = {
    "Low": "#2E7D32",
    "Medium": "#D98E04",
    "High": "#E4572E",
    "Emergency": "#C62828",
}

STATUS_COLORS = {
    "Scheduled": "#0F6B62",
    "Completed": "#2E7D32",
    "Cancelled": "#8A8F8D",
    "No-show": "#E4572E",
}


def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

        html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

        h1, h2, h3 { font-family: 'Fraunces', serif !important; font-weight: 600 !important; letter-spacing: -0.01em; }

        .cc-header {
            display: flex; align-items: baseline; gap: 0.6rem;
            border-bottom: 2px solid #0F6B62; padding-bottom: 0.5rem; margin-bottom: 1.2rem;
        }
        .cc-header .eyebrow {
            font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;
            letter-spacing: 0.12em; text-transform: uppercase; color: #0F6B62;
        }
        .cc-card {
            background: #EAF2F0; border-radius: 10px; padding: 1.1rem 1.3rem;
            border: 1px solid #d3e3df; margin-bottom: 0.8rem;
        }
        .cc-token {
            font-family: 'IBM Plex Mono', monospace; font-weight: 600;
            background: #16241F; color: #7FFFD4; display: inline-block;
            padding: 0.6rem 1.1rem; border-radius: 6px; font-size: 2.2rem;
            letter-spacing: 0.05em; line-height: 1;
        }
        .cc-badge {
            display: inline-block; padding: 0.18rem 0.65rem; border-radius: 999px;
            font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; font-weight: 600;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, eyebrow: str = ""):
    st.markdown(
        f"""
        <div class="cc-header">
            <div>
                {f'<div class="eyebrow">{eyebrow}</div>' if eyebrow else ''}
                <h1 style="margin:0;">{title}</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, color: str) -> str:
    return f'<span class="cc-badge" style="background:{color};">{text}</span>'


def urgency_badge(level: str) -> str:
    return badge(level, URGENCY_COLORS.get(level, "#607D8B"))


def status_badge(status: str) -> str:
    return badge(status, STATUS_COLORS.get(status, "#607D8B"))


def token_display(token_no: int, label: str = "TOKEN"):
    st.markdown(
        f"""
        <div style="text-align:center;">
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.8rem;
                        letter-spacing:0.15em; color:#5b6a66; margin-bottom:0.3rem;">{label}</div>
            <div class="cc-token">{token_no:03d}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(content_html: str):
    st.markdown(f'<div class="cc-card">{content_html}</div>', unsafe_allow_html=True)
