from telegram import Update
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes
)

from supabase import create_client
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

async def member_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    invite = update.chat_member.invite_link

    if not invite:
        return

    user = update.chat_member.new_chat_member.user

    supabase.table("referrals").insert({
        "telegram_user_id": user.id,
        "username": user.username,
        "invite_link_name": invite.name
    }).execute()

    print(
        f"{user.username} joined via {invite.name}"
    )

async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    username = update.effective_user.username

    result = (
        supabase
        .table("referrals")
        .select("*")
        .eq("invite_link_name", username)
        .execute()
    )

    count = len(result.data)

    await update.message.reply_text(
        f"You have {count} referrals"
    )

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)

app.add_handler(
    ChatMemberHandler(
        member_join,
        ChatMemberHandler.CHAT_MEMBER
    )
)

app.add_handler(
    CommandHandler(
        "stats",
        stats
    )
)

app.run_polling()
