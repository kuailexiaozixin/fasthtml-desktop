# FastMeet Roadmap — Frappe Meet feature comparison

`frappe/meet` is a **WebRTC video-conferencing** app (only 3 doctypes —
`Sae Meeting`, `Sae Meeting User`, `Sae Settings`; the substance is the
real-time media client). FastMeet ports the **scheduling & rooms** half that a
server-rendered app *can* do well, and is explicit about the part it can't.

## Implemented ✅

| Capability | Upstream area | FastMeet |
|---|---|---|
| Meetings | `Sae Meeting` | `meetings` (title, time, duration, status, room) |
| Participants | `Sae Meeting User` | `participants` (role + RSVP) |
| Scheduling | create meeting | `/schedule` + invites |
| Room lobby | meeting room | `/room/{id}` with participant tiles + controls |
| Agendas | — | stored + **AI-generated** |
| Recordings / summaries | recording | metadata + **AI summaries** of past meetings |
| **AI assistant** | *(not upstream)* | schedule Q&A, agenda gen, summaries |

## Near-term roadmap 🔜

1. ✅ **RSVP actions** (done) — accept/decline/tentative per attendee; host sees a live tally
   (today RSVPs are read-only).
2. **Recurring meetings** + calendar (week/month) view.
3. **Availability / scheduling assistant** — find a free slot across invitees.
4. **Notifications & reminders** — "starts in 10 minutes".
5. **Action items** — extract owners/due-dates from the AI summary into a tracker.
6. **Recording playback** — attach a (synthetic) recording + transcript to past
   meetings; let the AI answer questions over the transcript.

## The big one — live video ✅ (implemented via media embed)

Frappe Meet's core is **WebRTC**: peer media, SFU/TURN, screen share, live audio.
A FastHTML app can't carry WebRTC itself, so the room **embeds** a real media layer
(`web/media.py`). Implemented:

- **LiveKit** / **Jitsi** / **Daily** room embedded in `/room/{id}`, with FastMeet
  owning scheduling, identity, agendas, recordings and summaries around it; or
- a thin WebRTC client (vanilla JS + a signalling WebSocket) mounted only on the
  room page.

Everything else FastMeet already does is the **server-side** half such an
integration needs.

## Design notes

FastMeet deliberately builds the schedule/rooms/agenda/summary surface — the part
that's a great fit for server-rendered HTMX — and is honest in the room view that
live media needs a dedicated layer. The AI agenda/summary features (per-meeting,
swapped via HTMX) are the differentiator versus a plain calendar.
