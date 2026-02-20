import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import database
import coresystem
import config

app = Flask(__name__)
app.secret_key = "secure_key_shrdaa_demo"

# Initialize Database files on startup
database.init_all()

# --- Helpers ---
def get_current_user():
    if 'account_no' in session:
        return coresystem._get_account(session['account_no'])
    return None

def login_required(func):
    def wrapper(*args, **kwargs):
        if 'account_no' not in session:
            flash("Please login to access this page.", "warning")
            return redirect(url_for('login_page'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# --- Routes ---

@app.route('/')
def home():
    """Home Page - Landing area."""
    user = get_current_user()
    return render_template('home.html', user=user)

@app.route('/public')
def public_access():
    """Public Access Mode - View Ledger without login."""
    user = get_current_user()
    all_projects = coresystem.get_all_projects()
    return render_template('public.html', user=user, projects=all_projects)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Dedicated Login Page."""
    if request.method == 'POST':
        account_no = request.form.get('account_no')
        password = request.form.get('password')
        user = coresystem._get_account(account_no)
        
        if user and user['password_hash'] == coresystem._sha256(password):
            session['account_no'] = user['account_no']
            session['role'] = coresystem.resolve_user_role(user['rank'])
            flash(f"Welcome back, {user['name']}", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid Credentials", "danger")
            
    return render_template('login.html', user=get_current_user())

@app.route('/dashboard')
@login_required
def dashboard():
    """Private Dashboard for logged in users."""
    user = get_current_user()
    role = session.get('role')
    all_projects = coresystem.get_all_projects()
    
    my_project_ids = coresystem.get_user_projects(user['account_no'])
    my_projects = [p for p in all_projects if p['project_no'] in my_project_ids]

    return render_template('dashboard.html', user=user, role=role, projects=all_projects, my_projects=my_projects)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))

# --- Action Routes ---
@app.route('/ledger/<project_no>')
def view_ledger(project_no):
    transactions = coresystem.get_ledger_by_project(project_no)
    return render_template('partials_transactions.html', transactions=transactions, project_no=project_no)

@app.route('/action/create_user', methods=['POST'])
@login_required
def create_user():
    try:
        acc = coresystem.create_user(
            name=request.form.get('name'),
            age=request.form.get('age'),
            location=request.form.get('location'),
            rank_or_company=request.form.get('rank'),
            password=request.form.get('password'),
            balance=request.form.get('balance') or None
        )
        flash(f"User Created! Account No: {acc['account_no']}", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('dashboard'))

@app.route('/action/create_project', methods=['POST'])
@login_required
def create_project():
    try:
        acc_input = request.form.get('account_nos')
        account_nos = [a.strip() for a in acc_input.split(",") if a.strip()]
        
        p_no = coresystem.create_project(
            account_nos=account_nos,
            project_description=request.form.get('description')
        )
        flash(f"Project Created! Project No: {p_no}", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('dashboard'))

@app.route('/action/transaction', methods=['POST'])
@login_required
def make_transaction():
    try:
        # Re-verify password for security (as per original CLI requirement)
        password = request.form.get('password')
        user = get_current_user()
        if user['password_hash'] != coresystem._sha256(password):
            flash("Transaction Failed: Incorrect Password", "danger")
            return redirect(url_for('dashboard'))

        coresystem.process_transaction(
            from_account_no=user['account_no'],
            to_account_no=request.form.get('to_account'),
            project_no=request.form.get('project_no'),
            amount=float(request.form.get('amount'))
        )
        flash("Transaction Successful!", "success")
    except Exception as e:
        flash(f"Transaction Failed: {str(e)}", "danger")
    return redirect(url_for('dashboard'))

@app.route('/action/verify', methods=['POST'])
@login_required
def verify_transaction():
    try:
        txn_no = request.form.get('transaction_no')
        is_valid = coresystem.verify_transaction(txn_no)
        if is_valid:
            flash(f"Transaction {txn_no} Verified Successfully.", "success")
        else:
            flash(f"Transaction {txn_no} Verification FAILED.", "danger")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('dashboard'))


if __name__ == "__main__":
    app.run(debug=True, port=5000)