"""Fictional demonstration opportunities, with dates relative to first startup."""
from datetime import timedelta
from sqlalchemy import select, func
from .models import *
from .matching import india_now
from .documents import put_document

def ensure_skill(db,name):
    name = name.strip()
    skill = db.scalar(select(Skill).where(func.lower(Skill.name)==name.lower()))
    if not skill:
        skill = Skill(name=name); db.add(skill); db.flush()
    return skill
def ensure_branch(db,name):
    name=name.strip().upper()
    branch=db.get(Branch,name)
    if not branch:
        branch=Branch(name=name);db.add(branch);db.flush()
    return branch

def add_internship(db,data,is_demo=False):
    company = db.scalar(select(Company).where(func.lower(Company.name)==data['company'].lower()))
    if not company:
        palette=['#426447','#b75c39','#795b9a','#2a78a1','#b29037']
        company=Company(name=data['company'],color=palette[len(data['company'])%len(palette)])
        db.add(company); db.flush()
    fields = ['role','domain','location','work_mode','stipend','duration_months','min_cgpa','eligible_year','experience_months','description','application_url']
    internship=Internship(company_id=company.id,is_demo=is_demo,source='Demo dataset' if is_demo else 'Pasted announcement',**{k:data[k] for k in fields})
    db.add(internship); db.flush()
    if data['eligible_branch'].strip().lower() != 'any':
        internship.eligible_branches=[ensure_branch(db,name) for name in dict.fromkeys(x.strip().upper() for x in data['eligible_branch'].split(',') if x.strip())]
    seen=set()
    for name in data['skills']:
        skill=ensure_skill(db,name)
        if skill.id not in seen: db.add(InternshipSkill(internship_id=internship.id,skill_id=skill.id)); seen.add(skill.id)
    for kind in ['deadline','oa','ppt']:
        if data.get(kind):
            from datetime import datetime
            from .matching import IST
            date=datetime.fromisoformat(data[kind].replace('Z','+00:00'))
            if date.tzinfo: date=date.astimezone(IST).replace(tzinfo=None)
            db.add(TimelineEvent(internship_id=internship.id,kind=kind,starts_at=date))
    db.flush()
    return internship
def seed(db):
    if db.get(Student,1): return
    ensure_branch(db,'CSE')
    student=Student(id=1,name='Alex Morgan',email='alex@example.com',college='RV College of Engineering',branch='CSE',year=3,cgpa=8.6,graduation_year=2028,experience_months=3,bio='Third-year CS student building thoughtful products with Python and React. Interested in software engineering and applied ML.')
    db.add(student); db.flush()
    for name in ['Python','C++','React','JavaScript','SQL','Git','MongoDB','DSA']:
        db.add(StudentSkill(student_id=1,skill_id=ensure_skill(db,name).id))
    for title,desc,domain in [('Campus Connect','A React and MongoDB platform for college communities.','Software Development'),('Smart Traffic Vision','Python image processing for traffic-flow insights.','Machine Learning'),('QueryCraft','SQL and Python database query visualizer.','Software Development')]:
        db.add(Project(student_id=1,title=title,description=desc,domain=domain))
    for kind,values in [('domain',['Software Development','Machine Learning']),('location',['Bengaluru','Remote'])]:
        for value in values: db.add(Preference(student_id=1,kind=kind,value=value))
    now=india_now().replace(tzinfo=None,hour=23,minute=59,second=0,microsecond=0)
    opportunities=[
        ('Microsoft','Software Engineering Intern','Software Development','Bengaluru','Hybrid',50000,['Python','C++','DSA'],7.5,3,3,0),
        ('Razorpay','Frontend Engineering Intern','Software Development','Bengaluru','Hybrid',45000,['React','JavaScript','Git'],7,3,5,0),
        ('Atlassian','Software Development Intern','Software Development','Remote','Remote',60000,['Python','SQL','Docker'],7.5,3,7,0),
        ('Google','Student Researcher · ML','Machine Learning','Bengaluru','On-site',65000,['Python','PyTorch','Machine Learning'],8,3,10,0),
        ('Amazon','Cloud Engineering Intern','Software Development','Bengaluru','On-site',55000,['Python','SQL','AWS','Docker'],7,3,4,0),
        ('Deloitte','Data Analytics Intern','Data Analytics','Hyderabad','Hybrid',30000,['Python','SQL','Excel','Power BI'],6.5,3,9,0),
        ('Zepto','Backend Engineering Intern','Software Development','Bengaluru','On-site',40000,['Python','SQL','Docker'],7,3,12,0),
        ('Adobe','UX Design Intern','Design','Remote','Remote',40000,['Figma','HTML','CSS'],7,3,14,0),
        ('Stripe','Platform Engineering Intern','Software Development','Remote','Remote',70000,['Python','AWS','Docker','Linux'],8,3,16,3),
        ('NVIDIA','Deep Learning Intern','Machine Learning','Pune','On-site',60000,['Python','C++','PyTorch'],9,3,8,6),
        ('Swiggy','Full Stack Intern','Software Development','Bengaluru','Hybrid',35000,['React','Node.js','MongoDB','Git'],7,3,6,0),
        ('UPL','Software Intern','Software Development','Remote','Remote',25000,['Python','Java','C++'],6,3,11,0)
    ]
    for idx,(company,role,domain,location,mode,stipend,skills,cgpa,year,days,exp) in enumerate(opportunities):
        deadline=now+timedelta(days=days)
        data={'company':company,'role':role,'domain':domain,'location':location,'work_mode':mode,'stipend':stipend,'duration_months':6 if idx%3==0 else 3,'min_cgpa':cgpa,'eligible_year':year,'eligible_branch':'CSE, ISE, ECE' if idx%4==0 else 'Any','experience_months':exp,'skills':skills,'description':'Work alongside an experienced team to solve meaningful engineering problems. Build, test and ship real features, participate in technical reviews, and develop your skills with a dedicated mentor. This is a fictional opportunity for the InternFlow course demonstration.','application_url':'','deadline':deadline.isoformat(),'oa':(deadline+timedelta(days=2)).replace(hour=10,minute=0).isoformat() if idx%3!=1 else None,'ppt':(deadline-timedelta(days=1)).replace(hour=14,minute=0).isoformat() if idx%2==0 else None}
        internship=add_internship(db,data,True)
        if idx in [0,2,3,6,8]:
            db.add(Bookmark(student_id=1,internship_id=internship.id))
        if idx in [0,1,2,10]:
            status={0:'Assessment',1:'Applied',2:'Draft',10:'Interview'}[idx]
            app=Application(student_id=1,internship_id=internship.id,status=status,notes='Demo application. No external submission was made.')
            db.add(app); db.flush()
            db.add(ApplicationHistory(application_id=app.id,previous_status=None,new_status=status))
    put_document('resume_version',{'filename':'demo-profile.txt','mode':'Demo dataset','skills':['Python','React','C++','SQL'],'note':'Fictional student profile for demonstration.'},db)
    put_document('announcement',{'source_message':'Microsoft — Software Engineering Intern\\nSkills: Python, C++, DSA\\nEligible: 3rd year students\\nMinimum CGPA: 7.5','mode':'Demo dataset','note':'Fictional announcement. Imported records retain their complete source text and reviewed extraction.'},db)
    db.commit()
