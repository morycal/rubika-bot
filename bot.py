import aiohttp
import asyncio
import os
import time

TOKEN = os.getenv("RUBIKA_TOKEN")
BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

offset = None

queue = asyncio.Queue()

last_send = 0


# ---------------- SAFE SEND (GLOBAL LIMIT) ----------------
async def send_message(session, chat_id, text):

    global last_send

    # ⛔ GLOBAL RATE LIMIT (خیلی مهم)
    now = time.time()
    wait = 1.3 - (now - last_send)

    if wait > 0:
        await asyncio.sleep(wait)

    for attempt in range(3):

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

                last_send = time.time()

                if "TOO_REQUESTS" in data:
                    await asyncio.sleep(2.5)
                    continue

                return

        except Exception as e:
            print("SEND ERROR:", e)

        await asyncio.sleep(1)


# ---------------- WORKER ----------------
async def worker(session):

    while True:

        chat_id, text = await queue.get()

        if text == "/start":
            await send_message(session, chat_id, "🤖 فعال شد!")

        elif text == "سلام":
            await send_message(session, chat_id, "👋 سلام!")

        else:
            await send_message(session, chat_id, "❓ ناشناخته")

        queue.task_done()


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

            for u in data["data"]["updates"]:

                offset = u.get("update_time", offset)

                if u.get("type") != "NewMessage":
                    continue

                msg = u.get("new_message", {})

                chat_id = u.get("chat_id")
                text = msg.get("text", "")

                if chat_id and text:
                    await queue.put((chat_id, text))

        except Exception as e:
            print("LOOP ERROR:", e)

        await asyncio.sleep(1)


# ---------------- MAIN ----------------
async def main():

    print("🚀 FINAL STABLE BOT STARTED")

    async with aiohttp.ClientSession() as session:

        asyncio.create_task(worker(session))
        await get_updates(session)


if __name__ == "__main__":
    asyncio.run(main())
