import pytest

from services.auth_service import create_user, all_staff, deactivate_user, authenticate


def test_create_staff_account(session):
    user = create_user(session, "cashier1", "securepass1", role="staff")
    assert user.role == "staff"


def test_staff_can_authenticate(session):
    create_user(session, "cashier1", "securepass1", role="staff")
    user = authenticate(session, "cashier1", "securepass1")
    assert user is not None
    assert user.role == "staff"


def test_all_staff_returns_only_staff_role(session):
    create_user(session, "cashier1", "securepass1", role="staff")
    create_user(session, "somepatient", "securepass1", role="patient")
    staff = all_staff(session)
    assert len(staff) == 1
    assert staff[0].username == "cashier1"


def test_deactivate_user_removes_account(session):
    user = create_user(session, "cashier1", "securepass1", role="staff")
    deactivate_user(session, user.id, requesting_username="admin")
    assert authenticate(session, "cashier1", "securepass1") is None


def test_deactivate_user_refuses_self_removal(session):
    user = create_user(session, "cashier1", "securepass1", role="staff")
    with pytest.raises(ValueError):
        deactivate_user(session, user.id, requesting_username="cashier1")


def test_create_user_rejects_invalid_role(session):
    with pytest.raises(ValueError):
        create_user(session, "someone", "securepass1", role="superadmin")