import json
from datetime import datetime
from models.models import db, SupportTicket, HITLReview
from services.ai_service import ai_service
from utils.helpers import log_activity, create_notification, get_system_thresholds

class SupportService:
    @staticmethod
    def create_and_classify_ticket(data: dict) -> SupportTicket:
        """Processes customer support ticket, executes AI NLP classification, routes, and drafts response."""
        customer_name = data.get('customer_name', '').strip()
        email = data.get('email', '').strip()
        subject = data.get('subject', '').strip()
        description = data.get('description', '').strip()

        # Generate ticket identifier
        count = SupportTicket.query.count() + 101
        ticket_number = f"TICK-{count:04d}"

        # AI Classification
        classification = ai_service.classify_ticket(subject, description)

        category = classification.get('category', 'General')
        priority = classification.get('priority', 'Medium')
        sentiment = classification.get('sentiment', 'Neutral')
        department = classification.get('department', 'Support')
        confidence = int(classification.get('confidence', 88))
        reasoning = classification.get('reasoning', '')

        # Generate Draft AI Response
        ai_draft_response = ai_service.generate_support_response(
            customer_name=customer_name,
            subject=subject,
            description=description,
            category=category,
            sentiment=sentiment
        )

        auto_thresh, review_thresh = get_system_thresholds()

        # Flag for HITL if critical priority, negative sentiment on billing, or low confidence
        needs_hitl = False
        hitl_reason = ""

        if priority == 'Critical' or sentiment == 'Negative' or confidence < auto_thresh:
            needs_hitl = True
            hitl_reason = f"High sensitivity ticket ({priority} Priority, {sentiment} Sentiment, {category} Category)"

        status = 'Pending Review' if needs_hitl else 'Open'

        ticket = SupportTicket(
            ticket_number=ticket_number,
            customer_name=customer_name,
            email=email,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            sentiment=sentiment,
            department=department,
            ai_response=ai_draft_response,
            ai_response_status='Generated',
            ai_reasoning=reasoning,
            status=status,
            confidence=confidence
        )
        db.session.add(ticket)
        db.session.commit()

        if needs_hitl:
            hitl_task = HITLReview(
                task_type='ticket',
                task_id=ticket.id,
                task_title=f"Ticket {ticket.ticket_number}: {ticket.subject}",
                reason=hitl_reason,
                confidence=confidence,
                original_data=json.dumps({'customer': customer_name, 'subject': subject, 'description': description}),
                extracted_data=json.dumps({
                    'category': category,
                    'priority': priority,
                    'sentiment': sentiment,
                    'department': department,
                    'draft_response': ai_draft_response
                }),
                recommended_action="Review AI classification & draft response before dispatching to customer.",
                assigned_department=department,
                action='Pending'
            )
            db.session.add(hitl_task)
            db.session.commit()

            create_notification(
                title=f"Support Ticket {ticket.ticket_number} Needs Review",
                message=f"[{priority}] {category} issue from {customer_name}: \"{subject}\". Routed to {department} for HITL review.",
                module="Support",
                role_target=department.lower(),
                link=f"/hitl"
            )
            log_activity("Ticket Flagged for HITL", "Support", f"Ticket {ticket.ticket_number} flagged ({priority}, {sentiment}) -> {department}", "Warning")
        else:
            create_notification(
                title=f"Support Ticket {ticket.ticket_number} Created",
                message=f"[{priority}] {category} ticket from {customer_name} routed to {department}.",
                module="Support",
                role_target=department.lower(),
                link=f"/support"
            )
            log_activity("Ticket Classified", "Support", f"Ticket {ticket.ticket_number} classified as {category} ({priority} Priority) -> {department}", "Success")

        return ticket

    @staticmethod
    def regenerate_response(ticket_id: int) -> str:
        ticket = SupportTicket.query.get_or_404(ticket_id)
        new_response = ai_service.generate_support_response(
            customer_name=ticket.customer_name,
            subject=ticket.subject,
            description=ticket.description,
            category=ticket.category,
            sentiment=ticket.sentiment
        )
        ticket.ai_response = new_response
        ticket.ai_response_status = 'Generated'
        db.session.commit()
        log_activity("Response Regenerated", "Support", f"Regenerated AI draft response for Ticket {ticket.ticket_number}", "Info")
        return new_response

    @staticmethod
    def approve_and_send_response(ticket_id: int, response_text: str, user_name: str = "Support Agent") -> SupportTicket:
        ticket = SupportTicket.query.get_or_404(ticket_id)
        ticket.ai_response = response_text
        ticket.ai_response_status = 'Sent'
        ticket.status = 'Resolved'
        
        # Check if there was an associated HITL review and mark complete
        hitl_task = HITLReview.query.filter_by(task_type='ticket', task_id=ticket.id, action='Pending').first()
        if hitl_task:
            hitl_task.action = 'Approved'
            hitl_task.reviewer_name = user_name
            hitl_task.comment = "Response approved and transmitted to customer."
            hitl_task.completed_at = datetime.utcnow()

        db.session.commit()

        create_notification(
            title=f"Ticket {ticket.ticket_number} Resolved",
            message=f"Verified AI response sent to {ticket.customer_name} ({ticket.email}).",
            module="Support",
            role_target="support",
            link=f"/support"
        )
        log_activity("Response Sent", "Support", f"Approved & sent support response for Ticket {ticket.ticket_number} by {user_name}", "Success")
        return ticket
