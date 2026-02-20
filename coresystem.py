# coresystem.py
# Core business logic for SHRDAA

import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, List

import config
import database


# ---------- Utility Functions ----------

def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- ID Generators ----------

def generate_account_no() -> str:
    accounts = database.read_accounts()
    return f"A{len(accounts) + 1:05d}"


def generate_transaction_no() -> str:
    ledger = database.read_ledger()
    return f"T{len(ledger) + 1:06d}"


def generate_project_no() -> str:
    projects = database.read_project_dis()
    return f"P{len(projects) + 1:05d}"


# ---------- Role Resolution ----------

#def resolve_user_role(rank: str) -> str:
 #   if rank == config.ROLE_AUDITOR:
  #      return config.ROLE_AUDITOR
   # if rank.strip() == "":
    #    return config.ROLE_BENEFICIARY
    #return config.ROLE_GOVT_OFFICER
def resolve_user_role(rank: str) -> str:
    r = rank.strip().lower()

    if r == "auditor":
        return config.ROLE_AUDITOR

    govt_keywords = [
        "collector",
        "secretary",
        "joint secretary",
        "commissioner",
        "officer"
    ]

    for kw in govt_keywords:
        if kw in r:
            return config.ROLE_GOVT_OFFICER

    return config.ROLE_BENEFICIARY


# ---------- User Management ----------

def create_user(
    name: str,
    age: str,
    location: str,
    rank_or_company: str,
    password: str,
    balance: str = None,
) -> Dict[str, str]:

    account_no = generate_account_no()
    password_hash = _sha256(password)

    role = resolve_user_role(rank_or_company)

    if balance is None:
        if role == config.ROLE_GOVT_OFFICER:
            balance = str(config.DEFAULT_BALANCE_GOVT_OFFICER)
        elif role == config.ROLE_BENEFICIARY:
            balance = str(config.DEFAULT_BALANCE_BENEFICIARY)
        else:
            balance = "0"

    account_row = {
        "name": name,
        "account_no": account_no,
        "password_hash": password_hash,
        "balance": balance,
        "age": age,
        "location": location,
        "rank": rank_or_company,
        "authorised_projects_no": "",
    }

    database.append_account(account_row)
    return account_row


# ---------- Project Management ----------

def create_project(
    account_nos: List[str],
    project_description: str,
) -> str:

    project_no = generate_project_no()

    accounts = database.read_accounts()
    for acc in accounts:
        if acc["account_no"] in account_nos:
            existing = acc["authorised_projects_no"]
            updated = (
                project_no
                if existing.strip() == ""
                else f"{existing},{project_no}"
            )
            acc["authorised_projects_no"] = updated

    database.update_accounts(accounts)

    database.append_project_dis(
        {
            "project_no": project_no,
            "project_description": project_description,
        }
    )

    return project_no


# ---------- Transaction Processing ----------

def _get_account(account_no: str) -> Dict[str, str]:
    for acc in database.read_accounts():
        if acc["account_no"] == account_no:
            return acc
    return None


def process_transaction(
    from_account_no: str,
    to_account_no: str,
    project_no: str,
    amount: float,
) -> Dict[str, str]:

    from_acc = _get_account(from_account_no)
    to_acc = _get_account(to_account_no)

    # --- Project authorization check ---
    authorised_projects = from_acc["authorised_projects_no"].split(",") \
        if from_acc["authorised_projects_no"].strip() else []

    if project_no not in authorised_projects:
        raise ValueError("Sender is not authorised for this project")


    if not from_acc or not to_acc:
        raise ValueError("Invalid account")

    from_role = resolve_user_role(from_acc["rank"])
    to_role = resolve_user_role(to_acc["rank"])

    if from_role == config.ROLE_GOVT_OFFICER and to_role in (
        config.ROLE_GOVT_OFFICER,
        config.ROLE_AUDITOR,
    ):
        raise ValueError("Invalid transaction")

    new_balance = float(from_acc["balance"]) - float(amount)
    if new_balance < 0:
        raise ValueError("Invalid transaction")

    from_acc["balance"] = str(new_balance)
    to_acc["balance"] = str(float(to_acc["balance"]) + float(amount))

    accounts = database.read_accounts()
    for acc in accounts:
        if acc["account_no"] == from_account_no:
            acc["balance"] = from_acc["balance"]
        if acc["account_no"] == to_account_no:
            acc["balance"] = to_acc["balance"]

    database.update_accounts(accounts)

    transaction_no = generate_transaction_no()
    timestamp = _current_timestamp()

    ledger_row = {
        "transaction_no": transaction_no,
        "project_no": project_no,
        "from_account_no": from_account_no,
        "to_account_no": to_account_no,
        "amount": str(amount),
        "timestamp": timestamp,
        "verification_status": config.VERIFICATION_PENDING,
    }

    database.append_ledger(ledger_row)

    _append_blockchain_entry(ledger_row)

    return ledger_row


# ---------- Blockchain ----------

def _append_blockchain_entry(ledger_row: Dict[str, str]) -> None:
    chain = database.read_blockchain()
    previous_hash = chain[-1]["current_hash"] if chain else "GENESIS"

    hash_input = (
        f'{ledger_row["transaction_no"]}|'
        f'{ledger_row["project_no"]}|'
        f'{ledger_row["from_account_no"]}|'
        f'{ledger_row["to_account_no"]}|'
        f'{ledger_row["amount"]}|'
        f'{ledger_row["timestamp"]}|'
        f'{previous_hash}'
    )

    current_hash = _sha256(hash_input)

    block = {
        "transaction_no": ledger_row["transaction_no"],
        "project_no": ledger_row["project_no"],
        "previous_hash": previous_hash,
        "current_hash": current_hash,
    }

    database.append_blockchain(block)


# ---------- Verification ----------

def verify_transaction(transaction_no: str) -> bool:
    ledger = database.read_ledger()
    chain = database.read_blockchain()

    ledger_map = {tx["transaction_no"]: tx for tx in ledger}
    chain_map = {blk["transaction_no"]: blk for blk in chain}

    if transaction_no not in ledger_map:
        raise ValueError("Transaction not found")

    tx = ledger_map[transaction_no]

    if tx["verification_status"] == config.VERIFICATION_DONE:
        raise ValueError("Already verified")

    block = chain_map.get(transaction_no)
    if not block:
        return False

    hash_input = (
        f'{tx["transaction_no"]}|'
        f'{tx["project_no"]}|'
        f'{tx["from_account_no"]}|'
        f'{tx["to_account_no"]}|'
        f'{tx["amount"]}|'
        f'{tx["timestamp"]}|'
        f'{block["previous_hash"]}'
    )

    recalculated_hash = _sha256(hash_input)

    verified = recalculated_hash == block["current_hash"]

    if verified:
        for row in ledger:
            if row["transaction_no"] == transaction_no:
                row["verification_status"] = config.VERIFICATION_DONE
        database.update_ledger(ledger)

    return verified


# ---------- Data Fetchers for UI ----------

def get_all_projects() -> List[Dict[str, str]]:
    return database.read_project_dis()


def get_ledger_by_project(project_no: str) -> List[Dict[str, str]]:
    return [
        tx
        for tx in database.read_ledger()
        if tx["project_no"] == project_no
    ]


def get_user_projects(account_no: str) -> List[str]:
    acc = _get_account(account_no)
    if not acc or acc["authorised_projects_no"].strip() == "":
        return []
    return acc["authorised_projects_no"].split(",")


def get_account_info(account_no: str) -> Dict[str, str]:
    return _get_account(account_no)

