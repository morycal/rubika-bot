import aiohttp
import asyncio
import os

TOKEN = os.getenv("RUBIKA_TOKEN")

if not TOKEN:
    raise Exception("RUBIKA_TOKEN is not set!")

BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

offset = None


# ---------------- SEND MESSAGE (RELIABLE) ----------------
async def send_message(session, chat_id, text):

    payload = {
        "chat_id": chat_id,
        "peer_id": chat_id,   # fallback 1
        "text": text
    }

    for attempt in range(3):  # retry system
        try:
            async with session.post(
                f"{BASE_URL}/sendMessage",
                json=payload
            ) as res:

                data = await res.text()
                print(f"[SEND attempt {attempt+1}] {data}")

                if "OK" in data:
                    return True

                # اگر TOO_REQUESTS شد صبر کن
                if "TOO_REQUESTS" in data:
                    await asyncio.sleep(1.5)

        except Exception as e:
            print("SEND ERROR:", e)

        await asyncio.sleep(0.5)

    return False


# ---------------- HANDLE MESSAGE ----------------
async def handle_message(session, chat_id, text):

    text = text.strip()
    print("USER:", text)

    if text == "/start":
        await send_message(session, chat_id, "🤖 ربات روشن شد!")

    elif text == "سلام":
        await send_message(session, chat_id, "👋 سلام!")

    elif text == "ping":
        await send_message(session, chat_id, "pong 🟢")

    else:
        await send_message(session, chat_id, "❓ دستور ناشناخته")


# ---------------- UPDATE LOOP ----------------
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

            for u in updates:

                offset = u.get("update_time", offset)

                if u.get("type") != "NewMessage":
                    continue

                msg = u.get("new_message", {})

                text = msg.get("text", "")

                # 🔥 بهترین شناسه موجود
                chat_id = (
                    msg.get("sender_id")
                    or u.get("chat_id")
                )

                if not chat_id:
                    continue

                await handle_message(session, chat_id, text)

        except Exception as e:
            print("LOOP ERROR:", e)
            await asyncio.sleep(2)

        await asyncio.sleep(0.8)


# ---------------- MAIN ----------------
async def main():
    print("🚀 Reliable Bot Started")

    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        await get_updates(session)


if __name__ == "__main__":
    asyncio.run(main())
