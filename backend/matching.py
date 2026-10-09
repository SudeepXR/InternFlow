"""Deterministic, explainable scores. Eligibility is a hard gate."""
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from .models import StudentSkill, Skill, Project, Preference, InternshipSkill, TimelineEvent, Bookmark, Application, Company

IST = timezone(timedelta(hours=5, minutes=30))
def india_now():
    return datetime.now(IST)
def skill_key(name):
    aliases = {'js':'javascript','ts':'typescript','postgres':'sql','postgresql':'sql','mysql':'sql','nodejs':'node.js','node':'node.js','react.js':'react','cplusplus':'c++','amazon web services':'aws','bangalore':'bengaluru'}
    value = name.lower().strip()
    return aliases.get(value,value)
def profile_data(db, student):
    skills = list(db.scalars(select(Skill.name).join(StudentSkill, Skill.id==StudentSkill.skill_id).where(StudentSkill.student_id==student.id)))
    prefs = list(db.scalars(select(Preference).where(Preference.student_id==student.id)))
    projects = list(db.scalars(select(Project).where(Project.student_id==student.id)))
    return {k:getattr(student,k) for k in ['id','name','email','college','branch','year','cgpa','graduation_year','bio','experience_months']} | {'skills':skills,'domains':[p.value for p in prefs if p.kind=='domain'],'locations':[p.value for p in prefs if p.kind=='location'],'projects':[{'title':p.title,'description':p.description,'domain':p.domain} for p in projects]}
def calculate_match(profile, internship, required_skills, extra_skills=None):
    possessed = {skill_key(s) for s in profile['skills'] + (extra_skills or [])}
    matched = [s for s in required_skills if skill_key(s) in possessed]
    missing = [s for s in required_skills if skill_key(s) not in possessed]
    reasons = []
    if profile['cgpa'] < internship.min_cgpa: reasons.append('CGPA must be at least ' + str(internship.min_cgpa))
    if profile['year'] != internship.eligible_year: reasons.append('Only year ' + str(internship.eligible_year) + ' students are eligible')
    if internship.eligible_branch.lower() != 'any' and profile['branch'].lower() not in [b.strip().lower() for b in internship.eligible_branch.split(',')]:
        reasons.append('Eligible branches: ' + internship.eligible_branch)
    eligible = not reasons
    project_count = sum(1 for p in profile['projects'] if p['domain'].lower()==internship.domain.lower() or any(skill_key(s) in (p['description']+' '+p['title']).lower() for s in required_skills))
    factors = [
        {'name':'Skills','score':round(40*len(matched)/len(required_skills),1) if required_skills else 40,'max':40,'detail':str(len(matched))+' of '+str(len(required_skills))+' required skills'},
        {'name':'Eligibility','score':20 if eligible else 0,'max':20,'detail':'CGPA, year and branch requirements met' if eligible else '; '.join(reasons)},
        {'name':'Projects','score':min(15,project_count*7.5),'max':15,'detail':str(project_count)+' relevant projects'},
        {'name':'Experience','score':10 if internship.experience_months==0 else round(10*min(1,profile['experience_months']/internship.experience_months),1),'max':10,'detail':'No prior experience required' if internship.experience_months==0 else str(internship.experience_months)+' months requested'},
        {'name':'Domain','score':10 if internship.domain in profile['domains'] else 0,'max':10,'detail':internship.domain},
        {'name':'Location','score':5 if any(skill_key(l)==skill_key(internship.location) for l in profile['locations']) or (internship.work_mode=='Remote' and 'Remote' in profile['locations']) else 0,'max':5,'detail':internship.location}
    ]
    score = round(sum(f['score'] for f in factors))
    return {'score':score if eligible else min(score,49),'eligible':eligible,'eligibility_reasons':reasons,'matched_skills':matched,'missing_skills':missing,'factors':factors,'uncapped_score':score}
def internship_data(db, internship, profile, extra_skills=None):
    company = db.get(Company, internship.company_id)
    skills = list(db.scalars(select(Skill.name).join(InternshipSkill, Skill.id==InternshipSkill.skill_id).where(InternshipSkill.internship_id==internship.id)))
    events = list(db.scalars(select(TimelineEvent).where(TimelineEvent.internship_id==internship.id)))
    dates = {e.kind: e.starts_at.replace(tzinfo=IST).isoformat() for e in events}
    application = db.scalar(select(Application).where(Application.student_id==profile['id'], Application.internship_id==internship.id))
    deadline = next((e.starts_at for e in events if e.kind=='deadline'),None)
    return {k:getattr(internship,k) for k in ['id','role','domain','location','work_mode','stipend','duration_months','min_cgpa','eligible_year','eligible_branch','experience_months','description','application_url','source','is_demo']} | {'company':company.name,'color':company.color,'skills':skills,'dates':dates,'closed':deadline is not None and deadline<india_now().replace(tzinfo=None),'bookmarked':db.get(Bookmark,(profile['id'],internship.id)) is not None,'application':{'id':application.id,'status':application.status} if application else None,'match':calculate_match(profile,internship,skills,extra_skills)}
