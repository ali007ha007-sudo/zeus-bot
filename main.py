import os
import threading
import telebot
from flask import Flask
from telebot import types

# --- إعدادات البوت والـ Flask ---
TOKEN = "YOUR_BOT_TOKEN_HERE"  # ضع توكن البوت الخاص بك هنا
ADMIN_ID = 123456789  # ضع آيدي الأدمن هنا

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is running 24/7!"


def run_flask():
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)


# --- القائمة الرئيسية ---
def main_menu():
  markup = types.InlineKeyboardMarkup(row_width=2)
  btn_games = types.InlineKeyboardButton("🎮 شحن ألعاب", callback_data="games")
  btn_taka = types.InlineKeyboardButton(
      "🎙️ Taka Live (قريباً)", callback_data="taka_soon"
  )
  btn_other = types.InlineKeyboardButton(
      "💎 خدمات أخرى", callback_data="other_services"
  )
  markup.add(btn_games, btn_taka, btn_other)
  return markup


# --- أمر البداية /start ---
@bot.message_handler(commands=["start"])
def send_welcome(message):
  text = """
مرحباً بك في بوت الخدمات والدفع الإلكتروني 🌟
يرجى اختيار القسم المناسب من القائمة أدناه:
    """
  bot.send_message(
      message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu()
  )


# --- معالج قسم Taka Live (قريباً) ---
@bot.callback_query_handler(func=lambda call: call.data == "taka_soon")
def taka_coming_soon(call):
  bot.answer_callback_query(call.id)
  text = """
🎙️ **قسم شحن وتعبئة Taka Live**
━━━━━━━━━━━━━━━━━━━
🚀 **قريباً جداً - Coming Soon!**

نعمل حالياً على تجهيز خدمات شحن العملات والجواهر الخاصة بتطبيق **Taka** للبث المباشر والدردشة الصوتية لتكون متوفرة بأفضل الأسعار وسرعة تنفيذ عالية.

⏳ ترقبوا إطلاق الخدمة رسمياً خلال الفترة القادمة!
    """
  markup = types.InlineKeyboardMarkup()
  btn_back = types.InlineKeyboardButton(
      "🔙 العودة للقائمة الرئيسية", callback_data="back_to_main"
  )
  markup.add(btn_back)

  bot.edit_message_text(
      text=text,
      chat_id=call.message.chat.id,
      message_id=call.message.message.id,
      parse_mode="Markdown",
      reply_markup=markup,
  )


# --- زر العودة للقائمة الرئيسية ---
@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
  bot.answer_callback_query(call.id)
  text = """
مرحباً بك مرة أخرى في القائمة الرئيسية 🌟
يرجى اختيار القسم المناسب:
    """
  bot.edit_message_text(
      text=text,
      chat_id=call.message.chat.id,
      message_id=call.message.message.id,
      parse_mode="Markdown",
      reply_markup=main_menu(),
  )


# --- معالج الأقسام الأخرى كمثال ---
@bot.callback_query_handler(
    func=lambda call: call.data in ["games", "other_services"]
)
def other_sections(call):
  bot.answer_callback_query(call.id)
  section_name = "شحن الألعاب" if call.data == "games" else "خدمات أخرى"
  text = f"""
🎮 **{section_name}**
هذا القسم قيد التشغيل حالياً. يمكنك إضافة تفاصيلك هنا.
    """
  markup = types.InlineKeyboardMarkup()
  btn_back = types.InlineKeyboardButton(
      "🔙 العودة للقائمة الرئيسية", callback_data="back_to_main"
  )
  markup.add(btn_back)

  bot.edit_message_text(
      text=text,
      chat_id=call.message.chat.id,
      message_id=call.message.message.id,
      parse_mode="Markdown",
      reply_markup=markup,
  )


# --- تشغيل Flask والبوت معاً ---
if __name__ == "__main__":
  # تشغيل خادم الويب في خيط منفصل للاستضافة (Render 24/7)
  t = threading.Thread(target=run_flask)
  t.daemon = True
  t.start()

  print("Bot is running...")
  bot.infinity_polling()
