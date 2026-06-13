import aiohttp
import asyncio
import os

TOKEN = os.getenv("RUBIKA_TOKEN")
BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

offset = None


# ================= ارسال پیام =================
async def send_message(session, chat_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    try:
        async with session.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10) as r:
            await r.text()
    except Exception as e:
        print("Send error:", e)


# ================= هندل پیام =================
async def handle_message(session, chat_id, text):
    print("User:", text)

    if text == "/start":
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "👋 سلام", "callback_data": "hello"},
                    {"text": "ℹ️ اطلاعات", "callback_data": "info"}
                ]
            ]
        }
        await send_message(session, chat_id, "🤖 بات Async فعال شد!", keyboard)

    elif text == "سلام":
        await send_message(session, chat_id, "👋 سلام! حالت چطوره؟")

    else:
        await send_message(session, chat_id, "❓ دستور ناشناخته")


# ================= هندل callback =================
async def handle_callback(session, chat_id, data_cb):
    print("Callback:", data_cb)

    if data_cb == "hello":
        await send_message(session, chat_id, "سلام 👋 خوش اومدی!")
    elif data_cb == "info":
        await send_message(session, chat_id, "⚡ این یک بات Async بدون لگ است")
    else:
        await send_message(session, chat_id, "❓ گزینه نامشخص")


# ================= گرفتن آپدیت‌ها =================
async def get_updates(session):
    global offset

    while True:
        try:
            payload = {"offset_id": offset} if offset else {}

            async with session.post(f"{BASE_URL}/getUpdates", json=payload, timeout=15) as r:
                data = await r.json()

            if data.get("status") == "OK":
                updates = data["data"]["updates"]

                tasks = []

                for u in updates:
                    offset = u.get("update_time", offset)

                    if u["type"] == "NewMessage":
                        msg = u["new_message"]
                        text = msg.get("text", "")
                        chat_id = u["chat_id"]

                        tasks.append(handle_message(session, chat_id, text))

                    elif u["type"] == "CallbackQuery":
                        chat_id = u["chat_id"]
                        data_cb = u["callback_query"].get("data", "")

                        tasks.append(handle_callback(session, chat_id, data_cb))

                # اجرای همزمان همه پیام‌ها (بدون لگ)
                if tasks:
                    await asyncio.gather(*tasks)

        except Exception as e:
            print("Loop error:", e)

        await asyncio.sleep(0.2)  # خیلی سریع


# ================= اجرای اصلی =================
async def main():
    async with aiohttp.ClientSession() as session:
        print("🚀 Async Bot Started")
        await get_updates(session)


if __name__ == "__main__":
    asyncio.run(main())
