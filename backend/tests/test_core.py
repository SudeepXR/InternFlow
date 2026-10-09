"""Integration tests use an isolated, temporary database, never the demo data."""
import os, tempfile, unittest, json, io
from datetime import timedelta
from pathlib import Path
TEST_DIR=tempfile.TemporaryDirectory()
os.environ['DATABASE_URL']='sqlite:///'+str(Path(TEST_DIR.name)/'test.db').replace('\\','/')
os.environ['MONGODB_URI']=''
os.environ['ENABLE_AI']='false'
from fastapi.testclient import TestClient
from sqlalchemy import select, text, func
from sqlalchemy.exc import IntegrityError
from backend.main import app
from backend.models import *
from backend.matching import calculate_match, india_now
from backend.extraction import extract_announcement, extract_resume
from backend.schemas import AnnouncementInput
from backend.queries import QUERIES

class InternFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client=TestClient(app)
        cls.client.__enter__()
    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None,None,None)
        engine.dispose()
        TEST_DIR.cleanup()
    def test_seed_and_real_relational_schema(self):
        r=self.client.get('/api/database').json()
        self.assertEqual(r['engine'],'sqlite')
        self.assertEqual(len(r['tables']),16)
        self.assertEqual(len([i for i in self.client.get('/api/internships').json() if i['is_demo']]),12)
        with SessionLocal() as db:
            self.assertEqual(db.execute(text('PRAGMA foreign_keys')).scalar(),1)
            db.add(StudentSkill(student_id=999,skill_id=1))
            with self.assertRaises(IntegrityError): db.commit()
    def test_eligibility_is_a_hard_gate(self):
        p=self.client.get('/api/profile').json()
        with SessionLocal() as db:
            i=db.scalar(select(Internship).where(Internship.min_cgpa==9))
            result=calculate_match(p,i,['Python','C++'])
            self.assertFalse(result['eligible'])
            self.assertLessEqual(result['score'],49)
            self.assertIn('CGPA',result['eligibility_reasons'][0])
    def test_matching_aliases_and_score_weights(self):
        p=self.client.get('/api/profile').json()
        with SessionLocal() as db:
            i=db.get(Internship,1)
            result=calculate_match(p,i,['python','cplusplus','DSA'])
            self.assertEqual(len(result['matched_skills']),3)
            self.assertEqual(sum(f['max'] for f in result['factors']),100)
            self.assertEqual(result['score'],100)
    def test_bookmark_persists_and_toggles(self):
        before=self.client.get('/api/internships').json()
        item=next(i for i in before if i['id']==5)
        r=self.client.post('/api/internships/5/bookmark')
        self.assertEqual(r.status_code,200)
        after=next(i for i in self.client.get('/api/internships').json() if i['id']==5)
        self.assertNotEqual(item['bookmarked'],after['bookmarked'])
        self.client.post('/api/internships/5/bookmark')
    def test_draft_idempotency_atomic_status_and_notes(self):
        first=self.client.post('/api/internships/7/prepare')
        self.assertEqual(first.status_code,200,first.text)
        a=first.json()
        second=self.client.post('/api/internships/7/prepare').json()
        self.assertEqual(a['id'],second['id'])
        self.assertIn('Alex Morgan',a['cover_letter'])
        invalid=self.client.patch('/api/applications/'+str(a['id']),json={'status':'Offer'})
        self.assertEqual(invalid.status_code,409)
        updated=self.client.patch('/api/applications/'+str(a['id']),json={'status':'Applied','notes':'Submitted manually'})
        self.assertEqual(updated.status_code,200,updated.text)
        self.assertEqual(updated.json()['history'][-1]['from'],'Draft')
        self.assertEqual(updated.json()['history'][-1]['to'],'Applied')
        self.assertEqual(updated.json()['notes'],'Submitted manually')
        with SessionLocal() as db:
            db.add(Application(student_id=1,internship_id=7))
            with self.assertRaises(IntegrityError): db.commit()
    def test_ineligible_preparation_blocked(self):
        self.assertEqual(self.client.post('/api/internships/10/prepare').status_code,409)
        self.assertEqual(self.client.post('/api/internships/99999/prepare').status_code,404)
    def test_profile_update_recalculates_matches(self):
        original=self.client.get('/api/profile').json()
        changed=original|{'skills':original['skills']+['AWS','Docker']}
        before=next(i for i in self.client.get('/api/internships').json() if i['id']==5)['match']['score']
        self.assertEqual(self.client.put('/api/profile',json=changed).status_code,200)
        after=next(i for i in self.client.get('/api/internships').json() if i['id']==5)['match']['score']
        self.assertGreater(after,before)
        self.client.put('/api/profile',json=original)
        self.assertEqual(self.client.put('/api/profile',json=original|{'cgpa':11}).status_code,422)
    def test_announcement_review_import_and_duplicate_detection(self):
        deadline=(india_now()+timedelta(days=20)).replace(hour=23,minute=59).isoformat()
        source='Company: Test Labs\nRole: Engineering Intern\nLocation: Remote\nMode: Remote\nStipend: ₹25,000\nSkills: Python, SQL, Docker\nMinimum CGPA: 7.0\nEligible: 3rd year students\nDeadline: '+deadline
        extracted=self.client.post('/api/extract/announcement',json={'text':source}).json()
        self.assertEqual(extracted['data']['min_cgpa'],7)
        self.assertEqual(extracted['data']['eligible_year'],3)
        self.assertEqual(extracted['data']['stipend'],25000)
        payload={'announcement':extracted['data'],'source_text':source,'extraction_mode':extracted['mode']}
        r=self.client.post('/api/ingestions',json=payload)
        self.assertEqual(r.status_code,200,r.text)
        self.assertFalse(r.json()['is_demo'])
        self.assertEqual(self.client.post('/api/ingestions',json=payload).status_code,409)
        # Different text with same company/role/location is also a SQL-level conflict.
        self.assertEqual(self.client.post('/api/ingestions',json=payload|{'source_text':source+'\nUpdated message'}).status_code,409)
        docs=self.client.get('/api/database').json()['documents']
        self.assertTrue(any(d['payload'].get('source_message')==source for d in docs))
        rows=self.client.get('/api/calendar').json()
        self.assertTrue(any(e['internship_id']==r.json()['id'] and e['kind']=='deadline' for e in rows))
    def test_missing_date_not_invented_and_invalid_link_rejected(self):
        result=extract_announcement('Company: Empty Labs\nRole: Intern\nSkills: Python')
        self.assertIsNone(result['data']['deadline'])
        self.assertTrue(result['warnings'])
        with self.assertRaises(ValueError):
            AnnouncementInput(company='x',role='y',application_url='javascript:alert(1)')
    def test_calendar_utc_export_and_reminders(self):
        response=self.client.get('/api/calendar/export')
        self.assertEqual(response.status_code,200)
        self.assertIn('BEGIN:VCALENDAR',response.text)
        self.assertIn('TRIGGER:-P1D',response.text)
        self.assertIn('DTSTART:',response.text)
        self.assertTrue(all(len(line.encode('utf8'))<=75 for line in response.text.split('\r\n')))
    def test_skill_simulation_does_not_mutate_profile(self):
        before=self.client.get('/api/profile').json()
        simulation=self.client.get('/api/skill-gaps?extra=AWS,Docker').json()
        self.assertGreater(simulation['after'],simulation['before'])
        self.assertEqual(self.client.get('/api/profile').json(),before)
        nvidia=next(r for r in simulation['simulation'] if r['company']=='NVIDIA')
        self.assertFalse(nvidia['eligible'])
    def test_queries_are_whitelisted(self):
        for name in QUERIES:
            r=self.client.post('/api/database/queries/'+name)
            self.assertEqual(r.status_code,200,r.text)
            self.assertIn('rows',r.json())
        self.assertEqual(self.client.post('/api/database/queries/DROP%20TABLE').status_code,404)
    def test_resume_review_does_not_overwrite_profile(self):
        before=self.client.get('/api/profile').json()
        txt=b'Taylor Smith\ntaylor@example.com\nCollege: Example University\nCGPA: 9.0\nSkills: Python, SQL, Docker'
        r=self.client.post('/api/extract/resume',files={'file':('resume.txt',txt,'text/plain')})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['data']['name'],'Taylor Smith')
        self.assertIn('Docker',r.json()['data']['skills'])
        self.assertEqual(self.client.get('/api/profile').json(),before)
        self.assertEqual(self.client.post('/api/extract/resume',files={'file':('resume.docx',b'abc','application/octet-stream')}).status_code,415)
        self.assertEqual(self.client.post('/api/extract/resume',files={'file':('resume.pdf',b'not a pdf','application/pdf')}).status_code,422)
    def test_ai_opt_in_without_configuration_has_clear_error(self):
        r=self.client.post('/api/extract/announcement',json={'text':'Company: Test Labs\nRole: Intern\nSkills: Python','use_ai':True})
        self.assertEqual(r.status_code,422)
        self.assertIn('not configured',r.json()['detail'])
    def test_nonexistent_api_does_not_return_html(self):
        self.assertEqual(self.client.get('/api/unknown').status_code,404)

    def test_branch_requirements_are_normalized(self):
        with SessionLocal() as db:
            self.assertNotIn('eligible_branch',Internship.__table__.columns.keys())
            self.assertGreater(db.scalar(select(func.count()).select_from(InternshipBranch)),0)
            self.assertIn('branch', [fk.parent.name for fk in Student.__table__.foreign_keys])
            i=db.get(Internship,1)
            self.assertEqual({b.name for b in i.eligible_branches},{'CSE','ISE','ECE'})
    def test_text_based_pdf_resume_upload(self):
        stream=b'BT /F1 12 Tf 50 750 Td (Taylor Smith) Tj 0 -20 Td (taylor@example.com) Tj 0 -20 Td (CGPA: 9.0) Tj 0 -20 Td (Skills: Python, SQL, Docker) Tj ET'
        objects=[
            b'<< /Type /Catalog /Pages 2 0 R >>',
            b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
            b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
        pdf=b'%PDF-1.4\n'; offsets=[0]
        for idx,obj in enumerate(objects,1):
            offsets.append(len(pdf));pdf+=str(idx).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
        xref=len(pdf);pdf+=b'xref\n0 6\n0000000000 65535 f \n'
        for offset in offsets[1:]:pdf+=str(offset).zfill(10).encode()+b' 00000 n \n'
        pdf+=b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+str(xref).encode()+b'\n%%EOF\n'
        r=self.client.post('/api/extract/resume',files={'file':('resume.pdf',pdf,'application/pdf')})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['data']['name'],'Taylor Smith')
        self.assertIn('Docker',r.json()['data']['skills'])

if __name__=='__main__': unittest.main(verbosity=2)
