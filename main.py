import os
import threading
import re
import sqlite3
import uuid
import html
from datetime import datetime
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

# التحقق من وجود توكن البوت قبل البدء
TOKEN = os.environ.get('TOKEN')
if not TOKEN:
  raise RuntimeError('Missing TOKEN environment variable')

# إعداد خادم ويب مصغر لاستضافة Render ولضمان عمل البوت 24/7
app = Flask('')


@app.route('/')
def home():
  return 'ZEUS-ECHANCE-BOT is running 24/7!'


def run_web_server():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port, use_reloader=False)


threading.Thread(target=run_web_server, daemon=True).start()

bot = telebot.TeleBot(TOKEN)

# الآيدي الرقمي الصحيح الخاص بك لتلقي الطلبات
ADMIN_ID = 1632433018

# ==========================================
# 🗄️ إعداد قاعدة بيانات SQLite وحفظ الأرصدة والمعاملات والطلبات
# ==========================================
DB_PATH = os.environ.get('DB_PATH', 'zeus_bot.db')


def get_db_connection():
  conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=15)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  with get_db_connection() as conn:
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')
    conn.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                user_id INTEGER PRIMARY KEY,
                balance_usd REAL NOT NULL DEFAULT 0.0,
                balance_syp INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
        """)
    conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tx_type TEXT NOT NULL,
                amount_str TEXT NOT NULL,
                details TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
    conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                service_name TEXT NOT NULL,
                user_input TEXT NOT NULL,
                price_usd REAL NOT NULL,
                price_syp INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        """)
    conn.commit()


def ensure_wallet(user_id):
  now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
  with get_db_connection() as conn:
    conn.execute(
        """
            INSERT OR IGNORE INTO wallets (user_id, balance_usd, balance_syp, updated_at)
            VALUES (?, 0.0, 0, ?)
        """,
        (user_id, now_str),
    )
    conn.commit()


def get_wallet(user_id):
  ensure_wallet(user_id)
  with get_db_connection() as conn:
    row = conn.execute(
        'SELECT balance_usd, balance_syp FROM wallets WHERE user_id = ?',
        (user_id,),
    ).fetchone()
    return {
        'USD': float(row['balance_usd']) if row else 0.0,
        'SYP': int(row['balance_syp']) if row else 0,
    }


def add_balance(user_id, amount, currency):
  ensure_wallet(user_id)
  now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
  currency_upper = currency.upper()
  with get_db_connection() as conn:
    if currency_upper == 'USD':
      conn.execute(
          """
                UPDATE wallets
                SET balance_usd = ROUND(balance_usd + ?, 4), updated_at = ?
                WHERE user_id = ?
            """,
          (float(amount), now_str, user_id),
      )
      amt_str = f'+${float(amount):.2f}'
    elif currency_upper in ['SYP', 'ل.س']:
      syp_val = int(round(float(amount)))
      conn.execute(
          """
                UPDATE wallets
                SET balance_syp = balance_syp + ?, updated_at = ?
                WHERE user_id = ?
            """,
          (syp_val, now_str, user_id),
      )
      amt_str = f'+{syp_val:,} ل.س'
    else:
      return False, ''
    conn.commit()

  add_transaction(
      user_id=user_id,
      tx_type='شحن رصيد',
      amount_str=amt_str,
      details='تمت الإضافة بواسطة الإدارة',
  )
  return True, amt_str


def add_transaction(user_id, tx_type, amount_str, details):
  now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
  with get_db_connection() as conn:
    conn.execute(
        """
            INSERT INTO transactions (user_id, tx_type, amount_str, details, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, tx_type, amount_str, details, now_str),
    )
    conn.commit()


def get_user_transactions(user_id, limit=10):
  with get_db_connection() as conn:
    rows = conn.execute(
        """
            SELECT tx_type, amount_str, details, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def create_pending_order(user_id, service_name, user_input, price_usd, price_syp):
  order_id = uuid.uuid4().hex[:10]
  now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
  with get_db_connection() as conn:
    conn.execute(
        """
            INSERT INTO pending_orders (
                order_id, user_id, service_name, user_input, price_usd, price_syp, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
        """,
        (
            order_id,
            user_id,
            service_name,
            user_input,
            float(price_usd),
            int(price_syp),
            now_str,
        ),
    )
    conn.commit()
  return order_id


def pay_order_from_wallet(order_id, user_id, currency):
  ensure_wallet(user_id)
  now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
  currency_upper = currency.upper()

  conn = get_db_connection()
  try:
    conn.execute('BEGIN IMMEDIATE')
    order_row = conn.execute(
        """
            SELECT order_id, user_id, service_name, user_input, price_usd, price_syp, status
            FROM pending_orders
            WHERE order_id = ? AND user_id = ?
        """,
        (order_id, user_id),
    ).fetchone()

    if not order_row:
      conn.rollback()
      return False, 'الطلب غير موجود.', None

    if order_row['status'] != 'pending':
      conn.rollback()
      return False, 'تمت معالجة هذا الطلب مسبقاً.', None

    wallet_row = conn.execute(
        'SELECT balance_usd, balance_syp FROM wallets WHERE user_id = ?',
        (user_id,),
    ).fetchone()

    bal_usd = float(wallet_row['balance_usd']) if wallet_row else 0.0
    bal_syp = int(wallet_row['balance_syp']) if wallet_row else 0

    price_usd = float(order_row['price_usd'])
    price_syp = int(order_row['price_syp'])

    if currency_upper == 'USD':
      if bal_usd + 1e-9 < price_usd:
        conn.rollback()
        return False, 'رصيدك بالدولار غير كافٍ لإتمام هذه العملية.', None
      conn.execute(
          """
                UPDATE wallets
                SET balance_usd = ROUND(balance_usd - ?, 4), updated_at = ?
                WHERE user_id = ?
            """,
          (price_usd, now_str, user_id),
      )
      amt_spent_str = f'-${price_usd:.2f}'
    elif currency_upper == 'SYP':
      if bal_syp < price_syp:
        conn.rollback()
        return False, 'رصيدك بالليرة السورية غير كافٍ لإتمام هذه العملية.', None
      conn.execute(
          """
                UPDATE wallets
                SET balance_syp = balance_syp - ?, updated_at = ?
                WHERE user_id = ?
            """,
          (price_syp, now_str, user_id),
      )
      amt_spent_str = f'-{price_syp:,} ل.س'
    else:
      conn.rollback()
      return False, 'عملة الدفع غير مدعومة.', None

    conn.execute(
        "UPDATE pending_orders SET status = 'paid_wallet' WHERE order_id = ?",
        (order_id,),
    )
    conn.commit()

    order_data = dict(order_row)
    order_data['amt_spent_str'] = amt_spent_str
    order_data['currency'] = currency_upper
    return True, '', order_data
  except Exception as e:
    conn.rollback()
    return False, f'حدث خطأ أثناء الخصم: {e}', None
  finally:
    conn.close()


init_db()

# ==========================================
# 💳 إعدادات المحافظ وطرق الدفع
# ==========================================
SHAM_CASH_WALLET = '02d28a07292f2a11f12e0d8e2bd08dd1'
TRX_WALLET = 'TKva4xbJjCtwGy2vDFAoddsSd91aKZ5zqK'
PLASMA_WALLET = '0xb027c9b07f2b4ffffcf7a56fc80af180f8692c67'

# ==========================================
# 💱 إعدادات سعر الصرف (سعر السوق السوداء - قابل للتعديل)
# ==========================================
USD_TO_SYP_RATE = 155


def price_text(usd_amount):
  """دالة لتوليد السعر بالدولار وما يعادلها بالليرة السورية تلقائياً مع فاصل الآلاف"""
  syp_amount = int(round(usd_amount * USD_TO_SYP_RATE))
  return f'${usd_amount} ({syp_amount:,} ل.س)'


def extract_service_price(service_name):
  """يستخرج السعر بالدولار من اسم الخدمة ويحسب ما يعادله بالليرة السورية"""
  match = re.search(r'\$([0-9]+(?:\.[0-9]+)?)', service_name)
  if not match:
    return None, None
  usd_val = float(match.group(1))
  syp_val = int(round(usd_val * USD_TO_SYP_RATE))
  return usd_val, syp_val


def esc(text):
  """تهريب النصوص لاستخدامها بأمان مع HTML"""
  return html.escape(str(text or ''))


def safe_edit_message(chat_id, message_id, text, reply_markup=None):
  try:
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML',
    )
  except Exception as e:
    if 'message is not modified' not in str(e).lower():
      try:
        bot.send_message(
            chat_id,
            text,
            reply_markup=reply_markup,
            parse_mode='HTML',
        )
      except Exception as send_err:
        print(f'Error in safe_edit_message fallback: {send_err}')


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


# دالة إرسال تفاصيل الطلب الأولي إلى حسابك الشخصي مباشرة وتسجيله في سجل المعاملات
def send_order_to_admin(
    message, service_name, user_input, record_tx=True, order_id=None
):
  user = message.from_user

  if record_tx:
    price_match = re.search(r'\$([0-9]+(?:\.[0-9]+)?)', service_name)
    amount_label = (
        f'${price_match.group(1)}' if price_match else 'بانتظار التسعير'
    )
    add_transaction(
        user_id=user.id,
        tx_type='طلب خدمة',
        amount_str=amount_label,
        details=f'{service_name} ({user_input})',
    )

  order_line = (
      f'🧾 رقم الطلب: <code>{esc(order_id)}</code>\n' if order_id else ''
  )
  notification_text = (
      f'🚨 <b>طلب جديد بانتظار التحويل والتنفيذ!</b>\n\n'
      f'{order_line}'
      f'👤 اسم العميل: {esc(user.first_name)}\n'
      f'🆔 المعرف: @{esc(user.username) if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: <code>{user.id}</code>\n'
      f'📱 الحساب أو المعلومات المدخلة: <code>{esc(user_input)}</code>\n'
      f'📦 الخدمة المطلوبة: {esc(service_name)}\n\n'
      f'👉 بانتظار إتمام العميل للتحويل وإرسال إشعار أو رقم عملية التحويل.'
  )
  try:
    bot.send_message(ADMIN_ID, notification_text, parse_mode='HTML')
  except Exception as e:
    print(f'Error sending notification: {e}')


# 📸 استقبال صور إيصالات الدفع من العملاء وتحويلها للإدارة فوراً
@bot.message_handler(content_types=['photo'])
def handle_client_photo(message):
  if message.from_user.id == ADMIN_ID:
    return

  user = message.from_user
  photo_file_id = message.photo[-1].file_id

  caption = (
      f'📸 <b>إيصال دفع جديد (صورة) مرسل من عميل!</b>\n\n'
      f'👤 اسم العميل: {esc(user.first_name)}\n'
      f'🆔 المعرف: @{esc(user.username) if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: <code>{user.id}</code>\n\n'
      f'👉 يرجى التحقق من وصول المبلغ على المحافظ (شام كاش / بينانس / بلازما) لتنفيذ الطلب.'
  )

  try:
    bot.send_photo(
        ADMIN_ID,
        photo_file_id,
        caption=caption,
        reply_markup=get_persistent_keyboard(),
        parse_mode='HTML',
    )
    bot.reply_to(
        message,
        '✅ <b>تم استلام إيصال الدفع بنجاح!</b>\nجاري التحقق من قبل الإدارة وتنفيذ طلبك في أقرب وقت ❤️',
        reply_markup=get_persistent_keyboard(),
        parse_mode='HTML',
    )
  except Exception as e:
    print(f'Error forwarding payment receipt photo: {e}')


# 💳 استقبال أرقام عمليات التحويل أو نصوص إشعارات الدفع من العملاء وتحويلها فوراً
@bot.
