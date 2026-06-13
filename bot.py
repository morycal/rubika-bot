import aiohttp
import asyncio
import os

TOKEN = os.getenv("RUBIKA_TOKEN")

if not TOKEN:
    raise Exception("RUBIKA_TOKEN is not set!")

BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

offset = None
first_run = True


async def send_message(session, chat_id, text):
    try:
        async with session.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            }
        ) as response:

            result = await response.text()

            print("SEND STATUS:", response.status)
            print("SEND RESPONSE:", result)

            # جلوگیری از ریت‌لیمیت
            await asyncio.sleep(0.5)

    except Exception as e:
        print("SEND ERROR:", e)


async def handle_message(session, chat_id, text):

    text = text.strip()

    print("CHAT ID:", chat_id)
    print("User:", text)

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
            ) as response:

                data = await response.json()

            if data.get("status") != "OK":
                await asyncio.sleep(1)
                continue

            updates = data["data"]["updates"]

            # اولین اجرا: پیام‌های قدیمی را رد کن
            if first_run:

                if updates:

                    offset = updates[-1]["update_time"]

                    print(
                        f"Skipped {len(updates)} old messages"
                    )

                first_run = False

                await asyncio.sleep(1)
                continue

            for update in updates:

                offset = update.get(
                    "update_time",
                    offset
                )

                if update.get("type") != "NewMessage":
                    continue

                msg = update.get(
                    "new_message",
                    {}
                )

                text = msg.get(
                    "text",
                    ""
                )

                chat_id = update.get(
                    "chat_id"
                )

                if not chat_id:
                    continue

                await handle_message(
                    session,
                    chat_id,
                    text
                )

        except Exception as e:

            print("LOOP ERROR:", e)

            await asyncio.sleep(3)

        await asyncio.sleep(1)


async def main():

    print("🚀 Async Bot Started")

    timeout = aiohttp.ClientTimeout(
        total=60
    )

    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:

        await get_updates(session)


if __name__ == "__main__":
    asyncio.run(main())
