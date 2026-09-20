import os
import threading
import urllib3
from flask import Flask
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# تعطيل تحذيرات الأمان الخاصة بـ SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إعداد خادم ويب مصغر لاستضافة Render ولضمان عمل البوت 24/7
app = Flask('')


@app.route('/')
def home():
  return 'ZEUS Bot is running 24/7!'


def run_web_server():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)


threading.Thread(target=run_web_server).start()

# جلب توكن البوت بأمان من إعدادات منصة Render
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# معرف حسابك الشخصي لتلقي إشعارات الطلبات
ADMIN_ID = '@Ali00700Ali'

# رقم محفظة شام كاش الخاصة بك
SHAM_CASH_WALLET = '02d28a07292f2a11f12e0d8e2bd08dd1'

# أرقام الدعم الفني
SUPPORT_NUMBERS = '0951984521 & 0996743743'


# دالة إرسال تفاصيل الطلب إلى حسابك الشخصي مباشرة
def send_order_to_admin(message, service_name, amount, user_input):
  user = message.from_user
  notification_text = (
      f'🚨 طلب جديد بانتظار التحويل والتنفيذ!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: `{user.id}`\n'
      f'📱 الحساب أو المعلومات المدخلة: `{user_input}`\n'
      f'📦 الخدمة المطلوبة: {service_name}\n'
      f'💰 السعر الإجمالي (مع ربح 12%): {amount}\n\n'
      f'👉 بانتظار إتمام العميل للتحويل عبر شام كاش لتنفيذ الطلب.'
  )
  try:
    bot.send_message(ADMIN_ID, notification_text, parse_mode='Markdown')
  except Exception as e:
    print(f'Error sending notification: {e}')


# أمر البدء الرئيسي /start مع رسالة فريق ZEUS التعريفيّة
@bot.message_handler(commands=['start'])
def send_welcome(message):
  welcome_text = (
      '⚡ **أهلاً بك عزيزي العميل في بوت فريق ZEUS للخدمات الرقمية** ⚡\n\n'
      'نحن فريق **ZEUS**، نمتلك الخبرة لنقدم لك كافة خدمات الشحن الإلكتروني والدفع الآمن بسرعة ودقة عالية.\n\n'
      'يرجى اختيار القسم المطلوب من القائمة أدناه:'
  )

  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '🎮 1. شحن الألعاب (ببجي، فري فاير، كلاش، جواكر)',
          callback_data='games_menu',
      ),
      InlineKeyboardButton(
          '💬 2. شحن تطبيقات الدردشة (بيغو، سوبو، وغيرها)',
          callback_data='chat_menu',
      ),
      InlineKeyboardButton(
          '📄 3. دفع الفواتير (كهرباء، مياه، إنترنت)',
          callback_data='bills_menu',
      ),
      InlineKeyboardButton(
          '💳 4. تعبئة الرصيد (MTN / Syriatel)', callback_data='topup_menu'
      ),
      InlineKeyboardButton(
          '🌐 5. خدمات غوغل بلاي', callback_data='google_menu'
      ),
      InlineKeyboardButton(
          '📞 6. تواصل مع فريق الدعم', callback_data='support_menu'
      ),
  )
  bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode='Markdown')


# زر العودة للقائمة الرئيسية
@bot.callback_query_handler(func=lambda call: call.data == 'back_home')
def back_home(call):
  welcome_text = (
      '⚡ **القائمة الرئيسية - فريق ZEUS** ⚡\n\n'
      'يرجى اختيار القسم المطلوب:'
  )
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '🎮 1. شحن الألعاب (ببجي، فري فاير، كلاش، جواكر)',
          callback_data='games_menu',
      ),
      InlineKeyboardButton(
          '💬 2. شحن تطبيقات الدردشة (بيغو، سوبو، وغيرها)',
          callback_data='chat_menu',
      ),
      InlineKeyboardButton(
          '📄 3. دفع الفواتير (كهرباء، مياه، إنترنت)',
          callback_data='bills_menu',
      ),
      InlineKeyboardButton(
          '💳 4. تعبئة الرصيد (MTN / Syriatel)', callback_data='topup_menu'
      ),
      InlineKeyboardButton(
          '🌐 5. خدمات غوغل بلاي', callback_data='google_menu'
      ),
      InlineKeyboardButton(
          '📞 6. تواصل مع فريق الدعم', callback_data='support_menu'
      ),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=welcome_text,
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 1. قسم شحن الألعاب ---
@bot.callback_query_handler(func=lambda call: call.data == 'games_menu')
def games_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          'ببجي: 60 شدة ($1.00)', callback_data='select_PUBG_60_UC_$1.00'
      ),
      InlineKeyboardButton(
          'ببجي: 325 شدة ($5.04)', callback_data='select_PUBG_325_UC_$5.04'
      ),
      InlineKeyboardButton(
          'فري فاير: 100 جوهرة ($1.12)',
          callback_data='select_FreeFire_100_Gems_$1.12',
      ),
      InlineKeyboardButton(
          'كلاش: باقة أساسية ($5.04)', callback_data='select_Clash_Basic_$5.04'
      ),
      InlineKeyboardButton(
          'الجواكر: توكنز ($5.60)', callback_data='select_Jawaker_Tokens_$5.60'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🎮 **اختر اللعبة والباقة المطلوبة (الأسعار شاملة 12% ربح):**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 2. قسم تطبيقات الدردشة ---
@bot.callback_query_handler(func=lambda call: call.data == 'chat_menu')
def chat_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          'بيغو لايف: حزمة أساسية ($5.60)',
          callback_data='select_Bigo_Basic_$5.60',
      ),
      InlineKeyboardButton(
          'السوبو (Soubu): حزمة أساسية ($5.32)',
          callback_data='select_Soubu_Basic_$5.32',
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=(
          '💬 **اختر تطبيق الدردشة المطلوب (الأسعار شاملة 12% ربح):**'
      ),
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 3. قسم دفع الفواتير ---
@bot.callback_query_handler(func=lambda call: call.data == 'bills_menu')
def bills_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '⚡ دفع فاتورة الكهرباء', callback_data='select_Bill_Electricity_Custom'
      ),
      InlineKeyboardButton(
          '💧 دفع فاتورة المياه', callback_data='select_Bill_Water_Custom'
      ),
      InlineKeyboardButton(
          '🌐 دفع فاتورة الإنترنت', callback_data='select_Bill_Internet_Custom'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='📄 **اختر نوع الفاتورة المراد دفعها:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 4. قسم تعبئة الرصيد ---
@bot.callback_query_handler(func=lambda call: call.data == 'topup_menu')
def topup_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          '📱 تعبئة رصيد MTN', callback_data='select_Topup_MTN_Custom'
      ),
      InlineKeyboardButton(
          '📱 تعبئة رصيد Syriatel', callback_data='select_Topup_Syriatel_Custom'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='💳 **اختر شبكة الاتصالات لتعبئة الرصيد:**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 5. قسم خدمات غوغل بلاي ---
@bot.callback_query_handler(func=lambda call: call.data == 'google_menu')
def google_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          'غوغل بلاي: بطاقة 10$ ($11.20)',
          callback_data='select_GooglePlay_10$_$11.20',
      ),
      InlineKeyboardButton(
          'غوغل بلاي: بطاقة 25$ ($28.00)',
          callback_data='select_GooglePlay_25$_$28.00',
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🌐 **اختر فئة بطاقة غوغل بلاي (شاملة 12% ربح):**',
      reply_markup=markup,
      parse_mode='Markdown',
  )


# --- 6. قسم تواصل مع فريق الدعم ---
@bot.callback_query_handler(func=lambda call: call.data == 'support_menu')
def support_menu(call):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'))
  support_text = (
      '📞 **فريق الدعم الفني - ZEUS**\n\n'
      'إذا واجهتك أي مشكلة أو استفسار، يسعدنا تواصلكم معنا عبر الأرقام التالية:\n\n'
      f'📱 `{SUPPORT_NUMBERS}`\n\n'
      'أو مراسلة الإدارة مباشرة.'
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text=support_text,
      reply_markup=markup,
      parse_mode='Markdown',
  )


# خطوة عامة لطلب المعلومات/الآيدي من العميل بناءً على الخدمة المختارة
@bot.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def ask_for_input(call):
  parts = call.data.split('_')
  service = parts[1]
  package = parts[2]
  price = parts[3] if len(parts) > 3 else 'يُحدد لاحقاً'

  msg = bot.send_message(
      call.message.chat.id,
      f'📦 الخدمة المختارة: {service} - {package}\n'
      f'💰 السعر الإجمالي: {price}\n\n'
      f'✍️ **يرجى إرسال رقم الهوية (ID)، رقم الحساب، أو تفاصيل الطلب المطلوبة في رسالة واحدة:**',
      parse_mode='Markdown',
  )
  bot.register_next_step_handler(
      msg, process_user_order, service, f'{package} ({price})'
  )


# استقبال مدخلات العميل، إرسال الإشعار لك، وإرسال الباركود للعميل
def process_user_order(message, service, package_details):
  user_input = message.text
  service_full_name = f'{service} - {package_details}'

  # 1. إرسال إشعار تفصيلي لك على حسابك الشخصي فوراً
  send_order_to_admin(message, service_full_name, package_details, user_input)

  # 2. تجهيز رسالة الدفع وإرسال الباركود ومعلومات المحفظة للعميل
  caption_text = (
      f'✅ **تم تسجيل طلبك بنجاح بواسطة فريق ZEUS!**\n\n'
      f'📦 الخدمة: {service_full_name}\n'
      f'📱 التفاصيل المرسلة: `{user_input}`\n\n'
      f'💳 **يرجى إتمام عملية الدفع عن طريق التحويل إلى محفظة شام كاش التالية:**\n'
      f'رقم المحفظة: `{SHAM_CASH_WALLET}`\n\n'
      f'أو قم بمسح الباركود أعلاه، ثم أرسل إيصال الدفع للإدارة لتنفيذ طلبك فوراً.'
  )

  try:
    with open('sham_cash.jpg', 'rb') as photo:
      bot.send_photo(
          message.chat.id,
          photo,
          caption=caption_text,
          parse_mode='Markdown',
      )
  except Exception as e:
    bot.send_message(
        message.chat.id, caption_text, parse_mode='Markdown'
    )
    print(f'Error sending QR photo: {e}')


if __name__ == '__main__':
  print('Bot is running...')
  bot.infinity_polling()
