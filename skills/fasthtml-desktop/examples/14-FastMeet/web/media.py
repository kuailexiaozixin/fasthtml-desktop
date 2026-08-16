"""Live-video media layer for the FastMeet room.

A server-rendered HTML app can't carry WebRTC itself, so the room **embeds** a
real media provider. Two are supported via ``MEET_MEDIA_PROVIDER``:

  * ``jitsi`` (default) — embeds a Jitsi Meet room via its External API. Works
    out of the box against the public ``meet.jit.si`` (no account, no tokens),
    so the room carries real audio/video immediately.
  * ``livekit`` — embeds a LiveKit room. Requires ``LIVEKIT_URL`` plus
    ``LIVEKIT_API_KEY`` / ``LIVEKIT_API_SECRET`` to mint an access token
    server-side (see ``livekit_token``); falls back to Jitsi if unconfigured.
"""
from __future__ import annotations

import json
import os
import re

from fasthtml.common import NotStr

PROVIDER = os.getenv("MEET_MEDIA_PROVIDER", "jitsi").lower()
JITSI_DOMAIN = os.getenv("JITSI_DOMAIN", "meet.jit.si")
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")


def _slug(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", (s or "room")).strip("-")


def room_identifier(meeting: dict) -> str:
    """A stable, namespaced room name unique to this FastMeet meeting."""
    return f"FastMeet-{_slug(meeting.get('room_code') or '')}-{meeting['id']}"


def active_provider() -> str:
    if PROVIDER == "livekit" and LIVEKIT_URL and LIVEKIT_API_KEY and LIVEKIT_API_SECRET:
        return "livekit"
    return "jitsi"


def embed(meeting: dict, display_name: str = "You"):
    """Return an FT fragment that mounts a live video room (or a graceful note)."""
    room = room_identifier(meeting)
    if active_provider() == "livekit":
        return _livekit_embed(meeting, room, display_name)
    return _jitsi_embed(room, display_name)


# --- Jitsi ------------------------------------------------------------------

def _jitsi_embed(room: str, display_name: str):
    js = f"""
(function(){{
  function mount(){{
    try{{
      window._jitsi = new JitsiMeetExternalAPI({JITSI_DOMAIN!r}, {{
        roomName: {room!r},
        parentNode: document.getElementById('media-room'),
        width: '100%', height: 560,
        userInfo: {{ displayName: {display_name!r} }},
        configOverwrite: {{ prejoinPageEnabled: true, startWithAudioMuted: true, startWithVideoMuted: true }},
        interfaceConfigOverwrite: {{ MOBILE_APP_PROMO: false }}
      }});
    }}catch(e){{
      document.getElementById('media-room').innerHTML =
        '<div class=media-fallback>Live video needs a connection to {JITSI_DOMAIN}. '+
        '(Provider: Jitsi — no account needed.)</div>';
    }}
  }}
  var s=document.createElement('script');
  s.src='https://{JITSI_DOMAIN}/external_api.js';
  s.onload=mount;
  s.onerror=function(){{document.getElementById('media-room').innerHTML=
    '<div class=media-fallback>Could not load the Jitsi client (offline?).</div>';}};
  document.head.appendChild(s);
}})();
"""
    return NotStr(
        f'<div id="media-room" class="media-room"></div>'
        f'<div class="media-by">Live video via <b>Jitsi</b> · room <code>{room}</code></div>'
        f'<script>{js}</script>')


# --- LiveKit ----------------------------------------------------------------

def livekit_token(room: str, identity: str, name: str) -> str | None:
    """Mint a LiveKit access JWT (needs the ``livekit-api`` package + creds)."""
    if not (LIVEKIT_API_KEY and LIVEKIT_API_SECRET):
        return None
    try:
        from livekit import api  # type: ignore
    except Exception:
        return None
    grant = api.VideoGrants(room_join=True, room=room)
    return (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(identity).with_name(name).with_grants(grant).to_jwt())


def _livekit_embed(meeting: dict, room: str, display_name: str):
    token = livekit_token(room, f"u-{meeting['id']}", display_name)
    if not token:
        # creds present in env but token minting failed → fall back to Jitsi
        return _jitsi_embed(room, display_name)
    spec = json.dumps({"url": LIVEKIT_URL, "token": token})
    js = f"""
(function(){{
  var cfg={spec};
  function mount(){{
    var room=new LivekitClient.Room({{adaptiveStream:true,dynacast:true}});
    var el=document.getElementById('media-room');
    room.on(LivekitClient.RoomEvent.TrackSubscribed,function(track){{
      if(track.kind==='video'||track.kind==='audio'){{el.appendChild(track.attach());}}
    }});
    room.connect(cfg.url,cfg.token).then(function(){{
      return room.localParticipant.enableCameraAndMicrophone();
    }}).catch(function(e){{el.innerHTML='<div class=media-fallback>LiveKit connect failed: '+e+'</div>';}});
  }}
  var s=document.createElement('script');
  s.src='https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.umd.min.js';
  s.onload=mount; document.head.appendChild(s);
}})();
"""
    return NotStr(
        f'<div id="media-room" class="media-room"></div>'
        f'<div class="media-by">Live video via <b>LiveKit</b> · room <code>{room}</code></div>'
        f'<script>{js}</script>')
