# Tokopedia Price Tracker Bot

Telegram bot that tracks product prices on Tokopedia and notifies you when the price changes. 

## What it does

<img width="300" height="auto" alt="Preview Bot (2)" src="https://github.com/user-attachments/assets/16a3fb79-5b19-472a-8e30-61496a71dc5b" />



Send the bot a Tokopedia product URL, it keeps an eye on the price in the background, and pings you the moment it goes up or down. 

**Features:**

- **Track any product** — send `/track <url>` and the bot scrapes the current price and starts monitoring that product
- **View your tracked items** — `/myitems` shows everything you're currently tracking, with the last known price
- **Remove items** — `/remove <id>` stops tracking a product you're no longer interested in
- **Automatic price alerts** — a background scheduler re-checks all tracked products periodically and notifies you as soon the price changes (up or down)
- **Price history** — every price check is logged, so there's a running history of how a product's price has moved over time
- **Multi-user support** — multiple people can track the same product independently; tracking and removing items is scoped per-user

## How it works 


<img width="843" height="265" alt="image" src="https://github.com/user-attachments/assets/1a9dbaff-178a-46b2-984b-eef59ac345bc" />


- **`bot.py`** — the entry point. Receives Telegram commands (`/track`, `/myitems`, `/remove`) and replies to users.
- **`scraper.py`** — uses Playwright to open a product page, wait for the relevant elements, and get the product name and price.
- **`storage.py`** — a `Database` class wrapping SQLite. Handles saving products, linking them to the user who's tracking them, and recording price history.
- **`scheduler.py`** — runs in the background (via APScheduler) and periodically re-scrapes every tracked product, updating prices and firing off notifications when something changes.

## Commands

| Command | What it does |
|---|---|
| `/start` | Start the bot |
| `/track <url>` | Starts tracking a product from its Tokopedia URL |
| `/myitems` | Lists all products you're currently tracking |
| `/remove <id>` | Stops tracking a specific product (see the id in `/myitems`) |

## Tools

- **Python**
- **Playwright** — headless browser automation for scraping
- **pyTelegramBotAPI (`telebot`)** — Telegram bot interface
- **SQLite** — lightweight local storage
- **APScheduler** — background job scheduling for periodic price checks

## Setup

1. Clone the repo and install dependencies:
   ```bash
   pip install pyTelegramBotAPI playwright apscheduler python-dotenv
   playwright install chromium
   ```
2. Create a `.env` file in the project root with your bot token:
   ```
   API_TOKEN=your_telegram_bot_token_here
   ```
3. Run the bot:
   ```bash
   python bot.py
   ```

## Known limitations

- Currently scoped to Tokopedia product pages (relies on Tokopedia's page structure via XPath selectors, so it may break if their layout changes)
- No custom check interval yet — all tracked products are checked on the same fixed schedule
- Removing a product only removes *your* tracking of it; if other users are tracking the same product, it stays in the system for them
