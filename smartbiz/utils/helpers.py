from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify, g
from models.models import db, ActivityLog, Notification, SystemSetting, User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Authentication required'}), 401
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))
            user_role = session.get('role', '').lower()
            if user_role != 'admin' and user_role not in [r.lower() for r in allowed_roles]:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Unauthorized for your role'}), 403
                flash(f'Access restricted. Requires one of: {", ".join(allowed_roles)}', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def log_activity(action: str, module: str, description: str, status: str = "Success"):
    """Records an action in the centralized ActivityLog table."""
    try:
        from flask import has_request_context
        user_id = None
        user_name = "System"
        role = "system"
        ip_addr = "127.0.0.1"

        if has_request_context():
            user_id = session.get('user_id')
            user_name = session.get('user_name', 'System')
            role = session.get('role', 'system')
            ip_addr = request.remote_addr or '127.0.0.1'
        
        log_entry = ActivityLog(
            user_id=user_id,
            user_name=user_name,
            role=role,
            action=action,
            module=module,
            description=description,
            status=status,
            ip_address=ip_addr
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to log activity: {e}")

def create_notification(title: str, message: str, module: str = "System", role_target: str = "all", link: str = None):
    """Dispatches a notification to users or roles."""
    try:
        notif = Notification(
            title=title,
            message=message,
            module=module,
            role_target=role_target,
            link=link or '#',
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to create notification: {e}")

def get_system_thresholds():
    """Retrieves current confidence thresholds from DB or defaults."""
    auto_thresh = 80
    review_thresh = 60
    try:
        s_auto = SystemSetting.query.filter_by(key='AUTO_PROCESS_THRESHOLD').first()
        s_review = SystemSetting.query.filter_by(key='HITL_REVIEW_THRESHOLD').first()
        if s_auto:
            auto_thresh = int(s_auto.value)
        if s_review:
            review_thresh = int(s_review.value)
    except Exception:
        pass
    return auto_thresh, review_thresh
