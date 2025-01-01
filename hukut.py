from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
import time
import re
import csv
from datetime import datetime
import os

def create_csv_file():
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scraped_products_{timestamp}.csv"
    
    # Define CSV headers
    headers = [
        'Product Link',
        'Image URL',
        'Product Name',
        'Product Price',
        'Rating',
        'Number of Reviews',
        'Specifications'
    ]
    
    # Create CSV file with headers
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
    
    return filename

def save_product_to_csv(product_data, filename):
    # Append product data to CSV file
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=product_data.keys())
        writer.writerow(product_data)

# Initialize WebDriver
driver = webdriver.Chrome()
driver.get("https://www.hukut.com/")
time.sleep(2)

# Create CSV file
csv_filename = create_csv_file()
print(f"Created CSV file: {csv_filename}")

# Counter for scraped products
products_count = 0

# Click on the search bar
search_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Search']")
query = str(input("Enter the product you want to search for: "))
search_box.send_keys(query)
search_box.send_keys(Keys.RETURN)
time.sleep(2)

# Locate all divs with the specified class
div_elements = driver.find_elements(By.CSS_SELECTOR, "div.peer.h-full.w-full")

# Loop through each div and extract links
for div_element in div_elements:
    try:
        # Re-locate the div element to avoid stale references
        div_element = driver.find_element(By.CSS_SELECTOR, "div.peer.h-full.w-full")
        a_tags = div_element.find_elements(By.TAG_NAME, "a")
        
        # Visit each link found in the 'a' tags
        for a_tag in a_tags:
            href = a_tag.get_attribute("href")
            if href:
                print(f"\nVisiting: {href}")
                driver.get(href)
                time.sleep(2)
                
                # Dictionary to store product data
                product_data = {
                    'Product Link': '',
                    'Image URL': '',
                    'Product Name': '',
                    'Product Price': '',
                    'Rating': '',
                    'Number of Reviews': '',
                    'Specifications': ''
                }
                
                # Scrape data from the visited page
                try:
                    product_data['Product Link'] = driver.current_url
                    print("Product Link: ✓")
                except NoSuchElementException:
                    print("Product Link: ✗")
                
                try:
                    product_data['Product Name'] = driver.find_element(By.CSS_SELECTOR, "h1.text-md").text
                    print("Product Name: ✓")
                except NoSuchElementException:
                    print("Product Name: ✗")

                try:
                    price_element = driver.find_element(By.XPATH, "//div[contains(@class, 'font-semibold') and contains(text(), 'रु')]")
                    product_data['Product Price'] = price_element.text
                    print("Product Price: ✓")
                except NoSuchElementException:
                    print("Product Price: ✗")
                    
                try:
                    img_tag = driver.find_element(By.CSS_SELECTOR, "img[aria-label='Product Image']")
                    product_data['Image URL'] = img_tag.get_attribute("src")
                    print("Image URL: ✓")
                except NoSuchElementException:
                    print("Image URL: ✗")

                try:
                    rating_text = driver.find_element(By.XPATH, '/html/body/div[3]/section/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div/p').text
                    rating_match = re.match(r"(\d+\.\d+) \((\d+) Reviews?\)", rating_text)
                    
                    if rating_match:
                        product_data['Rating'] = rating_match.group(1)
                        product_data['Number of Reviews'] = rating_match.group(2)
                        print("Rating and Reviews: ✓")
                    else:
                        print("Rating and Reviews: ✗")
                except NoSuchElementException:
                    print("Rating and Reviews: ✗")

                try:
                    specification_section = driver.find_element(By.XPATH, '/html/body/div[3]/section/section[2]/div/div/div/div')
                    product_data['Specifications'] = specification_section.text.replace('\n', ' | ')
                    print("Specifications: ✓")
                except Exception:
                    print("Specifications: ✗")
                
                # Save product data immediately if it has at least some information
                if any(product_data.values()):
                    save_product_to_csv(product_data, csv_filename)
                    products_count += 1
                    print(f"\nSaved product #{products_count} to CSV: {product_data['Product Name']}")
                
                # Navigate back to the search results
                driver.back()
                time.sleep(2)
                
    except StaleElementReferenceException:
        print("Encountered StaleElementReferenceException. Re-locating elements...")
        div_elements = driver.find_elements(By.CSS_SELECTOR, "div.peer.h-full.w-full")

# Close the browser
driver.quit()

# Final summary
print(f"\nScraping completed!")
print(f"Total products saved to {csv_filename}: {products_count}")