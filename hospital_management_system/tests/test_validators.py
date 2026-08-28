from utils.validators import (
    validate_govt_id, validate_name, validate_age, validate_gender,
    validate_phone, validate_blood_group,
)


def test_govt_id_valid():
    assert validate_govt_id("123456789012")[0] is True


def test_govt_id_invalid_length():
    assert validate_govt_id("12345")[0] is False


def test_govt_id_non_numeric():
    assert validate_govt_id("12345678901a")[0] is False


def test_name_valid():
    assert validate_name("Ravi Kumar")[0] is True


def test_name_rejects_digits():
    assert validate_name("Ravi123")[0] is False


def test_age_valid():
    assert validate_age("34")[0] is True


def test_age_rejects_non_numeric():
    assert validate_age("abc")[0] is False


def test_age_rejects_out_of_range():
    assert validate_age("999")[0] is False
    assert validate_age("0")[0] is False


def test_gender_valid_values():
    for g in ("M", "F", "O"):
        assert validate_gender(g)[0] is True


def test_gender_invalid():
    assert validate_gender("X")[0] is False


def test_phone_valid():
    assert validate_phone("9876543210")[0] is True


def test_phone_rejects_short():
    assert validate_phone("123")[0] is False


def test_phone_rejects_bad_leading_digit():
    assert validate_phone("1876543210")[0] is False


def test_blood_group_valid():
    assert validate_blood_group("O+", ["O+", "O-", "A+"])[0] is True


def test_blood_group_invalid():
    assert validate_blood_group("Z+", ["O+", "O-", "A+"])[0] is False
