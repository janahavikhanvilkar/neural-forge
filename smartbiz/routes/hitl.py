import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models.models import db, HITLReview, Invoice, Lead, Resume, SupportTicket
from services.hitl_service import HITLService
from utils.helpers import login_required, log_activity

hitl_bp = Blueprint('hitl', __name__)

@hitl_bp.route('/hitl')
@login_required
def index():
    type_filter = request.args.get('type', 'all')
    status_filter = request.args.get('status', 'Pending')

    query = HITLReview.query
    if type_filter != 'all':
        query = query.filter_by(task_type=type_filter)
    if status_filter != 'all':
        query = query.filter_by(action=status_filter)

    reviews = query.order_by(HITLReview.created_at.desc()).all()

    pending_count = HITLReview.query.filter_by(action='Pending').count()
    approved_count = HITLReview.query.filter_by(action='Approved').count()
    rejected_count = HITLReview.query.filter_by(action='Rejected').count()
    total_reviews = HITLReview.query.count()

    return render_template(
        'hitl.html',
        reviews=reviews,
        type_filter=type_filter,
        status_filter=status_filter,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        total_reviews=total_reviews
    )

@hitl_bp.route('/hitl/<int:review_id>/resolve', methods=['POST'])
@login_required
def resolve(review_id):
    action = request.form.get('action', 'Approved')
    comment = request.form.get('comment', '').strip()
    new_dept = request.form.get('assigned_department')
    
    # Check if any field modifications were submitted
    changes = {}
    for key, val in request.form.items():
        if key.startswith('field_'):
            field_name = key.replace('field_', '')
            changes[field_name] = val

    reviewer_id = session.get('user_id')
    reviewer_name = session.get('user_name', 'Human Reviewer')

    try:
        review = HITLService.resolve_review(
            review_id=review_id,
            action=action,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            comment=comment,
            changes=changes if changes else None,
            new_dept=new_dept
        )
        flash(f"HITL task #{review.id} ({review.task_type.capitalize()}) resolved with action '{action}'.", "success")
    except Exception as e:
        flash(f"Error resolving HITL task: {str(e)}", "danger")

    return redirect(url_for('hitl.index'))
