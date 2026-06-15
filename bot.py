import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, ContextTypes

# تنظیمات
TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
ADMIN_ID = 586110315

# مراحل مکالمه
NAME, PHONE, INSURANCE_TYPE = range(3)

# دیتابیس موقت (در عمل از دیتابیس واقعی استفاده کن)
users = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    
    if user_id in users:
        # کاربر قبلاً ثبت‌نام کرده
        keyboard = [
            [InlineKeyboardButton("🛡 سفارش بیمه", callback_data='order_insurance')],
            [InlineKeyboardButton("📋 سفارشات من", callback_data='my_orders')],
            [InlineKeyboardButton("👤 پروفایل", callback_data='profile')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "سلام! به ازکی بیمه خوش اومدی 🌟\n\n"
            "چطور میتونم کمکت کنم؟",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "سلام! به ربات ازکی بیمه خوش اومدی 🌟\n\n"
        "لطفاً نام و نام خانوادگیت رو وارد کن:"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("ممنون! حالا شماره تلفنت رو وارد کن:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    users[user_id] = {
        'name': context.user_data['name'],
        'phone': update.message.text
    }
    
    # ارسال اطلاعات به ادمین
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"کاربر جدید ثبت‌نام کرد:\nنام: {users[user_id]['name']}\nشماره: {users[user_id]['phone']}\nآیدی: {user_id}"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛡 سفارش بیمه", callback_data='order_insurance')],
        [InlineKeyboardButton("📋 سفارشات من", callback_data='my_orders')],
        [InlineKeyboardButton("👤 پروفایل", callback_data='profile')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "ثبت‌نام با موفقیت انجام شد! 🎉\n\n"
        "از منوی زیر انتخاب کن:",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def insurance_type_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🚗 شخص ثالث خودرو", callback_data='third_party_car')],
        [InlineKeyboardButton("🏍 شخص ثالث موتور", callback_data='third_party_motor')],
        [InlineKeyboardButton("🚙 بدنه خودرو", callback_data='body_car')],
        [InlineKeyboardButton("🏍 بدنه موتور", callback_data='body_motor')],
        [InlineKeyboardButton("👤 عمر", callback_data='life')],
        [InlineKeyboardButton("📱 موبایل", callback_data='mobile')],
        [InlineKeyboardButton("✈️ مسافرتی", callback_data='travel')],
        [InlineKeyboardButton("🏥 تکمیلی", callback_data='supplementary')],
        [InlineKeyboardButton("🔥 آتش‌سوزی", callback_data='fire')],
        [InlineKeyboardButton("⚔️ جنگ", callback_data='war')],
        [InlineKeyboardButton("🏠 خانه", callback_data='home')],
        [InlineKeyboardButton("🔙 برگشت", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "لطفاً نوع بیمه مورد نظرت رو انتخاب کن:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == 'order_insurance':
        await insurance_type_menu(update, context)
    elif query.data == 'profile':
        user_id = update.effective_user.id
        if user_id in users:
            await query.edit_message_text(
                f"👤 پروفایل شما:\n\n"
                f"نام: {users[user_id]['name']}\n"
                f"شماره: {users[user_id]['phone']}\n"
                f"آیدی: {user_id}"
            )
    elif query.data == 'back_to_main':
        keyboard = [
            [InlineKeyboardButton("🛡 سفارش بیمه", callback_data='order_insurance')],
            [InlineKeyboardButton("📋 سفارشات من", callback_data='my_orders')],
            [InlineKeyboardButton("👤 پروفایل", callback_data='profile')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "چطور میتونم کمکت کنم؟",
            reply_markup=reply_markup
        )

def main():
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.run_polling()

if __name__ == '__main__':
    main()
