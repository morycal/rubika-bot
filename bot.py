import aiohttp
import asyncio
import os

TOKEN = os.getenv("RUBIKA_TOKEN")
BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

offset = None

# 🧠 QUEUE (خیلی مهم)
queue = asyncio.Queue()

# ⛔ فقط 1 sender همزمان
send_lock = asyncio.Lock()


# ---------------- SAFE SEND ----------------
async def send_message(session, chat_id, text):

    async with send_lock:

        try:
            async with session.post(
                f"{BASE_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text
                }
            ) as res:

                data = await res.text()
                print("SEND:", data)

                # ⛔ جلوگیری از flood
                await asyncio.sleep(0.8)

                return data

        except Exception as e:
            print("SEND ERROR:", e)


# ---------------- WORKER ----------------
async def worker(session):

    while True:

        chat_id, text = await queue.get()

        if text == "/start":
            await send_message(session, chat_id, "🤖 ربات روشن شد!")

        elif text == "سلام":
            await send_message(session, chat_id, "👋 سلام!")

        elif text == "کجایی":
            await send_message(session, chat_id, "📡 آنلاین هستم")

        else:
            await send_message(session, chat_id, "❓ دستور ناشناخته")

        queue.task_done()


# ---------------- GET UPDATES ----------------
async def get_updates(session):

    global offset

    seen = set()  # جلوگیری از duplicate

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

                uid = u.get("update_time")

                # ⛔ جلوگیری از تکرار
                if uid in seen:
                    continue

                seen.add(uid)

                offset = uid

                if u.get("type") != "NewMessage":
                    continue

                msg = u.get("new_message", {})

                chat_id = u.get("chat_id")
                text = msg.get("text", "")

                if chat_id and text:
                    await queue.put((chat_id, text))

        except Exception as e:
            print("LOOP ERROR:", e)
            await asyncio.sleep(2)

        await asyncio.sleep(0.8)


# ---------------- MAIN ----------------
async def main():

    print("🚀 ULTRA STABLE BOT STARTED")

    async with aiohttp.ClientSession() as session:

        asyncio.create_task(worker(session))
        await get_updates(session)


if __name__ == "__main__":
    asyncio.run(main())
