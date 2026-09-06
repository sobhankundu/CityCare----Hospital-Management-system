from PIL import Image

from utils.upi import build_upi_uri, generate_upi_qr


def test_build_upi_uri_has_correct_scheme():
    uri = build_upi_uri(500, "Test payment", "APPT1")
    assert uri.startswith("upi://pay?")


def test_build_upi_uri_includes_amount_formatted_as_decimal():
    uri = build_upi_uri(500, "Test payment", "APPT1")
    assert "am=500.00" in uri


def test_build_upi_uri_includes_currency():
    uri = build_upi_uri(500, "Test payment", "APPT1")
    assert "cu=INR" in uri


def test_generate_upi_qr_returns_valid_image():
    img = generate_upi_qr(800, "CityCare Token 5", "APPT42")
    assert isinstance(img, Image.Image)
    assert img.size[0] > 0 and img.size[1] > 0