from flask import Blueprint, render_template
from models.models import Invoice, Lead, Resume, SupportTicket, HITLReview
from utils.helpers import login_required

workflows_bp = Blueprint('workflows', __name__)

@workflows_bp.route('/workflows')
@login_required
def index():
    # Pipeline stage metrics
    invoice_metrics = {
        'total': Invoice.query.count(),
        'auto_processed': Invoice.query.filter_by(status='Processed').count(),
        'hitl_reviewed': HITLReview.query.filter_by(task_type='invoice').count(),
        'approved': Invoice.query.filter_by(status='Approved').count(),
        'rejected': Invoice.query.filter_by(status='Rejected').count()
    }

    lead_metrics = {
        'total': Lead.query.count(),
        'hot_sales': Lead.query.filter_by(category='HOT').count(),
        'warm_sales': Lead.query.filter_by(category='WARM').count(),
        'cold_nurture': Lead.query.filter_by(category='COLD').count()
    }

    resume_metrics = {
        'total': Resume.query.count(),
        'strong': Resume.query.filter_by(recommendation='Strong Match').count(),
        'review': Resume.query.filter_by(recommendation='Review').count(),
        'low': Resume.query.filter_by(recommendation='Low Match').count(),
        'shortlisted': Resume.query.filter_by(status='Shortlisted').count()
    }

    ticket_metrics = {
        'total': SupportTicket.query.count(),
        'open': SupportTicket.query.filter_by(status='Open').count(),
        'hitl_review': SupportTicket.query.filter_by(status='Pending Review').count(),
        'resolved': SupportTicket.query.filter_by(status='Resolved').count()
    }

    return render_template(
        'workflows.html',
        invoice_metrics=invoice_metrics,
        lead_metrics=lead_metrics,
        resume_metrics=resume_metrics,
        ticket_metrics=ticket_metrics
    )
