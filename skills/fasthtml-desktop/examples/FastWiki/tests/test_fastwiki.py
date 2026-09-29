import importlib, json, os, sqlite3
import base64, hashlib, hmac, time
from pathlib import Path
import pytest

@pytest.fixture()
def database(tmp_path,monkeypatch):
    monkeypatch.setenv("FASTWIKI_DB",str(tmp_path/"test.sqlite"))
    monkeypatch.setenv("FASTWIKI_UPLOAD_DIR",str(tmp_path/"uploads"))
    from fastwiki import db
    importlib.reload(db)
    a={"sub":"a","email":"a@example.com","name":"Alice","org_id":"org-a","org_name":"Alpha","role":"owner"}
    b={"sub":"b","email":"b@example.com","name":"Bob","org_id":"org-b","org_name":"Beta","role":"owner"}
    db.provision(a);db.provision(b)
    return db,a,b

def test_schema_migrates_existing_pages_and_comments(tmp_path,monkeypatch):
    path=tmp_path/"legacy.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE pages(id INTEGER PRIMARY KEY,org_id TEXT NOT NULL,space_id INTEGER NOT NULL,parent_id INTEGER,title TEXT NOT NULL,slug TEXT NOT NULL,content_json TEXT NOT NULL,markdown TEXT DEFAULT '',plain_text TEXT DEFAULT '',version INTEGER DEFAULT 1,status TEXT DEFAULT 'published',created_by TEXT,updated_by TEXT,created_at TEXT,updated_at TEXT,deleted_at TEXT)")
        connection.execute("CREATE TABLE comments(id INTEGER PRIMARY KEY,page_id INTEGER,org_id TEXT,user_id TEXT,body TEXT,kind TEXT DEFAULT 'page',anchor_json TEXT DEFAULT '{}',resolved_at TEXT,created_at TEXT)")
        connection.execute("INSERT INTO pages(id,org_id,space_id,title,slug,content_json,status,created_by,created_at,updated_at) VALUES(1,'org',1,'Legacy','legacy','{}','published','author','2026-01-01T00:00:00+00:00','2026-01-02T00:00:00+00:00')")
    monkeypatch.setenv("FASTWIKI_DB",str(path))
    from fastwiki import db
    importlib.reload(db)

    page_columns={column["name"] for column in db.rows("PRAGMA table_info(pages)")}
    comment_columns={column["name"] for column in db.rows("PRAGMA table_info(comments)")}
    migrated=db.row("SELECT published_at,published_by FROM pages WHERE id=1")
    assert {"published_at","published_by"}<=page_columns
    assert "parent_id" in comment_columns
    assert migrated=={"published_at":"2026-01-02T00:00:00+00:00","published_by":"author"}

def test_tenant_safe_pages(database):
    db,a,b=database
    aid=db.pages("org-a")[0]["id"]
    assert db.page("org-a",aid)
    assert db.page("org-b",aid) is None
    assert all(p["org_id"]=="org-b" for p in db.pages("org-b"))

def test_optimistic_lock_and_version_history(database):
    db,a,_=database
    page=db.pages("org-a")[0]
    body=json.dumps({"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Updated"}]}]})
    saved=db.save_page(a,page["id"],"Updated",body,"Updated",1)
    assert saved["version"]==2
    assert db.save_page(a,page["id"],"Stale",body,"",1)=={"conflict":True,"version":2}
    assert db.row("SELECT count(*) n FROM page_versions WHERE page_id=?",(page["id"],))["n"]==1

def test_trash_is_recoverable_and_scoped(database):
    db,a,b=database
    pid=db.pages("org-a")[0]["id"]
    db.trash(b,pid)
    assert db.page("org-a",pid)["deleted_at"] is None
    db.trash(a,pid)
    assert db.page("org-a",pid)["deleted_at"]
    db.restore(a,pid)
    assert db.page("org-a",pid)["deleted_at"] is None

def test_comment_modes(database):
    db,a,_=database
    pid=db.pages("org-a")[0]["id"]
    db.add_comment(a,pid,"A useful note","inline")
    assert db.comments("org-a",pid)[0]["body"]=="A useful note"
    db.execute("UPDATE spaces SET comments_mode='page' WHERE org_id=?",("org-a",))
    with pytest.raises(ValueError):
        db.add_comment(a,pid,"No inline","inline")

def test_comment_replies_are_nested_and_page_scoped(database):
    db,a,_=database
    page=db.pages("org-a")[0]
    root=db.add_comment(a,page["id"],"First comment")
    reply=db.add_comment(a,page["id"],"A reply","reply",parent_id=root)
    nested=db.add_comment(a,page["id"],"A nested reply","reply",parent_id=reply)
    thread=db.comments("org-a",page["id"])

    assert [item["parent_id"] for item in thread]==[None,root,reply]
    assert thread[-1]["id"]==nested
    other=db.create_page(a,page["space_id"],"Other page")
    with pytest.raises(ValueError):
        db.add_comment(a,other,"Wrong thread","reply",parent_id=root)

def test_local_attachment_storage(database):
    db,a,_=database
    from fastwiki import storage
    key="org-a/1/example.txt"
    storage.put(key,b"hello","text/plain")
    assert storage.get(key)==b"hello"

def test_new_page_route_creates_page(database,monkeypatch):
    db,_,_=database
    monkeypatch.setenv("FASTWIKI_ENV","development")
    from app import app
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        assert client.get("/auth/dev").status_code==200
        before=len(db.pages("dev"))
        response=client.get("/pages/new",follow_redirects=False)

    assert response.status_code==303
    assert response.headers["location"].startswith("/pages/")
    assert len(db.pages("dev"))==before+1

def test_health_exposes_dated_release(database):
    from app import app
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        response=client.get("/health")

    assert response.status_code==200
    assert response.json()["version"]=="1.0.0"
    assert response.json()["release_date"]=="2026-09-08"

def test_drafts_are_private_until_published(database):
    db,a,_=database
    member={"sub":"member","email":"member@example.com","name":"Member","org_id":"org-a","org_name":"Alpha","role":"member"}
    db.provision(member)
    space=db.spaces("org-a")[0]
    pid=db.create_page(a,space["id"],"Private plan")

    assert db.visible_page(a,pid)["status"]=="draft"
    assert db.visible_page(member,pid) is None
    assert db.set_page_status(a,pid,"published")
    published=db.visible_page(member,pid)
    assert published["title"]=="Private plan"
    assert published["published_at"]
    assert published["published_by"]==a["sub"]
    assert published["author_name"]==a["name"]
    assert not db.set_page_status(member,pid,"draft")

def test_page_layout_has_bottom_resources_threads_and_publication_metadata(database,monkeypatch):
    db,_,_=database
    monkeypatch.setenv("FASTWIKI_ENV","development")
    from app import app
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        client.get("/auth/dev")
        page=db.pages("dev")[0]
        who={"sub":"kaljuvee@gmail.com","email":"kaljuvee@gmail.com","name":"Julian Kaljuvee","org_id":"dev","org_name":"FastSME","role":"owner"}
        root=db.add_comment(who,page["id"],"Root discussion")
        db.add_comment(who,page["id"],"Threaded answer","reply",parent_id=root)
        response=client.get(f"/pages/{page['id']}")

    assert response.status_code==200
    assert 'class="bottom-bar"' in response.text
    assert 'class="rightbar"' not in response.text
    assert "Root discussion" in response.text and "Threaded answer" in response.text
    assert "Reply to Julian Kaljuvee" in response.text
    assert "Published " in response.text and "Version " in response.text
    assert 'id="publication-version">1</span>' in response.text
    assert "Julian Kaljuvee" in response.text
    assert 'id="mode-rich"' in response.text and 'aria-pressed="true"' in response.text
    assert 'id="mode-block"' in response.text and ">Blocks</button>" in response.text
    assert 'id="mode-md"' in response.text
    assert f'href="/pages/{page["id"]}/pdf"' in response.text
    assert "Download PDF" in response.text

def test_page_pdf_is_a_protected_download(database,monkeypatch):
    db,_,_=database
    monkeypatch.setenv("FASTWIKI_ENV","development")
    from app import app
    from starlette.testclient import TestClient

    with TestClient(app) as anonymous:
        page_id=db.pages("org-a")[0]["id"]
        redirect=anonymous.get(f"/pages/{page_id}/pdf",follow_redirects=False)
        assert redirect.status_code==303

    with TestClient(app) as client:
        client.get("/auth/dev")
        page=db.pages("dev")[0]
        response=client.get(f"/pages/{page['id']}/pdf")

    assert response.status_code==200
    assert response.headers["content-type"]=="application/pdf"
    assert "attachment;" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")
    assert len(response.content)>1000

def test_page_pdf_renders_lists_code_and_tables():
    from fastwiki.pdf import page_pdf
    content={"type":"doc","content":[
        {"type":"heading","attrs":{"level":2},"content":[{"type":"text","text":"Section"}]},
        {"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":"One"}]}]}]},
        {"type":"blockquote","content":[{"type":"paragraph","content":[{"type":"text","text":"Quoted"}]}]},
        {"type":"codeBlock","content":[{"type":"text","text":"print(1)"}]},
        {"type":"table","content":[
            {"type":"tableRow","content":[{"type":"tableHeader","content":[{"type":"paragraph","content":[{"type":"text","text":"Name"}]}]}]},
            {"type":"tableRow","content":[{"type":"tableCell","content":[{"type":"paragraph","content":[{"type":"text","text":"Value"}]}]}]},
        ]},
    ]}
    result=page_pdf({"title":"Rich page","status":"draft","version":3,"author_name":"Alice","content_json":json.dumps(content)})

    assert result.startswith(b"%PDF-")
    assert len(result)>1000

def test_child_pages_form_tenant_safe_hierarchy(database):
    db,a,b=database
    space=db.spaces("org-a")[0]
    parent=db.create_page(a,space["id"],"Parent")
    child=db.create_page(a,space["id"],"Child",parent_id=parent)
    grandchild=db.create_page(a,space["id"],"Grandchild",parent_id=child)

    assert db.page("org-a",child)["parent_id"]==parent
    assert [item["id"] for item in db.ancestors(a,grandchild)]==[parent,child]
    with pytest.raises(ValueError):
        db.create_page(b,db.spaces("org-b")[0]["id"],"Invalid child",parent_id=parent)

def test_assistant_sources_and_limits_are_tenant_scoped(database,monkeypatch):
    db,a,b=database
    from fastwiki import assistant
    monkeypatch.setenv("FASTWIKI_AI_QUERY_LIMIT","1")
    member={"sub":"member","email":"member@example.com","name":"Member","org_id":"org-a","org_name":"Alpha","role":"member"}
    db.provision(member)
    pid=db.pages("org-a")[0]["id"]
    db.save_page(a,pid,"Alpha handbook",json.dumps({"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Alpha launch policy"}]}]}),"Alpha launch policy",1)

    sources=assistant.source_pages(member,"launch policy")
    assert sources[0]["title"]=="Alpha handbook"
    assert all(item["id"]!=db.pages("org-b")[0]["id"] for item in sources)
    assert assistant.remaining_queries(member)==1
    db.record_assistant_query(member)
    assert assistant.remaining_queries(member)==0
    assert assistant.remaining_queries(a) is None

def test_configured_admin_role(monkeypatch):
    from fastwiki import assistant
    monkeypatch.setenv("FASTWIKI_ADMIN_EMAILS","admin@example.com")
    identity={"sub":"1","email":"ADMIN@example.com","role":"member"}
    assert assistant.configured_admin(identity)["role"]=="admin"

def test_assistant_ui_streams_grounded_response(database,monkeypatch):
    db,_,_=database
    monkeypatch.setenv("FASTWIKI_ENV","development")
    from app import app
    from fastwiki import assistant
    from starlette.testclient import TestClient
    monkeypatch.setattr(assistant,"stream_answer",lambda identity,question,history,sources:iter(["Grounded answer [1]"]))

    with TestClient(app) as client:
        client.get("/auth/dev")
        page=client.get("/assistant")
        thread_id=page.text.split('data-thread="',1)[1].split('"',1)[0]
        response=client.post("/assistant/query",json={"thread_id":thread_id,"question":"What is in the welcome page?"})
        message_id=json.loads(response.text.strip().splitlines()[-1])["message_id"]
        approved=client.post(f"/assistant/messages/{message_id}/draft",follow_redirects=False)

    assert "AI Assistant" in page.text
    assert "Grounded answer [1]" in response.text
    assert '"type": "sources"' in response.text
    assert approved.status_code==303
    created=db.page("dev",int(approved.headers["location"].rsplit("/",1)[1]))
    assert created["status"]=="draft"
    assert created["markdown"]=="Grounded answer [1]"

def test_fastoffice_ticket_contract_and_replay_protection(monkeypatch):
    monkeypatch.setenv("FASTOFFICE_SSO_SECRET","shared-test-secret")
    from fastwiki import security
    security._seen.clear()
    payload={
        "sub":"1","email":"owner@example.com","name":"Owner",
        "org_id":"org-a","org_name":"Alpha","role":"owner",
        "aud":"wiki","exp":int(time.time())+60,"jti":"single-use-ticket",
    }
    encoded=base64.urlsafe_b64encode(
        json.dumps(payload,separators=(",",":")).encode()
    ).decode().rstrip("=")
    signature=hmac.new(
        b"shared-test-secret",encoded.encode(),hashlib.sha256
    ).hexdigest()
    ticket=f"{encoded}.{signature}"
    assert security.verify_suite_ticket(ticket)["email"]=="owner@example.com"
    assert security.verify_suite_ticket(ticket) is None
