import os
import threading
import time
import urllib3
from bs4 import BeautifulSoup
from flask import Flask
import requests
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

# تعطيل تحذيرات الأمان الخاصة بـ SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# متغير لتخزين سعر صرف الدولار الحالي (يتم تحديثه تلقائياً من sp-today.com)
USD_TO_SYP_RATE = 15000.0  # قيمة افتراضية أولية لحين جلب السعر الفعلي


def update_exchange_rates():
  global USD_TO_SYP_RATE
  while True:
    try:
      url = 'https://sp-today.com/'
      headers = {
          'User-Agent': (
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
              ' (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
          )
      }
      response = requests.get(url, headers=headers, timeout=10, verify=False)

      if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table_rows = soup.find_all('tr')
        for row in table_rows:
          cols = row.find_all('td')
          if len(cols) >= 3:
            name = cols[0].get_text(strip=True)
            if 'دولار' in name:
              price_text = cols[1].get_text(strip=True)
              clean_price = (
                  price_text.replace(',', '')
                  .replace('ل.س', '')
                  .replace('SYP', '')
                  .strip()
              )
              import re

              nums = re.findall(r'\d+\.?\d*', clean_price)
              if nums:
                USD_TO_SYP_RATE = float(nums[0])
                print(
                    f'✅ تم تحديث سعر صرف الدولار بنجاح من SP-Today:'
                    f' {USD_TO_SYP_RATE}'
                )
                break
    except Exception as e:
      print(f'❌ حدث خطأ أثناء جلب سعر الصرف من SP-Today: {e}')

    # الانتظار لمدة ساعتين (7200 ثانية) قبل التحديث القادم
    time.sleep(7200)


# تشغيل خيط تحديث الأسعار في الخلفية
threading.Thread(target=update_exchange_rates, daemon=True).start()


def get_syp_price(usd_price):
  """دالة لتحويل السعر من الدولار إلى الليرة السورية بناءً على السعر المحدث"""
  global USD_TO_SYP_RATE
  syp_amount = int(usd_price * USD_TO_SYP_RATE)
  return f'{syp_amount:,} ل.س'


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

# رقم محفظة شام كاش الخاصة بك
SHAM_CASH_WALLET = '02d28a07292f2a11f12e0d8e2bd08dd1'


# دالة لوحة المفاتيح الثابتة (تظهر دائماً أسفل محادثة العميل)
def get_persistent_keyboard():
  markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      KeyboardButton('🏠 القائمة الرئيسية / Main Menu'),
      KeyboardButton('📞 الدعم الفني / Support'),
  )
  return markup


# دالة إرسال تفاصيل الطلب الأولي إلى حسابك الشخصي مباشرة
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


# 📸 استقبال صور إيصالات الدفع (سكرين شوت) من العملاء وتحويلها للإدارة فوراً
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
      f'👉 يرجى التحقق من وصول المبلغ على محفظة شام كاش لتنفيذ الطلب.'
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


# 💳 استقبال أرقام عمليات التحويل أو نصوص إشعارات شام كاش من العملاء وتحويلها فوراً
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
      f'👉 يرجى مطابقة رقم العملية مع حساب شام كاش لتأكيد التحويل.'
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


# استجابة أزرار لوحة المفاتيح الثابتة أسفل الشاشة
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
        '👤 **ALAA:** `0996743743`\n\n'
        'نحن في خدمتكم دائماً ❤️'
    )
    bot.send_message(
        message.chat.id,
        support_text,
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )


# أمر البدء الرئيسي /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
  welcome_text = (
      'اهلا بكم في ⚡️ **ZEUS-ECHANCE-BOT** ⚡️ للخدمات الرقمية الشاملة\n\n'
      'نحن فريق من الأشخاص يمتلك الخبرة لنقدم لك كافه خدمات الشحن والدفع الإلكتروني'
      ' بكافة انواعة بشكل آمن وسريع وبدقة عالية من الاحترافية ❤️\n\n'
      '📌 **ملاحظة:** الأسعار تتحدث تلقائياً وتظهر بالدولار والليرة'
      ' السورية.\n\n'
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
          '9️⃣ خدمة العملاء / SUPPORT TEAM 📞', callback_data='menu_support'
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
          '9️⃣ خدمة العملاء / SUPPORT TEAM 📞', callback_data='menu_support'
      ),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=welcome_text,
      reply_markup=markup,
      parse_mode='Markdown',
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
            f'PUBG: 60 شدة | $1 ({get_syp_price(1)})',
            callback_data='order_PUBG_60_UC_$1',
        ),
        InlineKeyboardButton(
            f'PUBG: 325 شدة | $5.5 ({get_syp_price(5.5)})',
            callback_data='order_PUBG_325_UC_$5.5',
        ),
        InlineKeyboardButton(
            f'PUBG: 660 شدة | $10.2 ({get_syp_price(10.2)})',
            callback_data='order_PUBG_660_UC_$10.2',
        ),
        InlineKeyboardButton(
            f'PUBG: 1800 شدة | $24.8 ({get_syp_price(24.8)})',
            callback_data='order_PUBG_1800_UC_$24.8',
        ),
        InlineKeyboardButton(
            f'PUBG: 3800 شدة | $49.7 ({get_syp_price(49.7)})',
            callback_data='order_PUBG_3800_UC_$49.7',
        ),
        InlineKeyboardButton(
            '✨ طلب حزم وترقية وشعارات (تواصل مع الدعم)',
            callback_data='menu_support',
        ),
    )
  elif game == 'freefire':
    markup.add(
        InlineKeyboardButton(
            f'Free Fire: 100+10 جوهرة | $1.5 ({get_syp_price(1.5)})',
            callback_data='order_FreeFire_110_Gems_$1.5',
        ),
        InlineKeyboardButton(
            f'Free Fire: 210+21 جوهرة | $2.5 ({get_syp_price(2.5)})',
            callback_data='order_FreeFire_231_Gems_$2.5',
        ),
        InlineKeyboardButton(
            f'Free Fire: 530+53 جوهرة | $5.8 ({get_syp_price(5.8)})',
            callback_data='order_FreeFire_583_Gems_$5.8',
        ),
        InlineKeyboardButton(
            f'Free Fire: 1080+120 جوهرة | $11 ({get_syp_price(11)})',
            callback_data='order_FreeFire_1200_Gems_$11',
        ),
        InlineKeyboardButton(
            '✨ طلب حزمة عضوية (تواصل مع الدعم)', callback_data='menu_support'
        ),
    )
  elif game == 'jawaker':
    markup.add(
        InlineKeyboardButton(
            f'Jawaker: 10,000 جوهرة | $1.8 ({get_syp_price(1.8)})',
            callback_data='order_Jawaker_10k_Gems_$1.8',
        ),
        InlineKeyboardButton(
            f'Jawaker: 20,000 جوهرة | $3.2 ({get_syp_price(3.2)})',
            callback_data='order_Jawaker_20k_Gems_$3.2',
        ),
        InlineKeyboardButton(
            '✨ طلب توكنز أسبوعي (تواصل مع الدعم)',
            callback_data='menu_support',
        ),
    )
  elif game == 'clash':
    markup.add(
        InlineKeyboardButton(
            f'Clash: 80 جوهرة | $2 ({get_syp_price(2)})',
            callback_data='order_Clash_80_Gems_$2',
        ),
        InlineKeyboardButton(
            f'Clash: 500 جوهرة | $8 ({get_syp_price(8)})',
            callback_data='order_Clash_500_Gems_$8',
        ),
        InlineKeyboardButton(
            '✨ طلب المزيد (تواصل مع الدعم)', callback_data='menu_support'
        ),
    )
  elif game == 'cod':
    markup.add(
        InlineKeyboardButton(
            f'Call of Duty: 30 CP | $0.8 ({get_syp_price(0.8)})',
            callback_data='order_COD_30_CP_$0.8',
        ),
        InlineKeyboardButton(
            f'Call of Duty: 80 CP | $2.1 ({get_syp_price(2.1)})',
            callback_data='order_COD_80_CP_$2.1',
        ),
        InlineKeyboardButton(
            f'Call of Duty: 320 CP | $7.5 ({get_syp_price(7.5)})',
            callback_data='order_COD_320_CP_$7.5',
        ),
        InlineKeyboardButton(
            '✨ طلب المزيد (تواصل مع الدعم)', callback_data='menu_support'
        ),
    )

  markup.add(InlineKeyboardButton('🔙 رجوع', callback_data='menu_games'))
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=f'🎮 **حزم قسم الألعاب (تظهر بالدولار والليرة السورية):**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 2. التطبيقات الصوتية والدردشة / CHAT APP ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_chat')
def chat_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton('Bigo Live 🔴', callback_data='chat_bigo'),
      InlineKeyboardButton('Sool Chill 💬', callback_data='chat_sool'),
      InlineKeyboardButton('Likee Live 💛', callback_data='order_Likee_Live'),
      InlineKeyboardButton('Sugo Chat 💬', callback_data='order_Sugo_Chat'),
      InlineKeyboardButton('Hony Jar 🍯', callback_data='order_Hony_Jar'),
      InlineKeyboardButton('Lama Chat 🦙', callback_data='order_Lama_Chat'),
      InlineKeyboardButton('Lggo Live 🟢', callback_data='order_Lggo_Live'),
      InlineKeyboardButton(
          'Taka Live Chat 🎙️', callback_data='order_Taka_Live'
      ),
      InlineKeyboardButton('Soul Chat 💫', callback_data='order_Soul_Chat'),
      InlineKeyboardButton('Mico Live 💜', callback_data='order_Mico_Live'),
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
          f'Bigo: 50 PC | $1 ({get_syp_price(1)})',
          callback_data='order_Bigo_50_PC_$1',
      ),
      InlineKeyboardButton(
          f'Bigo: 100 PC | $1.9 ({get_syp_price(1.9)})',
          callback_data='order_Bigo_100_PC_$1.9',
      ),
      InlineKeyboardButton(
          f'Bigo: 200 PC | $3.8 ({get_syp_price(3.8)})',
          callback_data='order_Bigo_200_PC_$3.8',
      ),
      InlineKeyboardButton(
          f'Bigo: 500 PC | $11 ({get_syp_price(11)})',
          callback_data='order_Bigo_500_PC_$11',
      ),
      InlineKeyboardButton(
          f'Bigo: 1000 PC | $21 ({get_syp_price(21)})',
          callback_data='order_Bigo_1000_PC_$21',
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


@bot.callback_query_handler(func=lambda call: call.data == 'chat_sool')
def sool_packages(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Sool Chill: 1000 PC | $1.98 ({get_syp_price(1.98)})',
          callback_data='order_Sool_1000_PC_$1.98',
      ),
      InlineKeyboardButton(
          f'Sool Chill: 2000 PC | $3.88 ({get_syp_price(3.88)})',
          callback_data='order_Sool_2000_PC_$3.88',
      ),
      InlineKeyboardButton(
          f'Sool Chill: 3000 PC | $5.95 ({get_syp_price(5.95)})',
          callback_data='order_Sool_3000_PC_$5.95',
      ),
      InlineKeyboardButton(
          f'Sool Chill: 4000 PC | $7.95 ({get_syp_price(7.95)})',
          callback_data='order_Sool_4000_PC_$7.95',
      ),
      InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💬 **حزم Sool Chill:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 3. تعبئة الرصيد / RECHARGE ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_recharge')
def recharge_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '📱 Syriatel Recharge', callback_data='order_Recharge_Syriatel'
      ),
      InlineKeyboardButton(
          '📱 MTN Syria Recharge', callback_data='order_Recharge_MTN'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💳 **اختر الشبكة لتعبئة الرصيد:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 4. توثيق الحسابات / ACCOUNTS VERIFICATION ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_verify')
def verify_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'YouTube: 1 شهر | $4.5 ({get_syp_price(4.5)})',
          callback_data='order_YouTube_1M_$4.5',
      ),
      InlineKeyboardButton(
          f'YouTube: 3 أشهر | $13 ({get_syp_price(13)})',
          callback_data='order_YouTube_3M_$13',
      ),
      InlineKeyboardButton(
          f'YouTube: 6 أشهر | $24 ({get_syp_price(24)})',
          callback_data='order_YouTube_6M_$24',
      ),
      InlineKeyboardButton(
          f'YouTube: 12 شهر | $44 ({get_syp_price(44)})',
          callback_data='order_YouTube_12M_$44',
      ),
      InlineKeyboardButton(
          f'Telegram: 3 أشهر | $15 ({get_syp_price(15)})',
          callback_data='order_Telegram_3M_$15',
      ),
      InlineKeyboardButton(
          f'Telegram: 6 أشهر | $22 ({get_syp_price(22)})',
          callback_data='order_Telegram_6M_$22',
      ),
      InlineKeyboardButton(
          f'Telegram: 12 شهر | $35 ({get_syp_price(35)})',
          callback_data='order_Telegram_12M_$35',
      ),
      InlineKeyboardButton(
          f'Snapchat: 3 أشهر | $7 ({get_syp_price(7)})',
          callback_data='order_Snapchat_3M_$7',
      ),
      InlineKeyboardButton(
          f'Snapchat: 6 أشهر | $12 ({get_syp_price(12)})',
          callback_data='order_Snapchat_6M_$12',
      ),
      InlineKeyboardButton(
          f'Snapchat: 12 شهر | $22 ({get_syp_price(22)})',
          callback_data='order_Snapchat_12M_$22',
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


# --- 5. خدمات متنوعة / Various Services ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_various')
def various_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '📁 شراء مساحة تخزين GOOGLE', callback_data='order_Google_Storage'
      ),
      InlineKeyboardButton('⭐ نجوم تلغرام', callback_data='order_Telegram_Stars'),
      InlineKeyboardButton(
          f'🤖 خدمة الرد الآلي FACEBOOK (1 شهر - $4.8) |'
          f' {get_syp_price(4.8)}',
          callback_data='order_FB_Bot_1M_$4.8',
      ),
      InlineKeyboardButton(
          f'🤖 خدمة الرد الآلي FACEBOOK (3 أشهر - $9.6) |'
          f' {get_syp_price(9.6)}',
          callback_data='order_FB_Bot_3M_$9.6',
      ),
      InlineKeyboardButton(
          f'🚫 فك الحظر عن واتساب ($1.5) | {get_syp_price(1.5)}',
          callback_data='order_WhatsApp_Unban_$1.5',
      ),
      InlineKeyboardButton(
          f'👥 متابعين FACEBOOK: 1000 متابع ($2) | {get_syp_price(2)}',
          callback_data='order_FB_1k_$2',
      ),
      InlineKeyboardButton(
          f'👥 متابعين FACEBOOK: 5000 متابع ($9.8) | {get_syp_price(9.8)}',
          callback_data='order_FB_5k_$9.8',
      ),
      InlineKeyboardButton(
          f'👥 متابعين FACEBOOK: 10,000 متابع ($19) | {get_syp_price(19)}',
          callback_data='order_FB_10k_$19',
      ),
      InlineKeyboardButton(
          f'👥 متابعين FACEBOOK: 20,000 متابع ($39) | {get_syp_price(39)}',
          callback_data='order_FB_20k_$39',
      ),
      InlineKeyboardButton(
          f'📸 متابعين INSTAGRAM: 1000 متابع ($4) | {get_syp_price(4)}',
          callback_data='order_IG_1k_$4',
      ),
      InlineKeyboardButton(
          f'📸 متابعين INSTAGRAM: 5000 متابع ($13) | {get_syp_price(13)}',
          callback_data='order_IG_5k_$13',
      ),
      InlineKeyboardButton(
          f'📸 متابعين INSTAGRAM: 10,000 متابع ($24) | {get_syp_price(24)}',
          callback_data='order_IG_10k_$24',
      ),
      InlineKeyboardButton(
          '💬 تفاعل مجموعات الواتساب والمزيد', callback_data='menu_support'
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


# --- 6. خدمة تخطي الموقع VPN (بروكسي) ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_vpn')
def vpn_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '📞 تواصل مع الدعم لطلب البروكسي والمفاتيح',
          callback_data='menu_support',
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=(
          '🛡️ **خدمة تخطي الموقع VPN (بروكسي):**\nيوجد بروكسي لأغلب المواقع'
          ' العالمية مع المفاتيح وبأسعار مميزة يرجى التواصل مع فريق الدعم.'
      ),
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 7. خدمات ويندوز / WINDOWS SERVICES ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_windows')
def windows_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '🔑 تفعيل وتنشيط مفاتيح ويندوز',
          callback_data='order_Windows_Activation',
      ),
      InlineKeyboardButton(
          '🔑 تفعيل وتنشيط مفاتيح أوفيس', callback_data='order_Office_Activation'
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


# --- 8. خدمات مزودين الانترنت / INTERNET SERVICES ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_internet')
def internet_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton('🌐 سوا (Sawa)', callback_data='order_ISP_Sawa'),
      InlineKeyboardButton('🌐 رن نت (RunNet)', callback_data='order_ISP_RunNet'),
      InlineKeyboardButton('🌐 آية (Aya)', callback_data='order_ISP_Aya'),
      InlineKeyboardButton(
          '🌐 تكامل (Takamol)', callback_data='order_ISP_Takamol'
      ),
      InlineKeyboardButton(
          '🌐 الجمعية السورية للمعلوماتية (SCS)', callback_data='order_ISP_SCS'
      ),
      InlineKeyboardButton(
          '🌐 السورية للاتصالات (Syrian Telecom)',
          callback_data='order_ISP_SyrianTelecom',
      ),
      InlineKeyboardButton(
          '🌐 الانترنت الهوائي (Wireless)',
          callback_data='order_ISP_Wireless',
      ),
      InlineKeyboardButton(
          '🌐 الانترنت العالمي (Global)', callback_data='order_ISP_Global'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🌐 **اختر مزود الانترنت المطلوب:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 9. خدمة العملاء / SUPPORT TEAM ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_support')
def support_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'))
  support_text = (
      '📞 **خدمة العملاء والدعم الفني - ZEUS**\n\n'
      'لأي استفسار أو طلب خاص يرجى التواصل مع الإدارة عبر الأرقام التالية:\n\n'
      '👤 **ALI:** `0951984521`\n'
      '👤 **ALAA:** `0996743743`\n\n'
      'نحن في خدمتكم دائماً ❤️'
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=support_text,
      reply_markup=markup,
      parse_mode='Markdown',
  )


# معالجة الطلبات العامة وطلب البيانات من العميل
@bot.callback_query_handler(
    func=lambda call: call.data.startswith('order_')
    or call.data.startswith('chat_')
)
def handle_order_selection(call):
  service_name = call.data.replace('order_', '').replace('_', ' ')

  if 'Recharge' in service_name or 'ISP' in service_name:
    prompt_text = (
        f'📦 الخدمة: {service_name}\n\n'
        f'✍️ **يرجى تزويدنا بالرقم أو كود التعبئة أو تفاصيل اشتراك الإنترنت المطلوبة في رسالة واحدة:**'
    )
  else:
    prompt_text = (
        f'📦 الخدمة المختارة: {service_name}\n\n'
        f'✍️ **يرجى إرسال رقم الهوية (ID)، رابط الحساب، أو تفاصيل الطلب المطلوبة في رسالة واحدة:**'
    )

  msg = bot.send_message(
      call.message.chat.id, prompt_text, parse_mode='Markdown'
  )
  bot.register_next_step_handler(msg, process_user_order, service_name)


# استقبال مدخلات العميل وإرسال الإشعار للإدارة وصورة الباركود ورقم المحفظة
def process_user_order(message, service_name):
  user_input = message.text

  send_order_to_admin(message, service_name, user_input)

  caption_text = (
      f'✅ **تم تسجيل طلبك بنجاح بواسطة فريق ZEUS!**\n\n'
      f'📦 الخدمة: {service_name}\n'
      f'📱 التفاصيل المرسلة: `{user_input}`\n\n'
      f'💳 **يرجى إتمام التحويل إلى محفظة شام كاش:**\n'
      f'رقم المحفظة (اضغط للنسخ):\n'
      f'`{SHAM_CASH_WALLET}`\n\n'
      f'📝 **بعد إتمام التحويل، يرجى إرسال رقم عملية التحويل أو نص الإشعار هنا في المحادثة** (أو صورة إيصال إن وُجدت) لكي يصل إلى الإدارة فوراً وتنفيذ طلبك.'
  )

  try:
    if os.path.exists('sham_cash.jpg'):
      with open('sham_cash.jpg', 'rb') as photo:
        bot.send_photo(
            message.chat.id,
            photo,
            caption=caption_text,
            reply_markup=get_persistent_keyboard(),
            parse_mode='Markdown',
        )
    else:
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
    print(f'Error sending QR photo: {e}')


if __name__ == '__main__':
  print('ZEUS Bot is running...')
  bot.infinity_polling()
