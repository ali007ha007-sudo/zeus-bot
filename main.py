import os
import re
import sqlite3
import threading
import time
from datetime import datetime
from flask import Flask
import requests
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
import urllib3

# تعطيل تحذيرات الأمان الخاصة بـ SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 🌐 خادم الويب لـ Render (24/7)
# ==========================================
app = Flask(__name__)


@app.route('/')
def home():
  return 'ZEUS-ECHANCE-BOT is running 24/7 with SQLite & New SYP Rate Sync!'


def run_web_server():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port, use_reloader=False)


threading.Thread(target=run_web_server, daemon=True).start()

# ==========================================
# ⚙️ إعدادات البوت والإدارة والأسعار
# ==========================================
TOKEN = os.environ.get('TOKEN')
if not TOKEN:
  raise ValueError('لم يتم العثور على متغير البيئة TOKEN!')

bot = telebot.TeleBot(TOKEN, parse_mode='Markdown')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '1632433018'))
DB_PATH = os.environ.get('DB_PATH', 'zeus_database.db')

# إعدادات المحافظ وطرق الدفع
SHAM_CASH_WALLET = '02d28a07292f2a11f12e0d8e2bd08dd1'
TRX_WALLET = 'TKva4xbJjCtwGy2vDFAoddsSd91aKZ5zqK'
PLASMA_WALLET = '0xb027c9b07f2b4ffffcf7a56fc80af180f8692c67'

# إعدادات SP Today لتحديث سعر الدولار مقابل العملة السورية الجديدة فقط كل 15 دقيقة
SP_TODAY_API_KEY = os.environ.get(
    'SP_TODAY_API_KEY', 'F2b72ec8905cf21f2ad3a5d9940db826'
)
SP_TODAY_ENDPOINT = os.environ.get(
    'SP_TODAY_ENDPOINT',
    'https://api-v2.sp-today.com/api/rates',
)
RATE_SYNC_INTERVAL_SECONDS = 15 * 60  # 15 دقيقة = 900 ثانية

# القيمة الافتراضية بالعملة السورية الجديدة
USD_TO_SYP_RATE = 140.0
BOT_USERNAME_CACHE = None


def get_bot_username():
  global BOT_USERNAME_CACHE
  if not BOT_USERNAME_CACHE:
    try:
      BOT_USERNAME_CACHE = bot.get_me().username
    except Exception:
      BOT_USERNAME_CACHE = 'ZEUS_FORCEbot'
  return BOT_USERNAME_CACHE


def format_syp(amount):
  val = round(float(amount), 2)
  if val.is_integer():
    return f'{int(val):,}'
  return f'{val:,.2f}'


def price_text(usd_amount):
  """توليد السعر بالدولار وما يعادله بالليرة السورية الجديدة"""
  syp_amount = round(usd_amount * USD_TO_SYP_RATE, 2)
  return f'${usd_amount:g} ({format_syp(syp_amount)} ل.س جديدة)'


def _extract_new_syp_rate(payload):
  """استخراج سعر العملة السورية الجديدة فقط (new) وتجاهل القديمة (old)"""
  if not isinstance(payload, dict):
    return None

  for key in (
      'new',
      'new_syp',
      'syp_new',
      'USD_SYP_NEW',
      'usd_syp_new',
      'sell_new',
      'rate_new',
  ):
    val = payload.get(key)
    if isinstance(val, (int, float)) and val > 0:
      return float(val)
    if isinstance(val, dict):
      for sub_k in ('sell', 'rate', 'price', 'value', 'buy'):
        sub_val = val.get(sub_k)
        if isinstance(sub_val, (int, float)) and sub_val > 0:
          return float(sub_val)

  for container_key in (
      'data',
      'rates',
      'currencies',
      'USD',
      'usd',
      'SYP',
      'syp',
  ):
    nested = payload.get(container_key)
    if isinstance(nested, dict):
      found = _extract_new_syp_rate(nested)
      if found:
        return found
    elif isinstance(nested, list):
      for item in nested:
        if isinstance(item, dict):
          code = str(
              item.get('code')
              or item.get('currency')
              or item.get('symbol')
              or ''
          ).upper()
          if code in ('USD', 'SYP', 'SYP_NEW', 'USD/SYP'):
            found = _extract_new_syp_rate(item)
            if found:
              return found

  return None


def sync_sp_today_new_syp():
  global USD_TO_SYP_RATE
  headers = {
      'Authorization': f'Bearer {SP_TODAY_API_KEY}',
      'X-API-Key': SP_TODAY_API_KEY,
      'Accept': 'application/json',
  }
  params = {'api_key': SP_TODAY_API_KEY}

  try:
    response = requests.get(
        SP_TODAY_ENDPOINT,
        headers=headers,
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    extracted = _extract_new_syp_rate(data)

    # حارس أمان: قبول قيم العملة الجديدة فقط وتجاهل أرقام العملة القديمة
    if extracted and 0 < extracted < 1000:
      USD_TO_SYP_RATE = round(extracted, 2)
      print(
          f'✅ [SP Today] تم تحديث العملة الجديدة USD -> SYP: {USD_TO_SYP_RATE}'
      )
      return True

    print(
        '⚠️ [SP Today] لم يتم العثور على حقل العملة الجديدة (new) في الرد؛ '
        f'يبقى السعر الحالي: {USD_TO_SYP_RATE}'
    )
  except Exception as e:
    print(
        f'⚠️ [SP Today] تعذر التحديث الدوري (الاحتفاظ بـ {USD_TO_SYP_RATE}): {e}'
    )
  return False


def start_sp_today_rate_sync():
  def loop():
    while True:
      sync_sp_today_new_syp()
      time.sleep(RATE_SYNC_INTERVAL_SECONDS)

  threading.Thread(target=loop, daemon=True).start()


# ==========================================
# 🗄️ إعداد قاعدة البيانات (SQLite)
# ==========================================
def get_db_connection():
  conn = sqlite3.connect(DB_PATH, check_same_thread=False)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute('''
      CREATE TABLE IF NOT EXISTS users (
          user_id INTEGER PRIMARY KEY,
          first_name TEXT,
          username TEXT,
          balance_usd REAL DEFAULT 0.0,
          balance_syp REAL DEFAULT 0.0,
          referred_by INTEGER,
          joined_date TEXT
      )
  ''')

  cursor.execute('''
      CREATE TABLE IF NOT EXISTS orders (
          order_id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER,
          service_name TEXT,
          user_input TEXT,
          status TEXT DEFAULT 'قيد المراجعة ⏳',
          created_at TEXT
      )
  ''')

  cursor.execute('''
      CREATE TABLE IF NOT EXISTS wallet_history (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER,
          amount_text TEXT,
          description TEXT,
          date TEXT
      )
  ''')

  cursor.execute('''
      CREATE TABLE IF NOT EXISTS coupons (
          code TEXT PRIMARY KEY,
          amount_usd REAL,
          is_used INTEGER DEFAULT 0
      )
  ''')

  conn.commit()
  conn.close()


init_db()


def log_wallet_transaction(user_id, amount_text, description):
  conn = get_db_connection()
  cursor = conn.cursor()
  now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  cursor.execute(
      '''
      INSERT INTO wallet_history (user_id, amount_text, description, date)
      VALUES (?, ?, ?, ?)
      ''',
      (user_id, amount_text, description, now),
  )
  conn.commit()
  conn.close()


def get_or_create_user(user_id, first_name, username, referred_by=None):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
  user = cursor.fetchone()

  if not user:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        '''
        INSERT INTO users (user_id, first_name, username, balance_usd, balance_syp, referred_by, joined_date)
        VALUES (?, ?, ?, 0.0, 0.0, ?, ?)
        ''',
        (user_id, first_name, username, referred_by, now),
    )
    conn.commit()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
  else:
    cursor.execute(
        'UPDATE users SET first_name = ?, username = ? WHERE user_id = ?',
        (first_name, username, user_id),
    )
    conn.commit()

  conn.close()
  return user


def update_user_balance(user_id, usd_add=0.0, syp_add=0.0, description='تعديل رصيد'):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT balance_usd, balance_syp FROM users WHERE user_id = ?',
      (user_id,),
  )
  res = cursor.fetchone()
  if res:
    new_usd = round(float(res['balance_usd']) + float(usd_add), 4)
    new_syp = round(float(res['balance_syp']) + float(syp_add), 2)
    cursor.execute(
        'UPDATE users SET balance_usd = ?, balance_syp = ? WHERE user_id = ?',
        (new_usd, new_syp, user_id),
    )
    conn.commit()

    if usd_add != 0.0:
      sign = '+' if usd_add > 0 else ''
      log_wallet_transaction(user_id, f'{sign}${float(usd_add):g}', description)
    if syp_add != 0.0:
      sign = '+' if syp_add > 0 else ''
      log_wallet_transaction(
          user_id, f'{sign}{format_syp(syp_add)} ل.س جديدة', description
      )
  conn.close()


# ==========================================
# 🧩 القوائم والأزرار المساعدة
# ==========================================
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


def get_main_menu_markup():
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '💰 محفظتي الشخصية / My Wallet', callback_data='menu_wallet_inline'
      ),
      InlineKeyboardButton('1️⃣ الألعاب / GAMES 🎮', callback_data='menu_games'),
      InlineKeyboardButton('2️⃣ الذكاء الاصطناعي / AI 💭', callback_data='menu_ai'),
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
  return markup


def send_order_to_admin(message, service_name, user_input):
  user = message.from_user
  conn = get_db_connection()
  cursor = conn.cursor()
  now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  cursor.execute(
      '''
      INSERT INTO orders (user_id, service_name, user_input, status, created_at)
      VALUES (?, ?, ?, ?, ?)
      ''',
      (user.id, service_name, user_input, 'قيد المراجعة ⏳', now),
  )
  conn.commit()
  order_id = cursor.lastrowid
  conn.close()

  uname = f'@{user.username}' if user.username else 'لا يوجد'
  notification_text = (
      f'🚨 طلب جديد رقم #{order_id} بانتظار التحويل والتنفيذ!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: {uname}\n'
      f'🔢 الآيدي: {user.id}\n'
      f'📱 الحساب أو المعلومات المدخلة: {user_input}\n'
      f'📦 الخدمة المطلوبة: {service_name}\n\n'
      f'👉 بانتظار إتمام العميل للتحويل وإرسال إشعار أو رقم عملية التحويل.'
  )
  try:
    bot.send_message(ADMIN_ID, notification_text)
  except Exception as e:
    print(f'Error sending notification: {e}')


# ==========================================
# 🚀 الأوامر الأساسية والمحفظة
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
  user = message.from_user
  text_args = message.text.split()
  referred_by = None

  if len(text_args) > 1 and text_args[1].startswith('ref_'):
    try:
      ref_id = int(text_args[1].replace('ref_', '', 1))
      if ref_id != user.id:
        referred_by = ref_id
    except ValueError:
      pass

  get_or_create_user(user.id, user.first_name, user.username, referred_by)

  welcome_text = (
      'اهلا بكم في ⚡️ **ZEUS SERVICES -BOT** ⚡️ للخدمات الرقمية الشاملة\n\n'
      'نحن فريق من الأشخاص يمتلك الخبرة لنقدم لك كافه خدمات الشحن والدفع الإلكتروني'
      ' بكافة انواعة بشكل آمن وسريع وبدقة عالية من الاحترافية ❤️\n\n'
      'يرجى إختيار القسم المطلوب:'
  )

  bot.send_message(
      message.chat.id,
      'تم تفعيل لوحة المفاتيح الخاصة بك 👇',
      reply_markup=get_persistent_keyboard(),
  )
  bot.reply_to(
      message, welcome_text, reply_markup=get_main_menu_markup()
  )


def show_user_wallet(chat_id, user, message_id=None):
  db_user = get_or_create_user(user.id, user.first_name, user.username)
  balance_usd = float(db_user['balance_usd'])
  balance_syp = float(db_user['balance_syp'])
  bot_uname = get_bot_username()

  wallet_text = (
      f'💰 **محفظتك الشخصية - ZEUS**\n\n'
      f'👤 صاحب المحفظة: {user.first_name}\n'
      f'🆔 الآيدي الخاص بك: `{user.id}`\n\n'
      f'💵 **الرصيد الحالي:**\n'
      f'• الرصيد بالدولار: **${balance_usd:.2f}**\n'
      f'• الرصيد بالليرة السورية الجديدة: **{format_syp(balance_syp)} ل.س جديدة**\n\n'
      f'🔗 **رابط الإحالة الخاص بك لدعوة أصدقائك:**\n'
      f'`https://t.me/{bot_uname}?start=ref_{user.id}`\n\n'
      f'💡 **ملاحظة:** لشحن محفظتك، حوّل إلى أحد محافظنا وأرسل الإشعار للإدارة أو فعّل كوبوناً عبر `/coupon CODE`.'
  )

  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton('➕ شحن المحفظة', callback_data='wallet_deposit'),
      InlineKeyboardButton(
          '📜 سجل المعاملات والطلبات', callback_data='wallet_history'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )

  if message_id:
    try:
      bot.edit_message_text(
          chat_id=chat_id,
          message_id=message_id,
          text=wallet_text,
          reply_markup=markup,
      )
      return
    except Exception:
      pass

  bot.send_message(chat_id, wallet_text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'menu_wallet_inline')
def menu_wallet_inline_handler(call):
  show_user_wallet(call.message.chat.id, call.from_user, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'back_wallet')
def back_to_wallet_callback(call):
  show_user_wallet(call.message.chat.id, call.from_user, call.message.message_id)


@bot.callback_query_handler(
    func=lambda call: call.data in ['wallet_deposit', 'wallet_history']
)
def handle_wallet_callbacks(call):
  if call.data == 'wallet_deposit':
    deposit_text = (
        '💳 **شحن المحفظة الشخصية:**\n\n'
        'لشحن رصيدك في المحفظة، يرجى التحويل إلى إحدى الطرق التالية:\n\n'
        f'1️⃣ **شام كاش:**\n`{SHAM_CASH_WALLET
