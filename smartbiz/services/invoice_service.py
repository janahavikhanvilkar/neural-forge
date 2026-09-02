import os
import json
from pathlib import Path
from models.models import db, Invoice, HITLReview
from services.ai_service import ai_service
from utils.file_parser import extract_text_from_file, clean_extracted_text
from utils.helpers import log_activity, create_notification, get_system_thresholds

class InvoiceService:
    @staticmethod
    def process_invoice_file(file_path: str, original_filename: str) -> Invoice:
        """Parses an invoice file, extracts structured data via AI, and applies HITL/routing rules."""
        raw_text = clean_extracted_text(extract_text_from_file(file_path))
        file_ext = Path(file_path).suffix.lower().replace('.', '')

        # AI Extraction
        extracted = ai_service.extract_invoice_data(raw_text, original_filename)

        invoice_number = extracted.get('invoice_number', '').strip()
        vendor = extracted.get('vendor', 'Unknown Vendor').strip()
        customer = extracted.get('customer_name', '').strip()
        invoice_date = extracted.get('invoice_date', '')
        due_date = extracted.get('due_date', '')
        subtotal = float(extracted.get('subtotal', 0) or 0)
        tax = float(extracted.get('tax', 0) or 0)
        total = float(extracted.get('total', 0) or 0)
        currency = extracted.get('currency', 'USD')
        payment_info = extracted.get('payment_info', '')
        confidence = int(extracted.get('confidence', 85))
        validation_flags = extracted.get('validation_flags', [])

        # Business Rule 1: Duplicate check
        if invoice_number:
            existing = Invoice.query.filter_by(invoice_number=invoice_number).first()
            if existing:
                validation_flags.append(f"Duplicate Alert: Invoice number '{invoice_number}' already exists in database (Invoice #{existing.id})")
                confidence = min(confidence, 45)

        # Business Rule 2: Math verification check
        calc_total = round(subtotal + tax, 2)
        if abs(calc_total - round(total, 2)) > 0.05:
            if not any("Math" in f for f in validation_flags):
                validation_flags.append(f"Calculation Error: Subtotal ({subtotal}) + Tax ({tax}) != Total ({total})")
            confidence = min(confidence, 55)

        # Retrieve thresholds
        auto_thresh, review_thresh = get_system_thresholds()

        # Routing and status determination
        needs_hitl = False
        hitl_reason = ""

        if confidence < auto_thresh or any("Alert" in f or "Error" in f or "Discrepancy" in f for f in validation_flags):
            status = 'Needs Review'
            needs_hitl = True
            hitl_reason = "; ".join(validation_flags) if validation_flags else f"Low AI confidence score ({confidence}%)"
        else:
            status = 'Processed'

        # Create Invoice Record
        invoice = Invoice(
            invoice_number=invoice_number,
            vendor=vendor,
            customer_name=customer,
            invoice_date=invoice_date,
            due_date=due_date,
            subtotal=subtotal,
            tax=tax,
            total=total,
            currency=currency,
            payment_info=payment_info,
            file_path=file_path,
            file_name=original_filename,
            file_type=file_ext,
            raw_text=raw_text[:5000],
            extracted_data=json.dumps(extracted),
            validation_flags=json.dumps(validation_flags),
            confidence=confidence,
            status=status,
            assigned_department='Finance'
        )
        db.session.add(invoice)
        db.session.commit()

        # If HITL review required, create HITL task
        if needs_hitl:
            hitl_task = HITLReview(
                task_type='invoice',
                task_id=invoice.id,
                task_title=f"Invoice #{invoice.invoice_number or invoice.id} ({invoice.vendor})",
                reason=hitl_reason,
                confidence=confidence,
                original_data=json.dumps({'file_name': original_filename, 'preview_text': raw_text[:800]}),
                extracted_data=json.dumps(extracted),
                recommended_action="Review vendor amounts, verify taxes, and approve or reject invoice.",
                assigned_department='Finance',
                action='Pending'
            )
            db.session.add(hitl_task)
            db.session.commit()

            create_notification(
                title="Invoice Verification Needed",
                message=f"Invoice '{invoice.invoice_number or invoice.id}' from {invoice.vendor} routed to HITL queue ({confidence}% confidence).",
                module="Invoices",
                role_target="finance",
                link=f"/hitl"
            )
            log_activity("HITL Flagged", "Invoices", f"Invoice #{invoice.id} ({invoice.vendor}) routed to HITL review queue: {hitl_reason}", "Warning")
        else:
            create_notification(
                title="Invoice Auto-Processed",
                message=f"Invoice '{invoice.invoice_number}' for ${invoice.total:,.2f} from {invoice.vendor} successfully verified ({confidence}% confidence).",
                module="Invoices",
                role_target="finance",
                link=f"/invoices/{invoice.id}"
            )
            log_activity("Invoice Processed", "Invoices", f"Invoice #{invoice.id} ({invoice.vendor}) auto-processed with {confidence}% confidence", "Success")

        return invoice

    @staticmethod
    def update_invoice_data(invoice_id: int, form_data: dict, user_id: int = None, user_name: str = "Finance User") -> Invoice:
        invoice = Invoice.query.get_or_404(invoice_id)
        
        # Track changes
        old_data = invoice.to_dict()
        
        invoice.vendor = form_data.get('vendor', invoice.vendor)
        invoice.invoice_number = form_data.get('invoice_number', invoice.invoice_number)
        invoice.customer_name = form_data.get('customer_name', invoice.customer_name)
        invoice.invoice_date = form_data.get('invoice_date', invoice.invoice_date)
        invoice.due_date = form_data.get('due_date', invoice.due_date)
        
        try:
            invoice.subtotal = float(form_data.get('subtotal', invoice.subtotal))
            invoice.tax = float(form_data.get('tax', invoice.tax))
            invoice.total = float(form_data.get('total', invoice.total))
        except ValueError:
            pass

        invoice.currency = form_data.get('currency', invoice.currency)
        invoice.payment_info = form_data.get('payment_info', invoice.payment_info)
        
        # Status change if provided
        new_status = form_data.get('status')
        if new_status and new_status in ['Uploaded', 'Processing', 'Processed', 'Needs Review', 'Approved', 'Rejected']:
            invoice.status = new_status

        db.session.commit()
        log_activity("Invoice Updated", "Invoices", f"Invoice #{invoice.id} details modified by {user_name}", "Info")
        return invoice
