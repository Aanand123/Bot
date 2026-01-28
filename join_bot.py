# ================= RENDER PORT FIX (TOP PE HI HONA CHAHIYE) =================
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

threading.Thread(target=start_http_server, daemon=True).start()
print("🌐 HTTP PORT BOUND FOR RENDER")

# ================= NORMAL BOT CODE BELOW =================
import asyncio
import logging
import time
from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import GetChatInviteImportersRequest
from telethon.tl.types import UpdatePendingJoinRequests
from telethon.errors import UserNotParticipantError

# ================= CONFIG =================
API_ID = 33618078
API_HASH = "db0e27743fc356d33be5293e91979a4c"

BOT_TOKEN = "8218412333:AAFIcvY2eiAKl5Xtzd4lvVhkLVOBlHH-o2c"

CHANNEL_ID = -1001661832857
CHANNEL_LINK = "https://t.me/+EFAM9Cl41QgyNDVl"

PENDING_TTL = 10
# =========================================

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("JOIN-SYSTEM")

# ================= TELEGRAM CLIENTS =================
userbot = TelegramClient("user_session", API_ID, API_HASH)
bot = TelegramClient("bot_session", API_ID, API_HASH)

# LIVE CACHE { user_id : timestamp }
LIVE_PENDING_CACHE = {}

def clean_cache():
    now = time.time()
    for uid in list(LIVE_PENDING_CACHE.keys()):
        if now - LIVE_PENDING_CACHE[uid] > PENDING_TTL:
            del LIVE_PENDING_CACHE[uid]

# ================= UI =================
async def show_agent_page(event, edit=False):
    text = "✅ **Access Granted!**"
    buttons = [[Button.inline("🕵️‍♂️ Get Agent", b"get_agent")]]
    try:
        if edit:
            await event.edit(text, buttons=buttons)
        else:
            await event.reply(text, buttons=buttons)
    except:
        pass

async def show_join_page(event, edit=False):
    text = "👋 **Please join the channel first**"
    buttons = [
        [Button.url("🚀 Join Channel", CHANNEL_LINK)],
        [Button.inline("🔄 Verify", b"check_status")]
    ]
    try:
        if edit:
            await event.edit(text, buttons=buttons)
        else:
            await event.reply(text, buttons=buttons)
    except:
        pass

# ================= CORE =================
async def is_actually_pending(user_id):
    clean_cache()

    if user_id in LIVE_PENDING_CACHE:
        return True

    try:
        entity = await userbot.get_entity(CHANNEL_ID)
        result = await userbot(GetChatInviteImportersRequest(
            peer=entity,
            requested=True,
            limit=100
        ))

        for imp in result.importers:
            if imp.user_id == user_id:
                LIVE_PENDING_CACHE[user_id] = time.time()
                return True
        return False
    except Exception as e:
        log.warning(f"Pending check error: {e}")
        return False

# ================= USERBOT LISTENER =================
@userbot.on(events.Raw)
async def on_raw(event):
    if isinstance(event, UpdatePendingJoinRequests):
        try:
            clean_id = int(str(CHANNEL_ID).replace("-100", ""))
            if event.peer.channel_id == clean_id:
                for uid in event.recent_requesters:
                    LIVE_PENDING_CACHE[uid] = time.time()
                    log.info(f"PENDING {uid}")
        except:
            pass

# ================= BOT HANDLERS =================
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    uid = event.sender_id

    try:
        await bot.get_permissions(CHANNEL_ID, uid)
        await show_agent_page(event)
        return
    except UserNotParticipantError:
        pass
    except:
        pass

    if await is_actually_pending(uid):
        await show_agent_page(event)
    else:
        await show_join_page(event)

@bot.on(events.CallbackQuery(data=b"check_status"))
async def verify(event):
    uid = event.sender_id

    try:
        await bot.get_permissions(CHANNEL_ID, uid)
        await event.answer("✅ Verified", alert=True)
        await show_agent_page(event, edit=True)
        return
    except UserNotParticipantError:
        pass
    except:
        pass

    if await is_actually_pending(uid):
        await event.answer("⏳ Pending", alert=True)
        await show_agent_page(event, edit=True)
    else:
        LIVE_PENDING_CACHE.pop(uid, None)
        await event.answer("❌ Not joined", alert=True)
        await show_join_page(event, edit=True)

@bot.on(events.CallbackQuery(data=b"get_agent"))
async def agent(event):
    try:
        await event.answer("Connecting...", alert=True)
        await event.edit("🕵️‍♂️ Agent will contact you soon.")
    except:
        pass

# ================= MAIN =================
async def main():
    log.info("Starting Telegram clients...")
    await userbot.start()
    await bot.start(bot_token=BOT_TOKEN)

    log.info("SYSTEM ONLINE (RENDER FIXED)")
    await asyncio.gather(
        userbot.run_until_disconnected(),
        bot.run_until_disconnected()
    )

if __name__ == "__main__":
    asyncio.run(main())
