from datetime import datetime
import json
from models.models import db, HITLReview, Invoice, Lead, Resume, SupportTicket
from utils.helpers import log_activity, create_notification

class HITLService:
    @staticmethod
    def resolve_review(review_id: int, action: str, reviewer_id: int = None, reviewer_name: str = "Human Reviewer", comment: str = "", changes: dict = None, new_dept: str = None) -> HITLReview:
        """Processes human-in-the-loop review decision and synchronizes target entity."""
        review = HITLReview.query.get_or_404(review_id)
        
        review.action = action  # Approved, Rejected, Edited, Reassigned
        review.reviewer_id = reviewer_id
        review.reviewer_name = reviewer_name
        review.comment = comment
        review.completed_at = datetime.utcnow()
        
        if changes:
            review.changes_made = json.dumps(changes)
            
        if new_dept:
            review.assigned_department = new_dept

        # Synchronize target entity
        if review.task_type == 'invoice':
            invoice = Invoice.query.get(review.task_id)
            if invoice:
                if action == 'Approved':
                    invoice.status = 'Approved'
                elif action == 'Rejected':
                    invoice.status = 'Rejected'
                elif action == 'Edited' and changes:
                    for k, v in changes.items():
                        if hasattr(invoice, k):
                            setattr(invoice, k, v)
                    invoice.status = 'Approved'
                if new_dept:
                    invoice.assigned_department = new_dept

        elif review.task_type == 'ticket':
            ticket = SupportTicket.query.get(review.task_id)
            if ticket:
                if action == 'Approved':
                    ticket.status = 'Resolved'
                    ticket.ai_response_status = 'Approved'
                elif action == 'Rejected':
                    ticket.status = 'Closed'
                    ticket.ai_response_status = 'Rejected'
                elif action == 'Edited' and changes:
                    if 'ai_response' in changes:
                        ticket.ai_response = changes['ai_response']
                        ticket.ai_response_status = 'Approved'
                        ticket.status = 'Resolved'
                    if 'priority' in changes:
                        ticket.priority = changes['priority']
                    if 'category' in changes:
                        ticket.category = changes['category']
                if new_dept:
                    ticket.department = new_dept

        elif review.task_type == 'lead':
            lead = Lead.query.get(review.task_id)
            if lead:
                if action == 'Approved':
                    lead.status = 'Qualified'
                elif action == 'Rejected':
                    lead.status = 'Disqualified'
                elif action == 'Edited' and changes:
                    for k, v in changes.items():
                        if hasattr(lead, k):
                            setattr(lead, k, v)
                if new_dept:
                    lead.assigned_department = new_dept

        elif review.task_type == 'resume':
            resume = Resume.query.get(review.task_id)
            if resume:
                if action == 'Approved':
                    resume.status = 'Shortlisted'
                elif action == 'Rejected':
                    resume.status = 'Rejected'
                elif action == 'Edited' and changes:
                    for k, v in changes.items():
                        if hasattr(resume, k):
                            setattr(resume, k, v)

        db.session.commit()

        # Notification & Log
        create_notification(
            title=f"HITL Review {action}",
            message=f"{review.task_type.capitalize()} #{review.task_id} marked as '{action}' by {reviewer_name}. {comment[:80]}",
            module="HITL",
            role_target="all",
            link=f"/hitl"
        )
        log_activity(
            f"HITL {action}", 
            "HITL", 
            f"Resolved {review.task_type} #{review.task_id} with action '{action}' by {reviewer_name}. Note: {comment}", 
            "Success" if action in ('Approved', 'Edited') else 'Info'
        )

        return review
