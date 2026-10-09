"""MongoDB document adapter with a durable SQLite JSON fallback."""
import os, json, uuid
from sqlalchemy import select
from .models import Document, SessionLocal

def mongo_collection():
    uri = os.getenv('MONGODB_URI')
    if not uri:
        return None
    from pymongo import MongoClient
    client = MongoClient(uri, serverSelectionTimeoutMS=2500)
    return client[os.getenv('MONGODB_DATABASE', 'internflow')]['documents']

def put_document(kind, payload, db):
    document_id = str(uuid.uuid4())
    # A relational outbox makes document writes atomic with business records.
    db.add(Document(id=document_id, kind=kind, payload=json.dumps(payload, ensure_ascii=False)))
    return document_id

def sync_documents():
    collection = mongo_collection()
    if collection is None:
        return
    with SessionLocal() as db:
        for d in db.scalars(select(Document)).all():
            collection.update_one({'id': d.id}, {'$set': {'kind': d.kind, 'payload': json.loads(d.payload), 'created_at': d.created_at.isoformat()}}, upsert=True)

def list_documents(db, limit=20):
    return [{'id': d.id, 'kind': d.kind, 'payload': json.loads(d.payload), 'created_at': d.created_at.isoformat()} for d in db.scalars(select(Document).order_by(Document.created_at.desc()).limit(limit)).all()]

def document_health():
    if not os.getenv('MONGODB_URI'):
        return {'mode': 'SQLite JSON', 'connected': True, 'detail': 'Local document store; set MONGODB_URI to mirror the durable outbox into MongoDB.'}
    try:
        collection = mongo_collection()
        collection.database.client.admin.command('ping')
        return {'mode': 'MongoDB + relational outbox', 'connected': True, 'detail': 'Documents synchronized from the transactional outbox.'}
    except Exception:
        return {'mode': 'MongoDB pending sync', 'connected': False, 'detail': 'Documents remain durable in the relational outbox. Check MongoDB and retry sync.'}
