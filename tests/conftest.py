import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Doctor


@pytest.fixture()
def session():
    """Fresh in-memory SQLite DB per test -- fully isolated, no shared state."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    s = Session()
    # minimal doctor roster needed by appointment tests
    s.add(Doctor(name="Dr. Test", department="General Medicine", room_no="101"))
    s.commit()
    yield s
    s.close()
