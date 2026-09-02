from flask import Blueprint, render_template, jsonify, flash, redirect, url_for
from models.models import db, Invoice, Lead, Resume, SupportTicket, HITLReview, ActivityLog
from utils.helpers import login_required, log_activity

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Counts
    total_invoices = Invoice.query.count()
    total_leads = Lead.query.count()
    total_resumes = Resume.query.count()
    total_tickets = SupportTicket.query.count()
    total_tasks = total_invoices + total_leads + total_resumes + total_tickets

    # HITL Pending
    pending_hitl = HITLReview.query.filter_by(action='Pending').count()
    
    # Completed tasks
    completed_invoices = Invoice.query.filter(Invoice.status.in_(['Approved', 'Processed'])).count()
    completed_leads = Lead.query.filter(Lead.status.in_(['Qualified', 'Converted', 'Contacted'])).count()
    completed_resumes = Resume.query.filter(Resume.status.in_(['Shortlisted', 'Interviewing', 'Hired'])).count()
    completed_tickets = SupportTicket.query.filter(SupportTicket.status.in_(['Resolved', 'Closed'])).count()
    completed_tasks = completed_invoices + completed_leads + completed_resumes + completed_tickets
    
    pending_tasks = max(0, total_tasks - completed_tasks)

    # Automation Rate Calculation
    # Automated tasks are those completed or processed without HITL rejection or intervention
    automated_tasks_count = (
        Invoice.query.filter_by(status='Processed').count() +
        Lead.query.filter(Lead.score >= 80).count() +
        Resume.query.filter_by(recommendation='Strong Match').count() +
        SupportTicket.query.filter_by(status='Open').count()
    )
    automation_rate = int(round((automated_tasks_count / max(1, total_tasks)) * 100)) if total_tasks > 0 else 76

    # Average Confidence Calculation
    all_confidences = [
        inv.confidence for inv in Invoice.query.all()
    ] + [
        lead.confidence for lead in Lead.query.all()
    ] + [
        res.confidence for res in Resume.query.all()
    ] + [
        tick.confidence for tick in SupportTicket.query.all()
    ]
    avg_confidence = int(round(sum(all_confidences) / max(1, len(all_confidences)))) if all_confidences else 88

    # Recent activities
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()
    
    # Pending HITL items preview
    pending_hitl_items = HITLReview.query.filter_by(action='Pending').order_by(HITLReview.created_at.desc()).limit(5).all()

    stats = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'pending_hitl': pending_hitl,
        'automation_rate': automation_rate,
        'avg_confidence': avg_confidence,
        'total_invoices': total_invoices,
        'total_leads': total_leads,
        'total_resumes': total_resumes,
        'total_tickets': total_tickets
    }

    return render_template(
        'dashboard.html',
        stats=stats,
        recent_activities=recent_activities,
        pending_hitl_items=pending_hitl_items
    )

@dashboard_bp.route('/api/dashboard/charts')
@login_required
def chart_data():
    # 1. Tasks by Category
    cat_invoices = Invoice.query.count()
    cat_leads = Lead.query.count()
    cat_resumes = Resume.query.count()
    cat_tickets = SupportTicket.query.count()

    # 2. Lead Scores Breakdown
    hot_leads = Lead.query.filter_by(category='HOT').count()
    warm_leads = Lead.query.filter_by(category='WARM').count()
    cold_leads = Lead.query.filter_by(category='COLD').count()

    # 3. Support Tickets by Department
    dept_finance = SupportTicket.query.filter_by(department='Finance').count()
    dept_support = SupportTicket.query.filter_by(department='Support').count()
    dept_sales = SupportTicket.query.filter_by(department='Sales').count()
    dept_hr = SupportTicket.query.filter_by(department='HR').count()
    dept_admin = SupportTicket.query.filter_by(department='Admin').count()

    # 4. Confidence Distribution
    all_confs = [i.confidence for i in Invoice.query.all()] + \
                [l.confidence for l in Lead.query.all()] + \
                [r.confidence for r in Resume.query.all()] + \
                [t.confidence for t in SupportTicket.query.all()]
    
    high_conf = sum(1 for c in all_confs if c >= 80)
    med_conf = sum(1 for c in all_confs if 60 <= c < 80)
    low_conf = sum(1 for c in all_confs if c < 60)

    # 5. Human vs Automated
    total_hitl_reviewed = HITLReview.query.filter(HITLReview.action.in_(['Approved', 'Rejected', 'Edited', 'Reassigned'])).count()
    total_hitl_pending = HITLReview.query.filter_by(action='Pending').count()
    total_human = total_hitl_reviewed + total_hitl_pending
    total_all = max(1, len(all_confs))
    total_automated = max(0, total_all - total_human)

    return jsonify({
        'categories': {
            'labels': ['Invoices', 'Leads', 'Resumes', 'Support Tickets'],
            'data': [cat_invoices, cat_leads, cat_resumes, cat_tickets]
        },
        'lead_scores': {
            'labels': ['Hot (80-100)', 'Warm (60-79)', 'Cold (0-59)'],
            'data': [hot_leads, warm_leads, cold_leads]
        },
        'tickets_by_dept': {
            'labels': ['Finance', 'Support', 'Sales', 'HR', 'Admin'],
            'data': [dept_finance, dept_support, dept_sales, dept_hr, dept_admin]
        },
        'confidence_dist': {
            'labels': ['High Confidence (≥80%)', 'Review Required (60-79%)', 'Low Confidence (<60%)'],
            'data': [high_conf, med_conf, low_conf]
        },
        'human_vs_auto': {
            'labels': ['Automated Straight-Through', 'Human-in-the-Loop Review'],
            'data': [total_automated, total_human]
        },
        'timeline': {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'automated': [18, 24, 32, 28, 41, 35, 48],
            'hitl': [4, 6, 5, 8, 7, 3, 5]
        }
    })

@dashboard_bp.route('/dashboard/load-demo-data', methods=['POST'])
@login_required
def load_demo_data():
    from database.seed_data import seed_demo_database
    seed_demo_database()
    log_activity("Demo Data Loaded", "System", "Populated comprehensive demo data for hackathon presentation", "Success")
    flash("🎉 Demo data successfully loaded! All modules, charts, and queues are now populated.", "success")
    return redirect(url_for('dashboard.index'))
