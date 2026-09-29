from __future__ import annotations
import json, os, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path

def now() -> str: return datetime.now(timezone.utc).isoformat()
def conn():
    path = Path(os.getenv("FASTWIKI_DB", "data/fastwiki.sqlite"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db
def rows(sql, args=()):
    with conn() as db: return [dict(r) for r in db.execute(sql, args).fetchall()]
def row(sql, args=()):
    with conn() as db:
        found = db.execute(sql, args).fetchone()
        return dict(found) if found else None
def execute(sql, args=()):
    with conn() as db:
        cur = db.execute(sql, args); db.commit(); return cur.lastrowid

SCHEMA = """
CREATE TABLE IF NOT EXISTS orgs(id TEXT PRIMARY KEY,name TEXT NOT NULL,logo_url TEXT);
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT NOT NULL,name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS memberships(org_id TEXT,user_id TEXT,role TEXT NOT NULL,PRIMARY KEY(org_id,user_id));
CREATE TABLE IF NOT EXISTS invitations(id INTEGER PRIMARY KEY,org_id TEXT,email TEXT,role TEXT,token TEXT UNIQUE,status TEXT DEFAULT 'pending',created_at TEXT);
CREATE TABLE IF NOT EXISTS spaces(id INTEGER PRIMARY KEY,org_id TEXT NOT NULL,name TEXT NOT NULL,slug TEXT NOT NULL,description TEXT DEFAULT '',visibility TEXT DEFAULT 'org',comments_mode TEXT DEFAULT 'both',created_at TEXT,UNIQUE(org_id,slug));
CREATE TABLE IF NOT EXISTS pages(id INTEGER PRIMARY KEY,org_id TEXT NOT NULL,space_id INTEGER NOT NULL,parent_id INTEGER,title TEXT NOT NULL,slug TEXT NOT NULL,content_json TEXT NOT NULL,markdown TEXT DEFAULT '',plain_text TEXT DEFAULT '',version INTEGER DEFAULT 1,status TEXT DEFAULT 'published',published_at TEXT,published_by TEXT,created_by TEXT,updated_by TEXT,created_at TEXT,updated_at TEXT,deleted_at TEXT);
CREATE TABLE IF NOT EXISTS page_versions(id INTEGER PRIMARY KEY,page_id INTEGER,org_id TEXT,version INTEGER,content_json TEXT,markdown TEXT,title TEXT,created_by TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS comments(id INTEGER PRIMARY KEY,page_id INTEGER,org_id TEXT,user_id TEXT,parent_id INTEGER,body TEXT,kind TEXT DEFAULT 'page',anchor_json TEXT DEFAULT '{}',resolved_at TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS attachments(id INTEGER PRIMARY KEY,page_id INTEGER,org_id TEXT,name TEXT,storage_key TEXT,content_type TEXT,size INTEGER,created_by TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS embeds(id INTEGER PRIMARY KEY,page_id INTEGER,org_id TEXT,product TEXT,title TEXT,url TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS favourites(org_id TEXT,user_id TEXT,page_id INTEGER,PRIMARY KEY(org_id,user_id,page_id));
CREATE TABLE IF NOT EXISTS assistant_threads(id TEXT PRIMARY KEY,org_id TEXT NOT NULL,user_id TEXT NOT NULL,title TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS assistant_messages(id INTEGER PRIMARY KEY,thread_id TEXT NOT NULL,org_id TEXT NOT NULL,user_id TEXT NOT NULL,role TEXT NOT NULL,content TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS assistant_queries(id INTEGER PRIMARY KEY,org_id TEXT NOT NULL,user_id TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_pages_parent ON pages(org_id,parent_id);
CREATE INDEX IF NOT EXISTS idx_assistant_threads_user ON assistant_threads(org_id,user_id,updated_at);
CREATE INDEX IF NOT EXISTS idx_assistant_messages_thread ON assistant_messages(thread_id,id);
CREATE INDEX IF NOT EXISTS idx_assistant_queries_user ON assistant_queries(org_id,user_id,created_at);
"""

def init():
    with conn() as db:
        db.executescript(SCHEMA)
        page_columns={column[1] for column in db.execute("PRAGMA table_info(pages)")}
        comment_columns={column[1] for column in db.execute("PRAGMA table_info(comments)")}
        if "published_at" not in page_columns: db.execute("ALTER TABLE pages ADD COLUMN published_at TEXT")
        if "published_by" not in page_columns: db.execute("ALTER TABLE pages ADD COLUMN published_by TEXT")
        if "parent_id" not in comment_columns: db.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER")
        db.execute("UPDATE pages SET published_at=COALESCE(published_at,updated_at,created_at),published_by=COALESCE(published_by,created_by) WHERE status='published'")
        db.execute("CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(org_id,page_id,parent_id)")
        db.commit()

def provision(who: dict):
    with conn() as db:
        db.execute("INSERT OR IGNORE INTO orgs VALUES(?,?,NULL)", (who["org_id"], who.get("org_name") or "Workspace"))
        db.execute("INSERT INTO users VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET email=excluded.email,name=excluded.name", (who["sub"],who["email"],who.get("name") or who["email"].split("@")[0]))
        db.execute("INSERT OR REPLACE INTO memberships VALUES(?,?,?)",(who["org_id"],who["sub"],who.get("role","member")))
        if not db.execute("SELECT 1 FROM spaces WHERE org_id=?",(who["org_id"],)).fetchone():
            ts=now(); sid=db.execute("INSERT INTO spaces(org_id,name,slug,description,created_at) VALUES(?,?,?,?,?)",(who["org_id"],"Company handbook","handbook","Shared knowledge for the whole team",ts)).lastrowid
            content={"type":"doc","content":[{"type":"heading","attrs":{"level":1},"content":[{"type":"text","text":"Welcome to FastWiki"}]},{"type":"paragraph","content":[{"type":"text","text":"Capture decisions, processes, and ideas in one calm workspace."}]}]}
            db.execute("INSERT INTO pages(org_id,space_id,title,slug,content_json,markdown,plain_text,status,published_at,published_by,created_by,updated_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(who["org_id"],sid,"Welcome","welcome",json.dumps(content),"# Welcome to FastWiki\n\nCapture decisions, processes, and ideas.","Welcome to FastWiki Capture decisions processes and ideas","published",ts,who["sub"],who["sub"],who["sub"],ts,ts))
        db.commit()

def spaces(org): return rows("SELECT * FROM spaces WHERE org_id=? ORDER BY name",(org,))
def pages(org, include_deleted=False):
    where="" if include_deleted else "AND deleted_at IS NULL"
    return rows(f"SELECT p.*,s.name space_name,u.name author_name FROM pages p JOIN spaces s ON s.id=p.space_id LEFT JOIN users u ON u.id=p.created_by WHERE p.org_id=? {where} ORDER BY p.parent_id IS NOT NULL,p.title",(org,))
def page(org,pid): return row("SELECT p.*,s.name space_name,s.comments_mode,u.name author_name FROM pages p JOIN spaces s ON s.id=p.space_id LEFT JOIN users u ON u.id=p.created_by WHERE p.org_id=? AND p.id=?",(org,pid))
def is_admin(who): return who.get("role") in ("owner","admin")
def can_view(who,item): return item and (item["status"]=="published" or item["created_by"]==who["sub"] or is_admin(who))
def visible_pages(who,include_deleted=False): return [item for item in pages(who["org_id"],include_deleted) if can_view(who,item)]
def visible_page(who,pid):
    item=page(who["org_id"],pid)
    return item if can_view(who,item) else None
def create_space(who,name,description="",visibility="org",comments_mode="both"):
    slug=re.sub(r"[^a-z0-9]+","-",name.lower()).strip("-") or "space"
    return execute("INSERT INTO spaces(org_id,name,slug,description,visibility,comments_mode,created_at) VALUES(?,?,?,?,?,?,?)",(who["org_id"],name,slug,description,visibility,comments_mode,now()))
def create_page(who,space_id,title,parent_id=None):
    allowed=row("SELECT id FROM spaces WHERE org_id=? AND id=?",(who["org_id"],space_id))
    if not allowed: raise ValueError("space")
    if parent_id:
        parent=visible_page(who,parent_id)
        if not parent or parent["space_id"]!=space_id or parent["deleted_at"]: raise ValueError("parent")
    empty=json.dumps({"type":"doc","content":[{"type":"paragraph"}]})
    slug=re.sub(r"[^a-z0-9]+","-",title.lower()).strip("-") or "untitled"
    ts=now()
    return execute("INSERT INTO pages(org_id,space_id,parent_id,title,slug,content_json,status,created_by,updated_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(who["org_id"],space_id,parent_id,title,slug,empty,"draft",who["sub"],who["sub"],ts,ts))
def _plain_text(value):
    parts=[]
    def visit(node):
        if isinstance(node,dict):
            if isinstance(node.get("text"),str): parts.append(node["text"])
            for child in node.get("content",[]): visit(child)
        elif isinstance(node,list):
            for child in node: visit(child)
    visit(value)
    return " ".join(parts)
def save_page(who,pid,title,content_json,markdown,version):
    current=visible_page(who,pid)
    if not current or current["deleted_at"]: return None
    if current["version"] != version: return {"conflict":True,"version":current["version"]}
    try: parsed=json.loads(content_json)
    except json.JSONDecodeError: raise ValueError("content_json")
    text=_plain_text(parsed)
    with conn() as db:
        db.execute("INSERT INTO page_versions(page_id,org_id,version,content_json,markdown,title,created_by,created_at) VALUES(?,?,?,?,?,?,?,?)",(pid,who["org_id"],current["version"],current["content_json"],current["markdown"],current["title"],who["sub"],now()))
        db.execute("UPDATE pages SET title=?,content_json=?,markdown=?,plain_text=?,version=version+1,updated_by=?,updated_at=? WHERE org_id=? AND id=? AND version=?",(title,json.dumps(parsed),markdown,text,who["sub"],now(),who["org_id"],pid,version))
        db.commit()
    return page(who["org_id"],pid)
def set_page_status(who,pid,status):
    if status not in ("draft","published"): raise ValueError("status")
    current=visible_page(who,pid)
    if not current or (current["created_by"]!=who["sub"] and not is_admin(who)): return False
    ts=now()
    if status=="published":
        execute("UPDATE pages SET status=?,published_at=?,published_by=?,updated_by=?,updated_at=? WHERE org_id=? AND id=?",(status,ts,who["sub"],who["sub"],ts,who["org_id"],pid))
    else:
        execute("UPDATE pages SET status=?,updated_by=?,updated_at=? WHERE org_id=? AND id=?",(status,who["sub"],ts,who["org_id"],pid))
    return True
def ancestors(who,pid):
    found=[]; seen=set(); current=visible_page(who,pid)
    while current and current.get("parent_id") and current["parent_id"] not in seen:
        seen.add(current["parent_id"]); current=visible_page(who,current["parent_id"])
        if current: found.append(current)
    return list(reversed(found))
def search(org,q):
    like=f"%{q}%"
    return rows("SELECT p.id,p.title,p.plain_text,s.name space_name,p.updated_at FROM pages p JOIN spaces s ON s.id=p.space_id WHERE p.org_id=? AND p.deleted_at IS NULL AND (p.title LIKE ? OR p.plain_text LIKE ?) ORDER BY p.updated_at DESC LIMIT 30",(org,like,like))
def trash(who,pid):
    if visible_page(who,pid): execute("UPDATE pages SET deleted_at=? WHERE org_id=? AND id=?",(now(),who["org_id"],pid))
def restore(who,pid):
    if visible_page(who,pid): execute("UPDATE pages SET deleted_at=NULL WHERE org_id=? AND id=?",(who["org_id"],pid))
def comments(org,pid): return rows("SELECT c.*,u.name user_name FROM comments c JOIN users u ON u.id=c.user_id WHERE c.org_id=? AND c.page_id=? ORDER BY c.id",(org,pid))
def add_comment(who,pid,body,kind="page",anchor_json="{}",parent_id=None):
    target=visible_page(who,pid)
    if not target or target["comments_mode"]=="off" or (target["comments_mode"]=="page" and kind=="inline") or (target["comments_mode"]=="inline" and kind=="page"): raise ValueError("comments disabled")
    if not body.strip(): raise ValueError("comment body")
    if parent_id and not row("SELECT id FROM comments WHERE id=? AND org_id=? AND page_id=?",(parent_id,who["org_id"],pid)): raise ValueError("parent comment")
    return execute("INSERT INTO comments(page_id,org_id,user_id,parent_id,body,kind,anchor_json,created_at) VALUES(?,?,?,?,?,?,?,?)",(pid,who["org_id"],who["sub"],parent_id,body.strip(),kind,anchor_json,now()))
def add_embed(who,pid,product,title,url):
    if not visible_page(who,pid): raise ValueError("page")
    return execute("INSERT INTO embeds(page_id,org_id,product,title,url,created_at) VALUES(?,?,?,?,?,?)",(pid,who["org_id"],product,title,url,now()))
def embeds(org,pid): return rows("SELECT * FROM embeds WHERE org_id=? AND page_id=? ORDER BY id DESC",(org,pid))
def add_attachment(who,pid,name,key,ctype,size):
    if not visible_page(who,pid): raise ValueError("page")
    return execute("INSERT INTO attachments(page_id,org_id,name,storage_key,content_type,size,created_by,created_at) VALUES(?,?,?,?,?,?,?,?)",(pid,who["org_id"],name,key,ctype,size,who["sub"],now()))
def attachment(org,aid): return row("SELECT * FROM attachments WHERE org_id=? AND id=?",(org,aid))
def visible_attachment(who,aid):
    item=attachment(who["org_id"],aid)
    return item if item and visible_page(who,item["page_id"]) else None
def attachments(org,pid): return rows("SELECT * FROM attachments WHERE org_id=? AND page_id=? ORDER BY id DESC",(org,pid))

def create_assistant_thread(who,thread_id,title="New conversation"):
    ts=now(); execute("INSERT INTO assistant_threads(id,org_id,user_id,title,created_at,updated_at) VALUES(?,?,?,?,?,?)",(thread_id,who["org_id"],who["sub"],title,ts,ts)); return thread_id
def assistant_threads(who): return rows("SELECT * FROM assistant_threads WHERE org_id=? AND user_id=? ORDER BY updated_at DESC LIMIT 30",(who["org_id"],who["sub"]))
def assistant_thread(who,thread_id): return row("SELECT * FROM assistant_threads WHERE id=? AND org_id=? AND user_id=?",(thread_id,who["org_id"],who["sub"]))
def assistant_messages(who,thread_id):
    if not assistant_thread(who,thread_id): return []
    return rows("SELECT id,role,content,created_at FROM assistant_messages WHERE thread_id=? AND org_id=? AND user_id=? ORDER BY id",(thread_id,who["org_id"],who["sub"]))
def assistant_message(who,message_id): return row("SELECT m.*,t.title thread_title FROM assistant_messages m JOIN assistant_threads t ON t.id=m.thread_id WHERE m.id=? AND m.org_id=? AND m.user_id=?",(message_id,who["org_id"],who["sub"]))
def add_assistant_message(who,thread_id,role,content):
    if role not in ("user","assistant") or not assistant_thread(who,thread_id): raise ValueError("thread")
    ts=now(); message_id=execute("INSERT INTO assistant_messages(thread_id,org_id,user_id,role,content,created_at) VALUES(?,?,?,?,?,?)",(thread_id,who["org_id"],who["sub"],role,content,ts))
    if role=="user": execute("UPDATE assistant_threads SET title=CASE WHEN title='New conversation' THEN ? ELSE title END,updated_at=? WHERE id=?",(content[:60] or "New conversation",ts,thread_id))
    else: execute("UPDATE assistant_threads SET updated_at=? WHERE id=?",(ts,thread_id))
    return message_id
def assistant_queries_today(who):
    start=datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0).isoformat()
    found=row("SELECT count(*) n FROM assistant_queries WHERE org_id=? AND user_id=? AND created_at>=?",(who["org_id"],who["sub"],start))
    return found["n"] if found else 0
def record_assistant_query(who): execute("INSERT INTO assistant_queries(org_id,user_id,created_at) VALUES(?,?,?)",(who["org_id"],who["sub"],now()))

init()
