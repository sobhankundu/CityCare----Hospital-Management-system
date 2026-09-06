"""
UPI QR code generation.

Generates a standard UPI deep-link (`upi://pay?...`) as a scannable QR code.
This is real, correctly-formatted UPI protocol -- any UPI app (GPay, PhonePe,
Paytm, etc.) can scan and act on it -- but there's no payment gateway
webhook wired up to auto-confirm the money arrived, since that requires a
registered merchant account with a payment aggregator. The staff member
confirms receipt manually after checking their own UPI app, same as any
small business accepting UPI without a gateway subscription.
"""
from urllib.parse import quote

import qrcode
from PIL import Image

from config import UPI_MERCHANT_VPA, UPI_MERCHANT_NAME


def build_upi_uri(amount: int, note: str, txn_ref: str) -> str:
    params = (
        f"pa={quote(UPI_MERCHANT_VPA)}"
        f"&pn={quote(UPI_MERCHANT_NAME)}"
        f"&am={amount:.2f}"
        f"&cu=INR"
        f"&tn={quote(note)}"
        f"&tr={quote(txn_ref)}"
    )
    return f"upi://pay?{params}"


def generate_upi_qr(amount: int, note: str, txn_ref: str) -> Image.Image:
    """Returns a PIL Image of the QR code -- pass straight to st.image()."""
    uri = build_upi_uri(amount, note, txn_ref)
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#16241F", back_color="white")
    # qrcode wraps a PIL image rather than subclassing it in some versions;
    # normalise to a real PIL.Image.Image so callers get a consistent type.
    return img.get_image() if hasattr(img, "get_image") else img