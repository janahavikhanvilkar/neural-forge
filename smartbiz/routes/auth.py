from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.models import db, User
from utils.helpers import log_activity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['email'] = user.email
            session['role'] = user.role.lower()
            
            log_activity("User Login", "Auth", f"User {user.name} ({user.email}) logged in successfully as {user.role.upper()}")
            flash(f"Welcome back, {user.name}!", "success")
            
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard.index'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            
    return render_template('login.html')

@auth_bp.route('/quick-login/<role>')
def quick_login(role):
    """Allows one-click demo login for hackathon judges and testing."""
    role = role.lower()
    role_email_map = {
        'admin': 'admin@smartbiz.ai',
        'finance': 'finance@smartbiz.ai',
        'sales': 'sales@smartbiz.ai',
        'hr': 'hr@smartbiz.ai',
        'support': 'support@smartbiz.ai'
    }
    
    email = role_email_map.get(role, 'admin@smartbiz.ai')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Fallback to creating or finding any user with that role
        user = User.query.filter_by(role=role).first()
        
    if user:
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['email'] = user.email
        session['role'] = user.role.lower()
        log_activity("Quick Login", "Auth", f"Quick logged in as {user.name} ({user.role.upper()})")
        flash(f"Logged in as {user.name} ({user.role.upper()} Mode)", "info")
        return redirect(url_for('dashboard.index'))
    
    flash("Demo user not found. Please initialize the database.", "warning")
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    user_name = session.get('user_name', 'User')
    log_activity("User Logout", "Auth", f"User {user_name} logged out")
    session.clear()
    flash("You have been securely logged out.", "info")
    return redirect(url_for('auth.login'))
