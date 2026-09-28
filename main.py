import os
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


threading.Thread(target=run_web_server).start()

# جلب توكن البوت بأمان من إعدادات منصة Render
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# الآيدي الرقمي الصحيح الخاص بك لتلقي الطلبات
ADMIN_ID = 1632433018

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
  """دالة لتوليد السعر بالدولار وما يعادلها بالليرة السورية تلقائياً مع فاصل الآلاف"""
  syp_amount = int(usd_amount * USD_TO_SYP_RATE)
  return f'${usd_amount} ({syp_amount:,} ل.س)'


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
      f'🔢 الآيدي: {user.id}\n'
      f'📱 الحساب أو المعلومات المدخلة: {user_input}\n'
      f'📦 الخدمة المطلوبة: {service_name}\n\n'
      f'👉 بانتظار إتمام العميل للتحويل وإرسال إشعار أو رقم عملية التحويل.'
  )
  try:
    bot.send_message(ADMIN_ID, notification_text)
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
      f'📸 إيصال دفع جديد (صورة) مرسل من عميل!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: {user.id}\n\n'
      f'👉 يرجى التحقق من وصول المبلغ على المحافظ لتنفيذ الطلب.'
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
        '✅ **تم استلام إيصال الدفع بنجاح!**\nجاري التحقق من قبل الإدارة وتنفيذ طلبك'
        ' في أقرب وقت ❤️',
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
  except Exception as e:
    print(f'Error forwarding payment receipt photo: {e}')


# 💳 استقبال أرقام عمليات التحويل أو نصوص إشعارات الدفع من العملاء
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
      f'💰 إشعار دفع / رقم عملية تحويل مرسل كنص من عميل!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: {user.id}\n\n'
      f'📝 النص أو رقم العملية المرسل:\n`{text_content}`\n\n'
      f'👉 يرجى مطابقة رقم العملية مع الحسابات لتأكيد التحويل.'
  )

  try:
    bot.send_message(
        ADMIN_ID,
        notification_text,
        reply_markup=get_persistent_keyboard(),
    )
    bot.reply_to(
        message,
        '✅ **تم استلام رقم العملية / إشعار الدفع بنجاح!**\nجاري التحقق من قبل الإدارة وتنفيذ طلبك'
        ' في أقرب وقت (مدة التحقق خلال 60 دقيقة) ❤️',
        reply_markup=get_persistent_keyboard(),
        parse_mode='Markdown',
    )
  except Exception as e:
    print(f'Error forwarding text receipt: {e}')


# دالة تتيح للإدارة الرد على العملاء مباشرة عبر الرد (Reply)
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
    else:
      bot.reply_to(message, '⚠️ لم يتم العثور على آيدي العميل في الرسالة الأصلية.')
  except Exception as e:
    print(f'Error sending reply to client: {e}')
    bot.reply_to(message, f'❌ حدث خطأ أثناء إرسال الرد: {e}')


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
        'لأي استفسار أو طلب خاص يرجى الضغط على الزر المناسب للتواصل مباشرة عبر'
        ' **تليجرام** مع الإدارة 👇'
    )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            '👤 تواصل مع ALI (تليجرام)', url='https://t.me/Ali_Username'
        ),
        InlineKeyboardButton(
            '👤 تواصل مع ALAA (تليجرام)', url='https://t.me/Alaa_Username'
        ),
        InlineKeyboardButton(
            '🚨 قسم الشكاوى (تليجرام)', url='https://t.me/Complaints_Username'
        ),
        InlineKeyboardButton('🏠 القائمة الرئيسية', callback_data='back_home'),
    )
    bot.send_message(
        message.chat.id,
        support_text,
        reply_markup=markup,
        parse_mode='Markdown',
    )


# أمر البدء الرئيسي /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
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
        InlineKeyboardButton(
            '✨ طلب حزم وترقية وشعارات (تواصل مع الدعم)',
            callback_data='menu_support',
        ),
    )
  elif game == 'freefire':
    markup.add(
        InlineKeyboardButton(
            f'Free Fire: 100+10 جوهرة ({price_text(1.5)})',
            callback_data='order_FreeFire_110_Gems_$1.5',
        ),
        InlineKeyboardButton(
            f'Free Fire: 210+21 جوهرة ({price_text(2.5)})',
            callback_data='order_FreeFire_231_Gems_$2.5',
        ),
        InlineKeyboardButton(
            f'Free Fire: 530+53 جوهرة ({price_text(5.8)})',
            callback_data='order_FreeFire_583_Gems_$5.8',
        ),
        InlineKeyboardButton(
            f'Free Fire: 1080+120 جوهرة ({price_text(11)})',
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
        InlineKeyboardButton(
            f'Call of Duty: 2400 CP ({price_text(35.2)})',
            callback_data='order_COD_2400_CP_$35.2',
        ),
        InlineKeyboardButton(
            f'Call of Duty: 5000 CP ({price_text(68.6)})',
            callback_data='order_COD_5000_CP_$68.6',
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
      text=f'🎮 **حزم قسم الألعاب:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 2. قسم الذكاء الاصطناعي / AI 💭 ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_ai')
def ai_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'ChatGPT Plus: 1 Month تفعيل شخصي ({price_text(19)})',
          callback_data='order_AI_ChatGPT_Plus_شهر1_$19',
      ),
      InlineKeyboardButton(
          f'Gemini AI: 6 Months تفعيل شخصي  ({price_text(12)})',
          callback_data='order_AI_Gemini_6 Months _$12',
      ),
      InlineKeyboardButton(
          f'Gemini AI Pro: تفعيل 1 Month ({price_text(3.7)})',
          callback_data='order_AI_GeminiPro_ 6 Months _$3.7',
      ),
      InlineKeyboardButton(
          f'Gemini AI Pro: تفعيل 12 Months ({price_text(49)})',
          callback_data='order_AI_GeminiPro_12 شهر_$49',
      ),
      InlineKeyboardButton(
          f'CapCut Pro: تفعيل شخصي 1 Month ({price_text(15)})',
          callback_data='order_AI_CapCut_1 Month $15',
      ),
      InlineKeyboardButton(
          f'Canva Pro: تفعيل شخصي مع جميع الميزات 12 Months ({price_text(14)})',
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
      InlineKeyboardButton(
          'Lama Chat 🦙 (قريباً ⏳️)', callback_data='chat_lama_soon'
      ),
      InlineKeyboardButton(
          'Lggo Live 🟢 (قريباً ⏳️)', callback_data='chat_lggo_soon'
      ),
      InlineKeyboardButton(
          'Taka Live Chat 🎙️ (قريباً ⏳️)', callback_data='chat_Taka_soon'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💬 **اختر التطبيق المطلوب:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(
    func=lambda call: call.data
    in ['chat_lama_soon', 'chat_lggo_soon', 'chat_Taka_soon']
)
def coming_soon_handler(call):
  bot.answer_callback_query(
      call.id,
      text='هذه الخدمة ستتوفر قريباً ⏳️ Coming soon',
      show_alert=True,
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
          f'Bigo: 200 PC ({price_text(3.9)})',
          callback_data='order_Bigo_200_PC_$3.9',
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


@bot.callback_query_handler(func=lambda call: call.data == 'chat_sool')
def sool_packages(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Sool Chill: 1000 PC ({price_text(1.98)})',
          callback_data='order_Sool_1000_PC_$1.98',
      ),
      InlineKeyboardButton(
          f'Sool Chill: 2000 PC ({price_text(3.88)})',
          callback_data='order_Sool_2000_PC_$3.88',
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


@bot.callback_query_handler(func=lambda call: call.data == 'chat_soul')
def soul_packages(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Soul Chat: 1000 PC ({price_text(2)})',
          callback_data='order_Soul_1000_$2',
      ),
      InlineKeyboardButton(
          f'Soul Chat: 2000 PC ({price_text(3.9)})',
          callback_data='order_Soul_2000_$3.9',
      ),
      InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💫 **حزم Soul Chat:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'chat_zaffa')
def zaffa_packages(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Zaffa: 60,000 PC ({price_text(1.2)})',
          callback_data='order_Zaffa_60k_$1.2',
      ),
      InlineKeyboardButton(
          f'Zaffa: 100,000 PC ({price_text(1.9)})',
          callback_data='order_Zaffa_100k_$1.9',
      ),
      InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🌟 **حزم Zaffa Live:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'chat_sugo')
def sugo_packages(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Sugo: 10,000 PC ({price_text(1.8)})',
          callback_data='order_Sugo_10k_$1.8',
      ),
      InlineKeyboardButton(
          f'Sugo: 20,000 PC ({price_text(3.4)})',
          callback_data='order_Sugo_20k_$3.4',
      ),
      InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💬 **حزم Sugo Live:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'chat_honey')
def honey_packages(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Honey Jar: 200 PC ({price_text(1.9)})',
          callback_data='order_Honey_200_$1.9',
      ),
      InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🍯 **حزم Honey Jar:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'chat_mico')
def mico_packages(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Mico: 5000 PC ({price_text(2.1)})',
          callback_data='order_Mico_5000_$2.1',
      ),
      InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💜 **حزم Mico Live:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'chat_likee')
def likee_packages(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Likee: 250 PC ({price_text(5.5)})',
          callback_data='order_Likee_250_$5.5',
      ),
      InlineKeyboardButton('🔙 رجوع', callback_data='menu_chat'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💛 **حزم Likee Live:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 4. تعبئة الرصيد / RECHARGE ---
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


# --- 5. توثيق الحسابات / ACCOUNTS VERIFICATION ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_verify')
def verify_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'YouTube:  1 Month ({price_text(4.5)})',
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


# --- 6. خدمات متنوعة / Various Services ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_various')
def various_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '📁 شراء مساحة تخزين GOOGLE', callback_data='order_Google_Storage'
      ),
      InlineKeyboardButton('⭐ نجوم تلغرام', callback_data='menu_tg_stars'),
      InlineKeyboardButton(
          f'🚫 فك الحظر عن واتساب ({price_text(1.5)})',
          callback_data='order_WhatsApp_Unban_$1.5',
      ),
      InlineKeyboardButton(
          f'👥 متابعين FACEBOOK: 1000 متابع ({price_text(2)})',
          callback_data='order_FB_1k_$2',
      ),
      InlineKeyboardButton(
          f'📸 متابعين INSTAGRAM: 1000 متابع ({price_text(4)})',
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


@bot.callback_query_handler(func=lambda call: call.data == 'menu_tg_stars')
def tg_stars_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'⭐ 50 نجمة ({price_text(1.5)})',
          callback_data='order_Telegram_Stars_50_$1.5',
      ),
      InlineKeyboardButton('🔙 رجوع', callback_data='menu_various'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='⭐ **نجوم تلغرام:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 7. خدمة تخطي الموقع VPN (بروكسي) ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_vpn')
def vpn_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton('🛡️ OPEN VPN', callback_data='vpn_open'),
      InlineKeyboardButton('🛡️ EXPRESS VPN', callback_data='vpn_express'),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=(
          '🛡️ **خدمة تخطي الموقع VPN (بروكسي):**\nاختر نوع البروكسي أو الخدمة'
          ' المطلوبة:'
      ),
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'vpn_open')
def vpn_open_packages(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Open VPN: 1 Month ({price_text(2)})',
          callback_data='order_OpenVPN_1 Month _$2',
      ),
      InlineKeyboardButton('🔙 رجوع', callback_data='menu_vpn'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🛡️ **حزم Open VPN:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(func=lambda call: call.data == 'vpn_express')
def vpn_express_packages(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'Express VPN: 1 Month ({price_text(6)})',
          callback_data='order_ExpressVPN_1 Month _$6',
      ),
      InlineKeyboardButton('🔙 رجوع', callback_data='menu_vpn'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🛡️ **حزم Express VPN:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 8. خدمات ويندوز / WINDOWS SERVICES ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_windows')
def windows_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          f'🔑 تنشيط وتفعيل مفاتيح ويندوز ({price_text(5)})',
          callback_data='order_Windows_Activation_$5',
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


# --- 9. خدمات مزودين الانترنت / INTERNET SERVICES ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_internet')
def internet_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton('🌐 زاد (ZAD)', callback_data='order_ISP_ZAD'),
      InlineKeyboardButton('🌐 سوا (Sawa)', callback_data='order_ISP_Sawa'),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🌐 **اختر مزود الانترنت المطلوب:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 🔟. خدمات شام كاش / SHAM CASH ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_sham_cash')
def sham_cash_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '🇸🇾 SYP ➡️ 🇺🇸 USD', callback_data='order_Sham_SYP_USD'
      ),
      InlineKeyboardButton(
          ' 🇺🇸 USD ➡️ 🇸🇾 SYP', callback_data='order_Sham_USD_SYP'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  sham_text = (
      '💳 **خدمات محفظة شام كاش (SHAM CASH):**\n\n'
      'نقدم خدمة مميزة للتحويل بين العملة السورية والعملات الأجنبية بكل أمان'
      ' وسرعة.\n\n'
      '📊 **العمولة:** 3%\n\n'
      '👇 **اختر اتجاه التحويل المطلوب:**'
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=sham_text,
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 1️⃣1️⃣. خدمة العملاء / SUPPORT TEAM (تليجرام فقط) ---
@bot.callback_query_handler(func=lambda call: call.data == 'menu_support')
def support_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '👤 تواصل مع ALI (تليجرام)', url='https://t.me/Ali_Username'
      ),
      InlineKeyboardButton(
          '👤 تواصل مع ALAA (تليجرام)', url='https://t.me/Alaa_Username'
      ),
      InlineKeyboardButton(
          '🚨 قسم الشكاوى (تليجرام)', url='https://t.me/Complaints_Username'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  support_text = (
      '📞 **خدمة العملاء والدعم الفني - ZEUS**\n\n'
      'لأي استفسار أو طلب خاص يرجى الضغط على الزر المناسب للتواصل مباشرة عبر'
      ' **تليجرام** مع الإدارة 👇'
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
  if call.data.startswith('order_Sham_'):
    sham_type = call.data.replace('order_Sham_', '')
    service_name = f'شام كاش ({sham_type})'
  else:
    service_name = (
        call.data.replace('order_', '').replace('chat_', '').replace('_', ' ')
    )

  prompt_text = (
      f'📦 الخدمة المختارة: {service_name}\n\n'
      f'✍️ **يرجى إرسال رقم (ID)، أو تفاصيل الطلب المطلوبة في رسالة واحدة:**'
  )

  msg = bot.send_message(
      call.message.chat.id, prompt_text, parse_mode='Markdown'
  )
  bot.register_next_step_handler(msg, process_user_order, service_name)


# استقبال مدخلات العميل وإرسال الإشعار للإدارة ومعلومات المحافظ
def process_user_order(message, service_name):
  user_input = message.text

  if user_input == '🏠 القائمة الرئيسية / Main Menu':
    send_welcome(message)
    return
  elif user_input == '📞 الدعم الفني / Support':
    support_text = (
        '📞 **خدمة العملاء والدعم الفني - ZEUS**\n\n'
        'لأي استفسار يرجى الضغط على الزر المناسب للتواصل مباشرة عبر'
        ' **تليجرام** مع الإدارة 👇'
    )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            '👤 تواصل مع ALI (تليجرام)', url='https://t.me/@Ali00700Ali'
        ),
        InlineKeyboardButton(
            '👤 تواصل مع ALAA (تليجرام)', url='https://t.me/@Alaaessa199'
        ),
        InlineKeyboardButton(
            '🚨 قسم الشكاوى (تليجرام)', url='https://t.me/Complaints_Username'
        ),
        InlineKeyboardButton('🏠 القائمة الرئيسية', callback_data='back_home'),
    )
    bot.send_message(
        message.chat.id,
        support_text,
        reply_markup=markup,
        parse_mode='Markdown',
    )
    return

  send_order_to_admin(message, service_name, user_input)

  caption_text = (
      f'✅ **تم تسجيل طلبك بنجاح بواسطة فريق ZEUS!**\n\n'
      f'📦 الخدمة: {service_name}\n'
      f'📱 التفاصيل المرسلة: `{user_input}`\n\n'
      f'💳 **طرق الدفع المتاحة:**\n\n'
      f'1️⃣ **شام كاش:**\n`{SHAM_CASH_WALLET}`\n\n'
      f'2️⃣ **بينانس TRX:**\n`{TRX_WALLET}`\n\n'
      f'3️⃣ **بلازما:**\n`{PLASMA_WALLET}`\n\n'
      f'📝 **بعد إتمام التحويل، أرسل رقم العملية أو إشعار الدفع هنا.**'
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
    print(f'Error sending photo: {e}')


if __name__ == '__main__':
  print('ZEUS Bot is running...')
  bot.infinity_polling()
