import csv
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def scrape_product_page(driver, required_spec_keys):
    product_data = {}
    try:
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(1)

        product_data['Product Link'] = driver.current_url
        product_data['Product Name'] = driver.find_element(By.TAG_NAME, "h1").text
        product_data['Product Price'] = driver.find_element(By.CSS_SELECTOR, "span.pdp-price").text
        product_data['Image URL'] = driver.find_element(By.CSS_SELECTOR, "img.pdp-mod-common-image").get_attribute("src")
        product_data['Rating'] = driver.find_element(By.CSS_SELECTOR, "span.score-average").text
        product_data['Number of Ratings'] = driver.find_element(By.CLASS_NAME, "pdp-review-summary__link").text

        specs_div = driver.find_element(By.CLASS_NAME, "pdp-mod-specification")
        specs_items = specs_div.find_elements(By.CLASS_NAME, "key-li")
        specifications = {}
        for item in specs_items:
            key = item.find_element(By.CLASS_NAME, "key-title").text.strip()
            value = item.find_element(By.CLASS_NAME, "key-value").text.strip()
            if key in required_spec_keys:
                specifications[key] = value
        product_data['Specifications'] = specifications

    except NoSuchElementException:
        pass
    return product_data


def scrape_daraz_products(query, required_spec_keys):
    driver = webdriver.Chrome()
    driver.get("https://www.daraz.com.np/#?")
    wait = WebDriverWait(driver, 10)

    search_box = wait.until(EC.presence_of_element_located((By.ID, "q")))
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div._95X4G")))

    page_number = 1
    all_products = []

    while True:
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(2)

        product_elements = driver.find_elements(By.CSS_SELECTOR, "div._95X4G a")
        product_links = [elem.get_attribute("href") for elem in product_elements if elem.get_attribute("href")]

        for link in product_links:
            driver.get(link)
            product_data = scrape_product_page(driver, required_spec_keys)
            if product_data:
                all_products.append(product_data)

        try:
            next_page = f"https://www.daraz.com.np/catalog/?page={page_number + 1}&q={query}&spm=a2a0e.tm80335409.search.d_go"
            driver.get(next_page)
            time.sleep(2)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div._95X4G")))
            page_number += 1
        except TimeoutException:
            break

    driver.quit()
    return all_products
