from __future__ import annotations
import html, json
from datetime import datetime
from fasthtml.common import *
from .version import RELEASE_DATE, VERSION
from urllib.parse import quote

ACCENT="#4f46e5"; TINT="#eef2ff"
FAVICON="data:image/svg+xml,"+quote('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="#4f46e5"/><path fill="white" d="M13 17h9l5 27 5-18 5 18 5-27h9l-10 31h-9l-5-16-5 16h-9Z"/></svg>',safe="")
PARTNERS=(
    ("SAASPASS","https://saaspass.com/","https://saaspass.com/_next/static/assets/0176aeff921f6359fee88e796be31ace.png","Full-stack identity and access management spanning MFA, SSO, passwordless access and integration APIs."),
    ("Sixty Four","https://sixtyfour.ee/","https://sixtyfour.ee/favicon.ico","A senior Tallinn technology studio delivering software, AI consultancy, service design and public-sector programmes."),
    ("EDI Labs","https://edilabs.tech/","https://edilabs.tech/static/favicon.svg","AI and data engineering for document intelligence, forecasting, geospatial systems and agentic workflows."),
    ("Predictive Labs","https://predictivelabs.ai/","https://predictivelabs.ai/static/favicon.svg","Auditable AI systems for health, defence, public management, mobility and financial services."),
    ("Consistente","https://consistente.tech/","https://consistente.tech/static/favicon.svg","Enterprise AI delivery across financial services, healthcare, the public sector and technology."),
    ("Manmouna Technologies","https://manmouna.tech/","data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%230B1E14'/%3E%3Cpath d='M32 12 52 32 32 52 12 32Z' fill='%2334D399'/%3E%3Cpath d='M32 22 42 32 32 42 22 32Z' fill='%230B1E14'/%3E%3C/svg%3E","Auditable-by-design AI systems for European public services across health, defence, public management and mobility."),
)
BASE_CSS=r"""
:root{--accent:#4f46e5;--tint:#eef2ff;--ink:#172033;--muted:#667085;--line:#e5e7eb;--panel:#f8fafc}
*{box-sizing:border-box}body{margin:0;color:var(--ink);background:#fff;font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}a{color:inherit}
.nav{height:68px;display:flex;align-items:center;justify-content:space-between;max-width:1200px;margin:auto;padding:0 24px}.brand{display:flex;align-items:center;gap:10px;text-decoration:none;font-weight:800}.mark{width:34px;height:34px;background:var(--accent);color:#fff;border-radius:10px;display:grid;place-items:center}.navlinks{display:flex;gap:18px;align-items:center}.btn{display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:10px;background:var(--accent);color:#fff;padding:11px 17px;font-weight:700;text-decoration:none;cursor:pointer}.btn.ghost{background:#fff;color:var(--ink);border:1px solid var(--line)}
.hero{max-width:1200px;margin:auto;padding:95px 24px 70px;display:grid;grid-template-columns:1.05fr .95fr;gap:68px;align-items:center}.eyebrow{color:var(--accent);font-weight:800;font-size:12px;letter-spacing:.17em;text-transform:uppercase}.hero h1{font-size:clamp(48px,6vw,76px);line-height:1.02;letter-spacing:-.055em;margin:18px 0}.hero p{font-size:20px;line-height:1.6;color:var(--muted)}.actions{display:flex;gap:12px;margin-top:28px}.mock{border:1px solid var(--line);border-radius:22px;padding:12px;background:#fff;box-shadow:0 30px 80px #312e8130}.mockin{height:430px;border-radius:14px;background:linear-gradient(135deg,#eef2ff,#fff);display:grid;grid-template-columns:150px 1fr}.mockside{padding:24px 15px;background:#f8fafc;border-radius:14px 0 0 14px}.mockline{height:10px;border-radius:99px;background:#dbe1ea;margin:14px 0}.mockpage{padding:48px 40px}.mockpage h3{font-size:30px;margin:0 0 24px}.mockpara{height:10px;background:#dbe1ea;border-radius:99px;margin:14px 0}.features{background:var(--panel);padding:82px 24px}.featuregrid{max-width:1200px;margin:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.feature{background:#fff;border:1px solid var(--line);border-radius:18px;padding:26px}.feature b{color:var(--accent)}.feature h2{font-size:20px}.feature p{color:var(--muted);line-height:1.6}.footer{max-width:1200px;margin:auto;padding:36px 24px;color:var(--muted);display:flex;justify-content:space-between}
.pricing{max-width:1200px;margin:auto;padding:82px 24px;scroll-margin-top:80px}.pricing h2{font-size:34px;margin:10px 0}.pricing>p{max-width:720px;color:var(--muted);line-height:1.65}.pricinggrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:30px}.pricingcard{border:1px solid var(--line);border-radius:17px;padding:22px}.pricingprice{font-size:36px;font-weight:800;margin:10px 0}.pricingcard p:last-child{color:var(--muted);line-height:1.55}@media(max-width:900px){.pricinggrid{grid-template-columns:1fr}}
.partners{max-width:1200px;margin:auto;padding:82px 24px;scroll-margin-top:80px}.partners h2{font-size:34px;margin:10px 0}.partners>p{max-width:720px;color:var(--muted);line-height:1.65}.partnergrid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:30px}.partner{min-width:0;border:1px solid var(--line);border-radius:17px;padding:18px;text-decoration:none}.partner img{width:44px;height:44px;object-fit:contain}.partner small{display:block;margin-top:14px;color:var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.08em}.partner h3{margin:7px 0}.partner p{font-size:12px;line-height:1.55;color:var(--muted)}
.shell{display:grid;grid-template-columns:260px minmax(0,1fr);height:100vh}.sidebar{background:#f8fafc;border-right:1px solid var(--line);padding:18px;overflow:auto}.sidehead{display:flex;align-items:center;justify-content:space-between;margin-bottom:22px}.user{font-size:12px;color:var(--muted);padding:11px 0;border-bottom:1px solid var(--line);margin-bottom:12px}.sideitem{display:block;text-decoration:none;padding:8px 10px;border-radius:8px;font-size:14px}.sideitem:hover,.sideitem.active{background:#e9eafc;color:var(--accent)}.treechild{padding-left:18px}.workspace{overflow:auto}.topbar{height:58px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px;padding:0 22px;position:sticky;top:0;background:#fffc;backdrop-filter:blur(10px);z-index:3}.search{border:1px solid var(--line);border-radius:9px;padding:9px 12px;min-width:260px}.editorwrap{max-width:880px;margin:auto;padding:54px 58px 70px}.titleinput{border:0;width:100%;font-size:42px;font-weight:800;letter-spacing:-.04em;outline:0;color:var(--ink)}.toolbar{display:flex;gap:4px;flex-wrap:wrap;margin:25px 0 16px;padding:7px;border:1px solid var(--line);border-radius:11px;position:sticky;top:68px;background:#fff;z-index:2}.tool{border:0;background:#fff;border-radius:6px;padding:7px 9px;cursor:pointer}.tool:hover{background:var(--tint)}.tool.mode{border:1px solid var(--line);font-weight:700}.tool.mode.active{background:var(--accent);border-color:var(--accent);color:#fff}.toolbar-spacer{flex:1}.editor{min-height:430px;outline:0;font-size:17px;line-height:1.72}.editor h1,.editor h2,.editor h3{line-height:1.2}.editor img{max-width:100%}.editor table{border-collapse:collapse}.editor td,.editor th{border:1px solid var(--line);padding:7px}.ProseMirror:focus{outline:0}.status{font-size:12px;color:var(--muted);margin-left:auto}.panel h3{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}.bottom-bar{border-top:1px solid var(--line);background:var(--panel);padding:32px clamp(24px,5vw,70px) 70px;display:grid;grid-template-columns:minmax(320px,1.5fr) minmax(220px,.75fr) minmax(260px,1fr);gap:28px;align-items:start}.bottom-bar .panel{min-width:0}.comment-list{margin-top:18px}.comment{border:1px solid var(--line);border-radius:10px;padding:12px;margin:9px 0;background:#fff}.comment .comment{margin-left:22px;border-left:3px solid #c7d2fe}.commenthead{display:flex;align-items:center;justify-content:space-between;gap:12px}.commenthead small,.publication-meta{font-size:11px;color:var(--muted)}.comment p{margin:7px 0;font-size:14px;white-space:pre-wrap}.replybox{margin-top:8px}.replybox summary{cursor:pointer;color:var(--accent);font-size:12px;font-weight:700}.replybox .smallform{margin-top:8px}.smallform{display:grid;gap:8px}.smallform input,.smallform textarea,.smallform select{width:100%;border:1px solid var(--line);border-radius:8px;padding:9px}.smallbtn{border:0;background:var(--accent);color:#fff;border-radius:8px;padding:8px 11px;font-weight:700;cursor:pointer}.cardlist{max-width:960px;margin:50px auto;padding:0 30px}.result{display:block;border-bottom:1px solid var(--line);padding:18px 4px;text-decoration:none}.result p{color:var(--muted)}.empty{padding:24px;color:var(--muted)}
.block-editor{min-height:430px}.block-actions{margin-bottom:10px}.block-list{display:flex;flex-direction:column;gap:7px}.block-row{display:grid;grid-template-columns:auto 122px minmax(0,1fr) auto;gap:8px;align-items:start;padding:7px;border:1px solid transparent;border-radius:10px}.block-row:hover{border-color:var(--line);background:#f8fafc}.block-format{display:flex;gap:2px;padding-top:4px}.block-format button{width:25px;height:25px;border:1px solid var(--line);border-radius:5px;background:#fff;cursor:pointer;font-size:11px}.block-format button:hover{background:var(--tint);color:var(--accent)}.block-type{width:100%;border:1px solid var(--line);border-radius:7px;background:#fff;padding:7px;font:inherit;font-size:12px}.block-body{min-width:0}.block-edit,.block-raw{width:100%;min-height:42px;border:1px solid var(--line);border-radius:8px;background:#fff;padding:8px 10px;font:inherit;line-height:1.5;outline:0}.block-edit:focus,.block-raw:focus{border-color:var(--accent);box-shadow:0 0 0 2px #4f46e520}.block-edit.heading1{font-size:28px;font-weight:800}.block-edit.heading2{font-size:22px;font-weight:750}.block-edit.heading3{font-size:18px;font-weight:700}.block-edit.quote{border-left:4px solid var(--accent);color:var(--muted);font-style:italic}.block-edit.bullet>div{display:list-item;list-style:disc;margin-left:20px}.block-edit.numbered{counter-reset:item}.block-edit.numbered>div{counter-increment:item;margin-left:24px;position:relative}.block-edit.numbered>div:before{content:counter(item) ".";position:absolute;left:-22px;color:var(--muted)}.block-raw{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;resize:vertical}.block-controls{display:flex;gap:2px}.block-control{border:0;background:transparent;color:var(--muted);border-radius:5px;padding:5px;cursor:pointer}.block-control:hover{background:var(--tint);color:var(--accent)}.block-table{border-collapse:collapse;width:100%;font-size:13px}.block-table td,.block-table th{border:1px solid var(--line);padding:7px;min-width:75px}.block-table th{background:var(--tint)}.block-table-tools{display:flex;gap:5px;margin-top:5px}.markdown-editor{width:100%;min-height:430px;border:1px solid var(--line);border-radius:10px;padding:14px;font:14px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;resize:vertical;outline:0}.markdown-editor:focus{border-color:var(--accent);box-shadow:0 0 0 2px #4f46e520}
.treeitem{display:flex;align-items:center;gap:6px;min-width:0}.treeitem a{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.treebadge,.pagebadge{border-radius:99px;background:#fff7ed;color:#9a3412;font-size:10px;font-weight:800;padding:2px 6px;text-transform:uppercase}.pagebadge.published{background:#ecfdf3;color:#027a48}.breadcrumbs{display:flex;gap:7px;align-items:center;flex-wrap:wrap;color:var(--muted);font-size:12px;margin-bottom:15px}.breadcrumbs a{text-decoration:none}.inlineform{display:inline-flex;margin:0}.topbar .status{margin-left:auto}.pageactions{display:flex;gap:8px;align-items:center}.release{display:block;padding:12px 10px 0;color:var(--muted);font-size:10px}
.assistant-shell{display:grid;grid-template-columns:260px minmax(0,1fr) 340px;height:100vh;background:var(--panel)}.assistant-left,.assistant-context{background:#fff;padding:18px;overflow:auto}.assistant-left{border-right:1px solid var(--line);display:flex;flex-direction:column}.assistant-context{border-left:1px solid var(--line)}.assistant-center{display:flex;flex-direction:column;min-width:0;overflow:hidden}.assistant-header{height:64px;background:#fff;border-bottom:1px solid var(--line);padding:0 22px;display:flex;align-items:center;justify-content:space-between}.assistant-messages{flex:1;overflow:auto;padding:32px max(24px,8vw)}.message{max-width:760px;border:1px solid var(--line);border-radius:15px;padding:14px 16px;margin:0 0 14px;white-space:pre-wrap;line-height:1.6;background:#fff}.message.user{margin-left:auto;background:var(--accent);border-color:var(--accent);color:#fff}.assistant-form{display:flex;gap:10px;padding:16px max(24px,8vw) 22px;border-top:1px solid var(--line);background:#fff}.assistant-form textarea{flex:1;resize:none;border:1px solid var(--line);border-radius:12px;padding:12px;font:inherit;min-height:50px}.assistant-form textarea:focus{outline:2px solid #4f46e530;border-color:var(--accent)}.conversation-list{margin-top:20px}.conversation-list h3,.assistant-context h3{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}.sourcecard{display:block;border:1px solid var(--line);border-radius:12px;padding:12px;margin:9px 0;text-decoration:none}.sourcecard b{display:block}.sourcecard p{font-size:12px;line-height:1.45;color:var(--muted);margin:7px 0}.usage{font-size:12px;color:var(--muted)}.assistant-empty{max-width:600px;margin:16vh auto;text-align:center;color:var(--muted)}
@media(max-width:1050px){.bottom-bar{grid-template-columns:1fr 1fr}.bottom-bar .panel:first-child{grid-column:1/-1}}
@media(max-width:900px){.hero{grid-template-columns:1fr}.mock{display:none}.featuregrid,.partnergrid{grid-template-columns:1fr}.shell{grid-template-columns:210px 1fr}.editorwrap{padding:35px 26px}.titleinput{font-size:34px}.assistant-shell{grid-template-columns:210px 1fr}.assistant-context{display:none}}
@media(max-width:650px){.shell,.assistant-shell{grid-template-columns:1fr}.sidebar,.assistant-left{display:none}.topbar{padding:0 12px}.search{min-width:0;width:100%}}
@media(max-width:600px){.bottom-bar{grid-template-columns:1fr;padding:28px 20px 50px}.bottom-bar .panel:first-child{grid-column:auto}.comment .comment{margin-left:10px}.block-row{grid-template-columns:1fr}.block-controls{justify-content:flex-end}}
"""

def head(title):
    return Head(Title(title),Meta(charset="utf-8"),Meta(name="viewport",content="width=device-width,initial-scale=1"),Meta(name="description",content="Open-source knowledge that works with your whole office suite."),Link(rel="icon",type="image/svg+xml",href=FAVICON),Link(rel="preconnect",href="https://fonts.googleapis.com"),Link(rel="stylesheet",href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"),Style(BASE_CSS))


def pricing_section():
    return Section(Span("Pricing",cls="eyebrow"),H2("Simple pricing for every FastSME product."),P("Every Fast* product uses the same two options: bring your own cloud for free, or host with us for €1 per month."),Div(Article(Span("BYOC",cls="eyebrow"),H3("Bring Your Own Cloud"),P("Free",cls="pricingprice"),P("Self-host on your own infrastructure or cloud. Full control of data and upgrades. No per-seat platform fee."),cls="pricingcard"),Article(Span("Hosted",cls="eyebrow"),H3("Host with us"),P("€1 / month",cls="pricingprice"),P("We run the product for you on FastSME-managed infrastructure. €1 per product per month."),cls="pricingcard"),cls="pricinggrid"),id="pricing",cls="pricing")

def partner_section():
    return Section(Span("Partners",cls="eyebrow"),H2("Connect with trusted integration specialists."),P("Identity, software delivery, data engineering and applied-AI expertise for FastSME implementations."),Div(*[A(Img(src=logo,alt=f"{name} logo",loading="lazy"),Small("Integration Partner"),H3(name),P(description),href=url,target="_blank",rel="noopener noreferrer",cls="partner") for name,url,logo,description in PARTNERS],cls="partnergrid"),id="partners",cls="partners")

def landing():
    return Html(head("FastWiki · Knowledge without lock-in"),Body(
        Nav(A(Span("W",cls="mark"),"FastWiki",href="/",cls="brand"),Div(A("Pricing",href="#pricing"),A("Partners",href="#partners"),A("Developers",href="/developers"),A("Sign In",href="/auth/suite",cls="btn ghost"),cls="navlinks"),cls="nav"),
        Main(Section(Div(Span("Open knowledge for independent teams",cls="eyebrow"),H1("Turn what your team knows into momentum."),P("A calm, connected workspace for handbooks, processes, project knowledge and decisions—open source, portable, and built for SMEs."),Div(A("Sign in to your workspace",href="/auth/suite",cls="btn"),A("Explore the API",href="/developers",cls="btn ghost"),cls="actions")),Div(Div(Div(Span("Spaces"),*[Div(cls="mockline") for _ in range(6)],cls="mockside"),Div(H3("Product launch playbook"),*[Div(cls="mockpara",style=f"width:{w}%") for w in (96,82,91,68,88,54)],cls="mockpage"),cls="mockin"),cls="mock"),cls="hero"),
        Section(Div(*[Article(B(f"0{i}"),H2(t),P(d),cls="feature") for i,(t,d) in enumerate([
            ("Write beautifully","Tiptap-powered rich editing with a portable JSON source and optional Markdown view."),
            ("Connect the work","Embed FastDocs, FastSheets, FastSlides, FastDrive and the rest of FastOffice."),
            ("Keep control","Organisation-scoped spaces, roles, recoverable trash and self-hosted or cloud storage."),
            ("Find the answer","Search titles and page content across every space in your organisation."),
            ("Discuss in context","Page and inline comments can be enabled independently for each space."),
            ("Build on it","Tenant-safe FastAPI endpoints, OpenAPI and Swagger schemas included.")
        ],1)],cls="featuregrid"),cls="features")),pricing_section(),partner_section(),
        Footer(Span("FastWiki is part of the open-source FastOffice suite."),A("Discover freedom with open source →",href="https://office.fastsme.com"),cls="footer")))

def _tree(pages,parent_id,active,depth=0,seen=None):
    seen=set() if seen is None else seen
    items=[]
    for page in sorted((p for p in pages if p.get("parent_id")==parent_id and p["id"] not in seen),key=lambda p:p["title"].lower()):
        seen.add(page["id"])
        badge=Span("Draft",cls="treebadge") if page.get("status")=="draft" else None
        items.append(Div(A(("▾ " if any(p.get("parent_id")==page["id"] for p in pages) else "▱ ")+page["title"],href=f"/pages/{page['id']}",cls="sideitem"+(" active" if page["id"]==active else "")),badge,cls="treeitem",style=f"padding-left:{10+depth*15}px"))
        items.extend(_tree(pages,page["id"],active,depth+1,seen))
    return items

def sidebar(who, spaces, pages, active=None):
    items=[]
    for space in spaces:
        space_pages=[p for p in pages if p["space_id"]==space["id"]]
        ids={p["id"] for p in space_pages}
        normalized=[{**p,"parent_id":p.get("parent_id") if p.get("parent_id") in ids else None} for p in space_pages]
        tree=_tree(normalized,None,active)
        items.extend([Div(B(space["name"]),cls="sideitem"),*tree])
    return Aside(Div(A(Span("W",cls="mark"),"FastWiki",href="/",cls="brand"),A("＋",href="/pages/new",title="New page"),cls="sidehead"),Div(f"{who['name']} · {who['role']}",cls="user"),A("✦ AI Assistant",href="/assistant",cls="sideitem"),*items,A("⚙ Workspace",href="/settings",cls="sideitem"),A("♻ Trash",href="/trash",cls="sideitem"),A("Sign out",href="/logout",cls="sideitem"),Span(f"v{VERSION} · {RELEASE_DATE}",cls="release"),cls="sidebar")

EDITOR_JS=r"""
import { Editor } from 'https://esm.sh/@tiptap/core@3.6.6';
import StarterKit from 'https://esm.sh/@tiptap/starter-kit@3.6.6';
import Underline from 'https://esm.sh/@tiptap/extension-underline@3.6.6';
import Link from 'https://esm.sh/@tiptap/extension-link@3.6.6';
import Image from 'https://esm.sh/@tiptap/extension-image@3.6.6';
import { Table } from 'https://esm.sh/@tiptap/extension-table@3.6.6';
import { TableRow } from 'https://esm.sh/@tiptap/extension-table-row@3.6.6';
import { TableCell } from 'https://esm.sh/@tiptap/extension-table-cell@3.6.6';
import { TableHeader } from 'https://esm.sh/@tiptap/extension-table-header@3.6.6';
const el=document.querySelector('#editor');
const blockEditor=document.querySelector('#block-editor');
const blockList=document.querySelector('#block-list');
const markdown=document.querySelector('#markdown');
const status=document.querySelector('#save-status');
const content=JSON.parse(document.querySelector('#initial-content').textContent);
let switching=false;
const state={mode:'rich',doc:content};
const editor=new Editor({element:el,extensions:[StarterKit.configure({underline:false,link:false}),Underline,Link.configure({openOnClick:false}),Image,Table.configure({resizable:true}),TableRow,TableCell,TableHeader],content,onUpdate:()=>{if(!switching)queueSave()}});
window.editor=editor;
document.querySelectorAll('[data-cmd]').forEach(b=>b.onclick=()=>{const c=editor.chain().focus(); const cmd=b.dataset.cmd;
 if(cmd==='bold')c.toggleBold().run(); if(cmd==='italic')c.toggleItalic().run(); if(cmd==='underline')c.toggleUnderline().run(); if(cmd==='h2')c.toggleHeading({level:2}).run(); if(cmd==='bullet')c.toggleBulletList().run(); if(cmd==='ordered')c.toggleOrderedList().run(); if(cmd==='quote')c.toggleBlockquote().run(); if(cmd==='code')c.toggleCodeBlock().run(); if(cmd==='table')c.insertTable({rows:3,cols:3,withHeaderRow:true}).run();});
let timer,version=Number(document.body.dataset.version);
const title=document.querySelector('#page-title'); title.addEventListener('input',queueSave);
function queueSave(){status.textContent='Unsaved changes';clearTimeout(timer);timer=setTimeout(save,700)}

const TYPES=[['paragraph','Paragraph'],['heading1','Heading 1'],['heading2','Heading 2'],['heading3','Heading 3'],['bullet','Bulleted list'],['numbered','Numbered list'],['quote','Quote'],['code','Code'],['table','Table'],['divider','Divider'],['raw','Raw JSON']];
function make(tag,cls,text){const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node}
function escapeHtml(value){return String(value||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function inlineHtml(nodes){return (nodes||[]).map(node=>{
 if(node.type==='hardBreak')return '<br>';
 if(node.type!=='text')return inlineHtml(node.content);
 let value=escapeHtml(node.text);
 (node.marks||[]).forEach(mark=>{if(mark.type==='bold')value='<strong>'+value+'</strong>';if(mark.type==='italic')value='<em>'+value+'</em>';if(mark.type==='underline')value='<u>'+value+'</u>';if(mark.type==='strike')value='<s>'+value+'</s>';if(mark.type==='code')value='<code>'+value+'</code>';if(mark.type==='link'){const href=escapeHtml((mark.attrs||{}).href||'');value='<a href="'+href+'">'+value+'</a>'}});
 return value;
}).join('')}
function domInline(root){
 const out=[];
 function visit(node,marks){
  if(node.nodeType===Node.TEXT_NODE){if(node.nodeValue)out.push({type:'text',text:node.nodeValue,...(marks.length?{marks}: {})});return}
  if(node.nodeType!==Node.ELEMENT_NODE)return;
  if(node.tagName==='BR'){out.push({type:'hardBreak'});return}
  const next=marks.slice(),tag=node.tagName;
  if(tag==='STRONG'||tag==='B')next.push({type:'bold'});if(tag==='EM'||tag==='I')next.push({type:'italic'});if(tag==='U')next.push({type:'underline'});if(tag==='S'||tag==='STRIKE')next.push({type:'strike'});if(tag==='CODE')next.push({type:'code'});if(tag==='A')next.push({type:'link',attrs:{href:node.getAttribute('href')||''}});
  node.childNodes.forEach(child=>visit(child,next));
 }
 root.childNodes.forEach(node=>visit(node,[]));
 return out.filter(node=>node.type!=='text'||node.text.length)
}
function textContent(node){if(node.type==='text')return node.text||'';if(node.type==='hardBreak')return '\n';return (node.content||[]).map(textContent).join('')}
function nodeBlock(node){
 if(node.type==='heading')return {type:'heading'+Math.min(3,Math.max(1,Number((node.attrs||{}).level||2))),node};
 if(node.type==='bulletList')return {type:'bullet',node};if(node.type==='orderedList')return {type:'numbered',node};if(node.type==='blockquote')return {type:'quote',node};if(node.type==='codeBlock')return {type:'code',node};if(node.type==='table')return {type:'table',node};if(node.type==='horizontalRule')return {type:'divider',node};if(node.type==='paragraph')return {type:'paragraph',node};
 return {type:'raw',node};
}
function blockControls(row){
 const controls=make('div','block-controls');
 [['↑','Move up',()=>{const previous=row.previousElementSibling;if(previous)blockList.insertBefore(row,previous)}],['↓','Move down',()=>{const next=row.nextElementSibling;if(next)blockList.insertBefore(next,row)}],['＋','Add block below',()=>{const added=renderBlock({type:'paragraph',node:{type:'paragraph'}});blockList.insertBefore(added,row.nextElementSibling);added.querySelector('.block-edit').focus()}],['✕','Delete block',()=>{if(blockList.children.length>1)row.remove()}]].forEach(([label,hint,action])=>{const button=make('button','block-control',label);button.type='button';button.title=hint;button.onclick=()=>{action();queueSave()};controls.appendChild(button)});
 return controls;
}
function blockFormat(row){
 const toolbar=make('div','block-format');
 [['B','bold','Bold'],['I','italic','Italic'],['U','underline','Underline'],['</>','code','Inline code']].forEach(([label,command,hint])=>{const button=make('button','',label);button.type='button';button.title=hint;button.onmousedown=event=>{const edit=row.querySelector('.block-edit'),selection=window.getSelection();button._range=selection?.rangeCount&&edit?.contains(selection.anchorNode)?selection.getRangeAt(0).cloneRange():null;event.preventDefault()};button.onclick=()=>{const edit=row.querySelector('.block-edit');if(!edit)return;const selection=window.getSelection();if(button._range){selection.removeAllRanges();selection.addRange(button._range)}else edit.focus();if(command==='code'){const selected=button._range?selection.toString():'code';document.execCommand('insertHTML',false,'<code>'+escapeHtml(selected||'code')+'</code>')}else document.execCommand(command,false,null);button._range=null;queueSave()};toolbar.appendChild(button)});
 return toolbar;
}
function tableEditor(node){
 const wrap=make('div');const table=make('table','block-table');
 const sourceRows=(node.content||[]).length?node.content:[{type:'tableRow',content:[{type:'tableHeader',content:[{type:'paragraph'}]}]},{type:'tableRow',content:[{type:'tableCell',content:[{type:'paragraph'}]}]}];
 sourceRows.forEach(sourceRow=>{const tr=make('tr');(sourceRow.content||[]).forEach(cell=>{const td=make(cell.type==='tableHeader'?'th':'td');td.contentEditable='true';td.dataset.cellType=cell.type||'tableCell';td.innerHTML=inlineHtml(((cell.content||[])[0]||{}).content)||'<br>';tr.appendChild(td)});table.appendChild(tr)});wrap.appendChild(table);
 const tools=make('div','block-table-tools');
 function button(label,action){const item=make('button','block-control',label);item.type='button';item.onclick=()=>{action();queueSave()};tools.appendChild(item)}
 button('＋ Row',()=>{const columns=table.rows[0]?.cells.length||1;const tr=make('tr');for(let i=0;i<columns;i++){const td=make('td');td.contentEditable='true';td.dataset.cellType='tableCell';td.innerHTML='<br>';tr.appendChild(td)}table.appendChild(tr)});
 button('＋ Column',()=>Array.from(table.rows).forEach((tr,index)=>{const cell=make(index===0?'th':'td');cell.contentEditable='true';cell.dataset.cellType=index===0?'tableHeader':'tableCell';cell.innerHTML='<br>';tr.appendChild(cell)}));
 button('－ Row',()=>{if(table.rows.length>1)table.deleteRow(-1)});wrap.appendChild(tools);return wrap;
}
function fillBlock(row,block){
 const body=row.querySelector('.block-body');body.replaceChildren();row.dataset.type=block.type;row.querySelector('.block-type').value=block.type;row.querySelector('.block-format').hidden=['code','raw','table','divider'].includes(block.type);
 if(block.type==='divider'){body.appendChild(document.createElement('hr'));return}
 if(block.type==='table'){body.appendChild(tableEditor(block.node||{}));return}
 if(block.type==='code'||block.type==='raw'){const raw=make('textarea','block-raw');raw.rows=block.type==='code'?5:8;raw.value=block.type==='raw'?JSON.stringify(block.node||{type:'paragraph'},null,2):textContent(block.node||{});body.appendChild(raw);return}
 const edit=make('div','block-edit '+block.type);edit.contentEditable='true';
 if(block.type==='bullet'||block.type==='numbered'){
  const items=(block.node?.content||[]);(items.length?items:[{content:[{type:'paragraph'}]}]).forEach(item=>{const line=make('div');const paragraph=(item.content||[]).find(child=>child.type==='paragraph')||{};line.innerHTML=inlineHtml(paragraph.content)||'<br>';edit.appendChild(line)});
 }else if(block.type==='quote'){
  const paragraph=(block.node?.content||[]).find(child=>child.type==='paragraph')||{};edit.innerHTML=inlineHtml(paragraph.content)||'<br>';
 }else edit.innerHTML=inlineHtml(block.node?.content)||'<br>';
 body.appendChild(edit);
}
function renderBlock(block){
 const row=make('div','block-row');const select=make('select','block-type');TYPES.forEach(([value,label])=>{const option=make('option','',label);option.value=value;select.appendChild(option)});const body=make('div','block-body');row.append(blockFormat(row),select,body,blockControls(row));fillBlock(row,block);
 select.onchange=()=>{const value=rowText(row);fillBlock(row,{type:select.value,node:valueNode(select.value,value)});queueSave()};return row;
}
function rowText(row){const edit=row.querySelector('.block-edit');const raw=row.querySelector('.block-raw');return raw?raw.value:(edit?edit.innerText:'')}
function valueNode(type,value){const inline=value?[{type:'text',text:value}]:undefined;if(type.startsWith('heading'))return {type:'heading',attrs:{level:Number(type.slice(-1))},...(inline?{content:inline}:{})};if(type==='quote')return {type:'blockquote',content:[{type:'paragraph',...(inline?{content:inline}:{})}]};if(type==='code')return {type:'codeBlock',...(inline?{content:inline}:{})};if(type==='divider')return {type:'horizontalRule'};if(type==='table')return {type:'table'};if(type==='raw'){try{return JSON.parse(value)}catch{return {type:'paragraph',...(inline?{content:inline}:{})}}}return {type:'paragraph',...(inline?{content:inline}:{})}}
function blockNode(row){
 const type=row.dataset.type;
 if(type==='divider')return {type:'horizontalRule'};
 if(type==='raw'){try{return JSON.parse(row.querySelector('.block-raw').value)}catch{return {type:'paragraph',content:[{type:'text',text:row.querySelector('.block-raw').value}]}}}
 if(type==='code'){const value=row.querySelector('.block-raw').value;return {type:'codeBlock',...(value?{content:[{type:'text',text:value}]}:{})}}
 if(type==='table'){const rows=Array.from(row.querySelectorAll('.block-table tr')).map(tr=>({type:'tableRow',content:Array.from(tr.cells).map(cell=>({type:cell.dataset.cellType||'tableCell',content:[{type:'paragraph',...(domInline(cell).length?{content:domInline(cell)}:{})}]}))}));return {type:'table',content:rows}}
 const edit=row.querySelector('.block-edit');
 if(type==='bullet'||type==='numbered'){const source=edit.children.length?Array.from(edit.children):[edit];return {type:type==='bullet'?'bulletList':'orderedList',content:source.map(item=>({type:'listItem',content:[{type:'paragraph',...(domInline(item).length?{content:domInline(item)}:{})}]}))}}
 const content=domInline(edit);if(type==='quote')return {type:'blockquote',content:[{type:'paragraph',...(content.length?{content}:{})}]};if(type.startsWith('heading'))return {type:'heading',attrs:{level:Number(type.slice(-1))},...(content.length?{content}:{})};return {type:'paragraph',...(content.length?{content}:{})};
}
function renderBlocks(doc){blockList.replaceChildren();(doc.content||[]).forEach(node=>blockList.appendChild(renderBlock(nodeBlock(node))));if(!blockList.children.length)blockList.appendChild(renderBlock({type:'paragraph',node:{type:'paragraph'}}))}
function blocksDoc(){return {type:'doc',content:Array.from(blockList.children).map(blockNode)}}

function inlineMarkdown(nodes){return (nodes||[]).map(node=>{if(node.type==='hardBreak')return '  \n';if(node.type!=='text')return inlineMarkdown(node.content);let value=node.text||'';(node.marks||[]).forEach(mark=>{if(mark.type==='bold')value='**'+value+'**';if(mark.type==='italic')value='*'+value+'*';if(mark.type==='strike')value='~~'+value+'~~';if(mark.type==='code')value='`'+value+'`';if(mark.type==='link')value='['+value+']('+((mark.attrs||{}).href||'')+')'});return value}).join('')}
function docMarkdown(doc){
 function nodeMd(node){if(node.type==='paragraph')return inlineMarkdown(node.content);if(node.type==='heading')return '#'.repeat(Number((node.attrs||{}).level||2))+' '+inlineMarkdown(node.content);if(node.type==='horizontalRule')return '---';if(node.type==='codeBlock')return '```\n'+textContent(node)+'\n```';if(node.type==='blockquote')return (node.content||[]).map(nodeMd).join('\n').split('\n').map(line=>'> '+line).join('\n');if(node.type==='bulletList'||node.type==='orderedList')return (node.content||[]).map((item,index)=>(node.type==='bulletList'?'- ':(index+1)+'. ')+(item.content||[]).map(nodeMd).join(' ')).join('\n');if(node.type==='table')return (node.content||[]).map((row,index)=>{const line='| '+(row.content||[]).map(cell=>textContent(cell).replace(/\|/g,'\\|')).join(' | ')+' |';return index===0?line+'\n| '+(row.content||[]).map(()=> '---').join(' | ')+' |':line}).join('\n');return textContent(node)}
 return (doc.content||[]).map(nodeMd).join('\n\n').replace(/\n{3,}/g,'\n\n').trim();
}
function inlineFromMarkdown(value){
 const nodes=[],pattern=/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;let at=0,match;
 function text(value,marks){if(value)nodes.push({type:'text',text:value,...(marks?{marks}: {})})}
 while((match=pattern.exec(value))){text(value.slice(at,match.index));const token=match[0];if(token.startsWith('**'))text(token.slice(2,-2),[{type:'bold'}]);else if(token.startsWith('*'))text(token.slice(1,-1),[{type:'italic'}]);else if(token.startsWith('`'))text(token.slice(1,-1),[{type:'code'}]);else{const link=token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);text(link[1],[{type:'link',attrs:{href:link[2]}}])}at=pattern.lastIndex}
 text(value.slice(at));return nodes;
}
function markdownDoc(value){
 const lines=String(value||'').replace(/\r\n/g,'\n').split('\n'),nodes=[];let i=0;
 while(i<lines.length){const line=lines[i];if(!line.trim()){i++;continue}if(/^```/.test(line)){const body=[];i++;while(i<lines.length&&!/^```/.test(lines[i]))body.push(lines[i++]);if(i<lines.length)i++;nodes.push({type:'codeBlock',...(body.length?{content:[{type:'text',text:body.join('\n')}]}:{})});continue}const heading=line.match(/^(#{1,3})\s+(.*)$/);if(heading){nodes.push({type:'heading',attrs:{level:heading[1].length},content:inlineFromMarkdown(heading[2])});i++;continue}if(/^\s*>\s?/.test(line)){const body=[];while(i<lines.length&&/^\s*>\s?/.test(lines[i]))body.push(lines[i++].replace(/^\s*>\s?/,''));nodes.push({type:'blockquote',content:[{type:'paragraph',content:inlineFromMarkdown(body.join(' '))}]});continue}if(/^\s*[-*+]\s+/.test(line)||/^\s*\d+[.)]\s+/.test(line)){const ordered=/^\s*\d/.test(line),items=[];const matcher=ordered?/^\s*\d+[.)]\s+/:/^\s*[-*+]\s+/;while(i<lines.length&&matcher.test(lines[i]))items.push({type:'listItem',content:[{type:'paragraph',content:inlineFromMarkdown(lines[i++].replace(matcher,''))}]});nodes.push({type:ordered?'orderedList':'bulletList',content:items});continue}if(/^\s*\|.*\|\s*$/.test(line)){const tableLines=[];while(i<lines.length&&/^\s*\|.*\|\s*$/.test(lines[i]))tableLines.push(lines[i++]);const rows=tableLines.filter((row,index)=>index!==1||!/^\s*\|?\s*:?-+/.test(row)).map((row,index)=>({type:'tableRow',content:row.trim().replace(/^\||\|$/g,'').split('|').map(value=>({type:index===0?'tableHeader':'tableCell',content:[{type:'paragraph',content:inlineFromMarkdown(value.trim())}]}))}));nodes.push({type:'table',content:rows});continue}if(/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(line)){nodes.push({type:'horizontalRule'});i++;continue}const paragraph=[];while(i<lines.length&&lines[i].trim()&&!/^(#{1,3}\s|```|\s*>\s?|\s*[-*+]\s+|\s*\d+[.)]\s+|\s*\|.*\|\s*$|\s*(-{3,}|\*{3,}|_{3,})\s*$)/.test(lines[i]))paragraph.push(lines[i++]);nodes.push({type:'paragraph',content:inlineFromMarkdown(paragraph.join(' '))})}
 return {type:'doc',content:nodes.length?nodes:[{type:'paragraph'}]};
}
function readMode(){if(state.mode==='rich')state.doc=editor.getJSON();else if(state.mode==='block')state.doc=blocksDoc();else state.doc=markdownDoc(markdown.value)}
function setMode(mode){
 if(mode!==state.mode)readMode();state.mode=mode;el.hidden=mode!=='rich';blockEditor.hidden=mode!=='block';markdown.hidden=mode!=='markdown';
 switching=true;if(mode==='rich')editor.commands.setContent(state.doc,{emitUpdate:false});if(mode==='block')renderBlocks(state.doc);if(mode==='markdown')markdown.value=docMarkdown(state.doc);switching=false;
 document.querySelectorAll('[data-mode]').forEach(button=>{button.classList.toggle('active',button.dataset.mode===mode);button.setAttribute('aria-pressed',button.dataset.mode===mode?'true':'false')});document.querySelectorAll('[data-rich-tool]').forEach(button=>button.hidden=mode!=='rich');
}
async function save(){clearTimeout(timer);readMode();status.textContent='Saving…';const markdownValue=state.mode==='markdown'?markdown.value:docMarkdown(state.doc);const res=await fetch(location.pathname+'/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:title.value,content_json:JSON.stringify(state.doc),markdown:markdownValue,version})});const out=await res.json();if(res.status===409){status.textContent='Newer version exists — reload';return false}if(res.ok){version=out.version;document.body.dataset.version=version;const publishedVersion=document.querySelector('#publication-version');if(publishedVersion)publishedVersion.textContent=version;status.textContent='Saved';return true}status.textContent=out.error||'Save failed';return false}
document.querySelectorAll('[data-mode]').forEach(button=>button.onclick=()=>setMode(button.dataset.mode));
blockEditor.addEventListener('input',queueSave);markdown.addEventListener('input',queueSave);
document.querySelector('#add-block').onclick=()=>{const added=renderBlock({type:'paragraph',node:{type:'paragraph'}});blockList.appendChild(added);added.querySelector('.block-edit').focus();queueSave()};
setMode('rich');
"""

def _display_time(value):
    if not value:return "Unknown time"
    try:return datetime.fromisoformat(value.replace("Z","+00:00")).strftime("%d %b %Y, %H:%M UTC")
    except ValueError:return value

def _comment_tree(comments,page_id,parent_id=None,seen=None):
    seen=set() if seen is None else seen
    rendered=[]
    for comment in (item for item in comments if item.get("parent_id")==parent_id and item["id"] not in seen):
        seen.add(comment["id"])
        reply=Details(
            Summary("Reply"),
            Form(
                Input(type="hidden",name="parent_id",value=comment["id"]),
                Input(type="hidden",name="kind",value="reply"),
                Textarea(name="body",placeholder=f"Reply to {comment['user_name']}",rows="2",required=True),
                Button("Reply",cls="smallbtn"),
                method="post",action=f"/pages/{page_id}/comments",cls="smallform"),
            cls="replybox")
        children=_comment_tree(comments,page_id,comment["id"],seen)
        rendered.append(Div(
            Div(B(comment["user_name"]),Small(_display_time(comment["created_at"])),cls="commenthead"),
            P(comment["body"]),reply,*children,cls="comment"))
    return rendered

def page_shell(who,spaces,pages,current,comments,attachments,embeds,ancestors=()):
    tools=[("B","bold"),("I","italic"),("U","underline"),("H2","h2"),("• List","bullet"),("1. List","ordered"),("❝","quote"),("</>","code"),("Table","table")]
    bottom=Section(
        Div(
            H3("Comments"),
            Form(Textarea(name="body",placeholder="Leave a comment",required=True),Select(Option("Page comment",value="page"),Option("Inline selection",value="inline"),name="kind"),Button("Comment",cls="smallbtn"),method="post",action=f"/pages/{current['id']}/comments",cls="smallform"),
            Div(*_comment_tree(comments,current["id"]),cls="comment-list"),id="comments",cls="panel"),
        Div(H3("Attachments"),*[A(a["name"],href=f"/attachments/{a['id']}",cls="result") for a in attachments],Form(Input(type="file",name="file",required=True),Button("Upload",cls="smallbtn"),method="post",action=f"/pages/{current['id']}/attachments",enctype="multipart/form-data",cls="smallform"),cls="panel"),
        Div(H3("FastOffice links"),*[A(f"{e['product']} · {e['title']}",href=e["url"],target="_blank",rel="noopener noreferrer",cls="result") for e in embeds],Form(Select(*[Option(p) for p in ("FastDocs","FastSheets","FastSlides","FastDrive","FastMeet","FastCal","FastMail","FastInsights","FastPilot")],name="product"),Input(name="title",placeholder="Resource title",required=True),Input(name="url",type="url",placeholder="https://…",required=True),Button("Add link",cls="smallbtn"),method="post",action=f"/pages/{current['id']}/embeds",cls="smallform"),cls="panel"),
        cls="bottom-bar")
    next_status="published" if current["status"]=="draft" else "draft"
    status_button="Publish" if current["status"]=="draft" else "Move to draft"
    can_manage=current["created_by"]==who["sub"] or who.get("role") in ("owner","admin")
    publication=Form(Input(type="hidden",name="status",value=next_status),Button(status_button,cls="btn"),method="post",action=f"/pages/{current['id']}/status",cls="inlineform") if can_manage else None
    topbar=Div(
        Form(Input(name="q",placeholder="Search this workspace",cls="search"),method="get",action="/search"),
        Span("Saved",id="save-status",cls="status"),
        Div(A("Download PDF",href=f"/pages/{current['id']}/pdf",id="download-pdf",cls="btn ghost",download=f"{current['slug']}.pdf"),Form(Button("Add child",cls="btn ghost"),method="post",action=f"/pages/{current['id']}/children",cls="inlineform"),publication,cls="pageactions"),cls="topbar")
    published_meta=Span("Published ",_display_time(current.get("published_at"))," · Version ",Span(str(current["version"]),id="publication-version")," · ",current.get("author_name") or current["created_by"],cls="publication-meta") if current["status"]=="published" else None
    editor=Div(
        Div(*[value for pair in [(A(item["title"],href=f"/pages/{item['id']}"),Span("/")) for item in ancestors] for value in pair],Span(current["space_name"]),Span(current["status"].title(),cls="pagebadge "+current["status"]),published_meta,cls="breadcrumbs"),
        Input(value=current["title"],id="page-title",cls="titleinput",aria_label="Page title"),
        Div(*[Button(label,type="button",data_cmd=cmd,data_rich_tool="true",cls="tool") for label,cmd in tools],
            Span(cls="toolbar-spacer"),
            Button("Rich",id="mode-rich",type="button",data_mode="rich",aria_pressed="true",cls="tool mode active"),
            Button("Blocks",id="mode-block",type="button",data_mode="block",aria_pressed="false",cls="tool mode"),
            Button("Markdown",id="mode-md",type="button",data_mode="markdown",aria_pressed="false",cls="tool mode"),cls="toolbar"),
        Div(id="editor",cls="editor"),
        Div(Button("＋ Add block",id="add-block",type="button",cls="btn ghost block-actions"),Div(id="block-list",cls="block-list"),id="block-editor",cls="block-editor",hidden=True),
        Textarea(current["markdown"],id="markdown",cls="markdown-editor",hidden=True,aria_label="Markdown editor"),
        Script(current["content_json"],type="application/json",id="initial-content"),
        Div(Form(Button("Move to trash",cls="btn ghost"),method="post",
                 action=f"/pages/{current['id']}/trash"),style="margin-top:50px"),
        cls="editorwrap")
    return Html(
        head(current["title"]+" · FastWiki"),
        Body(
            sidebar(who,spaces,pages,current["id"]),
            Main(topbar,editor,bottom,cls="workspace"),
            Script(EDITOR_JS,type="module"),
            cls="shell",data_version=str(current["version"])))

ASSISTANT_JS=r"""
const form=document.querySelector('#assistant-form');
const input=document.querySelector('#assistant-input');
const messages=document.querySelector('#assistant-messages');
const sources=document.querySelector('#assistant-sources');
const usage=document.querySelector('#assistant-usage');
function bubble(role,text){const node=document.createElement('div');node.className='message '+role;node.textContent=text;messages.appendChild(node);messages.scrollTop=messages.scrollHeight;return node}
function addDraftAction(node,id){const form=document.createElement('form');form.method='post';form.action='/assistant/messages/'+id+'/draft';const button=document.createElement('button');button.className='smallbtn';button.textContent='Create draft page from answer';button.style.marginTop='12px';form.appendChild(button);node.appendChild(form)}
function showSources(items){sources.replaceChildren();items.forEach((item,index)=>{const link=document.createElement('a');link.className='sourcecard';link.href='/pages/'+item.id;const title=document.createElement('b');title.textContent='['+(index+1)+'] '+item.title;const excerpt=document.createElement('p');excerpt.textContent=item.excerpt;const badge=document.createElement('span');badge.className='pagebadge '+item.status;badge.textContent=item.status;link.append(title,excerpt,badge);sources.appendChild(link)})}
form.addEventListener('submit',async event=>{event.preventDefault();const question=input.value.trim();if(!question)return;input.value='';bubble('user',question);const answer=bubble('assistant','');form.querySelector('button').disabled=true;
 try{const response=await fetch('/assistant/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({thread_id:document.body.dataset.thread,question})});if(!response.ok){const out=await response.json();throw new Error(out.error||'Assistant request failed')}
 const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='';while(true){const part=await reader.read();buffer+=decoder.decode(part.value||new Uint8Array(),{stream:!part.done});const lines=buffer.split('\n');buffer=lines.pop();for(const line of lines){if(!line)continue;const item=JSON.parse(line);if(item.type==='sources')showSources(item.items);if(item.type==='token')answer.textContent+=item.content;if(item.type==='error')throw new Error(item.error);if(item.type==='done'){usage.textContent=item.remaining===null?'Unlimited queries':item.remaining+' queries remaining today';addDraftAction(answer,item.message_id)}}if(part.done)break}
 }catch(error){answer.textContent=error.message}finally{form.querySelector('button').disabled=false;messages.scrollTop=messages.scrollHeight}});
input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();form.requestSubmit()}});
"""

def assistant_shell(who,threads,current,messages,sources,remaining):
    left=Aside(Div(A(Span("W",cls="mark"),"FastWiki",href="/",cls="brand"),cls="sidehead"),Form(Button("＋ New conversation",cls="btn",style="width:100%"),method="post",action="/assistant/threads"),Div(H3("Recent"),*[A(thread["title"],href=f"/assistant?thread={thread['id']}",cls="sideitem"+(" active" if thread["id"]==current["id"] else "")) for thread in threads],cls="conversation-list"),Div(A("← Back to pages",href="/",cls="sideitem"),A("⚙ Workspace",href="/settings",cls="sideitem"),A("Sign out",href="/logout",cls="sideitem"),style="margin-top:auto"),cls="assistant-left")
    rendered=[]
    for message in messages:
        actions=Form(Button("Create draft page from answer",cls="smallbtn",style="margin-top:12px"),method="post",action=f"/assistant/messages/{message['id']}/draft") if message["role"]=="assistant" else None
        rendered.append(Div(message["content"],actions,cls="message "+message["role"]))
    centre=Main(Div(Div(H2("AI Assistant"),P("Grounded in your workspace",cls="usage")),Span("Unlimited queries" if remaining is None else f"{remaining} queries remaining today",id="assistant-usage",cls="usage"),cls="assistant-header"),Div(*rendered,*([] if messages else [Div(H2("Ask your workspace"),P("Find answers, draft content, or propose edits using cited wiki pages."),cls="assistant-empty")]),id="assistant-messages",cls="assistant-messages"),Form(Textarea(name="question",id="assistant-input",placeholder="Ask about your workspace…",required=True),Button("Send",cls="btn"),id="assistant-form",cls="assistant-form"),cls="assistant-center")
    right=Aside(H3("Cited pages"),P("The assistant can read published pages and drafts you are allowed to see.",cls="usage"),Div(*[A(B(f"[{index}] {item['title']}"),P(item["excerpt"]),Span(item["status"],cls="pagebadge "+item["status"]),href=f"/pages/{item['id']}",cls="sourcecard") for index,item in enumerate(sources,1)],id="assistant-sources"),cls="assistant-context")
    return Html(head("AI Assistant · FastWiki"),Body(left,centre,right,Script(ASSISTANT_JS),cls="assistant-shell",data_thread=current["id"]))

def list_page(who,spaces,pages,title,items,kind="search"):
    content=[A(H2(i["title"]),P((i.get("plain_text") or "")[:180]),href=f"/pages/{i['id']}",cls="result") for i in items]
    return Html(head(title+" · FastWiki"),Body(sidebar(who,spaces,pages),Main(Div(Form(Input(name="q",placeholder="Search pages",cls="search",autofocus=True),Button("Search",cls="btn"),method="get"),H1(title),*(content or [Div("Nothing here yet.",cls="empty")]),cls="cardlist"),cls="workspace"),cls="shell",style="grid-template-columns:260px 1fr"))
