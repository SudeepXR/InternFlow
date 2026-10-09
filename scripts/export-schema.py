from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql, sqlite
from backend.models import Base
from backend.queries import QUERIES
for name,dialect in [('postgresql',postgresql.dialect()),('sqlite',sqlite.dialect())]:
    chunks=['-- InternFlow schema. Generated from backend/models.py.\n-- Run against an empty database; app startup creates and seeds tables automatically.\n']
    for table in Base.metadata.sorted_tables:
        chunks.append(str(CreateTable(table).compile(dialect=dialect)).strip()+';')
        for index in table.indexes: chunks.append(str(CreateIndex(index).compile(dialect=dialect)).strip()+';')
    (ROOT/'database').mkdir(exist_ok=True)
    (ROOT/'database'/('schema-'+name+'.sql')).write_text('\n\n'.join(chunks)+'\n',encoding='utf8')
(ROOT/'database'/'queries.sql').write_text('\n\n'.join('-- '+v['title']+'\n'+v['sql']+';' for v in QUERIES.values())+'\n',encoding='utf8')
print('Exported PostgreSQL and SQLite DDL and query examples.')
