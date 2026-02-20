# config.py
# System-wide configuration for SHRDAA

import os

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")

# Database file paths
ACCOUNTS_CSV = os.path.join(DATABASE_DIR, "accounts.csv")
LEDGER_CSV = os.path.join(DATABASE_DIR, "ledger.csv")
BLOCKCHAIN_CSV = os.path.join(DATABASE_DIR, "blockchain.csv")
PROJECT_DIS_CSV = os.path.join(DATABASE_DIR, "project_dis.csv")

# User role identifiers (implicit via 'rank' field in accounts.csv)
ROLE_GOVT_OFFICER = "Govt_officer"
ROLE_BENEFICIARY = "Beneficiary"
ROLE_AUDITOR = "Auditor"

# Default balances
DEFAULT_BALANCE_GOVT_OFFICER = 100_000_000
DEFAULT_BALANCE_BENEFICIARY = 1_000_000

# Cryptographic settings
HASH_ALGORITHM = "sha256"

# Ledger rules
VERIFICATION_PENDING = "pending"
VERIFICATION_DONE = "done"

# Session settings (single-user demo)
SESSION_ACTIVE = True

