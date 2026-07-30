from playwright.sync_api import sync_playwright


def block_resource(route, request) -> None:
    blocked_types = ["image", "stylesheet", "font", "media"]

    if request.resource_type in blocked_types:
        route.abort()
    else:
        route.continue_()  

def scraping(url: str) -> tuple:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless = False)
        page = browser.new_page()
        page.route("**/*", block_resource)
        page.goto(url)
        
        xpath_name = 'xpath= //*[@id="pdp_comp-product_content"]/div/div[1]/h1 '
        xpath_price = 'xpath= //*[@id="pdp_comp-product_content"]/div/div[3]/div'
        
        name_element = page.locator(xpath_name).first
        price_element = page.locator(xpath_price).first
        
        name_element.wait_for(state = "visible")

        name = name_element.inner_text() if name_element.count() > 0 else "-"
        price = price_element.inner_text() if price_element.count() > 0 else"-"
    
        browser.close()
        #print(f"{name}")
        #print(f"{price}")
        return name, price
                    
def parse_price(url: str) -> tuple:
    name, price =  scraping(url)
    clean_price = price.replace("Rp", "").replace(".", "").strip()
    return name, int(clean_price)

