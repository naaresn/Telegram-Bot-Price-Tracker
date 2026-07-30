from apscheduler.schedulers.background import BackgroundScheduler
from scraper import parse_price


def check_price(db, bot):
    products = db.get_all_product()

    for product_id, url, name, last_price in products:
        try:
            _, new_price = parse_price(url)
        except Exception as e:
            print(f"[schedulers] failed to scrape {name}: {e}")
            continue

        if new_price != last_price:
            db.update_price(product_id, new_price)
            users = db.get_user(product_id)
            direction = "drop" if new_price < last_price else "increase"

            for user_id in users:
                bot.send_message(user_id, f"The price {direction}!\n{name}\nRp{last_price:,} -> Rp{new_price:,}")

def start_scheduler(db, bot):
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_price, "interval", minutes = 30, args = [db, bot])
    scheduler.start()
    return scheduler

            
