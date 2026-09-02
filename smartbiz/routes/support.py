from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models.models import db, SupportTicket, HITLReview
from services.support_service import SupportService
from utils.helpers import login_required, log_activity

support_bp = Blueprint('support', __name__)

@support_bp.route('/support')
@login_required
def index():
    cat_filter = request.args.get('category', 'all')
    prio_filter = request.args.get('priority', 'all')
    dept_filter = request.args.get('department', 'all')
    search_query = request.args.get('q', '').strip()

    query = SupportTicket.query
    if cat_filter != 'all':
        query = query.filter_by(category=cat_filter)
    if prio_filter != 'all':
        query = query.filter_by(priority=prio_filter)
    if dept_filter != 'all':
        query = query.filter_by(department=dept_filter)
    if search_query:
        query = query.filter(
            (SupportTicket.ticket_number.ilike(f'%{search_query}%')) |
            (SupportTicket.subject.ilike(f'%{search_query}%')) |
            (SupportTicket.customer_name.ilike(f'%{search_query}%')) |
            (SupportTicket.description.ilike(f'%{search_query}%'))
        )

    tickets = query.order_by(SupportTicket.created_at.desc()).all()

    total_tickets = SupportTicket.query.count()
    open_tickets = SupportTicket.query.filter_by(status='Open').count()
    pending_review = SupportTicket.query.filter_by(status='Pending Review').count()
    resolved_tickets = SupportTicket.query.filter_by(status='Resolved').count()

    return render_template(
        'support.html',
        tickets=tickets,
        cat_filter=cat_filter,
        prio_filter=prio_filter,
        dept_filter=dept_filter,
        search_query=search_query,
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        pending_review=pending_review,
        resolved_tickets=resolved_tickets
    )

@support_bp.route('/support/create', methods=['POST'])
@login_required
def create_ticket():
    data = {
        'customer_name': request.form.get('customer_name'),
        'email': request.form.get('email'),
        'subject': request.form.get('subject'),
        'description': request.form.get('description')
    }

    try:
        ticket = SupportService.create_and_classify_ticket(data)
        flash(f"Ticket {ticket.ticket_number} created & classified! Category: {ticket.category}, Priority: {ticket.priority}, Sentiment: {ticket.sentiment}. Routed to {ticket.department}.", "success")
    except Exception as e:
        flash(f"Error creating ticket: {str(e)}", "danger")

    return redirect(url_for('support.index'))

@support_bp.route('/support/<int:ticket_id>/regenerate-response', methods=['POST'])
@login_required
def regenerate(ticket_id):
    try:
        new_resp = SupportService.regenerate_response(ticket_id)
        return jsonify({'success': True, 'response': new_resp})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@support_bp.route('/support/<int:ticket_id>/send-response', methods=['POST'])
@login_required
def send_response(ticket_id):
    response_text = request.form.get('ai_response', '').strip()
    user_name = session.get('user_name', 'Support Specialist')

    if not response_text:
        flash("Response content cannot be empty.", "warning")
        return redirect(url_for('support.index'))

    try:
        ticket = SupportService.approve_and_send_response(ticket_id, response_text, user_name)
        flash(f"✅ Approved & sent response for Ticket {ticket.ticket_number} to {ticket.customer_name} ({ticket.email})! Status marked as Resolved.", "success")
    except Exception as e:
        flash(f"Error sending response: {str(e)}", "danger")

    return redirect(url_for('support.index'))

@support_bp.route('/support/<int:ticket_id>/status', methods=['POST'])
@login_required
def update_status(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    new_status = request.form.get('status')
    if new_status:
        ticket.status = new_status
        db.session.commit()
        log_activity("Ticket Status Updated", "Support", f"Ticket {ticket.ticket_number} status changed to {new_status}", "Info")
        flash(f"Ticket status updated to {new_status}.", "success")
    return redirect(url_for('support.index'))
