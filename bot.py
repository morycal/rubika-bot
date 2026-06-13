import aiohttp
import asyncio
import os

TOKEN = os.getenv("RUBIKA_TOKEN")

if not TOKEN:
    raise Exception("RUBIKA_TOKEN is not set!")

BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

OFFSET_FILE = "offset.txt"


def load_offset():
    try:
        with open(OFFSET_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return None


def save_offset(offset):
    try:
        with open(OFFSET_FILE, "w") as f:
            f.write(str(offset))
    except Exception as e:
        print("OFFSET SAVE ERROR:", e)


offset = load_offset()


async def send_message(session, chat_id, text):
    try:
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        async with session.post(
            f"{BASE_URL}/sendMessage",
            json=payload
        ) as response:

            result = await response.text()

            print("SEND STATUS:", response.status)
            print("SEND RESPONSE:", result)

            # جلوگیری از اسپم
            await asyncio.sleep(0.5)

    except Exception as e:
        print("SEND ERROR:", e)


async def handle_message(session, chat_id, text):

    print("User:", text)

    text = text.strip()

    if text == "/start":

        await send_message(
            session,
            chat_id,
            "🤖 ربات فعال شد!\n\nسلام 👋"
        )

    elif text == "سلام":

        await send_message(
            session,
            chat_id,
            "👋 سلام! خوبی؟"
        )

    elif text == "کجایی؟؟":

        await send_message(
            session,
            chat_id,
            "📡 روی Railway آنلاینم!"
        )

    else:

        await send_message(
            session,
            chat_id,
            "❓ دستور ناشناخته"
        )


async def process_update(session, update):

    global offset

    update_time = update.get("update_time")

    if update_time:
        offset = update_time
        save_offset(offset)

    if update.get("type") != "NewMessage":
        return

    msg = update.get("new_message", {})

    text = msg.get("text", "")

    chat_id = update.get("chat_id")

    if not chat_id:
        return

    print("CHAT ID:", chat_id)

    await handle_message(
        session,
        chat_id,
        text
    )


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
            ) as response:

                data = await response.json()

            if data.get("status") == "OK":

                updates = data["data"]["updates"]

                for update in updates:

                    await process_update(
                        session,
                        update
                    )

        except Exception as e:

            print("LOOP ERROR:", e)

            await asyncio.sleep(3)

        await asyncio.sleep(1)


async def main():

    print("🚀 Async Bot Started")

    async with aiohttp.ClientSession() as session:

        await get_updates(session)


if __name__ == "__main__":
    asyncio.run(main())
