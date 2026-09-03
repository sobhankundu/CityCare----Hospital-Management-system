"""
Authentication service. All DB access goes through here rather than being
inlined into Streamlit pages, so the logic is unit-testable independently of
the UI framework and can be reused if the UI is ever swapped out.
"""
from database.models import User
from utils.security import hash_password, verify_password


def authenticate(session, username: str, password: str):
    """Returns the User on success, or None on failure. Never raises on bad
    credentials -- callers should treat None as 'invalid username or password'
    without distinguishing which, to avoid leaking which usernames exist."""
    user = session.query(User).filter_by(username=username).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash, user.salt):
        return None
    return user


def username_exists(session, username: str) -> bool:
    return session.query(User).filter_by(username=username).first() is not None


def create_user(session, username: str, password: str, role: str) -> User:
    if username_exists(session, username):
        raise ValueError(f"Username '{username}' is already taken.")
    if role not in ("admin", "doctor", "patient"):
        raise ValueError(f"Invalid role: {role}")
    pw_hash, salt = hash_password(password)
    user = User(username=username, password_hash=pw_hash, salt=salt, role=role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
