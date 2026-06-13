import aiohttp
import asyncio
import os
import time

TOKEN = os.getenv("RUBIKA_TOKEN")

if not TOKEN:
    raise Exception("RUBIKA_TOKEN is not set!")

BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

offset = None
first_run = True


# ---------------- SEND MESSAGE ----------------
async def send_message(session, peer_id, text):
    try:
        payload = {
            "chat_id": peer_id,   # در روبیکا peer = sender_id
            "text": text
        }

        async with session.post(
            f"{BASE_URL}/sendMessage",
            json=payload
        ) as res:

            data = await res.text()

            print("SEND:", data)

            # جلوگیری از rate limit
            await asyncio.sleep(0.4)

    except Exception as e:
        print("SEND ERROR:", e)


# ---------------- HANDLE MESSAGE ----------------
async def handle_message(session, peer_id, text):

    text = text.strip()
    print("USER:", text)
    print("PEER:", peer_id)

    if text == "/start":
        await send_message(
            session,
            peer_id,
            "🤖 ربات فعال شد!\nسلام 👋"
        )

    elif text == "سلام":
        await send_message(
            session,
            peer_id,
            "👋 سلام! خوش اومدی"
        )

    elif text == "کجایی":
        await send_message(
            session,
            peer_id,
            "📡 آنلاین روی سرور"
        )

    else:
        await send_message(
            session,
            peer_id,
            "❓ دستور ناشناخته"
        )


# ---------------- PROCESS UPDATE ----------------
async def process_update(session, update):

    global offset

    update_time = update.get("update_time")
    if update_time:
        offset = update_time

    if update.get("type") != "NewMessage":
        return

    msg = update.get("new_message", {})

    text = msg.get("text", "")

    # 🔥 مهم‌ترین تغییر: peer = sender_id
    peer_id = msg.get("sender_id")

    if not peer_id:
        return

    await handle_message(session, peer_id, text)


# ---------------- GET UPDATES ----------------
async def get_updates(session):

    global offset
    global first_run

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

            # 🚀 skip old messages
            if first_run:
                if updates:
                    offset = updates[-1]["update_time"]
                    print(f"Skipped {len(updates)} old updates")

                first_run = False
                await asyncio.sleep(1)
                continue

            for update in updates:
                await process_update(session, update)

        except Exception as e:
            print("LOOP ERROR:", e)
            await asyncio.sleep(3)

        await asyncio.sleep(1)


# ---------------- MAIN ----------------
async def main():
    print("🚀 Peer-based Bot Started")

    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        await get_updates(session)


if __name__ == "__main__":
    asyncio.run(main())
