from flask import Blueprint, request, jsonify, session
from models.models import db, Invoice, Lead, Resume, SupportTicket, Notification, ActivityLog
from utils.helpers import login_required

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/search')
@login_required
def global_search():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify({'results': []})

    results = []

    # Invoices
    invoices = Invoice.query.filter(
        (Invoice.invoice_number.ilike(f'%{q}%')) |
        (Invoice.vendor.ilike(f'%{q}%')) |
        (Invoice.customer_name.ilike(f'%{q}%'))
    ).limit(3).all()
    for inv in invoices:
        results.append({
            'type': 'Invoice',
            'title': f"Invoice #{inv.invoice_number or inv.id} - {inv.vendor}",
            'subtitle': f"${inv.total:,.2f} ({inv.status})",
            'link': f"/invoices/{inv.id}",
            'badge': inv.status
        })

    # Leads
    leads = Lead.query.filter(
        (Lead.name.ilike(f'%{q}%')) |
        (Lead.company.ilike(f'%{q}%')) |
        (Lead.email.ilike(f'%{q}%'))
    ).limit(3).all()
    for lead in leads:
        results.append({
            'type': 'Lead',
            'title': f"{lead.name} @ {lead.company}",
            'subtitle': f"Score: {lead.score}/100 ({lead.category})",
            'link': f"/leads",
            'badge': lead.category
        })

    # Resumes
    resumes = Resume.query.filter(
        (Resume.candidate_name.ilike(f'%{q}%')) |
        (Resume.skills.ilike(f'%{q}%'))
    ).limit(3).all()
    for res in resumes:
        results.append({
            'type': 'Resume',
            'title': f"{res.candidate_name}",
            'subtitle': f"Match: {res.match_score}% ({res.recommendation})",
            'link': f"/resumes",
            'badge': res.recommendation
        })

    # Support Tickets
    tickets = SupportTicket.query.filter(
        (SupportTicket.ticket_number.ilike(f'%{q}%')) |
        (SupportTicket.subject.ilike(f'%{q}%')) |
        (SupportTicket.customer_name.ilike(f'%{q}%'))
    ).limit(3).all()
    for t in tickets:
        results.append({
            'type': 'Ticket',
            'title': f"{t.ticket_number}: {t.subject}",
            'subtitle': f"[{t.priority}] {t.category} - {t.department}",
            'link': f"/support",
            'badge': t.priority
        })

    return jsonify({'results': results})

@api_bp.route('/api/notifications')
@login_required
def get_notifications():
    user_role = session.get('role', 'admin').lower()
    notifs = Notification.query.filter(
        (Notification.role_target == 'all') |
        (Notification.role_target == user_role) |
        (Notification.user_id == session.get('user_id'))
    ).order_by(Notification.created_at.desc()).limit(10).all()

    unread_count = sum(1 for n in notifs if not n.is_read)
    return jsonify({
        'unread_count': unread_count,
        'notifications': [n.to_dict() for n in notifs]
    })

@api_bp.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    user_role = session.get('role', 'admin').lower()
    notifs = Notification.query.filter(
        (Notification.role_target == 'all') |
        (Notification.role_target == user_role) |
        (Notification.user_id == session.get('user_id'))
    ).all()
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return jsonify({'success': True})
