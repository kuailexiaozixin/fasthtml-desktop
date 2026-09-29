"""FastDocs 3-pane layout — indigo palette, block document editor, SSE AI rail."""
from __future__ import annotations

from fasthtml.common import (
    Div, H1, H3, H4, P, Span, A, Button, Form, Input, Title, Link, Script, Style, NotStr,
)

import db

LAYOUT_CSS = """
:root{
  --bg:#f5f6fb; --surface:#ffffff; --surface-2:#eef0fb; --border:#e3e6f3; --text:#171a2b;
  --text-dim:#444a63; --text-mute:#878fae; --accent:#4f46e5; --accent-hover:#4338ca;
  --accent-light:#eef2ff; --ok:#16a34a; --warn:#d97706; --danger:#e11d48;
}
*{box-sizing:border-box;}
html,body{margin:0;padding:0;height:100%;background:var(--bg);color:var(--text);
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:14px;}
a{color:var(--accent);text-decoration:none;} a:hover{text-decoration:underline;}
.app{display:grid;grid-template-columns:248px 1fr var(--rail,340px);grid-template-rows:52px 1fr;
  grid-template-areas:"top top top" "left center right";height:100vh;overflow:hidden;transition:grid-template-columns .18s ease;}
.app.right-expanded{--rail:clamp(420px,42vw,720px);} .app.right-collapsed{--rail:0px;} .app.right-collapsed .right-pane{display:none;}
#copilot-reopen{position:fixed;right:0;bottom:26px;display:none;align-items:center;gap:6px;cursor:pointer;z-index:60;
  background:var(--accent);color:#fff;font-size:13px;font-weight:600;padding:9px 14px;border-radius:8px 0 0 8px;box-shadow:0 2px 10px rgba(0,0,0,.18);}
.app.right-collapsed #copilot-reopen{display:inline-flex;}
.copilot-min,.copilot-exp{cursor:pointer;border:1px solid var(--border);background:var(--surface);border-radius:6px;padding:4px 9px;font-size:13px;line-height:1;color:var(--text-mute);}
.topbar{grid-area:top;display:flex;align-items:center;justify-content:space-between;padding:0 20px;background:var(--surface);border-bottom:1px solid var(--border);}
.brand{font-weight:700;letter-spacing:.3px;display:flex;align-items:center;gap:8px;font-size:16px;}
.brand-dot{width:11px;height:11px;background:var(--accent);border-radius:3px;display:inline-block;}
.env-pill{background:var(--accent-light);color:var(--accent-hover);padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;}
.topbar .actions{display:flex;gap:10px;align-items:center;}
.left-pane{grid-area:left;background:var(--surface);border-right:1px solid var(--border);padding:12px 0;overflow-y:auto;}
.new-btn{display:block;margin:0 16px 12px;text-align:center;background:var(--accent);color:#fff;font-weight:600;padding:10px;border-radius:10px;}
.new-btn:hover{background:var(--accent-hover);color:#fff;text-decoration:none;}
.nav-section{margin-bottom:14px;} .nav-section h4{margin:8px 16px 4px;font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:var(--text-mute);font-weight:700;}
.nav-item{display:flex;align-items:center;gap:9px;padding:8px 16px;color:var(--text-dim);cursor:pointer;border-left:3px solid transparent;}
.nav-item:hover{background:var(--surface-2);color:var(--text);text-decoration:none;}
.nav-item.active{background:var(--accent-light);color:var(--accent-hover);border-left-color:var(--accent);font-weight:600;}
.nav-icon{width:18px;display:inline-block;text-align:center;}
.nav-doc{display:block;padding:6px 16px 6px 22px;color:var(--text-dim);font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.nav-doc:hover{background:var(--surface-2);color:var(--text);text-decoration:none;}
.nav-doc.active{color:var(--accent-hover);font-weight:600;}
.center-pane{grid-area:center;overflow-y:auto;padding:18px 28px 60px;}
.page-title{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;gap:12px;flex-wrap:wrap;}
.page-title h1{margin:0;font-size:21px;font-weight:700;} .page-title .sub{color:var(--text-mute);font-size:13px;margin-top:3px;}

/* document list */
.folder-sec{margin-bottom:22px;} .folder-sec h4{display:flex;align-items:center;gap:8px;margin:0 0 10px;font-size:13px;font-weight:700;color:var(--text-dim);}
.folder-sec h4 .count{color:var(--text-mute);font-weight:500;font-size:12px;}
.doc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px;}
.doc-card{display:block;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;color:var(--text);min-height:96px;}
.doc-card:hover{border-color:var(--accent);box-shadow:0 6px 18px rgba(79,70,229,.10);text-decoration:none;}
.doc-card h3{margin:0 0 6px;font-size:15px;line-height:1.3;display:flex;align-items:center;gap:6px;}
.doc-card .excerpt{color:var(--text-mute);font-size:12.5px;line-height:1.45;max-height:54px;overflow:hidden;}
.doc-card .meta{margin-top:10px;font-size:11px;color:var(--text-mute);display:flex;gap:8px;align-items:center;}
.badge{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;padding:2px 7px;border-radius:999px;background:var(--surface-2);color:var(--text-dim);}
.badge.live{background:#dcfce7;color:#15803d;}

/* editor */
.doc-bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px;}
.doc-title-form{display:flex;gap:8px;align-items:center;flex:1;min-width:240px;}
.doc-title-form input{flex:1;font-size:24px;font-weight:700;border:1px solid transparent;border-radius:8px;padding:6px 8px;background:transparent;color:var(--text);font-family:inherit;}
.doc-title-form input:hover{background:var(--surface-2);} .doc-title-form input:focus{background:var(--surface);border-color:var(--border);outline:none;}
.pub-box{margin-bottom:14px;padding:11px 14px;background:#ecfdf5;border:1px solid #bbf7d0;border-radius:10px;font-size:13px;color:#15803d;display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.pub-box code{background:#fff;border:1px solid #bbf7d0;padding:3px 8px;border-radius:6px;color:#166534;}
.blocks{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px 26px;max-width:820px;}
.block{position:relative;padding:3px 0;}
.block:hover{background:linear-gradient(90deg,transparent,transparent);}
.blk-toolbar{position:absolute;top:2px;right:0;display:none;gap:3px;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:3px;box-shadow:0 2px 8px rgba(0,0,0,.07);z-index:5;}
.block:hover>.blk-toolbar{display:flex;}
.blk-toolbar button{border:none;background:transparent;cursor:pointer;font-size:13px;line-height:1;padding:4px 6px;border-radius:5px;color:var(--text-mute);}
.blk-toolbar button:hover{background:var(--surface-2);color:var(--accent);} .blk-toolbar button:disabled{opacity:.3;cursor:not-allowed;}
.blk-toolbar button.del:hover{background:#fee2e2;color:var(--danger);}
.blk-h1{font-size:30px;font-weight:800;margin:14px 0 8px;line-height:1.2;}
.blk-h2{font-size:23px;font-weight:700;margin:18px 0 6px;line-height:1.25;}
.blk-h3{font-size:18px;font-weight:700;margin:14px 0 4px;color:var(--text-dim);}
.blk-p{margin:8px 0;line-height:1.7;color:var(--text-dim);}
.blk-p p{margin:8px 0;} .block ul,.block ol{margin:8px 0;padding-left:26px;line-height:1.7;color:var(--text-dim);} .block li{margin:4px 0;}
.block blockquote{margin:12px 0;padding:6px 16px;border-left:3px solid var(--accent);color:var(--text-mute);font-style:italic;}
.block pre{margin:10px 0;background:#0f172a;color:#e2e8f0;padding:14px 16px;border-radius:10px;overflow:auto;font-size:13px;}
.block pre code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;}
.block code{background:var(--surface-2);padding:1px 5px;border-radius:4px;font-size:.92em;}
.blk-hr{border:none;border-top:2px solid var(--border);margin:18px 0;}
.blk-empty{color:var(--text-mute);font-style:italic;}
.blk-edit{background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:12px;margin:6px 0;}
.blk-edit select{padding:6px 9px;border:1px solid var(--border);border-radius:7px;font-size:13px;font-family:inherit;margin-bottom:8px;}
.blk-edit textarea{width:100%;min-height:90px;padding:10px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px;font-family:ui-monospace,monospace;resize:vertical;line-height:1.5;}
.blk-edit .row{display:flex;gap:8px;align-items:center;margin-top:8px;}
.addbar{display:flex;gap:6px;flex-wrap:wrap;margin-top:14px;padding-top:14px;border-top:1px dashed var(--border);}
.addbar .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-mute);font-weight:700;align-self:center;margin-right:4px;}

.btn{padding:6px 12px;border-radius:7px;border:1px solid var(--border);background:var(--surface);color:var(--text);cursor:pointer;font-size:13px;font-family:inherit;}
.btn:hover{background:var(--surface-2);text-decoration:none;} .btn.primary{background:var(--accent);color:#fff;border-color:var(--accent);} .btn.primary:hover{background:var(--accent-hover);color:#fff;}
.btn.sm{padding:4px 9px;font-size:12px;} .btn.danger{border-color:var(--danger);color:var(--danger);} .btn.danger:hover{background:var(--danger);color:#fff;}
.btn:disabled{opacity:.4;cursor:not-allowed;}
.toolbar{display:flex;gap:6px;align-items:center;flex-wrap:wrap;}

/* templates + versions */
.tpl-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;}
.tpl-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:18px;}
.tpl-card h3{margin:0 0 6px;font-size:16px;} .tpl-card p{margin:0 0 12px;color:var(--text-mute);font-size:13px;line-height:1.45;}
.ver-list{max-width:680px;} .ver-row{display:flex;align-items:center;justify-content:space-between;gap:12px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 16px;margin-bottom:8px;}
.ver-row .when{font-weight:600;} .ver-row .tag{font-size:11px;color:var(--text-mute);}

.gen-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px;max-width:640px;}
.gen-card h3{margin:0 0 6px;} .gen-card .askbox{width:100%;padding:12px;border:1px solid var(--border);border-radius:8px;font-size:15px;font-family:inherit;}
.gen-card .row{display:flex;gap:10px;margin-top:10px;flex-wrap:wrap;align-items:center;} .gen-card select{padding:10px;border:1px solid var(--border);border-radius:8px;}
.notice{margin-bottom:14px;padding:12px 16px;background:var(--accent-light);border-left:4px solid var(--accent);color:var(--accent-hover);border-radius:8px;font-size:13px;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px;max-width:720px;}
.card h3{margin:0 0 6px;} .card+.card{margin-top:14px;}

.login-wrap{height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#e7e9fb 0%,#eef2ff 100%);}
.login-card{background:#fff;padding:36px 40px;border-radius:14px;width:360px;box-shadow:0 20px 40px rgba(15,23,42,.08);}
.login-card h1{margin:0 0 4px;font-size:22px;} .login-card p{margin:0 0 20px;color:var(--text-mute);font-size:13px;}
.login-card input{width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:8px;margin-bottom:10px;font-size:14px;}
.login-card button{width:100%;padding:10px;font-weight:600;} .login-card .error{color:var(--danger);font-size:12px;margin:6px 0;} .login-card .hint{font-size:11.5px;color:var(--text-mute);margin-top:10px;text-align:center;}

.right-pane{grid-area:right;background:var(--surface);border-left:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;}
.right-header{padding:12px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;} .right-header h3{margin:0;font-size:14px;font-weight:700;} .right-header .tabs{display:flex;gap:6px;}
.chat-body{flex:1;overflow-y:auto;padding:14px 16px;display:flex;flex-direction:column;gap:12px;}
.msg{max-width:90%;padding:10px 14px;border-radius:12px;font-size:13px;line-height:1.55;overflow-wrap:anywhere;}
.msg.user{background:var(--accent);color:#fff;align-self:flex-end;border-bottom-right-radius:3px;white-space:pre-wrap;}
.msg.assistant{background:var(--surface-2);border:1px solid var(--border);color:var(--text);align-self:flex-start;border-bottom-left-radius:3px;}
.msg code{background:rgba(0,0,0,.06);padding:1px 4px;border-radius:3px;font-size:12px;}
.chat-input{border-top:1px solid var(--border);padding:10px;background:var(--surface);} .chat-input-row{display:flex;gap:8px;align-items:stretch;}
.chat-input-row input{flex:1;min-width:0;padding:10px 12px;border:1px solid var(--border);border-radius:8px;font-size:13px;outline:none;}
.chat-input-row input:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-light);}
.chat-send-btn{display:inline-flex;align-items:center;background:var(--accent);color:#fff;border:none;border-radius:8px;padding:0 16px;font-weight:600;font-size:13px;cursor:pointer;} .chat-send-btn:disabled{background:var(--text-mute);}
.chat-empty-hint{color:var(--text-mute);font-size:12.5px;line-height:1.5;text-align:center;padding:18px 14px;}
.sample-cards{padding:.4rem 1rem .8rem;background:var(--surface);border-top:1px solid var(--border);}
.sample-cards-label{display:inline-block;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.12em;color:var(--text-mute);margin-bottom:6px;}
.sample-card{display:flex;align-items:center;gap:8px;background:var(--bg);border:1px solid var(--border);padding:9px 12px;border-radius:10px;font-size:12.5px;cursor:pointer;color:var(--text-dim);width:100%;text-align:left;line-height:1.35;margin-bottom:6px;font-family:inherit;}
.sample-card::before{content:"💬";flex-shrink:0;} .sample-card:hover{border-color:var(--accent);color:var(--accent);background:var(--accent-light);}
.thinking-indicator{display:flex;align-items:center;gap:8px;padding:6px 14px;font-size:12.5px;color:var(--text-mute);align-self:flex-start;}
.thinking-indicator .dot{width:8px;height:8px;border-radius:50%;background:var(--accent);animation:pulse 1.2s ease-in-out infinite;}
@keyframes pulse{0%,100%{opacity:.35;transform:scale(.85);}50%{opacity:1;transform:scale(1.1);}}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;vertical-align:middle;}
@keyframes spin{to{transform:rotate(360deg);}}
"""

NAV = [("docs", "All documents", "📄", "/"), ("templates", "Templates", "🧩", "/templates"),
       ("ai", "AI Assistant", "🤖", "/ai"), ("guide", "User Guide", "📖", "/guide"),
       ("developers", "Developers", "⌘", "/developers")]
SAMPLE_QUESTIONS = ["How many documents do I have?", "Draft an intro about onboarding", "Summarise the Q3 Product Plan"]


def topbar(env, user_email):
    right = Div(
        Button(NotStr("&laquo; Chat"), id="copilot-topbar-toggle", cls="btn", onclick="toggleCopilot()") if user_email else None,
        Span(env, cls="env-pill"),
        Span(user_email or "", style="color:var(--text-mute);font-size:12px;") if user_email else None,
        A("Logout", href="/logout", cls="btn") if user_email else None, cls="actions")
    return Div(Div(Span(cls="brand-dot"), Span("Fast", style="font-weight:800;"),
                   Span("Docs", style="color:var(--accent);font-weight:700;letter-spacing:.5px;"), cls="brand"),
               right, cls="topbar")


def left_pane(active, active_doc=None):
    items = [A(Span(icon, cls="nav-icon"), Span(label), href=href,
               cls=f"nav-item {'active' if active == key else ''}") for key, label, icon, href in NAV]
    recent = db.documents()[:8]
    doc_links = [A(d["title"], href=f"/doc/{d['id']}",
                   cls=f"nav-doc {'active' if active_doc == d['id'] else ''}") for d in recent]
    sections = [Div(*items, cls="nav-section")]
    if doc_links:
        sections.append(Div(H4("Recent"), *doc_links, cls="nav-section"))
    return Div(A("＋  New document", href="/new", cls="new-btn"), *sections, cls="left-pane")


def _sample_cards():
    cards = [Button(Span(q), cls="sample-card", onclick=f"fillChat({q!r});sendMessage(null);", title=q) for q in SAMPLE_QUESTIONS]
    return Div(Div(Span("Try asking:", cls="sample-cards-label")), Div(*cards), cls="sample-cards")


def right_pane_chat(thread_id):
    return Div(
        Div(H3("AI Assistant"),
            Div(Button("New", cls="btn", hx_get="/chat/new", hx_target="#chat-body", hx_swap="innerHTML"),
                Button(NotStr("&laquo;"), id="copilot-exp-btn", cls="copilot-exp", onclick="toggleExpand()"),
                Button(NotStr("&rsaquo;"), cls="copilot-min", onclick="toggleCopilot()"), cls="tabs"),
            cls="right-header"),
        Div(Div(P("Ask me to draft, rewrite or summarise — or generate a whole document from the Generate page.",
                  cls="chat-empty-hint"), id="chat-body", cls="chat-body"),
            Form(Input(type="hidden", name="thread_id", value=thread_id, id="thread-id"),
                 Div(Input(type="text", name="message", id="chat-input",
                           placeholder="Ask the writing assistant …", autocomplete="off"),
                     Button("Send", type="submit", cls="chat-send-btn", id="chat-send-btn"), cls="chat-input-row"),
                 onsubmit="return streamChat(event)", cls="chat-input"),
            _sample_cards(),
            style="display:flex;flex-direction:column;flex:1;overflow:hidden;"),
        cls="right-pane")


def page(active, env, user_email, thread_id, *content, active_doc=None, right_override=None):
    right = right_override if right_override is not None else right_pane_chat(thread_id)
    return (Title("FastDocs"),
            Link(rel="icon", type="image/svg+xml", href="/static/favicon.svg"),
            Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
            Style(LAYOUT_CSS),
            Div(topbar(env, user_email), left_pane(active, active_doc), Div(*content, cls="center-pane"), right,
                Div(NotStr("&lsaquo; AI Assistant"), id="copilot-reopen", onclick="toggleCopilot()"), cls="app"),
            Script(LAYOUT_JS))


LAYOUT_JS = """
function _sync(){var app=document.querySelector('.app');if(!app)return;
  var ex=app.classList.contains('right-expanded'),col=app.classList.contains('right-collapsed');
  var eb=document.getElementById('copilot-exp-btn');if(eb){eb.innerHTML=ex?'\\u00BB':'\\u00AB';}
  var tb=document.getElementById('copilot-topbar-toggle');if(tb){tb.innerHTML=col?'\\u00AB Chat':'Chat \\u203A';}}
function toggleCopilot(){var app=document.querySelector('.app');if(!app)return;app.classList.toggle('right-collapsed');
  if(app.classList.contains('right-collapsed'))app.classList.remove('right-expanded');
  try{localStorage.setItem('fdCollapsed',app.classList.contains('right-collapsed')?'1':'0');}catch(e){}_sync();}
function toggleExpand(){var app=document.querySelector('.app');if(!app)return;app.classList.remove('right-collapsed');app.classList.toggle('right-expanded');
  try{localStorage.setItem('fdExpanded',app.classList.contains('right-expanded')?'1':'0');localStorage.setItem('fdCollapsed','0');}catch(e){}_sync();}
(function(){try{var app=document.querySelector('.app');if(!app)return;
  if(localStorage.getItem('fdCollapsed')==='1')app.classList.add('right-collapsed');
  else if(localStorage.getItem('fdExpanded')==='1')app.classList.add('right-expanded');}catch(e){}})();
document.addEventListener('DOMContentLoaded',_sync);
function fillChat(t){var el=document.getElementById('chat-input');if(el){el.value=t;el.focus();}}
function sendMessage(ev){return streamChat(ev);}
function genSubmit(){var b=document.getElementById('gen-btn');if(b){b.disabled=true;b.innerHTML='<span class=spinner></span> Generating…';}return true;}
var _streaming=false,_thinker=null;
function _esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}
function _md(t){try{return marked.parse(t);}catch(e){return _esc(t);}}
function _scroll(){var cb=document.getElementById('chat-body');if(cb)cb.scrollTop=cb.scrollHeight;}
function addBubble(role,html){var cb=document.getElementById('chat-body');if(!cb)return null;
  var h=cb.querySelector('.chat-empty-hint');if(h)h.style.display='none';
  var d=document.createElement('div');d.className='msg '+role;d.innerHTML=html||'';cb.appendChild(d);_scroll();return d;}
function showThinking(){var cb=document.getElementById('chat-body');if(!cb)return;
  _thinker={el:document.createElement('div')};_thinker.el.className='thinking-indicator';
  _thinker.el.innerHTML='<span class="dot"></span> Thinking…';cb.appendChild(_thinker.el);_scroll();}
function hideThinking(){if(_thinker){if(_thinker.el.parentNode)_thinker.el.parentNode.removeChild(_thinker.el);_thinker=null;}}
async function streamChat(ev){if(ev&&ev.preventDefault)ev.preventDefault();if(_streaming)return false;
  var input=document.getElementById('chat-input');var msg=input?input.value.trim():'';if(!msg)return false;
  _streaming=true;var btn=document.getElementById('chat-send-btn');if(btn)btn.disabled=true;
  addBubble('user',_esc(msg));input.value='';
  var tid=(document.getElementById('thread-id')||{}).value||'';var bubble=null,acc='';showThinking();
  try{var resp=await fetch('/chat/stream',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:new URLSearchParams({message:msg,thread_id:tid})});
    if(!resp.ok){hideThinking();addBubble('assistant','Error: '+resp.status);_streaming=false;if(btn)btn.disabled=false;return false;}
    var reader=resp.body.getReader(),dec=new TextDecoder(),buf='';
    while(true){var r=await reader.read();if(r.done)break;buf+=dec.decode(r.value,{stream:true});
      var idx;while((idx=buf.indexOf('\\n\\n'))!==-1){var raw=buf.slice(0,idx);buf=buf.slice(idx+2);
        if(raw.indexOf('data: ')!==0)continue;var p={};try{p=JSON.parse(raw.slice(6));}catch(e){}
        if(p.token){if(acc===''){hideThinking();bubble=addBubble('assistant','');}acc+=p.token;bubble.innerHTML=_md(acc);_scroll();}
        else if(p.error){hideThinking();addBubble('assistant','⚠ '+p.error);}}}
  }catch(e){hideThinking();addBubble('assistant','⚠ '+e);}
  hideThinking();_streaming=false;if(btn)btn.disabled=false;return false;}
"""
