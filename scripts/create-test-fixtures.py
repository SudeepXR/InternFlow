"""Generate frontend fixtures through the real API in an isolated temporary DB."""
import os, tempfile, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
with tempfile.TemporaryDirectory() as directory:
    os.environ['DATABASE_URL']='sqlite:///'+str(Path(directory)/'fixtures.db').replace('\\','/')
    os.environ['MONGODB_URI']=''
    os.environ['ENABLE_AI']='false'
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.models import engine
    from backend.matching import india_now
    from datetime import timedelta
    with TestClient(app) as client:
        routes=['profile','internships','dashboard','applications','calendar','health','database','skill-gaps']
        fixtures={route:client.get('/api/'+route).json() for route in routes}
        fixtures['skill-simulation']=client.get('/api/skill-gaps?extra=Docker').json()
        fixtures['query-result']=client.post('/api/database/queries/opportunities').json()
        source='Company: Nova Labs\nRole: Software Engineering Intern\nDomain: Software Development\nLocation: Bengaluru\nWork mode: Hybrid\nStipend: ₹35,000\nDuration: 3 months\nEligible: 3rd year students\nMinimum CGPA: 7.0\nBranches: CSE, ISE, ECE\nSkills: Python, SQL, Docker\nDeadline: '+(india_now()+timedelta(days=20)).isoformat()
        fixtures['extraction']=client.post('/api/extract/announcement',json={'text':source}).json()
        fixtures['new-opportunity']=client.post('/api/ingestions',json={'source_text':source,'announcement':fixtures['extraction']['data']}).json()
        fixtures['prepared-app']=client.post('/api/internships/7/prepare').json()
        fixtures['existing-app']=client.post('/api/internships/1/prepare').json()
    engine.dispose()
    (ROOT/'src'/'test').mkdir(parents=True,exist_ok=True)
    (ROOT/'src'/'test'/'fixtures.json').write_text(json.dumps(fixtures,ensure_ascii=False,indent=2),encoding='utf8')
    print('Created frontend fixtures from the real API.')
