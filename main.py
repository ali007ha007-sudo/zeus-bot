import os
import telebot
import sqlite3
import requests
import urllib3
import threading
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# تعطيل تحذيرات الأمان الخاصة بشهادة SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إعداد خادم ويب مصغر لتلبية شروط الاستضافة المجانية على Render (منع خطأ Port timeout)
app = Flask('')

@app.route('/')
def home():
    return "ZEUS Bot is running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# تشغيل السيرفر في خلفية النظام
threading.Thread(target=run_web_server).start()

# جلب توكن البوت بأمان من إعدادات منصة Render
TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

# ⚠️ ضع هنا رقم الآيدي الخاص بك على تيليغرام
ADMIN_ID = t.me/Ali00700Ali
MERCHANT_ID = os.environ.get("3099259112049353")
API_SECRET_KEY = os.environ.get("0077")


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

def send_alsham_cash_request(wallet_number, amount, service_desc):
    headers = {
        "Authorization": f"Bearer {API_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "merchant_id": MERCHANT_ID,
        "wallet": wallet_number,
        "amount": amount,
        "description": service_desc
    }
    
    try:
        response = requests.post(ALSHAM_CASH_API_URL, json=payload, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return True, "تم الدفع بنجاح عبر البوابة الرسمية."
            else:
                return False, data.get("message", "فشلت العملية من المصدر.")
        else:
            return True, "تم محاكاة الاتصال بنجاح (بانتظار تفعيل المفتاح الحقيقي)."
    except requests.exceptions.RequestException as e:
        return False, f"خطأ في الاتصال بالشبكة: {str(e)}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"أهلاً بك يا {user_name} في منصة ZEUS الرقمية المتكاملة!\n\n"
        "نقدم لك أرقى الخدمات الرقمية، الألعاب، وبطاقات الشات الصوتية.\n"
        "اختر القسم المطلوب من الأزرار أدناه:"
    )
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💳 محفظة الشام كاش", callback_data="wallet_menu"),
        InlineKeyboardButton("🎮 شحن الألعاب والجواكر", callback_data="games_menu"),
        InlineKeyboardButton("🎙️ الدردشة والشات الصوتي", callback_data="voice_chat_menu"),
        InlineKeyboardButton("📱 التطبيقات والبطاقات", callback_data="apps_menu"),
        InlineKeyboardButton("📶 تعبئة رصيد الموبايل", callback_data="recharge_menu"),
        InlineKeyboardButton("💡 دفع الفواتير", callback_data="bills_menu"),
        InlineKeyboardButton("📞 الدعم الفني", callback_data="support")
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_panel_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "عذراً، هذا الأمر مخصص لمدير البوت فقط.")
        return
        
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📊 إحصائيات البوت الشاملة", callback_data="admin_stats"))
    markup.add(InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home"))
    bot.send_message(message.chat.id, "أهلاً بك في لوحة تحكم مدير منصة ZEUS\nاختر الإجراء المطلوب:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if call.data == "admin_stats":
        if user_id != ADMIN_ID:
            return
            
        conn = sqlite3.connect('zeus_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*), SUM(balance), COUNT(wallet_number) FROM users')
        row = cursor.fetchone()
        cursor.execute('SELECT COUNT(*) FROM transactions')
        tx_row = cursor.fetchone()
        conn.close()
        
        total_users = row[0] if row[0] else 0
        total_balance = row[1] if row[1] else 0.0
        linked_wallets = row[2] if row[2] else 0
        total_tx = tx_row[0] if tx_row[0] else 0
        
        stats_text = (
            "إحصائيات منصة ZEUS المباشرة:\n\n"
            f"- إجمالي المستخدمين المسجلين: {total_users}\n"
            f"- المحافظ المربوطة بنجاح: {linked_wallets}\n"
            f"- إجمالي عمليات الشراء المنفذة: {total_tx}\n"
            f"- إجمالي السيولة التجريبية بالمحافظ: {total_balance:,.0f} ل.س"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔄 تحديث الإحصائيات", callback_data="admin_stats"))
        markup.add(InlineKeyboardButton("🔙 لوحة التحكم", callback_data="back_home"))
        bot.edit_message_text(stats_text, chat_id, call.message.message_id, reply_markup=markup)

    elif call.data == "wallet_menu":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 ربط محفظة الشام كاش", callback_data="link_wallet"))
        markup.add(InlineKeyboardButton("💰 الاستعلام عن الرصيد", callback_data="check_balance"))
        markup.add(InlineKeyboardButton("💵 إيداع رصيد تجريبي (+10,000)", callback_data="add_test_balance"))
        markup.add(InlineKeyboardButton("📜 سجل مشترياتي", callback_data="my_transactions"))
        markup.add(InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home"))
        bot.send_message(chat_id, "إدارة محفظة الشام كاش (جاهز للربط الحقيقي)\nاختر العملية المطلوبة:", reply_markup=markup)

    elif call.data == "link_wallet":
        bot.send_message(chat_id, "لربط محفظتك، أرسل الأمر التالي في المحادثة:\n/link [رقم الهاتف]\nمثال:\n/link 0930000000")

    elif call.data == "check_balance":
        conn = sqlite3.connect('zeus_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT wallet_number, balance FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            wallet = row[0]
            balance = row[1]
            bot.send_message(chat_id, f"حسابك مربوط بنجاح\n- رقم المحفظة: {wallet}\n- الرصيد الحالي: {balance:,.0f} ل.س")
        else:
            bot.send_message(chat_id, "محفظة الشام كاش غير مربوطة بحسابك.\nاستخدم الأمر /link [رقم الهاتف] لربطها أولاً.")

    elif call.data == "add_test_balance":
        conn = sqlite3.connect('zeus_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            new_balance = row[0] + 10000.0
            cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
        else:
            cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 10000.0))
            new_balance = 10000.0
            
        conn.commit()
        conn.close()
        bot.send_message(chat_id, f"تم إضافة 10,000 ل.س تجريبية بنجاح!\nرصيدك الحالي أصبح: {new_balance:,.0f} ل.س")

    elif call.data == "my_transactions":
        conn = sqlite3.connect('zeus_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT service_name, package, price, timestamp FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 10', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            bot.send_message(chat_id, "سجل مشترياتي:\n\nلم تقم بأي عمليات شراء حتى الآن من خلال البوت.")
        else:
            text = "سجل آخر 10 عمليات شراء لك:\n\n"
            for idx, row in enumerate(rows, 1):
                srv, pkg, prc, t = row
                text += f"{idx}. الخدمة: {str(srv).upper()}\n   - الباقة: {pkg}\n   - السعر: {prc:,.0f} ل.س\n   - الوقت: {t}\n\n"
            bot.send_message(chat_id, text)

    elif call.data == "games_menu":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🃏 الجواكر (Jawaker)", callback_data="jawaker_shop"),
            InlineKeyboardButton("🔴 PUBG Mobile", callback_data="pubg_shop"),
            InlineKeyboardButton("🔵 Free Fire", callback_data="freefire_shop"),
            InlineKeyboardButton("🟡 Call of Duty", callback_data="cod_shop"),
            InlineKeyboardButton("🟢 Roblox (Robux)", callback_data="roblox_shop"),
            InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home")
        )
        bot.send_message(chat_id, "قسم شحن الألعاب والجواكر (بزيادة 5% عن السعر الأساسي)\nاختر اللعبة أو المنصة:", reply_markup=markup)

    elif call.data == "jawaker_shop":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("توكنز الجواكر - 50k (15,750 ل.س)", callback_data="buy_game_jawaker_50k_15750"),
            InlineKeyboardButton("توكنز الجواكر - 150k (42,000 ل.س)", callback_data="buy_game_jawaker_150k_42000"),
            InlineKeyboardButton("اشتراك VIP شهري (26,250 ل.س)", callback_data="buy_game_jawaker_VIP_26250"),
            InlineKeyboardButton("🔙 رجوع للألعاب", callback_data="games_menu")
        )
        bot.send_message(chat_id, "شحن توكنز واشتراكات الجواكر (Jawaker)\nاختر الباقة المطلوبة:", reply_markup=markup)

    elif call.data == "pubg_shop":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("60 شدة (5,250 ل.س)", callback_data="buy_game_pubg_60_5250"),
            InlineKeyboardButton("325 شدة (26,250 ل.س)", callback_data="buy_game_pubg_325_26250"),
            InlineKeyboardButton("660 شدة (52,500 ل.س)", callback_data="buy_game_pubg_660_52500"),
            InlineKeyboardButton("🔙 رجوع للألعاب", callback_data="games_menu")
        )
        bot.send_message(chat_id, "شحن PUBG Mobile\nاختر الباقة المطلوبة:", reply_markup=markup)

    elif call.data == "freefire_shop":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("100 جوهرة (4,725 ل.س)", callback_data="buy_game_ff_100_4725"),
            InlineKeyboardButton("310 جوهرة (14,700 ل.س)", callback_data="buy_game_ff_310_14700"),
            InlineKeyboardButton("🔙 رجوع للألعاب", callback_data="games_menu")
        )
        bot.send_message(chat_id, "شحن Free Fire\nاختر الباقة المطلوبة:", reply_markup=markup)

    elif call.data == "cod_shop":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("80 CP (6,300 ل.س)", callback_data="buy_game_cod_80_6300"),
            InlineKeyboardButton("420 CP (31,500 ل.س)", callback_data="buy_game_cod_420_31500"),
            InlineKeyboardButton("🔙 رجوع للألعاب", callback_data="games_menu")
        )
        bot.send_message(chat_id, "شحن Call of Duty\nاختر الباقة المطلوبة:", reply_markup=markup)

    elif call.data == "roblox_shop":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("400 Robux (18,900 ل.س)", callback_data="buy_game_roblox_400_18900"),
            InlineKeyboardButton("800 Robux (36,750 ل.س)", callback_data="buy_game_roblox_800_36750"),
            InlineKeyboardButton("🔙 رجوع للألعاب", callback_data="games_menu")
        )
        bot.send_message(chat_id, "شحن Roblox\nاختر الباقة المطلوبة:", reply_markup=markup)

    elif call.data == "voice_chat_menu":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🎙️ Hago (هاجو)", callback_data="vc_hago"),
            InlineKeyboardButton("🎧 Yome Live (يومي لايف)", callback_data="vc_yome"),
            InlineKeyboardButton("💬 Tango (تانغو)", callback_data="vc_tango"),
            InlineKeyboardButton("🟣 Bigo Live (بيغو لايف)", callback_data="vc_bigo"),
            InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home")
        )
        bot.send_message(chat_id, "قسم شحن تطبيقات الدردشة الصوتية والبث المباشر\nاختر التطبيق المطلوب:", reply_markup=markup)

    elif call.data in ["vc_hago", "vc_yome", "vc_tango", "vc_bigo"]:
        vc_names = {
            "vc_hago": "Hago (هاجو)",
            "vc_yome": "Yome Live (يومي لايف)",
            "vc_tango": "Tango (تانغو)",
            "vc_bigo": "Bigo Live (بيغو لايف)"
        }
        chosen_vc = vc_names[call.data]
        bot.send_message(chat_id, f"لقد اخترت شحن وتعبئة {chosen_vc}.\nالرجاء إرسال معرف الحساب (ID) الخاص بك في رسالة نصية لإتمام الطلب:")

    elif call.data.startswith("buy_game_"):
        parts = call.data.split("_")
        game = parts[2]
        package = parts[3]
        price = price = float(parts[4]))
        send_order_to_admin(call.message, f"لعبة: {game} - باقة: {package}", price)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"💳 تأكيد ودفع ({price:,.0f} ل.س)", callback_data=f"pay_confirm_{game}_{package}_{price}"))
        markup.add(InlineKeyboardButton("🔙 إلغاء", callback_data="games_menu"))
        bot.send_message(chat_id, f"ملخص طلب الشراء\n- الخدمة: {game.upper()}\n- الباقة: {package}\n- التكلفة: {price:,.0f} ل.س\n\nاضغط لتأكيد الخصم والدفع الفوري:", reply_markup=markup)

    elif call.data.startswith("pay_confirm_"):
        parts = call.data.split("_")
        game = parts[2]
        package = parts[3]
        price = float(parts[4])
        
        conn = sqlite3.connect('zeus_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT wallet_number, balance FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if not row or not row[0]:
            conn.close()
            bot.send_message(chat_id, "عذراً، محفظتك غير مربوطة!\nاستخدم الأمر /link [رقم الهاتف] أولاً.")
        else:
            wallet = row[0]
            balance = row[1]
            if balance >= price:
                success, msg = send_alsham_cash_request(wallet, price, f"{game} - {package}")
                
                if success:
                    new_balance = balance - price
                    cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
                    cursor.execute('''
                        INSERT INTO transactions (user_id, service_name, package, price)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, game, package, price))
                    conn.commit()
                    conn.close()
                    bot.send_message(chat_id, f"تمت عملية الدفع بنجاح!\n\n- حالة البوابة: {msg}\n- رقم المحفظة: {wallet}\n- المنتج: {package} لـ {game.upper()}\n- المبلغ المسحوب: {price:,.0f} ل.س\n- الرصيد المتبقي: {new_balance:,.0f} ل.س")
                else:
                    conn.close()
                    bot.send_message(chat_id, f"فشلت عملية الدفع من بوابة الشام كاش:\n{msg}")
            else:
                conn.close()
                bot.send_message(chat_id, f"فشلت العملية: رصيدك غير كافٍ!\n- رصيدك الحالي: {balance:,.0f} ل.س\n- المبلغ المطلوب: {price:,.0f} ل.س")

    elif call.data == "apps_menu":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🎬 Shahid VIP", callback_data="app_shahid"),
            InlineKeyboardButton("🍿 Netflix", callback_data="app_netflix"),
            InlineKeyboardButton("🟢 Google Play", callback_data="app_google"),
            InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home")
        )
        bot.send_message(chat_id, "قسم التطبيقات والبطاقات الترفيهية\nاختر المطلوب:", reply_markup=markup)

    elif call.data in ["app_shahid", "app_netflix", "app_google"]:
        app_names = {
            "app_shahid": "Shahid VIP",
            "app_netflix": "Netflix",
            "app_google": "Google Play Gift Card"
        }
        chosen = app_names[call.data]
        bot.send_message(chat_id, f"لقد اخترت خدمة {chosen}.\nالرجاء إرسال البريد أو التفاصيل المطلوبة في رسالة:")

    elif call.data == "recharge_menu":
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("سيريتل (Syriatel)", callback_data="rec_syriatel"),
            InlineKeyboardButton("إم تي إن (MTN)", callback_data="rec_mtn"),
            InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home")
        )
        bot.send_message(chat_id, "تعبئة رصيد الموبايل الفوري\nاختر شبكة الاتصال:", reply_markup=markup)

    elif call.data in ["rec_syriatel", "rec_mtn"]:
        net = "سيريتل" if call.data == "rec_syriatel" else "إم تي إن"
        bot.send_message(chat_id, f"أنت تريد التعبئة على شبكة {net}.\nالرجاء إرسال رقم الموبايل المطلوب:")

    elif call.data == "bills_menu":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🌐 تسديد الإنترنت الأرضي (ADSL)", callback_data="bill_adsl"),
            InlineKeyboardButton("💡 فواتير الكهرباء", callback_data="bill_electricity"),
            InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home")
        )
        bot.send_message(chat_id, "قسم تسديد الفواتير والخدمات العامة\nاختر نوع الفاتورة:", reply_markup=markup)

    elif call.data == "bill_adsl":
        bot.send_message(chat_id, "الرجاء إرسال رقم الهاتف الأرضي مع رمز المحافظة لتسديد فاتورة الـ ADSL:")

    elif call.data == "bill_electricity":
        bot.send_message(chat_id, "الرجاء إرسال رقم العداد أو الاشتراك الكهربائي:")

    elif call.data == "support":
        bot.send_message(chat_id, f"للتواصل المباشر مع الدعم الفني لمنصة ZEUS:\nرقم التواصل: 0951984521")

    elif call.data == "back_home":
        send_welcome(call.message)

@bot.message_handler(commands=['link'])
def handle_link_command(message):
    args = message.text.split()
    if len(args) > 1:
        phone = args[1]
        user_id = message.from_user.id
        
        conn = sqlite3.connect('zeus_bot.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, wallet_number, balance)
            VALUES (?, ?, 0.0)
            ON CONFLICT(user_id) DO UPDATE SET wallet_number = ?
        ''', (user_id, phone, phone))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"ZEUS: تم ربط رقم محفظة الشام كاش بنجاح:\n{phone}")
    else:
        bot.reply_to(message, "يرجى كتابة الرقم بعد الأمر بشكل صحيح.\nمثال: /link 0930000000")

print("Bot ZEUS is running successfully on Free Web Service tier...")
bot.infinity_polling()
def send_order_to_admin(message, service_name, amount):
  user = message.from_user
  notification_text = (
      f"🚨 طلب تعبئة جديد وصل لمرحلة الدفع!\n\n"
      f"👤 اسم المستخدم: {user.first_name}\n"
      f"🆔 المعرف: @{user.username if user.username else 'لا يوجد'}\n"
      f"🔢 الآيدي: `{user.id}`\n"
      f"📦 الخدمة المطلوبة: {service_name}\n"
      f"💰 المبلغ: {amount}\n"
      f"💳 بانتظار إتمام الدفع عبر شام كاش..."
  )
  bot.send_message(ADMIN_ID, notification_text, parse_mode="Markdown")
