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
    print("JOIN EVENT RECEIVED", flush=True)

    try:
        invite = update.chat_member.invite_link

        if not invite:
            print("NO INVITE LINK FOUND", flush=True)
            return

        print(f"Invite name: {invite.name}", flush=True)
        print(f"Invite link: {invite.invite_link}", flush=True)

        user = update.chat_member.new_chat_member.user

        print(
            f"User joined: {user.id} @{user.username}",
            flush=True
        )

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

        print(
            "Supabase insert:",
            response.status_code,
            response.text,
            flush=True,
        )

    except Exception as e:
        print("ERROR:", str(e), flush=True)


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

    await update.message.reply_text(
        f"You have {len(data)} referrals"
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
        key=lambda x: x[1],
        reverse=True,
    )

    if not sorted_counts:
        await update.message.reply_text(
            "No referrals yet."
        )
        return

    message = "🏆 Leaderboard\n\n"

    for i, (name, count) in enumerate(
        sorted_counts,
        start=1,
    ):
        message += f"{i}. {name} - {count}\n"

    await update.message.reply_text(message)


print("BOT STARTING...", flush=True)

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)

app.add_handler(
    ChatMemberHandler(
        member_join,
        ChatMemberHandler.CHAT_MEMBER | ChatMemberHandler.MY_CHAT_MEMBER,
    )
)


app.add_handler(
    CommandHandler(
        "stats",
        stats,
    )
)

app.add_handler(
    CommandHandler(
        "leaderboard",
        leaderboard,
    )
)

print("BOT RUNNING...", flush=True)

app.run_polling()
