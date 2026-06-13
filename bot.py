import aiohttp
import asyncio
from collections import deque

TOKEN = "1597508244:loyNgb9a1cdwlgLxF9ln7sofuwhYOjFN7Xk"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

seen = deque(maxlen=5000)
seen_set = set()


def mark_seen(update_id):
    seen.append(update_id)
    seen_set.add(update_id)

    if len(seen) == seen.maxlen:
        old = seen.popleft()
        seen_set.discard(old)


def is_seen(update_id):
    return update_id in seen_set


# ---------------- SEND MESSAGE (ASYNC) ----------------
async def send_message(session, chat_id, text):
    try:
        async with session.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
        ) as resp:
            await resp.text()
    except Exception as e:
        print("SEND ERROR:", e)


# ---------------- HANDLE UPDATE ----------------
async def handle_update(session, update, offset_ref):
    global offset

    update_id = update.get("update_id")

    if is_seen(update_id):
        return

    mark_seen(update_id)
    offset = update_id + 1

    message = update.get("message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    print("USER:", text)

    if text == "/start":
        await send_message(session, chat_id, "⚡ Async Bot Active")

    elif text == "سلام":
        await send_message(session, chat_id, "👋 سلام!")

    elif text == "ping":
        await send_message(session, chat_id, "pong 🏓")

    else:
        await send_message(session, chat_id, "❓ unknown")


# ---------------- GET UPDATES LOOP ----------------
async def get_updates(session):
    global offset

    while True:
        try:
            async with session.post(
                f"{BASE_URL}/getUpdates",
                json={"offset": offset},
                timeout=20
            ) as resp:

                data = await resp.json()

                if not data.get("ok"):
                    await asyncio.sleep(0.5)
                    continue

                updates = data.get("result", [])

                tasks = []

                for update in updates:
                    tasks.append(handle_update(session, update, offset))

                # 🔥 پردازش همزمان (10x سریع‌تر)
                if tasks:
                    await asyncio.gather(*tasks)

        except Exception as e:
            print("LOOP ERROR:", e)

        await asyncio.sleep(0.3)  # ⚡ سریع‌تر از نسخه sync


# ---------------- MAIN ----------------
async def main():
    print("🚀 Async Bale Bot Started")

    async with aiohttp.ClientSession() as session:
        await get_updates(session)


if __name__ == "__main__":
    asyncio.run(main())
