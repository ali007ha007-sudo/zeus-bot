from telebot import types


def main_menu():
  markup = types.InlineKeyboardMarkup(row_width=2)

  # الأزرار السابقة (أمثلة)
  btn_games = types.InlineKeyboardButton("🎮 شحن ألعاب", callback_data="games")

  # الزر الجديد الخاص بـ Taka Live
  btn_taka = types.InlineKeyboardButton(
      "🎙️ Taka Live (قريباً)", callback_data="taka_soon"
  )

  markup.add(btn_games, btn_taka)
  return markup
