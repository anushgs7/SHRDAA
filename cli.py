import os
import sys
import time
import getpass

import database
import authorisation
import coresystem
import config


# ---------- UI Helpers ----------

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nPress ENTER to continue...")


def header(title):
    clear()
    print("=" * 80)
    print(f"{title.center(80)}")
    print("=" * 80)


def table(headers, rows):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, col in enumerate(row):
            widths[i] = max(widths[i], len(str(col)))

    fmt = " | ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("-" * (sum(widths) + 3 * (len(widths) - 1)))

    for row in rows:
        print(fmt.format(*row))


# ---------- Pages ----------

def home_page():
    while True:
        header("SHRDAA – Secure High-Integrity Registry")
        print("1. Login")
        print("2. View Public Ledger")
        print("0. Exit")

        choice = input("\nSelect option: ").strip()
        if choice == "1":
            login_page()
        elif choice == "2":
            public_ledger_page()
        elif choice == "0":
            sys.exit()
        else:
            pause()


# ---------- Login ----------

def login_page():
    header("Login")
    acc = input("Account No: ").strip()
    pwd = getpass.getpass("Password: ")

    if authorisation.login(acc, pwd):
        role = authorisation.current_user_role()
        if role == config.ROLE_GOVT_OFFICER:
            govt_dashboard()
        elif role == config.ROLE_AUDITOR:
            auditor_dashboard()
        else:
            beneficiary_dashboard()
    else:
        print("\nInvalid credentials.")
        pause()


# ---------- Public Ledger ----------

def public_ledger_page():
    while True:
        header("Public Ledger – Projects")
        projects = coresystem.get_all_projects()

        if not projects:
            print("No projects available.")
            pause()
            return

        for i, p in enumerate(projects, 1):
            print(f"{i}. {p['project_no']} – {p['project_description']}")

        print("0. Back")
        choice = input("\nSelect project: ").strip()

        if choice == "0":
            return

        if choice.isdigit() and 1 <= int(choice) <= len(projects):
            view_transactions(projects[int(choice) - 1]["project_no"])
        else:
            pause()


def view_transactions(project_no):
    header(f"Transactions – {project_no}")
    txs = coresystem.get_ledger_by_project(project_no)

    if not txs:
        print("No transactions.")
    else:
        table(
            ["Txn No", "From", "To", "Amount", "Time", "Status"],
            [
                (
                    t["transaction_no"],
                    t["from_account_no"],
                    t["to_account_no"],
                    t["amount"],
                    t["timestamp"],
                    t["verification_status"],
                )
                for t in txs
            ],
        )
    pause()


# ---------- Govt Officer ----------

def govt_dashboard():
    while True:
        header("Government Officer Dashboard")
        print("1. Add New User")
        print("2. View My Projects")
        print("3. Make Transaction")
        print("4. Make Project")
        print("0. Logout")

        c = input("\nSelect option: ").strip()
        if c == "1":
            add_user_page()
        elif c == "2":
            user_projects_page()
        elif c == "3":
            make_transaction_page()
        elif c == "4":
            make_project_page()
        elif c == "0":
            authorisation.logout()
            return
        else:
            pause()


def add_user_page():
    header("Add New User")

    name = input("Name: ")
    age = input("Age: ")
    loc = input("Location: ")
    rank = input("Rank / Company: ")
    pwd = getpass.getpass("Password: ")
    bal = input("Initial Balance (leave blank for default): ").strip() or None

    acc = coresystem.create_user(name, age, loc, rank, pwd, bal)
    print(f"\nUser created successfully.")
    print(f"Account No: {acc['account_no']}")
    pause()


def user_projects_page():
    acc = authorisation.current_account_no()
    pnos = coresystem.get_user_projects(acc)

    header("Your Projects")
    if not pnos:
        print("No assigned projects.")
        pause()
        return

    projects = coresystem.get_all_projects()
    mapping = [p for p in projects if p["project_no"] in pnos]

    for i, p in enumerate(mapping, 1):
        print(f"{i}. {p['project_no']} – {p['project_description']}")

    c = input("\nSelect project (0 back): ").strip()
    if c.isdigit() and c != "0":
        view_transactions(mapping[int(c) - 1]["project_no"])


def make_transaction_page():
    header("Make Transaction")

    to_acc = input("To Account No: ")
    amt = float(input("Amount: "))
    proj = input("Project No: ")
    pwd = getpass.getpass("Confirm Password: ")

    if not authorisation.authorize_transaction(pwd):
        print("Authorization failed.")
        pause()
        return

    try:
        coresystem.process_transaction(
            authorisation.current_account_no(),
            to_acc,
            proj,
            amt,
        )
        print("Transaction successful.")
    except Exception as e:
        print(f"Error: {e}")
    pause()


def make_project_page():
    header("Create New Project")

    print("Enter account numbers to authorize for this project.")
    print("Separate multiple accounts with commas (e.g. A00001,A00002)")
    acc_input = input("Authorized Account Nos: ").strip()

    if not acc_input:
        print("No accounts provided.")
        pause()
        return

    account_nos = [a.strip() for a in acc_input.split(",") if a.strip()]

    project_description = input("Project Description: ").strip()
    if not project_description:
        print("Project description cannot be empty.")
        pause()
        return

    try:
        project_no = coresystem.create_project(
            account_nos=account_nos,
            project_description=project_description,
        )
        print(f"\nProject created successfully.")
        print(f"Project No: {project_no}")
    except Exception as e:
        print(f"Error creating project: {e}")

    pause()



# ---------- Auditor ----------

def auditor_dashboard():
    while True:
        header("Auditor Dashboard")
        print("1. View Projects")
        print("2. Verify Transaction")
        print("0. Logout")

        c = input("\nSelect option: ").strip()
        if c == "1":
            public_ledger_page()
        elif c == "2":
            verify_transaction_page()
        elif c == "0":
            authorisation.logout()
            return
        else:
            pause()


def verify_transaction_page():
    header("Verify Transaction")
    txn = input("Transaction No: ").strip()

    try:
        ok = coresystem.verify_transaction(txn)
        print("Verified successfully." if ok else "Verification failed.")
    except Exception as e:
        print(e)
    pause()


# ---------- Beneficiary ----------

def beneficiary_dashboard():
    while True:
        header("Beneficiary Dashboard")
        print("1. View Projects")
        print("0. Logout")

        c = input("\nSelect option: ").strip()
        if c == "1":
            user_projects_page()
        elif c == "0":
            authorisation.logout()
            return
        else:
            pause()


# ---------- Boot ----------

if __name__ == "__main__":
    database.init_all()
    home_page()

