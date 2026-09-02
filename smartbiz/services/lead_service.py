import json
from models.models import db, Lead, HITLReview
from services.ai_service import ai_service
from utils.helpers import log_activity, create_notification, get_system_thresholds

class LeadService:
    @staticmethod
    def create_and_score_lead(data: dict) -> Lead:
        """Processes a new lead, runs AI scoring, categorizes (HOT/WARM/COLD), and routes."""
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        company = data.get('company', '').strip()
        industry = data.get('industry', '').strip()
        company_size = data.get('company_size', '11-50')
        budget = float(data.get('budget', 0) or 0)
        product = data.get('product', '').strip()
        source = data.get('source', 'Website')
        previous_interaction = data.get('previous_interaction', 'None')
        engagement = data.get('engagement', 'Medium')

        lead_data_payload = {
            'name': name,
            'email': email,
            'company': company,
            'industry': industry,
            'company_size': company_size,
            'budget': budget,
            'product': product,
            'source': source,
            'previous_interaction': previous_interaction,
            'engagement': engagement
        }

        # Run AI Lead Scoring
        scored = ai_service.score_lead(lead_data_payload)

        score = int(scored.get('score', 50))
        category = scored.get('category', 'WARM')
        reasons = scored.get('reasons', [])
        recommended_action = scored.get('recommended_action', 'Follow up via email')
        recommended_dept = scored.get('recommended_department', 'Sales')
        confidence = int(scored.get('confidence', 90))

        # Determine routing & status
        assigned_dept = recommended_dept
        status = 'Qualified' if category == 'HOT' else ('In Review' if category == 'WARM' else 'New')

        lead = Lead(
            name=name,
            email=email,
            company=company,
            industry=industry,
            company_size=company_size,
            budget=budget,
            product=product,
            source=source,
            previous_interaction=previous_interaction,
            engagement=engagement,
            score=score,
            category=category,
            reason=json.dumps(reasons) if isinstance(reasons, list) else str(reasons),
            recommended_action=recommended_action,
            recommended_department=recommended_dept,
            assigned_department=assigned_dept,
            status=status,
            confidence=confidence
        )
        db.session.add(lead)
        db.session.commit()

        # Handle routing and notifications
        if category == 'HOT':
            create_notification(
                title="🔥 High-Value HOT Lead Detected",
                message=f"New HOT lead: {lead.name} from {lead.company} (Score: {score}/100, Budget: ${budget:,.0f}). Assigned to Sales.",
                module="Leads",
                role_target="sales",
                link=f"/leads"
            )
            log_activity("HOT Lead Scored", "Leads", f"Lead #{lead.id} ({lead.name} @ {lead.company}) scored HOT ({score}/100) -> Routed to Sales", "Success")
        else:
            create_notification(
                title=f"New {category} Lead Scored",
                message=f"Lead {lead.name} scored {score}/100 ({category}). Action: {recommended_action}",
                module="Leads",
                role_target="sales",
                link=f"/leads"
            )
            log_activity("Lead Scored", "Leads", f"Lead #{lead.id} ({lead.name}) scored {category} ({score}/100)", "Info")

        return lead
