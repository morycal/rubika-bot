import aiohttp
import asyncio
import os

TOKEN = os.getenv("RUBIKA_TOKEN")

if not TOKEN:
    raise Exception("RUBIKA_TOKEN is not set!")

BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

offset = None


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

    except Exception as e:
        print("SEND ERROR:", e)


async def handle_message(session, chat_id, text):
    print(f"User: {text}")

    if text == "/start":
        await send_message(
            session,
            chat_id,
            "🤖 ربات فعال شد!"
        )

    elif text == "سلام":
        await send_message(
            session,
            chat_id,
            "👋 سلام! خوبی؟"
        )

    else:
        await send_message(
            session,
            chat_id,
            "❓ دستور ناشناخته"
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

                    print("UPDATE:", update)

                    offset = update.get(
                        "update_time",
                        offset
                    )

                    if update.get("type") == "NewMessage":

                        msg = update.get(
                            "new_message",
                            {}
                        )

                        text = msg.get(
                            "text",
                            ""
                        )

                        chat_id = update.get("chat_id")

                        print("CHAT ID:", chat_id)

                        asyncio.create_task(
                            handle_message(
                                session,
                                chat_id,
                                text
                            )
                        )

        except Exception as e:
            print("LOOP ERROR:", e)

        await asyncio.sleep(0.5)


async def main():
    print("🚀 Async Bot Started")

    async with aiohttp.ClientSession() as session:
        await get_updates(session)


if __name__ == "__main__":
    asyncio.run(main())
