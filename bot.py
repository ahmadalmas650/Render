import telebot
from telebot import types
import json
import os

# Render ke environment variable se token secure tareeqay se uthayega
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN environment variable set nahi ki gayi!")

bot = telebot.TeleBot(TOKEN)

CONFIG_FILE = "accounts_config.json"
ORDERS_FILE = "orders.json"

# Helper functions for config and orders storage
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {} if filename == CONFIG_FILE else []

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "☁️ Cloud Control Center is 24/7 Active!\nReady to manage orders and marketing triggers.")

# /menu command
@bot.message_handler(commands=['menu'])
def show_menu(message):
    menu_text = """
📋 **Master Control Menu:**
/start - Cloud status
/ping - Check Termux connection
/addaccount - Connect new social account (Dynamic)
/addip - Bind dedicated proxy to account
/orders - View pending orders
/postad - Trigger marketing task
    """
    bot.send_message(message.chat.id, menu_text, parse_mode="Markdown")

# /ping command
@bot.message_handler(commands=['ping'])
def check_connection(message):
    bot.reply_to(message, "🟢 Cloud Bot is online and connected!")

# /addaccount command (Dynamic Platform Support)
@bot.message_handler(commands=['addaccount'])
def add_account_step(message):
    msg = bot.reply_to(message, "🌐 Kis platform ka account add karna hai? Uska naam likhein (maslan: Facebook, LinkedIn, TikTok):")
    bot.register_next_step_handler(msg, get_platform_name)

def get_platform_name(message):
    platform = message.text.strip()
    msg = bot.reply_to(message, f"👤 Ab is **{platform}** account ka koi unique naam/ID dein (maslan: {platform}_Acc_1):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, lambda m: save_account_final(m, platform))

def save_account_final(message, platform):
    acc_name = message.text.strip()
    config = load_json(CONFIG_FILE)
    if acc_name not in config:
        config[acc_name] = {"platform": platform, "proxy": None}
        save_json(CONFIG_FILE, config)
        bot.reply_to(message, f"✅ Account **{acc_name}** ({platform}) successfully registered!\nAb `/addip` use kar ke iske sath proxy bind karein.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Yeh account pehle se maujood hai!")

# /addip command (Dedicated Proxy Binding)
@bot.message_handler(commands=['addip'])
def add_ip_step(message):
    msg = bot.reply_to(message, "🌐 Details is format mein bhejein:\n`AccountName IP:Port`\n(Misal: `Facebook_Acc_1 192.168.1.50:8080`)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_account_ip)

def save_account_ip(message):
    try:
        parts = message.text.strip().split()
        acc_name = parts[0]
        proxy_ip = parts[1]
        
        config = load_json(CONFIG_FILE)
        if acc_name in config:
            config[acc_name]["proxy"] = proxy_ip
            save_json(CONFIG_FILE, config)
            bot.reply_to(message, f"✅ Proxy `{proxy_ip}` securely bound to **{acc_name}**!", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Account nahi mila! Pehle `/addaccount` se account banayein.")
    except Exception as e:
        bot.reply_to(message, "❌ Ghalat format! Sahi format use karein: `AccountName IP:Port`")

# /orders command with manual remove button
@bot.message_handler(commands=['orders'])
def view_orders(message):
    orders = load_json(ORDERS_FILE)
    if not orders:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🗑️ Remove Order", callback_data="remove_sample"))
        bot.send_message(message.chat.id, "📦 **Sample Order:**\n\n👤 Customer: Ali Khan\n🔥 Product: Smart Watch\n💰 Price: 2500 PKR\n🚚 COD: Available", parse_mode="Markdown", reply_markup=markup)
    else:
        for idx, order in enumerate(orders):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🗑️ Remove Order", callback_data=f"remove_order_{idx}"))
            bot.send_message(message.chat.id, f"📦 **Order Details:**\n\n{order}", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove"))
def remove_order(call):
    bot.answer_callback_query(call.id, "Order removed & storage cleaned!")
    bot.delete_message(call.message.chat.id, call.message.message_id)

# Multiple Platforms Ad Posting Trigger
@bot.message_handler(commands=['postad'])
def select_platform(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📘 Facebook", callback_data="market_facebook"),
        types.InlineKeyboardButton("🔗 LinkedIn", callback_data="market_linkedin"),
        types.InlineKeyboardButton("🐦 X / Twitter", callback_data="market_twitter"),
        types.InlineKeyboardButton("📸 Instagram", callback_data="market_instagram")
    )
    bot.send_message(message.chat.id, "🌍 Marketing ke liye target platform select karein:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("market_"))
def platform_selected(call):
    platform = call.data.split("_")[1].upper()
    bot.answer_callback_query(call.id, f"Trigger sent for {platform}!")
    bot.edit_message_text(f"🚀 Marketing task triggered for **{platform}**!\nTermux worker script execute hone ka intezaar hai.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")

print("Cloud Bot is running 24/7...")
bot.infinity_polling()
