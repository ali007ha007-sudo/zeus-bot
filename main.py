from datetime import datetime
import os
import sqlite3
import threading
import re
from flask import Flask
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
import urllib3

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


threading.Thread(target=run_web_server, daemon=True).start()

# جلب توكن البوت بأمان من إعدادات منصة Render
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# الآيدي الرقمي الصحيح الخاص بك لتلقي الطلبات
ADMIN_ID = 1632433018

# ==========================================
# 🗄️ إعداد قاعدة البيانات الآمنة للمحافظ والأرصدة
# ==========================================


def init_db():
  try:
    conn = sqlite3.connect('zeus_wallet.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 0.0
            )
        ''')
    conn.commit()
    conn.close()
  except Exception as e:
    print(f'Database init error: {e}')


init_db()


def get_user_balance(user_id, username, first_name):
  try:
    conn = sqlite3.connect('zeus_wallet.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT balance FROM users WHERE user_id = ?', (user_id,)
    )
    row = cursor.fetchone()
    if row is None:
      cursor.execute(
          'INSERT INTO users (user_id, username, first_name, balance) VALUES'
          ' (?, ?, ?, 0.0)',
          (user_id, username, first_name),
      )
      conn.commit()
      balance = 0.0
    else:
      balance = row[0]
    conn.close()
    return balance
  except Exception as e:
    print(f'Error getting balance: {e}')
    return 0.0


def update_user_balance(user_id, amount):
  try:
    conn = sqlite3.connect('zeus_wallet.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET balance = balance + ? WHERE user_id = ?',
        (amount, user_id),
    )
    conn.commit()
    conn.close()
  except Exception as e:
    print(f'Error updating balance: {e}')


# ==========================================
# 💳 إعدادات المحافظ وطرق الدفع
# ==========================================
SHAM_CASH_WALLET = '02d28a07292f2a11f12e0d8e2bd08dd1'
TRX_WALLET = 'TKva4xbJjCtwGy2vDFAoddsSd91aKZ5zqK'
PLASMA_WALLET = '0xb027c9b07f2b4ffffcf7a56fc80af180f8692c67'

# ==========================================
# 💱 إعدادات سعر الصرف (سعر السوق السوداء - قابل للتعديل)
# ==========================================
USD_TO_SYP_RATE = 14000


def price_text(usd_amount):
  syp_amount = int(usd_amount * USD_TO_SYP_RATE)
  return f'${usd_amount} ({syp_amount:,} ل.س)'


# لوحة المفاتيح الثابتة المحدثة (تتضمن زر المحفظة)
def get_persistent_keyboard():
  markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      KeyboardButton('🏠 القائمة الرئيسية / Main Menu'),
      KeyboardButton('💰 محفظتي / My Wallet'),
      KeyboardButton('📞 الدعم الفني / Support'),
  )
  return markup


def get_support_markup():
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '👤 مراسلة ALI (تليجرام)', url='https://t.me/Ali00700Ali'
      ),
      InlineKeyboardButton(
          '👤 مراسلة ALAA (تليجرام)', url='https://t.me/Alaaoo7'
      ),
      InlineKeyboardButton(
          '🚨 قسم الشكاوى والاستفسارات', url='https://t.me/Ali00700Ali'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  return markup


# دالة إرسال الطلب للإدارة مع زر لإضافة رصيد للعميل مباشرة
def send_order_to_admin(message, service_name, user_input):
  user = message.from_user
  notification_text = (
      f'🚨 طلب جديد بانتظار التحويل والتنفيذ!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: {user.id}\n'
      f'📱 الحساب أو المعلومات المدخلة: {user_input}\n'
      f'📦 الخدمة المطلوبة: {service_name}\n\n'
      f'👉 بانتظار إتمام العميل للتحويل أو خصم المبلغ من رصيده.'
  )
  try:
    bot.send_message(ADMIN_ID, notification_text)
  except Exception as e:
    print(f'Error sending notification: {e}')


# 📸 استقبال صور إيصالات الدفع
@bot.message_handler(content_types=['photo'])
def handle_client_photo(message):
  if message.from_user.id == ADMIN_ID:
    return

  user = message.from_user
  photo_file_id = message.photo[-1].file_id

  caption = (
      f'📸 إيصال دفع جديد (صورة) مرسل من عميل لشحن المحفظة أو الطلب!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: {user.id}\n\n'
      f'👉 للتحقق من الشحن، قم بالرد على هذه الرسالة بالأمر:\n'
      f'`/add {user.id} [المبلغ]` (مثال: `/add {user.id} 10` لإضافة 10 دولار لرصيده).'
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
        '✅ **تم استلام إيصال الدفع بنجاح!**\nجاري التحقق من قبل الإدارة وشحن'
        ' رصيدك أو تنفيذ طلبك ❤️',
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
  except Exception as e:
    print(f'Error forwarding payment receipt photo: {e}')


# 💳 استقبال النصوص ورسائل التحويل
@bot.message_handler(
    content_types=['text'],
    func=lambda message: message.from_user.id != ADMIN_ID
    and message.text
    not in [
        '🏠 القائمة الرئيسية / Main Menu',
        '💰 محفظتي / My Wallet',
        '📞 الدعم الفني / Support',
        '/start',
    ],
)
def handle_client_text_receipt(message):
  if message.text.startswith('/add'):
    return

  user = message.from_user
  text_content = message.text

  notification_text = (
      f'💰 إشعار دفع / رقم عملية تحويل مرسل كنص من عميل!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: {user.id}\n\n'
      f'📝 النص أو رقم العملية المرسل:\n`{text_content}`\n\n'
      f'👉 للشحن اليدوي، رد على الرسالة بالأمر: `/add {user.id} [المبلغ]`'
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
        '✅ **تم استلام رقم العملية / إشعار الدفع بنجاح!**\nجاري التحقق من قبل'
        ' الإدارة وإضافة الرصيد/تنفيذ الطلب خلال 60 دقيقة ❤️',
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
  except Exception as e:
    print(f'Error forwarding text receipt: {e}')


# ==========================================
# 🛠️ أوامر الأدمن لشحن محافظ العملاء
# ==========================================
@bot.message_handler(commands=['add'])
def admin_add_balance(message):
  if message.from_user.id != ADMIN_ID:
    return
  try:
    parts = message.text.split()
    if len(parts) < 3:
      bot.reply_to(
          message,
          '⚠️ صيغة خاطئة. استخدم الأمر هكذا:\n`/add [user_id] [المبلغ بالدولار]`',
          parse_mode='Markdown',
      )
      return

    target_user_id = int(parts[1])
    amount = float(parts[2])

    update_user_balance(target_user_id, amount)

    bot.send_message(
        target_user_id,
        f'🎉 **تم شحن محفظتك بنجاح!**\n💵 المبلغ المضاف: **${amount}**',
        parse_mode='Markdown',
    )
    bot.reply_to(
        message,
        f'✅ تم إضافة ${amount} بنجاح إلى حساب المستخدم {target_user_id}.',
    )
  except Exception as e:
    bot.reply_to(message, f'❌ حدث خطأ: {e}')


@bot.message_handler(
    func=lambda message: message.from_user.id == ADMIN_ID
    and message.reply_to_message
)
def admin_reply_to_client(message):
  try:
    replied_msg = message.reply_to_message
    replied_text = replied_msg.text or replied_msg.caption

    if not replied_text:
      return

    match = re.search(r'🔢 الآيدي:\s*(\d+)', replied_text)
    if match:
      client_id = int(match.group(1))
      admin_text = message.text

      bot.send_message(
          client_id,
          f'🎉 **تحديث بخصوص طلبك من ZEUS:**\n\n{admin_text}',
          reply_markup=get_persistent_keyboard(),
          parse_mode='Markdown',
      )

      bot.reply_to(
          message, '✅ **تم إرسال إشعار اكتمال الطلب للعميل بنجاح!**'
      )
  except Exception as e:
    print(f'Error sending reply to client: {e}')


# ==========================================
# 🎛️ أزرار القوائم والتحكم
# ==========================================


@bot.message_handler(
    func=lambda message: message.text
    in [
        '🏠 القائمة الرئيسية / Main Menu',
        '💰 محفظتي / My Wallet',
        '📞 الدعم الفني / Support',
    ]
)
def handle_persistent_buttons(message):
  if message.text == '🏠 القائمة الرئيسية / Main Menu':
    send_welcome(message)
  elif message.text == '💰 محفظتي / My Wallet':
    user = message.from_user
    balance = get_user_balance(user.id, user.username, user.first_name)
    syp_balance = int(balance * USD_TO_SYP_RATE)

    wallet_text = (
        f'💰 **إدارة محفظتك الشخصية - ZEUS**\n\n'
        f'👤 المستخدم: {user.first_name}\n'
        f'🆔 الآيدي: `{user.id}`\n\n'
        f'💵 **رصيدك الحالي:**\n'
        f'• **${balance:.2f}** دولار أمريكي\n'
        f'• **{syp_balance:,}** ليرة سورية\n\n'
        f'📌 يمكنك شحن رصيد محفظتك عبر تحويل المبلغ إلى أحد عناويننا أدناه ثم إرسال الإيصال (صورة أو رقم عملية):'
    )

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            '💳 عرض تفاصيل محافظ الدفع لشحن الرصيد',
            callback_data='show_deposit_methods',
        ),
        InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
    )

    bot.send_message(
        message.chat.id,
        wallet_text,
        reply_markup=markup,
        parse_mode='Markdown',
    )
  elif message.text == '📞 الدعم الفني / Support':
    support_text = (
        '📞 **خدمة العملاء والدعم الفني - ZEUS**\n\n'
        'لأي استفسار أو طلب خاص يرجى التواصل المباشر مع الإدارة عبر الأزرار أدناه:'
    )
    bot.send_message(
        message.chat.id,
        support_text,
        reply_markup=get_support_markup(),
        parse_mode='Markdown',
    )


@bot.callback_query_handler(func=lambda call: call.data == 'show_deposit_methods')
def show_deposit_methods(call):
  deposit_text = (
      f'💳 **طرق شحن المحفظة (اختر الطريقة المناسبة):**\n\n'
      f'1️⃣ **شام كاش (Sham Cash):**\n`{SHAM_CASH_WALLET}`\n\n'
      f'2️⃣ **بينانس TRX (TRC20):**\n`{TRX_WALLET}`\n\n'
      f'3️⃣ **بلازما (Plasma):**\n`{PLASMA_WALLET}`\n\n'
      f'📝 **بعد إتمام التحويل، يرجى إرسال صورة الإيصال أو رقم العملية هنا في المحادثة** لتقوم الإدارة بشحن رصيدك فوراً.'
  )
  markup = InlineKeyboardMarkup()
  markup.add(InlineKeyboardButton('🔙 رجوع للمحفظة', callback_data='back_wallet'))
  try:
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=deposit_text,
        reply_markup=markup,
        parse_mode='Markdown',
    )
  except Exception:
    pass


@bot.callback_query_handler(func=lambda call: call.data == 'back_wallet')
def back_wallet_handler(call):
  user = call.from_user
  balance = get_user_balance(user.id, user.username, user.first_name)
  syp_balance = int(balance * USD_TO_SYP_RATE)
  wallet_text = (
      f'💰 **إدارة محفظتك الشخصية - ZEUS**\n\n'
      f'👤 المستخدم: {user.first_name}\n'
      f'🆔 الآيدي: `{user.id}`\n\n'
      f'💵 **رصيدك الحالي:**\n'
      f'• **${balance:.2f}** دولار أمريكي\n'
      f'• **{syp_balance:,}** ليرة سورية'
  )
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '💳 عرض تفاصيل محافظ الدفع لشحن الرصيد',
          callback_data='show_deposit_methods',
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  try:
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=wallet_text,
        reply_markup=markup,
        parse_mode='Markdown',
    )
  except Exception:
    pass


# أمر البدء الرئيسي /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
  welcome_text = (
      'اهلا بكم في ⚡️ **ZEUS SERVICES -BOT** ⚡️ للخدمات الرقمية الشاملة\n\n'
      'نحن فريق يمتلك الخبرة لنقدم لك كافه خدمات الشحن والدفع الإلكتروني'
      ' بكافة أنواعه بشكل آمن وسريع وبدقة عالية ❤️\n\n'
      'يرجى إختيار القسم المطلوب:'
  )

  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton('1️⃣ الألعاب / GAMES 🎮', callback_data='menu_games'),
      InlineKeyboardButton(
          '2️⃣ الذكاء الاصطناعي / AI 💭', callback_data='menu_ai'
      ),
      InlineKeyboardButton(
          '3️⃣ التطبيقات الصوتية والدردشة / CHAT APP 💬',
          callback_data='menu_chat',
      ),
      InlineKeyboardButton(
          '4️⃣ تعبئة الرصيد / RECHARGE 💳', callback_data='menu_recharge'
      ),
      InlineKeyboardButton(
          '5️⃣ توثيق الحسابات / ACCOUNTS VERIFICATION 🔐',
          callback_data='menu_verify',
      ),
      InlineKeyboardButton(
          '6️⃣ خدمات متنوعة / Various Services 🌐',
          callback_data='menu_various',
      ),
      InlineKeyboardButton(
          '7️⃣ خدمة تخطي الموقع VPN (بروكسي) 🛡️', callback_data='menu_vpn'
      ),
      InlineKeyboardButton(
          '8️⃣ خدمات ويندوز / WINDOWS SERVICES 💻',
          callback_data='menu_windows',
      ),
      InlineKeyboardButton(
          '9️⃣ خدمات مزودين الانترنت / INTERNET SERVICES 🌐',
          callback_data='menu_internet',
      ),
      InlineKeyboardButton(
          '🔟 خدمات شام كاش / SHAM CASH 💸', callback_data='menu_sham_cash'
      ),
      InlineKeyboardButton(
          '1️⃣1️⃣ خدمة العملاء / SUPPORT TEAM 📞', callback_data='menu_support'
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
          '2️⃣ الذكاء الاصطناعي / AI 💭', callback_data='menu_ai'
      ),
      InlineKeyboardButton(
          '3️⃣ التطبيقات الصوتية والدردشة / CHAT APP 💬',
          callback_data='menu_chat',
      ),
      InlineKeyboardButton(
          '4️⃣ تعبئة الرصيد / RECHARGE 💳', callback_data='menu_recharge'
      ),
      InlineKeyboardButton(
          '5️⃣ توثيق الحسابات / ACCOUNTS VERIFICATION 🔐',
          callback_data='menu_verify',
      ),
      InlineKeyboardButton(
          '6️⃣ خدمات متنوعة / Various Services 🌐',
          callback_data='menu_various',
      ),
      InlineKeyboardButton(
          '7️⃣ خدمة تخطي الموقع VPN (بروكسي) 🛡️', callback_data='menu_vpn'
      ),
      InlineKeyboardButton(
          '8️⃣ خدمات ويندوز / WINDOWS SERVICES 💻',
          callback_data='menu_windows',
      ),
      InlineKeyboardButton(
          '9️⃣ خدمات مزودين الانترنت / INTERNET SERVICES 🌐',
          callback_data='menu_internet',
      ),
      InlineKeyboardButton(
          '🔟 خدمات شام كاش / SHAM CASH 💸', callback_data='menu_sham_cash'
      ),
      InlineKeyboardButton(
          '1️⃣1️⃣ خدمة العملاء / SUPPORT TEAM 📞', callback_data='menu_support'
      ),
  )
  try:
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=welcome_text,
        reply_markup=markup,
        parse_mode='Markdown',
    )
  except Exception:
    pass


@bot.callback_query_handler(
    func=lambda call: call.data.startswith('order_')
    or call.data.startswith('chat_')
)
def handle_order_selection(call):
  if call.data.startswith('order_Sham_'):
    sham_type = call.data.replace('order_Sham_', '')
    service_name = f'شام كاش ({sham_type})'
  else:
    service_name = (
        call.data.replace('order_', '').replace('chat_', '').replace('_', ' ')
    )

  prompt_text = (
      f'📦 الخدمة المختارة: {service_name}\n\n'
      f'✍ **يرجى إرسال رقم (ID)، رابط الحساب، أو تفاصيل الطلب المطلوبة في رسالة واحدة:**'
  )

  try:
    msg = bot.send_message(
        call.message.chat.id, prompt_text, parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_user_order, service_name)
  except Exception as e:
    print(f'Error in order selection: {e}')


def process_user_order(message, service_name):
  user_input = message.text

  if user_input in [
      '🏠 القائمة الرئيسية / Main Menu',
      '💰 محفظتي / My Wallet',
      '📞 الدعم الفني / Support',
  ]:
    return

  send_order_to_admin(message, service_name, user_input)

  caption_text = (
      f'✅ **تم تسجيل طلبك بنجاح بواسطة فريق ZEUS!**\n\n'
      f'📦 الخدمة: {service_name}\n'
      f'📱 التفاصيل المرسلة: `{user_input}`\n\n'
      f'💳 **طرق الدفع أو شحن المحفظة المتاحة:**\n\n'
      f'1️⃣ **شام كاش (Sham Cash):**\n`{SHAM_CASH_WALLET}`\n\n'
      f'2️⃣ **بينانس TRX (TRC20):**\n`{TRX_WALLET}`\n\n'
      f'3️⃣ **بلازما (Plasma):**\n`{PLASMA_WALLET}`\n\n'
      f'📝 **بعد التحويل، أرسل رقم العملية أو إيصال الدفع هنا ليتم تنفيذ طلبك.**'
  )

  try:
    bot.send_message(
        message.chat.id,
        caption_text,
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
  except Exception as e:
    print(f'Error in process_user_order: {e}')


if __name__ == '__main__':
  print('ZEUS Bot is running...')
  while True:
    try:
      bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
      print(f'Polling error occurred: {e}')
