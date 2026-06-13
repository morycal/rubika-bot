import aiohttp
import asyncio

TOKEN = "1597508244:loyNgb9a1cdwlgLxF9ln7sofuwhYOjFN7Xk"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

# 🔥 قفل واقعی (نه set ساده)
processing = set()


def make_key(update):
    msg = update.get("message", {})
    msg_id = msg.get("message_id")
    chat_id = msg.get("chat", {}).get("id")
    return f"{chat_id}:{msg_id}"


async def send_message(session, chat_id, text):
    async with session.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    ) as r:
        await r.text()


async def handle_update(session, update):
    global offset

    key = make_key(update)

    # 🔥 جلوگیری قطعی duplicate
    if key in processing:
        return

    processing.add(key)

    msg = update.get("message")
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    update_id = update.get("update_id")

    print("USER:", text)

    # offset فقط یک بار
    offset = max(offset, update_id + 1)

    if text == "/start":
        await send_message(session, chat_id, "🤖 OK")

    elif text == "سلام":
        await send_message(session, chat_id, "👋 سلام")

    else:
        await send_message(session, chat_id, "❓")


async def loop():
    global offset

    async with aiohttp.ClientSession() as session:

        while True:
            try:
                async with session.post(
                    f"{BASE_URL}/getUpdates",
                    json={"offset": offset},
                    timeout=20
                ) as r:

                    data = await r.json()
                    updates = data.get("result", [])

                    tasks = []

                    for u in updates:
                        tasks.append(handle_update(session, u))

                    if tasks:
                        await asyncio.gather(*tasks)

            except Exception as e:
                print("ERR:", e)

            await asyncio.sleep(0.4)


asyncio.run(loop())
