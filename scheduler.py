import logging

from apscheduler.schedulers.background import BackgroundScheduler

from scraper import parse_price

logger = logging.getLogger(__name__)


def check_price(db, bot):
    try:
        products = db.get_all_product()
    except Exception as e:
        logger.error("Gagal mengambil daftar produk: %s", e)
        return

    logger.info("Cek harga untuk %s produk", len(products))

    for product_id, url, name, last_price in products:
        try:
            _, new_price = parse_price(url)

            if new_price != last_price:
                db.update_price(product_id, new_price)
                users = db.get_user(product_id)
                direction = "drop" if new_price < last_price else "increase"
                logger.info(
                    "Harga %s berubah: Rp%s -> Rp%s",
                    name,
                    last_price,
                    new_price,
                )

                for user_id in users:
                    try:
                        bot.send_message(
                            user_id,
                            f"The price {direction}!\n{name}\nRp{last_price:,} -> Rp{new_price:,}",
                        )
                    except Exception as send_err:
                        logger.error(
                            "Gagal kirim notifikasi ke user %s untuk produk %s: %s",
                            user_id,
                            name,
                            send_err,
                        )
        except Exception as e:
            logger.error("Gagal scrape %s (%s): %s", name, url, e)
            continue


def start_scheduler(db, bot):
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_price, "interval", minutes=30, args=[db, bot])
    scheduler.start()
    logger.info("Scheduler dimulai (interval 30 menit)")
    return scheduler
