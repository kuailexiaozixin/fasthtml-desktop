from __future__ import annotations
import json
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel
from . import db
from .security import api_authorized

api=FastAPI(title="FastWiki API",version="1.0.0",docs_url="/docs",redoc_url="/redoc")
class PageCreate(BaseModel):
    org_id:str; space_id:int; title:str; user_id:str
class PageSave(BaseModel):
    org_id:str; user_id:str; title:str; content_json:str; markdown:str=""; version:int
def auth(value): 
    if not api_authorized(value): raise HTTPException(401,"Valid bearer token required")
@api.get("/v1/health")
def health(): return {"status":"ok","product":"FastWiki"}
@api.get("/v1/spaces")
def list_spaces(org_id:str=Query(...),authorization:str|None=Header(None)):
    auth(authorization); return {"items":db.spaces(org_id)}
@api.get("/v1/pages")
def list_pages(org_id:str=Query(...),q:str="",authorization:str|None=Header(None)):
    auth(authorization); return {"items":db.search(org_id,q) if q else db.pages(org_id)}
@api.get("/v1/pages/{page_id}")
def get_page(page_id:int,org_id:str=Query(...),authorization:str|None=Header(None)):
    auth(authorization); found=db.page(org_id,page_id)
    if not found: raise HTTPException(404,"Page not found")
    return found
@api.post("/v1/pages",status_code=201)
def create_page(body:PageCreate,authorization:str|None=Header(None)):
    auth(authorization); who={"org_id":body.org_id,"sub":body.user_id}
    try: pid=db.create_page(who,body.space_id,body.title)
    except ValueError: raise HTTPException(404,"Space not found")
    return db.page(body.org_id,pid)
@api.put("/v1/pages/{page_id}")
def update_page(page_id:int,body:PageSave,authorization:str|None=Header(None)):
    auth(authorization); who={"org_id":body.org_id,"sub":body.user_id}
    try: result=db.save_page(who,page_id,body.title,body.content_json,body.markdown,body.version)
    except ValueError: raise HTTPException(422,"Invalid content JSON")
    if not result: raise HTTPException(404,"Page not found")
    if result.get("conflict"): raise HTTPException(409,"Page was updated elsewhere")
    return result
@api.get("/v1/search")
def search(org_id:str,q:str,authorization:str|None=Header(None)):
    auth(authorization); return {"items":db.search(org_id,q)}

