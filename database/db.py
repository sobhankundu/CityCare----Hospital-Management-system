"""
Database engine/session management + first-run seeding.

Streamlit re-executes the script on every interaction, so we cache the engine
with st.cache_resource where this module is used from the app, but the module
itself stays framework-agnostic (it works fine from plain scripts / tests too).
"""
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
from database.models import Base, User, Doctor
from utils.security import hash_password

logger = logging.getLogger(__name__)

# check_same_thread is a SQLite-only pragma (needed because Streamlit's
# session handling can touch the connection from more than one thread); a
# real Postgres driver doesn't accept this argument at all, so it must only
# be passed when we're actually running against a local SQLite file.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
_engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)

# A representative seed roster so the app looks "populated" out of the box,
# mirroring the department list a real hospital directory would have.
_SEED_DOCTORS = [
    ("Dr. R. Sharma", "General Medicine", "101"),
    ("Dr. A. Verma", "General Medicine", "102"),
    ("Dr. S. Iyer", "Cardiology", "201"),
    ("Dr. K. Nair", "Cardiology", "202"),
    ("Dr. P. Kumar", "Orthopaedics", "301"),
    ("Dr. F. Khan", "Orthopaedics", "302"),
    ("Dr. V. Kohli", "Gynaecology", "401"),
    ("Dr. M. Singh", "Gynaecology", "402"),
    ("Dr. J. Sidharth", "Neurology", "501"),
    ("Dr. T. Rao", "Neurology", "502"),
    ("Dr. I. Ahmed", "Dermatology", "601"),
    ("Dr. L. Fernandes", "ENT", "701"),
    ("Dr. S. Bose", "Pediatrics", "801"),
    ("Dr. N. Joshi", "Pulmonology", "901"),
    ("Dr. D. Menon", "Gastroenterology", "1001"),
]


def init_db() -> None:
    """Create all tables (no-op if they already exist) and seed baseline data."""
    Base.metadata.create_all(_engine)
    _seed(SessionLocal())


def get_session() -> Session:
    return SessionLocal()


@contextmanager
def session_scope():
    """Usage: `with session_scope() as session: ...` -- commits on success,
    rolls back and re-raises on any exception, always closes the session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _seed(session: Session) -> None:
    try:
        if session.query(User).filter_by(username=DEFAULT_ADMIN_USERNAME).first() is None:
            pw_hash, salt = hash_password(DEFAULT_ADMIN_PASSWORD)
            admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=pw_hash,
                salt=salt,
                role="admin",
            )
            session.add(admin)
            logger.info("Seeded default admin account.")

        if session.query(Doctor).count() == 0:
            for name, dept, room in _SEED_DOCTORS:
                session.add(Doctor(name=name, department=dept, room_no=room))
            logger.info("Seeded doctor roster (%d doctors).", len(_SEED_DOCTORS))

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()