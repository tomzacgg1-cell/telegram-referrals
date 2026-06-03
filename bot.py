import os
import requests

from telegram import Update
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


async def member_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    invite = update.chat_member.invite_link

    if not invite:
        return

    user = update.chat_member.new_chat_member.user

    payload = {
        "telegram_user_id": user.id,
        "username": user.username,
        "invite_link_name": invite.name,
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/referrals",
        headers=supabase_headers(),
        json=payload,
        timeout=10,
    )

    print("Supabase insert:", response.status_code, response.text)
    print(f"{user.username} joined via {invite.name}")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/referrals",
        headers=supabase_headers(),
        params={
            "invite_link_name": f"eq.{username}",
            "select": "*",
        },
        timeout=10,
    )

    data = response.json()
    count = len(data)

    await update.message.reply_text(
        f"You have {count} referrals"
    )


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/referrals",
        headers=supabase_headers(),
        params={
            "select": "invite_link_name",
        },
        timeout=10,
    )

    data = response.json()

    counts = {}

    for row in data:
        name = row.get("invite_link_name") or "Unknown"
        counts[name] = counts.get(name, 0) + 1

    sorted_counts = sorted(
        counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    if not sorted_counts:
        await update.message.reply_text("No referrals yet.")
        return

    message = "Leaderboard:\n\n"

    for index, (name, count) in enumerate(sorted_counts, start=1):
        message += f"{index}. {name} - {count}\n"

    await update.message.reply_text(message)


app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(
    ChatMemberHandler(
        member_join,
        ChatMemberHandler.CHAT_MEMBER,
    )
)

app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("leaderboard", leaderboard))

app.run_polling()
