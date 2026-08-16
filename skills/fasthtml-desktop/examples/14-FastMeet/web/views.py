"""Center-pane renderers for FastMeet."""
from __future__ import annotations

from datetime import datetime

from fasthtml.common import (
    Div, H1, H3, P, Span, A, Form, Input, Textarea, Button, NotStr, Strong,
)

import db


def _title(title, sub="", *actions):
    return Div(Div(H1(title), P(sub, cls="sub") if sub else None),
               Div(*actions) if actions else None, cls="page-title")


def _pill(text, kind=""):
    return Span(text, cls="pill " + (kind or str(text)).lower().replace(" ", ""))


def _dt(ts):
    try:
        return datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _initials(name):
    parts = (name or "?").split()
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


def _meeting_row(m):
    dt = _dt(m["start_time"])
    day = dt.strftime("%d %b") if dt else "—"
    tm = dt.strftime("%H:%M") if dt else "—"
    live = m["status"] == "Live"
    rsvp_n = db.scalar("SELECT COUNT(*) FROM participants WHERE meeting_id=? AND rsvp='Accepted'", (m["id"],)) or 0
    right = []
    if live:
        right.append(_pill("● LIVE", "live"))
        right.append(A("Join", href=f"/room/{m['id']}", cls="btn live"))
    elif m["status"] == "Scheduled":
        right.append(_pill(m["status"]))
        right.append(A("Join", href=f"/room/{m['id']}", cls="btn primary"))
    else:
        right.append(_pill(m["status"]))
        if m["has_recording"]:
            right.append(Span("🎞 recording", style="font-size:12px;color:var(--text-mute);"))
    return Div(
        Div(Div(day, cls="d"), Div(tm, cls="t"), cls="time"),
        Div(Div(A(m["title"], href=f"/meeting/{m['id']}"), cls="title"),
            Div(f"{m['duration_min']} min · {rsvp_n} attending · host {m['host']}", cls="meta")),
        Div(*right, cls="right"), cls="mrow")


# ---------- dashboard -------------------------------------------------------

def dashboard():
    from web.layout import kpi_card
    st = db.stats()
    today = db.NOW.strftime("%Y-%m-%d")
    todays = db.rows("SELECT * FROM meetings WHERE start_time LIKE ? AND status!='Cancelled' ORDER BY start_time", (today + "%",))
    upcoming = [m for m in db.meetings("upcoming") if not m["start_time"].startswith(today)][:6]
    return (
        _title("Meetings Dashboard", "Your schedule at a glance — fully synthetic demo data.",
               A("＋ Schedule", href="/schedule", cls="btn primary")),
        Div(kpi_card("Today", st["today"], "meetings"),
            kpi_card("Upcoming", st["upcoming"], "scheduled"),
            kpi_card("Live now", st["live"], "in progress", tone="live" if st["live"] else ""),
            kpi_card("Recordings", st["recordings"], "available"), cls="kpi-grid"),
        Div(Div(H3("Today"), cls="card-header"),
            Div(*[_meeting_row(m) for m in todays] or [P("Nothing today.", style="color:var(--text-mute);")], cls="mlist"),
            cls="card"),
        Div(Div(H3("Coming up"), cls="card-header"),
            Div(*[_meeting_row(m) for m in upcoming] or [P("Nothing scheduled.", style="color:var(--text-mute);")], cls="mlist"),
            cls="card"),
    )


# ---------- meetings list ---------------------------------------------------

def meetings_list(scope="upcoming"):
    seg = Div(A("Upcoming", href="/meetings?scope=upcoming", cls="" + ("active" if scope == "upcoming" else "")),
              A("Past & Recordings", href="/meetings?scope=past", cls="" + ("active" if scope == "past" else "")),
              cls="seg")
    ms = db.meetings(scope)
    active = "upcoming" if scope == "upcoming" else "past"
    return (_title("Upcoming meetings" if scope == "upcoming" else "Past meetings & recordings", f"{len(ms)} meetings"),
            seg, Div(*[_meeting_row(m) for m in ms] or [P("Nothing here.", style="color:var(--text-mute);")], cls="mlist"))


# ---------- meeting detail --------------------------------------------------

def meeting_detail(mid):
    m = db.meeting(mid)
    if not m:
        return _title("Meeting not found"), P("No such meeting.")
    parts = db.participants(mid)
    dt = _dt(m["start_time"])
    live = m["status"] == "Live"

    join = (A("● Join live", href=f"/room/{mid}", cls="btn live") if live
            else (A("Join room", href=f"/room/{mid}", cls="btn primary") if m["status"] == "Scheduled" else None))

    info = Div(Div(H3("Details"), cls="card-header"),
               Div(Span("When", cls="k"), Span(dt.strftime("%A %d %b %Y, %H:%M") if dt else "—"),
                   Span("Duration", cls="k"), Span(f"{m['duration_min']} minutes"),
                   Span("Status", cls="k"), _pill("● LIVE" if live else m["status"], "live" if live else ""),
                   Span("Host", cls="k"), Span(m["host"]),
                   Span("Room code", cls="k"), Span(m["room_code"] or "—"),
                   Span("Recording", cls="k"), Span("Available 🎞" if m["has_recording"] else "—"),
                   cls="kv"), cls="card")
    agenda = Div(Div(H3("Agenda"),
                     Button("✨ Generate agenda", cls="btn",
                            **{"hx-post": f"/ai/agenda/{mid}", "hx-target": "#ai-panel", "hx-swap": "innerHTML"}),
                     cls="card-header"),
                 Div(id="ai-panel"),
                 Div(NotStr((m["agenda"] or "No agenda set.").replace("\n", "<br>")), cls="agenda"), cls="card")
    if m["summary"]:
        summary = Div(Div(H3("Summary"), cls="card-header"), Div(NotStr(m["summary"]), cls="agenda"), cls="card")
    elif m["status"] == "Ended":
        summary = Div(Div(H3("Summary"),
                          Button("✨ Summarise meeting", cls="btn",
                                 **{"hx-post": f"/ai/summary/{mid}", "hx-target": "#sum-panel", "hx-swap": "innerHTML"}),
                          cls="card-header"),
                      Div(id="sum-panel", style="margin-top:4px;"), cls="card")
    else:
        summary = None

    return (_title(m["title"], "", A("← Meetings", href="/meetings?scope=upcoming", cls="btn"), join),
            Div(Div(info, agenda, summary),
                Div(participants_card(mid), id="part-card"), cls="detail-grid"))


def participants_card(mid):
    parts = db.participants(mid)
    tally = db.rsvp_tally(mid)
    rsvp_opts = [("Accepted", "✓"), ("Tentative", "?"), ("Declined", "✕")]
    rows_ = []
    for p in parts:
        if p["role"] == "Host":
            right = _pill("Host")
        else:
            btns = [Button(sym, cls="btn xs" + (" primary" if p["rsvp"] == val else ""), title=val,
                           **{"hx-post": f"/rsvp/{p['id']}", "hx-vals": f'{{"rsvp":"{val}"}}',
                              "hx-target": "#part-card", "hx-swap": "innerHTML"}) for val, sym in rsvp_opts]
            right = Div(*btns, style="display:flex;gap:3px;")
        rows_.append(Div(Span(_initials(p["name"]), cls="avatar"),
                         Div(Div(p["name"], cls="nm"), Div(p["email"], cls="em")),
                         Div(right, style="margin-left:auto;"), cls="part-row"))
    tally_row = Div(_pill(f"{tally['Accepted']} attending", "accepted"),
                    _pill(f"{tally['Tentative']} tentative", "tentative"),
                    _pill(f"{tally['Declined']} declined", "declined"),
                    style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;")
    return Div(Div(H3(f"Participants ({len(parts)})"), cls="card-header"),
               tally_row, *rows_, cls="card")


# ---------- room ------------------------------------------------------------

def room_view(mid):
    from web import media
    m = db.meeting(mid)
    if not m:
        return _title("Meeting not found"), P("No such meeting.")
    parts = db.participants(mid)[:8]
    provider = media.active_provider()
    tiles = [Div(Div(_initials(p["name"]), cls="av"), Div(p["name"], cls="nm"), cls="vtile") for p in parts]
    return (_title(m["title"], f"Room {m['room_code']}", A("← Leave to details", href=f"/meeting/{mid}", cls="btn")),
            Div(NotStr(f"📡 <b>Live video.</b> This room embeds a real media layer "
                       f"(<b>{provider.title()}</b>) so it carries actual audio/video. Allow camera & mic when "
                       "prompted. Switch provider with <code>MEET_MEDIA_PROVIDER</code> in <code>.env</code>."),
                cls="notice"),
            Div(media.embed(m, parts[0]["name"] if parts else "You"), cls="stage"),
            Div(Div("Invited", style="font-weight:700;margin-bottom:8px;color:var(--text-dim);"),
                Div(*tiles, cls="tiles"), cls="card", style="margin-top:14px;"))


# ---------- schedule --------------------------------------------------------

def schedule_view(done_id=None, error=""):
    if done_id:
        m = db.meeting(done_id)
        return (_title("Meeting scheduled", ""),
                Div(f"✓ '{m['title']}' is on the calendar.", cls="notice"),
                Div(A("Open meeting", href=f"/meeting/{done_id}", cls="btn primary"),
                    A("Schedule another", href="/schedule", cls="btn"), style="display:flex;gap:8px;"))
    return (_title("Schedule a meeting", "Create a meeting and invite people."),
            Div(NotStr(f"<div class='notice'>⚠ {error}</div>") if error else "",
                Form(
                    Span("Title", style="font-size:11px;text-transform:uppercase;color:var(--text-mute);font-weight:600;"),
                    Input(name="title", placeholder="e.g. Project Kickoff", required=True),
                    NotStr("<label>Date & time</label>"),
                    Input(name="start", type="datetime-local"),
                    NotStr("<label>Duration (minutes)</label>"),
                    Input(name="duration", type="number", value="30"),
                    NotStr("<label>Invite (comma-separated emails)</label>"),
                    Input(name="invites", placeholder="priya@team.example, tom@team.example"),
                    NotStr("<label>Agenda (optional — or generate with AI after creating)</label>"),
                    Textarea("", name="agenda", placeholder="- Item 1\n- Item 2"),
                    Div(Button("Schedule", cls="btn primary", type="submit"),
                        A("Cancel", href="/", cls="btn"), style="margin-top:12px;display:flex;gap:8px;"),
                    method="post", action="/schedule"),
                cls="gen-card"))


def ai_panel(text):
    return Div(Div(Span("✨ AI", style="font-weight:700;"), style="margin-bottom:4px;"),
               NotStr(text), cls="ai-panel")
