import html
import logging
import os
import threading
from flask import Flask
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
import urllib3

# إعداد نظام تسجيل الأخطاء والنشاط (Logging) بدلاً من print
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log', encoding='utf-8'), logging.StreamHandler()]
)

# تعطيل تحذيرات الأمان الخاصة بـ SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إعداد خادم ويب مصغر لاستضافة Render ولضمان عمل البوت 24/7
app = Flask('')

@app.route('/')
def home():
    return 'ZEUS-ECHANCE-BOT is running 24/7 securely!'

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web_server, daemon=True).start()

# جلب الإعدادات والتوكن بأمان من إعدادات البيئة (Environment Variables)
TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    logging.critical("CRITICAL: Telegram BOT TOKEN is missing from environment variables!")
    raise ValueError("Telegram BOT TOKEN is missing!")

ADMIN_ID = int(os.environ.get('ADMIN_ID', 1632433018))
USD_TO_SYP_RATE = int(os.environ.get('USD_TO_SYP_RATE', 14000))

bot = telebot.TeleBot(TOKEN)

# ==========================================
# 💳 إعدادات المحافظ وطرق الدفع
# ==========================================
SHAM_CASH_WALLET = os.environ.get('SHAM_CASH_WALLET', '02d28a07292f2a11f12e0d8e2bd08dd1')
TRX_WALLET = os.environ.get('TRX_WALLET', 'TKva4xbJjCtwGy2vDFAoddsSd91aKZ5zqK')
PLASMA_WALLET = os.environ.get('PLASMA_WALLET', '0xb027c9b07f2b4ffffcf7a56fc80af180f8692c67')

def price_text(usd_amount):
    """دالة لتوليد السعر بالدولار وما يعادلها بالليرة السورية تلقائياً مع فاصل الآلاف"""
    syp_amount = int(usd_amount * USD_TO_SYP_RATE)
    return f"${usd_amount} ({syp_amount:,} ل.س)"

# لوحة المفاتيح الثابتة أسفل محادثة العميل
def get_persistent_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton('🏠 القائمة الرئيسية / Main Menu'),
        KeyboardButton('📞 الدعم الفني / Support')
    )
    return markup

# إرسال تفاصيل الطلب الأولي إلى حساب المدير باستخدام HTML (آمن ضد التلاعب)
def send_order_to_admin(message, service_name, user_input):
    user = message.from_user
    safe_name = html.escape(user.first_name)
    safe_username = f"@{html.escape(user.username)}" if user.username else "لا يوجد"
    safe_input = html.escape(user_input)
    safe_service = html.escape(service_name)
    
    notification_text = (
        f"🚨 <b>طلب جديد بانتظار التحويل والتنفيذ!</b>\n\n"
        f"👤 اسم العميل: {safe_name}\n"
        f"🆔 المعرف: {safe_username}\n"
        f"🔢 الآيدي: <code>{user.id}</code>\n"
        f"📱 الحساب أو المعلومات المدخلة:\n<code>{safe_input}</code>\n"
        f"📦 الخدمة المطلوبة: <b>{safe_service}</b>\n\n"
        f"👉 بانتظار إتمام العميل للتحويل وإرسال إشعار أو رقم العملية."
    )
    try:
        bot.send_message(ADMIN_ID, notification_text, parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error sending notification to admin: {e}")

# استقبال صور إيصالات الدفع من العملاء وتحويلها للإدارة
@bot.message_handler(content_types=['photo'])
def handle_client_photo(message):
    if message.from_user.id == ADMIN_ID:
        return

    user = message.from_user
    photo_file_id = message.photo[-1].file_id
    safe_name = html.escape(user.first_name)
    safe_username = f"@{html.escape(user.username)}" if user.username else "لا يوجد"

    caption = (
        f"📸 <b>إيصال دفع جديد (صورة) مرسل من عميل!</b>\n\n"
        f"👤 اسم العميل: {safe_name}\n"
        f"🆔 المعرف: {safe_username}\n"
        f"🔢 الآيدي: <code>{user.id}</code>\n\n"
        f"👉 يرجى التحقق من وصول المبلغ على المحافظ لتنفيذ الطلب."
    )

    try:
        bot.send_photo(
            ADMIN_ID,
            photo_file_id,
            caption=caption,
            reply_markup=get_persistent_keyboard(),
            parse_mode='HTML'
        )
        bot.reply_to(
            message,
            "✅ <b>تم استلام إيصال الدفع بنجاح!</b>\nجاري التحقق من قبل الإدارة وتنفيذ طلبك في أقرب وقت ❤️",
            reply_markup=get_persistent_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error forwarding payment receipt photo: {e}")

# استقبال أرقام عمليات التحويل النصية
@bot.message_handler(
    content_types=['text'],
    func=lambda message: message.from_user.id != ADMIN_ID and message.text not in [
        '🏠 القائمة الرئيسية / Main Menu',
        '📞 الدعم الفني / Support',
        '/start'
    ]
)
def handle_client_text_receipt(message):
    user = message.from_user
    safe_name = html.escape(user.first_name)
    safe_username = f"@{html.escape(user.username)}" if user.username else "لا يوجد"
    safe_text = html.escape(message.text)

    notification_text = (
        f"💰 <b>إشعار دفع / رقم عملية تحويل مرسل كنص من عميل!</b>\n\n"
        f"👤 اسم العميل: {safe_name}\n"
        f"🆔 المعرف: {safe_username}\n"
        f"🔢 الآيدي: <code>{user.id}</code>\n\n"
        f"📝 <b>النص أو رقم العملية المرسل:</b>\n<code>{safe_text}</code>\n\n"
        f"👉 يرجى مطابقة رقم العملية مع الحسابات لتأكيد التحويل."
    )

    try:
        bot.send_message(
            ADMIN_ID,
            notification_text,
            reply_markup=get_persistent_keyboard(),
            parse_mode='HTML'
        )
        bot.reply_to(
            message,
            "✅ <b>تم استلام رقم العملية / إشعار الدفع بنجاح!</b>\nجاري التحقق من قبل الإدارة وتنفيذ طلبك (مدة التحقق خلال 60 دقيقة) ❤️",
            reply_markup=get_persistent_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error forwarding text receipt: {e}")

# أزرار لوحة المفاتيح الثابتة
@bot.message_handler(func=lambda message: message.text in ['🏠 القائمة الرئيسية / Main Menu', '📞 الدعم الفني / Support'])
def handle_persistent_buttons(message):
    if message.text == '🏠 القائمة الرئيسية / Main Menu':
        send_welcome(message)
    elif message.text == '📞 الدعم الفني / Support':
        support_text = (
            "📞 <b>خدمة العملاء والدعم الفني - ZEUS</b>\n\n"
            "لأي استفسار أو طلب خاص يرجى التواصل مع الإدارة عبر الأرقام التالية:\n\n"
            "👤 <b>ALI:</b> <code>0951984521</code>\n"
            "👤 <b>ALAA:</b> <code>0996743743</code>\n"
            "🚨 <b>الشكاوى:</b> <code>0995611608</code>\n\n"
            "نحن في خدمتكم دائماً ❤️"
        )
        bot.send_message(
            message.chat.id,
            support_text,
            reply_markup=get_persistent_keyboard(),
            parse_mode='HTML'
        )

# أمر البدء الرئيسي /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "اهلا بكم في ⚡️ <b>ZEUS SERVICES -BOT</b> ⚡️ للخدمات الرقمية الشاملة\n\n"
        "نحن فريق محترف نقدم لك كافة خدمات الشحن والدفع الإلكتروني بكل أمان وسرعة وبدقة عالية ❤️\n\n"
        "يرجى اختيار القسم المطلوب:"
    )

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('1️⃣ الألعاب / GAMES 🎮', callback_data='menu_games'),
        InlineKeyboardButton('2️⃣ الذكاء الاصطناعي / AI 💭', callback_data='menu_ai'),
        InlineKeyboardButton('3️⃣ التطبيقات الصوتية والدردشة / CHAT APP 💬', callback_data='menu_chat'),
        InlineKeyboardButton('4️⃣ تعبئة الرصيد / RECHARGE 💳', callback_data='menu_recharge'),
        InlineKeyboardButton('5️⃣ توثيق الحسابات / ACCOUNTS VERIFICATION 🔐', callback_data='menu_verify'),
        InlineKeyboardButton('6️⃣ خدمات متنوعة / Various Services 🌐', callback_data='menu_various'),
        InlineKeyboardButton('7️⃣ خدمة تخطي الموقع VPN (بروكسي) 🛡️', callback_data='menu_vpn'),
        InlineKeyboardButton('8️⃣ خدمات ويندوز / WINDOWS SERVICES 💻', callback_data='menu_windows'),
        InlineKeyboardButton('9️⃣ خدمات مزودين الانترنت / INTERNET SERVICES 🌐', callback_data='menu_internet'),
        InlineKeyboardButton('🔟 خدمات شام كاش / SHAM CASH 💸', callback_data='menu_sham_cash'),
        InlineKeyboardButton('1️⃣1️⃣ خدمة العملاء / SUPPORT TEAM 📞', callback_data='menu_support')
    )

    bot.send_message(message.chat.id, "تم تفعيل لوحة المفاتيح الخاصة بك 👇", reply_markup=get_persistent_keyboard())
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode='HTML')

# زر العودة للقائمة الرئيسية
@bot.callback_query_handler(func=lambda call: call.data == 'back_home')
def back_home(call):
    welcome_text = "⚡ <b>القائمة الرئيسية - ZEUS-ECHANCE-BOT</b> ⚡\n\nيرجى اختيار القسم المطلوب:"
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('1️⃣ الألعاب / GAMES 🎮', callback_data='menu_games'),
        InlineKeyboardButton('2️⃣ الذكاء الاصطناعي / AI 💭', callback_data='menu_ai'),
        InlineKeyboardButton('3️⃣ التطبيقات الصوتية والدردشة / CHAT APP 💬', callback_data='menu_chat'),
        InlineKeyboardButton('4️⃣ تعبئة الرصيد / RECHARGE 💳', callback_data='menu_recharge'),
        InlineKeyboardButton('5️⃣ توثيق الحسابات / ACCOUNTS VERIFICATION 🔐', callback_data='menu_verify'),
        InlineKeyboardButton('6️⃣ خدمات متنوعة / Various Services 🌐', callback_data='menu_various'),
        InlineKeyboardButton('7️⃣ خدمة تخطي الموقع VPN (بروكسي) 🛡️', callback_data='menu_vpn'),
        InlineKeyboardButton('8️⃣ خدمات ويندوز / WINDOWS SERVICES 💻', callback_data='menu_windows'),
        InlineKeyboardButton('9️⃣ خدمات مزودين الانترنت / INTERNET SERVICES 🌐', callback_data='menu_internet'),
        InlineKeyboardButton('🔟 خدمات شام كاش / SHAM CASH 💸', callback_data='menu_sham_cash'),
        InlineKeyboardButton('1️⃣1️⃣ خدمة العملاء / SUPPORT TEAM 📞', callback_data='menu_support')
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=welcome_text,
        reply_markup=markup,
        parse_mode='HTML'
    )

# --- 1. قسم الألعاب / GAMES ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_games')
def games_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('PUBG Mobile 🎮', callback_data='game_pubg'),
        InlineKeyboardButton('Free Fire 🔥', callback_data='game_freefire'),
        InlineKeyboardButton('Jawaker 🃏', callback_data='game_jawaker'),
        InlineKeyboardButton('Clash of Clans 🏰', callback_data='game_clash'),
        InlineKeyboardButton('Call of Duty 🎯', callback_data='game_cod'),
        InlineKeyboardButton('Fortnite ⚔️', callback_data='game_fortnite'),
        InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home')
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='🎮 <b>اختر اللعبة المطلوبة:</b>',
        reply_markup=markup,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('game_'))
def game_packages(call):
    game = call.data.split('_')[1]
    markup = InlineKeyboardMarkup(row_width=1)

    if game == 'pubg':
        markup.add(
            InlineKeyboardButton(f'PUBG: 60 شدة ({price_text(1.2)})', callback_data='order_PUBG_60_UC_$1.2'),
            InlineKeyboardButton(f'PUBG: 325 شدة ({price_text(5.5)})', callback_data='order_PUBG_325_UC_$5.5'),
            InlineKeyboardButton(f'PUBG: 660 شدة ({price_text(10.2)})', callback_data='order_PUBG_660_UC_$10.2'),
            InlineKeyboardButton(f'PUBG: 1800 شدة ({price_text(24.8)})', callback_data='order_PUBG_1800_UC_$24.8'),
            InlineKeyboardButton(f'PUBG: 3800 شدة ({price_text(49.7)})', callback_data='order_PUBG_3800_UC_$49.7'),
            InlineKeyboardButton(f'PUBG: 8100 شدة ({price_text(90.2)})', callback_data='order_PUBG_8100_UC_$90.2'),
            InlineKeyboardButton('✨ طلب حزم وترقية وشعارات (تواصل مع الدعم)', callback_data='menu_support')
        )
    elif game == 'freefire':
        markup.add(
            InlineKeyboardButton(f'Free Fire: 110 جوهرة ({price_text(1.5)})', callback_data='order_FreeFire_110_Gems_$1.5'),
            InlineKeyboardButton(f'Free Fire: 231 جوهرة ({price_text(2.5)})', callback_data='order_FreeFire_231_Gems_$2.5'),
            InlineKeyboardButton(f'Free Fire: 583 جوهرة ({price_text(5.8)})', callback_data='order_FreeFire_583_Gems_$5.8'),
            InlineKeyboardButton(f'Free Fire: 1200 جوهرة ({price_text(11)})', callback_data='order_FreeFire_1200_Gems_$11'),
            InlineKeyboardButton('✨ طلب حزمة عضوية (تواصل مع الدعم)', callback_data='menu_support')
        )
    elif game == 'jawaker':
        markup.add(
            InlineKeyboardButton(f'Jawaker: 10,000 جوهرة ({price_text(1.8)})', callback_data='order_Jawaker_10k_Gems_$1.8'),
            InlineKeyboardButton(f'Jawaker: 20,000 جوهرة ({price_text(3.2)})', callback_data='order_Jawaker_20k_Gems_$3.2'),
            InlineKeyboardButton('✨ طلب توكنز أسبوعي (تواصل مع الدعم)', callback_data='menu_support')
        )
    elif game == 'clash':
        markup.add(
            InlineKeyboardButton(f'Clash: 80 جوهرة ({price_text(2)})', callback_data='order_Clash_80_Gems_$2'),
            InlineKeyboardButton(f'Clash: 500 جوهرة ({price_text(8)})', callback_data='order_Clash_500_Gems_$8'),
            InlineKeyboardButton('✨ طلب المزيد (تواصل مع الدعم)', callback_data='menu_support')
        )
    elif game == 'cod':
        markup.add(
            InlineKeyboardButton(f'Call of Duty: 30 CP ({price_text(0.8)})', callback_data='order_COD_30_CP_$0.8'),
            InlineKeyboardButton(f'Call of Duty: 80 CP ({price_text(2.1)})', callback_data='order_COD_80_CP_$2.1'),
            InlineKeyboardButton(f'Call of Duty: 420 CP ({price_text(7.5)})', callback_data='order_COD_420_CP_$7.5'),
            InlineKeyboardButton(f'Call of Duty: 880 CP ({price_text(14.1)})', callback_data='order_COD_880_CP_$14.1'),
            InlineKeyboardButton(f'Call of Duty: 2400 CP ({price_text(35.2)})', callback_data='order_COD_2400_CP_$35.2'),
            InlineKeyboardButton(f'Call of Duty: 5000 CP ({price_text(68.6)})', callback_data='order_COD_5000_CP_$68.6')
        )
    elif game == 'fortnite':
        markup.add(
            InlineKeyboardButton(f'Fortnite: 2800 بطاقة ({price_text(32.9)})', callback_data='order_Fortnite_2800_$32.9'),
            InlineKeyboardButton(f'Fortnite: 5000 بطاقة ({price_text(54.9)})', callback_data='order_Fortnite_5000_$54.9')
        )

    markup.add(InlineKeyboardButton('🔙 رجوع', callback_data='menu_games'))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='🎮 <b>حزم قسم الألعاب:</b>',
        reply_markup=markup,
        parse_mode='HTML'
    )

# --- 2. قسم الذكاء الاصطناعي / AI 💭 ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_ai')
def ai_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'ChatGPT Plus: تفعيل شخصي 1 شهر ({price_text(19)})', callback_data='order_AI_ChatGPT_Plus_شهر1_$19'),
        InlineKeyboardButton(f'Gemini AI: تفعيل شخصي 6 أشهر ({price_text(12)})', callback_data='order_AI_Gemini_6شهور_$12'),
        InlineKeyboardButton(f'Gemini AI Pro: تفعيل 1 شهر ({price_text(3.7)})', callback_data='order_AI_GeminiPro_1 شهر_$3.7'),
        InlineKeyboardButton(f'Gemini AI Pro: تفعيل 12 شهر ({price_text(49)})', callback_data='order_AI_GeminiPro_12 شهر_$49'),
        InlineKeyboardButton(f'CapCut Pro: تفعيل شخصي 1 شهر ({price_text(15)})', callback_data='order_AI_CapCut_1 شهر_$15'),
        InlineKeyboardButton(f'Canva Pro: تفعيل شخصي 12 شهر ({price_text(14)})', callback_data='order_AI_Canva_12 شهر_$14'),
        InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home')
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='💭 <b>اختر خدمة الذكاء الاصطناعي المطلوبة:</b>',
        reply_markup=markup,
        parse_mode='HTML'
    )

# --- 3. التطبيقات الصوتية والدردشة / CHAT APP ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_chat')
def chat_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('Bigo Live 🔴', callback_data='chat_bigo'),
        InlineKeyboardButton('Sool Chill 💬', callback_data='chat_sool'),
        InlineKeyboardButton('Soul Chat 💫', callback_data='chat_soul'),
        InlineKeyboardButton('Zaffa Live 🌟', callback_data='chat_zaffa'),
        InlineKeyboardButton('Sugo Chat 💬', callback_data='chat_sugo'),
        InlineKeyboardButton('Honey Jar 🍯', callback_data='chat_honey'),
        InlineKeyboardButton('Mico Live 💜', callback_data='chat_mico'),
        InlineKeyboardButton('Likee Live 💛', callback_data='chat_likee'),
        InlineKeyboardButton('Lama Chat 🦙 (قريباً ⏳️)', callback_data='chat_lama_soon'),
        InlineKeyboardButton('Lggo Live 🟢 (قريباً ⏳️)', callback_data='chat_lggo_soon'),
        InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home')
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='💬 <b>اختر التطبيق المطلوب:</b>',
        reply_markup=markup,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data in ['chat_lama_soon', 'chat_lggo_soon'])
def coming_soon_handler(call):
    bot.answer_callback_query(call.id, text='هذه الخدمة ستتوفر قريباً ⏳️ Coming soon', show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == 'chat_bigo')
def bigo_packages(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'Bigo: 100 PC ({price_text(2.1)})', callback_data='order_Bigo_100_PC_$2.1'),
        InlineKeyboardButton(f'Bigo: 500 PC ({price_text(9.5)})', callback_data='order_Bigo_500_PC_$9.5'),
        InlineKeyboardButton(f'Bigo: 1000 PC ({price_text(18.7)})', callback_data='order_Bigo_1000_PC_$18.7'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🔴 <b>حزم Bigo Live:</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'chat_sool')
def sool_packages(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'Sool Chill: 1000 PC ({price_text(1.98)})', callback_data='order_Sool_1000_PC_$1.98'),
        InlineKeyboardButton(f'Sool Chill: 4000 PC ({price_text(7.95)})', callback_data='order_Sool_4000_PC_$7.95'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='💬 <b>حزم Sool Chill:</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'chat_soul')
def soul_packages(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'Soul Chat: 1000 PC ({price_text(2)})', callback_data='order_Soul_1000_$2'),
        InlineKeyboardButton(f'Soul Chat: 5000 PC ({price_text(9.7)})', callback_data='order_Soul_5000_$9.7'),
        InlineKeyboardButton(f'Soul Chat: 10,000 PC ({price_text(18.9)})', callback_data='order_Soul_10k_$18.9'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='💫 <b>حزم Soul Chat:</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'chat_zaffa')
def zaffa_packages(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'Zaffa: 100,000 PC ({price_text(1.9)})', callback_data='order_Zaffa_100k_$1.9'),
        InlineKeyboardButton(f'Zaffa: 1,000,000 PC ({price_text(16)})', callback_data='order_Zaffa_1M_$16'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🌟 <b>حزم Zaffa Live:</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'chat_sugo')
def sugo_packages(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'Sugo: 10,000 PC ({price_text(1.8)})', callback_data='order_Sugo_10k_$1.8'),
        InlineKeyboardButton(f'Sugo: 100,000 PC ({price_text(14.85)})', callback_data='order_Sugo_100k_$14.85'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='💬 <b>حزم Sugo Live:</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'chat_honey')
def honey_packages(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'Honey Jar: 200 PC ({price_text(1.9)})', callback_data='order_Honey_200_$1.9'),
        InlineKeyboardButton(f'Honey Jar: 1000 PC ({price_text(8.9)})', callback_data='order_Honey_1000_$8.9'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🍯 <b>حزم Honey Jar:</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'chat_mico')
def mico_packages(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'Mico: 10,000 PC ({price_text(3.95)})', callback_data='order_Mico_10k_$3.95'),
        InlineKeyboardButton(f'Mico: 100,000 PC ({price_text(35.85)})', callback_data='order_Mico_100k_$35.85'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='💜 <b>حزم Mico Live:</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'chat_likee')
def likee_packages(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'Likee: 250 PC ({price_text(5.5)})', callback_data='order_Likee_250_$5.5'),
        InlineKeyboardButton(f'Likee: 1000 PC ({price_text(19.7)})', callback_data='order_Likee_1000_$19.7'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='💛 <b>حزم Likee Live:</b>', reply_markup=markup, parse_mode='HTML')

# --- 4. تعبئة الرصيد / RECHARGE ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_recharge')
def recharge_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('📱 Syriatel Recharge', callback_data='order_Recharge_Syriatel'),
        InlineKeyboardButton('📱 MTN Syria Recharge', callback_data='order_Recharge_MTN'),
        InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='💳 <b>اختر الشبكة لتعبئة الرصيد:</b>', reply_markup=markup, parse_mode='HTML')

# --- 5. توثيق الحسابات / ACCOUNTS VERIFICATION ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_verify')
def verify_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'YouTube: 1 Month ({price_text(4.5)})', callback_data='order_YouTube_1 Month _$4.5'),
        InlineKeyboardButton(f'YouTube: 12 Months ({price_text(44)})', callback_data='order_YouTube_12 Months _$44'),
        InlineKeyboardButton(f'Telegram: 3 Months ({price_text(15)})', callback_data='order_Telegram_3 Months _$15'),
        InlineKeyboardButton(f'Telegram: 12 Months ({price_text(35)})', callback_data='order_Telegram_12 شهر _$35'),
        InlineKeyboardButton(f'Snapchat: 3 Months ({price_text(7)})', callback_data='order_Snapchat_3 Months _$7'),
        InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🔐 <b>خدمات توثيق الحسابات:</b>', reply_markup=markup, parse_mode='HTML')

# --- 6. خدمات متنوعة / Various Services ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_various')
def various_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('📁 شراء مساحة تخزين GOOGLE', callback_data='order_Google_Storage'),
        InlineKeyboardButton('⭐ نجوم تلغرام', callback_data='menu_tg_stars'),
        InlineKeyboardButton(f'🤖 خدمة الرد الآلي FACEBOOK ({price_text(4.8)})', callback_data='order_FB_Bot_1 Month _$4.8'),
        InlineKeyboardButton(f'🚫 فك الحظر عن واتساب ({price_text(1.5)})', callback_data='order_WhatsApp_Unban_$1.5'),
        InlineKeyboardButton(f'👥 متابعين FACEBOOK: 1000 متابع ({price_text(2)})', callback_data='order_FB_1k_$2'),
        InlineKeyboardButton(f'📸 متابعين INSTAGRAM: 1000 متابع ({price_text(4)})', callback_data='order_IG_1k_$4'),
        InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🌐 <b>الخدمات المتنوعة:</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'menu_tg_stars')
def tg_stars_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'⭐ 50 نجمة ({price_text(1.5)})', callback_data='order_Telegram_Stars_50_$1.5'),
        InlineKeyboardButton(f'⭐ 100 نجمة ({price_text(2.97)})', callback_data='order_Telegram_Stars_100_$2.97'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_various')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='⭐ <b>نجوم تلغرام:</b>', reply_markup=markup, parse_mode='HTML')

# --- 7. خدمة تخطي الموقع VPN ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_vpn')
def vpn_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('🛡️ OPEN VPN', callback_data='vpn_open'),
        InlineKeyboardButton('🛡️ EXPRESS VPN', callback_data='vpn_express'),
        InlineKeyboardButton('🛡️ HOTSPOT SHIELD', callback_data='vpn_hotspot'),
        InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🛡️ <b>خدمة تخطي الموقع VPN:</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'vpn_open')
def vpn_open_packages(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'Open VPN: 1 Month ({price_text(2)})', callback_data='order_OpenVPN_1 Month _$2'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_vpn')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🛡️ <b>حزم Open VPN:</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'vpn_express')
def vpn_express_packages(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'Express VPN: 1 Month ({price_text(6)})', callback_data='order_ExpressVPN_1 Month _$6'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_vpn')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🛡️ <b>حزم Express VPN:</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'vpn_hotspot')
def vpn_hotspot_packages(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'Hotspot Shield: 1 Month ({price_text(2)})', callback_data='order_Hotspot_1 Month _$2'),
        InlineKeyboardButton('🔙 رجوع', callback_data='menu_vpn')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🛡️ <b>حزم Hotspot Shield:</b>', reply_markup=markup, parse_mode='HTML')

# --- 8. خدمات ويندوز ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_windows')
def windows_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'🔑 تفعيل مفاتيح ويندوز ({price_text(5)})', callback_data='order_Windows_Activation_$5'),
        InlineKeyboardButton(f'🔑 تفعيل الأوفيس ({price_text(5)})', callback_data='order_Office_Activation_$5'),
        InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='💻 <b>خدمات ويندوز وأوفيس:</b>', reply_markup=markup, parse_mode='HTML')

# --- 9. خدمات مزودين الانترنت ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_internet')
def internet_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('🌐 زاد (ZAD)', callback_data='order_ISP_ZAD'),
        InlineKeyboardButton('🌐 سوا (Sawa)', callback_data='order_ISP_Sawa'),
        InlineKeyboardButton('🌐 رن نت (RunNet)', callback_data='order_ISP_RunNet'),
        InlineKeyboardButton('🌐 السورية للاتصالات (Syrian Telecom)', callback_data='order_ISP_SyrianTelecom'),
        InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home')
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🌐 <b>اختر مزود الانترنت المطلوب:</b>', reply_markup=markup, parse_mode='HTML')

# --- 🔟. خدمات شام كاش ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_sham_cash')
def sham_cash_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('🇸🇾 SYP ➡️ 🇺🇸 USD', callback_data='order_Sham_SYP_USD'),
        InlineKeyboardButton('🇺🇸 USD ➡️ 🇸🇾 SYP', callback_data='order_Sham_USD_SYP'),
        InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home')
    )
    sham_text = (
        '💳 <b>خدمات محفظة شام كاش (SHAM CASH):</b>\n\n'
        'تحويل آمن وسريع بين العملة السورية والأجنبية.\n\n'
        '📊 <b>العمولة:</b> 3%\n\n'
        '👇 <b>اختر الاتجاه:</b>'
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=sham_text, reply_markup=markup, parse_mode='HTML')

# --- 1️⃣1️⃣. خدمة العملاء ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_support')
def support_menu(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'))
    support_text = (
        "📞 <b>خدمة العملاء والدعم الفني - ZEUS</b>\n\n"
        "👤 <b>ALI:</b> <code>0951984521</code>\n"
        "👤 <b>ALAA:</b> <code>0996743743</code>\n"
        "🚨 <b>الشكاوى:</b> <code>0995611608</code>\n\n"
        "نحن في خدمتكم دائماً ❤️"
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=support_text, reply_markup=markup, parse_mode='HTML')

# معالجة الطلبات
@bot.callback_query_handler(func=lambda call: call.data.startswith('order_') or call.data.startswith('chat_'))
def handle_order_selection(call):
    if call.data.startswith('order_Sham_'):
        sham_type = call.data.replace('order_Sham_', '')
        service_name = f"شام كاش ({sham_type.replace('_', ' ➡️ ')})"
    else:
        service_name = call.data.replace('order_', '').replace('chat_', '').replace('_', ' ')

    prompt_text = (
        f"📦 الخدمة: <b>{html.escape(service_name)}</b>\n\n"
        f"✍️ <b>يرجى إرسال تفاصيل الطلب المطلوبة (أو الآيدي/الرقم) في رسالة واحدة:</b>"
    )

    msg = bot.send_message(call.message.chat.id, prompt_text, parse_mode='HTML')
    bot.register_next_step_handler(msg, process_user_order, service_name)

# معالجة مدخلات العميل
def process_user_order(message, service_name):
    user_input = message.text

    if user_input == '🏠 القائمة الرئيسية / Main Menu':
        send_welcome(message)
        return
    elif user_input == '📞 الدعم الفني / Support':
        support_text = (
            "📞 <b>خدمة العملاء والدعم الفني - ZEUS</b>\n\n"
            "👤 <b>ALI:</b> <code>0951984521</code>\n"
            "👤 <b>ALAA:</b> <code>0996743743</code>\n"
            "🚨 <b>الشكاوى:</b> <code>0995611608</code>\n\n"
            "نحن في خدمتكم دائماً ❤️"
        )
        bot.send_message(message.chat.id, support_text, reply_markup=get_persistent_keyboard(), parse_mode='HTML')
        return

    send_order_to_admin(message, service_name, user_input)

    caption_text = (
        f"✅ <b>تم تسجيل طلبك بنجاح بواسطة فريق ZEUS!</b>\n\n"
        f"📦 الخدمة: <b>{html.escape(service_name)}</b>\n"
        f"📱 التفاصيل المرسلة: <code>{html.escape(user_input)}</code>\n\n"
        f"💳 <b>طرق الدفع المتاحة:</b>\n\n"
        f"1️⃣ <b>شام كاش (Sham Cash):</b>\n<code>{SHAM_CASH_WALLET}</code>\n\n"
        f"2️⃣ <b>بينانس TRX (TRC20):</b>\n<code>{TRX_WALLET}</code>\n\n"
        f"3️⃣ <b>بلازما (Plasma):</b>\n<code>{PLASMA_WALLET}</code>\n\n"
        f"📝 <b>بعد التحويل، أرسل رقم العملية أو إيصال الدفع هنا فوراً.</b>"
    )

    try:
        if os.path.exists('sham_cash.jpg'):
            with open('sham_cash.jpg', 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption_text, reply_markup=get_persistent_keyboard(), parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, caption_text, reply_markup=get_persistent_keyboard(), parse_mode='HTML')
    except Exception as e:
        bot.send_message(message.chat.id, caption_text, reply_markup=get_persistent_keyboard(), parse_mode='HTML')
        logging.error(f"Error sending order confirmation response: {e}")

if __name__ == '__main__':
    logging.info("ZEUS Bot is running securely...")
    bot.infinity_polling()
