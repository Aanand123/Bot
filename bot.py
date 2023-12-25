import logging
from telegram import Update, ChatPermissions
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = 'YOUR_BOT_TOKEN'

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Function to ban a user from the channel
def ban_user(chat_id, user_id):
    permissions = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
        can_change_info=False,
        can_invite_users=False,
        can_pin_messages=False
    )
    context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=permissions)

# Handler for 'left chat member' event
def handle_left_chat_member(update: Update, context: CallbackContext):
    if update.message.left_chat_member:
        user_id = update.message.left_chat_member.id
        chat_id = update.effective_chat.id
        
        ban_user(chat_id, user_id)
        update.message.reply_text(f"User {user_id} has been banned.")

left_chat_member_handler = MessageHandler(Filters.status_update.left_chat_member, handle_left_chat_member)
dispatcher.add_handler(left_chat_member_handler)

updater.start_polling()
￼Enter
