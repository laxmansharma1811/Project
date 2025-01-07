from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

class DarazScraper:
    def __init__(self):
        self.required_spec_keys = [
            'Brand', 'SKU', 'Wireless Connectivity', 'Display Size', 'Operating System', 'CPU Cores',
            'Ram Memory', 'Model No.', 'Touch Pad', 'Storage Capacity', 'Processor', 'Storage Type', 'Touch',
            'Generation', "What's in the box"
        ]
    
    def setup_driver(self):
        """Initialize and return a Chrome WebDriver."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=options)

    def scrape_product_page(self, driver, url):
        """Scrape details of a single product."""
        driver.get(url)
        product_data = {}
        
        try:
            # Scroll to load dynamic content
            driver.execute_script("window.scrollBy(0, 1500);")
            time.sleep(1)

            # Scrape basic product details
            product_data['product_link'] = driver.current_url
            product_data['product_name'] = driver.find_element(By.TAG_NAME, "h1").text
            product_data['product_price'] = driver.find_element(By.CSS_SELECTOR, "span.pdp-price").text
            product_data['image_url'] = driver.find_element(By.CSS_SELECTOR, "img.pdp-mod-common-image").get_attribute("src")
            
            try:
                product_data['rating'] = driver.find_element(By.CSS_SELECTOR, "span.score-average").text
                product_data['number_of_ratings'] = driver.find_element(By.CLASS_NAME, "pdp-review-summary__link").text
            except NoSuchElementException:
                product_data['rating'] = "No rating"
                product_data['number_of_ratings'] = "0 ratings"

            # Scrape product specifications
            specs_div = driver.find_element(By.CLASS_NAME, "pdp-mod-specification")
            specs_items = specs_div.find_elements(By.CLASS_NAME, "key-li")
            specifications = {}
            for item in specs_items:
                key = item.find_element(By.CLASS_NAME, "key-title").text.strip()
                value = item.find_element(By.CLASS_NAME, "key-value").text.strip()
                if key in self.required_spec_keys:
                    specifications[key] = value
            
            
            # Convert specifications dictionary to string
            if specifications:
                product_data['specifications'] = "; ".join(f"{k}: {v}" for k, v in specifications.items())
            else:
                product_data['specifications'] = "No specifications found"

        except NoSuchElementException as e:
            print(f"Error scraping product page: {str(e)}")
            return None

        return product_data

    def get_product_links(self, driver, limit=5):
        """Extract product links from search results page."""
        try:
            # Wait for product elements to load
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div._95X4G")))
            
            # Scroll to load all products
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(2)

            # Get product links
            product_elements = driver.find_elements(By.CSS_SELECTOR, "div._95X4G a")
            product_links = [elem.get_attribute("href") for elem in product_elements if elem.get_attribute("href")]
            
            return product_links[:limit]  # Return only the specified number of links
            
        except TimeoutException:
            print("Timeout while loading search results")
            return []

    def search_products(self, query, limit=5):
        """Search for products and return scraped data."""
        driver = self.setup_driver()
        products = []
        
        try:
            # Navigate to Daraz homepage
            driver.get("https://www.daraz.com.np/#?")
            wait = WebDriverWait(driver, 10)
            
            # Find and use the search box
            search_box = wait.until(EC.presence_of_element_located((By.ID, "q")))
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            # Get product links
            product_links = self.get_product_links(driver, limit)
            
            # Scrape each product
            for link in product_links:
                print(f"Scraping product: {link}")
                product_data = self.scrape_product_page(driver, link)
                if product_data:
                    products.append(product_data)
                if len(products) >= limit:
                    break

        except Exception as e:
            print(f"An error occurred during scraping: {str(e)}")
        
        finally:
            driver.quit()
        
        return products

# Example usage
if __name__ == "__main__":
    scraper = DarazScraper()
    results = scraper.search_products("laptop", limit=5)
    for result in results:
        print(f"Found product: {result.get('product_name')}")