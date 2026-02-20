# database.py
# CSV persistence layer for SHRDAA

import csv
import os
from typing import List, Dict
import config


# ---------- Internal Helpers ----------

def _ensure_file_exists(path: str, headers: List[str]) -> None:
    if not os.path.exists(path):
        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()


def _read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _write_csv(path: str, rows: List[Dict[str, str]], headers: List[str]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _append_csv(path: str, row: Dict[str, str], headers: List[str]) -> None:
    with open(path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writerow(row)


# ---------- Accounts ----------

ACCOUNTS_HEADERS = [
    "name",
    "account_no",
    "password_hash",
    "balance",
    "age",
    "location",
    "rank",
    "authorised_projects_no",
]


def init_accounts() -> None:
    _ensure_file_exists(config.ACCOUNTS_CSV, ACCOUNTS_HEADERS)


def read_accounts() -> List[Dict[str, str]]:
    return _read_csv(config.ACCOUNTS_CSV)


def append_account(account_row: Dict[str, str]) -> None:
    _append_csv(config.ACCOUNTS_CSV, account_row, ACCOUNTS_HEADERS)


def update_accounts(rows: List[Dict[str, str]]) -> None:
    _write_csv(config.ACCOUNTS_CSV, rows, ACCOUNTS_HEADERS)


# ---------- Ledger ----------

LEDGER_HEADERS = [
    "transaction_no",
    "project_no",
    "from_account_no",
    "to_account_no",
    "amount",
    "timestamp",
    "verification_status",
]


def init_ledger() -> None:
    _ensure_file_exists(config.LEDGER_CSV, LEDGER_HEADERS)


def read_ledger() -> List[Dict[str, str]]:
    return _read_csv(config.LEDGER_CSV)


def append_ledger(transaction_row: Dict[str, str]) -> None:
    _append_csv(config.LEDGER_CSV, transaction_row, LEDGER_HEADERS)


def update_ledger(rows: List[Dict[str, str]]) -> None:
    _write_csv(config.LEDGER_CSV, rows, LEDGER_HEADERS)


# ---------- Blockchain ----------

BLOCKCHAIN_HEADERS = [
    "transaction_no",
    "project_no",
    "previous_hash",
    "current_hash",
]


def init_blockchain() -> None:
    _ensure_file_exists(config.BLOCKCHAIN_CSV, BLOCKCHAIN_HEADERS)


def read_blockchain() -> List[Dict[str, str]]:
    return _read_csv(config.BLOCKCHAIN_CSV)


def append_blockchain(block_row: Dict[str, str]) -> None:
    _append_csv(config.BLOCKCHAIN_CSV, block_row, BLOCKCHAIN_HEADERS)


# ---------- Project Descriptions ----------

PROJECT_DIS_HEADERS = [
    "project_no",
    "project_description",
]


def init_project_dis() -> None:
    _ensure_file_exists(config.PROJECT_DIS_CSV, PROJECT_DIS_HEADERS)


def read_project_dis() -> List[Dict[str, str]]:
    return _read_csv(config.PROJECT_DIS_CSV)


def append_project_dis(project_row: Dict[str, str]) -> None:
    _append_csv(config.PROJECT_DIS_CSV, project_row, PROJECT_DIS_HEADERS)


# ---------- Global Initializer ----------

def init_all() -> None:
    """
    Initialize all CSV files if they do not exist.
    Must be called once at application startup.
    """
    init_accounts()
    init_ledger()
    init_blockchain()
    init_project_dis()

