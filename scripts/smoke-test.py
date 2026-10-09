"""Read-only HTTP check of the running production app."""
import json, re, sys
from urllib.request import urlopen
base=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000'
def get(path):
    with urlopen(base+path,timeout=10) as r:
        content=r.read().decode()
        if r.status!=200: raise RuntimeError(path+' failed')
        return content
html=get('/')
assert '<title>InternFlow' in html
assets=re.findall(r'(?:src|href)="(/assets/[^"]+)"',html)
assert assets
for asset in assets: get(asset)
health=json.loads(get('/api/health'))
internships=json.loads(get('/api/internships'))
db=json.loads(get('/api/database'))
assert len(db['tables'])==16
assert len(internships)>=12
assert 'BEGIN:VCALENDAR' in get('/api/calendar/export')
for route in ['profile','dashboard','applications','calendar','skill-gaps','notifications']:
    json.loads(get('/api/'+route))
print(json.dumps({'http':'OK','static_assets':len(assets),'relational_engine':health['relational'],'tables':len(db['tables']),'opportunities':len(internships),'calendar_export':'OK','url':base},indent=2))
