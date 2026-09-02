from datetime import datetime, timezone
import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='admin')  # admin, finance, sales, hr, support
    avatar = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(100), nullable=True, index=True)
    vendor = db.Column(db.String(200), nullable=True)
    customer_name = db.Column(db.String(200), nullable=True)
    invoice_date = db.Column(db.String(50), nullable=True)
    due_date = db.Column(db.String(50), nullable=True)
    
    subtotal = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(20), default='USD')
    payment_info = db.Column(db.String(255), nullable=True)
    
    file_path = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_type = db.Column(db.String(50), nullable=True)
    raw_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.Text, nullable=True)  # JSON string
    validation_flags = db.Column(db.Text, nullable=True)  # JSON string of errors/warnings
    
    confidence = db.Column(db.Integer, default=0)  # 0 - 100
    status = db.Column(db.String(50), default='Uploaded')  # Uploaded, Processing, Processed, Needs Review, Approved, Rejected
    assigned_department = db.Column(db.String(50), default='Finance')
    
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=datetime.utcnow)

    def get_extracted_json(self):
        if self.extracted_data:
            try:
                return json.loads(self.extracted_data)
            except Exception:
                return {}
        return {}

    def get_validation_json(self):
        if self.validation_flags:
            try:
                return json.loads(self.validation_flags)
            except Exception:
                return []
        return []

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number or 'N/A',
            'vendor': self.vendor or 'Unknown Vendor',
            'customer_name': self.customer_name or 'N/A',
            'invoice_date': self.invoice_date or 'N/A',
            'due_date': self.due_date or 'N/A',
            'subtotal': self.subtotal,
            'tax': self.tax,
            'total': self.total,
            'currency': self.currency or 'USD',
            'payment_info': self.payment_info or '',
            'file_name': self.file_name or '',
            'confidence': self.confidence,
            'status': self.status,
            'assigned_department': self.assigned_department,
            'validation_flags': self.get_validation_json(),
            'extracted_data': self.get_extracted_json(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(200), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    company_size = db.Column(db.String(50), nullable=True)  # 1-10, 11-50, 51-200, 201-1000, 1000+
    budget = db.Column(db.Float, default=0.0)
    product = db.Column(db.String(150), nullable=True)
    source = db.Column(db.String(100), nullable=True)  # Website, Referral, Inbound, LinkedIn, Event
    previous_interaction = db.Column(db.String(100), nullable=True)  # Demo Requested, Whitepaper Download, Webinar, None
    engagement = db.Column(db.String(50), nullable=True)  # High, Medium, Low
    
    score = db.Column(db.Integer, default=0)  # 0 - 100
    category = db.Column(db.String(50), default='COLD')  # HOT, WARM, COLD
    reason = db.Column(db.Text, nullable=True)  # JSON or bullet points
    recommended_action = db.Column(db.String(255), nullable=True)
    recommended_department = db.Column(db.String(50), default='Sales')
    assigned_department = db.Column(db.String(50), default='Sales')
    
    status = db.Column(db.String(50), default='New')  # New, Contacted, Qualified, In Review, Converted, Disqualified
    confidence = db.Column(db.Integer, default=85)
    
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=datetime.utcnow)

    def get_reasons_list(self):
        if not self.reason:
            return []
        try:
            parsed = json.loads(self.reason)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return [r.strip() for r in self.reason.split('\n') if r.strip()]

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'company': self.company or 'N/A',
            'industry': self.industry or 'N/A',
            'company_size': self.company_size or 'N/A',
            'budget': self.budget,
            'product': self.product or 'N/A',
            'source': self.source or 'Direct',
            'previous_interaction': self.previous_interaction or 'None',
            'engagement': self.engagement or 'Medium',
            'score': self.score,
            'category': self.category,
            'reasons': self.get_reasons_list(),
            'recommended_action': self.recommended_action or 'Follow up via email',
            'assigned_department': self.assigned_department,
            'status': self.status,
            'confidence': self.confidence,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class JobDescription(db.Model):
    __tablename__ = 'job_descriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), default='Engineering')
    experience_required = db.Column(db.String(100), default='3-5 years')
    key_skills = db.Column(db.Text, nullable=True)  # JSON list
    description = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def get_skills_list(self):
        if self.key_skills:
            try:
                return json.loads(self.key_skills)
            except Exception:
                return [s.strip() for s in self.key_skills.split(',') if s.strip()]
        return []

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'department': self.department,
            'experience_required': self.experience_required,
            'key_skills': self.get_skills_list(),
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_descriptions.id'), nullable=True)
    job = db.relationship('JobDescription', backref=db.backref('resumes', lazy=True))
    
    candidate_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    
    skills = db.Column(db.Text, nullable=True)  # JSON list
    experience = db.Column(db.Text, nullable=True)  # Summary / years
    education = db.Column(db.Text, nullable=True)
    certifications = db.Column(db.Text, nullable=True)  # JSON list
    projects = db.Column(db.Text, nullable=True)
    
    file_path = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    raw_text = db.Column(db.Text, nullable=True)
    
    # AI Comparison Results
    match_score = db.Column(db.Integer, default=0)  # 0 - 100
    skills_match_pct = db.Column(db.Integer, default=0)
    experience_match_pct = db.Column(db.Integer, default=0)
    matching_skills = db.Column(db.Text, nullable=True)  # JSON list
    missing_skills = db.Column(db.Text, nullable=True)   # JSON list
    recommendation = db.Column(db.String(50), default='Review')  # Strong Match, Review, Low Match
    ai_summary = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(50), default='Screened')  # Screened, Shortlisted, Interviewing, Rejected, Hired
    confidence = db.Column(db.Integer, default=90)
    
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=datetime.utcnow)

    def get_skills_list(self):
        if self.skills:
            try:
                return json.loads(self.skills)
            except Exception:
                return [s.strip() for s in self.skills.split(',') if s.strip()]
        return []

    def get_matching_skills(self):
        if self.matching_skills:
            try:
                return json.loads(self.matching_skills)
            except Exception:
                return [s.strip() for s in self.matching_skills.split(',') if s.strip()]
        return []

    def get_missing_skills(self):
        if self.missing_skills:
            try:
                return json.loads(self.missing_skills)
            except Exception:
                return [s.strip() for s in self.missing_skills.split(',') if s.strip()]
        return []

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_title': self.job.title if self.job else 'General Application',
            'candidate_name': self.candidate_name,
            'email': self.email or 'N/A',
            'phone': self.phone or 'N/A',
            'skills': self.get_skills_list(),
            'experience': self.experience or 'Not specified',
            'education': self.education or 'Not specified',
            'match_score': self.match_score,
            'skills_match_pct': self.skills_match_pct,
            'experience_match_pct': self.experience_match_pct,
            'matching_skills': self.get_matching_skills(),
            'missing_skills': self.get_missing_skills(),
            'recommendation': self.recommendation,
            'ai_summary': self.ai_summary or '',
            'status': self.status,
            'file_name': self.file_name or '',
            'confidence': self.confidence,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # AI Classification
    category = db.Column(db.String(50), default='General')  # Billing, Technical, Account, Product, General, Other
    priority = db.Column(db.String(50), default='Medium')   # Low, Medium, High, Critical
    sentiment = db.Column(db.String(50), default='Neutral') # Positive, Neutral, Negative
    department = db.Column(db.String(50), default='Support')# Finance, Support, Sales, HR, Admin
    
    # AI Response
    ai_response = db.Column(db.Text, nullable=True)
    ai_response_status = db.Column(db.String(50), default='Generated')  # Generated, Edited, Approved, Sent, Rejected
    ai_reasoning = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(50), default='Open')  # Open, In Progress, Pending Review, Resolved, Closed
    confidence = db.Column(db.Integer, default=85)
    
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'customer_name': self.customer_name,
            'email': self.email,
            'subject': self.subject,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'sentiment': self.sentiment,
            'department': self.department,
            'ai_response': self.ai_response or '',
            'ai_response_status': self.ai_response_status,
            'status': self.status,
            'confidence': self.confidence,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class HITLReview(db.Model):
    __tablename__ = 'hitl_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    task_type = db.Column(db.String(50), nullable=False)  # invoice, lead, resume, ticket
    task_id = db.Column(db.Integer, nullable=False)
    task_title = db.Column(db.String(255), nullable=True)
    
    reason = db.Column(db.Text, nullable=False)  # Reason why it triggered HITL
    confidence = db.Column(db.Integer, default=50)
    original_data = db.Column(db.Text, nullable=True)  # JSON
    extracted_data = db.Column(db.Text, nullable=True) # JSON
    recommended_action = db.Column(db.String(255), nullable=True)
    
    # Review outcome
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewer = db.relationship('User', backref=db.backref('hitl_reviews', lazy=True))
    reviewer_name = db.Column(db.String(120), nullable=True)
    
    action = db.Column(db.String(50), default='Pending')  # Pending, Approved, Rejected, Edited, Reassigned
    comment = db.Column(db.Text, nullable=True)
    changes_made = db.Column(db.Text, nullable=True)  # JSON diff
    assigned_department = db.Column(db.String(50), default='Admin')
    
    created_at = db.Column(db.DateTime, default=utc_now)
    completed_at = db.Column(db.DateTime, nullable=True)

    def get_original_json(self):
        if self.original_data:
            try:
                return json.loads(self.original_data)
            except Exception:
                return {}
        return {}

    def get_extracted_json(self):
        if self.extracted_data:
            try:
                return json.loads(self.extracted_data)
            except Exception:
                return {}
        return {}

    def to_dict(self):
        return {
            'id': self.id,
            'task_type': self.task_type,
            'task_id': self.task_id,
            'task_title': self.task_title or f"{self.task_type.capitalize()} #{self.task_id}",
            'reason': self.reason,
            'confidence': self.confidence,
            'original_data': self.get_original_json(),
            'extracted_data': self.get_extracted_json(),
            'recommended_action': self.recommended_action or 'Verify details and approve/reject',
            'reviewer_id': self.reviewer_id,
            'reviewer_name': self.reviewer_name or 'Unassigned',
            'action': self.action,
            'comment': self.comment or '',
            'assigned_department': self.assigned_department,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M') if self.completed_at else None
        }


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))
    user_name = db.Column(db.String(120), default='System')
    role = db.Column(db.String(50), default='system')
    
    action = db.Column(db.String(100), nullable=False)  # Login, Upload, AI Classification, HITL Approval, etc.
    module = db.Column(db.String(50), nullable=False)  # Auth, Invoices, Leads, Resumes, Tickets, HITL, System
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Success')  # Success, Warning, Info, Error
    ip_address = db.Column(db.String(50), default='127.0.0.1')
    
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user_name,
            'role': self.role,
            'action': self.action,
            'module': self.module,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    role_target = db.Column(db.String(50), default='all')  # all, admin, finance, sales, hr, support
    
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(50), default='System')
    link = db.Column(db.String(255), nullable=True)
    
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'module': self.module,
            'link': self.link or '#',
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
