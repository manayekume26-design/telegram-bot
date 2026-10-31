import os
import random
import sqlite3
import telebot
from telebot import types

# ----------------- CONFIGURATION -----------------
TOKEN = "9058831731:AAFie2bn78u_hiHq8iQA7xCHWOzLA4V18rM"  # የቦቱን ቶከን እዚህ ያስገቡ
ADMIN_ID = 6979095464  # የእርስዎን የቴሌግራም ዩዘር ID እዚህ ያስገቡ (አድሚን ለመሆን)

bot = telebot.TeleBot(TOKEN)


# ----------------- DATABASE SETUP -----------------
def init_db():
  conn = sqlite3.connect("lottery.db")
  cursor = conn.cursor()

  # ተሳታፊዎች
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            phone TEXT,
            department TEXT,
            year TEXT,
            campus TEXT,
            ticket_number INTEGER,
            round_number INTEGER
        )
    """)

  # ቅንብሮች (Admin Settings) - የዕጣ ዝርዝር፣ ቀን እና አሸናፊ
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

  # ነባሪ (Default) መረጃዎችን ማስገባት
  cursor.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('round', '1')"
  )
  cursor.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('prizes',"
      " 'እስካሁን አልተዘመኑም')"
  )
  cursor.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('draw_date',"
      " 'ገና አልተወሰነም')"
  )
  cursor.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('winners',"
      " 'ገና አልወጡም')"
  )

  conn.commit()
  conn.close()


init_db()


# የዳታቤዝ ረዳት ፋንክሽኖች
def get_setting(key):
  conn = sqlite3.connect("lottery.db")
  cursor = conn.cursor()
  cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
  val = cursor.fetchone()
  conn.close()
  return val[0] if val else ""


def update_setting(key, value):
  conn = sqlite3.connect("lottery.db")
  cursor = conn.cursor()
  cursor.execute(
      "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
  )
  conn.commit()
  conn.close()


# ----------------- USER REGISTRATION STATES -----------------
user_data = {}


@bot.message_handler(commands=['start'])
def start(message):
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      types.KeyboardButton('🎟️ ራዕይ/ይመዝገቡ (Register)'),
      types.KeyboardButton('🎁 የዕጣ ዝርዝር (Prizes)'),
  )
  markup.add(
      types.KeyboardButton('📅 የዕጣ ቀን (Draw Date)'),
      types.KeyboardButton('🏆 አሸናፊዎች (Winners)'),
  )

  if message.from_user.id == ADMIN_ID:
    markup.add(types.KeyboardButton('🛠️ Admin Panel'))

  bot.send_message(
      message.chat.id,
      'ሰላም! እንኳን ወደ ዕጣ ጨዋታ ቦት በደህና መጡ። ከታች ያሉትን አማራጮች ይጠቀሙ፦',
      reply_markup=markup,
  )


# --- Handle Main Menu Clicks ---
@bot.message_handler(
    func=lambda msg: msg.text
    in [
        '🎟️ ራዕይ/ይመዝገቡ (Register)',
        '🎁 የዕጣ ዝርዝር (Prizes)',
        '📅 የዕጣ ቀን (Draw Date)',
        '🏆 አሸናፊዎች (Winners)',
        '🛠️ Admin Panel',
    ]
)
def handle_menu(message):
  if message.text == '🎟️ ራዕይ/ይመዝገቡ (Register)':
    user_data[message.from_user.id] = {}
    msg = bot.send_message(
        message.chat.id,
        'እባክዎን ሙሉ ስምዎን (First & Last Name) ያስገቡ:',
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(msg, process_name)

  elif message.text == '🎁 የዕጣ ዝርዝር (Prizes)':
    prizes = get_setting('prizes')
    bot.send_message(
        message.chat.id, f'🎁 **የአሁኑ ዙር የዕጣ ዝርዝሮች፦**\n\n{prizes}', parse_mode='Markdown'
    )

  elif message.text == '📅 የዕጣ ቀን (Draw Date)':
    date_val = get_setting('draw_date')
    bot.send_message(
        message.chat.id,
        f'📅 **ዕጣ የሚወጣበት ቀን፦**\n\n{date_val}',
        parse_mode='Markdown',
    )

  elif message.text == '🏆 አሸናፊዎች (Winners)':
    winners = get_setting('winners')
    bot.send_message(
        message.chat.id,
        f'🏆 **የዚህ ዙር አሸናፊዎች፦**\n\n{winners}',
        parse_mode='Markdown',
    )

  elif message.text == '🛠️ Admin Panel':
    if message.from_user.id != ADMIN_ID:
      bot.send_message(message.chat.id, 'ይህንን ትዕዛዝ መጠቀም የሚችሉት አድሚኖች ብቻ ናቸው።')
      return

    admin_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    admin_markup.add(
        types.KeyboardButton('✏️ ሽልማት ቀይር'),
        types.KeyboardButton('✏️ የዕጣ ቀን ቀይር'),
    )
    admin_markup.add(
        types.KeyboardButton('✏️ አሸናፊዎችን ቀይር'),
        types.KeyboardButton('🔄 አዲስ ዙር ጀምር'),
    )
    admin_markup.add(
        types.KeyboardButton('📊 ተሳታፊዎችን አሳይ'),
        types.KeyboardButton('🏠 ዋና ምናሌ'),
    )
    bot.send_message(
        message.chat.id,
        'ወደ አድሚን ፓነል ገብተዋል፦ የሚፈልጉትን ትዕዛዝ ይምረጡ።',
        reply_markup=admin_markup,
    )


# ----------------- REGISTRATION FLOW -----------------
def process_name(message):
  user_data[message.from_user.id]['full_name'] = message.text
  msg = bot.send_message(message.chat.id, 'ስልክ ቁጥርዎን ያስገቡ (ለምሳሌ፦ 0911223344):')
  bot.register_next_step_handler(msg, process_phone)


def process_phone(message):
  user_data[message.from_user.id]['phone'] = message.text
  msg = bot.send_message(message.chat.id, 'የሚማሩበትን Department ያስገቡ:')
  bot.register_next_step_handler(msg, process_dept)


def process_dept(message):
  user_data[message.from_user.id]['department'] = message.text
  msg = bot.send_message(message.chat.id, 'የዕዝ/የትምህርት ዘመንዎን (Year) ያስገቡ:')
  bot.register_next_step_handler(msg, process_year)


def process_year(message):
  user_data[message.from_user.id]['year'] = message.text

  # Campus Selection Buttons
  campus_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  for c in ['Tecno', 'Main', 'Agri', 'Referal', 'Other']:
    campus_markup.add(types.KeyboardButton(c))

  msg = bot.send_message(
      message.chat.id,
      'የሚማሩበትን ግቢ (Campus) ከታች ካሉት ይምረጡ:',
      reply_markup=campus_markup,
  )
  bot.register_next_step_handler(msg, process_campus)


def process_campus(message):
  user_id = message.from_user.id
  user_data[user_id]['campus'] = message.text

  # Get current round
  current_round = int(get_setting('round'))

  # Generate unique ticket number per round
  conn = sqlite3.connect("lottery.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT MAX(ticket_number) FROM participants WHERE round_number = ?",
      (current_round,),
  )
  max_ticket = cursor.fetchone()[0]
  new_ticket = 1 if max_ticket is None else max_ticket + 1

  # Save to DB
  data = user_data[user_id]
  cursor.execute(
      """
        INSERT INTO participants (user_id, full_name, phone, department, year, campus, ticket_number, round_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
      (
          user_id,
          data['full_name'],
          data['phone'],
          data['department'],
          data['year'],
          data['campus'],
          new_ticket,
          current_round,
      ),
  )
  conn.commit()
  conn.close()

  # Confirmation message
  success_msg = (
      f'✅ **በሳካ ሁኔታ ተመዝግበዋል!**\n\n'
      f"👤 ስም: {data['full_name']}\n"
      f"📞 ስልክ: {data['phone']}\n"
      f"📚 Department: {data['department']}\n"
      f"🎓 Year: {data['year']}\n"
      f"🏫 Campus: {data['campus']}\n"
      f'🔄 ዙር: {current_round}\n'
      f'🎟️ **የቲኬት ቁጥርዎ: #{new_ticket}**\n\n'
      f'መልካም እድል! 🍀'
  )

  # Restore Main Menu
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      types.KeyboardButton('🎟️ ራዕይ/ይመዝገቡ (Register)'),
      types.KeyboardButton('🎁 የዕጣ ዝርዝር (Prizes)'),
  )
  markup.add(
      types.KeyboardButton('📅 የዕጣ ቀን (Draw Date)'),
      types.KeyboardButton('🏆 አሸናፊዎች (Winners)'),
  )
  if user_id == ADMIN_ID:
    markup.add(types.KeyboardButton('🛠️ Admin Panel'))

  bot.send_message(message.chat.id, success_msg, parse_mode='Markdown', reply_markup=markup)


# ----------------- ADMIN PANEL HANDLERS -----------------
@bot.message_handler(
    func=lambda msg: msg.text
    in [
        '✏️ ሽልማት ቀይር',
        '✏️ የዕጣ ቀን ቀይር',
        '✏️ አሸናፊዎችን ቀይር',
        '🔄 አዲስ ዙር ጀምር',
        '📊 ተሳታፊዎችን አሳይ',
        '🏠 ዋና ምናሌ',
    ]
)
def admin_actions(message):
  if message.from_user.id != ADMIN_ID:
    return

  if message.text == '✏️ ሽልማት ቀይር':
    msg = bot.send_message(
        message.chat.id,
        'አዲሱን የሽልማት ዝርዝር ጽሁፍ ልኩ (Markdown መጠቀም ይችላሉ):',
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(msg, save_prizes)

  elif message.text == '✏️ የዕጣ ቀን ቀይር':
    msg = bot.send_message(
        message.chat.id,
        'አዲሱን የዕጣ ቀን እና ሰዓት ልኩ:',
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(msg, save_draw_date)

  elif message.text == '✏️ አሸናፊዎችን ቀይር':
    msg = bot.send_message(
        message.chat.id,
        'የአዲሱን ዙር አሸናፊዎች ስም እና ዝርዝር ልኩ:',
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(msg, save_winners)

  elif message.text == '🔄 አዲስ ዙር ጀምር':
    current_round = int(get_setting('round'))
    new_round = current_round + 1
    update_setting('round', str(new_round))
    bot.send_message(
        message.chat.id,
        f'🔄 አዲስ ዙር (ዙር {new_round}) ተጀምሯል! የቲኬት ቁጥሮች ከ 1 ተጀምረዋል።',
    )

  elif message.text == '📊 ተሳታፊዎችን አሳይ':
    conn = sqlite3.connect("lottery.db")
    cursor = conn.cursor()
    cursor.execute(
        'SELECT full_name, phone, campus, ticket_number, round_number FROM'
        ' participants'
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
      bot.send_message(message.chat.id, 'እስካሁን የተመዘገበ ተሳታፊ የለም።')
      return

    text = '📊 **የተሳታፊዎች ዝርዝር፦**\n\n'
    for r in rows:
      text += (
          f'• {r[0]} | {r[1]} | {r[2]} | ዙር {r[4]} | 🎫 ቲኬት: **#{r[3]}**\n'
      )

    # ቴሌግራም የሜሴጅ ገደብ ስላለው ከረዘመ በክፍል እንልካለን
    if len(text) > 4000:
      for x in range(0, len(text), 4000):
        bot.send_message(
            message.chat.id, text[x : x + 4000], parse_mode='Markdown'
        )
    else:
      bot.send_message(message.chat.id, text, parse_mode='Markdown')

  elif message.text == '🏠 ዋና ምናሌ':
    start(message)


def save_prizes(message):
  update_setting('prizes', message.text)
  bot.send_message(message.chat.id, '✅ የሽልማት ዝርዝር በተሳካ ሁኔታ ተቀይሯል!')
  admin_panel_return(message)


def save_draw_date(message):
  update_setting('draw_date', message.text)
  bot.send_message(message.chat.id, '✅ የዕጣ ቀን በተሳካ ሁኔታ ተቀይሯል!')
  admin_panel_return(message)


def save_winners(message):
  update_setting('winners', message.text)
  bot.send_message(message.chat.id, '✅ የአሸናፊዎች ዝርዝር በተሳካ ሁኔታ ተቀይሯል!')
  admin_panel_return(message)


def admin_panel_return(message):
  admin_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  admin_markup.add(
      types.KeyboardButton('✏️ ሽልማት ቀይር'),
      types.KeyboardButton('✏️ የዕጣ ቀን ቀይር'),
  )
  admin_markup.add(
      types.KeyboardButton('✏️ አሸናፊዎችን ቀይር'),
      types.KeyboardButton('🔄 አዲስ ዙር ጀምር'),
  )
  admin_markup.add(
      types.KeyboardButton('📊 ተሳታፊዎችን አሳይ'),
      types.KeyboardButton('🏠 ዋና ምናሌ'),
  )
  bot.send_message(
      message.chat.id, 'ወደ አድሚን ፓነል ተመልሰዋል፦', reply_markup=admin_markup
  )


# ----------------- RUN BOT -----------------
if __name__ == '__main__':
  print('Bot is running...')
  bot.infinity_polling()
  from flask import Flask
import os
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ዌብ ሰርቨሩን ከቦቱ ጋር በአንድ ላይ ለማስኬድ (Background thread)
threading.Thread(target=run_web).start()

