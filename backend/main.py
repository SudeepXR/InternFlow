import os, io, json, hashlib, logging
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import Response, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, delete, func, text, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .models import *
from .schemas import *
from .matching import profile_data, internship_data, india_now, IST, skill_key
from .seed import seed, ensure_skill, ensure_branch, add_internship
from .extraction import extract_announcement, extract_resume, ai_available
from .documents import put_document, list_documents, document_health, sync_documents
from .queries import QUERIES

log = logging.getLogger('internflow')
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with SessionLocal() as db: seed(db)
    if os.getenv('MONGODB_URI'):
        try: sync_documents()
        except Exception: log.warning('MongoDB synchronization pending; documents are retained in the transactional outbox.')
    yield
app = FastAPI(title='InternFlow',description='Internship intelligence and application assistance. Local single-student course prototype.',version='1.0.0',lifespan=lifespan)

@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return JSONResponse(status_code=409,content={'detail':'This record already exists or violates a database constraint'})

def student(db):
    item=db.get(Student,1)
    if not item: raise HTTPException(503,'Profile has not been initialized')
    return item
def opportunity(db, id):
    item=db.get(Internship,id)
    if not item: raise HTTPException(404,'Internship not found')
    return item
def sync_safely():
    try: sync_documents()
    except Exception: log.warning('MongoDB sync pending; source document remains durable.')
def commit(db):
    try: db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'This record already exists or violates a database constraint')
def profile(db): return profile_data(db,student(db))

@app.get('/api/health')
def health():
    return {'status':'ok','relational':engine.dialect.name,'documents':document_health(),'ai':{'enabled':ai_available(),'mode':'LangChain (opt-in)' if ai_available() else 'Local extraction rules'},'timezone':'Asia/Kolkata','now':india_now().isoformat(),'prototype':'Single-student local demo; authentication and live integrations are not enabled.'}

@app.get('/api/profile')
def get_profile(db:Session=Depends(get_db)): return profile(db)

@app.put('/api/profile')
def update_profile(data:ProfileInput, background:BackgroundTasks, db:Session=Depends(get_db)):
    item=student(db)
    values=data.model_dump()
    values["branch"]=ensure_branch(db,data.branch).name
    for key,value in values.items():
        if key not in ('skills','projects','domains','locations'): setattr(item,key,value)
    db.execute(delete(StudentSkill).where(StudentSkill.student_id==1))
    db.execute(delete(Project).where(Project.student_id==1))
    db.execute(delete(Preference).where(Preference.student_id==1))
    seen=set()
    for name in data.skills:
        s=ensure_skill(db,name)
        if s.id not in seen: db.add(StudentSkill(student_id=1,skill_id=s.id)); seen.add(s.id)
    for project in data.projects: db.add(Project(student_id=1,**project.model_dump()))
    for kind,values in [('domain',data.domains),('location',data.locations)]:
        for value in values: db.add(Preference(student_id=1,kind=kind,value=value))
    put_document('profile_revision',{'profile':data.model_dump(),'mode':'Reviewed by student'},db)
    commit(db); background.add_task(sync_safely)
    return profile(db)

@app.get('/api/internships')
def get_internships(db:Session=Depends(get_db)):
    p=profile(db)
    rows=[internship_data(db,i,p) for i in db.scalars(select(Internship))]
    return sorted(rows,key=lambda i:(i['closed'],-i['match']['score']))

@app.post('/api/internships/{id}/bookmark')
def bookmark(id:int,db:Session=Depends(get_db)):
    opportunity(db,id)
    existing=db.get(Bookmark,(1,id))
    if existing: db.delete(existing)
    else: db.add(Bookmark(student_id=1,internship_id=id))
    commit(db)
    return {'bookmarked':not bool(existing)}

@app.get('/api/dashboard')
def dashboard(db:Session=Depends(get_db)):
    rows=get_internships(db)
    apps=list(db.scalars(select(Application).where(Application.student_id==1)))
    events=calendar(db)
    now=india_now()
    upcoming=[e for e in events if datetime.fromisoformat(e['starts_at'])>=now]
    return {'opportunities':len([r for r in rows if not r['closed']]),'strong_matches':sum(1 for r in rows if r['match']['eligible'] and r['match']['score']>=80 and not r['closed']),'applications':len([a for a in apps if a.status not in ['Draft','Withdrawn']]),'due_this_week':sum(1 for e in upcoming if e['kind']=='deadline' and datetime.fromisoformat(e['starts_at'])<now+timedelta(days=7)),'upcoming':upcoming[:6],'notifications':notifications(db),'profile_completeness':round(sum([bool(profile(db)['skills']),bool(profile(db)['projects']),bool(student(db).bio),bool(profile(db)['domains']),bool(student(db).college)])/5*100)}

def letter(p, i):
    matched=i['match']['matched_skills']
    projects=[x['title'] for x in p['projects'] if x['domain']==i['domain']]
    return ('Dear '+i['company']+' hiring team,\n\nI am '+p['name']+', a year '+str(p['year'])+' '+p['branch']+' student at '+p['college']+'. I would like to apply for the '+i['role']+' opportunity.\n\n'+('My skills include '+', '.join(matched)+'. ' if matched else '')+('Through '+', '.join(projects[:2])+', I have practiced turning ideas into working projects. ' if projects else '')+'I am interested in contributing to your team and learning through hands-on work.\n\nI would appreciate the opportunity to discuss how my background aligns with this internship. Thank you for considering my application.\n\nBest regards,\n'+p['name']+'\n'+p['email'])

def app_data(db,a):
    p=profile(db); i=internship_data(db,opportunity(db,a.internship_id),p)
    history=list(db.scalars(select(ApplicationHistory).where(ApplicationHistory.application_id==a.id).order_by(ApplicationHistory.changed_at)))
    return {'id':a.id,'internship':i,'status':a.status,'notes':a.notes,'cover_letter':a.cover_letter,'created_at':a.created_at.replace(tzinfo=timezone.utc).isoformat(),'updated_at':a.updated_at.replace(tzinfo=timezone.utc).isoformat(),'answers':{'Full name':p['name'],'Email':p['email'],'College':p['college'],'Branch':p['branch'],'CGPA':str(p['cgpa']),'Graduation year':str(p['graduation_year']),'Relevant skills':', '.join(i['match']['matched_skills'])},'history':[{'from':h.previous_status,'to':h.new_status,'at':h.changed_at.replace(tzinfo=timezone.utc).isoformat()} for h in history]}

@app.get('/api/applications')
def applications(db:Session=Depends(get_db)):
    return [app_data(db,a) for a in db.scalars(select(Application).where(Application.student_id==1).order_by(Application.updated_at.desc()))]

@app.post('/api/internships/{id}/prepare')
def prepare(id:int,db:Session=Depends(get_db)):
    i=internship_data(db,opportunity(db,id),profile(db))
    a=db.scalar(select(Application).where(Application.student_id==1,Application.internship_id==id))
    if a:
        if not a.cover_letter:
            a.cover_letter=letter(profile(db),i)
            commit(db)
        return app_data(db,a)
    if i['closed']: raise HTTPException(409,'The application deadline has passed')
    if not i['match']['eligible']: raise HTTPException(409,'Your profile does not meet the eligibility requirements')
    a=Application(student_id=1,internship_id=id,cover_letter=letter(profile(db),i))
    db.add(a); db.flush()
    db.add(ApplicationHistory(application_id=a.id,previous_status=None,new_status='Draft'))
    commit(db)
    return app_data(db,a)

@app.patch('/api/applications/{id}')
def change_application(id:int,data:ApplicationUpdate,db:Session=Depends(get_db)):
    a=db.get(Application,id)
    if not a or a.student_id!=1: raise HTTPException(404,'Application not found')
    if data.status and data.status!=a.status:
        if a.status=='Draft' and data.status not in ('Applied','Withdrawn'):
            raise HTTPException(409,'Mark this draft as applied after submitting it, or withdraw it')
        if data.status=='Applied' and a.status=='Draft':
            i=internship_data(db,opportunity(db,a.internship_id),profile(db))
            if i['closed']: raise HTTPException(409,'The deadline has passed')
            if not i['match']['eligible']: raise HTTPException(409,'The current profile is not eligible')
        db.add(ApplicationHistory(application_id=a.id,previous_status=a.status,new_status=data.status))
        a.status=data.status
    if data.cover_letter is not None: a.cover_letter=data.cover_letter
    if data.notes is not None: a.notes=data.notes
    a.updated_at=utcnow()
    commit(db)
    return app_data(db,a)

@app.get('/api/calendar')
def calendar(db:Session=Depends(get_db)):
    p=profile(db); result=[]
    for e in db.scalars(select(TimelineEvent).order_by(TimelineEvent.starts_at)):
        i=internship_data(db,opportunity(db,e.internship_id),p)
        result.append({'id':e.id,'internship_id':i['id'],'company':i['company'],'role':i['role'],'color':i['color'],'kind':e.kind,'starts_at':e.starts_at.replace(tzinfo=IST).isoformat(),'watched':i['bookmarked'] or bool(i['application'])})
    return result

def notifications(db):
    now=india_now(); out=[]
    for e in calendar(db):
        when=datetime.fromisoformat(e['starts_at'])
        if now<=when<=now+timedelta(days=3) and (e['kind']=='deadline' or e['watched']):
            out.append(e|{'message':('Application closes' if e['kind']=='deadline' else 'Online assessment' if e['kind']=='oa' else 'Pre-placement talk')+' · '+e['company']})
    return out[:20]

@app.get('/api/notifications')
def get_notifications(db:Session=Depends(get_db)): return notifications(db)

@app.get('/api/calendar/export')
def export_calendar(db:Session=Depends(get_db)):
    def esc(value): return value.replace('\\','\\\\').replace('\n','\\n').replace(';','\\;').replace(',','\\,')
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//InternFlow//Internship calendar//EN','CALSCALE:GREGORIAN']
    for e in calendar(db):
        when=datetime.fromisoformat(e['starts_at']).astimezone(timezone.utc)
        lines+=['BEGIN:VEVENT','UID:internflow-'+str(e['id'])+'@local','DTSTAMP:'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),'DTSTART:'+when.strftime('%Y%m%dT%H%M%SZ'),'DTEND:'+(when+timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ'),'SUMMARY:'+esc(e['company']+' · '+e['kind'].upper()+' · '+e['role']),'BEGIN:VALARM','TRIGGER:-P1D','ACTION:DISPLAY','DESCRIPTION:InternFlow reminder','END:VALARM','END:VEVENT']
    lines.append('END:VCALENDAR')
    # RFC 5545 line folding: split UTF-8 by codepoints without exceeding 75 bytes.
    folded=[]
    for line in lines:
        piece=''
        for ch in line:
            if len((piece+ch).encode('utf-8'))>75:
                folded.append(piece); piece=' '
            piece+=ch
        folded.append(piece)
    return Response('\r\n'.join(folded)+'\r\n',media_type='text/calendar',headers={'Content-Disposition':'attachment; filename=internflow-calendar.ics'})

@app.post('/api/extract/announcement')
def extract(data:TextExtraction):
    try: return extract_announcement(data.text,data.use_ai)
    except ValueError as e: raise HTTPException(422,str(e))
    except Exception: raise HTTPException(502,'Extraction could not complete. Try local rules or check your AI configuration.')

@app.post('/api/ingestions')
def ingest(data:IngestionInput,background:BackgroundTasks,db:Session=Depends(get_db)):
    if not data.announcement.deadline: raise HTTPException(422,'A reviewed application deadline is required')
    digest=hashlib.sha256(data.source_text.strip().encode()).hexdigest()
    if db.scalar(select(Ingestion).where(Ingestion.source_hash==digest)): raise HTTPException(409,'This source announcement was already imported')
    item=add_internship(db,data.announcement.model_dump())
    doc_id=put_document('announcement',{'source_message':data.source_text,'extracted_data':data.announcement.model_dump(),'mode':data.extraction_mode,'internship_id':item.id,'reviewed':True,'source_hash':digest},db)
    db.add(Ingestion(source_hash=digest,internship_id=item.id,document_id=doc_id))
    commit(db); background.add_task(sync_safely)
    return internship_data(db,item,profile(db))

@app.post('/api/extract/resume')
async def resume(background:BackgroundTasks,file:UploadFile=File(...),use_ai:bool=Query(False),db:Session=Depends(get_db)):
    data=await file.read(8*1024*1024+1)
    if len(data)>8*1024*1024: raise HTTPException(413,'Resume must be smaller than 8 MB')
    name=Path(file.filename or 'resume').name
    try:
        if name.lower().endswith('.pdf'):
            from pypdf import PdfReader
            reader=PdfReader(io.BytesIO(data))
            if len(reader.pages)>30: raise HTTPException(422,'Resume must contain at most 30 pages')
            extracted='\n'.join(p.extract_text() or '' for p in reader.pages)
        elif name.lower().endswith('.txt'): extracted=data.decode('utf-8')
        else: raise HTTPException(415,'Upload a PDF or UTF-8 text file')
    except HTTPException: raise
    except Exception: raise HTTPException(422,'Could not read this file. Use an unencrypted PDF or UTF-8 text file.')
    if len(extracted.strip())<20: raise HTTPException(422,'No readable text found. Scanned PDFs need OCR; try a text-based PDF or a TXT resume.')
    try: result=extract_resume(extracted[:30000],use_ai)
    except ValueError as e: raise HTTPException(422,str(e))
    except Exception: raise HTTPException(502,'Resume extraction could not complete. Try local rules or check your AI configuration.')
    put_document('resume_version',{'filename':name,'raw_text':extracted[:30000],'extracted_data':result['data'],'mode':result['mode'],'applied_to_profile':False},db)
    commit(db); background.add_task(sync_safely)
    return result

@app.get('/api/skill-gaps')
def gaps(extra:str='',db:Session=Depends(get_db)):
    p=profile(db); items=list(db.scalars(select(Internship)))
    current=[internship_data(db,i,p) for i in items]
    candidates={}
    for i in current:
        if i['match']['eligible'] and not i['closed']:
            for s in i['match']['missing_skills']: candidates.setdefault(s,[]).append(i)
    roadmap=[]
    for s,affected in candidates.items():
        unlocked=[]
        for row in affected:
            item=db.get(Internship,row['id'])
            after=internship_data(db,item,p,[s])
            if after['match']['score']>=80 and row['match']['score']<80: unlocked.append(row['company'])
        roadmap.append({'skill':s,'demand':len(affected),'unlocks':len(unlocked),'companies':list(dict.fromkeys(r['company'] for r in affected)),'unlocked_companies':unlocked})
    roadmap.sort(key=lambda r:(-r['unlocks'],-r['demand'],r['skill']))
    additions=[x.strip() for x in extra.split(',') if x.strip()][:20]
    simulated=[{'id':i.id,'company':r['company'],'role':r['role'],'before':r['match']['score'],'after':internship_data(db,i,p,additions)['match']['score'],'eligible':r['match']['eligible']} for i,r in zip(items,current) if not r['closed']]
    return {'roadmap':roadmap,'simulation':simulated,'threshold':80,'before':sum(r['before']>=80 and r['eligible'] for r in simulated),'after':sum(r['after']>=80 and r['eligible'] for r in simulated)}

@app.get('/api/database')
def database(db:Session=Depends(get_db)):
    tables=[]
    inspector=inspect(engine)
    for name in sorted(Base.metadata.tables):
        t=Base.metadata.tables[name]
        tables.append({'name':name,'rows':db.scalar(select(func.count()).select_from(t)),'columns':[{'name':c.name,'type':str(c.type),'pk':c.primary_key,'nullable':c.nullable} for c in t.columns],'foreign_keys':[{'column':fk.parent.name,'references':str(fk.column)} for fk in t.foreign_keys],'constraints':[str(c.sqltext) for c in t.constraints if isinstance(c,CheckConstraint)]})
    return {'engine':engine.dialect.name,'tables':tables,'documents':list_documents(db),'document_store':document_health(),'queries':[{'id':k,**v} for k,v in QUERIES.items()]}

@app.post('/api/database/queries/{name}')
def query(name:str,db:Session=Depends(get_db)):
    if name not in QUERIES: raise HTTPException(404,'Unknown query. Only predefined read-only examples are supported.')
    result=db.execute(text(QUERIES[name]['sql']))
    return {'columns':list(result.keys()),'rows':[dict(r._mapping) for r in result]}

@app.post('/api/database/sync')
def sync():
    try: sync_documents()
    except Exception: raise HTTPException(503,'MongoDB is unavailable. The local outbox retains all documents.')
    return {'status':'synced','documents':document_health()}

@app.get('/api/export')
def export(db:Session=Depends(get_db)):
    result={'exported_at':india_now().isoformat(),'profile':profile(db),'applications':applications(db),'saved_opportunities':[i for i in get_internships(db) if i['bookmarked']]}
    return Response(json.dumps(result,ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':'attachment; filename=internflow-export.json'})

@app.get('/api/{unknown:path}',include_in_schema=False)
def unknown_api(unknown:str): raise HTTPException(404,'API endpoint not found')

DIST=ROOT/'dist'
if DIST.exists():
    app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')
    @app.get('/{path:path}',include_in_schema=False)
    def frontend(path:str):
        candidate=(DIST/path).resolve()
        if candidate.is_relative_to(DIST.resolve()) and candidate.is_file(): return FileResponse(candidate)
        return FileResponse(DIST/'index.html')
