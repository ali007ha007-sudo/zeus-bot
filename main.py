import os
import threading
import urllib3
from flask import Flask
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

# تعطيل تحذيرات الأمان الخاصة بـ SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إعداد خادم ويب مصغر لاستضافة Render ولضمان عمل البوت 24/7
app = Flask('')


@app.route('/')
def home():
  return 'ZEUS-ECHANCE-BOT is running 24/7!'


def run_web_server():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)


threading.Thread(target=run_web_server).start()

# جلب توكن البوت بأمان من إعدادات منصة Render
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# الآيدي الرقمي الصحيح الخاص بك لتلقي الطلبات
ADMIN_ID = 1632433018

# ==========================================
# 💳 معلومات المحافظ وتفاصيل الدفع (قابلة للتعديل)
# ==========================================
SHAM_CASH_WALLET = '02d28a07292f2a11f12e0d8e2bd08dd1'
BINANCE_PAY_ID = 'User-eb517'
# 🔗 استبدل النص التالي برابط محفظة بينانس الخاص بك بين علامتي التنصيص
BINANCE_LINK = 'https://s.binance.com/ضع_رابطك_هنا'
TRX_WALLET = 'TKva4xbJjCtwGy2vDFAoddsSd91aKZ5zqK'
PLASMA_WALLET = '0xb027c9b07f2b4ffffcf7a56fc80af180f8692c67'

# إعدادات سعر الصرف
USD_TO_SYP_RATE = 14000


def price_text(usd_amount):
  syp_amount = int(usd_amount * USD_TO_SYP_RATE)
  return f'${usd_amount} ({syp_amount:,} ل.س)'


# دالة لوحة المفاتيح الثابتة أسفل المحادثة
def get_persistent_keyboard():
  markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      KeyboardButton('🏠 القائمة الرئيسية / Main Menu'),
      KeyboardButton('📞 الدعم الفني / Support'),
  )
  return markup


# إرسال إشعار الطلب الأولي إلى الإدارة
def send_order_to_admin(message, service_name, user_input):
  user = message.from_user
  notification_text = (
      f'🚨 طلب جديد بانتظار التحويل والتنفيذ!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: `{user.id}`\n'
      f'📱 الحساب أو المعلومات المدخلة: `{user_input}`\n'
      f'📦 الخدمة المطلوبة: {service_name}\n\n'
      f'👉 بانتظار إتمام العميل للتحويل وإرسال إشعار أو رقم عملية التحويل.'
  )
  try:
    bot.send_message(ADMIN_ID, notification_text, parse_mode='Markdown')
  except Exception as e:
    print(f'Error sending notification: {e}')


# استقبال صور إيصالات الدفع من العملاء وتحويلها للإدارة
@bot.message_handler(content_types=['photo'])
def handle_client_photo(message):
  if message.from_user.id == ADMIN_ID:
    return

  user = message.from_user
  photo_file_id = message.photo[-1].file_id

  caption = (
      f'📸 **إيصال دفع جديد (صورة) مرسل من عميل!**\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: `{user.id}`\n\n'
      f'👉 يرجى التحقق من وصول المبلغ على المحفظة لتنفيذ الطلب.'
  )

  try:
    bot.send_photo(
        ADMIN_ID,
        photo_file_id,
        caption=caption,
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
    bot.reply_to(
        message,
        '✅ **تم استلام إيصال الدفع بنجاح!**\nجاري التحقق من قبل الإدارة وتنفيذ طلبك'
        ' في أقرب وقت ❤️',
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
  except Exception as e:
    print(f'Error forwarding payment receipt photo: {e}')


# استقبال أرقام عمليات التحويل النصية من العملاء
@bot.message_handler(
    content_types=['text'],
    func=lambda message: message.from_user.id != ADMIN_ID
    and message.text
    not in [
        '🏠 القائمة الرئيسية / Main Menu',
        '📞 الدعم الفني / Support',
        '/start',
    ],
)
def handle_client_text_receipt(message):
  user = message.from_user
  text_content = message.text

  notification_text = (
      f'💰 **إشعار دفع / رقم عملية تحويل مرسل كنص من عميل!**\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: `{user.id}`\n\n'
      f'📝 **النص أو رقم العملية المرسل:**\n`{text_content}`\n\n'
      f'👉 يرجى مطابقة رقم العملية مع الحساب لتأكيد التحويل.'
  )

  try:
    bot.send_message(
        ADMIN_ID,
        notification_text,
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
    bot.reply_to(
        message,
        '✅ **تم استلام رقم العملية / إشعار الدفع بنجاح!**\nجاري التحقق من قبل الإدارة وتنفيذ طلبك'
        ' في أقرب وقت ❤️',
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
  except Exception as e:
    print(f'Error forwarding text receipt: {e}')


# استجابة الأزرار الثابتة أسفل الشاشة
@bot.message_handler(
    func=lambda message: message.text
    in ['🏠 القائمة الرئيسية / Main Menu', '📞 الدعم الفني / Support']
)
def handle_persistent_buttons(message):
  if message.text == '🏠 القائمة الرئيسية / Main Menu':
    send_welcome(message)
  elif message.text == '📞 الدعم الفني / Support':
    support_text = (
        '📞 **خدمة العملاء والدعم الفني - ZEUS**\n\n'
        'لأي استفسار أو طلب خاص يرجى التواصل مع الإدارة عبر الأرقام التالية:\n\n'
        '👤 **ALI:** `0951984521`\n'
        '👤 **ALAA:** `0996743743`\n'
        '🚨 **الشكاوى:** `0995611608`\n\n'
        'نحن في خدمتكم دائماً ❤️'
    )
    bot.send_message(
        message.chat.id,
        support_text,
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )


# أمر البدء الرئيسي /start والقائمة الرئيسية
@bot.message_handler(commands=['start'])
def send_welcome(message):
  welcome_text = (
      'اهلا بكم في ⚡️ **ZEUS-ECHANCE-BOT** ⚡️ للخدمات الرقمية الشاملة\n\n'
      'نحن فريق من الأشخاص يمتلك الخبرة لنقدم لك كافه خدمات الشحن والدفع الإلكتروني'
      ' بكافة انواعة بشكل آمن وسريع وبدقة عالية من الاحترافية ❤️\n\n'
      'يرجى إختيار القسم المطلوب:'
  )

  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton('1️⃣ الألعاب / GAMES 🎮', callback_data='menu_games'),
      InlineKeyboardButton(
          '2️⃣ التطبيقات الصوتية والدردشة / CHAT APP 💬',
          callback_data='menu_chat',
      ),
      InlineKeyboardButton(
          '3️⃣ تعبئة الرصيد / RECHARGE 💳', callback_data='menu_recharge'
      ),
      InlineKeyboardButton(
          '4️⃣ توثيق الحسابات / ACCOUNTS VERIFICATION 🔐',
          callback_data='menu_verify',
      ),
      InlineKeyboardButton(
          '5️⃣ خدمات متنوعة / Various Services 🌐',
          callback_data='menu_various',
      ),
      InlineKeyboardButton(
          '6️⃣ خدمة تخطي الموقع VPN (بروكسي) 🛡️', callback_data='menu_vpn'
      ),
      InlineKeyboardButton(
          '7️⃣ خدمات ويندوز / WINDOWS SERVICES 💻',
          callback_data='menu_windows',
      ),
      InlineKeyboardButton(
          '8️⃣ خدمات مزودين الانترنت / INTERNET SERVICES 🌐',
          callback_data='menu_internet',
      ),
      InlineKeyboardButton(
          '9️⃣ خدمات شام كاش / SHAM CASH 💸', callback_data='menu_sham_cash'
      ),
      InlineKeyboardButton(
          '🔟 خدمة العملاء / SUPPORT TEAM 📞', callback_data='menu_support'
      ),
  )

  bot.send_message(
      message.chat.id,
      'تم تفعيل لوحة المفاتيح الخاصة بك 👇',
      reply_markup=get_persistent_keyboard(),
  )
  bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode='Markdown')


# زر العودة للقائمة الرئيسية
@bot.callback_query_handler(func=lambda call: call.data == 'back_home')
def back_home(call):
  welcome_text = (
      '⚡ **القائمة الرئيسية - ZEUS-ECHANCE-BOT** ⚡\n\n'
      'يرجى إختيار القسم المطلوب:'
  )
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton('1️⃣ الألعاب / GAMES 🎮', callback_data='menu_games'),
      InlineKeyboardButton(
          '2️⃣ التطبيقات الصوتية والدردشة / CHAT APP 💬',
          callback_data='menu_chat',
      ),
      InlineKeyboardButton(
          '3️⃣ تعبئة الرصيد / RECHARGE 💳', callback_data='menu_recharge'
      ),
      InlineKeyboardButton(
          '4️⃣ توثيق الحسابات / ACCOUNTS VERIFICATION 🔐',
          callback_data='menu_verify',
      ),
      InlineKeyboardButton(
          '5️⃣ خدمات متنوعة / Various Services 🌐',
          callback_data='menu_various',
      ),
      InlineKeyboardButton(
          '6️⃣ خدمة تخطي الموقع VPN (بروكسي) 🛡️', callback_data='menu_vpn'
      ),
      InlineKeyboardButton(
          '7️⃣ خدمات ويندوز / WINDOWS SERVICES 💻',
          callback_data='menu_windows',
      ),
      InlineKeyboardButton(
          '8️⃣ خدمات مزودين الانترنت / INTERNET SERVICES 🌐',
          callback_data='menu_internet',
      ),
      InlineKeyboardButton(
          '9️⃣ خدمات شام كاش / SHAM CASH 💸', callback_data='menu_sham_cash'
      ),
      InlineKeyboardButton(
          '🔟 خدمة العملاء / SUPPORT TEAM 📞', callback_data='menu_support'
      ),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=welcome_text,
      reply_markup=markup,
      parse_mode='Markdown',
  )


# معالجة الطلبات واختيار الخدمات
@bot.callback_query_handler(
    func=lambda call: call.data.startswith('order_')
    or call.data.startswith('chat_')
)
def handle_order_selection(call):
  service_name = (
      call.data.replace('order_', '')
      .replace('chat_', '')
      .replace('_', ' ')
  )

  prompt_text = (
      f'📦 الخدمة المختارة: {service_name}\n\n'
      f'✍️ **يرجى إرسال رقم (ID)، رابط الحساب، أو تفاصيل الطلب المطلوبة في رسالة واحدة:**'
  )

  msg = bot.send_message(
      call.message.chat.id, prompt_text, parse_mode='Markdown'
  )
  bot.register_next_step_handler(msg, process_user_order, service_name)


# إرسال بيانات الدفع والمحافظ والباركودات للعميل بعد إرسال طلبه
def process_user_order(message, service_name):
  user_input = message.text

  send_order_to_admin(message, service_name, user_input)

  caption_text = (
      f'✅ **تم تسجيل طلبك بنجاح بواسطة فريق ZEUS!**\n\n'
      f'📦 الخدمة: {service_name}\n'
      f'📱 التفاصيل المرسلة: `{user_input}`\n\n'
      f'💳 **طرق الدفع المتاحة:**\n\n'
      f'1️⃣ **محفظة شام كاش (Sham Cash):**\n'
      f'رقم المحفظة (اضغط للنسخ):\n'
      f'`{SHAM_CASH_WALLET}`\n\n'
      f'2️⃣ **بينانس والعملات الرقمية (Binance & Crypto):**\n'
      f'• Binance Pay ID:\n`{BINANCE_PAY_ID}`\n\n'
      f'• رابط محفظة بينانس:\n{BINANCE_LINK}\n\n'
      f'• عنوان محفظة TRX (TRC20):\n`{TRX_WALLET}`\n\n'
      f'• عنوان محفظة Plasma / EVM:\n`{PLASMA_WALLET}`\n\n'
      f'📝 **بعد إتمام التحويل، يرجى إرسال رقم عملية التحويل أو نص الإشعار أو صورة إيصال الدفع هنا في المحادثة** لكي يصل إلى الإدارة فوراً وتنفيذ طلبك.'
  )

  try:
    # إرسال باركود شام كاش إن وجد
    if os.path.exists('sham_cash.jpg'):
      with open('sham_cash.jpg', 'rb') as photo1:
        bot.send_photo(
            message.chat.id,
            photo1,
            caption='📸 **باركود شام كاش:**',
            parse_mode='Markdown',
        )

    # إرسال باركود بينانس إن وجد
    if os.path.exists('binance.jpg'):
      with open('binance.jpg', 'rb') as photo2:
        bot.send_photo(
            message.chat.id,
            photo2,
            caption='🟡 **باركود بينانس (Binance):**',
            parse_mode='Markdown',
        )

    # إرسال تفاصيل المحافظ وطرق الدفع
    bot.send_message(
        message.chat.id,
        caption_text,
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
  except Exception as e:
    bot.send_message(
        message.chat.id,
        caption_text,
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
    print(f'Error sending payment details: {e}')


if __name__ == '__main__':
  print('ZEUS Bot is running...')
  bot.infinity_polling()
