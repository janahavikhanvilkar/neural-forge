import os
import uuid
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from werkzeug.utils import secure_filename
from models.models import db, Invoice, HITLReview
from services.invoice_service import InvoiceService
from utils.helpers import login_required, role_required, log_activity, create_notification
from config import Config

invoices_bp = Blueprint('invoices', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@invoices_bp.route('/invoices')
@login_required
def index():
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('q', '').strip()

    query = Invoice.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    if search_query:
        query = query.filter(
            (Invoice.invoice_number.ilike(f'%{search_query}%')) |
            (Invoice.vendor.ilike(f'%{search_query}%')) |
            (Invoice.customer_name.ilike(f'%{search_query}%'))
        )

    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    # Stats for invoice header
    total_count = Invoice.query.count()
    approved_count = Invoice.query.filter_by(status='Approved').count()
    processed_count = Invoice.query.filter_by(status='Processed').count()
    review_count = Invoice.query.filter_by(status='Needs Review').count()

    return render_template(
        'invoices.html',
        invoices=invoices,
        status_filter=status_filter,
        search_query=search_query,
        total_count=total_count,
        approved_count=approved_count,
        processed_count=processed_count,
        review_count=review_count
    )

@invoices_bp.route('/invoices/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash("No file part in request.", "danger")
        return redirect(url_for('invoices.index'))
        
    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('invoices.index'))

    if file and allowed_file(file.filename):
        original_name = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex[:8]}_{original_name}"
        save_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)
        file.save(save_path)

        try:
            invoice = InvoiceService.process_invoice_file(save_path, original_name)
            flash(f"Invoice '{original_name}' uploaded and processed successfully! (Confidence: {invoice.confidence}%)", "success")
            return redirect(url_for('invoices.detail', invoice_id=invoice.id))
        except Exception as e:
            flash(f"Error analyzing invoice: {str(e)}", "danger")
            return redirect(url_for('invoices.index'))
    else:
        flash(f"Unsupported file type. Please upload one of: {', '.join(Config.ALLOWED_EXTENSIONS)}", "danger")
        return redirect(url_for('invoices.index'))

@invoices_bp.route('/invoices/<int:invoice_id>')
@login_required
def detail(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    hitl_task = HITLReview.query.filter_by(task_type='invoice', task_id=invoice.id, action='Pending').first()
    return render_template('invoice_detail.html', invoice=invoice, hitl_task=hitl_task)

@invoices_bp.route('/invoices/<int:invoice_id>/update', methods=['POST'])
@login_required
def update(invoice_id):
    user_name = session.get('user_name', 'Finance User')
    form_data = {
        'vendor': request.form.get('vendor'),
        'invoice_number': request.form.get('invoice_number'),
        'customer_name': request.form.get('customer_name'),
        'invoice_date': request.form.get('invoice_date'),
        'due_date': request.form.get('due_date'),
        'subtotal': request.form.get('subtotal'),
        'tax': request.form.get('tax'),
        'total': request.form.get('total'),
        'currency': request.form.get('currency'),
        'payment_info': request.form.get('payment_info'),
        'status': request.form.get('status')
    }
    
    invoice = InvoiceService.update_invoice_data(invoice_id, form_data, session.get('user_id'), user_name)
    flash("Invoice information updated successfully.", "success")
    return redirect(url_for('invoices.detail', invoice_id=invoice.id))

@invoices_bp.route('/invoices/<int:invoice_id>/approve', methods=['POST'])
@login_required
def approve(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'Approved'
    
    # Resolve pending HITL task if any
    hitl_task = HITLReview.query.filter_by(task_type='invoice', task_id=invoice.id, action='Pending').first()
    if hitl_task:
        hitl_task.action = 'Approved'
        hitl_task.reviewer_name = session.get('user_name', 'Finance User')
        hitl_task.comment = "Approved directly from Invoice detail panel."

    db.session.commit()
    log_activity("Invoice Approved", "Invoices", f"Invoice #{invoice.id} ({invoice.vendor}) approved by {session.get('user_name')}", "Success")
    flash(f"Invoice #{invoice.invoice_number or invoice.id} approved successfully.", "success")
    return redirect(url_for('invoices.detail', invoice_id=invoice.id))

@invoices_bp.route('/invoices/<int:invoice_id>/reject', methods=['POST'])
@login_required
def reject(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    reason = request.form.get('rejection_reason', 'Rejected by finance reviewer')
    invoice.status = 'Rejected'
    
    hitl_task = HITLReview.query.filter_by(task_type='invoice', task_id=invoice.id, action='Pending').first()
    if hitl_task:
        hitl_task.action = 'Rejected'
        hitl_task.reviewer_name = session.get('user_name', 'Finance User')
        hitl_task.comment = reason

    db.session.commit()
    log_activity("Invoice Rejected", "Invoices", f"Invoice #{invoice.id} ({invoice.vendor}) rejected: {reason}", "Warning")
    flash(f"Invoice #{invoice.invoice_number or invoice.id} marked as Rejected.", "warning")
    return redirect(url_for('invoices.detail', invoice_id=invoice.id))
