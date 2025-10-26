"""Shopify purchase automation service."""

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urlparse
import requests
import time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import os
import lxml


class ProductVariant(BaseModel):
    """Represents a Shopify product variant."""
    size: str
    stock: str
    price: str
    variant_id: str


class ProductInfo(BaseModel):
    """Represents Shopify product information."""
    name: str
    url: str
    variants: List[ProductVariant]
    total_stock: int


class PurchaseConfig(BaseModel):
    """Configuration for Shopify purchase."""
    product_url: str
    size: Optional[str] = None  # Specific size, or None for first available
    quantity: str = "1"
    auto_buy: bool = True
    autofill_checkout: bool = True

    # Customer information
    email: str
    first_name: str
    last_name: str
    address1: str
    address2: str = ""
    city: str
    state: str
    zip_code: str
    country: str = "United States"
    phone: str

    # Payment information
    card_number: str
    cardholder_name: str
    exp_month: str
    exp_year: str
    cvv: str


class ShopifyPurchaseService:
    """Service for automating Shopify purchases."""

    def __init__(self):
        # Load default config from environment
        self.default_config = self._load_default_config()

    def _load_default_config(self) -> Dict[str, str]:
        """Load default purchase configuration from environment variables."""
        return {
            "email": os.getenv("SHOPIFY_EMAIL", "gooncube@gmail.com"),
            "first_name": os.getenv("SHOPIFY_FIRST_NAME", "John"),
            "last_name": os.getenv("SHOPIFY_LAST_NAME", "Doe"),
            "address1": os.getenv("SHOPIFY_ADDRESS1", "123 Test Street"),
            "address2": os.getenv("SHOPIFY_ADDRESS2", "Apt 4B"),
            "city": os.getenv("SHOPIFY_CITY", "Los Angeles"),
            "state": os.getenv("SHOPIFY_STATE", "California"),
            "zip_code": os.getenv("SHOPIFY_ZIP", "90210"),
            "country": os.getenv("SHOPIFY_COUNTRY", "United States"),
            "phone": os.getenv("SHOPIFY_PHONE", "9178349732"),
            "card_number": os.getenv("SHOPIFY_CARD_NUMBER", "4242424242424242"),
            "cardholder_name": os.getenv("SHOPIFY_CARDHOLDER_NAME", "John Doe"),
            "exp_month": os.getenv("SHOPIFY_EXP_MONTH", "12"),
            "exp_year": os.getenv("SHOPIFY_EXP_YEAR", "25"),
            "cvv": os.getenv("SHOPIFY_CVV", "123"),
        }

    async def get_product_info(self, product_url: str) -> ProductInfo:
        """
        Fetch product information from a Shopify URL.

        Args:
            product_url: Shopify product URL

        Returns:
            ProductInfo object with product details
        """
        # Clean URL
        if '?' in product_url:
            product_url, _, _ = product_url.partition('?')

        # Get product XML
        s = requests.Session()
        r = s.get(product_url + '.xml')
        soup = BeautifulSoup(r.text, 'lxml')

        # Extract product name
        name_tag = soup.find('title')
        name = name_tag.text if name_tag else "Unknown Product"

        # Find all variant tags
        variant_tags = soup.find_all('variant')

        if not variant_tags:
            # Fallback to old method if no variant tags found
            return await self._get_product_info_legacy(product_url, soup, name)

        # Build variants from variant tags
        variants = []
        total_stock = 0

        for variant_tag in variant_tags:
            # Extract variant details
            variant_id_tag = variant_tag.find('id')
            title_tag = variant_tag.find('title')
            price_tag = variant_tag.find('price')
            inventory_qty_tag = variant_tag.find('inventory-quantity')

            if not variant_id_tag or not title_tag or not price_tag:
                continue

            variant_id = variant_id_tag.text
            title = title_tag.text
            price = price_tag.text

            # Handle inventory quantity
            # If not available, assume "Available" (we can't know exact count)
            if inventory_qty_tag:
                stock = inventory_qty_tag.text
                try:
                    total_stock += int(stock)
                except (ValueError, TypeError):
                    # If we can't parse it, assume 1 in stock
                    stock = "Available"
                    total_stock += 1
            else:
                # No inventory quantity in XML - assume available
                stock = "Available"
                total_stock += 1

            variants.append(ProductVariant(
                size=title,
                stock=stock,
                price=price,
                variant_id=variant_id
            ))

        return ProductInfo(
            name=name,
            url=product_url,
            variants=variants,
            total_stock=total_stock
        )

    async def _get_product_info_legacy(self, product_url: str, soup, name: str) -> ProductInfo:
        """Legacy method for parsing product XML (fallback)."""
        # Extract sizes
        sizes = []
        for size in soup.find_all('title')[1:]:
            sizes.append(size.get_text())

        # Extract stock
        stocks = []
        for stock in soup.find_all('inventory-quantity'):
            stocks.append(stock.get_text())

        # Extract prices
        prices = []
        for price in soup.find_all('price'):
            prices.append(price.get_text())

        # Extract variant IDs
        variant_ids = []
        for variants in soup.find_all('product-id'):
            variant_ids.append(variants.find_previous('id').get_text())

        # If no stock info available, assume available
        if not stocks and sizes:
            stocks = ["Available"] * len(sizes)

        # Calculate total stock
        total_stock = 0
        for s in stocks:
            try:
                total_stock += int(s)
            except (ValueError, TypeError):
                total_stock += 1  # Assume 1 if we can't parse

        # Build variants
        variants = []
        for size, stock, price, variant_id in zip(sizes, stocks, prices, variant_ids):
            variants.append(ProductVariant(
                size=size,
                stock=stock,
                price=price,
                variant_id=variant_id
            ))

        return ProductInfo(
            name=name,
            url=product_url,
            variants=variants,
            total_stock=total_stock
        )

    def _fill_input(self, driver, field_id=None, field_name=None, value=''):
        """Helper function to fill input fields."""
        try:
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
                return True

            return False
        except Exception:
            return False

    def _autofill_checkout(self, driver, wait, config: PurchaseConfig):
        """Autofill Shopify checkout form."""
        time.sleep(1)

        # Click checkout button if on cart page
        try:
            checkout_btn = driver.find_element(By.NAME, 'checkout')
            checkout_btn.click()
            time.sleep(2)
        except:
            pass  # Already on checkout page

        # Fill email
        try:
            email_field = driver.find_element(By.ID, 'email')
            email_field.clear()
            time.sleep(0.5)
            email_field.send_keys(config.email)
            time.sleep(0.5)
        except:
            pass

        # Fill form fields
        self._fill_input(driver, field_name='firstName', value=config.first_name)
        self._fill_input(driver, field_name='lastName', value=config.last_name)
        self._fill_input(driver, field_name='address1', value=config.address1)
        self._fill_input(driver, field_name='address2', value=config.address2)
        self._fill_input(driver, field_name='city', value=config.city)
        self._fill_input(driver, field_name='postalCode', value=config.zip_code)
        self._fill_input(driver, field_name='phone', value=config.phone)

        # Fill payment info
        time.sleep(1)

        # Card number
        try:
            card_number_iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[id^="card-fields-number"]')
            driver.switch_to.frame(card_number_iframe)
            card_input = driver.find_element(By.ID, 'number')
            card_input.clear()
            time.sleep(0.5)
            card_input.send_keys(config.card_number)
            time.sleep(0.5)
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()

        # Expiry date
        try:
            expiry_iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[id^="card-fields-expiry"]')
            driver.switch_to.frame(expiry_iframe)
            expiry_input = driver.find_element(By.ID, 'expiry')
            expiry_input.clear()
            time.sleep(0.5)

            year_2digit = config.exp_year[-2:] if len(config.exp_year) > 2 else config.exp_year

            for char in config.exp_month:
                expiry_input.send_keys(char)
                time.sleep(0.1)
            time.sleep(0.2)
            for char in year_2digit:
                expiry_input.send_keys(char)
                time.sleep(0.1)

            time.sleep(0.5)
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()

        # CVV
        try:
            cvv_iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[id^="card-fields-verification_value"]')
            driver.switch_to.frame(cvv_iframe)
            cvv_input = driver.find_element(By.ID, 'verification_value')
            cvv_input.clear()
            time.sleep(0.5)
            cvv_input.send_keys(config.cvv)
            time.sleep(0.5)
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()

        # Name on card
        try:
            name_iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[id^="card-fields-name"]')
            driver.switch_to.frame(name_iframe)
            name_input = driver.find_element(By.ID, 'name')
            name_input.clear()
            time.sleep(0.5)
            name_input.send_keys(config.cardholder_name)
            time.sleep(0.5)
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()

        time.sleep(1)

        # Click Pay now button
        try:
            pay_button = driver.find_element(By.ID, 'checkout-pay-button')
            pay_button.click()
        except Exception:
            pass

    async def purchase_product(
        self,
        product_url: str,
        config: Optional[PurchaseConfig] = None
    ) -> Dict[str, Any]:
        """
        Automate purchase of a Shopify product.

        Args:
            product_url: Shopify product URL
            config: Optional purchase configuration (uses defaults if not provided)

        Returns:
            Dictionary with purchase status
        """
        # Get product info
        product_info = await self.get_product_info(product_url)

        # Check if we have any variants
        if not product_info.variants or len(product_info.variants) == 0:
            return {
                "success": False,
                "message": "No product variants found",
                "product": product_info.dict()
            }

        # Use default config if not provided
        if config is None:
            config = PurchaseConfig(
                product_url=product_url,
                **self.default_config
            )

        # Find variant to purchase
        variant = None
        selected_size = None

        if config.size:
            # Look for specific size
            for v in product_info.variants:
                if v.size == config.size:
                    variant = v
                    selected_size = v.size
                    break

        # Use first available if size not specified or not found
        if not variant and product_info.variants:
            variant = product_info.variants[0]
            selected_size = variant.size

        if not variant:
            return {
                "success": False,
                "message": "No variant found",
                "product": product_info.dict()
            }

        # Build cart URL
        url = urlparse(product_url)
        baseurl = 'https://' + url.netloc + '/cart/'
        cart_url = baseurl + variant.variant_id + ':' + config.quantity

        # Open browser and purchase
        try:
            driver = webdriver.Chrome()
            wait = WebDriverWait(driver, 10)

            driver.get(cart_url)

            if config.autofill_checkout:
                self._autofill_checkout(driver, wait, config)

            return {
                "success": True,
                "message": "Purchase initiated",
                "product": product_info.dict(),
                "selected_variant": variant.dict(),
                "cart_url": cart_url,
                "browser_open": True
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "product": product_info.dict()
            }


# Singleton instance
_purchase_service: Optional[ShopifyPurchaseService] = None


def get_purchase_service() -> ShopifyPurchaseService:
    """Get or create the Shopify purchase service singleton."""
    global _purchase_service
    if _purchase_service is None:
        _purchase_service = ShopifyPurchaseService()
    return _purchase_service
