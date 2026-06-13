import aiohttp
import asyncio
import os
import time

TOKEN = os.getenv("RUBIKA_TOKEN")

BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

offset = None

# ⛔ کنترل سرعت جهانی
last_send_time = 0


# ---------------- SAFE SEND ----------------
async def send_message(session, chat_id, text):

    global last_send_time

    # ⛔ حداقل فاصله بین پیام‌ها
    now = time.time()
    wait = 0.7 - (now - last_send_time)

    if wait > 0:
        await asyncio.sleep(wait)

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        async with session.post(
            f"{BASE_URL}/sendMessage",
            json=payload
        ) as res:

            data = await res.text()
            print("SEND:", data)

            last_send_time = time.time()

            # اگر TOO_REQUESTS شد صبر بیشتر
            if "TOO_REQUESTS" in data:
                await asyncio.sleep(2)

            return data

    except Exception as e:
        print("SEND ERROR:", e)


# ---------------- HANDLE ----------------
async def handle_message(session, chat_id, text):

    text = text.strip()
    print("USER:", text)

    if text == "/start":
        await send_message(session, chat_id, "🤖 ربات روشن شد!")

    elif text == "سلام":
        await send_message(session, chat_id, "👋 سلام!")

    elif text == "کجایی":
        await send_message(session, chat_id, "📡 آنلاین هستم")

    else:
        await send_message(session, chat_id, "❓ دستور ناشناخته")


# ---------------- LOOP ----------------
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

                chat_id = update.get("chat_id")

                text = msg.get("text", "")

                if not chat_id:
                    continue

                await handle_message(session, chat_id, text)

        except Exception as e:
            print("LOOP ERROR:", e)
            await asyncio.sleep(2)

        await asyncio.sleep(0.8)


async def main():
    print("🚀 Stable Bot Started")

    async with aiohttp.ClientSession() as session:
        await get_updates(session)


if __name__ == "__main__":
    asyncio.run(main())
