import aiohttp
import asyncio
import os

TOKEN = os.getenv("RUBIKA_TOKEN")

if not TOKEN:
    raise Exception("RUBIKA_TOKEN is not set!")

BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

offset = None


# ---------------- SEND MESSAGE ----------------
async def send_message(session, chat_id, text):
    try:
        payload = {
            "chat_id": str(chat_id),
            "text": str(text)
        }

        async with session.post(
            f"{BASE_URL}/sendMessage",
            json=payload
        ) as res:

            data = await res.text()

            print("SEND RESPONSE:", data)

            # جلوگیری از rate limit
            await asyncio.sleep(0.4)

    except Exception as e:
        print("SEND ERROR:", e)


# ---------------- HANDLE MESSAGE ----------------
async def handle_message(session, chat_id, text):

    text = text.strip()
    print("USER:", text)
    print("CHAT:", chat_id)

    if text == "/start":
        await send_message(session, chat_id, "🤖 ربات روشن شد!")

    elif text == "سلام":
        await send_message(session, chat_id, "👋 سلام! خوش اومدی")

    elif text == "کجایی":
        await send_message(session, chat_id, "📡 آنلاین روی سرور")

    else:
        await send_message(session, chat_id, "❓ دستور ناشناخته")


# ---------------- GET UPDATES ----------------
async def get_updates(session):

    global offset

    while True:
        try:
            payload = {}

            if offset:
                payload["offset_id"] = offset

            async with session.post(
                f"{BASE_URL}/getUpdates",
                json=payload
            ) as res:

                data = await res.json()

            if data.get("status") != "OK":
                await asyncio.sleep(1)
                continue

            updates = data["data"]["updates"]

            for update in updates:

                offset = update.get("update_time", offset)

                if update.get("type") != "NewMessage":
                    continue

                msg = update.get("new_message", {})

                text = msg.get("text", "")

                # ✅ فقط chat_id واقعی
                chat_id = update.get("chat_id")

                if not chat_id:
                    continue

                await handle_message(session, chat_id, text)

        except Exception as e:
            print("LOOP ERROR:", e)
            await asyncio.sleep(2)

        await asyncio.sleep(0.8)


# ---------------- MAIN ----------------
async def main():
    print("🚀 Bot Started (Fixed Version)")

    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        await get_updates(session)


if __name__ == "__main__":
    asyncio.run(main())
