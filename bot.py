import os
import telebot
from storage import Database
from dotenv import load_dotenv
from scheduler import start_scheduler

load_dotenv()

BOT_TOKEN = os.getenv("API_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

db = Database()
start_scheduler(db, bot)

menu_commands = [
    telebot.types.BotCommand("/start", "Start using the bot"),
    telebot.types.BotCommand("/track", "Insert product to track the rice"),
    telebot.types.BotCommand("/myitems", "Show your items"),
    telebot.types.BotCommand("/remove", "Remove item"),
]
bot.set_my_commands(menu_commands)


@bot.message_handler(commands = ["start"])
def send_welcome(message):
    bot.reply_to(message, "Hello! Use /track <url_product> to start tracking.")

@bot.message_handler(commands =["track"])
def send_product(message):
    parts = message.text.split(maxsplit = 1)
    if len(parts) < 2:
        bot.reply_to(message, "Send: /track [url_product]")
        return
    
    url = parts[1]
    user_id = message.chat.id
    name, price = db.track(url, user_id)
    bot.reply_to(message, f"Track successfully!\n Name Product:{name}\n Price: Rp{price:,}")
     
@bot.message_handler(commands = ["myitems"])
def show_list_of_items(message):
    user_id = message.chat.id
    get_product = db.get_user_product(user_id)
    
    if not get_product:
        bot.reply_to(message, "You dont have any tracked items yet.")
        return

    list_item = "Your items:\n\n"

    for product_id, url, name, last_price in get_product:
        list_item += f" [{product_id}] - {name} <Rp{last_price:,}>\n"
    
    bot.reply_to(message, list_item)

@bot.message_handler(commands = ["remove"])
def remove_items(message):
    parts = message.text.split(maxsplit = 1)
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "Use /remove <product_id>")
        return
    
    product_id = int(parts[1])
    user_id = message.chat.id
    removed = db.remove_product(product_id, user_id)

    if removed:
        bot.reply_to(message, "successfully removed the product")

    else:
        bot.reply_to(message, "Product not found in your tracked items")


@bot.message_handler(func = lambda message:True)
def echo_all(message):
    bot.reply_to(message, message.text)

bot.infinity_polling()

