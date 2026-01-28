import asyncio
import logging
import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

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

PENDING_TTL = 10   # seconds
# =========================================

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("JOIN-SYSTEM")

# ================= HTTP SERVER (RENDER FIX) =================
class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_http():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Health).serve_forever()

threading.Thread(target=run_http, daemon=True).start()
log.info("🌐 HTTP server started for Render")

# ================= TELEGRAM =================
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
    text = "✅ **Access Granted!**\n\nYou are eligible."
    buttons = [[Button.inline("🕵️‍♂️ Get Agent", b"get_agent")]]
    try:
        if edit:
            await event.edit(text, buttons=buttons)
        else:
            await event.reply(text, buttons=buttons)
    except:
        pass

async def show_join_page(event, edit=False):
    text = "👋 **Welcome!**\n\nPlease join the channel or send request."
    buttons = [
        [Button.url("🚀 Join Channel", CHANNEL_LINK)],
        [Button.inline("🔄 Verify Status", b"check_status")]
    ]
    try:
        if edit:
            await event.edit(text, buttons=buttons)
        else:
            await event.reply(text, buttons=buttons)
    except:
        pass

# ================= CORE LOGIC =================
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

        for importer in result.importers:
            if importer.user_id == user_id:
                LIVE_PENDING_CACHE[user_id] = time.time()
                return True

        return False
    except Exception as e:
        log.warning(f"Pending check failed: {e}")
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
                    log.info(f"🔔 Live Pending: {uid}")
        except:
            pass

# ================= BOT HANDLERS =================
@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    user_id = event.sender_id

    try:
        await bot.get_permissions(CHANNEL_ID, user_id)
        await show_agent_page(event)
        return
    except UserNotParticipantError:
        pass
    except:
        pass

    if await is_actually_pending(user_id):
        await show_agent_page(event)
    else:
        await show_join_page(event)

@bot.on(events.CallbackQuery(data=b"check_status"))
async def verify(event):
    user_id = event.sender_id

    try:
        await bot.get_permissions(CHANNEL_ID, user_id)
        await event.answer("✅ Verified", alert=True)
        await show_agent_page(event, edit=True)
        return
    except UserNotParticipantError:
        pass
    except:
        pass

    if await is_actually_pending(user_id):
        await event.answer("⏳ Request Pending", alert=True)
        await show_agent_page(event, edit=True)
    else:
        LIVE_PENDING_CACHE.pop(user_id, None)
        await event.answer("❌ Not joined", alert=True)
        await show_join_page(event, edit=True)

@bot.on(events.CallbackQuery(data=b"get_agent"))
async def agent(event):
    try:
        await event.answer("🔄 Connecting...", alert=True)
        await event.edit("🕵️‍♂️ **Agent Notified!**\n\nWe will contact you.")
    except:
        pass

# ================= MAIN =================
async def main():
    log.info("🔄 Starting userbot & bot...")
    await userbot.start()
    await bot.start(bot_token=BOT_TOKEN)

    try:
        entity = await userbot.get_entity(CHANNEL_ID)
        log.info(f"✅ Channel connected: {entity.title}")
    except Exception as e:
        log.warning(f"Userbot channel access issue: {e}")

    log.info("🚀 SYSTEM ONLINE (Render Ready)")
    await asyncio.gather(
        userbot.run_until_disconnected(),
        bot.run_until_disconnected()
    )

if __name__ == "__main__":
    asyncio.run(main())
