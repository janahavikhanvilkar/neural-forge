import os
from flask import Flask, render_template, jsonify
from config import Config
from models.models import db, User
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.invoices import invoices_bp
from routes.leads import leads_bp
from routes.resumes import resumes_bp
from routes.support import support_bp
from routes.hitl import hitl_bp
from routes.workflows import workflows_bp
from routes.analytics import analytics_bp
from routes.settings import settings_bp
from routes.api import api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(resumes_bp)
    app.register_blueprint(support_bp)
    app.register_blueprint(hitl_bp)
    app.register_blueprint(workflows_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)

    # Global Template Context
    @app.context_processor
    def inject_global_vars():
        from models.models import HITLReview
        try:
            pending_hitl_count = HITLReview.query.filter_by(action='Pending').count()
        except Exception:
            pending_hitl_count = 0
        return dict(
            pending_hitl_count=pending_hitl_count,
            min=min,
            max=max,
            round=round
        )

    # Custom Jinja Filters
    @app.template_filter('format_currency')
    def format_currency(value):
        try:
            return f"${float(value):,.2f}"
        except (ValueError, TypeError):
            return "$0.00"

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('base.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred.'}), 500

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({'error': 'File too large', 'message': 'Uploaded file exceeds the 16MB maximum size limit.'}), 413

    # Database Initialization & Auto-Seeding
    with app.app_context():
        db.create_all()
        # Seed initial demo data if database is fresh
        if User.query.count() == 0:
            from database.seed_data import seed_demo_database
            seed_demo_database()

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    print(f"[SmartBiz] Starting Automation Server on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
