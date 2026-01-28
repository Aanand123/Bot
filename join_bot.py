# ================= RENDER PORT BIND (TOP) =================
import os
import threading
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
print("🌐 HTTP PORT READY")

# ================= MAIN IMPORTS =================
import asyncio
import time
from flask import Flask, request, jsonify

from telethon import TelegramClient, events
from telethon.tl.types import UpdatePendingJoinRequests
from telethon.tl.functions.messages import GetChatInviteImportersRequest

# ================= CONFIG =================
API_ID = 33618078
API_HASH = "db0e27743fc356d33be5293e91979a4c"

SESSION_NAME = "user_session"
CACHE_TTL = 10   # seconds
# =========================================

# ================= GLOBAL CACHE =================
# PENDING[channel_id][user_id] = timestamp
PENDING = {}

def norm(cid):
    cid = str(cid).strip()
    return cid if cid.startswith("-100") else "-100" + cid

def cleanup():
    now = time.time()
    for ch in list(PENDING.keys()):
        for u in list(PENDING[ch].keys()):
            if now - PENDING[ch][u] > CACHE_TTL:
                del PENDING[ch][u]
        if not PENDING[ch]:
            del PENDING[ch]

# ================= TELETHON =================
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.Raw)
async def on_pending(update):
    if isinstance(update, UpdatePendingJoinRequests):
        channel = norm(update.peer.channel_id)
        now = time.time()
        PENDING.setdefault(channel, {})
        for uid in update.recent_requesters:
            PENDING[channel][str(uid)] = now
            print(f"🟡 LIVE REQUEST | user={uid} channel={channel}")

# ================= FLASK API =================
app = Flask(__name__)

@app.route("/check")
def check():
    user = request.args.get("user", type=str)
    channel = request.args.get("channelid", type=str)

    if not user or not channel:
        return jsonify({
            "ok": False,
            "error": "user or channelid missing"
        }), 400

    user = user.strip()
    channel = norm(channel)

    cleanup()

    # 1️⃣ FAST CHECK (live cache)
    if channel in PENDING and user in PENDING[channel]:
        return jsonify({
            "ok": True,
            "requested": True,
            "source": "live"
        })

    # 2️⃣ SERVER CONFIRM (slow but accurate)
    async def server_check():
        try:
            entity = await client.get_entity(int(channel))
            result = await client(GetChatInviteImportersRequest(
                peer=entity,
                requested=True,
                limit=100
            ))
            for imp in result.importers:
                if str(imp.user_id) == user:
                    PENDING.setdefault(channel, {})[user] = time.time()
                    return True
        except Exception as e:
            print("⚠️ Server check error:", e)
        return False

    try:
        loop = asyncio.get_event_loop()
        requested = loop.run_until_complete(server_check())
    except RuntimeError:
        requested = asyncio.run(server_check())

    return jsonify({
        "ok": True,
        "requested": requested,
        "source": "server" if requested else "none"
    })

# ================= MAIN =================
async def main():
    await client.start()
    print("👤 TELEGRAM USER LOGGED IN")
    await client.run_until_disconnected()

def run_telethon():
    asyncio.run(main())

threading.Thread(target=run_telethon, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
