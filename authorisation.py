# authorisation.py
# Authentication and authorization handling for SHRDAA

import hashlib
from typing import Optional

import database
import coresystem


# ---------- Session State (Single User Demo) ----------

_active_account_no: Optional[str] = None


# ---------- Internal Helpers ----------

def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _get_account(account_no: str):
    for acc in database.read_accounts():
        if acc["account_no"] == account_no:
            return acc
    return None


# ---------- Login / Logout ----------

def login(account_no: str, password: str) -> bool:
    """
    Validates credentials.
    On success, overrides any existing session.
    """
    global _active_account_no

    acc = _get_account(account_no)
    if not acc:
        _active_account_no = None
        return False

    if _sha256(password) != acc["password_hash"]:
        _active_account_no = None
        return False

    _active_account_no = account_no
    return True


def logout() -> None:
    global _active_account_no
    _active_account_no = None


def is_logged_in() -> bool:
    return _active_account_no is not None


def current_account_no() -> Optional[str]:
    return _active_account_no


# ---------- Transaction Authorization ----------

def authorize_transaction(password: str) -> bool:
    """
    Re-validates password for the currently logged-in user
    before allowing a transaction.
    """
    if not is_logged_in():
        return False

    acc = _get_account(_active_account_no)
    if not acc:
        return False

    return _sha256(password) == acc["password_hash"]


# ---------- Role Access Helpers ----------

def current_user_role() -> Optional[str]:
    """
    Returns resolved role of the active user.
    """
    if not is_logged_in():
        return None

    acc = _get_account(_active_account_no)
    if not acc:
        return None

    return coresystem.resolve_user_role(acc["rank"])


def current_user_info():
    """
    Returns full account row of active user.
    """
    if not is_logged_in():
        return None

    return _get_account(_active_account_no)

