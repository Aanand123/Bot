import os
import asyncio
import time
from flask import Flask, request, Response

from telethon import TelegramClient, events
from telethon.tl.types import UpdatePendingJoinRequests
from telethon.tl.functions.messages import GetChatInviteImportersRequest

# ================= CONFIG =================
API_ID = 33618078
API_HASH = "db0e27743fc356d33be5293e91979a4c"
SESSION = "user_session"

CACHE_TTL = 600  # 10 minutes
PORT = int(os.environ.get("PORT", 10000))
# =========================================

app = Flask(__name__)

# channel -> { user : timestamp }
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

# ================= TELETHON =================
client = TelegramClient(SESSION, API_ID, API_HASH)

@client.on(events.Raw)
async def on_raw(update):
    if isinstance(update, UpdatePendingJoinRequests):
        ch = norm(update.peer.channel_id)
        PENDING.setdefault(ch, {})
        for uid in update.recent_requesters:
            PENDING[ch][str(uid)] = time.time()
            print(f"🟡 REQUEST CACHED | user={uid} channel={ch}")

# ================= ROUTES =================

@app.route("/")
def root():
    return "API RUNNING", 200

@app.route("/check")
def check():
    user = request.args.get("user")
    channel = request.args.get("channelid")

    if not user or not channel:
        return Response("false", mimetype="text/plain")

    user = user.strip()
    channel = norm(channel)
    cleanup()

    # 1️⃣ CACHE CHECK (10 min memory)
    if channel in PENDING and user in PENDING[channel]:
        return Response("true", mimetype="text/plain")

    # 2️⃣ SERVER CONFIRM
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
        except Exception as e:
            print("⚠️ server error:", e)
        return False

    try:
        loop = asyncio.get_event_loop()
        ok = loop.run_until_complete(server_check())
    except RuntimeError:
        ok = asyncio.run(server_check())

    return Response("true" if ok else "false", mimetype="text/plain")

# ================= START =================

async def start_telethon():
    await client.start()
    print("👤 TELEGRAM USER LOGGED IN")
    await client.run_until_disconnected()

import threading
threading.Thread(target=lambda: asyncio.run(start_telethon()), daemon=True).start()

if __name__ == "__main__":
    print("🌐 Flask listening on port", PORT)
    app.run(host="0.0.0.0", port=PORT)
