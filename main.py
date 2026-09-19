import os
import telebot

# جلب توكن البوت الذي وضعناه في إعدادات Render تلقائياً
TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)


# أمر الترحيب عند إرسال /start للبوت
@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message, "أهلاً بك! أنا بوت Zues وأعمل الآن 24 ساعة على منصة Render 🚀"
  )


# تشغيل البوت باستمرار
print("Bot is running...")
bot.infinity_polling()
