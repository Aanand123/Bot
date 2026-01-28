# ================= RENDER PORT FIX =================
import os, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_http():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Health).serve_forever()

threading.Thread(target=start_http, daemon=True).start()
print("🌐 PORT READY")

# ================= IMPORTS =================
import asyncio, time
from flask import Flask, request, Response
from telethon import TelegramClient, events
from telethon.tl.types import UpdatePendingJoinRequests
from telethon.tl.functions.messages import GetChatInviteImportersRequest

# ================= CONFIG =================
API_ID = 33618078
API_HASH = "db0e27743fc356d33be5293e91979a4c"
SESSION = "user_session"
CACHE_TTL = 10
# =========================================

# channel → { user : timestamp }
PENDING = {}

def norm(cid):
    cid = str(cid).strip()
    return cid if cid.startswith("-100") else "-100" + cid

def cleanup():
    now = time.time()
    for ch in list(PENDING):
        for u in list(PENDING[ch]):
            if now - PENDING[ch][u] > CACHE_TTL:
                del PENDING[ch][u]
        if not PENDING[ch]:
            del PENDING[ch]

client = TelegramClient(SESSION, API_ID, API_HASH)

# ================= LIVE LISTENER =================
@client.on(events.Raw)
async def on_raw(update):
    if isinstance(update, UpdatePendingJoinRequests):
        ch = norm(update.peer.channel_id)
        PENDING.setdefault(ch, {})
        for uid in update.recent_requesters:
            PENDING[ch][str(uid)] = time.time()
            print(f"PENDING | {uid} | {ch}")

# ================= FLASK API =================
app = Flask(__name__)

@app.route("/check")
def check():
    user = request.args.get("user")
    channel = request.args.get("channelid")

    if not user or not channel:
        return Response("false", mimetype="text/plain")

    user = user.strip()
    channel = norm(channel)
    cleanup()

    # FAST CACHE CHECK
    if channel in PENDING and user in PENDING[channel]:
        return Response("true", mimetype="text/plain")

    # SERVER CONFIRM
    async def server_check():
        try:
            entity = await client.get_entity(int(channel))
            res = await client(GetChatInviteImportersRequest(
                peer=entity,
                requested=True,
                limit=100
            ))
            for r in res.importers:
                if str(r.user_id) == user:
                    PENDING.setdefault(channel, {})[user] = time.time()
                    return True
        except:
            pass
        return False

    try:
        loop = asyncio.get_event_loop()
        ok = loop.run_until_complete(server_check())
    except RuntimeError:
        ok = asyncio.run(server_check())

    return Response("true" if ok else "false", mimetype="text/plain")

# ================= MAIN =================
async def main():
    await client.start()
    print("👤 USER LOGGED IN")
    await client.run_until_disconnected()

threading.Thread(target=lambda: asyncio.run(main()), daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
