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


# دالة إرسال تفاصيل الطلب إلى حسابك الشخصي مباشرة
def send_order_to_admin(message, service_name, amount, user_input):
  user = message.from_user
  notification_text = (
      f'🚨 طلب جديد بانتظار التحويل والتنفيذ!\n\n'
      f'👤 اسم العميل: {user.first_name}\n'
      f'🆔 المعرف: @{user.username if user.username else "لا يوجد"}\n'
      f'🔢 الآيدي: `{user.id}`\n'
      f'📱 الحساب أو الآيدي المدخل: `{user_input}`\n'
      f'📦 الخدمة المطلوبة: {service_name}\n'
      f'💰 السعر الإجمالي (مع ربح 12%): {amount} $\n\n'
      f'👉 بانتظار إتمام العميل للتحويل عبر شام كاش لتنفيذ الطلب.'
  )
  try:
    bot.send_message(ADMIN_ID, notification_text, parse_mode='Markdown')
  except Exception as e:
    print(f'Error sending notification: {e}')


# أمر البدء الأساسي /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
  markup = InlineKeyboardMarkup(row_width=2)
  markup.add(
      InlineKeyboardButton('🎮 الألعاب والخدمات', callback_data='games_menu'),
      InlineKeyboardButton('💳 تعبئة رصيد', callback_data='topup_menu'),
      InlineKeyboardButton('📄 دفع فواتير', callback_data='bills_menu'),
  )
  bot.reply_to(
      message,
      'أهلاً بك في بوت الخدمات الرقمية. يرجى اختيار القسم المطلوب:',
      reply_markup=markup,
  )


# قائمة الألعاب والخدمات مع نسبة 12% ربح مضافة مسبقاً
@bot.callback_query_handler(func=lambda call: call.data == 'games_menu')
def games_menu(call):
  markup = InlineKeyboardMarkup(row_width=2)
  markup.add(
      InlineKeyboardButton(
          'ببجي: 60 شدة ($1.00)', callback_data='select_pubg_60_1.00'
      ),
      InlineKeyboardButton(
          'ببجي: 325 شدة ($5.04)', callback_data='select_pubg_325_5.04'
      ),
      InlineKeyboardButton(
          'فري فاير: 100 جوهرة ($1.12)', callback_data='select_ff_100_1.12'
      ),
      InlineKeyboardButton(
          'كود: 80 نقطة ($1.01)', callback_data='select_cod_80_1.01'
      ),
      InlineKeyboardButton(
          'روبلوكس: 400 روبوكس ($5.04)', callback_data='select_roblox_400_5.04'
      ),
      InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_home'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='🎮 اختر الباقة المطلوبة (الأسعار شاملة 12% ربح):',
      reply_markup=markup,
  )


# زر العودة للقائمة الرئيسية
@bot.callback_query_handler(func=lambda call: call.data == 'back_home')
def back_home(call):
  markup = InlineKeyboardMarkup(row_width=2)
  markup.add(
      InlineKeyboardButton('🎮 الألعاب والخدمات', callback_data='games_menu'),
      InlineKeyboardButton('💳 تعبئة رصيد', callback_data='topup_menu'),
      InlineKeyboardButton('📄 دفع فواتير', callback_data='bills_menu'),
  )
  bot.edit_message_text(
      chat_id=call.message.chat.id,
      message_id=call.message.message_id,
      text='أهلاً بك مجدداً. اختر القسم المطلوب:',
      reply_markup=markup,
  )


# خطوة طلب الآيدي أو رقم الحساب من العميل عند اختيار أي خدمة
@bot.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def ask_for_input(call):
  parts = call.data.split('_')
  service = parts[1]
  package = parts[2]
  price = parts[3]

  msg = bot.send_message(
      call.message.chat.id,
      f'📦 لقد اخترت: {service.upper()} - باقة {package}\n'
      f'💰 السعر الإجمالي: {price} $\n\n'
      f'✍️ **يرجى إرسال رقم الهوية (ID) أو رقم الحساب المراد الشحن إليه في رسالة واحدة:**',
      parse_mode='Markdown',
  )
  # الانتقال لاستقبال رد العميل بالرقم المدخل
  bot.register_next_step_handler(
      msg, process_user_order, service, package, price
  )


# استقبال مدخلات العميل، إرسال الإشعار لك، وإرسال الباركود للعميل
def process_user_order(message, service, package, price):
  user_input = message.text
  service_name = f'{service.upper()} - {package}'

  # 1. إرسال إشعار تفصيلي لك على حسابك الشخصي فوراً
  send_order_to_admin(message, service_name, price, user_input)

  # 2. تجهيز رسالة الدفع وإرسال الباركود ومعلومات المحفظة للعميل
  caption_text = (
      f'✅ **تم تسجيل طلبك بنجاح!**\n\n'
      f'📦 الخدمة: {service_name}\n'
      f'📱 الحساب المرسل: `{user_input}`\n'
      f'💰 المبلغ المطلوب: {price} $\n\n'
      f'💳 **يرجى إتمام عملية الدفع عن طريق التحويل إلى محفظة شام كاش التالية:**\n'
      f'رقم المحفظة: `{SHAM_CASH_WALLET}`\n\n'
      f'أو قم بمسح الباركود أعلاه، ثم أرسل إيصال الدفع للإدارة لتنفيذ طلبك فوراً.'
  )

  try:
    # إرسال الصورة المخزنة في المستودع مع النص
    with open('sham_cash.jpg', 'rb') as photo:
      bot.send_photo(
          message.chat.id,
          photo,
          caption=caption_text,
          parse_mode='Markdown',
      )
  except Exception as e:
    # في حال لم يتم العثور على الصورة، يتم إرسال النص فقط لضمان استمرار عمل البوت
    bot.send_message(
        message.chat.id, caption_text, parse_mode='Markdown'
    )
    print(f'Error sending QR photo: {e}')


if __name__ == '__main__':
  print('Bot is running...')
  bot.infinity_polling()
