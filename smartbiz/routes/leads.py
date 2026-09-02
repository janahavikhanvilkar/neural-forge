from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models.models import db, Lead
from services.lead_service import LeadService
from utils.helpers import login_required, log_activity

leads_bp = Blueprint('leads', __name__)

@leads_bp.route('/leads')
@login_required
def index():
    category_filter = request.args.get('category', 'all')
    search_query = request.args.get('q', '').strip()

    query = Lead.query
    if category_filter != 'all':
        query = query.filter_by(category=category_filter.upper())
    if search_query:
        query = query.filter(
            (Lead.name.ilike(f'%{search_query}%')) |
            (Lead.company.ilike(f'%{search_query}%')) |
            (Lead.email.ilike(f'%{search_query}%'))
        )

    leads = query.order_by(Lead.score.desc(), Lead.created_at.desc()).all()
    
    total_leads = Lead.query.count()
    hot_leads = Lead.query.filter_by(category='HOT').count()
    warm_leads = Lead.query.filter_by(category='WARM').count()
    cold_leads = Lead.query.filter_by(category='COLD').count()

    return render_template(
        'leads.html',
        leads=leads,
        category_filter=category_filter,
        search_query=search_query,
        total_leads=total_leads,
        hot_leads=hot_leads,
        warm_leads=warm_leads,
        cold_leads=cold_leads
    )

@leads_bp.route('/leads/create', methods=['POST'])
@login_required
def create():
    data = {
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'company': request.form.get('company'),
        'industry': request.form.get('industry'),
        'company_size': request.form.get('company_size'),
        'budget': request.form.get('budget', 0),
        'product': request.form.get('product'),
        'source': request.form.get('source'),
        'previous_interaction': request.form.get('previous_interaction'),
        'engagement': request.form.get('engagement')
    }

    try:
        lead = LeadService.create_and_score_lead(data)
        flash(f"🎉 Lead '{lead.name}' created & scored: {lead.score}/100 ({lead.category})! Assigned to {lead.assigned_department}.", "success")
    except Exception as e:
        flash(f"Error creating lead: {str(e)}", "danger")

    return redirect(url_for('leads.index'))

@leads_bp.route('/leads/<int:lead_id>/status', methods=['POST'])
@login_required
def update_status(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    new_status = request.form.get('status')
    if new_status:
        lead.status = new_status
        db.session.commit()
        log_activity("Lead Status Updated", "Leads", f"Lead #{lead.id} ({lead.name}) status updated to {new_status}", "Info")
        flash(f"Lead status updated to {new_status}.", "success")
    return redirect(url_for('leads.index'))
