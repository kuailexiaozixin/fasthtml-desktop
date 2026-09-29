from __future__ import annotations
import json, mimetypes, os, re, secrets, uuid
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv
from fasthtml.common import *
from starlette.responses import JSONResponse, RedirectResponse, Response, StreamingResponse
load_dotenv()
from fastwiki import assistant, db, pdf, storage, views
from fastwiki.api import api
from fastwiki.security import verify_suite_ticket
from fastwiki.version import RELEASE_DATE, VERSION

app,rt=fast_app(secret_key=os.getenv("FASTWIKI_SECRET",secrets.token_hex(32)))
app.mount("/api",api)
def who(session):
    identity=session.get("identity")
    if identity:
        identity=assistant.configured_admin(identity);session["identity"]=identity
    return identity
def guard(session): return who(session) or RedirectResponse("/auth/suite",status_code=303)
@rt("/")
def get(session):
    identity=who(session)
    if not identity:return views.landing()
    pages=db.visible_pages(identity)
    return RedirectResponse(f"/pages/{pages[0]['id']}",status_code=303) if pages else RedirectResponse("/pages/new",status_code=303)
@rt("/health")
def get(): return JSONResponse({"status":"ok","product":"FastWiki","version":VERSION,"release_date":RELEASE_DATE,"storage":storage.backend()})
@rt("/favicon.ico")
def get():
    return Response('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="#4f46e5"/><path fill="white" d="M13 17h9l5 27 5-18 5 18 5-27h9l-10 31h-9l-5-16-5 16h-9Z"/></svg>',media_type="image/svg+xml")
@rt("/swagger.json")
def get(): return JSONResponse(api.openapi())
@rt("/openapi.json")
def get(): return JSONResponse(api.openapi())
@rt("/developers")
def get(): return RedirectResponse("/api/docs",status_code=307)
@rt("/auth/suite")
def get():
    return RedirectResponse(os.getenv("FASTOFFICE_URL","http://localhost:5020").rstrip("/")+"/launch/wiki",status_code=303)
@rt("/auth/suite/callback")
def get(session,ticket:str=""):
    identity=verify_suite_ticket(ticket)
    if not identity:return RedirectResponse("/?auth=invalid",status_code=303)
    db.provision(identity);session["identity"]={k:identity.get(k) for k in ("sub","email","name","org_id","org_name","role")}
    return RedirectResponse("/",status_code=303)
@rt("/auth/dev")
def get(session,email:str="kaljuvee@gmail.com"):
    if os.getenv("FASTWIKI_ENV","development")=="production":return RedirectResponse("/",status_code=303)
    identity={"sub":email,"email":email,"name":"Julian Kaljuvee","org_id":"dev","org_name":"FastSME","role":"owner"}
    db.provision(identity);session["identity"]=identity
    return RedirectResponse("/",status_code=303)
@rt("/logout")
def get(session):session.clear();return RedirectResponse("/",status_code=303)
@rt("/pages/{pid:int}")
def get(session,pid:int):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    current=db.visible_page(identity,pid)
    if not current or current["deleted_at"]:return Response("Page not found",status_code=404)
    return views.page_shell(identity,db.spaces(identity["org_id"]),db.visible_pages(identity),current,db.comments(identity["org_id"],pid),db.attachments(identity["org_id"],pid),db.embeds(identity["org_id"],pid),db.ancestors(identity,pid))
@rt("/pages/{pid:int}/pdf")
def get(session,pid:int):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    current=db.visible_page(identity,pid)
    if not current or current["deleted_at"]:return Response("Page not found",status_code=404)
    safe_name=re.sub(r"[^A-Za-z0-9._-]+","-",current["title"]).strip("-.") or "wiki-page"
    encoded_name=quote((current["title"] or "wiki-page")+".pdf")
    return Response(pdf.page_pdf(current),media_type="application/pdf",headers={"Content-Disposition":f"attachment; filename=\"{safe_name}.pdf\"; filename*=UTF-8''{encoded_name}"})
@rt("/pages/new")
def get(session):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    spaces=db.spaces(identity["org_id"])
    if not spaces:return RedirectResponse("/settings",status_code=303)
    pid=db.create_page(identity,spaces[0]["id"],"Untitled page")
    return RedirectResponse(f"/pages/{pid}",status_code=303)
@rt("/pages/{pid}/children")
def post(session,pid:int):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    parent=db.visible_page(identity,pid)
    if not parent or parent["deleted_at"]:return Response("Page not found",status_code=404)
    child_id=db.create_page(identity,parent["space_id"],"Untitled child page",parent_id=pid)
    return RedirectResponse(f"/pages/{child_id}",status_code=303)
@rt("/pages/{pid}/status")
def post(session,pid:int,status:str):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    try: changed=db.set_page_status(identity,pid,status)
    except ValueError:return Response("Invalid page status",status_code=422)
    if not changed:return Response("Page not found",status_code=404)
    return RedirectResponse(f"/pages/{pid}",status_code=303)
@rt("/pages/{pid}/save")
async def post(request,session,pid:int):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return JSONResponse({"error":"unauthorized"},status_code=401)
    body=await request.json()
    try: result=db.save_page(identity,pid,body.get("title","Untitled"),body.get("content_json","{}"),body.get("markdown",""),int(body.get("version",0)))
    except (ValueError,TypeError):return JSONResponse({"error":"invalid content"},status_code=422)
    if not result:return JSONResponse({"error":"not found"},status_code=404)
    if result.get("conflict"):return JSONResponse(result,status_code=409)
    return JSONResponse({"id":pid,"version":result["version"],"updated_at":result["updated_at"]})
@rt("/pages/{pid}/trash")
def post(session,pid:int):
    identity=guard(session)
    if not isinstance(identity,RedirectResponse):db.trash(identity,pid)
    return RedirectResponse("/",status_code=303)
@rt("/pages/{pid}/restore")
def post(session,pid:int):
    identity=guard(session)
    if not isinstance(identity,RedirectResponse):db.restore(identity,pid)
    return RedirectResponse(f"/pages/{pid}",status_code=303)
@rt("/pages/{pid}/comments")
def post(session,pid:int,body:str,kind:str="page",parent_id:int=0):
    identity=guard(session)
    if not isinstance(identity,RedirectResponse):
        try:db.add_comment(identity,pid,body,kind,parent_id=parent_id or None)
        except ValueError:pass
    return RedirectResponse(f"/pages/{pid}#comments",status_code=303)
@rt("/pages/{pid}/embeds")
def post(session,pid:int,product:str,title:str,url:str):
    identity=guard(session)
    if not isinstance(identity,RedirectResponse):db.add_embed(identity,pid,product,title,url)
    return RedirectResponse(f"/pages/{pid}",status_code=303)
@rt("/pages/{pid}/attachments")
async def post(request,session,pid:int):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    form=await request.form(); upload=form.get("file")
    if not upload:return RedirectResponse(f"/pages/{pid}",status_code=303)
    body=await upload.read();limit=int(os.getenv("FASTWIKI_MAX_UPLOAD_MB","20"))*1024*1024
    if len(body)>limit:return Response("File too large",status_code=413)
    safe=Path(upload.filename or "attachment").name.replace(" ","-")
    key=f"{identity['org_id']}/{pid}/{uuid.uuid4().hex}-{safe}"
    storage.put(key,body,upload.content_type or "application/octet-stream")
    db.add_attachment(identity,pid,safe,key,upload.content_type or "application/octet-stream",len(body))
    return RedirectResponse(f"/pages/{pid}",status_code=303)
@rt("/attachments/{aid}")
def get(session,aid:int):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    item=db.visible_attachment(identity,aid)
    if not item:return Response("Not found",status_code=404)
    return Response(storage.get(item["storage_key"]),media_type=item["content_type"],headers={"Content-Disposition":f'inline; filename="{item["name"]}"'})
@rt("/search")
def get(session,q:str=""):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    items=[item for item in db.search(identity["org_id"],q) if db.can_view(identity,db.page(identity["org_id"],item["id"]))] if q else []
    return views.list_page(identity,db.spaces(identity["org_id"]),db.visible_pages(identity),"Search",items)
@rt("/assistant")
def get(session,thread:str=""):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    threads=db.assistant_threads(identity)
    current=db.assistant_thread(identity,thread) if thread else (threads[0] if threads else None)
    if not current:
        thread_id=uuid.uuid4().hex;db.create_assistant_thread(identity,thread_id);current=db.assistant_thread(identity,thread_id);threads=db.assistant_threads(identity)
    return views.assistant_shell(identity,threads,current,db.assistant_messages(identity,current["id"]),assistant.source_pages(identity,""),assistant.remaining_queries(identity))
@rt("/assistant/threads")
def post(session):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    thread_id=uuid.uuid4().hex;db.create_assistant_thread(identity,thread_id)
    return RedirectResponse(f"/assistant?thread={thread_id}",status_code=303)
@rt("/assistant/query")
async def post(request,session):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return JSONResponse({"error":"unauthorized"},status_code=401)
    body=await request.json();thread_id=str(body.get("thread_id","")).strip();question=str(body.get("question","")).strip()
    if not question:return JSONResponse({"error":"Ask a question first."},status_code=422)
    if not db.assistant_thread(identity,thread_id):return JSONResponse({"error":"Conversation not found."},status_code=404)
    remaining=assistant.remaining_queries(identity)
    if remaining==0:return JSONResponse({"error":"Daily query limit reached. Try again tomorrow."},status_code=429)
    history=db.assistant_messages(identity,thread_id);sources=assistant.source_pages(identity,question)
    db.add_assistant_message(identity,thread_id,"user",question);db.record_assistant_query(identity)
    def events():
        yield json.dumps({"type":"sources","items":sources})+"\n";answer=[]
        try:
            for token in assistant.stream_answer(identity,question,history,sources):
                answer.append(token);yield json.dumps({"type":"token","content":token})+"\n"
            content="".join(answer).strip() or "I could not find an answer in the available pages."
            message_id=db.add_assistant_message(identity,thread_id,"assistant",content)
            yield json.dumps({"type":"done","remaining":assistant.remaining_queries(identity),"message_id":message_id})+"\n"
        except Exception:
            yield json.dumps({"type":"error","error":"The AI assistant is temporarily unavailable."})+"\n"
    return StreamingResponse(events(),media_type="application/x-ndjson")
@rt("/assistant/messages/{message_id}/draft")
def post(session,message_id:int):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    message=db.assistant_message(identity,message_id)
    if not message or message["role"]!="assistant":return Response("Assistant answer not found",status_code=404)
    spaces=db.spaces(identity["org_id"])
    if not spaces:return RedirectResponse("/settings",status_code=303)
    title=("Draft: "+message["thread_title"])[:120]
    page_id=db.create_page(identity,spaces[0]["id"],title)
    content=json.dumps({"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":message["content"]}]}]})
    db.save_page(identity,page_id,title,content,message["content"],1)
    return RedirectResponse(f"/pages/{page_id}",status_code=303)
@rt("/trash")
def get(session):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    deleted=[p for p in db.visible_pages(identity,True) if p["deleted_at"]]
    return views.list_page(identity,db.spaces(identity["org_id"]),db.visible_pages(identity),"Trash",deleted)
@rt("/settings")
def get(session):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    return Html(views.head("Workspace settings · FastWiki"),Body(Div(H1("Workspace settings"),P("Create spaces and choose how your team can discuss pages."),Form(Input(name="name",placeholder="Space name",required=True),Input(name="description",placeholder="Description"),Select(Option("Organisation",value="org"),Option("Private",value="private"),name="visibility"),Select(Option("Page and inline",value="both"),Option("Page only",value="page"),Option("Inline only",value="inline"),Option("Off",value="off"),name="comments_mode"),Button("Create space",cls="btn"),method="post",action="/spaces",cls="smallform"),A("Back to wiki",href="/",cls="btn ghost"),cls="cardlist")))
@rt("/spaces")
def post(session,name:str,description:str="",visibility:str="org",comments_mode:str="both"):
    identity=guard(session)
    if not isinstance(identity,RedirectResponse):db.create_space(identity,name,description,visibility,comments_mode)
    return RedirectResponse("/",status_code=303)
if __name__=="__main__":serve(port=int(os.getenv("FASTWIKI_PORT","5022")))
