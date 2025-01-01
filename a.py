import csv
import re
import time
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException
)
from selenium.webdriver.chrome.options import Options

class ProductScraper:
    def __init__(self, base_url, max_workers=4):
        self.base_url = base_url
        self.max_workers = max_workers
        self.wait_time = 10
        self.products = []
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-logging')
        chrome_options.page_load_strategy = 'eager'  # Don't wait for all resources to load
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver

    def wait_for_element(self, driver, selector, by=By.CSS_SELECTOR, timeout=10):
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            return None

    def extract_product_data(self, driver, url):
        try:
            driver.get(url)
            product_data = {
                "Product Link": url,
                "Image URL": "",
                "Product Name": "",
                "Product Price": "",
                "Rating": "",
                "Number of Ratings": "",
                "Specifications": ""
            }

            # Use dictionary mapping for selectors
            selectors = {
                "Product Name": ("h1.text-md", By.CSS_SELECTOR),
                "Product Price": ("//div[contains(@class, 'font-semibold') and contains(text(), 'रु')]", By.XPATH),
                "Image URL": ("img[aria-label='Product Image']", By.CSS_SELECTOR),
                "Rating": ('/html/body/div[3]/section/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div/p', By.XPATH),
                "Specifications": ('/html/body/div[3]/section/section[2]/div/div/div/div', By.XPATH)
            }

            # Extract data using the selectors
            for key, (selector, by) in selectors.items():
                element = self.wait_for_element(driver, selector, by)
                if element:
                    if key == "Image URL":
                        product_data[key] = element.get_attribute("src")
                    elif key == "Rating":
                        rating_text = element.text
                        rating_match = re.match(r"(\d+\.\d+) \((\d+) Reviews?\)", rating_text)
                        if rating_match:
                            product_data["Rating"] = rating_match.group(1)
                            product_data["Number of Ratings"] = rating_match.group(2)
                    else:
                        product_data[key] = element.text

            return product_data
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

    def scrape_product_links(self, driver):
        search_box = self.wait_for_element(driver, "input[placeholder='Search']")
        if search_box:
            search_box.send_keys("phone" + Keys.RETURN)

        product_links = set()
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            # Get all product links
            elements = driver.find_elements(By.CSS_SELECTOR, "div.peer.h-full.w-full a")
            for element in elements:
                href = element.get_attribute("href")
                if href:
                    product_links.add(href)

            # Check if we've reached the bottom
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        return list(product_links)

    def scrape_products(self):
        driver = self.setup_driver()
        try:
            driver.get(self.base_url)
            product_links = self.scrape_product_links(driver)
            
            # Use ThreadPoolExecutor for parallel scraping
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for url in product_links:
                    product_driver = self.setup_driver()
                    futures.append(
                        executor.submit(self.extract_product_data, product_driver, url)
                    )
                
                for future in futures:
                    product_data = future.result()
                    if product_data:
                        self.products.append(product_data)
                        
        finally:
            driver.quit()

    def save_to_csv(self, filename):
        if not self.products:
            return
        
        fieldnames = self.products[0].keys()
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.products)

def main():
    scraper = ProductScraper("https://www.hukut.com/")
    scraper.scrape_products()
    scraper.save_to_csv('scraped_data.csv')

if __name__ == "__main__":
    main()