from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urlparse
import requests
import sys
import time
import lxml

''' ------------------------------ SETTINGS ------------------------------ '''

# Mode: Choose 'url' or 'keyword'
MODE = 'url'  # 'url' = direct product link, 'keyword' = search by keywords

# Direct URL Mode Settings (if MODE = 'url')
PRODUCT_URL = 'https://saicstore.myshopify.com/products/saic-water-bottle'

# Keyword Search Mode Settings (if MODE = 'keyword')
WEBSITE = 'kith.com'  # Domain name only (e.g., kith.com, deadstock.ca)
KEYWORD1 = 'adidas'
KEYWORD2 = 'yeezy'
KEYWORD3 = ''  # Optional
KEYWORD4 = ''  # Optional
KEYWORD5 = ''  # Optional
KEYWORD6 = ''  # Optional

# Purchase Settings
AUTO_BUY = True  # Set to False to only check stock without buying
SIZE = ''  # Size you want to purchase (set to '' to use first available)
USE_FIRST_AVAILABLE = True  # If SIZE not found, use first available size
QUANTITY = '1'  # Quantity to purchase

# Display Settings
SHOW_STOCK_INFO = True  # Show detailed stock information

# Autofill Settings
AUTOFILL_CHECKOUT = True  # Automatically fill checkout fields
AUTOFILL_DELAY = 0 # Seconds to wait for page loads

# Customer Information for Autofill
EMAIL = 'gooncube@gmail.com'
FIRST_NAME = 'John'
LAST_NAME = 'Doe'
ADDRESS1 = '123 Test Street'
ADDRESS2 = 'Apt 4B'
CITY = 'Los Angeles'
STATE = 'California'
ZIP_CODE = '90210'
COUNTRY = 'United States'
PHONE = '9178349732'

# Payment Information for Autofill
CARD_NUMBER = '4242424242424242'  # Stripe test card
CARDHOLDER_NAME = 'John Doe'
EXP_MONTH = '12'
EXP_YEAR = '25'
CVV = '123'


def getTime():
    return time.strftime('|%D | %H:%M:%S|')

def getURL():
    global URL
    print('___________________________________________________________________________________________________________________________________________________________')
    print('')
    print(getTime())
    print('')

    if MODE == 'url':
        URL = PRODUCT_URL
        if '?' in URL:
            URL, y, z = URL.partition('?')
        print(f'Using direct URL: {URL}')

    elif MODE == 'keyword':
        print(f'Searching on {WEBSITE} for product with keywords...')
        print(f'Keywords: {KEYWORD1}, {KEYWORD2}, {KEYWORD3}, {KEYWORD4}, {KEYWORD5}, {KEYWORD6}')

        s = requests.Session()
        f = s.get(f'https://{WEBSITE}/sitemap_products_1.xml')
        soup1 = BeautifulSoup(f.text, 'lxml')
        products = soup1.find_all('url')

        for url in products:
            if KEYWORD1 in url.get_text():
                URL = (url.find('loc').text)
                if KEYWORD2.lower() in URL:
                    if not KEYWORD3 or KEYWORD3.lower() in URL:
                        if not KEYWORD4 or KEYWORD4.lower() in URL:
                            if not KEYWORD5 or KEYWORD5.lower() in URL:
                                if not KEYWORD6 or KEYWORD6.lower() in URL:
                                    print('')
                                    print(f'Product found: {URL}')
                                    return URL

        print('No product found matching all keywords!')
        sys.exit()

    return URL

def getSoup():
    global soup
    s = requests.Session()
    r = s.get(URL + '.xml')
    soup = BeautifulSoup(r.text, 'lxml')
    return soup

def getItem():
    global item
    item = soup.find('title').text

def getSize():
    global sz
    sz = list()
    for size in soup.find_all('title')[1:]:
        sz.append(size.get_text())
    return sz

def getStock():
    global stk
    stk = list()
    for stock in soup.find_all('inventory-quantity'):
        stk.append(stock.get_text())
    return stk

def getPrice():
    global prc
    prc = list()
    for price in soup.find_all('price'):
        prc.append(price.get_text())
    return prc

def getVariants():
    global vrnt
    vrnt = list()
    for variants in soup.find_all('product-id'):
        vrnt.append(variants.find_previous('id').get_text())
    return vrnt

def getTotal():
    global ttl
    ttl = list()
    for stocktotal in soup.findAll("inventory-quantity"):
        ttl.append(int(stocktotal.text))
    return ttl

# Get all product data
getURL()
getSoup()
getItem()
getSize()
getStock()
getPrice()
getVariants()
getTotal()

def formatData():
    print('')
    print(item)

    if len(stk) > 0:
        print('{:<5} | {:<20} | {:<10} | {:10} | {:20} '.format('', 'size', 'stock', 'price', 'variants'))
        for i, (size, stock, price, variant) in enumerate(zip(sz, stk, prc, vrnt)):
            print('{:<5} | {:<20} | {:<10} | {:10} | {:20} '.format(i, size, stock, '$' + price, variant))

        if sum(ttl) == 0:
            print('Sold out!')
        elif sum(ttl) != 0:
            print('Total stock: {:<5}'.format(sum(ttl)))
    else:
        print('STOCK: ')
        print('{:<5} | {:<20} | {:10} | {:20} '.format('', 'size', 'price', 'variants'))
        for i, (size, price, variant) in enumerate(zip(sz, prc, vrnt)):
            print('{:<5} | {:<20} | {:10} | {:20} '.format(i, size, '$' + price, variant))

if SHOW_STOCK_INFO:
    formatData()

def fill_input(driver, field_id=None, field_name=None, value=''):
    """Helper function to fill input fields - fast version"""
    try:
        # Try to find element quickly (no wait)
        element = None

        if field_id:
            try:
                element = driver.find_element(By.ID, field_id)
            except NoSuchElementException:
                pass

        if not element and field_name:
            try:
                element = driver.find_element(By.NAME, field_name)
            except NoSuchElementException:
                pass

        if element:
            element.clear()
            element.send_keys(value)
            print(f'  ✓ {field_id or field_name}')
            return True

        return False
    except Exception:
        return False

def autofill_checkout(driver, wait):
    """Autofill Shopify checkout form - FAST version"""
    print('\n[AUTOFILL] Starting autofill...')

    # Wait a moment for page to load
    time.sleep(1)

    # Click checkout button if on cart page
    try:
        checkout_btn = driver.find_element(By.NAME, 'checkout')
        checkout_btn.click()
        print('[AUTOFILL] Clicked checkout')
        time.sleep(2)  # Wait for checkout page to load
    except:
        print('[AUTOFILL] Already on checkout page')

    # Fill fields using actual Shopify field IDs
    print('[AUTOFILL] Filling fields...')

    # Email - try multiple IDs (clear first to avoid duplicates)
    try:
        email_field = driver.find_element(By.ID, 'email')
        email_field.clear()
        time.sleep(0.5)
        email_field.send_keys(EMAIL)
        print(f'  ✓ email')
        time.sleep(0.5)  # Wait after email
    except:
        try:
            email_field = driver.find_element(By.NAME, 'email')
            email_field.clear()
            time.sleep(0.5)
            email_field.send_keys(EMAIL)
            print(f'  ✓ email')
            time.sleep(0.5)  # Wait after email
        except:
            pass

    # First name - try common TextField patterns
    filled = False
    for i in range(20):  # Try TextField0 through TextField19
        if fill_input(driver, field_id=f'TextField{i}', value=FIRST_NAME):
            filled = True
            break
    if not filled:
        fill_input(driver, field_name='firstName', value=FIRST_NAME)

    # Last name
    filled = False
    for i in range(20):
        try:
            elem = driver.find_element(By.ID, f'TextField{i}')
            placeholder = elem.get_attribute('placeholder') or ''
            name_attr = elem.get_attribute('name') or ''
            if 'last' in placeholder.lower() or 'lastName' in name_attr:
                elem.clear()
                elem.send_keys(LAST_NAME)
                print(f'  ✓ TextField{i} (last name)')
                filled = True
                break
        except:
            continue
    if not filled:
        fill_input(driver, field_name='lastName', value=LAST_NAME)

    # Company (optional)
    fill_input(driver, field_name='company', value='')

    # Address 1
    filled = False
    for i in range(20):
        try:
            elem = driver.find_element(By.ID, f'TextField{i}')
            placeholder = elem.get_attribute('placeholder') or ''
            name_attr = elem.get_attribute('name') or ''
            if 'address' in placeholder.lower() and 'address1' in name_attr:
                elem.clear()
                elem.send_keys(ADDRESS1)
                print(f'  ✓ TextField{i} (address)')
                filled = True
                break
        except:
            continue
    if not filled:
        fill_input(driver, field_name='address1', value=ADDRESS1)

    # Address 2
    fill_input(driver, field_name='address2', value=ADDRESS2)

    # City
    filled = False
    for i in range(20):
        try:
            elem = driver.find_element(By.ID, f'TextField{i}')
            placeholder = elem.get_attribute('placeholder') or ''
            name_attr = elem.get_attribute('name') or ''
            if 'city' in placeholder.lower() or 'city' in name_attr:
                elem.clear()
                elem.send_keys(CITY)
                print(f'  ✓ TextField{i} (city)')
                filled = True
                break
        except:
            continue
    if not filled:
        fill_input(driver, field_name='city', value=CITY)

    # ZIP Code
    filled = False
    for i in range(20):
        try:
            elem = driver.find_element(By.ID, f'TextField{i}')
            placeholder = elem.get_attribute('placeholder') or ''
            name_attr = elem.get_attribute('name') or ''
            if 'zip' in placeholder.lower() or 'postal' in placeholder.lower() or 'postalCode' in name_attr:
                elem.clear()
                elem.send_keys(ZIP_CODE)
                print(f'  ✓ TextField{i} (zip)')
                filled = True
                break
        except:
            continue
    if not filled:
        fill_input(driver, field_name='postalCode', value=ZIP_CODE)

    # Phone
    filled = False
    for i in range(20):
        try:
            elem = driver.find_element(By.ID, f'TextField{i}')
            placeholder = elem.get_attribute('placeholder') or ''
            name_attr = elem.get_attribute('name') or ''
            if 'phone' in placeholder.lower() or 'phone' in name_attr:
                elem.clear()
                elem.send_keys(PHONE)
                print(f'  ✓ TextField{i} (phone)')
                filled = True
                break
        except:
            continue
    if not filled:
        fill_input(driver, field_name='phone', value=PHONE)

    # Country dropdown - try multiple Select IDs
    try:
        for select_id in ['Select709', 'Select0', 'countryCode']:
            try:
                country_select = Select(driver.find_element(By.ID, select_id))
                country_select.select_by_value('US')
                print(f'  ✓ Country (US)')
                break
            except:
                continue
    except:
        pass

    # State dropdown
    try:
        for select_id in ['Select710', 'Select1', 'zone']:
            try:
                state_select = Select(driver.find_element(By.ID, select_id))
                state_select.select_by_value('CA')  # California
                print(f'  ✓ State (CA)')
                break
            except:
                continue
    except:
        pass

    # Uncheck "Remember me" / Shop account checkbox
    try:
        remember_me = driver.find_element(By.ID, 'RememberMe-RememberMeCheckbox')
        if remember_me.is_selected():
            remember_me.click()
            print('  ✓ Unchecked RememberMe')
    except:
        pass

    # Fill credit card fields (in iframes)
    print('[AUTOFILL] Filling payment info...')
    time.sleep(1)  # Wait for payment iframes to load

    # Card number
    try:
        # Find iframe with card number
        card_number_iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[id^="card-fields-number"]')
        driver.switch_to.frame(card_number_iframe)
        card_input = driver.find_element(By.ID, 'number')
        card_input.clear()
        time.sleep(0.5)
        card_input.send_keys(CARD_NUMBER)
        time.sleep(0.5)  # Wait after card number
        driver.switch_to.default_content()
        print('  ✓ Card number')
    except Exception as e:
        driver.switch_to.default_content()
        print(f'  ✗ Card number')

    # Expiry date
    try:
        expiry_iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[id^="card-fields-expiry"]')
        driver.switch_to.frame(expiry_iframe)
        expiry_input = driver.find_element(By.ID, 'expiry')
        expiry_input.clear()
        time.sleep(0.5)

        # Get last 2 digits of year
        year_2digit = EXP_YEAR[-2:] if len(EXP_YEAR) > 2 else EXP_YEAR

        # Send keys one at a time with small delays to trigger auto-formatting
        for char in EXP_MONTH:
            expiry_input.send_keys(char)
            time.sleep(0.1)

        # Small pause after month
        time.sleep(0.2)

        # Send year digits
        for char in year_2digit:
            expiry_input.send_keys(char)
            time.sleep(0.1)

        time.sleep(0.5)  # Wait after expiry
        driver.switch_to.default_content()
        print('  ✓ Expiry date')
    except Exception as e:
        driver.switch_to.default_content()
        print(f'  ✗ Expiry date')

    # CVV / Security code
    try:
        cvv_iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[id^="card-fields-verification_value"]')
        driver.switch_to.frame(cvv_iframe)
        cvv_input = driver.find_element(By.ID, 'verification_value')
        cvv_input.clear()
        time.sleep(0.5)
        cvv_input.send_keys(CVV)
        time.sleep(0.5)  # Wait after CVV
        driver.switch_to.default_content()
        print('  ✓ CVV')
    except Exception as e:
        driver.switch_to.default_content()
        print(f'  ✗ CVV')

    # Name on card
    try:
        name_iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[id^="card-fields-name"]')
        driver.switch_to.frame(name_iframe)
        name_input = driver.find_element(By.ID, 'name')
        name_input.clear()
        time.sleep(0.5)
        name_input.send_keys(CARDHOLDER_NAME)
        time.sleep(0.5)  # Wait after name
        driver.switch_to.default_content()
        print('  ✓ Name on card')
    except Exception as e:
        driver.switch_to.default_content()
        print(f'  ✗ Name on card')

    print('[AUTOFILL] Payment info filled!')
    print('[AUTOFILL] Waiting 1 second before clicking Pay now...')

    time.sleep(1)

    # Click Pay now button
    try:
        pay_button = driver.find_element(By.ID, 'checkout-pay-button')
        pay_button.click()
        print('[AUTOFILL] ✓ Clicked Pay now!')
        print('[AUTOFILL] Order submitted!')
    except Exception as e:
        print(f'[AUTOFILL] ✗ Could not click Pay now button')
        print('[AUTOFILL] Please click "Pay now" manually')

def ATC():
    print('')

    if not AUTO_BUY:
        print('AUTO_BUY is set to False - Exiting without purchase')
        sys.exit()

    variant = None
    selected_size = None

    # Try to find specific SIZE first
    if SIZE:
        print(f'AUTO_BUY enabled - Looking for size: {SIZE}')
        try:
            variant = soup.find(string=SIZE).findPrevious('id').text
            selected_size = SIZE
            print(f'Found exact size match: {SIZE} (Variant ID: {variant})')
        except AttributeError:
            print(f"Size '{SIZE}' not found")
            if not USE_FIRST_AVAILABLE:
                print("Available sizes:")
                for s in sz:
                    print(f"  - {s}")
                print("USE_FIRST_AVAILABLE is False - Exiting")
                sys.exit()

    # Use first available if SIZE not specified or not found
    if not variant and (not SIZE or USE_FIRST_AVAILABLE):
        if len(vrnt) > 0:
            variant = vrnt[0]
            selected_size = sz[0] if len(sz) > 0 else 'Unknown'
            print(f'Using first available size: {selected_size} (Variant ID: {variant})')
        else:
            print('ERROR: No variants found!')
            sys.exit()

    if not variant:
        print('ERROR: Could not determine variant to purchase')
        sys.exit()

    url = urlparse(URL)
    baseurl = 'https://' + url.netloc + '/cart/'
    BD = baseurl + variant + ':' + QUANTITY

    print(f'Adding to cart - Size: {selected_size}, Quantity: {QUANTITY}')
    print(f'Cart URL: {BD}')

    try:
        driver = webdriver.Chrome()
        wait = WebDriverWait(driver, 10)

        driver.get(BD)
        print('Successfully added to cart! Browser window opened.')

        if AUTOFILL_CHECKOUT:
            autofill_checkout(driver, wait)
        else:
            print('AUTOFILL_CHECKOUT is disabled - Complete checkout manually.')

        print('\nBrowser will remain open for you to complete the purchase.')
        print('Press Ctrl+C in terminal when done to close.')

        # Keep browser open
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print('\nClosing browser...')
            driver.quit()

    except Exception as e:
        print(f'Error opening browser: {e}')
        print('Make sure ChromeDriver is installed and in your PATH')
        import traceback
        traceback.print_exc()
        sys.exit()

ATC()

print('')
print('Bot completed successfully!')
