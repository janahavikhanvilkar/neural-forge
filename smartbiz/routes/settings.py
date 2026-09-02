import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.models import db, SystemSetting
from services.ai_service import ai_service
from utils.helpers import login_required, role_required, log_activity

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def index():
    auto_thresh = SystemSetting.query.filter_by(key='AUTO_PROCESS_THRESHOLD').first()
    review_thresh = SystemSetting.query.filter_by(key='HITL_REVIEW_THRESHOLD').first()

    settings_dict = {
        'auto_thresh': auto_thresh.value if auto_thresh else '80',
        'review_thresh': review_thresh.value if review_thresh else '60',
        'gemini_configured': bool(os.getenv("GEMINI_API_KEY") or ai_service.api_key),
        'api_key_masked': f"{ai_service.api_key[:4]}...{ai_service.api_key[-4:]}" if ai_service.api_key and len(ai_service.api_key) > 8 else "Not configured (Using Heuristic Fallback Engine)"
    }
    return render_template('settings.html', settings=settings_dict)

@settings_bp.route('/settings/update-thresholds', methods=['POST'])
@login_required
def update_thresholds():
    auto_val = request.form.get('auto_process_threshold', '80')
    review_val = request.form.get('hitl_review_threshold', '60')

    s_auto = SystemSetting.query.filter_by(key='AUTO_PROCESS_THRESHOLD').first()
    if not s_auto:
        s_auto = SystemSetting(key='AUTO_PROCESS_THRESHOLD', value=auto_val, description="Threshold above which items auto-process")
        db.session.add(s_auto)
    else:
        s_auto.value = auto_val

    s_review = SystemSetting.query.filter_by(key='HITL_REVIEW_THRESHOLD').first()
    if not s_review:
        s_review = SystemSetting(key='HITL_REVIEW_THRESHOLD', value=review_val, description="Threshold below which items require mandatory HITL review")
        db.session.add(s_review)
    else:
        s_review.value = review_val

    db.session.commit()
    log_activity("Settings Updated", "System", f"Updated thresholds: Auto-Process={auto_val}%, Review={review_val}%", "Info")
    flash("System automation thresholds updated successfully.", "success")
    return redirect(url_for('settings.index'))

@settings_bp.route('/settings/test-ai', methods=['POST'])
@login_required
def test_ai():
    test_prompt = "Say 'SmartBiz AI connected successfully!' in 5 words."
    res = ai_service.call_gemini(test_prompt)
    if res:
        return jsonify({'success': True, 'message': f"Gemini API Response: {res}"})
    else:
        return jsonify({'success': False, 'message': "Gemini API key not configured or unreachable. Intelligent local fallback engine is active."})
