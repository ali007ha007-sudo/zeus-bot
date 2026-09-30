import os
import threading
import re
import sqlite3
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
  return 'ZEUS-ECHANCE-BOT with User Wallets is running 24/7!'


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
# 💳 إعدادات محافظ الإدارة (لتعبئة الرصيد)
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


# ==========================================
# 🗄️ إعداد قاعدة البيانات لتخزين أرصدة العملاء
# ==========================================
def init_db():
  conn = sqlite3.connect('zeus_wallets.db', check_same_thread=False)
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


init_db()


def get_user_balance(user_id, username, first_name):
  conn = sqlite3.connect('zeus_wallets.db', check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
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


def update_user_balance(user_id, amount):
  conn = sqlite3.connect('zeus_wallets.db', check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute(
      'UPDATE users SET balance = balance + ? WHERE user_id = ?',
      (amount, user_id),
  )
  conn.commit()
  conn.close()


# دالة لوحة المفاتيح الثابتة (تظهر دائماً أسفل محادثة العميل)
def get_persistent_keyboard():
  markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      KeyboardButton('🏠 القائمة الرئيسية / Main Menu'),
      KeyboardButton('💰 محفظتي / My Wallet'),
      KeyboardButton('📞 الدعم الفني / Support'),
  )
  return markup


# دالة أزرار التواصل المباشر مع الإدارة (تليجرام)
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


# أمر البدء الرئيسي /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
  get_user_balance(
      message.from_user.id,
      message.from_user.username,
      message.from_user.first_name,
  )
  welcome_text = (
      'اهلا بكم في ⚡️ **ZEUS SERVICES -BOT** ⚡️ للخدمات الرقمية الشاملة\n\n'
      'نحن فريق من الأشخاص يمتلك الخبرة لنقدم لك كافه خدمات الشحن والدفع الإلكتروني'
      ' بكافة انواعة بشكل آمن وسريع وبدقة عالية من الاحترافية ❤️\n\n'
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
          '1️⃣1️⃣ محفظتي ورصيدي / MY WALLET 💰', callback_data='menu_my_wallet'
      ),
      InlineKeyboardButton(
          '1️⃣2️⃣ خدمة العملاء / SUPPORT TEAM 📞', callback_data='menu_support'
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
          '1️⃣1️⃣ محفظتي ورصيدي / MY WALLET 💰', callback_data='menu_my_wallet'
      ),
      InlineKeyboardButton(
          '1️⃣2️⃣ خدمة العملاء / SUPPORT TEAM 📞', callback_data='menu_support'
      ),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=welcome_text,
      reply_markup=markup,
      parse_mode='Markdown',
  )


# عرض محفظة العميل عند الضغط على الزر
@bot.callback_query_handler(func=lambda call: call.data == 'menu_my_wallet')
def user_wallet_menu(call):
  user = call.from_user
  balance = get_user_balance(user.id, user.username, user.first_name)

  wallet_text = (
      f'💰 **محفظتك الشخصية في بوت ZEUS**\n\n'
      f'👤 اسم المستخدم: {user.first_name}\n'
      f'🆔 الآيدي الخاص بك: `{user.id}`\n\n'
      f'💵 **رصيدك الحالي:** `${balance:.2f}`\n\n'
      '━━━━━━━━━━━━━━━━━━\n'
      '💳 **شحن الرصيد:**\n'
      'لشحن رصيدك في المحفظة، قم بالتحويل إلى إحدى محافظ الإدارة التالية:\n\n'
      f'1️⃣ **شام كاش:**\n`{SHAM_CASH_WALLET}`\n\n'
      f'2️⃣ **بينانس TRX:**\n`{TRX_WALLET}`\n\n'
      f'3️⃣ **بلازما:**\n`{PLASMA_WALLET}`\n\n'
      '📸 *بعد التحويل، أرسل إيصال الدفع أو رقم العملية هنا في المحادثة مع ذكر عبارة (شحن رصيد) ليتم إضافته لمحفظتك فوراً.*'
  )

  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'))

  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=wallet_text,
      reply_markup=markup,
      parse_mode='Markdown',
  )


# استجابة الأزرار الثابتة (من ضمنها محفظتي)
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
    wallet_text = (
        f'💰 **محفظتك الشخصية في بوت ZEUS**\n\n'
        f'👤 اسم المستخدم: {user.first_name}\n'
        f'🆔 الآيدي الخاص بك: `{user.id}`\n\n'
        f'💵 **رصيدك الحالي:** `${balance:.2f}`\n\n'
        '━━━━━━━━━━━━━━━━━━\n'
        '💳 **شحن الرصيد:**\n'
        'لشحن رصيدك، قم بالتحويل إلى إحدى محافظ الإدارة:\n\n'
        f'1️⃣ **شام كاش:**\n`{SHAM_CASH_WALLET}`\n\n'
        f'2️⃣ **بينانس TRX:**\n`{TRX_WALLET}`\n\n'
        f'3️⃣ **بلازما:**\n`{PLASMA_WALLET}`\n\n'
        '📸 *بعد التحويل، أرسل إيصال الدفع أو رقم العملية هنا لتتم الإضافة لمحفظتك.*'
    )
    bot.send_message(
        message.chat.id,
        wallet_text,
        reply_markup=get_persistent_keyboard(),
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


# --- أقسام البوت (ألعاب، ذكاء اصطناعي، دردشة، إلخ) ---
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
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🎮 **اختر اللعبة المطلوبة:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith('game_'))
def game_packages(call):
  game = call.data.split('_')[1]
  markup = InlineKeyboardMarkup(row_width=1)

  if game == 'pubg':
    markup.add(
        InlineKeyboardButton(
            f'PUBG: 60 شدة ({price_text(1.2)})',
            callback_data='order_PUBG_60_UC_$1.2',
        ),
        InlineKeyboardButton(
            f'PUBG: 325 شدة ({price_text(5.5)})',
            callback_data='order_PUBG_325_UC_$5.5',
        ),
        InlineKeyboardButton(
            f'PUBG: 660 شدة ({price_text(10.2)})',
            callback_data='order_PUBG_660_UC_$10.2',
        ),
        InlineKeyboardButton(
            f'PUBG: 1800 شدة ({price_text(24.8)})',
            callback_data='order_PUBG_1800_UC_$24.8',
        ),
        InlineKeyboardButton(
            f'PUBG: 3800 شدة ({price_text(49.7)})',
            callback_data='order_PUBG_3800_UC_$49.7',
        ),
        InlineKeyboardButton(
            f'PUBG: 8100 شدة ({price_text(90.2)})',
            callback_data='order_PUBG_8100_UC_$90.2',
        ),
    )
  elif game == 'freefire':
    markup.add(
        InlineKeyboardButton(
            f'Free Fire: 110 جوهرة ({price_text(1.5)})',
            callback_data='order_FreeFire_110_Gems_$1.5',
        ),
        InlineKeyboardButton(
            f'Free Fire: 231 جوهرة ({price_text(2.5)})',
            callback_data='order_FreeFire_231_Gems_$2.5',
        ),
        InlineKeyboardButton(
            f'Free Fire: 583 جوهرة ({price_text(5.8)})',
            callback_data='order_FreeFire_583_Gems_$5.8',
        ),
        InlineKeyboardButton(
            f'Free Fire: 1200 جوهرة ({price_text(11)})',
            callback_data='order_FreeFire_1200_Gems_$11',
        ),
    )
  elif game == 'jawaker':
    markup.add(
        InlineKeyboardButton(
            f'Jawaker: 10,000 جوهرة ({price_text(1.8)})',
            callback_data='order_Jawaker_10k_Gems_$1.8',
        ),
        InlineKeyboardButton(
            f'Jawaker: 20,000 جوهرة ({price_text(3.2)})',
            callback_data='order_Jawaker_20k_Gems_$3.2',
        ),
    )
  elif game == 'clash':
    markup.add(
        InlineKeyboardButton(
            f'Clash: 80 جوهرة ({price_text(2)})',
            callback_data='order_Clash_80_Gems_$2',
        ),
        InlineKeyboardButton(
            f'Clash: 500 جوهرة ({price_text(8)})',
            callback_data='order_Clash_500_Gems_$8',
        ),
    )
  elif game == 'cod':
    markup.add(
        InlineKeyboardButton(
            f'Call of Duty: 30 CP ({price_text(0.8)})',
            callback_data='order_COD_30_CP_$0.8',
        ),
        InlineKeyboardButton(
            f'Call of Duty: 80 CP ({price_text(2.1)})',
            callback_data='order_COD_80_CP_$2.1',
        ),
        InlineKeyboardButton(
            f'Call of Duty: 420 CP ({price_text(7.5)})',
            callback_data='order_COD_420_CP_$7.5',
        ),
        InlineKeyboardButton(
            f'Call of Duty: 880 CP ({price_text(14.1)})',
            callback_data='order_COD_880_CP_$14.1',
        ),
    )
  elif game == 'fortnite':
    markup.add(
        InlineKeyboardButton(
            f'Fortnite: 2800 بطاقة ({price_text(32.9)})',
            callback_data='order_Fortnite_2800_$32.9',
        ),
        InlineKeyboardButton(
            f'Fortnite: 5000 بطاقة ({price_text(54.9)})',
            callback_data='order_Fortnite_5000_$54.9',
        ),
    )

  markup.add(InlineKeyboardButton('🔙 رجوع', callback_data='menu_games'))
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🎮 **حزم قسم الألعاب:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'menu_ai')
def ai_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'ChatGPT Plus: تفعيل شخصي ({price_text(19)})',
          callback_data='order_AI_ChatGPT_Plus_شهر1_$19',
      ),
      InlineKeyboardButton(
          f'Gemini AI: 6 Months ({price_text(12)})',
          callback_data='order_AI_Gemini_6 Months _$12',
      ),
      InlineKeyboardButton(
          f'CapCut Pro: 1 Month ({price_text(15)})',
          callback_data='order_AI_CapCut_1 Month $15',
      ),
      InlineKeyboardButton(
          f'Canva Pro: 12 Months ({price_text(14)})',
          callback_data='order_AI_Canva_12 Months _$14',
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💭 **اختر خدمة الذكاء الاصطناعي المطلوبة:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


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
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💬 **اختر التطبيق المطلوب:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'chat_bigo')
def bigo_packages(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Bigo: 100 PC ({price_text(2.1)})',
          callback_data='order_Bigo_100_PC_$2.1',
      ),
      InlineKeyboardButton(
          f'Bigo: 300 PC ({price_text(5.8)})',
          callback_data='order_Bigo_300_PC_$5.8',
      ),
      InlineKeyboardButton(
          f'Bigo: 500 PC ({price_text(9.5)})',
          callback_data='order_Bigo_500_PC_$9.5',
      ),
      InlineKeyboardButton(
          f'Bigo: 1000 PC ({price_text(18.7)})',
          callback_data='order_Bigo_1000_PC_$18.7',
      ),
      InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🔴 **حزم Bigo Live:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'menu_recharge')
def recharge_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '📱 رصيد سيريتل / Syriatel', callback_data='order_Recharge_Syriatel'
      ),
      InlineKeyboardButton(
          '📱 رصيد إم تي إن / MTN', callback_data='order_Recharge_MTN'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💳 **اختر خدمة التعبئة المطلوبة:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'menu_verify')
def verify_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'YouTube: 1 Month ({price_text(4.5)})',
          callback_data='order_YouTube_1 Month _$4.5',
      ),
      InlineKeyboardButton(
          f'Telegram: 3 Months ({price_text(15)})',
          callback_data='order_Telegram_3 Months _$15',
      ),
      InlineKeyboardButton(
          f'Snapchat: 3 Months ({price_text(7)})',
          callback_data='order_Snapchat_3 Months _$7',
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🔐 **خدمات توثيق الحسابات:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'menu_various')
def various_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'🤖 رد آلي فيسبوك (1 Month {price_text(4.8)})',
          callback_data='order_FB_Bot_1 Month _$4.8',
      ),
      InlineKeyboardButton(
          f'👥 متابعين فيسبوك: 1000 متابع ({price_text(2)})',
          callback_data='order_FB_1k_$2',
      ),
      InlineKeyboardButton(
          f'📸 متابعين إنستغرام: 1000 متابع ({price_text(4)})',
          callback_data='order_IG_1k_$4',
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🌐 **الخدمات المتنوعة:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'menu_vpn')
def vpn_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Open VPN: 1 Month ({price_text(2)})',
          callback_data='order_OpenVPN_1 Month _$2',
      ),
      InlineKeyboardButton(
          f'Express VPN: 1 Month ({price_text(6)})',
          callback_data='order_ExpressVPN_1 Month _$6',
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🛡️ **خدمات VPN:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'menu_windows')
def windows_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'🔑 تفعيل ويندوز ({price_text(5)})',
          callback_data='order_Windows_Activation_$5',
      ),
      InlineKeyboardButton(
          f'🔑 تفعيل أوفيس ({price_text(5)})',
          callback_data='order_Office_Activation_$5',
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💻 **خدمات ويندوز وأوفيس:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'menu_internet')
def internet_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton('🌐 زاد (ZAD)', callback_data='order_ISP_ZAD'),
      InlineKeyboardButton('🌐 سوا (Sawa)', callback_data='order_ISP_Sawa'),
      InlineKeyboardButton('🌐 رن نت (RunNet)', callback_data='order_ISP_RunNet'),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🌐 **مزودين الانترنت:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'menu_sham_cash')
def sham_cash_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '🇸🇾 SYP ➡ 🇺🇸 USD', callback_data='order_Sham_SYP_USD'
      ),
      InlineKeyboardButton(
          '🇺🇸 USD ➡️ 🇸🇾 SYP', callback_data='order_Sham_USD_SYP'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💳 **خدمات شام كاش:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'menu_support')
def support_menu(call):
  support_text = (
      '📞 **خدمة العملاء والدعم الفني - ZEUS**\n\n'
      'لأي استفسار أو طلب خاص يرجى التواصل المباشر مع الإدارة عبر الأزرار أدناه:'
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=support_text,
      reply_markup=get_support_markup(),
      parse_mode='Markdown',
  )


# ==========================================
# 📸📸 استقبال الإيصالات والصور (مع إمكانية شحن رصيد العميل أوتوماتيكياً من الإدارة)
# ==========================================
@bot.message_handler(content_types=['photo'])
def handle_client_photo(message):
  if message.from_user.id == ADMIN_ID:
    return

  user = message.from_user
  photo_file_id = message.photo[-1].file_id

  caption = (
      f'📸 إيصال دفع جديد (صورة) مرسل من عميل!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: {user.id}\n\n'
      f'👉 للتحقق وإضافة المبلغ إلى محفظة العميل، قم بالرد على هذه الرسالة بالأمر:\n'
      f'`+رصيد` (مثال: `+10` لإضافة 10 دولار لرصيده).'
  )

  try:
    bot.send_photo(
        ADMIN_ID,
        photo_file_id,
        caption=caption,
        reply_markup=get_persistent_keyboard(),
    )
    bot.reply_to(
        message,
        '✅ **تم استلام إيصال الدفع بنجاح!**\nجاري التحقق من قبل الإدارة لإضافة'
        ' الرصيد أو تنفيذ طلبك ❤️',
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
  except Exception as e:
    print(f'Error forwarding photo: {e}')


# 💰 استقبال النصوص أو أرقام عمليات التحويل
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
  user = message.from_user
  text_content = message.text

  notification_text = (
      f'💰 إشعار دفع / طلب شحن رصيد من عميل!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: {user.id}\n\n'
      f'📝 التفاصيل أو النص المرسل:\n`{text_content}`\n\n'
      f'👉 لإضافة رصيد لمحفظة هذا العميل، رد على هذه الرسالة بالأمر:\n'
      f'`+رصيد` (مثال: `+5` لإضافة 5 دولار).'
  )

  try:
    bot.send_message(
        ADMIN_ID,
        notification_text,
        reply_markup=get_persistent_keyboard(),
    )
    bot.reply_to(
        message,
        '✅ **تم استلام طلبك بنجاح!**\nجاري التحقق من قبل الإدارة وتحديث رصيد'
        ' محفظتك في أقرب وقت ❤️',
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
  except Exception as e:
    print(f'Error forwarding text: {e}')


# ==========================================
# 👑 نظام تحكم الإدارة بالرصيد عبر الرد (Reply)
# ==========================================
@bot.message_handler(
    func=lambda message: message.from_user.id == ADMIN_ID
    and message.reply_to_message
)
def admin_reply_action(message):
  try:
    replied_msg = message.reply_to_message
    replied_text = replied_msg.text or replied_msg.caption

    if not replied_text:
      return

    match = re.search(r'🔢 الآيدي:\s*(\d+)', replied_text)
    if match:
      client_id = int(match.group(1))
      admin_text = message.text

      # إذا بدأت رسالة الإدارة بعلامة (+) سيتم تعديل رصيد العميل تلقائياً
      if admin_text.startswith('+'):
        try:
          amount_to_add = float(admin_text.replace('+', '').strip())
          update_user_balance(client_id, amount_to_add)

          # إبلاغ العميل بإضافة الرصيد لمحفظته
          bot.send_message(
              client_id,
              f'🎉 **تم شحن محفظتك بنجاح!**\n\n💵 تم إضافة مبلغ: **${amount_to_add}'
              '** إلى رصيدك في بوت ZEUS ❤️',
              reply_markup=get_persistent_keyboard(),
              parse_mode='Markdown',
          )
          bot.reply_to(
              message,
              f'✅ تم إضافة ${amount_to_add} إلى محفظة العميل ({client_id})'
              ' بنجاح وإبلاغه!',
          )
        except ValueError:
          bot.reply_to(
              message,
              '❌ صيغة المبلغ غير صحيحة. استخدم الشكل الصحيح مثل: `+10`',
          )
      else:
        # إرسال رد عادي للعميل
        bot.send_message(
            client_id,
            f'🎉 **تحديث بخصوص طلبك من ZEUS:**\n\n{admin_text}',
            reply_markup=get_persistent_keyboard(),
            parse_mode='Markdown',
        )
        bot.reply_to(message, '✅ **تم إرسال الرد للعميل بنجاح!**')
    else:
      bot.reply_to(
          message,
          '⚠️ لم يتم العثور على آيدي العميل في الرسالة الأصلية التي ردرت'
          ' عليها.',
      )
  except Exception as e:
    print(f'Error in admin reply: {e}')
    bot.reply_to(message, f'❌ حدث خطأ أثناء تنفيذ الإجراء: {e}')


# معالجة طلبات الخدمات
@bot.callback_query_handler(
    func=lambda call: call.data.startswith('order_')
    or call.data.startswith('chat_')
)
def handle_order_selection(call):
  if call.data.startswith('order_Sham_'):
    service_name = 'شام كاش تحويل'
  else:
    service_name = (
        call.data.replace('order_', '').replace('chat_', '').replace('_', ' ')
    )

  prompt_text = (
      f'📦 الخدمة المختارة: {service_name}\n\n'
      f'✍️ **يرجى إرسال رقم (ID) أو رابط الحساب أو تفاصيل الطلب في رسالة واحدة:**'
  )

  msg = bot.send_message(
      call.message.chat.id, prompt_text, parse_mode='Markdown'
  )
  bot.register_next_step_handler(msg, process_user_order, service_name)


def process_user_order(message, service_name):
  user = message.from_user
  user_input = message.text

  if user_input in [
      '🏠 القائمة الرئيسية / Main Menu',
      '💰 محفظتي / My Wallet',
      '📞 الدعم الفني / Support',
  ]:
    return

  notification_text = (
      f'🚨 طلب جديد من عميل!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: {user.id}\n'
      f'📱 التفاصيل: {user_input}\n'
      f'📦 الخدمة: {service_name}'
  )

  try:
    bot.send_message(ADMIN_ID, notification_text)
  except Exception as e:
    print(f'Error sending order to admin: {e}')

  caption_text = (
      f'✅ **تم استلام طلبك وتسجيله بنجاح!**\n\n'
      f'📦 الخدمة: {service_name}\n'
      f'📱 التفاصيل: `{user_input}`\n\n'
      f'⏳ جاري مراجعة الطلب وتنفيذه من قبل الإدارة في أقرب وقت ❤️'
  )

  bot.send_message(
      message.chat.id,
      caption_text,
      reply_markup=get_persistent_keyboard(),
      parse_mode='Markdown',
  )


if __name__ == '__main__':
  print('ZEUS Bot with Wallets is running...')
  bot.infinity_polling()
