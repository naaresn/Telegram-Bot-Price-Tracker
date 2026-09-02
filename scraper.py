import logging
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3
GOTO_TIMEOUT_MS = 30_000
WAIT_TIMEOUT_MS = 15_000

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-infobars",
    "--disable-extensions",
    "--disable-gpu",
    "--window-size=1920,1080",
]


class ScrapeError(Exception):
    """Raised when a product page cannot be scraped."""


def block_resource(route, request) -> None:
    blocked_types = ["image", "stylesheet", "font", "media"]

    if request.resource_type in blocked_types:
        route.abort()
    else:
        route.continue_()


def _validate_url(url: str) -> None:
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ScrapeError("URL tidak valid. Kirim tautan produk yang lengkap (diawali http/https).")
    if "tokopedia.com" not in url.lower():
        raise ScrapeError("Hanya tautan produk Tokopedia yang didukung.")


def _scrape_once(url: str) -> tuple:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=LAUNCH_ARGS)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            locale="id-ID",
            extra_http_headers={"Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"},
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page.route("**/*", block_resource)

        try:
            page.goto(url, timeout=GOTO_TIMEOUT_MS, wait_until="domcontentloaded")

            xpath_name = 'xpath= //*[@id="pdp_comp-product_content"]/div/div[1]/h1 '
            xpath_price = 'xpath= //*[@id="pdp_comp-product_content"]/div/div[3]/div'

            name_element = page.locator(xpath_name).first
            price_element = page.locator(xpath_price).first

            name_element.wait_for(state="visible", timeout=WAIT_TIMEOUT_MS)

            if name_element.count() == 0:
                raise ScrapeError(
                    "Produk tidak ditemukan. Mungkin sudah dihapus, habis, atau tautannya salah."
                )

            name = name_element.inner_text()
            price = price_element.inner_text() if price_element.count() > 0 else "-"

            if not price or price.strip() == "-":
                raise ScrapeError(
                    "Harga produk tidak ditemukan. Produk mungkin habis atau halaman berubah."
                )

            logger.info("Berhasil scrape: %s", name)
            return name, price
        finally:
            context.close()
            browser.close()


def scraping(url: str) -> tuple:
    _validate_url(url)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Scraping %s (percobaan %s/%s)", url, attempt, MAX_RETRIES)
            return _scrape_once(url)
        except ScrapeError:
            raise
        except PlaywrightTimeoutError as e:
            last_error = e
            logger.error(
                "Timeout saat scrape %s (percobaan %s/%s): %s",
                url,
                attempt,
                MAX_RETRIES,
                e,
            )
        except Exception as e:
            last_error = e
            logger.error(
                "Gagal scrape %s (percobaan %s/%s): %s",
                url,
                attempt,
                MAX_RETRIES,
                e,
            )

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)

    raise ScrapeError(
        "Gagal memuat halaman produk setelah beberapa percobaan. Coba lagi nanti."
    ) from last_error


def parse_price(url: str) -> tuple:
    name, price = scraping(url)
    clean_price = price.replace("Rp", "").replace(".", "").replace(",", "").strip()
    digits = "".join(ch for ch in clean_price if ch.isdigit())
    if not digits:
        raise ScrapeError(
            "Harga produk tidak bisa dibaca. Produk mungkin habis atau halaman berubah."
        )
    return name, int(digits)
