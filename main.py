import os
import sqlite3
import requests
import urllib3
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bs4 import BeautifulSoup


# تعطيل تحذيرات الأمان الخاصة بشهادات SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إعداد خادم الويب (Flask) لضمان عدم حدوث مشكلة Port timeout في منصة Render
app = Flask('')

@app.route('/')
def home():
    return "ZEUS Bot is running 24/7!"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# تشغيل السيرفر في خلفية النظام
threading.Thread(target=run_web_server).start()

# جلب توكن البوت من أمان منصة Render
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 1632433018

# إعدادات بوابات الدفع (مثال: شام كاش)
ALSHAM_CASH_API_URL = "https://api.alshamcash.com/v1/pay"
MERCHANT_ID = "293918375fc6b32d10496d55ab346a24"
API_SECRET_KEY = "YOUR_REAL_API_SECRET_KEY_HERE"

# قاعدة البيانات (SQLite)
def init_db():
    conn = sqlite3.connect('zeus_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            wallet_number TEXT,
            balance REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service_name TEXT,
            package TEXT,
            price REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# دالة جلب سعر الصرف من موقع الليرة اليوم (sp.today)
def get_exchange_rate():
    try:
        url = "https://sp.today/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # يمكنك تعديل طريقة الجلب بناءً على هيكل الموقع، وهنا يتم جلب التحديث العام كمثال
            return "💱 **أسعار الصرف الحالية مرتبطة مباشرة بموقع الليرة اليوم (sp.today)**."
    except Exception as e:
        return "⚠️ تعذر تحديث سعر الصرف حالياً من الموقع الرسمي."

# دالة إرسال طلب الدفع عبر شام كاش
def send_alsham_cash_request(wallet_number, amount, service_desc):
    headers = {
        'Authorization': f'Bearer {API_SECRET_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'merchant_id': MERCHANT_ID,
        'wallet': wallet_number,
        'amount': amount,
        'description': service_desc
    }
    try:
        response = requests.post(ALSHAM_CASH_API_URL, json=payload, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return True, "تم الدفع بنجاح من البوابة الرسمية."
        return False, "فشلت عملية الدفع الإلكتروني."
    except Exception as ex:
        return False, f"حدث خطأ في الاتصال: {str(ex)}"


# --- واجهة الأوامر والقوائم ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💳 تعبئة رصيد", callback_data="menu_topup"),
        InlineKeyboardButton("🌐 مزودات الإنترنت (سوريا)", callback_data="menu_internet"),
        InlineKeyboardButton("💱 أسعار الصرف", callback_data="menu_rates")
    )
    welcome_text = (
        "مرحباً بك في بوت الخدمات الذكي 🇸🇾\n"
        "يرجى اختيار القسم المطلوب من القائمة أدناه:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


# معالجة القوائم والضغط على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    
    # 1. قائمة أسعار الصرف
    if call.data == "menu_rates":
        rate_info = get_exchange_rate()
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, rate_info)

    # 2. قائمة تعبئة الرصيد (الخيارات المطلوبة)
    elif call.data == "menu_topup":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("SHAM_CASH", callback_data="pay_sham"),
            InlineKeyboardButton("SYRIATEL_CASH", callback_data="pay_syriatel"),
            InlineKeyboardButton("MTN_CASH", callback_data="pay_mtn"),
            InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")
        )
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "💳 **اختر طريقة الدفع لتعبئة الرصيد:**", reply_markup=markup)

    # اختيار إحدى طرق الدفع لتعبئة الرصيد
    elif call.data in ["pay_sham", "pay_syriatel", "pay_mtn"]:
        method_name = call.data.replace("pay_", "").upper()
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, f"لقد اخترت الدفع عبر `{method_name}`.\nالرجاء إرسال **قيمة الرصيد المطلوب** بالأرقام:")
        bot.register_next_step_handler(msg, process_topup_amount, method_name)

    # 3. قائمة مزودي الإنترنت في سوريا
    elif call.data == "menu_internet":
        providers_text = (
            "🌐 **قائمة مزودي خدمة الإنترنت في سوريا 🇸🇾:**\n\n"
            "1️⃣ زاد (Zad)\n"
            "2️⃣ سيريتل دي إس إل (Syriatel DSL)\n"
            "3️⃣ آيو (Ayo)\n"
            "4️⃣ ترامسول (Tarassul)\n"
            "5️⃣ سيبار (Siber)\n\n"
            "⚠️ **تنبيه هام جداً:** عند إدخال رقم الهاتف، يرجى كتابته **مع مفتاح المحافظة حصراً** (مثال: 011xxxxxxx أو 021xxxxxxx) ليتم تنفيذ طلبك بنجاح دون أخطاء."
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="main_menu"))
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, providers_text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)
        send_welcome(call.message)


# استكمال عملية تعبئة الرصيد بعد إدخال القيمة
def process_topup_amount(message, method_name):
    amount = message.text
    chat_id = message.chat.id
    
    if not amount.isdigit():
        msg = bot.send_message(chat_id, "❌ يرجى إدخال قيمة صحيحة بالأرقام فقط:")
        bot.register_next_step_handler(msg, process_topup_amount, method_name)
        return

    # سؤال العميل عن رقم المحفظة أو الحساب لإتمام العملية (بدون رقم هوية)
    msg = bot.send_message(chat_id, f"تم تحديد القيمة: {amount}\nالرجاء إدخال رقم الحساب أو الهاتف المراد التعبئة إليه عبر {method_name}:")
    bot.register_next_step_handler(msg, execute_topup_transaction, method_name, amount)


def execute_topup_transaction(message, method_name, amount):
    wallet_or_phone = message.text
    chat_id = message.chat.id
    
    # تنفيذ الطلب بنجاح وتأكيده للعميل
    bot.send_message(chat_id, f"✅ تم استلام طلبك بنجاح!\n\n🔹 الطريقة: {method_name}\n🔹 القيمة: {amount}\n🔹 الحساب: {wallet_or_phone}\n\nجاري معالجة الطلب...")


# تشغيل البوت بشكل مستمر
if __name__ == '__main__':
    print("Bot is starting...")
    bot.infinity_polling(skip_pending=True)
