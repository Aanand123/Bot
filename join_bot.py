import asyncio
import logging
from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import GetChatInviteImportersRequest
from telethon.tl.types import UpdatePendingJoinRequests
from telethon.errors import UserNotParticipantError

# ==========================================
# 👇 BAS YAHAN APNI DETAILS BHAR DO 👇
# ==========================================

API_ID = 33618078                   # Apni ASLI API ID
API_HASH = "db0e27743fc356d33be5293e91979a4c"  # Apna ASLI API HASH
BOT_TOKEN = "8218412333:AAFIcvY2eiAKl5Xtzd4lvVhkLVOBlHH-o2c"
CHANNEL_ID = -1001661832857   # <--- YAHAN SAHI CHANNEL ID DAALO
CHANNEL_LINK = "https://t.me/+EFAM9Cl41QgyNDVl"

# ==========================================

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Live Cache (Turant pakadne ke liye)
LIVE_PENDING_CACHE = set()

print("🚀 System Initializing...")

try:
    userbot = TelegramClient("user_session", API_ID, API_HASH)
    bot = TelegramClient("bot_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
except Exception as e:
    print(f"\n❌ ERROR: Details galat hain!\nError: {e}")
    exit()

# --- HELPER FUNCTIONS ---

async def show_agent_page(event, edit=False):
    """Page 2: Access Granted"""
    text = "✅ **Access Granted!**\n\nAap eligible hain. Agent se connect karne ke liye neeche click karein."
    buttons = [[Button.inline("🕵️‍♂️ Get Agent", data="get_agent")]]
    if edit: await event.edit(text, buttons=buttons)
    else: await event.reply(text, buttons=buttons)

async def show_join_page(event, edit=False):
    """Page 1: Join First"""
    text = "👋 **Welcome!**\n\nAage badhne ke liye pehle Channel Join karein ya Request bhejein."
    buttons = [
        [Button.url("🚀 Join Channel First", url=CHANNEL_LINK)],
        [Button.inline("Verify Status 🔄", data="check_status")]
    ]
    if edit: await event.edit(text, buttons=buttons)
    else: await event.reply(text, buttons=buttons)

async def is_actually_pending(user_id):
    """
    Server se confirm karta hai ki request asli me hai ya nahi.
    Debug prints add kiye hain taaki pata chale error kahan hai.
    """
    # 1. Pehle Live Cache check karo (Fastest)
    if user_id in LIVE_PENDING_CACHE:
        return True

    # 2. Agar Cache me nahi hai, to Server se pucho (Slow but Accurate)
    try:
        # Channel Entity ko resolve karo taaki connection fresh ho
        entity = await userbot.get_entity(CHANNEL_ID)
        
        # Pending List Mangwao
        result = await userbot(GetChatInviteImportersRequest(
            peer=entity,
            requested=True,
            limit=100
        ))
        
        # Console me print karo ki script ko kya dikha (Debugging ke liye)
        print(f"🔍 Checking Server: Found {len(result.importers)} total pending requests.")
        
        for importer in result.importers:
            if importer.user_id == user_id:
                print(f"✅ User {user_id} found in Server List!")
                LIVE_PENDING_CACHE.add(user_id) # Cache update kar do
                return True
                
        print(f"❌ User {user_id} NOT found in Server List.")
        return False

    except Exception as e:
        print(f"⚠️ Error reading pending list: {e}")
        # Agar error aaye (jaise permission nahi hai), to fail maano
        return False

# --- USERBOT SPY (Live Listener) ---
@userbot.on(events.Raw)
async def on_raw_event(event):
    """Jab koi banda request bhejta hai, turant note kar lo"""
    if isinstance(event, UpdatePendingJoinRequests):
        try:
            # Channel ID Check (clean format)
            clean_id = int(str(CHANNEL_ID).replace("-100", ""))
            if event.peer.channel_id == clean_id:
                for uid in event.recent_requesters:
                    LIVE_PENDING_CACHE.add(uid)
                    print(f"🔔 Live Request Detected: User {uid}")
        except Exception:
            pass

# --- BOT LOGIC ---

@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    user_id = event.sender_id
    
    # 1. Member Check
    try:
        await bot.get_permissions(CHANNEL_ID, user_id)
        await show_agent_page(event)
        return
    except UserNotParticipantError:
        pass # Not a member
    except Exception:
        pass

    # 2. Pending Check
    if await is_actually_pending(user_id):
        await show_agent_page(event)
    else:
        await show_join_page(event)

@bot.on(events.CallbackQuery(data="check_status"))
async def verify_callback(event):
    user_id = event.sender_id

    # 1. Member Check
    try:
        await bot.get_permissions(CHANNEL_ID, user_id)
        await event.answer("✅ Verified!", alert=True)
        await show_agent_page(event, edit=True)
        return
    except UserNotParticipantError:
        pass

    # 2. Pending Check
    if await is_actually_pending(user_id):
        await event.answer("✅ Request Pending Found!", alert=True)
        await show_agent_page(event, edit=True)
    else:
        # Agar Server list me nahi mila, to Cache se bhi hata do (Clean up)
        if user_id in LIVE_PENDING_CACHE:
            LIVE_PENDING_CACHE.remove(user_id)
            
        await event.answer("❌ Request nahi mili! Dobara Join karein.", alert=True)
        await show_join_page(event, edit=True)

@bot.on(events.CallbackQuery(data="get_agent"))
async def agent_callback(event):
    await event.answer("🔄 Connecting...", alert=True)
    await event.edit("🕵️‍♂️ **Agent Notified!**\n\nHum aapse jaldi hi contact karenge.")

# --- MAIN LOOP ---

async def main():
    print("\n🔄 Connecting Userbot & Bot...")
    await userbot.start()
    
    # Permission Check at Startup
    try:
        entity = await userbot.get_entity(CHANNEL_ID)
        print(f"✅ Connected to Channel: {entity.title}")
    except Exception as e:
        print(f"⚠️ WARNING: Userbot Channel access nahi kar pa raha!\nReason: {e}")
        print("Make sure Userbot is ADMIN in the channel.")

    print("\n✅ SYSTEM ONLINE!")
    print("---------------------------------------")
    
    await asyncio.gather(
        userbot.run_until_disconnected(),
        bot.run_until_disconnected()
    )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
