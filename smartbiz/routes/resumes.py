import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from models.models import db, Resume, JobDescription
from services.resume_service import ResumeService
from utils.helpers import login_required, log_activity
from config import Config

resumes_bp = Blueprint('resumes', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@resumes_bp.route('/resumes')
@login_required
def index():
    job_id = request.args.get('job_id')
    rec_filter = request.args.get('rec', 'all')
    search_query = request.args.get('q', '').strip()

    jobs = JobDescription.query.order_by(JobDescription.created_at.desc()).all()
    
    # Active selected job
    selected_job = None
    if job_id:
        selected_job = JobDescription.query.get(job_id)
    if not selected_job and jobs:
        selected_job = jobs[0]

    query = Resume.query
    if selected_job:
        query = query.filter_by(job_id=selected_job.id)
    if rec_filter != 'all':
        query = query.filter_by(recommendation=rec_filter)
    if search_query:
        query = query.filter(
            (Resume.candidate_name.ilike(f'%{search_query}%')) |
            (Resume.email.ilike(f'%{search_query}%')) |
            (Resume.skills.ilike(f'%{search_query}%'))
        )

    resumes = query.order_by(Resume.match_score.desc()).all()

    # Counters
    strong_matches = sum(1 for r in resumes if r.recommendation == 'Strong Match')
    review_matches = sum(1 for r in resumes if r.recommendation == 'Review')
    low_matches = sum(1 for r in resumes if r.recommendation == 'Low Match')

    return render_template(
        'resumes.html',
        resumes=resumes,
        jobs=jobs,
        selected_job=selected_job,
        rec_filter=rec_filter,
        search_query=search_query,
        strong_matches=strong_matches,
        review_matches=review_matches,
        low_matches=low_matches
    )

@resumes_bp.route('/resumes/upload', methods=['POST'])
@login_required
def upload_resumes():
    job_id = request.form.get('job_id')
    uploaded_files = request.files.getlist('files')

    if not uploaded_files or uploaded_files[0].filename == '':
        flash("Please select at least one resume file to upload.", "warning")
        return redirect(url_for('resumes.index', job_id=job_id))

    success_count = 0
    for file in uploaded_files:
        if file and allowed_file(file.filename):
            original_name = secure_filename(file.filename)
            unique_name = f"resume_{uuid.uuid4().hex[:8]}_{original_name}"
            save_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)
            file.save(save_path)

            try:
                ResumeService.screen_resume_file(save_path, original_name, job_id=int(job_id) if job_id else None)
                success_count += 1
            except Exception as e:
                flash(f"Error screening {original_name}: {str(e)}", "danger")

    if success_count > 0:
        flash(f"✅ Successfully screened and ranked {success_count} candidate resume(s)!", "success")

    return redirect(url_for('resumes.index', job_id=job_id))

@resumes_bp.route('/resumes/jobs/create', methods=['POST'])
@login_required
def create_job():
    title = request.form.get('title')
    department = request.form.get('department', 'Engineering')
    experience_req = request.form.get('experience_required', '3-5 years')
    skills_raw = request.form.get('key_skills', '')
    description = request.form.get('description', '')

    skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]

    job = ResumeService.create_job_description(title, department, experience_req, skills_list, description)
    flash(f"Job opening '{title}' created successfully!", "success")
    return redirect(url_for('resumes.index', job_id=job.id))

@resumes_bp.route('/resumes/<int:resume_id>/decision', methods=['POST'])
@login_required
def candidate_decision(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    decision = request.form.get('decision')  # Shortlisted, Rejected, Interviewing, Hired
    if decision:
        resume.status = decision
        db.session.commit()
        log_activity("HR Decision", "Resumes", f"Candidate {resume.candidate_name} marked as '{decision}' by {session.get('user_name', 'HR')}", "Success")
        flash(f"Candidate {resume.candidate_name} updated to '{decision}'.", "success")
    return redirect(url_for('resumes.index', job_id=resume.job_id))
