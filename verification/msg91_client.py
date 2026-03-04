"""
MSG91 OTP API client. OTP is sent and verified by MSG91; we do not generate or store OTP.
"""
import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

MSG91_HOST = "control.msg91.com"
SEND_PATH = "/api/v5/otp"
VERIFY_PATH = "/api/v5/otp/verify"


def _authkey():
    return getattr(settings, "MSG91_AUTH_KEY", "") or ""


def _template_id():
    return getattr(settings, "MSG91_OTP_TEMPLATE_ID", "") or ""


def _otp_expiry():
    return getattr(settings, "MSG91_OTP_EXPIRY", 1)  # minutes


def _otp_length():
    return getattr(settings, "MSG91_OTP_LENGTH", 4)  # 4-digit OTP


def is_configured():
    return bool(_authkey() and _template_id())


def _normalize_mobile(phone: str) -> str:
    """Ensure mobile is digits with country code (no + or spaces)."""
    return "".join(c for c in phone.strip() if c.isdigit()) or phone.strip()


def send_otp(phone: str, template_params: dict | None = None) -> tuple[bool, str]:
    """
    Ask MSG91 to send OTP to the given phone. We do not generate or store OTP.
    Returns (success, message).
    """
    authkey = _authkey()
    template_id = _template_id()
    if not authkey or not template_id:
        return False, "MSG91 not configured (MSG91_AUTH_KEY, MSG91_OTP_TEMPLATE_ID)."

    mobile = _normalize_mobile(phone)
    if not mobile:
        return False, "Invalid mobile number."

    expiry = _otp_expiry()
    otp_len = _otp_length()
    query = urllib.parse.urlencode({
        "mobile": mobile,
        "authkey": authkey,
        "template_id": template_id,
        "otp_expiry": str(expiry),
        "otp_length": str(min(9, max(4, otp_len))),
        "realTimeResponse": "1",
    })
    url = f"https://{MSG91_HOST}{SEND_PATH}?{query}"

    payload = template_params or {}
    body = json.dumps(payload).encode("utf-8") if payload else b""

    req = urllib.request.Request(
        url,
        data=body if body else None,
        method="POST",
        headers={
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8")
            try:
                out = json.loads(data)
                if out.get("type") == "success" or out.get("request_id"):
                    logger.info("MSG91 OTP sent to %s***", mobile[:3])
                    return True, "OTP sent."
                return False, out.get("message", data) or "Send failed."
            except json.JSONDecodeError:
                return False, data or "Send failed."
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
            out = json.loads(body)
            msg = out.get("message", out.get("detail", body))
        except Exception:
            msg = str(e)
        logger.warning("MSG91 send OTP HTTP error %s: %s", e.code, msg)
        return False, msg
    except Exception as e:
        logger.exception("MSG91 send OTP error")
        return False, str(e)


def verify_otp(phone: str, otp: str) -> tuple[bool, str]:
    """
    Ask MSG91 to verify the OTP for the given phone. We do not store OTP.
    Returns (success, message).
    """
    authkey = _authkey()
    if not authkey:
        return False, "MSG91 not configured."

    mobile = _normalize_mobile(phone)
    if not mobile or not (otp or "").strip():
        return False, "Invalid mobile or OTP."

    query = urllib.parse.urlencode({
        "mobile": mobile,
        "otp": otp.strip(),
    })
    url = f"https://{MSG91_HOST}{VERIFY_PATH}?{query}"

    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "authkey": authkey,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("utf-8")
            try:
                out = json.loads(data)
                if out.get("type") == "success":
                    return True, "Verified."
                return False, out.get("message", "Invalid or expired OTP.")
            except json.JSONDecodeError:
                return False, "Verify failed."
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
            out = json.loads(body)
            msg = out.get("message", out.get("detail", body))
        except Exception:
            msg = str(e)
        return False, msg
    except Exception as e:
        logger.exception("MSG91 verify OTP error")
        return False, str(e)
