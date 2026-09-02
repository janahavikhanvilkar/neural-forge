import os
import json
from datetime import datetime, timedelta, timezone
from models.models import db, User, Invoice, Lead, JobDescription, Resume, SupportTicket, HITLReview, ActivityLog, Notification, SystemSetting
from config import Config

def seed_demo_database():
    """Populates the database with realistic hackathon demo data."""
    # Ensure tables exist
    db.create_all()

    # Clear existing data for fresh demo reload
    db.session.query(Notification).delete()
    db.session.query(ActivityLog).delete()
    db.session.query(HITLReview).delete()
    db.session.query(SupportTicket).delete()
    db.session.query(Resume).delete()
    db.session.query(JobDescription).delete()
    db.session.query(Lead).delete()
    db.session.query(Invoice).delete()
    db.session.query(User).delete()
    db.session.query(SystemSetting).delete()
    db.session.commit()

    # 1. System Settings
    db.session.add(SystemSetting(key='AUTO_PROCESS_THRESHOLD', value='80', description='Confidence threshold to auto-process without human review'))
    db.session.add(SystemSetting(key='HITL_REVIEW_THRESHOLD', value='60', description='Confidence threshold requiring mandatory HITL verification'))

    # 2. Users (Role-based demo accounts)
    users_data = [
        ('Alex Morgan', 'admin@smartbiz.ai', 'admin123', 'admin'),
        ('Sarah Jenkins', 'finance@smartbiz.ai', 'finance123', 'finance'),
        ('David Ross', 'sales@smartbiz.ai', 'sales123', 'sales'),
        ('Rachel Green', 'hr@smartbiz.ai', 'hr123', 'hr'),
        ('Michael Chang', 'support@smartbiz.ai', 'support123', 'support'),
    ]
    users_dict = {}
    for name, email, password, role in users_data:
        u = User(name=name, email=email, role=role)
        u.set_password(password)
        db.session.add(u)
        users_dict[role] = u
    db.session.commit()

    # 3. Invoices
    inv1 = Invoice(
        invoice_number='INV-2026-8801',
        vendor='CloudScale Systems Inc.',
        customer_name='SmartBiz Corp',
        invoice_date='2026-08-10',
        due_date='2026-09-10',
        subtotal=4500.00,
        tax=450.00,
        total=4950.00,
        currency='USD',
        payment_info='ACH Transfer Routing: 021000021 / Acc: 987654321',
        file_name='invoice_cloudscale_8801.pdf',
        file_type='pdf',
        raw_text="CloudScale Systems Inc.\nInvoice #: INV-2026-8801\nDate: 2026-08-10\nDue Date: 2026-09-10\nBill To: SmartBiz Corp\nCloud Infrastructure Tier 3 Hosting: $4,500.00\nSales Tax (10%): $450.00\nTotal Due: $4,950.00",
        extracted_data=json.dumps({
            'vendor': 'CloudScale Systems Inc.',
            'invoice_number': 'INV-2026-8801',
            'subtotal': 4500.0,
            'tax': 450.0,
            'total': 4950.0,
            'currency': 'USD',
            'line_items': [{'description': 'Cloud Hosting Infrastructure', 'quantity': 1, 'amount': 4500.0}]
        }),
        validation_flags=json.dumps(['All mathematical and vendor validations passed']),
        confidence=96,
        status='Processed',
        assigned_department='Finance',
        created_at=datetime.now(timezone.utc) - timedelta(days=2)
    )

    inv2 = Invoice(
        invoice_number='INV-2026-9412',
        vendor='Nexus Tech Solutions LLC',
        customer_name='SmartBiz Operations',
        invoice_date='2026-08-14',
        due_date='2026-09-14',
        subtotal=12800.00,
        tax=1280.00,
        total=14080.00,
        currency='USD',
        payment_info='Wire Transfer: Swift CODE NEXUSUS33',
        file_name='nexus_tech_consulting.pdf',
        file_type='pdf',
        raw_text="Nexus Tech Solutions LLC\nInvoice INV-2026-9412\nDate: 2026-08-14\nTotal: $14,080.00",
        extracted_data=json.dumps({
            'vendor': 'Nexus Tech Solutions LLC',
            'invoice_number': 'INV-2026-9412',
            'subtotal': 12800.0,
            'tax': 1280.0,
            'total': 14080.0,
            'currency': 'USD'
        }),
        validation_flags=json.dumps(['All validations passed']),
        confidence=94,
        status='Approved',
        assigned_department='Finance',
        created_at=datetime.now(timezone.utc) - timedelta(days=1)
    )

    # Low confidence invoice with math discrepancy (Routed to HITL)
    inv3 = Invoice(
        invoice_number='INV-2026-1049',
        vendor='Apex Global Logistics',
        customer_name='SmartBiz Warehouse',
        invoice_date='2026-08-18',
        due_date='2026-09-18',
        subtotal=3200.00,
        tax=500.00,
        total=3950.00,  # 3200 + 500 = 3700, but stated is 3950!
        currency='USD',
        payment_info='Check by Mail to PO Box 4022',
        file_name='apex_logistics_scanned.png',
        file_type='png',
        raw_text="Apex Global Logistics\nInvoice: INV-2026-1049\nSubtotal: $3,200.00\nTax: $500.00\nTotal Due: $3,950.00 (Math variance detected)",
        extracted_data=json.dumps({
            'vendor': 'Apex Global Logistics',
            'invoice_number': 'INV-2026-1049',
            'subtotal': 3200.0,
            'tax': 500.0,
            'total': 3950.0,
            'currency': 'USD'
        }),
        validation_flags=json.dumps([
            "Math Discrepancy: Subtotal ($3,200.00) + Tax ($500.00) = $3,700.00, but document states Total of $3,950.00 (Variance: $250.00)",
            "Low image scan resolution detected"
        ]),
        confidence=52,
        status='Needs Review',
        assigned_department='Finance',
        created_at=datetime.now(timezone.utc) - timedelta(hours=5)
    )

    # Another invoice: duplicate check warning
    inv4 = Invoice(
        invoice_number='INV-2026-8801',  # Duplicate of inv1!
        vendor='CloudScale Systems Inc.',
        customer_name='SmartBiz Corp',
        invoice_date='2026-08-20',
        due_date='2026-09-20',
        subtotal=4500.00,
        tax=450.00,
        total=4950.00,
        currency='USD',
        payment_info='ACH Transfer',
        file_name='duplicate_cloudscale.pdf',
        file_type='pdf',
        raw_text="CloudScale Systems Inc. Duplicate bill submission for INV-2026-8801",
        extracted_data=json.dumps({'vendor': 'CloudScale Systems Inc.', 'invoice_number': 'INV-2026-8801', 'total': 4950.0}),
        validation_flags=json.dumps(["Duplicate Alert: Invoice number 'INV-2026-8801' already exists in system"]),
        confidence=48,
        status='Needs Review',
        assigned_department='Finance',
        created_at=datetime.now(timezone.utc) - timedelta(hours=2)
    )

    db.session.add_all([inv1, inv2, inv3, inv4])
    db.session.commit()

    # 4. HITL Reviews for Invoices
    hitl_inv1 = HITLReview(
        task_type='invoice',
        task_id=inv3.id,
        task_title=f"Invoice #{inv3.invoice_number} ({inv3.vendor})",
        reason="Math Discrepancy: Subtotal ($3,200.00) + Tax ($500.00) != Total ($3,950.00). Variance of $250.00 found.",
        confidence=52,
        original_data=json.dumps({'file_name': 'apex_logistics_scanned.png', 'preview_text': inv3.raw_text}),
        extracted_data=inv3.extracted_data,
        recommended_action="Verify subtotal line items and adjust either Tax or Total before approving.",
        assigned_department='Finance',
        action='Pending',
        created_at=datetime.now(timezone.utc) - timedelta(hours=5)
    )

    hitl_inv2 = HITLReview(
        task_type='invoice',
        task_id=inv4.id,
        task_title=f"Invoice #{inv4.invoice_number} ({inv4.vendor})",
        reason="Duplicate Alert: Invoice number 'INV-2026-8801' was already processed on 2026-08-10.",
        confidence=48,
        original_data=json.dumps({'file_name': 'duplicate_cloudscale.pdf', 'preview_text': inv4.raw_text}),
        extracted_data=inv4.extracted_data,
        recommended_action="Confirm whether this is an accidental double submission and reject if duplicate.",
        assigned_department='Finance',
        action='Pending',
        created_at=datetime.now(timezone.utc) - timedelta(hours=2)
    )
    db.session.add_all([hitl_inv1, hitl_inv2])
    db.session.commit()

    # 5. Leads
    leads_data = [
        Lead(
            name='Elena Rostova',
            email='elena.rostova@quantumfin.io',
            company='Quantum Financial Tech',
            industry='FinTech',
            company_size='1000+',
            budget=85000.0,
            product='Enterprise Automation Suite',
            source='Inbound Demo Request',
            previous_interaction='Requested Executive Live Demo',
            engagement='High',
            score=94,
            category='HOT',
            reason=json.dumps([
                'Substantial enterprise budget ($85,000)',
                '1,000+ employee financial institution in high-growth sector',
                'Executive requested immediate live demonstration'
            ]),
            recommended_action='Assign to Senior Enterprise AE for direct executive demo within 24h',
            recommended_department='Sales',
            assigned_department='Sales',
            status='Qualified',
            confidence=95,
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        ),
        Lead(
            name='Marcus Vance',
            email='m.vance@vanguardlogistics.com',
            company='Vanguard Logistics Group',
            industry='Supply Chain / Logistics',
            company_size='201-1000',
            budget=45000.0,
            product='Document AI & Invoice Module',
            source='Webinar Attendee',
            previous_interaction='Attended AI in Logistics Webinar',
            engagement='High',
            score=86,
            category='HOT',
            reason=json.dumps([
                'Strong mid-market budget ($45,000)',
                'High operational alignment for invoice automation',
                'Actively participated in product Q&A during webinar'
            ]),
            recommended_action='Send custom logistics case study and schedule technical scoping call',
            recommended_department='Sales',
            assigned_department='Sales',
            status='Qualified',
            confidence=92,
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        ),
        Lead(
            name='Samantha Wright',
            email='swright@solardigital.co',
            company='Solar Digital Labs',
            industry='Renewable Energy',
            company_size='51-200',
            budget=15000.0,
            product='Lead & Ticket Automation',
            source='Organic Search',
            previous_interaction='Downloaded Whitepaper',
            engagement='Medium',
            score=68,
            category='WARM',
            reason=json.dumps([
                'Mid-sized company with verified corporate domain',
                'Moderate budget ($15,000)',
                'Downloaded technical whitepaper'
            ]),
            recommended_action='Enroll in automated nurture email series with product ROI calculator',
            recommended_department='Sales',
            assigned_department='Sales',
            status='In Review',
            confidence=88,
            created_at=datetime.now(timezone.utc) - timedelta(days=3)
        ),
        Lead(
            name='Brian O\'Connor',
            email='brian@fastfreight.xyz',
            company='FastFreight Direct',
            industry='Transportation',
            company_size='1-10',
            budget=1200.0,
            product='Starter Plan',
            source='Social Media Ad',
            previous_interaction='None',
            engagement='Low',
            score=42,
            category='COLD',
            reason=json.dumps([
                'Small company size (1-10 employees)',
                'Low initial budget ($1,200)',
                'No prior demo or product engagement'
            ]),
            recommended_action='Route to self-serve onboarding drip campaign',
            recommended_department='Marketing',
            assigned_department='Marketing',
            status='New',
            confidence=85,
            created_at=datetime.now(timezone.utc) - timedelta(days=4)
        )
    ]
    db.session.add_all(leads_data)
    db.session.commit()

    # 6. Job Descriptions & Resumes
    jd1 = JobDescription(
        title='Senior Full-Stack Automation Engineer',
        department='Engineering',
        experience_required='4-6 years',
        key_skills=json.dumps(['Python', 'Flask', 'SQL', 'Docker', 'REST APIs', 'System Design', 'JavaScript', 'Html', 'Css', 'Js']),
        description='We are seeking an experienced Full-Stack Engineer to scale our AI-driven business process automation backend. Required proficiency in Python, Flask/FastAPI, SQLAlchemy, asynchronous architectures, and modern web interfaces.',
        is_active=True
    )
    jd2 = JobDescription(
        title='Financial Systems Analyst',
        department='Finance',
        experience_required='3-5 years',
        key_skills=json.dumps(['Accounting', 'Financial Modeling', 'Excel', 'ERP Systems', 'Invoice Reconciliation', 'SQL']),
        description='Seeking a detail-oriented Financial Systems Analyst to oversee automated accounts payable workflows, financial audit controls, and ERP data pipelines.',
        is_active=True
    )
    db.session.add_all([jd1, jd2])
    db.session.commit()

    resumes_data = [
        Resume(
            job_id=jd1.id,
            candidate_name='Rahul Sharma',
            email='rahul.sharma.dev@gmail.com',
            phone='+1 (555) 349-8821',
            skills=json.dumps(['Python', 'Flask', 'SQL', 'Docker', 'REST APIs', 'System Design', 'JavaScript', 'AWS', 'Redis']),
            experience='5+ years leading backend microservices and Python web systems.',
            education='B.Tech in Computer Science, IIT Roorkee',
            certifications=json.dumps(['AWS Certified Solutions Architect']),
            match_score=94,
            skills_match_pct=100,
            experience_match_pct=90,
            matching_skills=json.dumps(['Python', 'Flask', 'SQL', 'Docker', 'REST APIs', 'System Design', 'JavaScript']),
            missing_skills=json.dumps([]),
            recommendation='Strong Match',
            ai_summary='Exceptional match across all technical requirements. 5 years direct experience with Python/Flask stacks and distributed architectures.',
            status='Shortlisted',
            confidence=95,
            file_name='rahul_sharma_resume.pdf',
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        ),
        Resume(
            job_id=jd1.id,
            candidate_name='Priya Patel',
            email='priya.patel.code@outlook.com',
            phone='+1 (555) 782-9014',
            skills=json.dumps(['Python', 'Django', 'SQL', 'JavaScript', 'React', 'HTML5', 'CSS3']),
            experience='3.5 years in full-stack web applications and UI interfaces.',
            education='B.S. in Software Engineering, University of Washington',
            certifications=json.dumps(['Certified Scrum Developer']),
            match_score=78,
            skills_match_pct=72,
            experience_match_pct=80,
            matching_skills=json.dumps(['Python', 'SQL', 'JavaScript']),
            missing_skills=json.dumps(['Flask', 'Docker', 'System Design']),
            recommendation='Review',
            ai_summary='Strong frontend and Django background. Would easily adapt to Flask, but Docker and distributed system design skills need verification during technical interview.',
            status='Screened',
            confidence=89,
            file_name='priya_patel_resume.docx',
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        ),
        Resume(
            job_id=jd1.id,
            candidate_name='Amit Kumar',
            email='amit.kumar99@yahoo.com',
            phone='+1 (555) 124-7751',
            skills=json.dumps(['HTML5', 'CSS3', 'WordPress', 'Basic PHP', 'SEO']),
            experience='2 years in digital agency web content and basic PHP scripting.',
            education='Diploma in Web Design',
            certifications=json.dumps([]),
            match_score=48,
            skills_match_pct=30,
            experience_match_pct=50,
            matching_skills=json.dumps(['JavaScript']),
            missing_skills=json.dumps(['Python', 'Flask', 'SQL', 'Docker', 'REST APIs', 'System Design']),
            recommendation='Low Match',
            ai_summary='Candidate profile is focused on CMS/WordPress content rather than scalable backend automation engineering.',
            status='Screened',
            confidence=92,
            file_name='amit_kumar_cv.pdf',
            created_at=datetime.now(timezone.utc) - timedelta(hours=8)
        )
    ]
    db.session.add_all(resumes_data)
    db.session.commit()

    # 7. Support Tickets & Generated AI Responses
    t1 = SupportTicket(
        ticket_number='TICK-0101',
        customer_name='Jonathan Blake',
        email='jblake@apexglobal.net',
        subject='Payment was deducted twice for August subscription',
        description='Hi SmartBiz Support, I checked my bank account statement this morning and noticed that our monthly enterprise charge of $499 was deducted twice on August 15th. Please refund the duplicate transaction immediately.',
        category='Billing',
        priority='High',
        sentiment='Negative',
        department='Finance',
        ai_response=(
            "Dear Jonathan,\n\n"
            "Thank you for contacting SmartBiz Support. We sincerely apologize for any frustration caused regarding the duplicate subscription charge on your account.\n\n"
            "We have escalated your ticket directly to our Finance & Billing Department for urgent verification. Our billing team will examine transaction logs, reverse the duplicate $499 charge, and ensure your statement is updated within 1-2 business days.\n\n"
            "You will receive a refund confirmation receipt once completed. If you have any additional bank statement reference IDs, please feel free to reply directly to this ticket.\n\n"
            "Best regards,\n"
            "SmartBiz Customer Care Team"
        ),
        ai_response_status='Generated',
        ai_reasoning="Classified as Billing due to duplicate charge complaint. Negative sentiment detected; routed to Finance for review.",
        status='Pending Review',
        confidence=94,
        created_at=datetime.now(timezone.utc) - timedelta(hours=6)
    )

    t2 = SupportTicket(
        ticket_number='TICK-0102',
        customer_name='Claire Sterling',
        email='c.sterling@acmecorp.com',
        subject='Webhook 500 error when receiving invoice payload',
        description='Our automated integration is receiving an intermittent HTTP 500 Internal Server Error when posting JSON webhooks to the /api/invoices endpoint. Logs attached.',
        category='Technical',
        priority='High',
        sentiment='Neutral',
        department='Support',
        ai_response=(
            "Dear Claire,\n\n"
            "Thank you for reaching out to SmartBiz Technical Support regarding the intermittent HTTP 500 webhook issue.\n\n"
            "Our engineering team has received your log details and is actively investigating the API endpoint gateway. We will deploy a patch and keep you updated on progress.\n\n"
            "Best regards,\n"
            "SmartBiz Technical Support Team"
        ),
        ai_response_status='Approved',
        ai_reasoning="Classified as Technical due to API webhook 500 failure. Routed to Technical Support.",
        status='In Progress',
        confidence=92,
        created_at=datetime.now(timezone.utc) - timedelta(hours=12)
    )

    t3 = SupportTicket(
        ticket_number='TICK-0103',
        customer_name='Liam Henderson',
        email='liam@hendersonpartners.com',
        subject='Inquiry about custom SSO SAML integration for 500 users',
        description='We are planning an enterprise deployment and would like to know if Okta SSO and custom SCIM user provisioning are supported out of the box.',
        category='Product',
        priority='Medium',
        sentiment='Positive',
        department='Sales',
        ai_response=(
            "Dear Liam,\n\n"
            "Thank you for your interest in SmartBiz Enterprise! Yes, our platform natively supports SAML 2.0 with Okta, Azure AD, and automated SCIM user provisioning.\n\n"
            "Our Enterprise Solutions Team will reach out shortly to provide technical documentation and schedule a walkthrough.\n\n"
            "Best regards,\n"
            "SmartBiz Enterprise Team"
        ),
        ai_response_status='Sent',
        ai_reasoning="Classified as Product/Sales inquiry with Positive sentiment.",
        status='Resolved',
        confidence=96,
        created_at=datetime.now(timezone.utc) - timedelta(days=1)
    )

    db.session.add_all([t1, t2, t3])
    db.session.commit()

    # HITL Review for Support Ticket #1
    hitl_tick = HITLReview(
        task_type='ticket',
        task_id=t1.id,
        task_title=f"Ticket #{t1.ticket_number}: {t1.subject}",
        reason="High sensitivity billing ticket with Negative sentiment. Requires human verification before response dispatch.",
        confidence=94,
        original_data=json.dumps({'customer': t1.customer_name, 'subject': t1.subject, 'description': t1.description}),
        extracted_data=json.dumps({
            'category': t1.category,
            'priority': t1.priority,
            'sentiment': t1.sentiment,
            'department': t1.department,
            'draft_response': t1.ai_response
        }),
        recommended_action="Review AI draft response and approve refund authorization.",
        assigned_department='Finance',
        action='Pending',
        created_at=datetime.now(timezone.utc) - timedelta(hours=6)
    )
    db.session.add(hitl_tick)
    db.session.commit()

    # 8. Notifications
    notifications_data = [
        Notification(
            title="⚠️ Invoice Math Discrepancy Flagged",
            message="Invoice INV-2026-1049 from Apex Global Logistics routed to HITL queue due to math variance ($250 variance).",
            module="Invoices",
            role_target="finance",
            link="/hitl"
        ),
        Notification(
            title="🔥 High-Value HOT Lead Detected",
            message="Elena Rostova (Quantum Financial Tech, $85k budget) scored 94/100 HOT! Assigned to Sales.",
            module="Leads",
            role_target="sales",
            link="/leads"
        ),
        Notification(
            title="✨ Strong Candidate Match",
            message="Candidate Rahul Sharma scored 94% match for Senior Full-Stack Automation Engineer.",
            module="Resumes",
            role_target="hr",
            link="/resumes"
        ),
        Notification(
            title="🚨 High Priority Support Ticket",
            message="Ticket TICK-0101 (Duplicate payment deducted) flagged with Negative sentiment for Finance review.",
            module="Support",
            role_target="finance",
            link="/hitl"
        )
    ]
    db.session.add_all(notifications_data)

    # 9. Activity Logs
    logs_data = [
        ActivityLog(user_name='System', role='system', action='AI Extraction', module='Invoices', description='Extracted and validated INV-2026-8801 with 96% confidence', status='Success'),
        ActivityLog(user_name='David Ross', role='sales', action='Lead Scored', module='Leads', description='Lead Elena Rostova scored HOT (94/100) -> Routed to Sales', status='Success'),
        ActivityLog(user_name='Rachel Green', role='hr', action='Resume Screened', module='Resumes', description='Screened candidate Rahul Sharma against Senior Engineer JD (94% Match)', status='Success'),
        ActivityLog(user_name='System', role='system', action='HITL Flagged', module='Invoices', description='Flagged INV-2026-1049 (Apex Global) to HITL review queue due to calculation variance', status='Warning'),
        ActivityLog(user_name='Michael Chang', role='support', action='Response Approved', module='Support', description='Approved & dispatched AI resolution response for Ticket TICK-0103', status='Success'),
    ]
    db.session.add_all(logs_data)
    db.session.commit()

    # 10. Generate sample files in uploads/samples directory for easy user testing!
    _generate_sample_files()
    print("Demo database successfully seeded!")

def _generate_sample_files():
    """Generates sample test invoice and resume files in uploads/samples/."""
    samples_dir = Config.SAMPLES_FOLDER
    samples_dir.mkdir(parents=True, exist_ok=True)

    # 1. Sample Clean Invoice (TXT / PDF)
    clean_inv_text = """ACME ENTERPRISE SOLUTIONS INC.
100 Innovation Way, Suite 400, San Francisco, CA 94107
Tax ID: 94-3829102

INVOICE
Invoice Number: INV-2026-7732
Invoice Date: August 25, 2026
Payment Due: September 25, 2026
Billed To: SmartBiz Automation Group

Description                                  Qty    Unit Price     Amount
-------------------------------------------------------------------------
AI Document Processing Platform License        1    $3,000.00   $3,000.00
Cloud Integration Setup & Security Audit       1    $1,500.00   $1,500.00
Dedicated Support SLA (Monthly)                1      $500.00     $500.00

Subtotal: $5,000.00
Tax / GST (10%): $500.00
Total Amount Due: $5,500.00 USD

Payment Instructions:
Bank: Silicon Valley Commercial Bank
Account: 8847291039 | Routing: 121000358
Terms: Net 30 Days
"""
    with open(samples_dir / "sample_clean_invoice.txt", "w", encoding="utf-8") as f:
        f.write(clean_inv_text)

    # 2. Sample Discrepancy Invoice (Triggers HITL)
    discrepancy_inv_text = """SUMMIT LOGISTICS & FREIGHT CORP
Invoice #: INV-2026-9041
Date: August 28, 2026
Due Date: September 28, 2026
Bill To: SmartBiz Global

Line Items:
- Cross-docking and shipping services: $4,200.00
- Warehouse handling fee: $800.00

Subtotal: $5,000.00
Sales Tax (8%): $400.00
Total Amount Due: $5,850.00  (Notice: Math calculation error, 5000 + 400 != 5850)

Payment via Wire Transfer or Corporate Check.
"""
    with open(samples_dir / "sample_math_error_invoice.txt", "w", encoding="utf-8") as f:
        f.write(discrepancy_inv_text)

    # 3. Sample Resume
    sample_resume_text = """ALEXANDER CHEN
alex.chen.engineer@gmail.com | (555) 892-3341 | San Francisco, CA
LinkedIn: linkedin.com/in/alexchen-dev | GitHub: github.com/alexchen-dev

SUMMARY
Experienced Senior Software Engineer with 6+ years specializing in Python backend systems, microservices, REST APIs, and automated business workflows. Passionate about clean system architecture and scalable cloud infrastructure.

TECHNICAL SKILLS
- Languages: Python, JavaScript, TypeScript, SQL, Bash
- Frameworks & Libraries: Flask, FastAPI, Django, SQLAlchemy, React, Node.js
- Cloud & DevOps: Docker, Kubernetes, AWS (ECS, S3, RDS, Lambda), CI/CD (GitHub Actions)
- Databases: PostgreSQL, MySQL, Redis, SQLite
- Methodologies: Agile, Scrum, TDD, Microservices Design

PROFESSIONAL EXPERIENCE
Senior Backend Engineer | CloudFlow Technologies (2022 - Present)
- Architected and built high-throughput REST APIs handling 5M+ daily requests using Python, Flask, and PostgreSQL.
- Containerized legacy services with Docker and Kubernetes, reducing deployment cycle times by 45%.
- Implemented real-time asynchronous job pipelines with Celery and Redis.

Software Engineer | Apex Data Systems (2019 - 2022)
- Developed automated data extraction scripts and ETL pipelines using Python and SQL.
- Designed database schemas and optimized complex queries for high-volume financial transactions.
- Collaborated with frontend engineers to deliver intuitive SaaS dashboard interfaces.

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley (2015 - 2019)

CERTIFICATIONS
- AWS Certified Solutions Architect - Associate
- Professional Scrum Developer
"""
    with open(samples_dir / "sample_senior_engineer_resume.txt", "w", encoding="utf-8") as f:
        f.write(sample_resume_text)
