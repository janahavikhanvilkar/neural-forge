import json
from pathlib import Path
from models.models import db, Resume, JobDescription, HITLReview
from services.ai_service import ai_service
from utils.file_parser import extract_text_from_file, clean_extracted_text
from utils.helpers import log_activity, create_notification

class ResumeService:
    @staticmethod
    def screen_resume_file(file_path: str, original_filename: str, job_id: int = None) -> Resume:
        """Extracts candidate data from resume and performs AI screening against target Job Description."""
        raw_text = clean_extracted_text(extract_text_from_file(file_path))
        
        job = JobDescription.query.get(job_id) if job_id else None
        jd_text = job.description if job else "General Senior Software / Business Automation Specialist"
        target_skills = job.get_skills_list() if job else ["Python", "SQL", "Flask", "System Design", "Cloud", 'Html', 'Css', 'Js']

        # AI Resume Screening
        screened = ai_service.screen_resume(raw_text, jd_text, target_skills)

        candidate_name = screened.get('candidate_name', 'Candidate').strip()
        email = screened.get('email', '')
        phone = screened.get('phone', '')
        skills = screened.get('skills', [])
        experience = screened.get('experience', '')
        education = screened.get('education', '')
        certifications = screened.get('certifications', [])
        projects = screened.get('projects', '')
        
        match_score = int(screened.get('match_score', 65))
        skills_match_pct = int(screened.get('skills_match_pct', 60))
        experience_match_pct = int(screened.get('experience_match_pct', 60))
        matching_skills = screened.get('matching_skills', [])
        missing_skills = screened.get('missing_skills', [])
        recommendation = screened.get('recommendation', 'Review')
        ai_summary = screened.get('ai_summary', '')
        confidence = int(screened.get('confidence', 90))

        status = 'Shortlisted' if recommendation == 'Strong Match' else 'Screened'

        resume = Resume(
            job_id=job_id,
            candidate_name=candidate_name,
            email=email,
            phone=phone,
            skills=json.dumps(skills),
            experience=experience,
            education=education,
            certifications=json.dumps(certifications),
            file_path=file_path,
            file_name=original_filename,
            raw_text=raw_text[:5000],
            match_score=match_score,
            skills_match_pct=skills_match_pct,
            experience_match_pct=experience_match_pct,
            matching_skills=json.dumps(matching_skills),
            missing_skills=json.dumps(missing_skills),
            recommendation=recommendation,
            ai_summary=ai_summary,
            status=status,
            confidence=confidence
        )
        db.session.add(resume)
        db.session.commit()

        # Notification & Log
        job_title = job.title if job else "General Role"
        create_notification(
            title="Resume Screened",
            message=f"Candidate {candidate_name} scored {match_score}% match for '{job_title}' ({recommendation}).",
            module="Resumes",
            role_target="hr",
            link=f"/resumes"
        )
        log_activity(
            "Resume Screened", 
            "Resumes", 
            f"Screened {candidate_name} for '{job_title}': Match {match_score}%, Skills Match {skills_match_pct}% ({recommendation})", 
            "Success"
        )

        return resume

    @staticmethod
    def create_job_description(title: str, department: str, experience_req: str, skills_list: list, description: str) -> JobDescription:
        job = JobDescription(
            title=title,
            department=department,
            experience_required=experience_req,
            key_skills=json.dumps(skills_list),
            description=description,
            is_active=True
        )
        db.session.add(job)
        db.session.commit()
        log_activity("Job Created", "Resumes", f"Created new job opening: '{title}' in {department}", "Success")
        return job
