import logging
import os
import sys

import telebot
from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from scheduler import start_scheduler
from scraper import ScrapeError
from storage import Database

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("API_TOKEN")
if not BOT_TOKEN or not BOT_TOKEN.strip():
    logger.error(
        "API_TOKEN kosong atau tidak ada di file .env. "
        "Isi API_TOKEN lalu jalankan ulang bot."
    )
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN.strip())

db = Database()
start_scheduler(db, bot)

menu_commands = [
    telebot.types.BotCommand("/start", "Start using the bot"),
    telebot.types.BotCommand("/track", "Insert product to track the rice"),
    telebot.types.BotCommand("/myitems", "Show your items"),
    telebot.types.BotCommand("/remove", "Remove item"),
]
try:
    bot.set_my_commands(menu_commands)
except Exception as e:
    logger.error("Gagal mengatur menu command: %s", e)


def _reply_error(message, text: str) -> None:
    try:
        bot.reply_to(message, text)
    except Exception as e:
        logger.error("Gagal mengirim pesan error ke user: %s", e)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    try:
        bot.reply_to(message, "Hello! Use /track <url_product> to start tracking.")
    except Exception as e:
        logger.error("Handler /start gagal: %s", e)
        _reply_error(message, "Terjadi kesalahan. Coba lagi nanti.")


@bot.message_handler(commands=["track"])
def send_product(message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "Send: /track [url_product]")
            return

        url = parts[1].strip()
        user_id = message.chat.id
        logger.info("User %s track: %s", user_id, url)
        name, price = db.track(url, user_id)
        bot.reply_to(message, f"Track successfully!\n Name Product:{name}\n Price: Rp{price:,}")
    except ScrapeError as e:
        logger.error("Scraping gagal untuk /track: %s", e)
        _reply_error(message, str(e))
    except PlaywrightTimeoutError:
        logger.error("Timeout saat /track untuk chat %s", message.chat.id)
        _reply_error(
            message,
            "Gagal memuat halaman produk (timeout). Periksa tautan atau coba lagi nanti.",
        )
    except ValueError as e:
        logger.error("Input /track tidak valid: %s", e)
        _reply_error(message, "URL tidak valid. Kirim tautan produk Tokopedia yang lengkap.")
    except Exception as e:
        logger.error("Handler /track gagal: %s", e)
        _reply_error(
            message,
            "Gagal menambahkan produk. Pastikan tautan benar dan produk masih tersedia, lalu coba lagi.",
        )


@bot.message_handler(commands=["myitems"])
def show_list_of_items(message):
    try:
        user_id = message.chat.id
        get_product = db.get_user_product(user_id)

        if not get_product:
            bot.reply_to(message, "You dont have any tracked items yet.")
            return

        list_item = "Your items:\n\n"

        for product_id, url, name, last_price in get_product:
            list_item += f" [{product_id}] - {name} <Rp{last_price:,}>\n"

        bot.reply_to(message, list_item)
    except Exception as e:
        logger.error("Handler /myitems gagal: %s", e)
        _reply_error(message, "Gagal menampilkan daftar produk. Coba lagi nanti.")


@bot.message_handler(commands=["remove"])
def remove_items(message):
    try:
        parts = message.text.split(maxsplit=1)
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
    except Exception as e:
        logger.error("Handler /remove gagal: %s", e)
        _reply_error(message, "Gagal menghapus produk. Coba lagi nanti.")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        bot.reply_to(message, message.text)
    except Exception as e:
        logger.error("Handler echo gagal: %s", e)


logger.info("Bot mulai polling...")
bot.infinity_polling()
