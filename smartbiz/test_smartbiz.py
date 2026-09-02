import unittest
import json
from app import create_app
from models.models import db, User, Invoice, Lead, Resume, SupportTicket, HITLReview, JobDescription
from services.ai_service import ai_service
from services.invoice_service import InvoiceService
from services.lead_service import LeadService
from services.resume_service import ResumeService
from services.support_service import SupportService
from services.hitl_service import HITLService
from config import Config

class SmartBizIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from database.seed_data import seed_demo_database
        seed_demo_database()

    def tearDown(self):
        self.ctx.pop()

    def test_01_user_authentication(self):
        # Test demo users exist
        admin = User.query.filter_by(email='admin@smartbiz.ai').first()
        self.assertIsNotNone(admin)
        self.assertTrue(admin.check_password('admin123'))

        finance = User.query.filter_by(email='finance@smartbiz.ai').first()
        self.assertIsNotNone(finance)
        self.assertTrue(finance.check_password('finance123'))

        # Test login request
        resp = self.client.post('/login', data={
            'email': 'admin@smartbiz.ai',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_02_dashboard_and_charts(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'admin'
            sess['user_name'] = 'Alex Morgan'

        resp = self.client.get('/dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Automation Dashboard', resp.data)

        # Test chart API
        chart_resp = self.client.get('/api/dashboard/charts')
        self.assertEqual(chart_resp.status_code, 200)
        chart_json = chart_resp.get_json()
        self.assertIn('categories', chart_json)
        self.assertIn('confidence_dist', chart_json)
        self.assertIn('human_vs_auto', chart_json)

    def test_03_invoice_processing(self):
        sample_file = Config.SAMPLES_FOLDER / "sample_clean_invoice.txt"
        self.assertTrue(sample_file.exists())

        # Process clean invoice
        inv = InvoiceService.process_invoice_file(str(sample_file), "sample_clean_invoice.txt")
        self.assertIsNotNone(inv)
        self.assertGreaterEqual(inv.confidence, 80)
        self.assertEqual(inv.status, 'Processed')
        self.assertEqual(inv.assigned_department, 'Finance')

        # Process math discrepancy invoice
        err_file = Config.SAMPLES_FOLDER / "sample_math_error_invoice.txt"
        inv_err = InvoiceService.process_invoice_file(str(err_file), "sample_math_error_invoice.txt")
        self.assertIsNotNone(inv_err)
        self.assertEqual(inv_err.status, 'Needs Review')

        # Verify HITL task created
        hitl = HITLReview.query.filter_by(task_type='invoice', task_id=inv_err.id).first()
        self.assertIsNotNone(hitl)
        self.assertEqual(hitl.action, 'Pending')

    def test_04_lead_scoring(self):
        hot_lead_data = {
            'name': 'Sophia Loren',
            'email': 'sophia@enterprisecorp.com',
            'company': 'Enterprise Global Inc.',
            'industry': 'Financial Technology',
            'company_size': '1000+',
            'budget': 65000,
            'product': 'Automation Platform',
            'source': 'Inbound Demo Request',
            'previous_interaction': 'Requested Live Demo',
            'engagement': 'High'
        }
        lead = LeadService.create_and_score_lead(hot_lead_data)
        self.assertIsNotNone(lead)
        self.assertGreaterEqual(lead.score, 80)
        self.assertEqual(lead.category, 'HOT')
        self.assertEqual(lead.assigned_department, 'Sales')

    def test_05_resume_screening(self):
        sample_resume = Config.SAMPLES_FOLDER / "sample_senior_engineer_resume.txt"
        self.assertTrue(sample_resume.exists())

        jd = JobDescription.query.first()
        self.assertIsNotNone(jd)

        resume = ResumeService.screen_resume_file(str(sample_resume), "sample_senior_engineer_resume.txt", jd.id)
        self.assertIsNotNone(resume)
        self.assertGreaterEqual(resume.match_score, 75)
        self.assertIn(resume.recommendation, ['Strong Match', 'Review'])

    def test_06_support_ticket_classification_and_response(self):
        ticket_data = {
            'customer_name': 'Robert Taylor',
            'email': 'rtaylor@clientcorp.com',
            'subject': 'Charged twice for monthly invoice',
            'description': 'Our account was billed $1,200 twice on the 1st of this month. Please issue a refund.'
        }
        ticket = SupportService.create_and_classify_ticket(ticket_data)
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.category, 'Billing')
        self.assertEqual(ticket.department, 'Finance')
        self.assertIsNotNone(ticket.ai_response)

        # Test approving and sending response
        updated_ticket = SupportService.approve_and_send_response(ticket.id, ticket.ai_response, 'Support Agent')
        self.assertEqual(updated_ticket.status, 'Resolved')
        self.assertEqual(updated_ticket.ai_response_status, 'Sent')

    def test_07_hitl_resolution(self):
        # Find a pending review
        pending_review = HITLReview.query.filter_by(action='Pending').first()
        self.assertIsNotNone(pending_review)

        # Resolve review
        resolved = HITLService.resolve_review(
            review_id=pending_review.id,
            action='Approved',
            reviewer_name='Test Reviewer',
            comment='Verified and approved during automated tests'
        )
        self.assertEqual(resolved.action, 'Approved')

    def test_08_all_navigation_pages(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'admin'
            sess['user_name'] = 'Alex Morgan'

        endpoints = [
            '/invoices',
            '/leads',
            '/resumes',
            '/support',
            '/hitl',
            '/workflows',
            '/analytics',
            '/settings'
        ]
        for ep in endpoints:
            resp = self.client.get(ep)
            self.assertEqual(resp.status_code, 200, f"Failed accessing endpoint {ep}")

if __name__ == '__main__':
    unittest.main()
